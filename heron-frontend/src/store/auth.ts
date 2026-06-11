"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";
import { heronApi } from "@/lib/api";

interface AuthState {
  token: string | null;
  email: string | null;
  isAdmin: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => void;
  setIsAdmin: (value: boolean) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      email: null,
      isAdmin: false,
      login: async (email, password) => {
        const res = await heronApi.login(email, password);
        localStorage.setItem("heron_token", res.data.access_token);
        set({ token: res.data.access_token, email });
      },
      register: async (email, password) => {
        const res = await heronApi.register(email, password);
        localStorage.setItem("heron_token", res.data.access_token);
        set({ token: res.data.access_token, email });
      },
      logout: () => {
        localStorage.removeItem("heron_token");
        set({ token: null, email: null, isAdmin: false });
      },
      setIsAdmin: (value) => set({ isAdmin: value }),
    }),
    { name: "heron_auth" }
  )
);
