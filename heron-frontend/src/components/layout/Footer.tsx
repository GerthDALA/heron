import Link from "next/link";

export function Footer() {
  return (
    <footer className="border-t border-heron-border bg-heron-surface">
      <div className="mx-auto max-w-6xl px-4 py-10">
        <div className="flex flex-col items-start justify-between gap-6 sm:flex-row">
          <div>
            <p className="font-mono text-lg font-bold text-heron-teal">Heron</p>
            <p className="text-sm text-heron-muted">Radar, pas juge.</p>
          </div>
          <div className="flex gap-6 text-sm text-heron-muted">
            <Link href="/legal" className="hover:text-heron-teal">Textes de loi</Link>
            <a href="#" className="hover:text-heron-teal">Mentions légales</a>
            <a href="#" className="hover:text-heron-teal">Politique de confidentialité</a>
            <a href="mailto:contact@heron.app" className="hover:text-heron-teal">Contact</a>
          </div>
        </div>
        <p className="mt-8 text-xs text-heron-muted">
          Directive EmpCo (UE) 2024/825 — Article L132-2 Code de la consommation — DGCCRF
        </p>
      </div>
    </footer>
  );
}
