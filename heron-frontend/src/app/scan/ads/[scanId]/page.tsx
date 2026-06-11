"use client";

import Link from "next/link";
import { Navbar } from "@/components/layout/Navbar";
import { Footer } from "@/components/layout/Footer";
import { AdsClaimCard } from "@/components/ads/AdsClaimCard";
import { RadarNotJudge } from "@/components/shared/RadarNotJudge";
import { useScanStore } from "@/store/scan";
import { formatEUR } from "@/lib/utils";
import { INPUT_TYPES, type InputType } from "@/lib/constants";

export default function AdsFreemiumResultsPage() {
  const { adsResult, adsInputText } = useScanStore();

  if (!adsResult) {
    return (
      <>
        <Navbar />
        <main className="mx-auto max-w-xl px-4 py-24 text-center">
          <p className="text-lg">
            Ce résultat d&apos;analyse n&apos;est plus en mémoire. Les résultats freemium sont
            aussi envoyés par email à l&apos;adresse fournie.
          </p>
          <Link
            href="/scan/ads"
            className="mt-6 inline-block rounded-md bg-heron-teal px-6 py-3 font-semibold text-white hover:bg-heron-teal-dark"
          >
            Analyser un nouveau texte
          </Link>
        </main>
        <Footer />
      </>
    );
  }

  const first = adsResult.visible_claims[0];
  const sourceLabel = first ? "Texte soumis" : "—";
  const plural = adsResult.total_claims > 1 ? "s" : "";

  return (
    <>
      <Navbar />
      <main className="mx-auto max-w-3xl px-4 py-12 space-y-8">
        <h1 className="text-2xl font-bold leading-snug">
          {adsResult.total_claims} allégation{plural} EmpCo identifiée{plural} dans votre{" "}
          {INPUT_TYPES[(first ? "ad_copy" : "ad_copy") as InputType].label.toLowerCase()}.
          <br />
          Exposition maximale totale :{" "}
          <span className="text-heron-danger">{formatEUR(adsResult.total_exposure_eur)}</span>.
        </h1>

        {adsInputText && (
          <div>
            <p className="text-xs uppercase tracking-wide text-heron-muted">Texte analysé</p>
            <div className="mt-1 max-h-[120px] overflow-y-auto rounded-md border border-heron-border bg-heron-surface p-3 font-mono text-sm">
              {adsInputText}
            </div>
            <p className="mt-1 text-xs text-heron-muted">{adsInputText.length} caractères</p>
          </div>
        )}

        {adsResult.total_claims === 0 ? (
          <div className="rounded-lg border border-heron-border bg-white p-8">
            <p className="font-semibold">Aucune allégation EmpCo identifiée dans ce texte.</p>
            <p className="mt-3 text-sm text-heron-muted">
              Heron n&apos;a trouvé aucun pattern correspondant aux interdictions Annexe I points
              4a, 4b, 4c ou Article 6(2)(d) de la Directive EmpCo (UE) 2024/825 dans ce texte.
            </p>
            <p className="mt-3 text-sm text-heron-muted">
              Cela ne constitue pas une certification de conformité. Votre juriste valide que le
              contenu est conforme avant diffusion.
            </p>
          </div>
        ) : (
          <div className="space-y-6">
            {adsResult.visible_claims.map((claim) => (
              <AdsClaimCard key={claim.id} claim={claim} sourceLabel={sourceLabel} />
            ))}
            {adsResult.redacted_count > 0 && (
              <div className="rounded-lg bg-heron-amber-bg p-4 text-sm font-medium text-heron-amber">
                {adsResult.redacted_count} allégation{adsResult.redacted_count > 1 ? "s" : ""}{" "}
                supplémentaire{adsResult.redacted_count > 1 ? "s" : ""} identifiée
                {adsResult.redacted_count > 1 ? "s" : ""} dans ce texte. Les remplacements sont
                disponibles dans le rapport complet.
              </div>
            )}
            <div className="rounded-lg bg-heron-surface p-6 text-center">
              <Link
                href="/auth/register"
                className="inline-block rounded-md bg-heron-teal px-6 py-3 font-semibold text-white hover:bg-heron-teal-dark"
              >
                Voir tous les remplacements — Starter EUR 290
              </Link>
            </div>
          </div>
        )}

        <RadarNotJudge />
      </main>
      <Footer />
    </>
  );
}
