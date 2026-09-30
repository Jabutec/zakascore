"use client";

export default function DashboardError({
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <main className="dashboard-state" role="alert">
      <div className="dashboard-state-card">
        <span className="brand-mark" aria-hidden="true">Z</span>
        <h1>Dashboard data is unavailable</h1>
        <p>
          We couldn’t load your business data from ZakaScore. Check your
          connection and try again.
        </p>
        <button className="state-retry-button" onClick={reset} type="button">
          Try again
        </button>
      </div>
    </main>
  );
}
