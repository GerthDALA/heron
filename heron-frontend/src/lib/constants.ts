export const EMPCO_DEADLINE = new Date("2026-09-27T00:00:00+02:00");

// Citations vérifiées contre le JO (Directive (UE) 2024/825, Annexe).
// Les interdictions sont insérées à l'Annexe I de la Directive 2005/29/CE.
export const EMPCO_ARTICLES = {
  "Annexe I, Point 4a":
    "Allégation environnementale générique sans performance reconnue documentée",
  "Annexe I, Point 4b":
    "Allégation sur un seul aspect présentée comme bénéfice environnemental global",
  "Annexe I, Point 4c":
    "Allégation de neutralité carbone fondée sur la compensation des émissions",
  "Article 6(2)(d)":
    "Affirmation climatique prospective sans plan vérifié indépendamment",
} as const;

export const PLANS = {
  free: { name: "Gratuit", price: 0, maxPages: 1, currency: "EUR" },
  starter: { name: "Starter", price: 290, maxPages: 500, currency: "EUR" },
  brand: { name: "Brand", price: 890, maxPages: 3000, currency: "EUR" },
  studio: { name: "Studio", price: 2400, maxPages: -1, currency: "EUR", monthly: true },
} as const;

export const RISK_LEVELS = {
  high: { label: "Risque élevé", colour: "danger" },
  medium: { label: "Risque moyen", colour: "amber" },
  low: { label: "Risque faible", colour: "safe" },
} as const;

export const REVENUE_OPTIONS = [
  { label: "EUR 1M – 5M", value: 3000000 },
  { label: "EUR 5M – 10M", value: 7500000 },
  { label: "EUR 10M – 25M", value: 17500000 },
  { label: "EUR 25M – 50M", value: 37500000 },
  { label: "EUR 50M+", value: 75000000 },
] as const;

export const INPUT_TYPES = {
  ad_copy: { label: "Publicité (annonce)", description: "Texte d'une annonce Meta, Google, display" },
  email: { label: "Email marketing", description: "Corps d'un email commercial ou newsletter" },
  social_post: { label: "Post réseaux sociaux", description: "Post Instagram, LinkedIn, Twitter/X" },
  transcript: {
    label: "Transcription (texte brut)",
    description: "Texte d'une publicité vidéo ou audio — texte brut uniquement, sans horodatage",
  },
  other: { label: "Autre copy", description: "Tout autre texte marketing" },
} as const;

export type InputType = keyof typeof INPUT_TYPES;

export const CERTIFICATION_TYPES = {
  COSMOS: { name: "COSMOS Organic / Natural", issuer: "Ecocert", covers: "Annexe I, Point 4a EmpCo" },
  EU_ECOLABEL: { name: "EU Ecolabel", issuer: "Commission européenne", covers: "Annexe I, Point 4a EmpCo" },
  GOTS: { name: "GOTS", issuer: "Global Standard gGmbH", covers: "Annexe I, Point 4a EmpCo" },
  GRS: { name: "Global Recycled Standard", issuer: "Textile Exchange", covers: "Annexe I, Point 4a EmpCo" },
  FSC: { name: "FSC", issuer: "FSC International", covers: "Annexe I, Point 4a EmpCo" },
  ISO14024: { name: "EN ISO 14024 Type I", issuer: "Organisme national reconnu", covers: "Annexe I, Point 4a EmpCo" },
  ECOCERT: { name: "Ecocert Organic", issuer: "Ecocert", covers: "Annexe I, Point 4a EmpCo" },
} as const;

export const ADS_SCAN_MAX_CHARS = 50000;
export const ADS_SCAN_MIN_CHARS = 10;
