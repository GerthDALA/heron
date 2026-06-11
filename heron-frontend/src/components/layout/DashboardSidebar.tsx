"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  Home, Plus, FileText, CreditCard, LogOut, AlignLeft, Award, ShieldCheck,
} from "lucide-react";
import { useAuthStore } from "@/store/auth";
import { cn } from "@/lib/utils";

const links = [
  { href: "/dashboard", label: "Tableau de bord", icon: Home },
  { href: "/dashboard/new-scan", label: "Nouveau scan", icon: Plus },
  { href: "/dashboard", label: "Mes rapports", icon: FileText, anchor: "#rapports" },
  { href: "/dashboard/ads", label: "Vérifier du copy", icon: AlignLeft },
  { href: "/dashboard/evidence", label: "Mes certificats", icon: Award },
  { href: "/pricing", label: "Facturation", icon: CreditCard },
];

export function DashboardSidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const { logout, isAdmin } = useAuthStore();

  return (
    <aside className="fixed inset-y-0 left-0 w-60 border-r border-heron-border bg-white pt-16">
      <nav className="flex h-full flex-col gap-1 p-3">
        {links.map(({ href, label, icon: Icon, anchor }) => (
          <Link
            key={label}
            href={anchor ? `${href}${anchor}` : href}
            className={cn(
              "flex items-center gap-3 rounded-md px-3 py-2 text-sm hover:bg-heron-surface",
              pathname === href && !anchor && "bg-heron-teal-light font-semibold text-heron-teal"
            )}
          >
            <Icon className="h-4 w-4" />
            {label}
          </Link>
        ))}
        {isAdmin && (
          <Link
            href="/dashboard/admin"
            className={cn(
              "flex items-center gap-3 rounded-md px-3 py-2 text-sm hover:bg-heron-surface",
              pathname.startsWith("/dashboard/admin") &&
                "bg-heron-teal-light font-semibold text-heron-teal"
            )}
          >
            <ShieldCheck className="h-4 w-4" />
            Administration
          </Link>
        )}
        <button
          onClick={() => {
            logout();
            router.push("/");
          }}
          className="mt-auto flex items-center gap-3 rounded-md px-3 py-2 text-sm text-heron-muted hover:bg-heron-surface"
        >
          <LogOut className="h-4 w-4" />
          Déconnexion
        </button>
      </nav>
    </aside>
  );
}
