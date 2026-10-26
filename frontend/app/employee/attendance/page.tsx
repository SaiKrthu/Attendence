"use client";

import { useEffect, useState } from "react";
import AppShell from "@/components/AppShell";
import CameraCapture from "@/components/CameraCapture";
import { useAuth } from "@/components/AuthProvider";
import { api } from "@/services/api";
import type { AttendanceRecord } from "@/types";

export default function EmployeeAttendancePage() {
  const { user } = useAuth();
  const [image, setImage] = useState("");
  const [today, setToday] = useState<AttendanceRecord | null>(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const refresh = () => api<AttendanceRecord[]>("/attendance/today").then((rows) => setToday(rows[0] ?? null)).catch((cause: unknown) => setError(cause instanceof Error ? cause.message : "Unable to load today's attendance."));
  useEffect(() => { void refresh(); }, []);

  async function mark(action: "check-in" | "check-out") {
    setError(""); setMessage("");
    if (action === "check-in" && !image) { setError("Capture a face image first."); return; }
    setBusy(true);
    try {
      const row = await api<AttendanceRecord>(`/attendance/${action}`, { method: "POST", body: JSON.stringify({ image: image || null }) });
      setToday(row);
      setMessage(action === "check-in" ? `${row.employee_name} — check-in recorded successfully.` : `Check-out recorded. Working time: ${row.working_hours ?? 0} hours.`);
      setImage("");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Attendance could not be recorded.");
    } finally { setBusy(false); }
  }

  const checkedIn = Boolean(today?.check_in_time);
  const checkedOut = Boolean(today?.check_out_time);
  return <AppShell role="employee"><div className="page-heading"><div><div className="eyebrow">EMPLOYEE PORTAL · {user?.employee_id ?? "ACCOUNT"}</div><h1>Make today count.</h1><p>Verify your face to securely record your attendance.</p></div></div>
    {error && <div className="alert alert-error" role="alert">{error}</div>}{message && <div className="alert alert-success">{message}</div>}
    <div className="attendance-layout"><section className="panel checkin-panel"><div className="panel-head"><div><div className="eyebrow">FACE VERIFICATION</div><h2>Camera check-in</h2></div><span className="online-pill"><span className="status-dot" /> Secure</span></div><p className="panel-subtitle">Your image is checked against your enrollment. Only the attendance record is saved.</p><CameraCapture label={image ? "Capture again" : "Capture face"} onCapture={(capture) => { setImage(capture); setError(""); }} />{image && <div className="capture-ready"><span>✓</span> Capture ready for verification</div>}
      {!checkedIn ? <button className="button-primary full-button" disabled={busy || !image} onClick={() => void mark("check-in")} type="button">{busy ? "Verifying face…" : "Verify & check in"} <span>→</span></button> : <button className="button-outline full-button" disabled={busy || checkedOut} onClick={() => void mark("check-out")} type="button">{checkedOut ? "Check-out complete" : busy ? "Saving…" : "Check out"} <span>→</span></button>}
    </section><section className="panel today-panel"><div className="eyebrow">TODAY’S RECORD</div><h2>Your attendance</h2><div className="today-date">{new Intl.DateTimeFormat("en", { dateStyle: "full" }).format(new Date())}</div><div className="time-line"><div className={`time-point ${checkedIn ? "done" : ""}`}><span>{checkedIn ? "✓" : "01"}</span><div><small>CHECK-IN</small><b>{today?.check_in_time?.slice(0, 5) ?? "Not recorded"}</b></div></div><div className="time-connector" /><div className={`time-point ${checkedOut ? "done" : ""}`}><span>{checkedOut ? "✓" : "02"}</span><div><small>CHECK-OUT</small><b>{today?.check_out_time?.slice(0, 5) ?? "Not recorded"}</b></div></div></div><div className="today-status"><small>ATTENDANCE STATUS</small><span className={`status-tag ${today?.status ?? "pending"}`}>{today?.status?.replace("_", " ") ?? "Awaiting check-in"}</span></div>{checkedOut && <div className="hours-total"><span>Working hours</span><b>{today?.working_hours ?? 0} hrs</b></div>}<p className="fine-print">Only one check-in and one check-out are allowed each day.</p></section></div>
  </AppShell>;
}
