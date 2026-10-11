export default function DashboardLoading() {
  return (
    <main className="dashboard-state" aria-live="polite">
      <div className="dashboard-state-card">
        <span className="brand-mark" aria-hidden="true">Z</span>
        <h1>Loading your dashboard</h1>
        <p>Fetching the latest business data.</p>
      </div>
    </main>
  );
}
