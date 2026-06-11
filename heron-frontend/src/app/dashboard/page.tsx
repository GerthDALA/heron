"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Loader2 } from "lucide-react";
import { heronApi } from "@/lib/api";
import { formatEUR, formatDate, cn } from "@/lib/utils";
import { ExpiryBadge } from "@/components/evidence/ExpiryBadge";
import type { Scan, EvidenceSummary } from "@/types/api";

function StatusBadge({ status }: { status: string }) {
  if (status === "complete")
    return <span className="rounded-full bg-heron-teal-light px-3 py-1 text-xs font-semibold text-heron-teal">Complet</span>;
  if (status === "error")
    return <span className="rounded-full bg-heron-danger-bg px-3 py-1 text-xs font-semibold text-heron-danger">Erreur</span>;
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-heron-amber-bg px-3 py-1 text-xs font-semibold text-heron-amber">
      <Loader2 className="h-3 w-3 animate-spin" /> En cours
    </span>
  );
}

export default function DashboardHome() {
  const [scans, setScans] = useState<Scan[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [evidence, setEvidence] = useState<EvidenceSummary | null>(null);

  useEffect(() => {
    // Scan IDs launched in this browser are tracked locally; the backend
    // exposes per-scan endpoints, ownership-checked.
    const ids: string[] = JSON.parse(localStorage.getItem("heron_scan_ids") || "[]");
    Promise.allSettled(ids.map((id) => heronApi.getScanStatus(id))).then((results) => {
      setScans(
        results
          .filter((r) => r.status === "fulfilled")
          .map((r) => (r as PromiseFulfilledResult<{ data: Scan }>).value.data)
      );
      setLoaded(true);
    });
    heronApi.getEvidenceSummary().then((res) => setEvidence(res.data)).catch(() => null);
  }, []);

  const downloadPdf = async (scanId: string) => {
    const res = await heronApi.downloadPdf(scanId);
    const url = URL.createObjectURL(res.data);
    const a = document.createElement("a");
    a.href = url;
    a.download = `heron-${scanId}.pdf`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="mx-auto max-w-5xl space-y-8">
      <h1 className="text-2xl font-bold">Tableau de bord</h1>

      <section id="rapports" className="rounded-lg border border-heron-border bg-white">
        {loaded && scans.length === 0 ? (
          <div className="p-12 text-center">
            <p className="text-heron-muted">
              Aucun scan pour le moment.
              <br />
              Lancez votre premier scan pour voir vos allégations EmpCo.
            </p>
            <Link
              href="/dashboard/new-scan"
              className="mt-4 inline-block rounded-md bg-heron-teal px-6 py-3 font-semibold text-white hover:bg-heron-teal-dark"
            >
              Lancer un scan
            </Link>
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-heron-border bg-heron-surface text-left">
                {["Domaine", "Date", "Allégations", "Exposition max", "Statut", "Actions"].map((h) => (
                  <th key={h} className="p-3 font-semibold">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {scans.map((scan) => (
                <tr key={scan.scan_id} className="border-b border-heron-border last:border-0">
                  <td className="p-3 font-mono">{scan.domain}</td>
                  <td className="p-3">{formatDate(scan.created_at)}</td>
                  <td className="p-3 font-mono">{scan.total_claims}</td>
                  <td className={cn("p-3 font-mono", scan.total_exposure_eur > 0 && "text-heron-danger")}>
                    {formatEUR(scan.total_exposure_eur)}
                  </td>
                  <td className="p-3"><StatusBadge status={scan.status} /></td>
                  <td className="p-3 space-x-3">
                    <Link href={`/dashboard/report/${scan.scan_id}`} className="font-semibold text-heron-teal hover:underline">
                      Voir rapport
                    </Link>
                    {scan.status === "complete" && (
                      <button onClick={() => downloadPdf(scan.scan_id)} className="text-heron-muted hover:text-heron-teal">
                        Télécharger PDF
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <section className="rounded-lg border border-heron-border bg-white p-6">
        {evidence && evidence.active_certs > 0 ? (
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <p className="font-semibold">{evidence.active_certs} certificats actifs</p>
              <p className="text-sm text-heron-muted">
                Couverture : {evidence.covered_articles.length > 0 ? "Annexe I, Point 4a EmpCo" : "—"}
              </p>
              {evidence.expiring_soon > 0 && <ExpiryBadge expiresSoon />}
            </div>
            <Link href="/dashboard/evidence" className="font-semibold text-heron-teal hover:underline">
              Gérer les certificats →
            </Link>
          </div>
        ) : (
          <div className="flex flex-wrap items-center justify-between gap-4">
            <p className="text-sm text-heron-muted">
              Aucun certificat. Sans certificat, les allégations &laquo; biologique &raquo; et
              &laquo; naturel &raquo; sont traitées à exposition maximale.
            </p>
            <Link href="/dashboard/evidence/upload" className="font-semibold text-heron-teal hover:underline">
              Ajouter un certificat →
            </Link>
          </div>
        )}
      </section>
    </div>
  );
}
