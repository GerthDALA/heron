export function RiskBadge({ article }: { article: string }) {
  return (
    <span className="inline-block rounded-full bg-heron-teal px-3 py-1 text-xs font-semibold text-white">
      {article}
    </span>
  );
}
