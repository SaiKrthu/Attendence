"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/components/AuthProvider";

export default function LoginPage() {
  const { signIn } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const user = await signIn(email, password);
      router.replace(user.role === "admin" ? "/admin/dashboard" : "/employee/attendance");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Unable to sign in.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="login-shell">
      <section className="login-panel">
        <div className="login-copy"><h1>Good work starts<br />with being <em>seen.</em></h1><p>Sign in to your secure attendance workspace.</p></div>
        <form className="form-stack" onSubmit={submit}>
          <label>Email address<input autoComplete="username" onChange={(event) => setEmail(event.target.value)} placeholder="you@company.com" required type="email" value={email} /></label>
          <label>Password<input autoComplete="current-password" onChange={(event) => setPassword(event.target.value)} placeholder="Enter your password" required type="password" value={password} /></label>
          {error && <div className="alert alert-error" role="alert">{error}</div>}
          <button className="button-primary full-button" disabled={busy} type="submit">{busy ? "Signing in…" : "Sign in"} <span>→</span></button>
        </form>
        <p className="login-signup-link">New employee? <Link className="text-link" href="/signup">Create an account</Link></p>
        <p className="login-security"><span className="tiny-lock">◆</span> Your account is protected with encrypted authentication.</p>
      </section>
      <aside className="login-aside">
        <div className="abstract-art"><div className="art-orbit orbit-one" /><div className="art-orbit orbit-two" /><div className="art-orbit orbit-three" /><div className="art-disc"><span>A</span></div><div className="art-spark spark-one" /><div className="art-spark spark-two" /></div>
        <div className="aside-caption"><span className="eyebrow">A BETTER WAY TO SHOW UP</span><h2>People first.<br />Presence always.</h2><p>Thoughtful tools for teams doing meaningful work.</p></div>
      </aside>
    </main>
  );
}
