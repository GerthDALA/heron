export function CoverageTag({ coversArticle, tooltip }: { coversArticle: string; tooltip?: string }) {
  const label = coversArticle.includes("4A") || coversArticle.includes("4a")
    ? "Annexe I, Point 4a EmpCo"
    : coversArticle;
  return (
    <span
      title={tooltip}
      className="inline-block cursor-help rounded-full bg-heron-teal px-3 py-1 text-xs font-semibold text-white"
    >
      {label}
    </span>
  );
}
