"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/components/AuthProvider";

export default function Protected({
  children,
  role,
}: {
  children: React.ReactNode;
  role?: "admin" | "employee";
}) {
  const { user, loading } = useAuth();
  const router = useRouter();
  useEffect(() => {
    if (!loading && !user) router.replace("/login");
    if (!loading && user && role && user.role !== role) {
      router.replace(user.role === "admin" ? "/admin/dashboard" : "/employee/attendance");
    }
  }, [loading, role, router, user]);
  if (loading || !user || (role && user.role !== role)) {
    return <div className="grid min-h-screen place-items-center text-sm text-muted">Loading secure workspace…</div>;
  }
  return <>{children}</>;
}
