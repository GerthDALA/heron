"""DGCCRF financial exposure formula (Article L132-2, Code de la consommation).

Zero LLM involvement in this file. Exposure = 10% of annual revenue,
weighted by EmpCo severity, reduced to 20% when certification evidence
covers the claim. Exact arithmetic, never estimated.
"""

DGCCRF_REVENUE_SHARE = 0.10  # Article L132-2: up to 10% of annual revenue
EVIDENCE_MITIGATION = 0.2    # documented evidence reduces exposure to 20%


class RiskCalculator:
    SEVERITY_COEFFICIENTS = {
        "high": 1.0,    # Article 4a generic claims — full 10% exposure
        "medium": 0.6,  # Article 4c single-aspect claims
        "low": 0.3,     # Minor violations
    }

    def calculate_claim_exposure(
        self,
        annual_revenue_eur: float,
        risk_level: str,
        has_evidence: bool = False,
    ) -> float:
        coefficient = self.SEVERITY_COEFFICIENTS[risk_level]
        exposure = (
            annual_revenue_eur
            * DGCCRF_REVENUE_SHARE
            * coefficient
            * (EVIDENCE_MITIGATION if has_evidence else 1.0)
        )
        return round(exposure, 2)

    def calculate_scan_exposure(
        self,
        claims: list[dict],
        annual_revenue_eur: float,
    ) -> dict:
        claims_by_risk = {"high": 0, "medium": 0, "low": 0}
        exposure_per_claim: list[dict] = []
        total = 0.0
        most_exposed: dict | None = None

        for claim in claims:
            exposure = self.calculate_claim_exposure(
                annual_revenue_eur,
                claim["risk_level"],
                has_evidence=bool(claim.get("has_evidence")),
            )
            claims_by_risk[claim["risk_level"]] += 1
            total += exposure
            enriched = {**claim, "exposure_eur": exposure}
            exposure_per_claim.append(enriched)
            if most_exposed is None or exposure > most_exposed["exposure_eur"]:
                most_exposed = enriched

        return {
            "total_exposure_eur": round(total, 2),
            "claims_by_risk": claims_by_risk,
            "most_exposed_claim": most_exposed,
            "exposure_per_claim": exposure_per_claim,
        }

    def calculate_risk_score(
        self,
        claims: list[dict],
        annual_revenue_eur: float,
    ) -> float:
        """Risk score: Σ(Ei × Ci) × (1 - S_evidence).

        Ei = frequency of match type i (per rule), Ci = severity coefficient,
        S_evidence = 1 if cert evidence covers the claim type, 0 otherwise.
        """
        score = 0.0
        frequency: dict[str, dict] = {}
        for claim in claims:
            key = claim["rule_id"]
            entry = frequency.setdefault(
                key,
                {"count": 0, "risk_level": claim["risk_level"],
                 "has_evidence": bool(claim.get("has_evidence"))},
            )
            entry["count"] += 1

        for entry in frequency.values():
            ci = self.SEVERITY_COEFFICIENTS[entry["risk_level"]]
            s_evidence = 1.0 if entry["has_evidence"] else 0.0
            score += entry["count"] * ci * (1.0 - s_evidence)
        return round(score, 4)
