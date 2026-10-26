"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/components/AuthProvider";

export default function Home() {
  const { user, loading } = useAuth();
  const router = useRouter();
  useEffect(() => {
    if (!loading) router.replace(user ? (user.role === "admin" ? "/admin/dashboard" : "/employee/attendance") : "/login");
  }, [loading, router, user]);
  return <div className="grid min-h-screen place-items-center text-sm text-muted">Opening your workspace…</div>;
}
