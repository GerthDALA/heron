"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Navbar } from "@/components/layout/Navbar";
import { Footer } from "@/components/layout/Footer";
import { ScanProgress } from "@/components/scan/ScanProgress";
import { heronApi } from "@/lib/api";
import { useScanStore } from "@/store/scan";
import { REVENUE_OPTIONS } from "@/lib/constants";

export default function FreemiumScanPage() {
  const router = useRouter();
  const setFreemiumResult = useScanStore((s) => s.setFreemiumResult);
  const [url, setUrl] = useState("");
  const [revenue, setRevenue] = useState<number>(REVENUE_OPTIONS[0].value);
  const [email, setEmail] = useState("");
  const [scanning, setScanning] = useState(false);
  const [step, setStep] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (!/^https:\/\/.+\..+/.test(url)) {
      setError("L'URL doit commencer par https:// et pointer vers un domaine valide.");
      return;
    }
    setScanning(true);
    const stepper = setInterval(() => setStep((s) => Math.min(3, s + 1)), 15000);
    try {
      const res = await heronApi.freemiumScan(url, revenue, email);
      setFreemiumResult(res.data, email);
      router.push(`/scan/${res.data.scan_id}`);
    } catch (err: unknown) {
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(
        detail ||
          `Le scan a échoué sur ${url}. Vérifiez que l'URL est accessible publiquement et réessayez.`
      );
      setScanning(false);
      setStep(0);
    } finally {
      clearInterval(stepper);
    }
  };

  return (
    <>
      <Navbar />
      <main className="mx-auto max-w-xl px-4 py-16">
        <h1 className="text-2xl font-bold">Scanner votre homepage</h1>
        <p className="mt-2 text-heron-muted">
          Collez l&apos;URL de votre boutique. Heron scanne votre page d&apos;accueil en 90
          secondes et identifie les allégations EmpCo visibles.
        </p>

        {scanning ? (
          <div className="mt-8">
            <ScanProgress activeStep={step} />
            <p className="mt-3 text-sm text-heron-muted">Scan de {url} en cours…</p>
          </div>
        ) : (
          <form onSubmit={submit} className="mt-8 space-y-4">
            <div>
              <label className="mb-1 block text-sm font-medium">URL de votre boutique</label>
              <input
                type="url"
                required
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://votre-marque.com"
                className="w-full rounded-md border border-heron-border px-3 py-2 focus:border-heron-teal focus:outline-none"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium">Chiffre d&apos;affaires annuel</label>
              <select
                value={revenue}
                onChange={(e) => setRevenue(Number(e.target.value))}
                className="w-full rounded-md border border-heron-border bg-white px-3 py-2 focus:border-heron-teal focus:outline-none"
              >
                {REVENUE_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium">Email</label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="votre@email.com"
                className="w-full rounded-md border border-heron-border px-3 py-2 focus:border-heron-teal focus:outline-none"
              />
            </div>
            {error && <p className="rounded-md bg-heron-danger-bg p-3 text-sm text-heron-danger">{error}</p>}
            <button
              type="submit"
              className="w-full rounded-md bg-heron-teal px-4 py-3 font-semibold text-white hover:bg-heron-teal-dark"
            >
              Lancer le scan gratuit
            </button>
          </form>
        )}

        <p className="mt-8 text-xs text-heron-muted">
          Heron ne stocke pas le contenu de vos fiches produit au-delà du traitement. Le rapport
          est envoyé uniquement à l&apos;email fourni. Radar, pas juge.
        </p>
      </main>
      <Footer />
    </>
  );
}
