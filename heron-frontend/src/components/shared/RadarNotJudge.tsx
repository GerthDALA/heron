export function RadarNotJudge() {
  return (
    <section className="rounded-lg bg-heron-teal-light p-8 my-8">
      <div className="grid gap-8 md:grid-cols-2">
        <div>
          <h3 className="text-sm font-bold uppercase tracking-widest text-heron-teal mb-4">
            CE QUE HERON FAIT
          </h3>
          <p className="text-base leading-relaxed">
            Heron identifie les allégations qui correspondent aux patterns interdits par la
            Directive EmpCo (UE) 2024/825, Annexe I points 4a, 4b et 4c. Heron calcule
            l&apos;exposition financière maximale selon l&apos;Article L132-2 du Code de la
            consommation. Heron génère un remplacement conforme dans le registre de votre marque.
            Heron délivre un rapport PDF avec horodatage.
          </p>
        </div>
        <div>
          <h3 className="text-sm font-bold uppercase tracking-widest text-heron-teal mb-4">
            CE QUE HERON NE FAIT PAS
          </h3>
          <p className="text-base leading-relaxed">
            Heron ne certifie pas la conformité de votre contenu. Heron ne fournit pas de conseil
            juridique. Heron n&apos;audite pas votre chaîne d&apos;approvisionnement. Heron ne
            vérifie pas vos certifications tierces. Heron ne se substitue pas à votre conseil
            juridique.
          </p>
        </div>
      </div>
      <div className="mt-8 border-t border-heron-teal/20 pt-6">
        <h4 className="font-semibold mb-2">
          Pourquoi cette distinction est une caractéristique, pas une limite
        </h4>
        <p className="text-sm text-heron-muted leading-relaxed max-w-3xl">
          Un outil qui sait exactement ce qu&apos;il fait et ce qu&apos;il ne fait pas est le seul
          outil qu&apos;une Directrice Juridique peut utiliser sans risquer d&apos;engager sa
          responsabilité personnelle. Un outil qui prétend certifier la conformité crée une
          responsabilité — la sienne et la vôtre.
        </p>
      </div>
    </section>
  );
}
