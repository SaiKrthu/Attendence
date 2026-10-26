"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import Protected from "@/components/Protected";
import { SignOutButton, useAuth } from "@/components/AuthProvider";

const adminLinks = [
  ["/admin/dashboard", "Overview", "01"],
  ["/admin/employees", "Employees", "02"],
  ["/admin/signups", "Sign-up requests", "03"],
  ["/admin/attendance", "Attendance", "04"],
  ["/admin/reports", "Reports", "05"],
  ["/admin/settings", "Settings", "06"],
];

export default function AppShell({
  children,
  role = "admin",
}: {
  children: React.ReactNode;
  role?: "admin" | "employee";
}) {
  const pathname = usePathname();
  const { user } = useAuth();
  const links = role === "admin" ? adminLinks : [["/employee/attendance", "Attendance", "01"], ["/employee/profile", "My profile", "02"]];
  return (
    <Protected role={role}>
      <div className="app-frame">
        <aside className="sidebar">
          <div className="side-label">{role === "admin" ? "WORKSPACE" : "MY SPACE"}</div>
          <nav className="side-nav">
            {links.map(([href, label, number]) => (
              <Link className={`nav-link ${pathname === href ? "active" : ""}`} href={href} key={href}>
                <span className="nav-number">{number}</span>{label}
              </Link>
            ))}
            {role === "admin" && <Link className={`nav-link ${pathname.startsWith("/admin/employees/new") ? "active" : ""}`} href="/admin/employees/new"><span className="nav-number">＋</span>Add employee</Link>}
          </nav>
          <div className="sidebar-bottom">
            <div className="secure-note"><span className="status-dot" /> Workspace secure<br /><span>Face data is processed on your server</span></div>
            <div className="user-mini"><span className="avatar">{user?.full_name?.slice(0, 1) || user?.email.slice(0, 1).toUpperCase()}</span><span className="user-mini-copy"><b>{user?.full_name || user?.email}</b><small>{role === "admin" ? "Administrator" : user?.employee_id}</small></span></div>
          </div>
        </aside>
        <div className="main-column">
          <header className="topbar">
            <div><span className="topbar-title">{role === "admin" ? "Attendance workspace" : "Employee portal"}</span></div>
            <div className="topbar-right"><span className="today-label">{new Intl.DateTimeFormat("en", { dateStyle: "medium" }).format(new Date())}</span><span className="online-pill"><span className="status-dot" /> Live</span><SignOutButton /></div>
          </header>
          <main className="page-content">{children}</main>
          <footer className="footer-note">ATTENDANT · EMPLOYEE ATTENDANCE MANAGEMENT</footer>
        </div>
      </div>
    </Protected>
  );
}
