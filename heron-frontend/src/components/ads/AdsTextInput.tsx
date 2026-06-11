"use client";

import { INPUT_TYPES, type InputType, ADS_SCAN_MAX_CHARS } from "@/lib/constants";
import { cn } from "@/lib/utils";

const stripHtml = (text: string) => text.replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim();

export function AdsTextInput({
  inputType, setInputType,
  inputTitle, setInputTitle,
  inputText, setInputText,
}: {
  inputType: InputType;
  setInputType: (t: InputType) => void;
  inputTitle: string;
  setInputTitle: (t: string) => void;
  inputText: string;
  setInputText: (t: string) => void;
}) {
  const charCount = inputText.length;
  const isNearLimit = charCount > 48000;
  const isOverLimit = charCount > ADS_SCAN_MAX_CHARS;

  return (
    <div className="space-y-5">
      <div>
        <label className="mb-2 block text-sm font-medium">Type de contenu</label>
        <div className="flex flex-wrap gap-2">
          {(Object.keys(INPUT_TYPES) as InputType[]).map((type) => (
            <button
              key={type} type="button" onClick={() => setInputType(type)}
              title={INPUT_TYPES[type].description}
              className={cn(
                "rounded-md px-4 py-2 text-sm font-semibold",
                inputType === type
                  ? "bg-heron-teal text-white"
                  : "border border-heron-border text-heron-neutral hover:border-heron-teal"
              )}
            >
              {type === "ad_copy" ? "Publicité" : type === "email" ? "Email"
                : type === "social_post" ? "Post" : type === "transcript" ? "Transcription" : "Autre"}
            </button>
          ))}
        </div>
        <p className="mt-1 text-xs text-heron-muted">{INPUT_TYPES[inputType].description}</p>
      </div>

      {inputType === "transcript" && (
        <div className="rounded-md bg-heron-amber-bg p-3 text-sm text-heron-amber">
          <p className="font-semibold">Format texte brut requis.</p>
          <p>
            Les horodatages et étiquettes de locuteur ne sont pas filtrés automatiquement.
            Vérifiez que vous avez collé uniquement le texte parlé.
          </p>
        </div>
      )}

      <div>
        <label className="mb-1 block text-sm font-medium">Titre (optionnel)</label>
        <input
          value={inputTitle} onChange={(e) => setInputTitle(e.target.value)}
          placeholder="ex. Meta Ad — Sérum Vitamine C — Juin 2026"
          className="w-full rounded-md border border-heron-border px-3 py-2 focus:border-heron-teal focus:outline-none"
        />
        <p className="mt-1 text-xs text-heron-muted">Ce titre apparaît dans votre rapport. Non obligatoire.</p>
      </div>

      <div>
        <label className="mb-1 block text-sm font-medium">Texte à analyser</label>
        <textarea
          required rows={12} value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onPaste={(e) => {
            e.preventDefault();
            const pasted = stripHtml(e.clipboardData.getData("text"));
            setInputText(inputText + pasted);
          }}
          placeholder={
            "Collez ici le texte exact de votre annonce, email ou post.\n\nPour les transcriptions : texte brut uniquement — supprimez les horodatages et les étiquettes de locuteur avant de coller."
          }
          className="w-full rounded-md border border-heron-border px-3 py-2 font-mono text-sm focus:border-heron-teal focus:outline-none"
        />
        <p className={cn("mt-1 text-xs", isOverLimit ? "text-heron-danger font-semibold" : isNearLimit ? "text-heron-amber" : "text-heron-muted")}>
          {charCount.toLocaleString("fr-FR")} / 50 000 caractères
        </p>
      </div>
    </div>
  );
}
