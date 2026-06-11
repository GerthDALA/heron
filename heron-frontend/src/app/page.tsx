import { Navbar } from "@/components/layout/Navbar";
import { Footer } from "@/components/layout/Footer";
import { HeroSection } from "@/components/home/HeroSection";
import { ProblemSection } from "@/components/home/ProblemSection";
import { ScanTimeline } from "@/components/home/ScanTimeline";
import { ClaimsDemo } from "@/components/home/ClaimsDemo";
import { RadarNotJudge } from "@/components/shared/RadarNotJudge";
import { PricingSection } from "@/components/home/PricingSection";
import { FaqSection } from "@/components/home/FaqSection";
import { LegalTransparency } from "@/components/home/LegalTransparency";
import { ClosingCta } from "@/components/home/ClosingCta";

export default function HomePage() {
  return (
    <>
      <Navbar />
      <main>
        <HeroSection />
        <ProblemSection />
        <ScanTimeline />
        <ClaimsDemo />
        <div className="mx-auto max-w-5xl px-4">
          <RadarNotJudge />
        </div>
        <PricingSection />
        <FaqSection />
        <LegalTransparency />
        <ClosingCta />
      </main>
      <Footer />
    </>
  );
}
