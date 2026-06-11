import Link from "next/link";
import { Countdown } from "@/components/shared/Countdown";

export function HeroSection() {
  return (
    <section className="bg-white px-4 pb-20 pt-[120px]">
      <div className="mx-auto max-w-[800px] text-center">
        <p className="mb-6 text-sm">
          <Countdown />
        </p>
        <h1 className="text-4xl font-bold leading-tight md:text-5xl">
          27 septembre 2026. Chaque allégation environnementale sur vos fiches produit.
          L&apos;article EmpCo exact. L&apos;exposition DGCCRF en euros. Le remplacement
          prêt-à-coller. En moins de 10 minutes.
        </h1>
        <p className="mx-auto mt-6 max-w-[640px] text-lg text-heron-muted">
          Heron lit chaque fiche produit de votre domaine, identifie chaque allégation interdite
          par la Directive EmpCo (UE) 2024/825, calcule l&apos;exposition maximale DGCCRF par
          allégation selon l&apos;Article L132-2 du Code de la consommation, et livre le
          remplacement conforme dans le registre de votre marque — prêt à coller dans votre CMS.
        </p>
        <p className="mt-2 text-sm text-heron-muted">
          Pour les marques françaises gérant plus de 300 fiches produit avec des allégations
          environnementales. Avant le 27 septembre 2026.
        </p>
        <div className="mt-8">
          <Link
            href="/scan"
            className="inline-block w-full rounded-md bg-heron-teal px-8 py-4 text-lg font-semibold text-white hover:bg-heron-teal-dark sm:w-auto"
          >
            Scanner ma homepage
          </Link>
          <p className="mt-2 text-xs text-heron-muted">
            Scan gratuit de votre page d&apos;accueil. Résultats en 90 secondes.
          </p>
          <p className="mt-4 text-sm text-heron-muted">
            Vous avez une annonce, un email ou une transcription à vérifier ?
          </p>
          <Link href="/scan/ads" className="text-sm font-semibold text-heron-teal hover:underline">
            Analyser du copy publicitaire →
          </Link>
        </div>
        <div className="mt-12 rounded-lg bg-heron-surface px-6 py-8">
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-3">
            {[
              { number: "14", label: "marques scannées en bêta" },
              { number: "23", label: "allégations en moyenne" },
              { number: "EUR 340 000", label: "exposition moyenne" },
            ].map((stat) => (
              <div key={stat.label}>
                <p className="text-2xl font-bold text-heron-teal">{stat.number}</p>
                <p className="text-sm text-heron-muted">{stat.label}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
