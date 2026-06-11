"use client";

import { create } from "zustand";
import type { FreemiumScanResult, AdsScanResponse } from "@/types/api";

interface ScanState {
  // Freemium domain scan result, kept in memory between /scan and /scan/[id]
  freemiumResult: FreemiumScanResult | null;
  freemiumEmail: string | null;
  setFreemiumResult: (result: FreemiumScanResult, email: string) => void;
  // Ads scan result (freemium and paid)
  adsResult: AdsScanResponse | null;
  adsEmail: string | null;
  adsInputText: string | null;
  setAdsResult: (result: AdsScanResponse, email: string | null, inputText: string) => void;
}

export const useScanStore = create<ScanState>((set) => ({
  freemiumResult: null,
  freemiumEmail: null,
  setFreemiumResult: (result, email) => set({ freemiumResult: result, freemiumEmail: email }),
  adsResult: null,
  adsEmail: null,
  adsInputText: null,
  setAdsResult: (result, email, inputText) =>
    set({ adsResult: result, adsEmail: email, adsInputText: inputText }),
}));
