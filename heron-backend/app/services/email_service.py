"""Resend transactional email dispatch.

All sends are best-effort: a mail failure is logged, never raised into
the scan pipeline.
"""

import logging

import resend

from app.config import get_settings

logger = logging.getLogger("heron.email")


def _send(to: str, subject: str, body: str) -> None:
    settings = get_settings()
    if not settings.RESEND_API_KEY:
        logger.info("RESEND_API_KEY not set — skipping email to %s (%s)", to, subject)
        return
    try:
        resend.api_key = settings.RESEND_API_KEY
        resend.Emails.send({
            "from": settings.HERON_FROM_EMAIL,
            "to": [to],
            "subject": subject,
            "text": body,
        })
    except Exception as exc:
        logger.warning("Email to %s failed: %s", to, exc)


def send_freemium_report(email: str, scan_results: dict) -> None:
    settings = get_settings()
    domain = scan_results["domain"]
    total = scan_results["total_claims"]
    exposure = scan_results["total_exposure_eur"]
    visible = scan_results.get("visible_claims", [])
    redacted = scan_results.get("redacted_count", 0)

    lines = [
        f"Heron a scanné la page d'accueil de {domain}.",
        "",
        f"Allégations EmpCo identifiées : {total}",
        f"Exposition maximale totale : EUR {exposure:,.2f}",
        "",
    ]
    for claim in visible:
        lines += [
            "Allégation visible :",
            f"  Texte : {claim['original_text']}",
            f"  Article : {claim['empco_article']} ({claim['empco_article_full_ref']})",
            f"  Exposition : EUR {claim['exposure_eur']:,.2f}",
            "",
        ]
    if redacted:
        lines.append(f"{redacted} autre(s) allégation(s) masquée(s) dans la version gratuite.")
    lines += [
        "",
        f"Débloquez le rapport complet et les remplacements conformes : {settings.FRONTEND_URL}/checkout",
        "",
        "Heron — Radar, pas juge.",
    ]
    subject = f"{domain} — {total} allégations EmpCo identifiées — EUR {exposure:,.2f}"
    _send(email, subject, "\n".join(lines))


def send_scan_complete(user_email: str, scan_id: str, domain: str,
                       total_claims: int, total_exposure: float) -> None:
    settings = get_settings()
    body = "\n".join([
        f"Votre scan Heron de {domain} est terminé.",
        "",
        f"Allégations identifiées : {total_claims}",
        f"Exposition maximale totale : EUR {total_exposure:,.2f}",
        "",
        f"Consultez votre rapport : {settings.FRONTEND_URL}/dashboard/scans/{scan_id}",
        "",
        "Heron — Radar, pas juge.",
    ])
    _send(user_email, f"Votre rapport Heron est prêt — {domain}", body)


def send_welcome(user_email: str) -> None:
    settings = get_settings()
    body = "\n".join([
        "Bienvenue sur Heron.",
        "",
        "Lancez votre premier scan en 3 étapes :",
        f"1. Connectez-vous : {settings.FRONTEND_URL}/login",
        "2. Saisissez votre domaine et votre chiffre d'affaires annuel.",
        "3. Lancez le scan — votre rapport arrive en quelques minutes.",
        "",
        "Heron — Radar, pas juge.",
    ])
    _send(user_email, "Heron — scanner votre premier domaine", body)
