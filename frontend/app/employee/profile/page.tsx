"use client";

import { useEffect, useState } from "react";
import AppShell from "@/components/AppShell";
import { useAuth } from "@/components/AuthProvider";
import { api } from "@/services/api";
import type { AttendanceRecord } from "@/types";

export default function EmployeeProfilePage() {
  const { user } = useAuth();
  const [history, setHistory] = useState<AttendanceRecord[]>([]);
  const [error, setError] = useState("");
  useEffect(() => {
    if (user?.employee_id) api<AttendanceRecord[]>(`/attendance/employee/${encodeURIComponent(user.employee_id)}`).then(setHistory).catch((cause: unknown) => setError(cause instanceof Error ? cause.message : "Unable to load attendance history."));
  }, [user]);
  return <AppShell role="employee"><div className="page-heading"><div><div className="eyebrow">YOUR ACCOUNT</div><h1>My profile</h1><p>Account information and attendance history.</p></div></div>{error && <div className="alert alert-error">{error}</div>}
    <section className="panel profile-panel"><div className="profile-hero"><span className="avatar avatar-large">{user?.full_name?.slice(0, 1) || "E"}</span><div><h2>{user?.full_name ?? "Employee"}</h2><p>{user?.employee_id ?? "Employee account"}</p></div><span className="status-tag active">Active</span></div><div className="profile-grid"><div><small>EMAIL</small><b>{user?.email}</b></div><div><small>EMPLOYEE ID</small><b>{user?.employee_id ?? "—"}</b></div><div><small>ROLE</small><b>Employee</b></div></div></section>
    <section className="panel history-panel"><div className="panel-head"><div><div className="eyebrow">YOUR RECORD</div><h2>Attendance history</h2></div></div>{history.length ? <div className="table-wrap"><table><thead><tr><th>DATE</th><th>CHECK-IN</th><th>CHECK-OUT</th><th>HOURS</th><th>STATUS</th></tr></thead><tbody>{history.map((row) => <tr key={row.id}><td>{row.attendance_date}</td><td>{row.check_in_time?.slice(0, 5) ?? "—"}</td><td>{row.check_out_time?.slice(0, 5) ?? "—"}</td><td>{row.working_hours ?? "—"}</td><td><span className={`status-tag ${row.status}`}>{row.status.replace("_", " ")}</span></td></tr>)}</tbody></table></div> : <div className="empty-state"><b>No attendance records yet</b><p>Completed workday records will show here.</p></div>}</section>
  </AppShell>;
}
