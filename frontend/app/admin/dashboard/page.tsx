"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import AppShell from "@/components/AppShell";
import { api } from "@/services/api";
import type { AttendanceRecord, DashboardSummary } from "@/types";

const cards: { key: keyof DashboardSummary; label: string; detail: string; tone: string }[] = [
  { key: "total_employees", label: "Active employees", detail: "Currently on the team", tone: "tone-teal" },
  { key: "present_today", label: "Present today", detail: "Checked in so far", tone: "tone-blue" },
  { key: "absent_today", label: "Not checked in", detail: "Of active employees", tone: "tone-amber" },
  { key: "late_today", label: "Arrived late", detail: "After the grace period", tone: "tone-violet" },
  { key: "on_leave", label: "On leave", detail: "Admin-recorded today", tone: "tone-blue" },
];

export default function AdminDashboard() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [recent, setRecent] = useState<AttendanceRecord[]>([]);
  const [error, setError] = useState("");
  useEffect(() => {
    Promise.all([api<DashboardSummary>("/dashboard/summary"), api<AttendanceRecord[]>("/attendance/today")])
      .then(([data, records]) => { setSummary(data); setRecent(records.slice(0, 6)); })
      .catch((cause: unknown) => setError(cause instanceof Error ? cause.message : "Unable to load dashboard."));
  }, []);

  return <AppShell><div className="page-heading"><div><div className="eyebrow">TODAY · WORKFORCE OVERVIEW</div><h1>Good morning.</h1><p>Here’s what’s happening with your people today.</p></div><Link className="button-primary" href="/admin/employees/new">＋ &nbsp;Add employee</Link></div>
    {error && <div className="alert alert-error">{error}</div>}
    <section className="stat-grid">
      {cards.map((card) => <article className="stat-card" key={card.key}><div className={`stat-icon ${card.tone}`}>{card.key === "total_employees" ? "↗" : card.key === "present_today" ? "✓" : card.key === "absent_today" ? "◷" : "⌁"}</div><div className="stat-label">{card.label}</div><div className="stat-value">{summary ? summary[card.key] : "—"}</div><div className="stat-detail">{card.detail}</div></article>)}
    </section>
    <section className="content-grid">
      <article className="panel attendance-panel"><div className="panel-head"><div><div className="eyebrow">TODAY · LIVE</div><h2>Recent check-ins</h2></div><Link className="text-link" href="/admin/attendance">View all <span>→</span></Link></div>
        {recent.length ? <div className="table-wrap"><table><thead><tr><th>EMPLOYEE</th><th>CHECK-IN</th><th>STATUS</th></tr></thead><tbody>{recent.map((item) => <tr key={item.id}><td><div className="person-cell"><span className="avatar avatar-small">{item.employee_name.slice(0, 1)}</span><span><b>{item.employee_name}</b><small>{item.employee_id}</small></span></div></td><td>{item.check_in_time?.slice(0, 5) ?? "—"}</td><td><span className={`status-tag ${item.status}`}>{item.status.replace("_", " ")}</span></td></tr>)}</tbody></table></div> : <div className="empty-state"><span>◷</span><b>No check-ins yet today</b><p>Today’s attendance will appear here as employees check in.</p></div>}
      </article>
      <article className="panel side-panel"><div className="eyebrow">TEAM PULSE</div><h2>Today at a glance</h2><p className="panel-subtitle">Attendance across your active team.</p>
        <div className="pulse-ring" style={{ "--progress": `${summary && summary.total_employees ? Math.round(summary.present_today / summary.total_employees * 100) : 0}%` } as React.CSSProperties}><div><b>{summary && summary.total_employees ? Math.round(summary.present_today / summary.total_employees * 100) : 0}%</b><small>present</small></div></div>
        <div className="pulse-legend"><span><i className="legend-present" /> Present <b>{summary?.present_today ?? "—"}</b></span><span><i className="legend-absent" /> Not checked in <b>{summary?.absent_today ?? "—"}</b></span><span><i className="legend-leave" /> On leave <b>{summary?.on_leave ?? "—"}</b></span></div>
        <Link className="button-outline full-button" href="/admin/reports">Explore reports <span>→</span></Link>
      </article>
    </section>
  </AppShell>;
}
