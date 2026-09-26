"use client";

import { useState } from "react";

export interface Transaction {
  transaction_id: string;
  amount_zar: number;
  quantity: number | null;
  raw_message: string | null;
  transaction_date: string;
}

export interface RevenuePoint {
  date: string;
  revenue: number;
}

export interface Offering {
  offering: string;
  revenue: number;
  quantity: number;
}

export interface PaymentMethod {
  payment_method: string;
  amount: number;
}

export interface DashboardOverview {
  total_revenue: number;
  transaction_count: number;
  average_transaction: number;
  revenue_growth_pct: number | null;
  revenue_trend: string;
  transaction_activity: string;
  revenue_stability: string;
  activity_status: string;
  digital_payment_adoption: string;
  insights: string[];
}

export interface CreditScore {
  credit_score: number | null;
}

interface DashboardViewProps {
  transactions: Transaction[];
  revenue: RevenuePoint[];
  offerings: Offering[];
  overview: DashboardOverview;
  paymentMethods: PaymentMethod[];
  creditScore: CreditScore;
}

const currency = new Intl.NumberFormat("en-ZA", {
  style: "currency",
  currency: "ZAR",
  maximumFractionDigits: 0,
});

function formatCurrency(value: number) {
  return currency.format(value);
}

function formatDate(value: string, options: Intl.DateTimeFormatOptions = {}) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("en-ZA", {
    day: "numeric",
    month: "short",
    ...options,
  }).format(date);
}

