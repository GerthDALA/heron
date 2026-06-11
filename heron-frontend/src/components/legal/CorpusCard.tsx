import Link from "next/link";
import { formatDate, cn } from "@/lib/utils";
import type { LegalCorpus } from "@/types/api";

export function CorpusCard({ corpus }: { corpus: LegalCorpus }) {
  return (
    <div className="rounded-lg border border-heron-border bg-white p-6">
      <div className="flex gap-2">
        <span
          className={cn(
            "rounded-full px-3 py-1 text-xs font-semibold",
            corpus.jurisdiction === "EU"
              ? "bg-heron-teal-light text-heron-teal"
              : "bg-blue-100 text-blue-800"
          )}
        >
          {corpus.jurisdiction}
        </span>
        <span className="rounded-full bg-heron-surface px-3 py-1 text-xs text-heron-muted">
          {corpus.status === "active" ? "En vigueur" : corpus.status}
        </span>
      </div>
      <h2 className="mt-3 font-semibold leading-snug">{corpus.full_name}</h2>
      {corpus.official_reference && (
        <p className="mt-2 text-sm text-heron-muted">Référence : {corpus.official_reference}</p>
      )}
      <p className="text-sm text-heron-muted">
        Date d&apos;application : {formatDate(corpus.application_date)}
      </p>
      <p className="text-sm text-heron-muted">{corpus.article_count} articles disponibles</p>
      <Link
        href={`/legal/${corpus.id}`}
        className="mt-4 inline-block rounded-md border border-heron-teal px-4 py-2 text-sm font-semibold text-heron-teal hover:bg-heron-teal-light"
      >
        Lire le texte complet →
      </Link>
    </div>
  );
}
