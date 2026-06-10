"""Claude Sonnet template filler.

The LLM never sees, generates, summarises, or paraphrases legal text.
It only fits brand parameters into a pre-written specialist template.
Article references always come from the rules table, never from the model.
"""

import asyncio
import logging

import anthropic

from app.config import get_settings

logger = logging.getLogger("heron.replacement")

BATCH_SIZE = 5
BATCH_DELAY_SECONDS = 0.5

SYSTEM_PROMPT = """You are a consumer law compliance copywriter specialising in EU environmental claims regulations.

Your only task: fill the brand-specific parameters into the provided compliance template.

RULES:
1. You MUST use the exact template structure provided. Do not change any legal language.
2. Replace only the {parameter} placeholders with brand-specific information.
3. If you cannot determine a parameter from the brand context, use a generic but honest placeholder like "[à compléter]".
4. Never add new claims. Never add "eco-friendly", "sustainable", "green", "natural" or any synonym.
5. Output ONLY the completed replacement text. No explanation. No preamble. No quotes around the output.
6. Maximum 2 sentences. The replacement must be shorter than the original claim."""

USER_PROMPT_TEMPLATE = """ORIGINAL CLAIM (prohibited under {empco_article}):
"{original_text}"

COMPLIANCE TEMPLATE (written by a consumer law specialist — do not alter the structure):
"{safe_template}"

BRAND CONTEXT:
- Domain: {domain}
- Industry: {industry}
- Known ingredients/materials: {known_ingredients}
- Active certifications: {certifications}

Fill the template with the brand context. Output the completed replacement text only."""


class ReplacementGenerator:
    def __init__(self, api_key: str):
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.model = get_settings().CLAUDE_MODEL

    async def generate_replacement(
        self,
        original_text: str,
        safe_template: str,
        brand_context: dict,
        empco_article: str,
    ) -> str:
        user_prompt = USER_PROMPT_TEMPLATE.format(
            empco_article=empco_article,
            original_text=original_text,
            safe_template=safe_template,
            domain=brand_context.get("domain", "[à compléter]"),
            industry=brand_context.get("industry", "[à compléter]"),
            known_ingredients=brand_context.get("known_ingredients", "[à compléter]"),
            certifications=brand_context.get("certifications", "aucune"),
        )
        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=300,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_prompt}],
            )
            text = "".join(
                block.text for block in response.content if block.type == "text"
            ).strip()
            return text or safe_template
        except Exception as exc:
            logger.warning("Replacement generation failed (%s); falling back to raw template", exc)
            return safe_template

    async def generate_batch(self, claims: list[dict], brand_context: dict) -> list[dict]:
        """Fill templates for all claims, in batches of 5 with a rate-limit delay."""
        for start in range(0, len(claims), BATCH_SIZE):
            batch = claims[start:start + BATCH_SIZE]
            results = await asyncio.gather(
                *(
                    self.generate_replacement(
                        original_text=claim.get("context") or claim.get("matched_text", ""),
                        safe_template=claim["safe_template"],
                        brand_context=brand_context,
                        empco_article=claim["empco_article"],
                    )
                    for claim in batch
                )
            )
            for claim, replacement in zip(batch, results):
                claim["replacement_text"] = replacement
            if start + BATCH_SIZE < len(claims):
                await asyncio.sleep(BATCH_DELAY_SECONDS)
        return claims
