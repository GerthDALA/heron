"""Ads copy scanner: text-input scan pipeline. No crawler involved.

Same regex engine, same risk calculation, same replacement generation as
domain scans — synchronous, returning results in the HTTP response.
"""

import re

from app.engine.regex_engine import RegexEngine
from app.engine.replacement_generator import ReplacementGenerator
from app.engine.risk_calculator import RiskCalculator

VALID_INPUT_TYPES = ("ad_copy", "email", "social_post", "transcript", "other")
MIN_CHARS = 10
MAX_CHARS = 50000

_HTML_TAG_RE = re.compile(r"<[^>]+>")
_WHITESPACE_RE = re.compile(r"\s+")


def normalise_input_text(text: str) -> str:
    """Strip HTML tags and collapse whitespace before scanning."""
    text = _HTML_TAG_RE.sub(" ", text)
    return _WHITESPACE_RE.sub(" ", text).strip()


class AdsScanner:
    def __init__(self, regex_engine: RegexEngine, risk_calculator: RiskCalculator):
        self.regex_engine = regex_engine
        self.risk_calculator = risk_calculator

    def scan_text(
        self,
        text: str,
        input_type: str,
        annual_revenue_eur: float,
        source_label: str = "",
    ) -> list[dict]:
        """Run the regex engine over raw copy and price each match."""
        clean = normalise_input_text(text)
        fake_page = {
            "url": source_label or "submitted_text",
            "title": input_type,
            "body_text": clean,
        }
        matches = self.regex_engine.match_all_pages([fake_page])
        for match in matches:
            match["exposure_eur"] = self.risk_calculator.calculate_claim_exposure(
                annual_revenue_eur, match["risk_level"]
            )
        return matches

    async def scan_text_with_replacements(
        self,
        text: str,
        input_type: str,
        annual_revenue_eur: float,
        brand_context: dict,
        replacement_generator: ReplacementGenerator,
        source_label: str = "",
    ) -> list[dict]:
        """Same as scan_text, plus compliant replacement copy (paid scans)."""
        claims = self.scan_text(text, input_type, annual_revenue_eur, source_label)
        if claims:
            claims = await replacement_generator.generate_batch(claims, brand_context)
        return claims
