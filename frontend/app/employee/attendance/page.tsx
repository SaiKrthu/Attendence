"use client";

import { useEffect, useState } from "react";
import AppShell from "@/components/AppShell";
import CameraCapture from "@/components/CameraCapture";
import { useAuth } from "@/components/AuthProvider";
import { api } from "@/services/api";
import { getMapUrl } from "@/services/location";
import type { AttendanceRecord } from "@/types";

type AttendanceLocation = {
  latitude: number;
  longitude: number;
};

async function getCurrentLocation(): Promise<AttendanceLocation> {
  if (!navigator.geolocation) {
    throw new Error("This browser does not support location access.");
  }

  const coords = await new Promise<GeolocationCoordinates>((resolve, reject) => {
    navigator.geolocation.getCurrentPosition(
      (position) => resolve(position.coords),
      (cause) => {
        if (cause.code === cause.PERMISSION_DENIED) {
          reject(new Error("Allow location access in your browser to continue."));
        } else if (cause.code === cause.POSITION_UNAVAILABLE) {
          reject(new Error("Your current location is unavailable. Try again when location services are enabled."));
        } else {
          reject(new Error("Location lookup timed out. Please try again."));
        }
      },
      { enableHighAccuracy: true, maximumAge: 0, timeout: 15000 },
    );
  });

  return { latitude: coords.latitude, longitude: coords.longitude };
}

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
      const location = await getCurrentLocation();
      const payload = action === "check-in"
        ? {
            image,
            check_in_latitude: location.latitude,
            check_in_longitude: location.longitude,
          }
        : {
            image: image || null,
            check_out_latitude: location.latitude,
            check_out_longitude: location.longitude,
          };
      const row = await api<AttendanceRecord>(`/attendance/${action}`, { method: "POST", body: JSON.stringify(payload) });
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
      {!checkedOut && <p className="fine-print">Your browser will ask for location permission at check-in and check-out. GPS coordinates are saved with each attendance time.</p>}
      {!checkedIn ? <button className="button-primary full-button" disabled={busy || !image} onClick={() => void mark("check-in")} type="button">{busy ? "Verifying face…" : "Verify & check in"} <span>→</span></button> : <button className="button-outline full-button" disabled={busy || checkedOut} onClick={() => void mark("check-out")} type="button">{checkedOut ? "Check-out complete" : busy ? "Saving…" : "Check out"} <span>→</span></button>}
    </section><section className="panel today-panel"><div className="eyebrow">TODAY’S RECORD</div><h2>Your attendance</h2><div className="today-date">{new Intl.DateTimeFormat("en", { dateStyle: "full" }).format(new Date())}</div><div className="time-line"><div className={`time-point ${checkedIn ? "done" : ""}`}><span>{checkedIn ? "✓" : "01"}</span><div><small>CHECK-IN</small><b>{today?.check_in_time?.slice(0, 5) ?? "Not recorded"}</b></div></div><div className="time-connector" /><div className={`time-point ${checkedOut ? "done" : ""}`}><span>{checkedOut ? "✓" : "02"}</span><div><small>CHECK-OUT</small><b>{today?.check_out_time?.slice(0, 5) ?? "Not recorded"}</b></div></div></div><div className="today-status"><small>ATTENDANCE STATUS</small><span className={`status-tag ${today?.status ?? "pending"}`}>{today?.status?.replace("_", " ") ?? "Awaiting check-in"}</span></div>{typeof today?.check_in_latitude === "number" && typeof today.check_in_longitude === "number" && <div className="today-status"><small>CHECK-IN LOCATION</small><a href={getMapUrl(today.check_in_latitude, today.check_in_longitude)} rel="noopener noreferrer" target="_blank">Lat: {today.check_in_latitude.toFixed(6)}, Long: {today.check_in_longitude.toFixed(6)} ↗</a></div>}{typeof today?.check_out_latitude === "number" && typeof today.check_out_longitude === "number" && <div className="today-status"><small>CHECK-OUT LOCATION</small><a href={getMapUrl(today.check_out_latitude, today.check_out_longitude)} rel="noopener noreferrer" target="_blank">Lat: {today.check_out_latitude.toFixed(6)}, Long: {today.check_out_longitude.toFixed(6)} ↗</a></div>}{checkedOut && <div className="hours-total"><span>Working hours</span><b>{today?.working_hours ?? 0} hrs</b></div>}<p className="fine-print">Only one check-in and one check-out are allowed each day.</p></section></div>
  </AppShell>;
}
