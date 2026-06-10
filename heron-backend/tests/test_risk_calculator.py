"""Formula correctness for the DGCCRF exposure calculator (Article L132-2)."""

import pytest


def test_high_risk_is_full_ten_percent(risk_calculator):
    assert risk_calculator.calculate_claim_exposure(1_000_000, "high") == 100_000.00


def test_medium_risk_coefficient(risk_calculator):
    assert risk_calculator.calculate_claim_exposure(1_000_000, "medium") == 60_000.00


def test_low_risk_coefficient(risk_calculator):
    assert risk_calculator.calculate_claim_exposure(1_000_000, "low") == 30_000.00


def test_evidence_reduces_exposure_to_twenty_percent(risk_calculator):
    assert risk_calculator.calculate_claim_exposure(1_000_000, "high", has_evidence=True) == 20_000.00


def test_exposure_rounded_to_two_decimals(risk_calculator):
    exposure = risk_calculator.calculate_claim_exposure(333_333.33, "medium")
    assert exposure == round(333_333.33 * 0.10 * 0.6, 2)
    assert exposure == 20_000.0


def test_unknown_risk_level_raises(risk_calculator):
    with pytest.raises(KeyError):
        risk_calculator.calculate_claim_exposure(1_000_000, "catastrophic")


def _claims():
    return [
        {"rule_id": "VLX-EMP-001", "risk_level": "high"},
        {"rule_id": "VLX-EMP-001", "risk_level": "high"},
        {"rule_id": "VLX-EMP-005", "risk_level": "medium"},
        {"rule_id": "VLX-EMP-009", "risk_level": "low", "has_evidence": True},
    ]


def test_scan_exposure_totals(risk_calculator):
    summary = risk_calculator.calculate_scan_exposure(_claims(), 500_000)
    # high: 50_000 each (x2), medium: 30_000, low+evidence: 50_000*0.3*0.2 = 3_000
    assert summary["total_exposure_eur"] == 50_000 + 50_000 + 30_000 + 3_000
    assert summary["claims_by_risk"] == {"high": 2, "medium": 1, "low": 1}
    assert summary["most_exposed_claim"]["risk_level"] == "high"
    assert len(summary["exposure_per_claim"]) == 4
    assert all("exposure_eur" in c for c in summary["exposure_per_claim"])


def test_scan_exposure_empty(risk_calculator):
    summary = risk_calculator.calculate_scan_exposure([], 500_000)
    assert summary["total_exposure_eur"] == 0
    assert summary["most_exposed_claim"] is None


def test_risk_score_formula(risk_calculator):
    # Σ(Ei × Ci) × (1 - S_evidence) per rule:
    # VLX-EMP-001: 2 × 1.0 × 1 = 2.0; VLX-EMP-005: 1 × 0.6 × 1 = 0.6
    # VLX-EMP-009: 1 × 0.3 × 0 = 0 (evidence)
    assert risk_calculator.calculate_risk_score(_claims(), 500_000) == 2.6


def test_risk_score_zero_when_all_evidenced(risk_calculator):
    claims = [{"rule_id": "R1", "risk_level": "high", "has_evidence": True}]
    assert risk_calculator.calculate_risk_score(claims, 1_000_000) == 0.0
