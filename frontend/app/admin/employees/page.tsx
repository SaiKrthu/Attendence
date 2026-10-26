"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import AppShell from "@/components/AppShell";
import { api } from "@/services/api";
import type { Employee } from "@/types";

type EmployeeList = { items: Employee[]; total: number };

export default function EmployeesPage() {
  const [items, setItems] = useState<Employee[]>([]);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [error, setError] = useState("");
  const load = useCallback(() => {
    const query = new URLSearchParams();
    if (search) query.set("search", search);
    if (statusFilter) query.set("status", statusFilter);
    api<EmployeeList>(`/employees?${query}`).then((data) => setItems(data.items)).catch((cause: unknown) => setError(cause instanceof Error ? cause.message : "Unable to load employees."));
  }, [search, statusFilter]);
  useEffect(() => { load(); }, [load]);
  async function toggleStatus(employee: Employee) {
    setError("");
    try {
      await api<Employee>(`/employees/${encodeURIComponent(employee.employee_id)}/status`, {
        method: "PATCH",
        body: JSON.stringify({ status: employee.status === "active" ? "inactive" : "active" }),
      });
      load();
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Status update failed."); }
  }
  return <AppShell><div className="page-heading"><div><div className="eyebrow">YOUR PEOPLE</div><h1>Employees</h1><p>Manage your team and their attendance profiles.</p></div><Link className="button-primary" href="/admin/employees/new">＋ &nbsp;Add employee</Link></div>
    {error && <div className="alert alert-error">{error}</div>}
    <section className="panel directory-panel"><div className="toolbar"><label className="search-field"><span>⌕</span><input onChange={(e) => setSearch(e.target.value)} placeholder="Search name, ID or email…" value={search} /></label><select aria-label="Filter by status" onChange={(e) => setStatusFilter(e.target.value)} value={statusFilter}><option value="">All statuses</option><option value="active">Active</option><option value="inactive">Inactive</option></select><span className="result-count">{items.length} employees</span></div>
      {items.length ? <div className="table-wrap"><table><thead><tr><th>EMPLOYEE</th><th>DEPARTMENT</th><th>DESIGNATION</th><th>FACE PROFILE</th><th>STATUS</th><th /></tr></thead><tbody>{items.map((employee) => <tr key={employee.id}><td><div className="person-cell"><span className="avatar avatar-small">{employee.full_name.slice(0, 1)}</span><span><b>{employee.full_name}</b><small>{employee.employee_id} · {employee.email}</small></span></div></td><td>{employee.department || "—"}</td><td>{employee.designation || "—"}</td><td><span className={`status-tag ${employee.face_registered ? "present" : "pending"}`}>{employee.face_registered ? "Enrolled" : "Not enrolled"}</span></td><td><span className={`status-tag ${employee.status}`}>{employee.status}</span></td><td className="actions-cell"><Link href={`/admin/employees/${encodeURIComponent(employee.employee_id)}`}>View</Link><button onClick={() => void toggleStatus(employee)} type="button">{employee.status === "active" ? "Deactivate" : "Reactivate"}</button></td></tr>)}</tbody></table></div> : <div className="empty-state"><span>◎</span><b>No employees found</b><p>Try another search or add an employee to your team.</p><Link className="text-link" href="/admin/employees/new">Add your first employee →</Link></div>}
    </section>
  </AppShell>;
}
