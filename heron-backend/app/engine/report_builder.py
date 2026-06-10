"""ReportLab Platypus PDF assembler for Heron compliance reports."""

from datetime import datetime, timezone
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

TEAL = colors.HexColor("#0F6E56")
DANGER = colors.HexColor("#A32D2D")
SAFE = colors.HexColor("#3B6D11")
DANGER_BG = colors.HexColor("#FCEBEB")
SAFE_BG = colors.HexColor("#EAF3DE")

LEGAL_DISCLAIMER = (
    "Ce rapport a été produit par Heron, un outil de détection automatique des "
    "allégations prohibées par la Directive EmpCo (UE) 2024/825. Il ne constitue pas "
    "un conseil juridique, ne certifie pas la conformité du contenu audité, et ne se "
    "substitue pas à l'analyse d'un conseil juridique qualifié. Les montants "
    "d'exposition indiqués sont les maximums théoriques calculés selon l'Article "
    "L132-2 du Code de la consommation. Heron — Radar, pas juge."
)


def _eur(amount: float) -> str:
    return f"{amount:,.2f} EUR".replace(",", " ")


class ReportBuilder:
    def __init__(self):
        base = getSampleStyleSheet()
        self.styles = {
            "logo": ParagraphStyle("logo", parent=base["Title"], fontName="Helvetica-Bold",
                                   fontSize=40, textColor=TEAL, spaceAfter=24),
            "domain": ParagraphStyle("domain", parent=base["Title"], fontName="Helvetica",
                                     fontSize=24, spaceAfter=12),
            "h1": ParagraphStyle("h1", parent=base["Heading1"], fontName="Helvetica-Bold",
                                 textColor=TEAL),
            "h2": ParagraphStyle("h2", parent=base["Heading2"], fontName="Helvetica-Bold",
                                 textColor=TEAL),
            "body": ParagraphStyle("body", parent=base["BodyText"], fontName="Helvetica",
                                   fontSize=10, leading=14),
            "exposure": ParagraphStyle("exposure", parent=base["Title"], fontName="Helvetica-Bold",
                                       fontSize=28, textColor=DANGER, spaceBefore=12, spaceAfter=12),
            "tagline": ParagraphStyle("tagline", parent=base["BodyText"], fontName="Helvetica-Oblique",
                                      fontSize=11, textColor=TEAL),
            "mono": ParagraphStyle("mono", parent=base["BodyText"], fontName="Courier",
                                   fontSize=9, textColor=colors.HexColor("#333333")),
            "original": ParagraphStyle("original", parent=base["BodyText"], fontName="Helvetica",
                                       fontSize=10, leading=14, backColor=DANGER_BG,
                                       borderPadding=6, textColor=DANGER),
            "replacement": ParagraphStyle("replacement", parent=base["BodyText"], fontName="Helvetica",
                                          fontSize=10, leading=14, backColor=SAFE_BG,
                                          borderPadding=6, textColor=SAFE),
            "legal": ParagraphStyle("legal", parent=base["BodyText"], fontName="Helvetica-Oblique",
                                    fontSize=8, textColor=colors.HexColor("#555555")),
            "bold": ParagraphStyle("bold", parent=base["BodyText"], fontName="Helvetica-Bold",
                                   fontSize=11),
        }

    def build_report(self, scan: dict, claims: list[dict], exposure_summary: dict) -> bytes:
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=2 * cm,
            rightMargin=2 * cm,
            topMargin=2 * cm,
            bottomMargin=2 * cm,
            title=f"Heron — Rapport EmpCo — {scan['domain']}",
        )
        story = []
        story += self._cover_page(scan, claims)
        story += self._executive_summary(scan, claims, exposure_summary)
        story += self._claims_detail(claims)
        story += self._disclaimer_page()
        doc.build(story)
        return buffer.getvalue()

    # Page 1 — cover
    def _cover_page(self, scan: dict, claims: list[dict]) -> list:
        scanned_at = scan.get("created_at") or datetime.now(timezone.utc).isoformat()
        return [
            Spacer(1, 3 * cm),
            Paragraph("Heron", self.styles["logo"]),
            Paragraph(scan["domain"], self.styles["domain"]),
            Paragraph(f"Date et heure du scan : {scanned_at}", self.styles["body"]),
            Spacer(1, 1 * cm),
            Paragraph(f"Allégations identifiées : {len(claims)}", self.styles["bold"]),
            Paragraph(
                f"Exposition maximale totale : {_eur(scan.get('total_exposure_eur', 0))}",
                self.styles["exposure"],
            ),
            Spacer(1, 2 * cm),
            Paragraph("Radar, pas juge. Ce rapport identifie — votre juriste valide.",
                      self.styles["tagline"]),
            PageBreak(),
        ]

    # Page 2 — executive summary
    def _executive_summary(self, scan: dict, claims: list[dict], exposure_summary: dict) -> list:
        story = [Paragraph("Synthèse exécutive", self.styles["h1"]), Spacer(1, 0.5 * cm)]

        by_article: dict[str, dict] = {}
        for claim in claims:
            entry = by_article.setdefault(claim["empco_article"], {"count": 0, "exposure": 0.0})
            entry["count"] += 1
            entry["exposure"] += claim.get("exposure_eur", 0.0)

        table_data = [["Article EmpCo", "Allégations", "Exposition maximale"]]
        for article in sorted(by_article):
            entry = by_article[article]
            table_data.append([article, str(entry["count"]), _eur(entry["exposure"])])
        table = Table(table_data, colWidths=[6 * cm, 4 * cm, 6 * cm])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), TEAL),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F4F8F6")]),
        ]))
        story += [table, Spacer(1, 0.8 * cm)]

        story.append(Paragraph("Top 3 des allégations les plus exposées", self.styles["h2"]))
        top3 = sorted(claims, key=lambda c: c.get("exposure_eur", 0), reverse=True)[:3]
        for i, claim in enumerate(top3, 1):
            story.append(Paragraph(
                f"{i}. « {claim['original_text'][:120]} » — {claim['empco_article']} — "
                f"{_eur(claim.get('exposure_eur', 0))}",
                self.styles["body"],
            ))
        story.append(Spacer(1, 0.8 * cm))

        now = datetime.now(timezone.utc)
        story.append(Paragraph(
            f"Ce rapport a été généré le {now.date().isoformat()} à "
            f"{now.strftime('%H:%M:%S')} UTC. Il constitue une trace de due diligence "
            f"attestant qu'à cette date, {scan['domain']} a identifié les allégations "
            f"à risque sur son domaine.",
            self.styles["body"],
        ))
        story.append(PageBreak())
        return story

    # Pages 3+ — one section per claim, highest exposure first
    def _claims_detail(self, claims: list[dict]) -> list:
        story = [Paragraph("Détail des allégations", self.styles["h1"]), Spacer(1, 0.4 * cm)]
        ordered = sorted(claims, key=lambda c: c.get("exposure_eur", 0), reverse=True)
        for i, claim in enumerate(ordered, 1):
            story.append(Paragraph(f"Allégation {i} — {claim['empco_article']}", self.styles["h2"]))
            story.append(Paragraph(claim["page_url"], self.styles["mono"]))
            story.append(Spacer(1, 0.2 * cm))
            story.append(Paragraph(f"Texte original : {claim['original_text']}", self.styles["original"]))
            story.append(Spacer(1, 0.2 * cm))
            story.append(Paragraph(f"Référence : {claim['empco_article_full_ref']}", self.styles["body"]))
            story.append(Paragraph(
                f"<b>Exposition maximale : {_eur(claim.get('exposure_eur', 0))}</b>",
                self.styles["bold"],
            ))
            replacement = claim.get("replacement_text")
            if replacement:
                story.append(Spacer(1, 0.2 * cm))
                story.append(Paragraph(f"Remplacement proposé : {replacement}", self.styles["replacement"]))
            story.append(Spacer(1, 0.2 * cm))
            story.append(Paragraph(
                "Remplacement proposé sur la base du texte EmpCo. Votre juriste valide avant publication.",
                self.styles["legal"],
            ))
            story.append(Spacer(1, 0.6 * cm))
        story.append(PageBreak())
        return story

    # Last page — legal disclaimer
    def _disclaimer_page(self) -> list:
        return [
            Spacer(1, 4 * cm),
            Paragraph("Avertissement juridique", self.styles["h1"]),
            Spacer(1, 0.5 * cm),
            Paragraph(LEGAL_DISCLAIMER, self.styles["body"]),
        ]
