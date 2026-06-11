import Link from "next/link";

const cards = [
  {
    title: "Directive EmpCo (UE) 2024/825",
    line1: "En vigueur le 27 septembre 2026",
    line2: "6 articles intégrés",
    href: "/legal/EMPCO_2024_825",
  },
  {
    title: "Code de la consommation",
    line1: "Articles L. 121-2 et L. 132-2",
    line2: "En vigueur",
    href: "/legal/FR_CONSUMER_CODE",
  },
  {
    title: "Code de l'environnement",
    line1: "Articles L. 541-9-1, L. 541-9-4-1 et R. 541-223",
    line2: "En vigueur depuis 2023",
    href: "/legal/FR_ENV_CODE",
  },
];

export function LegalTransparency() {
  return (
    <section className="bg-white px-4 py-20">
      <div className="mx-auto max-w-3xl">
        <h2 className="mb-6 text-2xl font-bold">Les textes de loi, pas nos interprétations</h2>
        <div className="space-y-4 text-base leading-relaxed">
          <p>
            Chaque article cité dans un rapport Heron est extrait verbatim du Journal officiel de
            l&apos;Union européenne ou du texte officiel du Code de la consommation français.
          </p>
          <p>
            Aucun article n&apos;est rédigé, résumé ou paraphrasé par l&apos;IA. Le numéro
            d&apos;article dans votre rapport est le même numéro d&apos;article dans la loi
            publiée.
          </p>
          <p>
            Quand une nouvelle loi entre en vigueur, nous mettons à jour la base et votre prochaine
            analyse utilise le nouveau texte. Votre ancienne analyse reste archivée avec le texte
            qui était en vigueur à la date du scan.
          </p>
        </div>
        <div className="mt-8 grid gap-4 sm:grid-cols-3">
          {cards.map((card) => (
            <Link
              key={card.title}
              href={card.href}
              className="rounded-lg border border-heron-border p-4 hover:border-heron-teal"
            >
              <p className="font-semibold">{card.title}</p>
              <p className="mt-1 text-sm text-heron-muted">{card.line1}</p>
              <p className="text-sm text-heron-muted">{card.line2}</p>
              <p className="mt-2 text-sm font-semibold text-heron-teal">Lire →</p>
            </Link>
          ))}
        </div>
      </div>
    </section>
  );
}
