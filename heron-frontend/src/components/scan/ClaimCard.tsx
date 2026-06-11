import { Lock } from "lucide-react";
import { RiskBadge } from "@/components/shared/RiskBadge";
import { ExposureTag } from "@/components/shared/ExposureTag";

export interface ClaimCardProps {
  originalText: string;
  detectedOn?: string;
  article: string;
  articleFullRef?: string;
  articleDescription?: string;
  exposureEur: number;
  exposureLabel?: string;
  replacementText?: string | null;
  locked?: boolean;
  downgradeNote?: string | null;
  sourceLabel?: string; // ads variant: replaces the URL line
}

export function ClaimCard({
  originalText,
  detectedOn,
  article,
  articleFullRef,
  articleDescription,
  exposureEur,
  exposureLabel,
  replacementText,
  locked = false,
  downgradeNote,
  sourceLabel,
}: ClaimCardProps) {
  return (
    <div className="rounded-lg border border-heron-border bg-white p-6 space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <RiskBadge article={article} />
        <ExposureTag amount={exposureEur} />
      </div>

      <div className="rounded-md bg-heron-danger-bg p-4">
        <p className="text-xs uppercase tracking-wide text-heron-danger/70 mb-1">Texte original</p>
        <p className="font-medium text-heron-danger">&laquo; {originalText} &raquo;</p>
      </div>

      {sourceLabel && (
        <p className="text-sm text-heron-muted">
          Source : <span className="font-mono">{sourceLabel}</span>
        </p>
      )}
      {detectedOn && (
        <p className="text-sm text-heron-muted">
          Détecté sur : <span className="font-mono">{detectedOn}</span>
        </p>
      )}
      {articleFullRef && <p className="text-sm text-heron-muted">{articleFullRef}</p>}
      {articleDescription && <p className="text-sm">{articleDescription}</p>}
      {exposureLabel && <p className="text-sm font-semibold">{exposureLabel}</p>}
      {downgradeNote && (
        <p className="rounded-md bg-heron-safe-bg p-3 text-sm text-heron-safe">{downgradeNote}</p>
      )}

      {locked ? (
        <div className="relative rounded-md bg-heron-safe-bg p-4 overflow-hidden">
          <p className="text-xs uppercase tracking-wide text-heron-safe/70 mb-1">
            Remplacement conforme
          </p>
          <p className="blur-sm select-none text-heron-safe" aria-hidden>
            Formule à base d&apos;ingrédients documentés dans le dossier technique de la marque,
            conforme au registre EmpCo applicable.
          </p>
          <div className="absolute inset-0 flex items-center justify-center gap-2 bg-white/40">
            <Lock className="h-4 w-4 text-heron-teal" />
            <span className="text-sm font-medium text-heron-teal">
              Disponible dans le rapport complet
            </span>
          </div>
        </div>
      ) : replacementText ? (
        <div className="rounded-md bg-heron-safe-bg p-4">
          <p className="text-xs uppercase tracking-wide text-heron-safe/70 mb-1">
            Remplacement conforme
          </p>
          <p className="text-heron-safe">{replacementText}</p>
          <p className="mt-3 text-xs text-heron-muted italic">
            Remplacement proposé sur la base du texte EmpCo. Votre juriste valide avant publication.
          </p>
        </div>
      ) : null}
    </div>
  );
}
