"use client";

import { useState } from "react";
import AppShell from "@/components/AppShell";
import { downloadReport } from "@/services/api";

export default function ReportsPage() {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function exportCsv() {
    setBusy(true); setError("");
    try { await downloadReport(); } catch (cause) { setError(cause instanceof Error ? cause.message : "Export failed."); }
    finally { setBusy(false); }
  }
  return <AppShell><div className="page-heading"><div><div className="eyebrow">INSIGHTS & EXPORTS</div><h1>Reports</h1><p>Export attendance records for your internal reporting.</p></div></div>{error && <div className="alert alert-error">{error}</div>}
    <section className="report-grid"><article className="panel report-card"><div className="report-icon">▤</div><div className="eyebrow">ATTENDANCE DATA</div><h2>Attendance report</h2><p>Download the stored attendance history as CSV. Use the attendance page to review a particular day or status.</p><button className="button-primary" disabled={busy} onClick={() => void exportCsv()} type="button">{busy ? "Preparing…" : "Download CSV"} <span>↓</span></button></article><article className="panel report-note"><div className="eyebrow">DATA INTEGRITY</div><h2>Grounded in real records</h2><p>Reports export only database records. The system does not create demo attendance entries or infer attendance for an employee with no check-in record.</p><div className="report-note-rule" /><small>DATE FILTERS AND DEPARTMENT FILTERS CAN BE ADDED TO THE EXPORT REQUEST.</small></article></section>
  </AppShell>;
}
