const exposureRows = [
  ["EUR 5M", "EUR 500 000", "EUR 11,5M (23 allégations)"],
  ["EUR 15M", "EUR 1 500 000", "EUR 34,5M (23 allégations)"],
  ["EUR 35M", "EUR 3 500 000", "EUR 80,5M (23 allégations)"],
];

export function ProblemSection() {
  return (
    <section className="bg-heron-surface px-4 py-20">
      <div className="mx-auto max-w-3xl space-y-16">
        <div>
          <h2 className="mb-6 text-2xl font-bold">Le compte à rebours invisible</h2>
          <div className="space-y-4 text-base leading-relaxed">
            <p>
              C&apos;est il y a trois ans. Tu rédiges la fiche produit du nouveau sérum. Tu écris
              &laquo; Formule éco-responsable enrichie en vitamine C &raquo;. Ça sonne bien.
              C&apos;est vrai — la formule est naturelle. Tu valides. Tu passes à la suivante.
            </p>
            <p>
              En mars 2024, tu vois passer une alerte sur LinkedIn : le Parlement européen gèle le
              Green Claims Directive. Tu retiens ce que tout le monde retient : les contraintes sur
              les allégations vertes sont suspendues. Tu mets le dossier EmpCo de côté.
            </p>
            <p>
              Ce que tu n&apos;as pas vu : EmpCo (UE) 2024/825 et le Green Claims Directive ne sont
              pas le même texte. EmpCo a été signé le 6 mars 2024. Sa date d&apos;entrée en
              application : 27 septembre 2026. Non modifiée. Non suspendue. Non reportée.
            </p>
            <p>
              Le 28 septembre 2026, &laquo; Formule éco-responsable &raquo; sur 847 fiches produit
              est une allégation générique non documentée au sens de l&apos;Annexe I, point 4a. La
              DGCCRF a un an pour agir.
            </p>
          </div>
        </div>

        <div>
          <h2 className="mb-6 text-2xl font-bold">La paralysie de la mise en conformité</h2>
          <div className="space-y-4 text-base leading-relaxed">
            <p>
              847 fiches produit. Tu as deux rédacteurs. Tu as un juriste interne qui met trois
              semaines à répondre à un brief. Et une agence qui t&apos;a dit &laquo; on a vérifié
              le copy &raquo; — tu n&apos;as pas demandé contre quoi elle avait vérifié.
            </p>
            <p>
              Briefer le cabinet juridique : EUR 400/heure pour une analyse qui ne te donnera pas
              les remplacements, seulement une liste de risques. Mandater l&apos;agence : trois
              semaines minimum. Faire faire par ton équipe interne : deux rédacteurs, 847 fiches,
              107 jours — et ils ne savent pas non plus ce qui est légal et ce qui ne l&apos;est
              pas.
            </p>
            <p>
              Le problème de la mise en conformité n&apos;est pas la volonté. C&apos;est la
              combinaison : pas de liste exhaustive, pas de priorité par exposition financière,
              pas de remplacement prêt-à-l&apos;emploi, pas de trace prouvant que le travail a été
              fait. Heron résout les quatre.
            </p>
          </div>
        </div>

        <div>
          <h2 className="mb-6 text-2xl font-bold">L&apos;amende qu&apos;elle ne peut pas absorber</h2>
          <div className="overflow-x-auto rounded-lg border border-heron-border bg-white">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-heron-border bg-heron-surface text-left">
                  <th className="p-3 font-semibold">CA annuel</th>
                  <th className="p-3 font-semibold">Exposition max par allégation (Annexe I, 4a)</th>
                  <th className="p-3 font-semibold">Exposition totale théorique max</th>
                </tr>
              </thead>
              <tbody>
                {exposureRows.map((row) => (
                  <tr key={row[0]} className="border-b border-heron-border last:border-0">
                    {row.map((cell, i) => (
                      <td key={i} className="p-3 font-mono">{cell}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="mt-6 space-y-4 text-base leading-relaxed">
            <p className="font-semibold">Ce n&apos;est pas l&apos;amende probable. C&apos;est l&apos;amende maximale.</p>
            <p>
              Ce qui change après le 27 septembre : ce n&apos;est plus seulement une amende
              d&apos;entreprise. L&apos;Article L132-2, tel que transposé depuis EmpCo, prévoit des
              poursuites individuelles. La personne qui a approuvé la campagne. Jusqu&apos;à 5 ans
              d&apos;emprisonnement. Ce n&apos;est pas une dramatisation — c&apos;est le texte
              statutaire.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
