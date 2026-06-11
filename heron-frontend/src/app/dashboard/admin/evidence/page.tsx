"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { heronApi } from "@/lib/api";
import { formatDate, cn } from "@/lib/utils";
import type { AdminEvidenceRow } from "@/types/api";

export default function AdminEvidencePage() {
  const [filter, setFilter] = useState<number | undefined>(undefined);
  const [rows, setRows] = useState<AdminEvidenceRow[]>([]);
  const [message, setMessage] = useState<string | null>(null);

  const load = useCallback(() => {
    heronApi.getAdminEvidence(filter).then((res) => setRows(res.data.evidence));
  }, [filter]);

  useEffect(() => {
    load();
  }, [load]);

  const setVerified = async (id: string, verified: 0 | 1 | 2) => {
    const res = await heronApi.verifyEvidence(id, verified);
    setMessage(
      `Certificat ${id.slice(0, 8)}… : ${res.data.previous} → ${res.data.verified_label} (par ${res.data.by}).`
    );
    load();
  };

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h1 className="text-2xl font-bold">Certificats — file de vérification</h1>
        <Link href="/dashboard/admin" className="text-sm text-heron-teal hover:underline">
          ← Administration
        </Link>
      </div>

      <div className="flex gap-2">
        {[
          { label: "Tous", value: undefined },
          { label: "Non vérifiés", value: 0 },
          { label: "Attestés", value: 1 },
          { label: "Vérifiés", value: 2 },
        ].map((option) => (
          <button
            key={option.label}
            onClick={() => setFilter(option.value)}
            className={cn(
              "rounded-md px-4 py-2 text-sm font-semibold",
              filter === option.value
                ? "bg-heron-teal text-white"
                : "border border-heron-border hover:border-heron-teal"
            )}
          >
            {option.label}
          </button>
        ))}
      </div>

      {message && <p className="rounded-md bg-heron-teal-light p-3 text-sm">{message}</p>}

      <div className="space-y-4">
        {rows.length === 0 ? (
          <p className="rounded-lg border border-heron-border bg-white p-8 text-center text-heron-muted">
            Aucun certificat dans cette file. Changez le filtre pour voir les autres statuts.
          </p>
        ) : (
          rows.map((row) => (
            <div key={row.id} className="rounded-lg border border-heron-border bg-white p-5">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="font-bold">
                    {row.cert_type_name} — <span className="font-mono">{row.cert_number}</span>
                  </p>
                  <p className="text-sm text-heron-muted">
                    {row.cert_holder} • {row.user_email} • envoyé le {formatDate(row.uploaded_at)}
                  </p>
                  <p className="text-sm text-heron-muted">
                    Émis par {row.issuer_name} — valide jusqu&apos;au{" "}
                    {row.valid_until ? formatDate(row.valid_until) : "sans expiration"}
                  </p>
                  <p className="mt-1 text-sm">Scope : {row.scope}</p>
                </div>
                <span
                  className={cn(
                    "rounded-full px-3 py-1 text-xs font-semibold",
                    row.verified === 2
                      ? "bg-heron-teal-light text-heron-teal"
                      : row.verified === 1
                        ? "bg-heron-amber-bg text-heron-amber"
                        : "bg-heron-surface text-heron-muted"
                  )}
                >
                  {row.verified_label}
                </span>
              </div>
              <div className="mt-4 flex gap-3">
                {row.verified < 2 && (
                  <button
                    onClick={() => setVerified(row.id, 2)}
                    className="rounded-md bg-heron-teal px-4 py-2 text-sm font-semibold text-white hover:bg-heron-teal-dark"
                  >
                    Marquer vérifié
                  </button>
                )}
                {row.verified > 0 && (
                  <button
                    onClick={() => setVerified(row.id, 0)}
                    className="rounded-md border border-heron-danger px-4 py-2 text-sm font-semibold text-heron-danger hover:bg-heron-danger-bg"
                  >
                    Rétrograder en non vérifié
                  </button>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
