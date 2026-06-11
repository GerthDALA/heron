import { ClaimCard } from "@/components/scan/ClaimCard";
import type { Claim } from "@/types/api";

/** ClaimCard variant for ads results: shows the source label instead of a URL. */
export function AdsClaimCard({
  claim,
  sourceLabel,
  locked = false,
}: {
  claim: Claim;
  sourceLabel: string;
  locked?: boolean;
}) {
  return (
    <ClaimCard
      originalText={claim.original_text}
      sourceLabel={sourceLabel}
      article={claim.empco_article}
      articleFullRef={claim.empco_article_full_ref}
      exposureEur={claim.exposure_eur}
      replacementText={claim.replacement_text}
      locked={locked}
    />
  );
}
