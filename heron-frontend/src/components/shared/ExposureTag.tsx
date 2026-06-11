import { formatEUR, cn } from "@/lib/utils";

export function ExposureTag({ amount }: { amount: number }) {
  const colour =
    amount > 500000
      ? "bg-heron-danger-bg text-heron-danger"
      : amount >= 100000
        ? "bg-heron-amber-bg text-heron-amber"
        : "bg-heron-safe-bg text-heron-safe";
  return (
    <span className={cn("inline-block rounded-full px-3 py-1 text-sm font-semibold font-mono", colour)}>
      {formatEUR(amount)}
    </span>
  );
}
