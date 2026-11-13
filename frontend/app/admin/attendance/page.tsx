"use client";

import { FormEvent, useEffect, useState } from "react";
import AppShell from "@/components/AppShell";
import { api } from "@/services/api";
import { getMapUrl } from "@/services/location";
import type { AttendanceRecord } from "@/types";

type LocationDetailsProps = {
  address: string | null;
  latitude: number | null;
  longitude: number | null;
  label: string;
  hasAttendanceTime: boolean;
};

function LocationDetails({ address, latitude, longitude, label, hasAttendanceTime }: LocationDetailsProps) {
  const hasCoordinates = typeof latitude === "number" && typeof longitude === "number";

  if (!hasCoordinates) {
    return <span>{hasAttendanceTime ? "Not captured" : "—"}</span>;
  }

  return <div className="location-details">
    <b>{address || "Readable address unavailable"}</b>
    <small>Lat: {latitude.toFixed(6)} · Long: {longitude.toFixed(6)}</small>
    <a
      href={getMapUrl(latitude, longitude)}
      rel="noopener noreferrer"
      target="_blank"
    >View {label.toLowerCase()} map ↗</a>
  </div>;
}

export default function AdminAttendancePage() {
  const [records, setRecords] = useState<AttendanceRecord[]>([]);
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10));
  const [status, setStatus] = useState("");
  const [employeeCode, setEmployeeCode] = useState("");
  const [manualStatus, setManualStatus] = useState<"absent" | "leave">("leave");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => {
    const query = new URLSearchParams({ date });
    if (status) query.set("status", status);
    api<AttendanceRecord[]>(`/attendance?${query}`).then(setRecords).catch((cause: unknown) => setError(cause instanceof Error ? cause.message : "Unable to load attendance."));
  }, [date, status]);
  async function recordStatus(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(""); setSaving(true);
    try {
      const created = await api<AttendanceRecord>("/attendance/admin-status", {
        method: "POST",
        body: JSON.stringify({ employee_id: employeeCode, attendance_date: date, status: manualStatus }),
      });
      if (!status || status === created.status) {
        setRecords((current) => [...current, created].sort((a, b) => a.employee_name.localeCompare(b.employee_name)));
      }
      setEmployeeCode("");
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Unable to save the attendance status."); }
    finally { setSaving(false); }
  }
  return <AppShell><div className="page-heading"><div><div className="eyebrow">WORKFORCE RECORDS</div><h1>Attendance</h1><p>Daily check-ins, check-outs, locations, and working hours.</p></div></div>{error && <div className="alert alert-error">{error}</div>}
    <form className="panel admin-status-form" onSubmit={(event) => void recordStatus(event)}><div><div className="eyebrow">ADMIN ENTRY</div><b>Record absence or leave</b><small>Use a real employee ID and selected date. Existing records cannot be overwritten here.</small></div><input aria-label="Employee ID" onChange={(event) => setEmployeeCode(event.target.value)} placeholder="Employee ID" required value={employeeCode} /><select aria-label="Attendance status to record" onChange={(event) => setManualStatus(event.target.value as "absent" | "leave")} value={manualStatus}><option value="leave">On leave</option><option value="absent">Absent</option></select><button className="button-outline" disabled={saving} type="submit">{saving ? "Saving…" : "Record status"}</button></form>
    <section className="panel directory-panel"><div className="toolbar"><label className="filter-field">Date<input onChange={(event) => setDate(event.target.value)} type="date" value={date} /></label><select aria-label="Filter attendance status" onChange={(event) => setStatus(event.target.value)} value={status}><option value="">All statuses</option><option value="present">Present</option><option value="late">Late</option><option value="half_day">Half day</option><option value="leave">Leave</option><option value="absent">Absent</option></select><span className="result-count">{records.length} records</span></div>
      {records.length ? <><div className="table-wrap"><table><thead><tr><th>EMPLOYEE NAME / ID</th><th>DATE</th><th>CHECK-IN TIME</th><th>CHECK-IN LOCATION · ADDRESS / GPS</th><th>CHECK-OUT TIME</th><th>CHECK-OUT LOCATION · ADDRESS / GPS</th><th>TOTAL HOURS</th><th>STATUS</th></tr></thead><tbody>{records.map((item) => <tr key={item.id}><td><div className="person-cell"><span className="avatar avatar-small">{item.employee_name.slice(0, 1)}</span><span><b>{item.employee_name}</b><small>{item.employee_id}</small></span></div></td><td>{item.attendance_date}</td><td>{item.check_in_time?.slice(0, 5) ?? "—"}</td><td><LocationDetails address={item.check_in_location_name} latitude={item.check_in_latitude} longitude={item.check_in_longitude} label="Check-in" hasAttendanceTime={Boolean(item.check_in_time)} /></td><td>{item.check_out_time?.slice(0, 5) ?? "—"}</td><td><LocationDetails address={item.check_out_location_name} latitude={item.check_out_latitude} longitude={item.check_out_longitude} label="Check-out" hasAttendanceTime={Boolean(item.check_out_time)} /></td><td>{item.working_hours === null ? "—" : `${item.working_hours}h`}</td><td><span className={`status-tag ${item.status}`}>{item.status.replace("_", " ")}</span></td></tr>)}</tbody></table></div><p className="fine-print">Address lookup by <a href="https://www.openstreetmap.org/copyright" rel="noreferrer" target="_blank">OpenStreetMap contributors</a>.</p></> : <div className="empty-state"><span>◷</span><b>No attendance records for this date</b><p>Records appear when employees check in; none are generated automatically.</p></div>}
    </section>
  </AppShell>;
}
