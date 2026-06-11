import { StatutoryTextBox } from "./StatutoryTextBox";
import type { LegalArticle } from "@/types/api";

export function ArticleBlock({
  article,
  sourceReference,
}: {
  article: LegalArticle;
  sourceReference: string;
}) {
  return (
    <article className="border-b border-heron-border py-8 last:border-0">
      <h3 className="text-lg font-bold">
        {article.article_ref}
        {article.article_title ? ` — ${article.article_title}` : ""}
      </h3>
      <p className="mt-1 text-sm text-heron-muted">{article.summary}</p>
      {article.verification_status !== "verified_source" && (
        <p className="mt-2 inline-block rounded-full bg-heron-amber-bg px-3 py-1 text-xs text-heron-amber">
          Texte en attente de vérification contre la source officielle
        </p>
      )}
      <div className="mt-4">
        <StatutoryTextBox
          text={article.full_text}
          sourceReference={sourceReference}
          articleRef={article.article_ref}
        />
      </div>
      <div className="mt-4 space-y-3 text-sm">
        <div>
          <p className="font-semibold">Ce que cela interdit :</p>
          <p className="text-heron-muted">{article.prohibited_behaviour}</p>
        </div>
        <div>
          <p className="font-semibold">Preuves pouvant réduire le risque :</p>
          <p className="text-heron-muted">
            {article.evidence_required || "Aucune — cette mention doit être supprimée"}
          </p>
        </div>
      </div>
    </article>
  );
}
