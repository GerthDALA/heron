"""Evidence verifier: matches user certificates against flagged claims and
applies risk downgrades.

A downgrade never dismisses a claim — risk drops to 'low' and exposure is
reduced (minimum 10% of the original for EU Ecolabel / ISO 14024 Type I,
20% for other certifications), but the claim stays in the report with the
certificate that justified the reduction.
"""

import logging
import uuid
from datetime import datetime, timezone

import aiosqlite

logger = logging.getLogger("heron.evidence")


class EvidenceVerifier:
    # Exposure multipliers after downgrade, by certification type.
    DOWNGRADE_MULTIPLIERS = {
        "EU_ECOLABEL": 0.1,  # recognised excellent environmental performance
        "ISO14024": 0.1,
    }
    DEFAULT_MULTIPLIER = 0.2  # COSMOS, ECOCERT, GOTS, GRS, FSC — strong evidence

    async def get_user_evidence(self, user_id: str, db: aiosqlite.Connection) -> list[dict]:
        """All non-expired evidence records for the user, joined with cert type."""
        cursor = await db.execute(
            """SELECT e.*, ct.name AS cert_type_name, ct.covers_article,
                      ct.covers_claim_patterns AS type_claim_patterns
               FROM evidence_records e
               JOIN certification_types ct ON ct.id = e.cert_type_id
               WHERE e.user_id = ?
                 AND (e.valid_until IS NULL OR e.valid_until > date('now'))""",
            (user_id,),
        )
        return [dict(row) for row in await cursor.fetchall()]

    @staticmethod
    def _keywords(evidence: dict) -> list[str]:
        merged = ",".join(
            filter(None, [evidence.get("covers_claim_patterns"), evidence.get("type_claim_patterns")])
        )
        return [k.strip().lower() for k in merged.split(",") if k.strip()]

    @staticmethod
    def _covered_articles(evidence: dict) -> set[str]:
        return {a.strip() for a in (evidence.get("covers_article") or "").split(",") if a.strip()}

    def matches_claim(
        self,
        evidence: dict,
        claim_text: str,
        claim_article_ids: set[str],
    ) -> bool:
        """True only if the cert covers the claim's legal article AND one of
        its coverage keywords appears in the claim text."""
        if not (self._covered_articles(evidence) & claim_article_ids):
            return False
        text = claim_text.lower()
        return any(keyword in text for keyword in self._keywords(evidence))

    def calculate_downgraded_exposure(self, original_exposure: float, cert_type: str) -> float:
        multiplier = self.DOWNGRADE_MULTIPLIERS.get(cert_type, self.DEFAULT_MULTIPLIER)
        return round(original_exposure * multiplier, 2)

    async def _rule_article_map(self, db: aiosqlite.Connection) -> dict[str, set[str]]:
        cursor = await db.execute("SELECT id, linked_article_ids FROM rules")
        rows = await cursor.fetchall()
        return {
            row["id"]: {a.strip() for a in (row["linked_article_ids"] or "").split(",") if a.strip()}
            for row in rows
        }

    async def apply_downgrades(
        self,
        claims: list[dict],
        user_id: str | None,
        db: aiosqlite.Connection,
    ) -> list[dict]:
        """Downgrade high/medium claims covered by valid user evidence.

        Mutates claim dicts (risk_level, exposure_eur, downgrade metadata),
        updates persisted claim rows, and writes evidence_claim_links audit
        records. Returns the updated claims list.
        """
        if not user_id:
            return claims
        evidence_list = await self.get_user_evidence(user_id, db)
        if not evidence_list:
            return claims
        rule_articles = await self._rule_article_map(db)

        for claim in claims:
            if claim["risk_level"] not in ("high", "medium"):
                continue
            claim_articles = rule_articles.get(claim["rule_id"], set())
            claim_text = claim.get("original_text") or claim.get("matched_text", "")
            for evidence in evidence_list:
                if not self.matches_claim(evidence, claim_text, claim_articles):
                    continue
                original_risk = claim["risk_level"]
                original_exposure = claim["exposure_eur"]
                claim["risk_level"] = "low"
                claim["exposure_eur"] = self.calculate_downgraded_exposure(
                    original_exposure, evidence["cert_type_id"]
                )
                claim["evidence_id"] = evidence["id"]
                claim["downgrade_note"] = (
                    f"Risque réduit : certificat {evidence['cert_type_name']} "
                    f"n°{evidence['cert_number']} couvre cette allégation"
                )
                applied_at = datetime.now(timezone.utc).isoformat()
                await db.execute(
                    """INSERT INTO evidence_claim_links
                       (id, claim_id, evidence_id, original_risk_level,
                        downgraded_risk_level, downgrade_reason, applied_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (
                        str(uuid.uuid4()), claim["id"], evidence["id"],
                        original_risk, "low", claim["downgrade_note"], applied_at,
                    ),
                )
                await db.execute(
                    "UPDATE claims SET risk_level = 'low', exposure_eur = ? WHERE id = ?",
                    (claim["exposure_eur"], claim["id"]),
                )
                logger.info(
                    "Claim %s downgraded %s→low via %s", claim["id"],
                    original_risk, evidence["cert_type_id"],
                )
                break  # first matching certificate wins
        await db.commit()
        return claims
