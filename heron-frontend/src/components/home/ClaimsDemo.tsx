import { ClaimCard } from "@/components/scan/ClaimCard";

export function ClaimsDemo() {
  return (
    <section className="bg-heron-surface px-4 py-20">
      <div className="mx-auto max-w-3xl">
        <h2 className="mb-2 text-2xl font-bold">Ce que Heron trouve sur votre domaine</h2>
        <p className="mb-8 text-sm text-heron-muted">
          Cette section est une démonstration du produit. Chaque ligne est exactement le format
          d&apos;un rapport Heron réel.
        </p>
        <div className="space-y-6">
          <ClaimCard
            originalText="Formule éco-responsable"
            detectedOn="/serum-anti-age, /creme-hydratante et 845 autres fiches"
            article="Annexe I, Point 4a"
            articleFullRef="Annexe I, point 4a — Directive EmpCo (UE) 2024/825"
            articleDescription="Allégation environnementale générique sans performance reconnue documentée"
            exposureEur={1500000}
            exposureLabel="Exposition (CA EUR 15M) : EUR 1 500 000 max. par fiche (Art. L132-2 Code conso.)"
            replacementText="Formule à base de [ingrédient spécifique], dont les propriétés de [bénéfice documenté] sont certifiées dans notre dossier technique interne. [Optionnel : certification Ecocert / COSMOS si applicable]"
          />
          <ClaimCard
            originalText="Carbon neutral by 2030"
            detectedOn="/about, /engagements, /marque"
            article="Annexe I, Point 4c"
            articleFullRef="Annexe I, point 4c et Article 6(2)(d) — Directive EmpCo (UE) 2024/825"
            articleDescription="Affirmation climatique prospective sans plan vérifié indépendamment et fondé sur la science"
            exposureEur={1500000}
            exposureLabel="Exposition (CA EUR 15M) : EUR 1 500 000 max. par page (Art. L132-2 Code conso.)"
            replacementText="Dans le cadre de notre engagement environnemental, nous réduisons nos émissions de [X]% depuis [année] conformément à notre plan de transition vérifié par [organisme tiers]. Notre objectif 2030 est détaillé dans notre rapport de durabilité disponible ici."
          />
          <ClaimCard
            originalText="Notre collection la plus durable à ce jour"
            detectedOn="/collection-automne, /nouvelles-arrivees"
            article="Annexe I, Point 4b"
            articleFullRef="Annexe I, point 4b — Directive EmpCo (UE) 2024/825"
            articleDescription="Allégation sur un seul aspect présentée comme bénéfice environnemental global du produit"
            exposureEur={1500000}
            exposureLabel="Exposition (CA EUR 15M) : EUR 1 500 000 max. par page (Art. L132-2 Code conso.)"
            replacementText="Notre collection automne intègre [X]% de matières certifiées [spécification] — notre taux le plus élevé à ce jour pour cette catégorie de produit. [Spécificité documentée uniquement — pas de « plus durable » sans critère mesurable.]"
          />
        </div>
      </div>
    </section>
  );
}
