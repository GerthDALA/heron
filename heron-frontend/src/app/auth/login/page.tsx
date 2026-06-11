"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Navbar } from "@/components/layout/Navbar";
import { useAuthStore } from "@/store/auth";

export default function LoginPage() {
  const router = useRouter();
  const login = useAuthStore((s) => s.login);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(email, password);
      router.push("/dashboard");
    } catch {
      setError("Email ou mot de passe incorrect. Vérifiez vos identifiants et réessayez.");
      setLoading(false);
    }
  };

  return (
    <>
      <Navbar />
      <main className="mx-auto max-w-sm px-4 py-20">
        <h1 className="text-2xl font-bold">Connexion</h1>
        <form onSubmit={submit} className="mt-6 space-y-4">
          <input
            type="email" required value={email} onChange={(e) => setEmail(e.target.value)}
            placeholder="votre@email.com"
            className="w-full rounded-md border border-heron-border px-3 py-2 focus:border-heron-teal focus:outline-none"
          />
          <input
            type="password" required value={password} onChange={(e) => setPassword(e.target.value)}
            placeholder="Mot de passe"
            className="w-full rounded-md border border-heron-border px-3 py-2 focus:border-heron-teal focus:outline-none"
          />
          {error && <p className="rounded-md bg-heron-danger-bg p-3 text-sm text-heron-danger">{error}</p>}
          <button
            type="submit" disabled={loading}
            className="w-full rounded-md bg-heron-teal px-4 py-3 font-semibold text-white hover:bg-heron-teal-dark disabled:opacity-50"
          >
            {loading ? "Connexion…" : "Se connecter"}
          </button>
        </form>
        <p className="mt-4 text-sm text-heron-muted">
          Pas encore de compte ?{" "}
          <Link href="/auth/register" className="font-semibold text-heron-teal hover:underline">
            Créer un compte
          </Link>
        </p>
      </main>
    </>
  );
}
