"use client";

import { motion } from "framer-motion";

export function AdsScanProgress() {
  return (
    <div className="rounded-lg border border-heron-border bg-white p-6 text-center">
      <p className="font-semibold">Analyse en cours…</p>
      <div className="mt-4 h-2 overflow-hidden rounded-full bg-heron-surface">
        <motion.div
          className="h-full bg-heron-teal"
          initial={{ width: "10%" }}
          animate={{ width: "90%" }}
          transition={{ duration: 3 }}
        />
      </div>
      <p className="mt-2 text-sm text-heron-muted">Résultats en moins de 30 secondes.</p>
    </div>
  );
}
