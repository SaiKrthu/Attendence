"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/services/api";
import type { User } from "@/types";

type AuthContextValue = {
  user: User | null;
  loading: boolean;
  signIn: (email: string, password: string) => Promise<User>;
  signOut: () => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    const token = window.localStorage.getItem("attendance-token");
    if (!token) {
      void Promise.resolve().then(() => {
        if (active) setLoading(false);
      });
      return () => { active = false; };
    }
    api<User>("/auth/me")
      .then((currentUser) => {
        if (active) setUser(currentUser);
      })
      .catch(() => window.localStorage.removeItem("attendance-token"))
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => { active = false; };
  }, []);

  const signIn = useCallback(async (email: string, password: string) => {
    const result = await api<{ access_token: string; user: User }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    window.localStorage.setItem("attendance-token", result.access_token);
    setUser(result.user);
    return result.user;
  }, []);

  const signOut = useCallback(() => {
    void api<void>("/auth/logout", { method: "POST" }).catch(() => undefined);
    window.localStorage.removeItem("attendance-token");
    setUser(null);
  }, []);

  const value = useMemo(() => ({ user, loading, signIn, signOut }), [user, loading, signIn, signOut]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth must be used inside AuthProvider.");
  return value;
}

export function SignOutButton() {
  const { signOut } = useAuth();
  const router = useRouter();
  return (
    <button
      className="button-quiet"
      onClick={() => {
        signOut();
        router.push("/login");
      }}
      type="button"
    >
      Sign out
    </button>
  );
}
