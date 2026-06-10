"""Deterministic EmpCo pattern matcher.

Zero LLM involvement in this file. Every match is the product of a
pre-compiled regular expression stored in the rules table — article
references and legal explanations are carried verbatim from the rule
metadata, never generated.
"""

import re

CONTEXT_CHARS = 100


class RegexEngine:
    def __init__(self, rules: list[dict]):
        """Compile all regex patterns on init — fail fast on bad patterns."""
        self.rules: dict[str, dict] = {}
        errors: list[str] = []
        for rule in rules:
            try:
                compiled = re.compile(rule["pattern"], re.IGNORECASE)
            except re.error as exc:
                errors.append(f"{rule['id']}: {exc}")
                continue
            self.rules[rule["id"]] = {"compiled": compiled, "meta": rule}
        if errors:
            raise ValueError("Invalid regex pattern(s) in rules: " + "; ".join(errors))

    def match_page(self, page: dict) -> list[dict]:
        """Run all compiled patterns against page['body_text']."""
        text = page.get("body_text") or ""
        page_url = page.get("url", "")
        matches: list[dict] = []
        for rule_id, entry in self.rules.items():
            meta = entry["meta"]
            for m in entry["compiled"].finditer(text):
                start, end = m.span()
                context = text[max(0, start - CONTEXT_CHARS): min(len(text), end + CONTEXT_CHARS)]
                matches.append(
                    {
                        "rule_id": rule_id,
                        "matched_text": m.group(0),
                        "context": context,
                        "page_url": page_url,
                        "empco_article": meta["empco_article"],
                        "empco_article_full_ref": meta["empco_article_full_ref"],
                        "risk_level": meta["risk_level"],
                        "legal_explanation": meta["legal_explanation"],
                        "safe_template": meta["safe_template"],
                        "matched_pattern": meta["pattern"],
                        "requires_evidence": meta.get("requires_evidence", 0),
                    }
                )
        return matches

    def match_all_pages(self, pages: list[dict]) -> list[dict]:
        """Run match_page on all pages, deduplicating identical claims.

        Same rule_id + same matched_text (case-insensitive) on the same
        URL counts as one claim.
        """
        seen: set[tuple[str, str, str]] = set()
        results: list[dict] = []
        for page in pages:
            for match in self.match_page(page):
                key = (match["rule_id"], match["matched_text"].lower(), match["page_url"])
                if key in seen:
                    continue
                seen.add(key)
                results.append(match)
        return results
