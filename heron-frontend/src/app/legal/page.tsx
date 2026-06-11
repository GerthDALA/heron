import type { Metadata } from "next";
import { Navbar } from "@/components/layout/Navbar";
import { Footer } from "@/components/layout/Footer";
import { CorpusCard } from "@/components/legal/CorpusCard";
import type { LegalCorpus } from "@/types/api";

export const metadata: Metadata = {
  title: "Textes de loi applicables — Heron",
  robots: { index: true, follow: true },
};

export const dynamic = "force-dynamic";

const API_URL = process.env.API_INTERNAL_URL || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

async function getCorpora(): Promise<LegalCorpus[]> {
  try {
    const res = await fetch(`${API_URL}/corpus`, { cache: "no-store" });
    if (!res.ok) return [];
    const data = await res.json();
    return data.corpora;
  } catch {
    return [];
  }
}

export default async function LegalIndexPage() {
  const corpora = await getCorpora();
  return (
    <>
      <Navbar />
      <main className="mx-auto max-w-[760px] px-4 py-16">
        <h1 className="text-3xl font-bold">Textes de loi applicables</h1>
        <p className="mt-3 text-heron-muted">
          Heron cite uniquement les textes statutaires officiels. Aucun article n&apos;est généré
          par l&apos;IA. Les textes ci-dessous sont intégrés dans l&apos;application et mis à jour
          dès qu&apos;une nouvelle version est publiée au Journal officiel.
        </p>
        <div className="mt-10 space-y-6">
          {corpora.length === 0 ? (
            <p className="rounded-md bg-heron-surface p-4 text-sm text-heron-muted">
              Les textes de loi ne sont pas joignables pour le moment. Vérifiez que le serveur
              Heron est démarré, puis rechargez cette page.
            </p>
          ) : (
            corpora.map((corpus) => <CorpusCard key={corpus.id} corpus={corpus} />)
          )}
        </div>
      </main>
      <Footer />
    </>
  );
}
