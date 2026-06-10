"""Ground-truth tests for the deterministic EmpCo regex engine.

These cases define the product's detection contract:
zero false negatives on known prohibited claims, zero false positives
on the documented compliant phrasings.
"""

import re

import pytest


def matches_for(engine, text: str) -> list[dict]:
    return engine.match_page({"url": "https://example.fr/test", "body_text": text})


def risk_levels(engine, text: str) -> set[str]:
    return {m["risk_level"] for m in matches_for(engine, text)}


def articles(engine, text: str) -> set[str]:
    return {m["empco_article"] for m in matches_for(engine, text)}


# --- Must return HIGH risk (Article 4a generic claims) ---

HIGH_4A_CASES = [
    "Formule eco-responsable",
    "eco-friendly formula",
    "ingredients naturels soigneusement sélectionnés",
    "respectueux de la planète",
    "green formula",
    "naturel",
    "durable",
    "biologique",
    "umweltfreundlich",
    "nachhaltig",
]


@pytest.mark.parametrize("text", HIGH_4A_CASES)
def test_high_risk_article_4a(regex_engine, text):
    found = matches_for(regex_engine, text)
    assert found, f"Expected a match for prohibited claim: {text!r}"
    assert any(m["risk_level"] == "high" and m["empco_article"] == "Article 4a" for m in found), \
        f"Expected HIGH / Article 4a for {text!r}, got {found}"


# --- Must return HIGH risk (Article 4d carbon claims) ---

HIGH_4D_CASES = [
    "carbon neutral by 2030",
    "nous serons carbon neutral en 2030",
    "objectif zéro carbone 2030",
]


@pytest.mark.parametrize("text", HIGH_4D_CASES)
def test_high_risk_article_4d(regex_engine, text):
    found = matches_for(regex_engine, text)
    assert found, f"Expected a match for carbon claim: {text!r}"
    assert any(m["risk_level"] == "high" and m["empco_article"] == "Article 4d" for m in found), \
        f"Expected HIGH / Article 4d for {text!r}, got {found}"


# --- Must return MEDIUM risk (Article 4c single-aspect superlatives) ---

MEDIUM_4C_CASES = [
    "notre collection la plus durable à ce jour",
    "le packaging le plus eco-conçu de notre gamme",
]


@pytest.mark.parametrize("text", MEDIUM_4C_CASES)
def test_medium_risk_article_4c(regex_engine, text):
    found = matches_for(regex_engine, text)
    assert found, f"Expected a match for superlative claim: {text!r}"
    assert any(m["risk_level"] == "medium" and m["empco_article"] == "Article 4c" for m in found), \
        f"Expected MEDIUM / Article 4c for {text!r}, got {found}"
    assert not any(m["risk_level"] == "high" for m in found), \
        f"Superlative claim must not also trigger a HIGH generic rule: {found}"


# --- Must NOT match (true negatives) ---

TRUE_NEGATIVES = [
    "certifié COSMOS par Ecocert",
    "100% coton biologique certifié GOTS",
    "notre empreinte carbone 2024 est de 1.2 tonne CO2eq",
    "fabriqué en France",
    "sans parabènes",
]


@pytest.mark.parametrize("text", TRUE_NEGATIVES)
def test_true_negatives(regex_engine, text):
    found = matches_for(regex_engine, text)
    assert found == [], f"False positive on compliant text {text!r}: {found}"


# --- Engine mechanics ---

def test_all_seed_patterns_compile(rules):
    for rule in rules:
        re.compile(rule["pattern"], re.IGNORECASE)


def test_bad_pattern_fails_fast():
    from app.engine.regex_engine import RegexEngine
    broken = [{
        "id": "BAD-001", "pattern": "([unclosed", "risk_level": "high",
        "empco_article": "Article 4a", "empco_article_full_ref": "x",
        "legal_explanation": "x", "safe_template": "x",
    }]
    with pytest.raises(ValueError):
        RegexEngine(broken)


def test_context_window_is_captured(regex_engine):
    padding = "lorem ipsum " * 30
    text = padding + "formule eco-responsable" + " " + padding
    found = matches_for(regex_engine, text)
    assert found
    match = next(m for m in found if "eco-responsable" in m["matched_text"].lower())
    assert match["matched_text"].lower() in match["context"].lower()
    assert len(match["context"]) > len(match["matched_text"])


def test_match_all_pages_deduplicates(regex_engine):
    page = {"url": "https://example.fr/p", "body_text": "eco-responsable et encore eco-responsable"}
    results = regex_engine.match_all_pages([page, page])
    keys = [(m["rule_id"], m["matched_text"].lower(), m["page_url"]) for m in results]
    assert len(keys) == len(set(keys)), "Duplicate claims must be collapsed"
    assert sum(1 for m in results if "eco-responsable" in m["matched_text"].lower()) == 1


def test_match_carries_rule_metadata(regex_engine):
    found = matches_for(regex_engine, "Formule eco-responsable")
    match = found[0]
    for field in ("rule_id", "empco_article", "empco_article_full_ref",
                  "legal_explanation", "safe_template", "matched_pattern"):
        assert match[field], f"Missing metadata field {field}"
    assert "2024/825" in match["empco_article_full_ref"]
