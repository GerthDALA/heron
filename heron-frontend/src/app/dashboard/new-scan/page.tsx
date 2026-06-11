"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { heronApi } from "@/lib/api";
import { ScanProgress } from "@/components/scan/ScanProgress";
import { REVENUE_OPTIONS } from "@/lib/constants";

function rememberScanId(id: string) {
  const ids: string[] = JSON.parse(localStorage.getItem("heron_scan_ids") || "[]");
  localStorage.setItem("heron_scan_ids", JSON.stringify([id, ...ids.filter((x) => x !== id)]));
}

export default function NewScanPage() {
  const router = useRouter();
  const [domain, setDomain] = useState("");
  const [revenue, setRevenue] = useState<number>(REVENUE_OPTIONS[0].value);
  const [planTier, setPlanTier] = useState<"starter" | "brand">("starter");
  const [error, setError] = useState<string | null>(null);
  const [scanId, setScanId] = useState<string | null>(null);
  const [pagesScanned, setPagesScanned] = useState(0);
  const [step, setStep] = useState(0);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => () => { if (pollRef.current) clearInterval(pollRef.current); }, []);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      const res = await heronApi.startScan(domain, revenue, planTier);
      const id = res.data.scan_id;
      rememberScanId(id);
      setScanId(id);
      pollRef.current = setInterval(async () => {
        const status = await heronApi.getScanStatus(id);
        setPagesScanned(status.data.pages_scanned);
        setStep((s) => Math.min(3, status.data.pages_scanned > 0 ? Math.max(1, s) : s));
        if (status.data.status === "complete") {
          if (pollRef.current) clearInterval(pollRef.current);
          router.push(`/dashboard/report/${id}`);
        }
        if (status.data.status === "error") {
          if (pollRef.current) clearInterval(pollRef.current);
          setError(`Le scan a échoué sur ${domain}. Vérifiez que l'URL est accessible publiquement et réessayez.`);
          setScanId(null);
        }
      }, 3000);
    } catch (err: unknown) {
      const status = (err as { response?: { status?: number; data?: { detail?: string } } })?.response;
      setError(
        status?.status === 403
          ? "Votre plan actuel ne permet pas ce type de scan. Passez au plan Starter ou Brand depuis la page Facturation."
          : status?.data?.detail || `Le scan a échoué sur ${domain}. Vérifiez que l'URL est accessible publiquement et réessayez.`
      );
    }
  };

  return (
    <div className="mx-auto max-w-xl">
      <h1 className="text-2xl font-bold">Nouveau scan</h1>
      <p className="mt-2 text-heron-muted">
        Scan complet du domaine : jusqu&apos;à 500 fiches (Starter) ou 3 000 fiches (Brand).
      </p>
      {scanId ? (
        <div className="mt-8">
          <ScanProgress activeStep={step} pagesScanned={pagesScanned} />
          <p className="mt-3 text-sm text-heron-muted">
            Scan de {domain} en cours. Cette page se met à jour toutes les 3 secondes.
          </p>
        </div>
      ) : (
        <form onSubmit={submit} className="mt-8 space-y-4">
          <input
            type="url" required value={domain} onChange={(e) => setDomain(e.target.value)}
            placeholder="https://votre-marque.com"
            className="w-full rounded-md border border-heron-border px-3 py-2 focus:border-heron-teal focus:outline-none"
          />
          <select
            value={revenue} onChange={(e) => setRevenue(Number(e.target.value))}
            className="w-full rounded-md border border-heron-border bg-white px-3 py-2"
          >
            {REVENUE_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
          <div className="flex gap-3">
            {(["starter", "brand"] as const).map((tier) => (
              <button
                key={tier} type="button" onClick={() => setPlanTier(tier)}
                className={`flex-1 rounded-md border px-4 py-3 text-sm font-semibold ${
                  planTier === tier
                    ? "border-heron-teal bg-heron-teal text-white"
                    : "border-heron-border text-heron-neutral hover:border-heron-teal"
                }`}
              >
                {tier === "starter" ? "Starter — 500 fiches" : "Brand — 3 000 fiches"}
              </button>
            ))}
          </div>
          {error && <p className="rounded-md bg-heron-danger-bg p-3 text-sm text-heron-danger">{error}</p>}
          <button
            type="submit"
            className="w-full rounded-md bg-heron-teal px-4 py-3 font-semibold text-white hover:bg-heron-teal-dark"
          >
            Lancer le scan complet
          </button>
        </form>
      )}
    </div>
  );
}
