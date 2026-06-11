export function ExpiryBadge({
  expiresSoon,
  validUntil,
}: {
  expiresSoon?: boolean;
  validUntil?: string | null;
}) {
  if (validUntil) {
    const expired = new Date(validUntil) < new Date();
    if (expired) {
      return (
        <span className="inline-block rounded-full bg-heron-danger-bg px-3 py-1 text-xs font-semibold text-heron-danger">
          Certificat expiré — non appliqué
        </span>
      );
    }
  }
  if (expiresSoon) {
    return (
      <span className="inline-block rounded-full bg-heron-amber-bg px-3 py-1 text-xs font-semibold text-heron-amber">
        Expire dans moins de 60 jours
      </span>
    );
  }
  return null;
}
