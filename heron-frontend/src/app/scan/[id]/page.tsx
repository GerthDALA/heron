"use client";

import Link from "next/link";
import { Navbar } from "@/components/layout/Navbar";
import { Footer } from "@/components/layout/Footer";
import { ClaimCard } from "@/components/scan/ClaimCard";
import { ExposureSummary } from "@/components/scan/ExposureSummary";
import { RadarNotJudge } from "@/components/shared/RadarNotJudge";
import { useScanStore } from "@/store/scan";
import { formatEUR } from "@/lib/utils";

export default function FreemiumResultsPage() {
  const result = useScanStore((s) => s.freemiumResult);

  if (!result) {
    return (
      <>
        <Navbar />
        <main className="mx-auto max-w-xl px-4 py-24 text-center">
          <p className="text-lg">
            Ce résultat de scan n&apos;est plus en mémoire. Les résultats freemium sont aussi
            envoyés par email à l&apos;adresse fournie lors du scan.
          </p>
          <Link
            href="/scan"
            className="mt-6 inline-block rounded-md bg-heron-teal px-6 py-3 font-semibold text-white hover:bg-heron-teal-dark"
          >
            Lancer un nouveau scan
          </Link>
        </main>
        <Footer />
      </>
    );
  }

  const totalClaims = result.visible_claims.length + result.redacted_count;
  return (
    <>
      <Navbar />
      <main className="mx-auto max-w-6xl px-4 py-12">
        <h1 className="text-2xl font-bold leading-snug">
          Heron a scanné {result.domain} ce matin.
          <br />
          {totalClaims} allégations EmpCo identifiées. Exposition totale estimée :{" "}
          <span className="text-heron-danger">{formatEUR(result.total_exposure_eur)}</span>.
        </h1>

        <div className="mt-10 grid gap-8 lg:grid-cols-[1fr_320px]">
          <div className="space-y-6">
            {result.visible_claims.map((claim) => (
              <ClaimCard
                key={claim.id}
                originalText={claim.original_text}
                detectedOn={claim.page_url}
                article={claim.empco_article}
                articleFullRef={claim.empco_article_full_ref}
                exposureEur={claim.exposure_eur}
                replacementText={claim.replacement_text}
                locked={claim.replacement_text === null}
              />
            ))}
            {result.redacted_count > 0 && (
              <div className="rounded-lg bg-heron-amber-bg p-4 text-sm font-medium text-heron-amber">
                {result.redacted_count} allégations supplémentaires identifiées sur vos fiches
                produit. Exposition totale : {formatEUR(result.total_exposure_eur)}.
              </div>
            )}
            {Array.from({ length: Math.min(result.redacted_count, 3) }).map((_, i) => (
              <ClaimCard
                key={`locked-${i}`}
                originalText="Allégation masquée — visible dans le rapport complet"
                article="EmpCo"
                exposureEur={0}
                locked
              />
            ))}
            <RadarNotJudge />
          </div>
          <div>
            <ExposureSummary
              totalExposure={result.total_exposure_eur}
              claims={result.visible_claims}
              redactedCount={result.redacted_count}
              ctaLabel={`Voir les ${totalClaims} remplacements — EUR 290`}
              onCta={() => (window.location.href = "/auth/register")}
            />
          </div>
        </div>

        <section className="mt-16 rounded-lg bg-heron-surface p-8 text-center">
          <h2 className="text-2xl font-bold">
            Votre équipe peut corriger ces {totalClaims} allégations ce soir.
          </h2>
          <div className="mt-6 flex flex-col justify-center gap-4 sm:flex-row">
            <Link
              href="/auth/register"
              className="rounded-md bg-heron-teal px-6 py-3 font-semibold text-white hover:bg-heron-teal-dark"
            >
              Starter — EUR 290
            </Link>
            <Link
              href="/auth/register"
              className="rounded-md border border-heron-teal px-6 py-3 font-semibold text-heron-teal hover:bg-heron-teal-light"
            >
              Brand — EUR 890
            </Link>
          </div>
          <p className="mt-3 text-sm text-heron-muted">
            Starter : 500 fiches. Brand : 3 000 fiches + multilingue + re-scan.
          </p>
        </section>
      </main>
      <Footer />
    </>
  );
}
