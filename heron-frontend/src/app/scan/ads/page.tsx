"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Navbar } from "@/components/layout/Navbar";
import { Footer } from "@/components/layout/Footer";
import { AdsTextInput } from "@/components/ads/AdsTextInput";
import { AdsScanProgress } from "@/components/ads/AdsScanProgress";
import { heronApi } from "@/lib/api";
import { useScanStore } from "@/store/scan";
import { REVENUE_OPTIONS, ADS_SCAN_MIN_CHARS, ADS_SCAN_MAX_CHARS, type InputType } from "@/lib/constants";

export default function AdsFreemiumScanPage() {
  const router = useRouter();
  const setAdsResult = useScanStore((s) => s.setAdsResult);
  const [inputType, setInputType] = useState<InputType>("ad_copy");
  const [inputTitle, setInputTitle] = useState("");
  const [inputText, setInputText] = useState("");
  const [revenue, setRevenue] = useState<number>(REVENUE_OPTIONS[0].value);
  const [email, setEmail] = useState("");
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const hasToken = typeof window !== "undefined" && !!localStorage.getItem("heron_token");

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (inputText.length < ADS_SCAN_MIN_CHARS) {
      setError(`Le texte doit contenir au moins ${ADS_SCAN_MIN_CHARS} caractères.`);
      return;
    }
    if (inputText.length > ADS_SCAN_MAX_CHARS) {
      setError("Le texte dépasse 50 000 caractères. Découpez-le et analysez chaque partie séparément.");
      return;
    }
    setScanning(true);
    try {
      const res = hasToken
        ? await heronApi.startAdsPaidScan(inputType, inputTitle, inputText, revenue)
        : await heronApi.startAdsFreemiumScan(inputType, inputTitle, inputText, revenue, email);
      setAdsResult(res.data, hasToken ? null : email, inputText, inputType);
      router.push(hasToken ? `/dashboard/ads/${res.data.scan_id}` : `/scan/ads/${res.data.scan_id}`);
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(
        typeof detail === "string"
          ? detail
          : "L'analyse a échoué. Vérifiez que le texte fait entre 10 et 50 000 caractères et réessayez."
      );
      setScanning(false);
    }
  };

  return (
    <>
      <Navbar />
      <main className="mx-auto max-w-2xl px-4 py-16">
        <h1 className="text-2xl font-bold">Vérifier votre copy publicitaire</h1>
        <p className="mt-2 text-heron-muted">
          Collez le texte de votre annonce, email, post ou transcription. Heron identifie chaque
          allégation EmpCo en moins de 30 secondes. Fonctionne sur : annonces Meta et Google,
          emails marketing, posts LinkedIn et Instagram, transcriptions de publicités vidéo (texte
          brut uniquement).
        </p>

        {scanning ? (
          <div className="mt-8"><AdsScanProgress /></div>
        ) : (
          <form onSubmit={submit} className="mt-8 space-y-5">
            <AdsTextInput
              inputType={inputType} setInputType={setInputType}
              inputTitle={inputTitle} setInputTitle={setInputTitle}
              inputText={inputText} setInputText={setInputText}
            />
            <div>
              <label className="mb-1 block text-sm font-medium">Chiffre d&apos;affaires annuel</label>
              <select
                value={revenue} onChange={(e) => setRevenue(Number(e.target.value))}
                className="w-full rounded-md border border-heron-border bg-white px-3 py-2"
              >
                {REVENUE_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
            </div>
            {!hasToken && (
              <div>
                <label className="mb-1 block text-sm font-medium">Email</label>
                <input
                  type="email" required value={email} onChange={(e) => setEmail(e.target.value)}
                  placeholder="votre@email.com"
                  className="w-full rounded-md border border-heron-border px-3 py-2 focus:border-heron-teal focus:outline-none"
                />
              </div>
            )}
            {error && <p className="rounded-md bg-heron-danger-bg p-3 text-sm text-heron-danger">{error}</p>}
            <button
              type="submit"
              className="w-full rounded-md bg-heron-teal px-4 py-3 font-semibold text-white hover:bg-heron-teal-dark"
            >
              Analyser ce texte
            </button>
          </form>
        )}

        <div className="mt-10 rounded-md bg-heron-surface p-4 text-sm text-heron-muted">
          <p className="font-semibold">Pour les transcriptions vidéo ou audio :</p>
          <p className="mt-2">Heron analyse le texte brut uniquement. Avant de coller :</p>
          <ol className="mt-1 list-decimal pl-5">
            <li>Supprimez les horodatages (00:00:14 → ...)</li>
            <li>Supprimez les étiquettes de locuteur ([Voix off], [Speaker 1])</li>
            <li>Gardez uniquement le texte parlé</li>
          </ol>
          <p className="mt-2">Les formats SRT, VTT ou JSON ne sont pas supportés.</p>
        </div>
      </main>
      <Footer />
    </>
  );
}
