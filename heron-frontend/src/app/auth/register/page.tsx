"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Navbar } from "@/components/layout/Navbar";
import { useAuthStore } from "@/store/auth";

export default function RegisterPage() {
  const router = useRouter();
  const register = useAuthStore((s) => s.register);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (password.length < 8) {
      setError("Le mot de passe doit contenir au moins 8 caractères.");
      return;
    }
    setLoading(true);
    try {
      await register(email, password);
      router.push("/dashboard");
    } catch (err: unknown) {
      const status = (err as { response?: { status?: number } })?.response?.status;
      setError(
        status === 409
          ? `Un compte existe déjà pour ${email}. Connectez-vous à la place.`
          : "La création du compte a échoué. Vérifiez l'email saisi et réessayez."
      );
      setLoading(false);
    }
  };

  return (
    <>
      <Navbar />
      <main className="mx-auto max-w-sm px-4 py-20">
        <h1 className="text-2xl font-bold">Créer un compte</h1>
        <p className="mt-2 text-sm text-heron-muted">
          Le compte donne accès au tableau de bord, aux scans complets et aux rapports PDF.
        </p>
        <form onSubmit={submit} className="mt-6 space-y-4">
          <input
            type="email" required value={email} onChange={(e) => setEmail(e.target.value)}
            placeholder="votre@email.com"
            className="w-full rounded-md border border-heron-border px-3 py-2 focus:border-heron-teal focus:outline-none"
          />
          <input
            type="password" required value={password} onChange={(e) => setPassword(e.target.value)}
            placeholder="Mot de passe (8 caractères minimum)"
            className="w-full rounded-md border border-heron-border px-3 py-2 focus:border-heron-teal focus:outline-none"
          />
          {error && <p className="rounded-md bg-heron-danger-bg p-3 text-sm text-heron-danger">{error}</p>}
          <button
            type="submit" disabled={loading}
            className="w-full rounded-md bg-heron-teal px-4 py-3 font-semibold text-white hover:bg-heron-teal-dark disabled:opacity-50"
          >
            {loading ? "Création…" : "Créer mon compte"}
          </button>
        </form>
        <p className="mt-4 text-sm text-heron-muted">
          Déjà un compte ?{" "}
          <Link href="/auth/login" className="font-semibold text-heron-teal hover:underline">
            Connexion
          </Link>
        </p>
      </main>
    </>
  );
}
