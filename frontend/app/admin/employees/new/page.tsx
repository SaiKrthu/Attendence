"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import AppShell from "@/components/AppShell";
import CameraCapture from "@/components/CameraCapture";
import { api } from "@/services/api";
import type { Employee } from "@/types";

export default function NewEmployeePage() {
  const [samples, setSamples] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formElement = event.currentTarget;
    setError(""); setSuccess("");
    if (samples.length < 3) { setError("Capture at least three clear face samples before saving."); return; }
    setBusy(true);
    const form = new FormData(formElement);
    const body = { ...Object.fromEntries(form.entries()), face_samples: samples };
    try {
      const employee = await api<Employee>("/employees", { method: "POST", body: JSON.stringify(body) });
      setSuccess(`${employee.full_name} is registered with ${samples.length} face samples.`);
      setSamples([]);
      formElement.reset();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Employee registration failed.");
    } finally { setBusy(false); }
  }

  return <AppShell><div className="page-heading"><div><div className="eyebrow"><Link href="/admin/employees">EMPLOYEES</Link> &nbsp;/&nbsp; NEW</div><h1>Add employee</h1><p>Create a secure employee profile and enroll their face.</p></div><Link className="button-quiet" href="/admin/employees">← Back to directory</Link></div>
    {error && <div className="alert alert-error" role="alert">{error}</div>}{success && <div className="alert alert-success">{success} <Link href="/admin/employees">Return to employees →</Link></div>}
    <form className="registration-layout" onSubmit={submit}>
      <section className="panel form-panel"><div className="panel-head"><div><div className="eyebrow">01 · EMPLOYEE DETAILS</div><h2>Profile information</h2></div></div><div className="form-grid">
        <label>Employee ID *<input name="employee_id" maxLength={50} placeholder="e.g. EMP-1042" required /></label>
        <label>Full name *<input name="full_name" maxLength={200} placeholder="Employee full name" required /></label>
        <label>Work email *<input name="email" placeholder="name@company.com" required type="email" /></label>
        <label>Phone<input name="phone" maxLength={30} placeholder="+880 1XXX XXXXXX" /></label>
        <label>Department *<input name="department" maxLength={150} placeholder="e.g. Engineering" required /></label>
        <label>Designation<input name="designation" maxLength={150} placeholder="e.g. Product designer" /></label>
        <label>Joining date *<input defaultValue={new Date().toISOString().slice(0, 10)} name="joining_date" required type="date" /></label>
        <label>Status<select defaultValue="active" name="status"><option value="active">Active</option><option value="inactive">Inactive</option></select></label>
        <label>Temporary password *<input name="password" minLength={10} placeholder="At least 10 characters" required type="password" /><small>Share this securely with the employee; do not reuse passwords.</small></label>
      </div>
      <div className="inline-note"><span>i</span><p>New profiles are created as <b>Active</b>. Passwords are stored using a salted one-way hash.</p></div>
      <div className="form-actions"><Link className="button-outline" href="/admin/employees">Cancel</Link><button className="button-primary" disabled={busy} type="submit">{busy ? "Saving profile…" : "Save employee profile"}</button></div>
      </section>
      <section className="panel camera-panel"><div className="panel-head"><div><div className="eyebrow">02 · FACE ENROLLMENT</div><h2>Capture face samples</h2></div><span className="sample-count">{samples.length}/3</span></div><p className="panel-subtitle">Take three separate captures. Images are processed immediately; only face vectors are retained.</p>
        <CameraCapture label="Capture sample" onCapture={(image) => { setSamples((existing) => existing.length < 10 ? [...existing, image] : existing); setError(""); }} />
        <div className="sample-list">{samples.map((_, index) => <div className="sample-item" key={index}><span className="sample-check">✓</span> Sample {index + 1}<button aria-label={`Remove sample ${index + 1}`} onClick={() => setSamples((existing) => existing.filter((__, sampleIndex) => sampleIndex !== index))} type="button">×</button></div>)}</div>
        <p className="fine-print">A usable capture requires exactly one visible face. Raw camera images are not saved.</p>
      </section>
    </form>
  </AppShell>;
}
