import AppShell from "@/components/AppShell";

export default function SettingsPage() {
  return <AppShell><div className="page-heading"><div><div className="eyebrow">WORKSPACE</div><h1>Settings</h1><p>Attendance rules are controlled by protected backend configuration.</p></div></div>
    <section className="panel settings-card"><div className="eyebrow">SERVER CONFIGURATION</div><h2>Attendance policy</h2><p>Change policy values using the backend environment variables, then restart the API.</p><div className="setting-row"><div><b>Workday start</b><small>WORK_START_TIME · local configured timezone</small></div><code>09:00 default</code></div><div className="setting-row"><div><b>Late grace period</b><small>LATE_AFTER_MINUTES · before marking as late</small></div><code>15 minutes default</code></div><div className="setting-row"><div><b>Timezone</b><small>TIMEZONE · IANA time zone name</small></div><code>Asia/Dhaka default</code></div><div className="alert alert-info">The defaults above are informational. The API remains the source of truth and reads actual values from its environment.</div></section>
  </AppShell>;
}
