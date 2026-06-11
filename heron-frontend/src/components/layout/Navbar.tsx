"use client";

import Link from "next/link";
import { useAuthStore } from "@/store/auth";

export function Navbar() {
  const token = useAuthStore((s) => s.token);
  return (
    <nav className="sticky top-0 z-50 border-b border-heron-border bg-white">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
        <Link href="/" className="font-mono text-xl font-bold text-heron-teal">
          Heron
        </Link>
        <div className="flex items-center gap-3">
          <Link href="/legal" className="hidden text-sm text-heron-neutral hover:text-heron-teal sm:block">
            Textes de loi
          </Link>
          <Link
            href="/scan"
            className="rounded-md border border-heron-teal px-4 py-2 text-sm font-semibold text-heron-teal hover:bg-heron-teal-light"
          >
            Scanner ma homepage
          </Link>
          <Link
            href={token ? "/dashboard" : "/auth/login"}
            className="rounded-md px-4 py-2 text-sm text-heron-neutral hover:bg-heron-surface"
          >
            {token ? "Tableau de bord" : "Connexion"}
          </Link>
        </div>
      </div>
    </nav>
  );
}
