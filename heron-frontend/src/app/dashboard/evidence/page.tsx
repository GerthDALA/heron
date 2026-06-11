"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { heronApi } from "@/lib/api";
import { EvidenceCard } from "@/components/evidence/EvidenceCard";
import type { EvidenceRecord } from "@/types/api";

export default function EvidencePage() {
  const [records, setRecords] = useState<EvidenceRecord[]>([]);
  const [loaded, setLoaded] = useState(false);

  const load = () =>
    heronApi.getUserEvidence().then((res) => {
      setRecords(res.data.evidence);
      setLoaded(true);
    });

  useEffect(() => {
    load();
  }, []);

  const handleDelete = async (id: string) => {
    await heronApi.deleteEvidence(id);
    load();
  };

  return (
    <div className="mx-auto max-w-3xl space-y-8">
      <div>
        <h1 className="text-2xl font-bold">Vos certificats</h1>
        <p className="mt-2 text-heron-muted">
          Heron applique automatiquement vos certificats lors de chaque scan. Une allégation
          couverte par un certificat valide voit son exposition réduite de 80 à 90 %.
        </p>
      </div>

      {loaded && records.length === 0 ? (
        <div className="rounded-lg border border-heron-border bg-white p-8">
          <p className="font-semibold">Aucun certificat enregistré.</p>
          <p className="mt-3 text-sm text-heron-muted">
            Sans certificat, chaque allégation &laquo; biologique &raquo;, &laquo; naturel &raquo;
            ou &laquo; éco &raquo; sur votre domaine est traitée comme une violation Annexe I,
            point 4a à exposition maximale.
          </p>
          <p className="mt-3 text-sm text-heron-muted">
            Un certificat COSMOS, par exemple, réduit l&apos;exposition de 80 % sur toutes les
            allégations qu&apos;il couvre.
          </p>
          <Link
            href="/dashboard/evidence/upload"
            className="mt-6 inline-block rounded-md bg-heron-teal px-6 py-3 font-semibold text-white hover:bg-heron-teal-dark"
          >
            Ajouter un certificat
          </Link>
        </div>
      ) : (
        <>
          <div className="space-y-4">
            {records.map((record) => (
              <EvidenceCard key={record.id} record={record} onDelete={handleDelete} />
            ))}
          </div>
          <Link
            href="/dashboard/evidence/upload"
            className="inline-block rounded-md border border-heron-teal px-6 py-3 font-semibold text-heron-teal hover:bg-heron-teal-light"
          >
            Ajouter un certificat
          </Link>
        </>
      )}
    </div>
  );
}
