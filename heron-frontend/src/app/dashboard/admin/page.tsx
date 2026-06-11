"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { RefreshCw, BellRing } from "lucide-react";
import { heronApi } from "@/lib/api";
import type { AdminStats } from "@/types/api";

export default function AdminHomePage() {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [forbidden, setForbidden] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(() => {
    heronApi
      .getAdminStats()
      .then((res) => setStats(res.data))
      .catch((err) => setForbidden(err.response?.status === 403));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const reloadCorpus = async () => {
    setBusy(true);
    setMessage(null);
    try {
      const res = await heronApi.reloadCorpus();
      const changed = res.data.changed_on_disk;
      setMessage(
        changed.length > 0
          ? `Corpus rechargé : ${res.data.corpora_loaded} textes, ${res.data.articles_loaded} articles. Fichiers modifiés : ${changed.join(", ")}.`
          : `Corpus rechargé : ${res.data.corpora_loaded} textes, ${res.data.articles_loaded} articles. Aucun fichier modifié sur le disque.`
      );
      load();
    } catch {
      setMessage("Le rechargement du corpus a échoué. Vérifiez les fichiers JSON dans app/db/legal_corpus/ et les journaux du serveur.");
    }
    setBusy(false);
  };

  const triggerExpiry = async () => {
    setBusy(true);
    setMessage(null);
    try {
      const res = await heronApi.triggerExpiryCheck();
      setMessage(`Vérification d'expiration exécutée : ${res.data.notices_sent} notification(s) envoyée(s).`);
    } catch {
      setMessage("La vérification d'expiration a échoué. Consultez les journaux du serveur.");
    }
    setBusy(false);
  };

  if (forbidden) {
    return (
      <p className="rounded-md bg-heron-danger-bg p-4 text-heron-danger">
        Accès administrateur requis. Votre email doit figurer dans ADMIN_EMAILS côté serveur.
      </p>
    );
  }
  if (!stats) return <p className="text-heron-muted">Chargement…</p>;

  const counters = [
    { label: "Utilisateurs", value: stats.users },
    { label: "Scans domaine", value: stats.scans },
    { label: "Scans copy", value: stats.ads_scans },
    { label: "Allégations", value: stats.claims },
    { label: "Certificats", value: stats.evidence_records },
    { label: "Certificats à vérifier", value: stats.evidence_pending_review, warn: stats.evidence_pending_review > 0 },
    { label: "Textes de loi", value: stats.corpora },
    { label: "Articles juridiques", value: stats.legal_articles },
    { label: "Articles sans source vérifiée", value: stats.articles_pending_source, warn: stats.articles_pending_source > 0 },
  ];

  return (
    <div className="mx-auto max-w-4xl space-y-8">
      <h1 className="text-2xl font-bold">Administration</h1>

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
        {counters.map((counter) => (
          <div
            key={counter.label}
            className={`rounded-lg border p-4 ${counter.warn ? "border-heron-amber bg-heron-amber-bg" : "border-heron-border bg-white"}`}
          >
            <p className="font-mono text-2xl font-bold">{counter.value}</p>
            <p className="text-sm text-heron-muted">{counter.label}</p>
          </div>
        ))}
      </div>

      <div className="rounded-lg border border-heron-border bg-white p-4 text-sm">
        <p className="font-semibold">Scans par statut</p>
        <div className="mt-2 flex flex-wrap gap-3">
          {Object.entries(stats.scans_by_status).length === 0 ? (
            <span className="text-heron-muted">Aucun scan enregistré.</span>
          ) : (
            Object.entries(stats.scans_by_status).map(([status, count]) => (
              <span key={status} className="rounded-full bg-heron-surface px-3 py-1 font-mono">
                {status} : {count}
              </span>
            ))
          )}
        </div>
      </div>

      <div className="flex flex-wrap gap-4">
        <Link
          href="/dashboard/admin/scans"
          className="rounded-md border border-heron-teal px-5 py-3 font-semibold text-heron-teal hover:bg-heron-teal-light"
        >
          Parcourir les scans
        </Link>
        <Link
          href="/dashboard/admin/evidence"
          className="rounded-md border border-heron-teal px-5 py-3 font-semibold text-heron-teal hover:bg-heron-teal-light"
        >
          File de vérification des certificats
          {stats.evidence_pending_review > 0 && ` (${stats.evidence_pending_review})`}
        </Link>
        <button
          onClick={reloadCorpus} disabled={busy}
          className="flex items-center gap-2 rounded-md bg-heron-teal px-5 py-3 font-semibold text-white hover:bg-heron-teal-dark disabled:opacity-50"
        >
          <RefreshCw className="h-4 w-4" />
          Recharger le corpus juridique
        </button>
        <button
          onClick={triggerExpiry} disabled={busy}
          className="flex items-center gap-2 rounded-md border border-heron-border px-5 py-3 font-semibold hover:bg-heron-surface disabled:opacity-50"
        >
          <BellRing className="h-4 w-4" />
          Lancer la vérification d&apos;expiration
        </button>
      </div>

      {message && <p className="rounded-md bg-heron-teal-light p-4 text-sm">{message}</p>}
    </div>
  );
}
