"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Navbar } from "@/components/layout/Navbar";
import { DashboardSidebar } from "@/components/layout/DashboardSidebar";
import { useAuthStore } from "@/store/auth";
import { heronApi } from "@/lib/api";

export default function DashboardShell({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { setIsAdmin } = useAuthStore();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("heron_token");
    if (!token) {
      router.replace("/auth/login");
      return;
    }
    setReady(true);
    // Probe admin access once; 403 simply means not an admin.
    heronApi
      .getAdminStats()
      .then(() => setIsAdmin(true))
      .catch(() => setIsAdmin(false));
  }, [router, setIsAdmin]);

  if (!ready) return null;

  return (
    <>
      <Navbar />
      <DashboardSidebar />
      <main className="ml-60 min-h-screen bg-heron-surface/40 p-8">{children}</main>
    </>
  );
}
