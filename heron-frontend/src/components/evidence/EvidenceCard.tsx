import { ExpiryBadge } from "./ExpiryBadge";
import { CoverageTag } from "./CoverageTag";
import { formatDate } from "@/lib/utils";
import type { EvidenceRecord } from "@/types/api";

export function EvidenceCard({
  record,
  onDelete,
}: {
  record: EvidenceRecord;
  onDelete: (id: string) => void;
}) {
  return (
    <div className="rounded-lg border border-heron-border bg-white p-6 space-y-3">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <h3 className="font-bold">
            {record.cert_type_name} — <span className="font-mono">{record.cert_number}</span>
          </h3>
          <p className="text-sm text-heron-muted">
            {record.cert_holder} | Émis par {record.issuer_name}
          </p>
          <p className="text-sm text-heron-muted">
            Valide du {formatDate(record.issue_date)} au{" "}
            {record.valid_until ? formatDate(record.valid_until) : "Sans expiration"}
          </p>
        </div>
        <ExpiryBadge expiresSoon={record.expires_soon} validUntil={record.valid_until} />
      </div>

      <div className="space-y-1 text-sm">
        <p className="font-semibold">Couverture :</p>
        <CoverageTag coversArticle={record.covers_article} />
        {record.covers_claim_patterns && (
          <p className="text-heron-muted">
            Allégations couvertes : {record.covers_claim_patterns.split(",").join(", ")}
          </p>
        )}
      </div>

      <div className="text-sm">
        <p className="font-semibold">Scope déclaré :</p>
        <p className="text-heron-muted">{record.scope}</p>
      </div>

      <div className="flex items-center justify-between">
        <span
          className={
            record.verified === 2
              ? "rounded-full bg-heron-teal-light px-3 py-1 text-xs font-semibold text-heron-teal"
              : "rounded-full bg-heron-surface px-3 py-1 text-xs text-heron-muted"
          }
        >
          {record.verified === 2 ? "Vérifié" : "Attesté par l'utilisateur"}
        </span>
        <div className="space-x-3 text-sm">
          {record.file_url && (
            <a
              href={`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"}${record.file_url.replace("/api/v1", "")}`}
              target="_blank"
              className="text-heron-teal hover:underline"
            >
              Voir le fichier
            </a>
          )}
          <button onClick={() => onDelete(record.id)} className="text-heron-danger hover:underline">
            Supprimer
          </button>
        </div>
      </div>
    </div>
  );
}
