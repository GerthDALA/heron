import { Navbar } from "@/components/layout/Navbar";
import { Footer } from "@/components/layout/Footer";
import { PricingSection } from "@/components/home/PricingSection";

const roiRows = [
  ["Marque A (EUR 5M CA)", "24 allégations", "EUR 500 000 exposition max/allégation", "Starter EUR 290", "Ratio 1:1 724"],
  ["Marque B (EUR 15M CA)", "67 allégations", "EUR 1 500 000 exposition max/allégation", "Brand EUR 890", "Ratio 1:4 517"],
  ["Marque C (EUR 35M CA)", "142 allégations", "EUR 3 500 000 exposition max/allégation", "Brand EUR 890", "Ratio 1:382"],
];

export default function PricingPage() {
  return (
    <>
      <Navbar />
      <main>
        <section className="mx-auto max-w-3xl px-4 pt-16">
          <h1 className="text-3xl font-bold">EUR 290 vs EUR 18 400.</h1>
          <p className="mt-4 text-lg text-heron-muted">
            Une heure de votre cabinet juridique à EUR 400/heure n&apos;identifie pas vos 847
            fiches produit. EUR 290 donne le rapport complet avec les remplacements. Ce que votre
            juriste fait ensuite avec, c&apos;est son travail.
          </p>
        </section>
        <PricingSection showHeading={false} />
        <section className="mx-auto max-w-5xl px-4 pb-20">
          <div className="overflow-x-auto rounded-lg border border-heron-border">
            <table className="w-full text-sm">
              <tbody>
                {roiRows.map((row) => (
                  <tr key={row[0]} className="border-b border-heron-border last:border-0">
                    {row.map((cell, i) => (
                      <td key={i} className="p-3 font-mono">{cell}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </main>
      <Footer />
    </>
  );
}
