const steps = [
  {
    t: "T+00:00",
    title: "Vous collez votre URL",
    body: "Heron cible votre domaine. Aucune installation. Aucune intégration CMS requise.",
  },
  {
    t: "T+00:30",
    title: "Lecture des fiches produit",
    body: "Crawl4AI commence la lecture de vos fiches produit. Chaque URL est extraite, chaque texte de description est indexé.",
  },
  {
    t: "T+04:30",
    title: "Analyse réglementaire",
    body: "Le moteur regex complète son premier passage. Chaque pattern interdit par la Directive EmpCo (UE) 2024/825 — Annexe I, points 4a, 4b et 4c — est comparé contre la base de règles. Les correspondances sont logguées.",
  },
  {
    t: "T+07:00",
    title: "Calcul d'exposition",
    body: "Les calculs d'exposition sont complétés par allégation flaggée. Pour chaque correspondance : article EmpCo exact, texte statutaire extrait de la base SQLite, montant d'exposition maximale calculé selon votre CA annuel.",
  },
  {
    t: "T+09:15",
    title: "Génération des remplacements",
    body: "Claude intègre les paramètres de votre marque dans le modèle de remplacement rédigé par un spécialiste en droit de la consommation. L'IA ne touche pas au texte juridique. Elle remplit les paramètres de la marque.",
  },
  {
    t: "T+10:00",
    title: "Rapport livré",
    body: "Allégations en ordre d'exposition décroissante. Article EmpCo exact. Exposition DGCCRF calculée. Remplacement conforme prêt-à-coller. PDF avec horodatage.",
  },
];

export function ScanTimeline() {
  return (
    <section className="bg-white px-4 py-20">
      <div className="mx-auto max-w-3xl">
        <h2 className="mb-10 text-2xl font-bold">Ce qui se passe en 10 minutes</h2>
        <ol className="relative space-y-8 border-l-2 border-heron-teal-light pl-8">
          {steps.map((step) => (
            <li key={step.t} className="relative">
              <span className="absolute -left-[39px] top-1 h-3 w-3 rounded-full bg-heron-teal" />
              <p className="font-mono text-sm font-semibold text-heron-teal">{step.t}</p>
              <h3 className="mt-1 font-semibold">{step.title}</h3>
              <p className="mt-1 text-sm leading-relaxed text-heron-muted">{step.body}</p>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}
