"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import AppShell from "@/components/AppShell";
import CameraCapture from "@/components/CameraCapture";
import { api } from "@/services/api";
import type { AttendanceRecord, Employee } from "@/types";

export default function EmployeeDetailsPage() {
  const params = useParams<{ id: string }>();
  const id = decodeURIComponent(params.id);
  const [employee, setEmployee] = useState<Employee | null>(null);
  const [records, setRecords] = useState<AttendanceRecord[]>([]);
  const [error, setError] = useState("");
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [faceSamples, setFaceSamples] = useState<string[]>([]);
  const [faceSaving, setFaceSaving] = useState(false);
  const [faceNotice, setFaceNotice] = useState("");
  useEffect(() => {
    Promise.all([api<Employee>(`/employees/${encodeURIComponent(id)}`), api<AttendanceRecord[]>(`/attendance/employee/${encodeURIComponent(id)}`)])
      .then(([profile, history]) => { setEmployee(profile); setRecords(history); })
      .catch((cause: unknown) => setError(cause instanceof Error ? cause.message : "Unable to load employee."));
  }, [id]);
  async function saveProfile(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!employee) return;
    setSaving(true); setError("");
    const values = Object.fromEntries(new FormData(event.currentTarget).entries());
    try {
      const updated = await api<Employee>(`/employees/${encodeURIComponent(id)}`, { method: "PUT", body: JSON.stringify(values) });
      setEmployee(updated);
      setEditing(false);
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Unable to save employee."); }
    finally { setSaving(false); }
  }
  async function enrollFace() {
    if (faceSamples.length < 3) {
      setError("Capture at least three clear face samples before enrolling.");
      return;
    }
    setFaceSaving(true);
    setError("");
    setFaceNotice("");
    try {
      const result = await api<{ samples_registered: number }>(
        `/employees/${encodeURIComponent(id)}/face/register`,
        { method: "POST", body: JSON.stringify({ samples: faceSamples }) },
      );
      setEmployee((current) => current ? { ...current, face_registered: true } : current);
      setFaceSamples([]);
      setFaceNotice(`${result.samples_registered} face samples were enrolled successfully.`);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Unable to enroll the employee's face.");
    } finally {
      setFaceSaving(false);
    }
  }
  return <AppShell><div className="page-heading"><div><div className="eyebrow"><Link href="/admin/employees">EMPLOYEES</Link> &nbsp;/&nbsp; PROFILE</div><h1>{employee?.full_name ?? "Employee profile"}</h1><p>Employee record and recent attendance history.</p></div><div className="heading-actions"><Link className="button-quiet" href="/admin/employees">← Directory</Link>{employee && <button className="button-outline" onClick={() => setEditing((value) => !value)} type="button">{editing ? "Cancel editing" : "Edit profile"}</button>}</div></div>
    {error && <div className="alert alert-error">{error}</div>}
    {employee && <><section className="panel profile-panel"><div className="profile-hero"><span className="avatar avatar-large">{employee.full_name.slice(0, 1)}</span><div><h2>{employee.full_name}</h2><p>{employee.employee_id} · {employee.designation || "Employee"}</p></div><span className={`status-tag ${employee.status}`}>{employee.status}</span></div>{editing ? <form className="profile-edit-form" onSubmit={(event) => void saveProfile(event)}><div className="form-grid"><label>Full name<input defaultValue={employee.full_name} name="full_name" required /></label><label>Email<input defaultValue={employee.email} name="email" required type="email" /></label><label>Phone<input defaultValue={employee.phone ?? ""} name="phone" /></label><label>Department<input defaultValue={employee.department ?? ""} name="department" required /></label><label>Designation<input defaultValue={employee.designation ?? ""} name="designation" /></label><label>Joining date<input defaultValue={employee.joining_date} name="joining_date" required type="date" /></label></div><div className="form-actions"><button className="button-primary" disabled={saving} type="submit">{saving ? "Saving…" : "Save changes"}</button></div></form> : <div className="profile-grid"><div><small>EMAIL</small><b>{employee.email}</b></div><div><small>PHONE</small><b>{employee.phone || "—"}</b></div><div><small>DEPARTMENT</small><b>{employee.department || "—"}</b></div><div><small>JOINED</small><b>{employee.joining_date}</b></div><div><small>FACE PROFILE</small><b>{employee.face_registered ? "Enrolled" : "Not enrolled"}</b></div></div>}</section>
    <section className="panel camera-panel employee-face-enrollment"><div className="panel-head"><div><div className="eyebrow">FACE ENROLLMENT</div><h2>{employee.face_registered ? "Update face samples" : "Enroll employee face"}</h2></div><span className="sample-count">{faceSamples.length}/3</span></div><p className="panel-subtitle">Capture at least three separate clear images of this employee. Raw images are not saved.</p>{faceNotice && <div className="alert alert-success" role="status">{faceNotice}</div>}<CameraCapture label="Capture sample" onCapture={(image) => { setFaceSamples((current) => current.length < 10 ? [...current, image] : current); setError(""); setFaceNotice(""); }} /><div className="sample-list">{faceSamples.map((_, index) => <div className="sample-item" key={index}><span className="sample-check">✓</span> Sample {index + 1}<button aria-label={`Remove sample ${index + 1}`} onClick={() => setFaceSamples((current) => current.filter((__, sampleIndex) => sampleIndex !== index))} type="button">×</button></div>)}</div><div className="form-actions"><button className="button-primary" disabled={faceSaving || faceSamples.length < 3} onClick={() => void enrollFace()} type="button">{faceSaving ? "Enrolling…" : employee.face_registered ? "Replace face enrollment" : "Enroll face"}</button></div></section>
    <section className="panel history-panel"><div className="panel-head"><div><div className="eyebrow">ATTENDANCE</div><h2>Recent history</h2></div></div>{records.length ? <div className="table-wrap"><table><thead><tr><th>DATE</th><th>CHECK-IN</th><th>CHECK-OUT</th><th>HOURS</th><th>STATUS</th></tr></thead><tbody>{records.map((item) => <tr key={item.id}><td>{item.attendance_date}</td><td>{item.check_in_time?.slice(0, 5) || "—"}</td><td>{item.check_out_time?.slice(0, 5) || "—"}</td><td>{item.working_hours ?? "—"}</td><td><span className={`status-tag ${item.status}`}>{item.status.replace("_", " ")}</span></td></tr>)}</tbody></table></div> : <div className="empty-state"><b>No attendance history yet</b><p>Records will appear after this employee checks in.</p></div>}</section></>}
  </AppShell>;
}
