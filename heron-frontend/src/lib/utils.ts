/** Formats 1500000 as "EUR 1 500 000" (French convention). */
export function formatEUR(amount: number): string {
  const formatted = new Intl.NumberFormat("fr-FR", { maximumFractionDigits: 0 })
    .format(Math.round(amount))
    .replace(/ | /g, " ");
  return `EUR ${formatted}`;
}

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("fr-FR", {
    day: "numeric",
    month: "long",
    year: "numeric",
  });
}

export function formatTime(iso: string | null | undefined): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" });
}

export function truncateUrl(url: string, max = 48): string {
  const clean = url.replace(/^https?:\/\//, "");
  return clean.length > max ? clean.slice(0, max - 1) + "…" : clean;
}

export function cn(...classes: (string | false | null | undefined)[]): string {
  return classes.filter(Boolean).join(" ");
}
