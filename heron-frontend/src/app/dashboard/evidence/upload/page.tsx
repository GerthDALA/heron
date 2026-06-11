"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { heronApi } from "@/lib/api";
import type { CertificationType } from "@/types/api";

const evidenceSchema = z.object({
  cert_type_id: z.string().min(1, "Sélectionnez un type de certification"),
  cert_number: z.string().min(3, "Numéro de certificat requis"),
  cert_holder: z.string().min(2, "Nom du titulaire requis"),
  issuer_name: z.string().min(2, "Organisme émetteur requis"),
  issue_date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, "Format AAAA-MM-JJ"),
  valid_until: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, "Format AAAA-MM-JJ").or(z.literal("")),
  scope: z.string().min(10, "Décrivez le périmètre couvert (minimum 10 caractères)"),
  no_expiry: z.boolean(),
});

type FormData = z.infer<typeof evidenceSchema>;

const inputClass =
  "w-full rounded-md border border-heron-border px-3 py-2 focus:border-heron-teal focus:outline-none";

export default function EvidenceUploadPage() {
  const router = useRouter();
  const [certTypes, setCertTypes] = useState<CertificationType[]>([]);
  const [file, setFile] = useState<File | null>(null);
  const [serverError, setServerError] = useState<string | null>(null);

  const {
    register, handleSubmit, watch, setValue, formState: { errors, isSubmitting },
  } = useForm<FormData>({
    resolver: zodResolver(evidenceSchema),
    defaultValues: { no_expiry: false, valid_until: "" },
  });

  useEffect(() => {
    heronApi.getCertificationTypes().then((res) => setCertTypes(res.data.certification_types));
  }, []);

  const selectedTypeId = watch("cert_type_id");
  const noExpiry = watch("no_expiry");
  const selectedType = certTypes.find((t) => t.id === selectedTypeId);

  useEffect(() => {
    if (selectedType) setValue("issuer_name", selectedType.issuer);
  }, [selectedType, setValue]);

  const onSubmit = async (data: FormData) => {
    setServerError(null);
    const formData = new FormData();
    formData.append("cert_type_id", data.cert_type_id);
    formData.append("cert_number", data.cert_number);
    formData.append("cert_holder", data.cert_holder);
    formData.append("issuer_name", data.issuer_name);
    formData.append("issue_date", data.issue_date);
    if (!data.no_expiry && data.valid_until) formData.append("valid_until", data.valid_until);
    formData.append("scope", data.scope);
    if (file) {
      if (file.size > 10 * 1024 * 1024) {
        setServerError("Le fichier dépasse 10 Mo. Compressez le PDF ou l'image et réessayez.");
        return;
      }
      formData.append("file", file);
    }
    try {
      await heronApi.uploadEvidence(formData);
      router.push("/dashboard/evidence?saved=1");
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setServerError(
        detail || "L'enregistrement du certificat a échoué. Vérifiez les champs marqués et réessayez."
      );
    }
  };

  return (
    <div className="mx-auto max-w-xl">
      <h1 className="text-2xl font-bold">Ajouter un certificat</h1>
      <p className="mt-2 text-heron-muted">
        Heron utilise vos certificats pour réduire automatiquement le risque sur les allégations
        couvertes. Le certificat n&apos;est jamais envoyé à un tiers. Il est stocké sur vos
        serveurs uniquement.
      </p>

      <form onSubmit={handleSubmit(onSubmit)} className="mt-8 space-y-5">
        <div>
          <label className="mb-1 block text-sm font-medium">Type de certification</label>
          <select {...register("cert_type_id")} className={`${inputClass} bg-white`}>
            <option value="">Sélectionnez…</option>
            {certTypes.map((type) => (
              <option key={type.id} value={type.id}>{type.name}</option>
            ))}
          </select>
          {errors.cert_type_id && <p className="mt-1 text-xs text-heron-danger">{errors.cert_type_id.message}</p>}
          {selectedType && (
            <div className="mt-2 rounded-md bg-heron-teal-light p-3 text-sm">
              <p>{selectedType.description}</p>
              <p className="mt-1 text-xs text-heron-muted">Couvre : Annexe I, Point 4a EmpCo</p>
              {selectedType.verification_url && (
                <a href={selectedType.verification_url} target="_blank" className="text-xs text-heron-teal hover:underline">
                  Vérifier ce type de certificat →
                </a>
              )}
            </div>
          )}
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium">Numéro de certificat</label>
          <input {...register("cert_number")} placeholder="ex. COSMOS-123456" className={inputClass} />
          {errors.cert_number && <p className="mt-1 text-xs text-heron-danger">{errors.cert_number.message}</p>}
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium">Titulaire du certificat</label>
          <input {...register("cert_holder")} placeholder="Nom légal de l'entité sur le certificat" className={inputClass} />
          {errors.cert_holder && <p className="mt-1 text-xs text-heron-danger">{errors.cert_holder.message}</p>}
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium">Organisme émetteur</label>
          <input {...register("issuer_name")} className={inputClass} />
          {errors.issuer_name && <p className="mt-1 text-xs text-heron-danger">{errors.issuer_name.message}</p>}
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label className="mb-1 block text-sm font-medium">Date d&apos;émission</label>
            <input type="date" {...register("issue_date")} className={inputClass} />
            {errors.issue_date && <p className="mt-1 text-xs text-heron-danger">{errors.issue_date.message}</p>}
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">Date d&apos;expiration</label>
            <input type="date" {...register("valid_until")} disabled={noExpiry} className={`${inputClass} disabled:opacity-50`} />
            <label className="mt-1 flex items-center gap-2 text-xs text-heron-muted">
              <input type="checkbox" {...register("no_expiry")} />
              Pas de date d&apos;expiration
            </label>
          </div>
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium">Périmètre couvert (scope)</label>
          <textarea
            {...register("scope")} rows={3}
            placeholder="Décrivez les produits, ingrédients ou matières couverts par ce certificat. Ex: Toute la gamme soins visage, ingrédients certifiés COSMOS listés dans le dossier technique."
            className={inputClass}
          />
          <p className="mt-1 text-xs text-heron-muted">
            Soyez précis — Heron s&apos;appuie sur ce périmètre pour déterminer quelles allégations
            sont couvertes.
          </p>
          {errors.scope && <p className="mt-1 text-xs text-heron-danger">{errors.scope.message}</p>}
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium">Fichier du certificat (optionnel)</label>
          <input
            type="file" accept=".pdf,.jpg,.jpeg,.png"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
            className="text-sm"
          />
          {file && <p className="mt-1 text-xs text-heron-muted">{file.name}</p>}
        </div>

        {serverError && <p className="rounded-md bg-heron-danger-bg p-3 text-sm text-heron-danger">{serverError}</p>}

        <button
          type="submit" disabled={isSubmitting}
          className="w-full rounded-md bg-heron-teal px-4 py-3 font-semibold text-white hover:bg-heron-teal-dark disabled:opacity-50"
        >
          {isSubmitting ? "Enregistrement…" : "Enregistrer le certificat"}
        </button>
      </form>

      <p className="mt-8 text-xs text-heron-muted">
        Heron ne certifie pas la conformité sur la base de vos certificats. Il réduit le risque
        calculé sur les allégations couvertes. Votre juriste valide que le périmètre du certificat
        couvre bien les allégations concernées.
      </p>
    </div>
  );
}
