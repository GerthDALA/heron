"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

const STEPS = ["Crawl", "Analyse", "Calculate", "Generate"] as const;

export function ScanProgress({
  activeStep,
  pagesScanned,
}: {
  activeStep: number; // 0..3
  pagesScanned?: number;
}) {
  return (
    <div className="rounded-lg border border-heron-border bg-white p-6">
      <div className="flex items-center justify-between mb-4">
        {STEPS.map((step, i) => (
          <div key={step} className="flex flex-col items-center flex-1">
            <div
              className={cn(
                "h-3 w-3 rounded-full mb-2",
                i <= activeStep ? "bg-heron-teal" : "bg-heron-border"
              )}
            />
            <span
              className={cn(
                "text-xs",
                i <= activeStep ? "text-heron-teal font-semibold" : "text-heron-muted"
              )}
            >
              {step}
            </span>
          </div>
        ))}
      </div>
      <div className="h-2 rounded-full bg-heron-surface overflow-hidden">
        <motion.div
          className="h-full bg-heron-teal"
          initial={{ width: "5%" }}
          animate={{ width: `${Math.min(95, (activeStep + 1) * 24)}%` }}
          transition={{ duration: 0.8 }}
        />
      </div>
      {pagesScanned !== undefined && pagesScanned > 0 && (
        <p className="mt-3 text-sm text-heron-muted font-mono">{pagesScanned} fiches lues</p>
      )}
    </div>
  );
}
