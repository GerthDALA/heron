"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Download } from "lucide-react";
import { heronApi } from "@/lib/api";
import { ClaimCard } from "@/components/scan/ClaimCard";
import { RadarNotJudge } from "@/components/shared/RadarNotJudge";
import { formatEUR, formatDate, formatTime } from "@/lib/utils";
import type { Report, Claim } from "@/types/api";

interface DowngradedClaim extends Claim {
  downgrade_note?: string | null;
  original_risk_level?: string;
}

export default function FullReportPage() {
  const { scanId } = useParams<{ scanId: string }>();
  const [report, setReport] = useState<Report | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    heronApi
      .getReport(scanId)
      .then((res) => setReport(res.data))
      .catch((err) => {
        setError(
          err.response?.status === 403
            ? "Ce rapport appartient à un autre compte."
            : `Le rapport ${scanId} est introuvable. Vérifiez l'identifiant du scan dans votre tableau de bord.`
        );
      });
  }, [scanId]);

  const downloadPdf = async () => {
    const res = await heronApi.downloadPdf(scanId);
    const url = URL.createObjectURL(res.data);
    const a = document.createElement("a");
    a.href = url;
    a.download = `heron-${scanId}.pdf`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (error) return <p className="rounded-md bg-heron-danger-bg p-4 text-heron-danger">{error}</p>;
  if (!report) return <p className="text-heron-muted">Chargement du rapport…</p>;

  const claims = report.claims as DowngradedClaim[];
  const downgraded = claims.filter((c) => c.downgrade_note);
  const generated = report.generated_at || new Date().toISOString();

  return (
    <div className="mx-auto max-w-4xl space-y-8">
      <header className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">Rapport Heron — {report.domain}</h1>
          <p className="text-heron-muted">
            Généré le {formatDate(generated)} à {formatTime(generated)}
          </p>
          <p className="mt-1 font-semibold">
            {report.total_claims} allégations identifiées — Exposition maximale totale :{" "}
            <span className="text-heron-danger">{formatEUR(report.total_exposure_eur)}</span>
          </p>
        </div>
        <button
          onClick={downloadPdf}
          className="flex items-center gap-2 rounded-md bg-heron-teal px-5 py-3 font-semibold text-white hover:bg-heron-teal-dark"
        >
          <Download className="h-4 w-4" />
          Télécharger le rapport PDF
        </button>
      </header>

      <div className="rounded-lg bg-heron-teal-light p-5 text-sm">
        Ce rapport a été généré le {formatDate(generated)} à {formatTime(generated)}. Il constitue
        une trace de due diligence attestant qu&apos;à cette date, {report.domain} a identifié les
        allégations à risque sur son domaine.
      </div>

      {downgraded.length > 0 && (
        <section className="rounded-lg border border-heron-border bg-white p-6">
          <h2 className="text-lg font-bold">Réductions de risque appliquées</h2>
          <p className="mt-1 text-sm text-heron-muted">
            {downgraded.length} allégation{downgraded.length > 1 ? "s ont" : " a"} vu leur
            exposition réduite grâce à vos certificats.
          </p>
          <table className="mt-4 w-full text-sm">
            <thead>
              <tr className="border-b border-heron-border text-left">
                {["Allégation", "Certificat appliqué", "Risque après réduction", "Exposition"].map((h) => (
                  <th key={h} className="p-2 font-semibold">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {downgraded.map((claim) => (
                <tr key={claim.id} className="border-b border-heron-border last:border-0">
                  <td className="p-2 font-mono">&laquo; {claim.original_text} &raquo;</td>
                  <td className="p-2">{claim.downgrade_note}</td>
                  <td className="p-2 text-heron-safe">Faible</td>
                  <td className="p-2 font-mono">{formatEUR(claim.exposure_eur)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="mt-3 text-xs text-heron-muted">
            L&apos;exposition réduite est calculée sur la base du périmètre déclaré de votre
            certificat. Votre juriste confirme que le périmètre couvre bien les allégations
            concernées.
          </p>
        </section>
      )}

      <div className="space-y-6">
        {claims.map((claim) => (
          <ClaimCard
            key={claim.id}
            originalText={claim.original_text}
            detectedOn={claim.page_url}
            article={claim.empco_article}
            articleFullRef={claim.empco_article_full_ref}
            exposureEur={claim.exposure_eur}
            replacementText={claim.replacement_text}
            downgradeNote={claim.downgrade_note}
          />
        ))}
      </div>

      <RadarNotJudge />
    </div>
  );
}
