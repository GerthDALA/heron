"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { AdsTextInput } from "@/components/ads/AdsTextInput";
import { AdsScanProgress } from "@/components/ads/AdsScanProgress";
import { heronApi } from "@/lib/api";
import { useScanStore } from "@/store/scan";
import { REVENUE_OPTIONS, ADS_SCAN_MIN_CHARS, ADS_SCAN_MAX_CHARS, type InputType } from "@/lib/constants";

export default function DashboardAdsPage() {
  const router = useRouter();
  const setAdsResult = useScanStore((s) => s.setAdsResult);
  const [inputType, setInputType] = useState<InputType>("ad_copy");
  const [inputTitle, setInputTitle] = useState("");
  const [inputText, setInputText] = useState("");
  const [revenue, setRevenue] = useState<number>(REVENUE_OPTIONS[0].value);
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (inputText.length < ADS_SCAN_MIN_CHARS || inputText.length > ADS_SCAN_MAX_CHARS) {
      setError("Le texte doit contenir entre 10 et 50 000 caractères.");
      return;
    }
    setScanning(true);
    try {
      const res = await heronApi.startAdsPaidScan(inputType, inputTitle, inputText, revenue);
      setAdsResult(res.data, null, inputText);
      router.push(`/dashboard/ads/${res.data.scan_id}`);
    } catch {
      setError("L'analyse a échoué. Vérifiez que le texte fait entre 10 et 50 000 caractères et réessayez.");
      setScanning(false);
    }
  };

  return (
    <div className="mx-auto max-w-2xl">
      <h1 className="text-2xl font-bold">Vérifier du copy</h1>
      <p className="mt-2 text-heron-muted">
        Analyse complète : chaque allégation flaggée avec article EmpCo, exposition et remplacement
        conforme. Vos certificats enregistrés sont appliqués automatiquement.
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
          <select
            value={revenue} onChange={(e) => setRevenue(Number(e.target.value))}
            className="w-full rounded-md border border-heron-border bg-white px-3 py-2"
          >
            {REVENUE_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
          {error && <p className="rounded-md bg-heron-danger-bg p-3 text-sm text-heron-danger">{error}</p>}
          <button
            type="submit"
            className="w-full rounded-md bg-heron-teal px-4 py-3 font-semibold text-white hover:bg-heron-teal-dark"
          >
            Analyser ce texte
          </button>
        </form>
      )}
    </div>
  );
}
