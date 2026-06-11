import { formatEUR } from "@/lib/utils";
import type { Claim } from "@/types/api";

export function ExposureSummary({
  totalExposure,
  claims,
  redactedCount,
  ctaLabel,
  onCta,
}: {
  totalExposure: number;
  claims: Claim[];
  redactedCount?: number;
  ctaLabel?: string;
  onCta?: () => void;
}) {
  const byArticle = new Map<string, number>();
  for (const claim of claims) {
    byArticle.set(claim.empco_article, (byArticle.get(claim.empco_article) || 0) + 1);
  }
  return (
    <div className="rounded-lg border border-heron-border bg-white p-6 space-y-4 sticky top-24">
      <div>
        <p className="text-xs uppercase tracking-wide text-heron-muted">
          Exposition maximale totale
        </p>
        <p className="text-4xl font-bold text-heron-danger font-mono">{formatEUR(totalExposure)}</p>
      </div>
      <div className="space-y-1">
        {Array.from(byArticle.entries()).map(([article, count]) => (
          <div key={article} className="flex justify-between text-sm">
            <span>{article}</span>
            <span className="font-mono">{count}</span>
          </div>
        ))}
        {redactedCount !== undefined && redactedCount > 0 && (
          <div className="flex justify-between text-sm text-heron-muted">
            <span>Allégations masquées</span>
            <span className="font-mono">{redactedCount}</span>
          </div>
        )}
      </div>
      <p className="text-sm text-heron-muted">
        Le rapport complet inclut les remplacements pour chaque allégation
      </p>
      {ctaLabel && (
        <button
          onClick={onCta}
          className="w-full rounded-md bg-heron-teal px-4 py-3 font-semibold text-white hover:bg-heron-teal-dark"
        >
          {ctaLabel}
        </button>
      )}
    </div>
  );
}