function titleCase(value: string) {
  return value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function Icon({ name, size = 19 }: { name: string; size?: number }) {
  const common = {
    fill: "none",
    height: size,
    stroke: "currentColor",
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
    strokeWidth: 1.7,
    viewBox: "0 0 24 24",
    width: size,
    "aria-hidden": true as const,
  };

  switch (name) {
    case "overview":
      return <svg {...common}><rect x="3.5" y="3.5" width="7" height="7" rx="1" /><rect x="13.5" y="3.5" width="7" height="7" rx="1" /><rect x="3.5" y="13.5" width="7" height="7" rx="1" /><rect x="13.5" y="13.5" width="7" height="7" rx="1" /></svg>;
    case "merchants":
      return <svg {...common}><path d="M4 9.5 5.5 4h13L20 9.5" /><path d="M4 9.5a2.5 2.5 0 0 0 5 0 2.5 2.5 0 0 0 5 0 2.5 2.5 0 0 0 5 0" /><path d="M5.5 12v8h13v-8M9 20v-5h6v5" /></svg>;
    case "data":
      return <svg {...common}><path d="M4 19.5h16M6.5 16V10M12 16V5M17.5 16v-3" /></svg>;
    case "scores":
      return <svg {...common}><path d="m12 3 8 4.5v9L12 21l-8-4.5v-9L12 3Z" /><path d="m8.5 12 2.2 2.2 4.8-5" /></svg>;
    case "insights":
      return <svg {...common}><path d="M9 18h6M10 21h4M8.2 14.5a7 7 0 1 1 7.6 0c-.8.6-1.3 1.3-1.5 2.5h-4.6c-.2-1.2-.7-1.9-1.5-2.5Z" /></svg>;
    case "reports":
      return <svg {...common}><path d="M6 3.5h8l4 4V20H6z" /><path d="M14 3.5V8h4M9 12h6M9 15.5h6" /></svg>;
    case "settings":
      return <svg {...common}><path d="M12 8.5a3.5 3.5 0 1 0 0 7 3.5 3.5 0 0 0 0-7Z" /><path d="m19.4 15 .1.1 1.3 1-1.5 2.6-1.6-.6a7.6 7.6 0 0 1-1.5.9l-.3 1.7h-3l-.3-1.7a7.6 7.6 0 0 1-1.5-.9l-1.6.6L8 16.1l1.3-1a7.2 7.2 0 0 1 0-1.8l-1.3-1 1.5-2.6 1.6.6a7.6 7.6 0 0 1 1.5-.9l.3-1.7h3l.3 1.7a7.6 7.6 0 0 1 1.5.9l1.6-.6 1.5 2.6-1.3 1a7.2 7.2 0 0 1 0 1.7Z" transform="translate(-1 -1)" /></svg>;
    case "search":
      return <svg {...common}><circle cx="10.8" cy="10.8" r="6.3" /><path d="m16 16 4.2 4.2" /></svg>;
    case "bell":
      return <svg {...common}><path d="M18 9a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4" /></svg>;
    case "arrow":
      return <svg {...common}><path d="M5 12h14M13 6l6 6-6 6" /></svg>;
    case "trend":
      return <svg {...common}><path d="m4 16 5-5 4 3 7-8M14 6h6v6" /></svg>;
    default:
      return null;
  }
}

function RevenueChart({ points }: { points: RevenuePoint[] }) {
  if (points.length === 0) {
    return <div className="chart-empty">Revenue data will appear here once transactions are recorded.</div>;
  }

  const values = points.map((point) => point.revenue);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const spread = max - min || Math.max(max, 1);
  const coordinates = values.map((value, index) => ({
    x: points.length === 1 ? 50 : 4 + (index / (points.length - 1)) * 92,
    y: 82 - ((value - min) / spread) * 64,
  }));
  const line = coordinates
    .map((point, index) => `${index === 0 ? "M" : "L"} ${point.x} ${point.y}`)
    .join(" ");
  const area = `${line} L ${coordinates[coordinates.length - 1].x} 92 L ${coordinates[0].x} 92 Z`;
  const labelIndices = [...new Set([0, Math.floor((points.length - 1) / 3), Math.floor(((points.length - 1) * 2) / 3), points.length - 1])];

  return (
    <>
      <div className="chart-plot">
        <div className="chart-y-labels" aria-hidden="true">
          {[max, (max + min) / 2, min].map((value, index) => (
            <span key={index}>{formatCurrency(value)}</span>
          ))}
        </div>
        <svg className="revenue-chart" viewBox="0 0 100 100" preserveAspectRatio="none" role="img" aria-label="Revenue by date">
          {[24, 53, 82].map((y) => <line key={y} x1="0" x2="100" y1={y} y2={y} className="chart-gridline" />)}
          <path d={area} className="chart-area" />
          <path d={line} className="chart-line" />
          {coordinates.map((point, index) => (
            <circle key={`${points[index].date}-${index}`} cx={point.x} cy={point.y} r="1.1" className="chart-point" />
          ))}
        </svg>
      </div>
      <div className="chart-x-labels" aria-hidden="true">
        {labelIndices.map((index) => (
          <span key={points[index].date}>{formatDate(points[index].date, { month: "short" })}</span>
        ))}
      </div>
    </>
  );
}

export default function DashboardView({
  transactions,
  revenue,
  offerings,
  overview,
  paymentMethods,
  creditScore,
}: DashboardViewProps) {
  const [query, setQuery] = useState("");
  const [period, setPeriod] = useState<7 | 30 | 0>(30);

  const chartPoints = (() => {
    if (period === 0) return revenue;
    const latestDate = revenue.length > 0 ? new Date(revenue[revenue.length - 1].date) : null;
    if (!latestDate || Number.isNaN(latestDate.getTime())) return revenue.slice(-period);
    const startDate = new Date(latestDate);
    startDate.setDate(startDate.getDate() - period + 1);
    return revenue.filter((point) => new Date(point.date) >= startDate);
  })();

  const filteredTransactions = (() => {
    const normalizedQuery = query.trim().toLowerCase();
    if (!normalizedQuery) return transactions;
    return transactions.filter((transaction) =>
      `${transaction.transaction_id} ${transaction.amount_zar} ${transaction.quantity ?? ""} ${transaction.raw_message ?? ""} ${transaction.transaction_date}`
        .toLowerCase()
        .includes(normalizedQuery),
    );
  })();

  const growth = overview.revenue_growth_pct;
  const businessStatus = titleCase(overview.activity_status);
  const score = creditScore.credit_score;
  const intelligence = [
    { label: "Revenue trend", value: titleCase(overview.revenue_trend) },
    { label: "Transaction activity", value: titleCase(overview.transaction_activity) },
    { label: "Cash-flow consistency", value: titleCase(overview.revenue_stability) },
    { label: "Business activity", value: businessStatus },
    { label: "Score movement", value: "Not yet tracked" },
  ];
  const insight = overview.insights[0] ?? "Insights will appear as your transaction history grows.";

  return (
    <div className="dashboard-shell">
      <aside className="sidebar" aria-label="Main navigation">
        <a className="brand" href="#overview" aria-label="ZakaScore overview">
          <span className="brand-mark">Z</span>
          <span className="brand-name">Zaka<span>Score</span></span>
        </a>
        <div className="sidebar-label">WORKSPACE</div>
        <nav className="nav-list">
          {[
            ["overview", "Overview", "#overview"],
            ["merchants", "Merchants", "#business-portfolio"],
            ["data", "Financial data", "#financial-data"],
            ["scores", "Scores", "#score-overview"],
            ["insights", "Insights", "#insights"],
            ["reports", "Reports", "#revenue-chart"],
          ].map(([icon, label, href], index) => (
            <a
              className={`nav-link${index === 0 ? " active" : ""}`}
              href={href}
              key={label}
              aria-current={index === 0 ? "page" : undefined}
            >
              <Icon name={icon} />
              <span>{label}</span>
            </a>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="nav-link nav-link-disabled" aria-disabled="true" title="Settings are not available in this view">
            <Icon name="settings" />
            <span>Settings</span>
          </div>
          <div className="sidebar-identity">
            <div className="avatar avatar-small">ZS</div>
            <div className="identity-copy">
              <strong>Merchant account</strong>
              <span>Business profile</span>
            </div>
          </div>
        </div>
      </aside>

      <main className="dashboard-main" id="overview">
        <header className="topbar">
          <div className="breadcrumb"><span>Workspace</span><span className="breadcrumb-divider">/</span><strong>Overview</strong></div>
          <div className="topbar-actions">
            <label className="search-box">
              <Icon name="search" size={17} />
              <input
                type="search"
                aria-label="Search transactions"
                placeholder="Search activity"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
              />
            </label>
            <button className="icon-button notification-button" type="button" aria-label="Notifications">
              <Icon name="bell" size={18} />
              <span className="notification-dot" />
            </button>
            <div className="profile-button" id="profile">
              <span className="avatar">ZS</span>
              <span className="profile-copy"><strong>Merchant</strong><span>South Africa</span></span>
            </div>
          </div>
        </header>

        <div className="page-content">
          <section className="page-heading">
            <div>
              <p className="eyebrow">FINANCIAL INTELLIGENCE</p>
              <h1>Overview</h1>
              <p className="page-description">A clear view of your business performance and financial health.</p>
            </div>
            <div className="report-date"><span className="live-dot" /> Live business data</div>
          </section>

          <section className="metric-grid" aria-label="Business performance metrics" id="score-overview">
            <article className="metric-card score-card">
              <div className="metric-label"><span>ZakaScore</span><span className="metric-icon"><Icon name="scores" size={17} /></span></div>
              <div className="metric-value">{score === null ? "—" : score.toFixed(0)}<span className="metric-unit">/ 100</span></div>
              <div className="metric-footnote"><span className="metric-accent"><Icon name="trend" size={14} /> Credit health</span><span>Current score</span></div>
              <div className="score-track"><span style={{ width: `${score === null ? 0 : Math.min(Math.max(score, 0), 100)}%` }} /></div>
            </article>
            <article className="metric-card">
              <div className="metric-label"><span>Total revenue</span><span className="metric-icon"><Icon name="data" size={17} /></span></div>
              <div className="metric-value">{formatCurrency(overview.total_revenue)}</div>
              <div className="metric-footnote">
                <span className={growth !== null && growth > 0 ? "metric-accent" : "metric-neutral"}>
                  {growth === null ? "No comparison" : `${growth > 0 ? "+" : ""}${growth.toFixed(1)}%`}
                </span>
                <span>vs. previous period</span>
              </div>
            </article>
            <article className="metric-card">
              <div className="metric-label"><span>Transaction volume</span><span className="metric-icon"><Icon name="merchants" size={17} /></span></div>
              <div className="metric-value">{overview.transaction_count.toLocaleString("en-ZA")}</div>
              <div className="metric-footnote"><span className="metric-neutral">Recorded activity</span><span>All transactions</span></div>
            </article>
            <article className="metric-card">
              <div className="metric-label"><span>Average transaction</span><span className="metric-icon"><Icon name="reports" size={17} /></span></div>
              <div className="metric-value">{formatCurrency(overview.average_transaction)}</div>
              <div className="metric-footnote"><span className="metric-neutral">Per transaction</span><span>All-time average</span></div>
            </article>
          </section>

          <section className="analytics-grid">
            <article className="panel chart-panel" id="revenue-chart">
              <div className="panel-heading">
                <div>
                  <p className="eyebrow">PERFORMANCE</p>
                  <h2>Revenue trend</h2>
                  <p className="panel-description">Daily revenue across your business.</p>
                </div>
                <div className="period-switch" aria-label="Revenue chart period">
                  {([7, 30, 0] as const).map((value) => (
                    <button
                      aria-pressed={period === value}
                      className={period === value ? "selected" : ""}
                      key={value}
                      onClick={() => setPeriod(value)}
                      type="button"
                    >
                      {value === 0 ? "All" : `${value}D`}
                    </button>
                  ))}
                </div>
              </div>
              <div className="chart-legend"><span className="legend-mark" /> Revenue</div>
              <RevenueChart points={chartPoints} />
            </article>

            <aside className="panel intelligence-panel" id="insights">
              <div className="intelligence-topline"><span className="intelligence-icon"><Icon name="insights" size={20} /></span><span>BUSINESS INTELLIGENCE</span></div>
              <h2>Business intelligence</h2>
              <p className="intelligence-copy">{insight}</p>
              <div className="insight-divider" />
              <div className="insight-stat"><span>Digital payment adoption</span><strong>{titleCase(overview.digital_payment_adoption)}</strong></div>
              <div className="insight-stat"><span>Leading offering</span><strong>{offerings[0]?.offering ?? "Not available"}</strong></div>
              <a className="insight-link" href="#financial-data">View insights <Icon name="arrow" size={16} /></a>
            </aside>
          </section>

          <section className="intelligence-strip panel" aria-label="Financial intelligence indicators">
            <div className="strip-heading">
              <div><p className="eyebrow">FINANCIAL INTELLIGENCE</p><h2>Business signals</h2></div>
              <span className="strip-note">Based on recorded activity</span>
            </div>
            <div className="signal-grid">
              {intelligence.map((item) => (
                <div className="signal-item" key={item.label}>
                  <span className="signal-label">{item.label}</span>
                  <strong className={item.value === "Not yet tracked" || item.value === "Insufficient Data" ? "signal-muted" : ""}>{item.value}</strong>
                </div>
              ))}
            </div>
          </section>

          <section className="panel portfolio-panel" id="business-portfolio">
            <div className="section-heading">
              <div><p className="eyebrow">MERCHANT PROFILE</p><h2>Business performance</h2></div>
              <span className="table-count">1 business</span>
            </div>
            <div className="table-scroll">
              <table className="data-table">
                <thead><tr>
                  <th>Business</th><th>ZakaScore</th><th>Revenue</th><th>Transactions</th><th>Average transaction</th><th>Score change</th><th>Status</th>
                </tr></thead>
                <tbody><tr>
                  <td><div className="business-cell"><span className="business-mark">B</span><span><strong>Your business</strong><small>Merchant profile</small></span></div></td>
                  <td><strong className="score-cell">{score === null ? "—" : score.toFixed(0)}</strong></td>
                  <td>{formatCurrency(overview.total_revenue)}</td>
                  <td>{overview.transaction_count.toLocaleString("en-ZA")}</td>
                  <td>{formatCurrency(overview.average_transaction)}</td>
                  <td className="muted-cell">Not yet tracked</td>
                  <td><span className={`status-pill${overview.activity_status === "active" ? " status-active" : ""}`}><span />{businessStatus}</span></td>
                </tr></tbody>
              </table>
            </div>
          </section>

          <section className="lower-grid">
            <article className="panel activity-panel" id="financial-data">
              <div className="section-heading">
                <div><p className="eyebrow">FINANCIAL DATA</p><h2>Recent activity</h2></div>
                <span className="table-count">{filteredTransactions.length} records</span>
              </div>
              <div className="table-scroll">
                <table className="data-table activity-table">
                  <thead><tr><th>Transaction</th><th>Date</th><th>Units</th><th>Amount</th></tr></thead>
                  <tbody>
                    {filteredTransactions.slice(0, 8).map((transaction) => (
                      <tr key={transaction.transaction_id}>
                        <td><div className="transaction-cell"><span className="transaction-mark"><Icon name="data" size={16} /></span><span><strong>{transaction.raw_message?.trim() || "Business transaction"}</strong><small>Ref. {transaction.transaction_id.slice(0, 8)}</small></span></div></td>
                        <td>{formatDate(transaction.transaction_date)}</td>
                        <td>{transaction.quantity ?? "—"}</td>
                        <td><strong>{formatCurrency(transaction.amount_zar)}</strong></td>
                      </tr>
                    ))}
                    {filteredTransactions.length === 0 && (
                      <tr><td className="empty-row" colSpan={4}>{query ? "No transactions match your search." : "No transactions have been recorded yet."}</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </article>

            <aside className="panel composition-panel">
              <div className="section-heading">
                <div><p className="eyebrow">BUSINESS MIX</p><h2>Top offerings</h2></div>
              </div>
              {offerings.length > 0 ? (
                <div className="offering-list">
                  {offerings.slice(0, 4).map((offering, index) => {
                    const percentage = overview.total_revenue > 0
                      ? Math.min((offering.revenue / overview.total_revenue) * 100, 100)
                      : 0;
                    return (
                      <div className="offering-row" key={offering.offering}>
                        <div className="offering-copy"><span>{offering.offering}</span><strong>{formatCurrency(offering.revenue)}</strong></div>
                        <div className="offering-track"><span className={index === 0 ? "offering-highlight" : ""} style={{ width: `${percentage}%` }} /></div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <p className="empty-message">Offering data will appear as sales are recorded.</p>
              )}
              {paymentMethods.length > 0 && (
                <div className="payment-summary">
                  <p className="eyebrow">PAYMENT CHANNELS</p>
                  {paymentMethods.map((method) => (
                    <div className="payment-row" key={method.payment_method}>
                      <span>{titleCase(method.payment_method)}</span><strong>{formatCurrency(method.amount)}</strong>
                    </div>
                  ))}
                </div>
              )}
            </aside>
          </section>

          <footer className="page-footer"><span>ZakaScore Financial Intelligence</span><span>South Africa · ZAR</span></footer>
        </div>
      </main>
    </div>
  );
}
