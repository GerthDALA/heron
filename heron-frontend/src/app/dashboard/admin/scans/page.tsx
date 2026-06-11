"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { heronApi } from "@/lib/api";
import { formatEUR, formatDate, cn } from "@/lib/utils";
import type { AdminScanRow } from "@/types/api";

export default function AdminScansPage() {
  const [scanType, setScanType] = useState<"domain" | "ads">("domain");
  const [status, setStatus] = useState<string>("");
  const [rows, setRows] = useState<AdminScanRow[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);

  useEffect(() => {
    heronApi.getAdminScans(scanType, status || undefined, page).then((res) => {
      setRows(res.data.scans);
      setTotal(res.data.total);
    });
  }, [scanType, status, page]);

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h1 className="text-2xl font-bold">Scans — administration</h1>
        <Link href="/dashboard/admin" className="text-sm text-heron-teal hover:underline">
          ← Administration
        </Link>
      </div>

      <div className="flex flex-wrap gap-3">
        {(["domain", "ads"] as const).map((type) => (
          <button
            key={type}
            onClick={() => { setScanType(type); setPage(1); }}
            className={cn(
              "rounded-md px-4 py-2 text-sm font-semibold",
              scanType === type ? "bg-heron-teal text-white" : "border border-heron-border hover:border-heron-teal"
            )}
          >
            {type === "domain" ? "Scans domaine" : "Scans copy"}
          </button>
        ))}
        <select
          value={status}
          onChange={(e) => { setStatus(e.target.value); setPage(1); }}
          className="rounded-md border border-heron-border bg-white px-3 py-2 text-sm"
        >
          <option value="">Tous les statuts</option>
          {["pending", "running", "complete", "error"].map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
        <span className="self-center text-sm text-heron-muted">{total} scans</span>
      </div>

      <div className="overflow-x-auto rounded-lg border border-heron-border bg-white">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-heron-border bg-heron-surface text-left">
              {["Cible", "Utilisateur", "Date", "Allégations", "Exposition", "Statut", "Freemium"].map((h) => (
                <th key={h} className="p-3 font-semibold">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 ? (
              <tr><td colSpan={7} className="p-6 text-center text-heron-muted">
                Aucun scan pour ces filtres. Changez le type ou le statut.
              </td></tr>
            ) : (
              rows.map((row) => (
                <tr key={row.id} className="border-b border-heron-border last:border-0">
                  <td className="p-3 font-mono">{row.domain || row.input_title || row.input_type}</td>
                  <td className="p-3">{row.user_email || "—"}</td>
                  <td className="p-3">{formatDate(row.created_at)}</td>
                  <td className="p-3 font-mono">{row.total_claims}</td>
                  <td className="p-3 font-mono">{formatEUR(row.total_exposure_eur)}</td>
                  <td className="p-3">{row.status}</td>
                  <td className="p-3">{row.is_freemium ? "Oui" : "Non"}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div className="flex gap-3">
        <button
          disabled={page <= 1} onClick={() => setPage((p) => p - 1)}
          className="rounded-md border border-heron-border px-4 py-2 text-sm disabled:opacity-40"
        >
          ← Précédent
        </button>
        <button
          disabled={page * 50 >= total} onClick={() => setPage((p) => p + 1)}
          className="rounded-md border border-heron-border px-4 py-2 text-sm disabled:opacity-40"
        >
          Suivant →
        </button>
      </div>
    </div>
  );
}
