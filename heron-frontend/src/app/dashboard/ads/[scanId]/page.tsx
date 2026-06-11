"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Download } from "lucide-react";
import { AdsClaimCard } from "@/components/ads/AdsClaimCard";
import { RadarNotJudge } from "@/components/shared/RadarNotJudge";
import { heronApi } from "@/lib/api";
import { formatEUR, formatDate } from "@/lib/utils";
import { INPUT_TYPES, type InputType } from "@/lib/constants";
import type { AdsScanDetail } from "@/types/api";

export default function DashboardAdsResultPage() {
  const { scanId } = useParams<{ scanId: string }>();
  const [detail, setDetail] = useState<AdsScanDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    heronApi
      .getAdsScan(scanId)
      .then((res) => setDetail(res.data))
      .catch(() =>
        setError(`L'analyse ${scanId} est introuvable ou appartient à un autre compte.`)
      );
  }, [scanId]);

  const downloadPdf = async () => {
    const res = await heronApi.downloadAdsPdf(scanId);
    const url = URL.createObjectURL(res.data);
    const a = document.createElement("a");
    a.href = url;
    a.download = `heron-ads-${scanId}.pdf`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (error) return <p className="rounded-md bg-heron-danger-bg p-4 text-heron-danger">{error}</p>;
  if (!detail) return <p className="text-heron-muted">Chargement…</p>;

  const { scan, claims } = detail;
  const typeLabel = INPUT_TYPES[(scan.input_type as InputType) || "other"]?.label || scan.input_type;
  const sourceLabel = scan.input_title || typeLabel;
  const plural = scan.total_claims > 1 ? "s" : "";

  return (
    <div className="mx-auto max-w-3xl space-y-8">
      <header className="flex flex-wrap items-start justify-between gap-4">
        <h1 className="text-2xl font-bold leading-snug">
          {scan.total_claims} allégation{plural} EmpCo identifiée{plural} dans votre{" "}
          {typeLabel.toLowerCase()}.
          <br />
          Exposition maximale totale :{" "}
          <span className="text-heron-danger">{formatEUR(scan.total_exposure_eur)}</span>.
        </h1>
        <button
          onClick={downloadPdf}
          className="flex items-center gap-2 rounded-md bg-heron-teal px-5 py-3 text-sm font-semibold text-white hover:bg-heron-teal-dark"
        >
          <Download className="h-4 w-4" />
          Télécharger le rapport — copy publicitaire
        </button>
      </header>

      <p className="text-sm text-heron-muted">
        {scan.input_title ? `${scan.input_title} • ` : ""}
        {typeLabel} • {formatDate(scan.created_at)}
      </p>

      {scan.total_claims === 0 ? (
        <div className="rounded-lg border border-heron-border bg-white p-8">
          <p className="font-semibold">Aucune allégation EmpCo identifiée dans ce texte.</p>
          <p className="mt-3 text-sm text-heron-muted">
            Heron n&apos;a trouvé aucun pattern correspondant aux interdictions Annexe I points 4a,
            4b, 4c ou Article 6(2)(d) de la Directive EmpCo (UE) 2024/825 dans ce texte.
          </p>
          <p className="mt-3 text-sm text-heron-muted">
            Cela ne constitue pas une certification de conformité. Votre juriste valide que le
            contenu est conforme avant diffusion.
          </p>
        </div>
      ) : (
        <div className="space-y-6">
          {claims.map((claim) => (
            <AdsClaimCard key={claim.id} claim={claim} sourceLabel={sourceLabel} />
          ))}
        </div>
      )}

      <RadarNotJudge />
    </div>
  );
}
