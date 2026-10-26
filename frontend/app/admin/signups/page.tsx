"use client";

import { useCallback, useEffect, useState } from "react";
import AppShell from "@/components/AppShell";
import { api } from "@/services/api";
import type { EmployeeSignupRequest } from "@/types";

type SignupPageResult = {
  items: EmployeeSignupRequest[];
  page: number;
  page_size: number;
  total: number;
};

export default function AdminSignupsPage() {
  const [requests, setRequests] = useState<EmployeeSignupRequest[]>([]);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const load = useCallback(async () => {
    setError("");
    try {
      const result = await api<SignupPageResult>(`/signup-requests?page=${page}&page_size=50`);
      setRequests(result.items);
      setTotal(result.total);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Unable to load sign-up requests.");
    }
  }, [page]);

  useEffect(() => { void load(); }, [load]);

  async function review(request: EmployeeSignupRequest, approve: boolean) {
    if (!approve && !window.confirm(`Reject the sign-up request from ${request.full_name}?`)) return;
    setBusyId(request.id);
    setError("");
    setNotice("");
    try {
      if (approve) {
        await api(`/signup-requests/${request.id}/approve`, { method: "POST" });
        setNotice(`${request.full_name} was approved. Enroll their face before they use attendance check-in.`);
      } else {
        await api<void>(`/signup-requests/${request.id}`, { method: "DELETE" });
        setNotice(`The request from ${request.full_name} was rejected.`);
      }
      setTotal((count) => Math.max(0, count - 1));
      if (requests.length === 1 && page > 1) setPage((current) => current - 1);
      else await load();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Unable to update this request.");
    } finally {
      setBusyId(null);
    }
  }

  const pageCount = Math.max(1, Math.ceil(total / 50));

  return (
    <AppShell>
      <div className="page-heading">
        <div><div className="eyebrow">ADMIN REVIEW</div><h1>Sign-up requests</h1><p>Review employee registrations before creating their accounts.</p></div>
      </div>
      {error && <div className="alert alert-error" role="alert">{error}</div>}
      {notice && <div className="alert alert-success" role="status">{notice}</div>}
      <section className="panel directory-panel">
        <div className="panel-head"><div><span className="eyebrow">PENDING APPLICATIONS</span><h2>{total} waiting for review</h2></div></div>
        {requests.length ? (
          <>
            <div className="table-wrap"><table><thead><tr><th>APPLICANT</th><th>EMPLOYEE ID</th><th>DEPARTMENT</th><th>DESIGNATION</th><th>SUBMITTED</th><th>REVIEW</th></tr></thead>
              <tbody>{requests.map((request) => <tr key={request.id}>
                <td><div className="person-cell"><span className="avatar avatar-small">{request.full_name.slice(0, 1)}</span><span><b>{request.full_name}</b><small>{request.email}</small></span></div></td>
                <td>{request.employee_id}</td><td>{request.department}</td><td>{request.designation || "—"}</td>
                <td>{new Date(request.created_at).toLocaleDateString()}</td>
                <td className="actions-cell"><button disabled={busyId !== null} onClick={() => void review(request, true)} type="button">{busyId === request.id ? "Saving…" : "Approve"}</button><button className="danger-text" disabled={busyId !== null} onClick={() => void review(request, false)} type="button">Reject</button></td>
              </tr>)}</tbody></table></div>
            {pageCount > 1 && <div className="signup-pagination"><button className="button-outline" disabled={page <= 1} onClick={() => setPage((current) => current - 1)} type="button">Previous</button><span>Page {page} of {pageCount}</span><button className="button-outline" disabled={page >= pageCount} onClick={() => setPage((current) => current + 1)} type="button">Next</button></div>}
          </>
        ) : <div className="empty-state"><span>✓</span><b>No pending sign-up requests</b><p>New employee registrations will appear here for review.</p></div>}
      </section>
    </AppShell>
  );
}
