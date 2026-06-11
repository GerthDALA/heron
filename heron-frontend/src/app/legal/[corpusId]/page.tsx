import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { Navbar } from "@/components/layout/Navbar";
import { Footer } from "@/components/layout/Footer";
import { ArticleBlock } from "@/components/legal/ArticleBlock";
import { formatDate } from "@/lib/utils";
import type { LegalArticle } from "@/types/api";

export const metadata: Metadata = { robots: { index: true, follow: true } };
export const dynamic = "force-dynamic";

const API_URL = process.env.API_INTERNAL_URL || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

interface CorpusDetail {
  corpus: {
    id: string;
    short_name: string;
    full_name: string;
    official_reference: string;
    publication_date: string;
    application_date: string;
    status: string;
  };
  articles: LegalArticle[];
}

async function getCorpus(corpusId: string): Promise<CorpusDetail | null> {
  try {
    const res = await fetch(`${API_URL}/corpus/${corpusId}`, { cache: "no-store" });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

export default async function CorpusPage({ params }: { params: { corpusId: string } }) {
  const data = await getCorpus(params.corpusId);
  if (!data) notFound();
  const { corpus, articles } = data;

  return (
    <>
      <Navbar />
      <main className="mx-auto max-w-[760px] px-4 py-16">
        <nav className="text-sm text-heron-muted">
          <Link href="/legal" className="hover:text-heron-teal">Textes de loi</Link>
          {" / "}
          <span>{corpus.short_name}</span>
        </nav>
        <h1 className="mt-4 text-2xl font-bold leading-snug">{corpus.full_name}</h1>
        <dl className="mt-4 space-y-1 rounded-md bg-heron-surface p-4 text-sm">
          <div><dt className="inline font-semibold">Référence officielle : </dt><dd className="inline">{corpus.official_reference}</dd></div>
          <div><dt className="inline font-semibold">Date de publication : </dt><dd className="inline">{formatDate(corpus.publication_date)}</dd></div>
          <div><dt className="inline font-semibold">Date d&apos;application : </dt><dd className="inline">{formatDate(corpus.application_date)}</dd></div>
          <div><dt className="inline font-semibold">Statut : </dt><dd className="inline">{corpus.status === "active" ? "En vigueur" : corpus.status}</dd></div>
        </dl>
        <div className="mt-6">
          {articles.map((article) => (
            <ArticleBlock
              key={article.id}
              article={article}
              sourceReference={corpus.official_reference}
            />
          ))}
        </div>
      </main>
      <Footer />
    </>
  );
}
