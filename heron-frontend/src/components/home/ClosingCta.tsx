import Link from "next/link";

export function ClosingCta() {
  return (
    <section className="bg-heron-teal px-4 py-20 text-white">
      <div className="mx-auto grid max-w-5xl gap-12 md:grid-cols-2">
        <div>
          <p className="text-lg leading-relaxed">
            Vous avez la liste. Vous avez les remplacements. Vous avez l&apos;ordre de priorité par
            exposition financière décroissante. Votre équipe peut commencer ce soir. Le scan prend
            moins de 10 minutes. Le rapport arrive avant que vous ayez fini votre café.
          </p>
          <Link
            href="/scan"
            className="mt-6 inline-block rounded-md bg-white px-6 py-3 font-semibold text-heron-teal hover:bg-heron-teal-light"
          >
            Scanner ma homepage
          </Link>
        </div>
        <div>
          <p className="text-lg leading-relaxed">
            La question n&apos;est pas de savoir si la DGCCRF contrôlera votre marque. C&apos;est
            quand. Heron vous donne le tampon de date qui prouve que vous avez agi — avant le 27
            septembre, pas après. Ce rapport répond à la question &laquo; quand avez-vous su ?
            &raquo; avec la date exacte à laquelle vous avez lancé le scan.
          </p>
          <Link
            href="/scan"
            className="mt-6 inline-block rounded-md border border-white px-6 py-3 font-semibold text-white hover:bg-heron-teal-dark"
          >
            Télécharger la trace de due diligence
          </Link>
        </div>
      </div>
    </section>
  );
}
