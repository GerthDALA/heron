"use client";

import { useState } from "react";
import { ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";

const faqs = [
  {
    q: "Le Green Claims Directive a été suspendu — EmpCo est aussi retardé ?",
    a: "Non. Ce sont deux textes distincts. Le Green Claims Directive est en cours d'arrêt de son processus législatif depuis mars 2024. Pas en application. La Directive EmpCo (UE) 2024/825 a été signée le 6 mars 2024 et son article 4 entre en application le 27 septembre 2026, sans modification. La confusion entre ces deux textes est la raison pour laquelle la majorité des marques françaises n'ont pas encore agi.",
  },
  {
    q: "Comment Heron identifie-t-il les allégations ?",
    a: "Un moteur regex déterministe compare chaque texte de fiche produit contre une base de règles construite sur les patterns interdits par la Directive EmpCo (UE) 2024/825, Annexe I points 4a, 4b et 4c. Aucune IA ne décide ce qui est une violation. Le même texte donne toujours le même résultat.",
  },
  {
    q: "L'IA rédige-t-elle les citations juridiques ?",
    a: "Non. Chaque numéro d'article et chaque texte statutaire dans un rapport Heron est extrait d'une base de données contenant le texte verbatim du Journal officiel. L'IA remplit uniquement les paramètres de votre marque dans des modèles de remplacement rédigés par un spécialiste en droit de la consommation.",
  },
  {
    q: "Comment l'exposition en euros est-elle calculée ?",
    a: "Selon l'Article L132-2 du Code de la consommation : l'amende peut être portée à 10 % du chiffre d'affaires moyen annuel, calculé sur les trois derniers exercices connus. Heron applique ce taux à votre CA déclaré, pondéré par la gravité de chaque catégorie EmpCo. Le montant affiché est le maximum théorique, pas une prédiction.",
  },
  {
    q: "Mes certificats COSMOS ou GOTS changent-ils le résultat ?",
    a: "Oui. Un certificat valide enregistré dans Heron réduit l'exposition calculée de 80 % (COSMOS, Ecocert, GOTS, GRS, FSC) ou de 90 % (EU Ecolabel, EN ISO 14024 Type I) sur les allégations qu'il couvre. L'allégation reste flaggée dans le rapport — elle est reclassée, pas supprimée.",
  },
  {
    q: "Heron stocke-t-il le contenu de mes fiches produit ?",
    a: "Heron ne stocke pas le contenu de vos fiches produit au-delà du traitement. Le rapport conserve uniquement les allégations flaggées, leur URL et le remplacement généré.",
  },
  {
    q: "Que vaut le rapport face à la DGCCRF ?",
    a: "Le rapport est une trace de due diligence horodatée : il prouve qu'à une date donnée, vous avez identifié les allégations à risque sur votre domaine. Il ne certifie pas la conformité et ne remplace pas votre juriste. C'est la pièce qui répond à la question « quand avez-vous su ? ».",
  },
  {
    q: "Combien de temps prend un scan ?",
    a: "Le scan freemium de votre page d'accueil prend 90 secondes. Un scan Starter (jusqu'à 500 fiches) prend moins de 10 minutes. Une vérification de copy publicitaire prend moins de 30 secondes.",
  },
  {
    q: "Heron fonctionne-t-il sur un site en anglais ou en allemand ?",
    a: "La base de règles couvre le français, l'anglais et l'allemand. Le plan Brand scanne le français et l'anglais sur le même domaine. Les remplacements sont générés dans la langue de l'allégation détectée.",
  },
  {
    q: "Que se passe-t-il si je corrige mes fiches après le scan ?",
    a: "Le plan Brand inclut un crédit de re-scan. Le second rapport, daté après vos corrections, documente que les allégations identifiées ne sont plus présentes. Les deux rapports ensemble constituent votre dossier : détection datée, correction datée.",
  },
];

export function FaqSection() {
  const [open, setOpen] = useState<number | null>(0);
  return (
    <section className="bg-heron-surface px-4 py-20">
      <div className="mx-auto max-w-3xl">
        <h2 className="mb-8 text-2xl font-bold">Questions fréquentes</h2>
        <div className="divide-y divide-heron-border rounded-lg border border-heron-border bg-white">
          {faqs.map((faq, i) => (
            <div key={faq.q}>
              <button
                onClick={() => setOpen(open === i ? null : i)}
                className="flex w-full items-center justify-between gap-4 p-4 text-left font-semibold hover:bg-heron-surface"
              >
                {faq.q}
                <ChevronDown
                  className={cn("h-4 w-4 shrink-0 transition-transform", open === i && "rotate-180")}
                />
              </button>
              {open === i && (
                <p className="px-4 pb-4 text-sm leading-relaxed text-heron-muted">{faq.a}</p>
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
