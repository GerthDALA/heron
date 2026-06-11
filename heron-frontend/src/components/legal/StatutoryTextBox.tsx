interface StatutoryTextBoxProps {
  text: string;
  sourceReference: string;
  articleRef: string;
}

export function StatutoryTextBox({ text, sourceReference, articleRef }: StatutoryTextBoxProps) {
  return (
    <div>
      <p className="mb-1 text-xs font-medium uppercase tracking-widest text-heron-muted">
        TEXTE STATUTAIRE OFFICIEL
      </p>
      {/* Never truncated. Never transformed. The law is the law — show all of it. */}
      <div className="whitespace-pre-wrap rounded-r-md border-l-4 border-heron-teal bg-heron-surface p-4 font-mono text-sm">
        {text}
      </div>
      <p className="mt-2 text-xs text-heron-muted">
        Source : {sourceReference} — {articleRef}
      </p>
      <p className="text-xs italic text-heron-muted">Texte reproduit verbatim. Non modifié par l&apos;IA.</p>
    </div>
  );
}
