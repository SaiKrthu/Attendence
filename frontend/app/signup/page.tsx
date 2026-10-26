"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { api } from "@/services/api";

type SignupForm = {
  full_name: string;
  employee_id: string;
  email: string;
  department: string;
  designation: string;
  password: string;
  confirmPassword: string;
};

const initialForm: SignupForm = {
  full_name: "",
  employee_id: "",
  email: "",
  department: "",
  designation: "",
  password: "",
  confirmPassword: "",
};

export default function SignupPage() {
  const [form, setForm] = useState(initialForm);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  function update(field: keyof SignupForm, value: string) {
    setForm((current) => ({ ...current, [field]: value }));
    setError("");
    setMessage("");
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setMessage("");
    if (form.password !== form.confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setBusy(true);
    try {
      const result = await api<{ message: string }>("/auth/signup", {
        method: "POST",
        body: JSON.stringify({
          full_name: form.full_name.trim(),
          employee_id: form.employee_id.trim(),
          email: form.email.trim().toLowerCase(),
          department: form.department,
          designation: form.designation.trim() || null,
          password: form.password,
        }),
      });
      setMessage(result.message);
      setForm(initialForm);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Unable to submit your registration.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="login-shell">
      <section className="login-panel signup-panel">
        <div className="login-copy">
          <div className="eyebrow">EMPLOYEE REGISTRATION</div>
          <h1>Create your<br /><em>account.</em></h1>
          <p>Submit your details for administrator review.</p>
        </div>
        {error && <div className="alert alert-error" role="alert">{error}</div>}
        {message && <div className="alert alert-success" role="status">{message} An administrator must approve your request before you can sign in.</div>}
        <form className="form-stack" onSubmit={(event) => void submit(event)}>
          <label>Full name<input autoComplete="name" maxLength={200} onChange={(event) => update("full_name", event.target.value)} required value={form.full_name} /></label>
          <label>Employee ID<input autoComplete="off" maxLength={50} onChange={(event) => update("employee_id", event.target.value)} placeholder="EMP001" required value={form.employee_id} /></label>
          <label>Work email<input autoComplete="email" maxLength={254} onChange={(event) => update("email", event.target.value)} placeholder="you@company.com" required type="email" value={form.email} /></label>
          <label>Department<select className="signup-select" onChange={(event) => update("department", event.target.value)} required value={form.department}><option disabled value="">Select department</option>{["Engineering", "Human Resources", "Finance", "Operations", "Sales", "Marketing", "Cybersecurity", "Other"].map((department) => <option key={department} value={department}>{department}</option>)}</select></label>
          <label>Designation<input autoComplete="organization-title" maxLength={150} onChange={(event) => update("designation", event.target.value)} placeholder="Job title (optional)" value={form.designation} /></label>
          <label>Password<input autoComplete="new-password" minLength={8} maxLength={128} onChange={(event) => update("password", event.target.value)} required type="password" value={form.password} /></label>
          <label>Confirm password<input autoComplete="new-password" minLength={8} maxLength={128} onChange={(event) => update("confirmPassword", event.target.value)} required type="password" value={form.confirmPassword} /></label>
          <p className="signup-approval-note">Your request will be visible to administrators. You can sign in only after approval.</p>
          <button className="button-primary full-button" disabled={busy} type="submit">{busy ? "Submitting…" : "Submit for approval"} <span>→</span></button>
        </form>
        <p className="login-signup-link">Already have an account? <Link className="text-link" href="/login">Sign in</Link></p>
      </section>
      <aside className="login-aside">
        <div className="abstract-art"><div className="art-orbit orbit-one" /><div className="art-orbit orbit-two" /><div className="art-orbit orbit-three" /><div className="art-disc"><span>A</span></div><div className="art-spark spark-one" /><div className="art-spark spark-two" /></div>
        <div className="aside-caption"><span className="eyebrow">A BETTER WAY TO SHOW UP</span><h2>People first.<br />Presence always.</h2><p>Thoughtful tools for teams doing meaningful work.</p></div>
      </aside>
    </main>
  );
}
