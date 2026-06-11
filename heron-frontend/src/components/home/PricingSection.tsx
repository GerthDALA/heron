"use client";

import Link from "next/link";
import { Check } from "lucide-react";
import { cn } from "@/lib/utils";

interface Card {
  plan: string;
  price: string;
  badge?: string;
  cta: string;
  ctaHref: string;
  target?: string;
  items: string[];
  note?: string;
  featured?: boolean;
}

const cards: Card[] = [
  {
    plan: "Gratuit",
    price: "EUR 0",
    cta: "Scanner ma homepage",
    ctaHref: "/scan",
    items: [
      "Scan de la page d'accueil uniquement",
      "1 allégation visible avec article EmpCo exact",
      "Exposition totale estimée (montant global, sans ventilation)",
      "Remplacement conforme pour l'allégation la plus exposée",
    ],
    note: "Résultats en 90 secondes. Sans inscription.",
  },
  {
    plan: "Starter",
    price: "EUR 290",
    badge: "Le plus choisi",
    cta: "Lancer le scan complet",
    ctaHref: "/auth/register",
    items: [
      "Scan jusqu'à 500 fiches produit",
      "Liste complète des allégations flaggées avec citations EmpCo",
      "Remplacement conforme par allégation — prêt-à-coller",
      "Calcul d'exposition par allégation en euros",
      "Rapport PDF avec horodatage — trace de due diligence",
      "Valable pour un domaine, un scan",
    ],
    note: "EUR 290 pour identifier les allégations qui exposent à EUR 18 400 minimum d'amende. Ratio : 1:63.",
    featured: true,
  },
  {
    plan: "Brand",
    price: "EUR 890",
    cta: "Lancer le scan Brand",
    ctaHref: "/auth/register",
    items: [
      "Scan jusqu'à 3 000 fiches produit",
      "Tout le Starter inclus",
      "Scan multilingue (français + anglais sur le même domaine)",
      "Crédit de re-scan — vérifiez après corrections",
      "Livraison prioritaire (moins de 5 minutes)",
    ],
    note: "Premier scan : « À la date du [date], nous avons identifié 23 allégations à risque. » Deuxième scan : « À la date du [date+N jours], nous avons vérifié que toutes les corrections sont conformes. » Ces deux dates, c'est le dossier que vous montrez à la DGCCRF.",
  },
  {
    plan: "Studio",
    price: "EUR 2 400 / mois",
    cta: "Nous contacter",
    ctaHref: "mailto:contact@heron.app",
    target: "Pour les agences gérant plusieurs clients",
    items: [
      "Scans illimités sur domaines illimités",
      "Webhook Shopify/WooCommerce — flagge les allégations avant publication",
      "Digest mensuel de conformité par client",
      "Canal Slack dédié avec l'équipe Heron",
    ],
    note: "Nouveau copy mis en ligne. Le webhook le lit. Si il contient un pattern interdit par EmpCo, Heron le flagge avant que le brand manager approuve la publication. L'agence ressemble à l'experte. La marque évite l'amende.",
  },
];

export function PricingSection({ showHeading = true }: { showHeading?: boolean }) {
  return (
    <section className="bg-white px-4 py-20">
      <div className="mx-auto max-w-6xl">
        {showHeading && (
          <>
            <h2 className="text-2xl font-bold">
              EUR 290 vs EUR 18 400. Le ratio est 1:63. L&apos;offre est irrefusable.
            </h2>
            <p className="mt-2 mb-10 text-heron-muted">
              L&apos;amende documentée la plus basse dans notre base de données est EUR 18 400. Le
              Starter est EUR 290. Le ratio parle de lui-même.
            </p>
          </>
        )}
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
          {cards.map((card) => (
            <div
              key={card.plan}
              className={cn(
                "flex flex-col rounded-lg border bg-white p-6",
                card.featured ? "border-2 border-heron-teal" : "border-heron-border"
              )}
            >
              {card.badge && (
                <span className="mb-2 self-start rounded-full bg-heron-teal px-3 py-1 text-xs font-semibold text-white">
                  {card.badge}
                </span>
              )}
              <h3 className="text-lg font-bold">{card.plan}</h3>
              <p className="font-mono text-2xl font-bold text-heron-teal">{card.price}</p>
              {card.target && <p className="mt-1 text-sm text-heron-muted">{card.target}</p>}
              <ul className="my-4 space-y-2 text-sm">
                {card.items.map((item) => (
                  <li key={item} className="flex gap-2">
                    <Check className="mt-0.5 h-4 w-4 shrink-0 text-heron-teal" />
                    {item}
                  </li>
                ))}
              </ul>
              {card.note && <p className="mb-4 text-xs text-heron-muted">{card.note}</p>}
              <Link
                href={card.ctaHref}
                className={cn(
                  "mt-auto rounded-md px-4 py-2 text-center text-sm font-semibold",
                  card.featured
                    ? "bg-heron-teal text-white hover:bg-heron-teal-dark"
                    : "border border-heron-teal text-heron-teal hover:bg-heron-teal-light"
                )}
              >
                {card.cta}
              </Link>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
