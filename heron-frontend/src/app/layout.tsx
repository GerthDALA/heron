import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
const jetbrains = JetBrains_Mono({ subsets: ["latin"], variable: "--font-jetbrains" });

export const metadata: Metadata = {
  title: "Heron — Scanner EmpCo pour marques françaises",
  description:
    "Heron lit chaque fiche produit de votre domaine, identifie chaque allégation interdite par la Directive EmpCo (UE) 2024/825, calcule l'exposition maximale DGCCRF par allégation et livre le remplacement conforme.",
  openGraph: {
    title: "Heron — Radar, pas juge.",
    description:
      "Chaque allégation environnementale. L'article EmpCo exact. L'exposition DGCCRF en euros. Le remplacement prêt-à-coller.",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr">
      <body className={`${inter.variable} ${jetbrains.variable} font-body text-heron-neutral`}>
        {children}
      </body>
    </html>
  );
}
