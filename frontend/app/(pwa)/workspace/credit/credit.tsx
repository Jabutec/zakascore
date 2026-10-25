"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { authClient } from "@/lib/auth/client";

// Put your logo file in frontend/public and set its filename here (same one used on the dashboard).
const LOGO_SRC = "/logo.png";

const CREDIT_PATH = "/workspace/credit";

export interface Business {
  merchant_id: string;
  business_name: string;
  role: "owner" | "admin" | "employee" | "viewer";
  stores: {
    store_id: string;
    store_name: string;
    pwa_logging_enabled: boolean;
  }[];
}

export interface CreditFactor {
  key: string;
  label: string;
  description: string;
  score: number;
  weight_pct: number;
  points_available: number;
  status: "strong" | "ok" | "focus";
}

export interface CreditTip {
  factor: string | null;
  impact_points: number | null;
  text: string;
}

export interface CreditMetrics {
  weeks_scored: number;
  weeks_of_history: number;
  total_revenue_zar: number;
  typical_weekly_revenue_zar: number;
  quiet_week_revenue_zar: number;
  revenue_growth_pct: number | null;
  trading_weeks: number;
  weeks_without_sales: number;
}

export interface CreditForecast {
  expected_zar: number;
  low_zar: number;
  high_zar: number;
  direction: "up" | "down" | "steady" | null;
  based_on_weeks: number;
  confidence: "low" | "medium";
}

export interface CreditThisWeek {
  week_start: string;
  revenue_zar: number;
  active_days: number;
  days_left: number;
  share_of_typical_week_pct: number | null;
}

export interface CreditProgress {
  weeks_of_history: number;
  weeks_required: number;
  weeks_remaining: number;
  available_from: string | null;
}

export interface CreditProfile {
  state: "no_data" | "building" | "scored";
  plan: "insights" | "full";
  as_of: string;
  score: number | null;
  band: string | null;
  maturity: "early" | "growing" | "established" | null;
  score_change: number | null;
  window: { start: string; end: string } | null;
  weeks_scored: number;
  factors: CreditFactor[] | null;
  tips: CreditTip[];
  metrics: CreditMetrics | null;
  forecast: CreditForecast | null;
  this_week: CreditThisWeek | null;
  progress: CreditProgress | null;
  locked: string[];
  disclaimer: string;
}

interface CreditProfileViewProps {
  profile: CreditProfile;
  businesses: Business[];
  selectedBusiness: Business;
}

const currency = new Intl.NumberFormat("en-ZA", {
  style: "currency",
  currency: "ZAR",
  maximumFractionDigits: 0,
});

function formatCurrency(value: number) {
  return currency.format(value);
}

function formatDay(value: string, options: Intl.DateTimeFormatOptions = {}) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("en-ZA", { day: "numeric", month: "short", ...options }).format(date);
}

function titleCase(value: string) {
  return value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

const MATURITY_TEXT: Record<NonNullable<CreditProfile["maturity"]>, string> = {
  early: "Early score. It will settle as your history grows.",
  growing: "Growing score. More weeks of history make it steadier.",
  established: "Established score, built on a full 12 weeks.",
};

const STATUS_TEXT: Record<CreditFactor["status"], string> = {
  strong: "Strong",
  ok: "Okay",
  focus: "Room to improve",
};

const DIRECTION_TEXT = { up: "Trending up", down: "Trending down", steady: "Steady" } as const;

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
    case "scores":
      return <svg {...common}><path d="m12 3 8 4.5v9L12 21l-8-4.5v-9L12 3Z" /><path d="m8.5 12 2.2 2.2 4.8-5" /></svg>;
    case "insights":
      return <svg {...common}><path d="M9 18h6M10 21h4M8.2 14.5a7 7 0 1 1 7.6 0c-.8.6-1.3 1.3-1.5 2.5h-4.6c-.2-1.2-.7-1.9-1.5-2.5Z" /></svg>;
    case "reports":
      return <svg {...common}><path d="M6 3.5h8l4 4V20H6z" /><path d="M14 3.5V8h4M9 12h6M9 15.5h6" /></svg>;
    case "settings":
      return <svg {...common}><path d="M12 8.5a3.5 3.5 0 1 0 0 7 3.5 3.5 0 0 0 0-7Z" /><path d="m19.4 15 .1.1 1.3 1-1.5 2.6-1.6-.6a7.6 7.6 0 0 1-1.5.9l-.3 1.7h-3l-.3-1.7a7.6 7.6 0 0 1-1.5-.9l-1.6.6L8 16.1l1.3-1a7.2 7.2 0 0 1 0-1.8l-1.3-1 1.5-2.6 1.6.6a7.6 7.6 0 0 1 1.5-.9l.3-1.7h3l.3 1.7a7.6 7.6 0 0 1 1.5.9l1.6-.6 1.5 2.6-1.3 1a7.2 7.2 0 0 1 0 1.7Z" transform="translate(-1 -1)" /></svg>;
    case "bell":
      return <svg {...common}><path d="M18 9a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4" /></svg>;
    case "trend":
      return <svg {...common}><path d="m4 16 5-5 4 3 7-8M14 6h6v6" /></svg>;
    case "menu":
      return <svg {...common}><path d="M4 7h16M4 12h16M4 17h16" /></svg>;
    case "close":
      return <svg {...common}><path d="M6 6l12 12M18 6 6 18" /></svg>;
    case "log":
      return <svg {...common}><path d="M12 20h9" /><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z" /></svg>;
    case "lock":
      return <svg {...common}><rect x="5" y="11" width="14" height="9" rx="2" /><path d="M8 11V8a4 4 0 0 1 8 0v3" /></svg>;
    default:
      return null;
  }
}

/* A section the merchant's plan doesn't include. No data is sent for it, so there is nothing to unblur. */
function LockedCard({ title, text, wide = false }: { title: string; text: string; wide?: boolean }) {
  return (
    <article className={`panel ${wide ? "intelligence-strip" : "composition-panel"} cp-locked`}>
      <span className="intelligence-icon"><Icon name="lock" size={18} /></span>
      <div className="section-heading"><div><p className="eyebrow">Included in the Full plan</p><h2>{title}</h2></div></div>
      <p>{text}</p>
    </article>
  );
}

function changeText(profile: CreditProfile) {
  if (profile.locked.includes("score_change")) return "Full plan";
  const change = profile.score_change;
  if (change === null) return "After 8 weeks";
  if (change === 0) return "No change";
  return `${change > 0 ? "+" : "−"}${Math.abs(change).toFixed(1)} points`;
}

export default function CreditProfileView({ profile, businesses, selectedBusiness }: CreditProfileViewProps) {
  const router = useRouter();
  const [signOutError, setSignOutError] = useState("");
  const [menuOpen, setMenuOpen] = useState(false);

  // Mobile drawer: lock page scroll while open and close with Escape.
  useEffect(() => {
    document.body.classList.toggle("menu-open", menuOpen);
    if (!menuOpen) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") setMenuOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => {
      window.removeEventListener("keydown", onKey);
      document.body.classList.remove("menu-open");
    };
  }, [menuOpen]);

  async function signOut() {
    setSignOutError("");
    try {
      const result = await authClient.signOut();
      if (result.error) {
        setSignOutError(result.error.message || "Unable to sign out.");
        return;
      }
      router.replace("/login");
      router.refresh();
    } catch {
      setSignOutError("Could not reach Neon Auth. Check your connection and try again.");
    }
  }

  const isLocked = (key: string) => profile.locked.includes(key);
  const scored = profile.state === "scored" && profile.score !== null;
  const score = profile.score ?? 0;
  const factorLabels = new Map((profile.factors ?? []).map((factor) => [factor.key, factor.label]));
  const week = profile.this_week;

  const navItems: { icon: string; label: string; href: string; active?: boolean }[] = [
    { icon: "log", label: "Log a sale", href: "/workspace" },
    { icon: "overview", label: "Dashboard", href: "/workspace/dashboard" },
    { icon: "reports", label: "Reports", href: "/workspace/dashboard#revenue-chart" },
    { icon: "scores", label: "Credit", href: CREDIT_PATH, active: true },
    { icon: "insights", label: "Insights", href: "/workspace/dashboard#insights" },
    { icon: "bell", label: "Notifications", href: "/workspace/dashboard#notifications-panel" },
  ];

  return (
    <div className="dashboard-shell">
      {menuOpen && (
        <button
          type="button"
          className="sidebar-backdrop"
          aria-label="Close menu"
          onClick={() => setMenuOpen(false)}
        />
      )}

      <aside
        id="dashboard-sidebar"
        className={`sidebar${menuOpen ? " open" : ""}`}
        aria-label="Main navigation"
        onClick={(event) => {
          // Close the mobile drawer after tapping any link inside it.
          if ((event.target as HTMLElement).closest("a")) setMenuOpen(false);
        }}
      >
        <button
          type="button"
          className="icon-button sidebar-close"
          aria-label="Close menu"
          onClick={() => setMenuOpen(false)}
        >
          <Icon name="close" size={20} />
        </button>

        <Link className="brand" href="/workspace/dashboard" aria-label="ZakaScore overview">
          <span className="brand-mark">
            <Image
              src={LOGO_SRC}
              alt=""
              fill
              sizes="40px"
              style={{ objectFit: "cover", transform: "scale(1.45)" }}
              priority
            />
          </span>
          <span className="brand-name">Zaka<span>Score</span></span>
        </Link>

        <Link className="btn-lime sidebar-new-sale" href="/workspace">
          <Icon name="log" size={17} />
          <span>New sale</span>
        </Link>

        <div className="sidebar-label">WORKSPACE</div>
        <nav className="nav-list">
          {navItems.map((item) => (
            <Link
              className={`nav-link${item.active ? " active" : ""}`}
              href={item.href}
              key={item.label}
              aria-current={item.active ? "page" : undefined}
            >
              <Icon name={item.icon} />
              <span>{item.label}</span>
            </Link>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="nav-link nav-link-disabled" aria-disabled="true" title="Settings are coming soon">
            <Icon name="settings" />
            <span>Settings</span>
          </div>
          <button type="button" className="nav-link" onClick={signOut}>
            <span>Sign out</span>
          </button>
          {signOutError && <p role="alert" className="form-error">{signOutError}</p>}
          <div className="sidebar-identity">
            <div className="avatar avatar-small">ZS</div>
            <div className="identity-copy">
              <strong>{selectedBusiness.business_name}</strong>
              <span>{titleCase(selectedBusiness.role)} · {selectedBusiness.stores.length} {selectedBusiness.stores.length === 1 ? "store" : "stores"}</span>
            </div>
          </div>
        </div>
      </aside>

      <main className="dashboard-main" id="credit-profile">
        <header className="topbar">
          <div className="topbar-left">
            <button
              type="button"
              className="icon-button menu-button"
              aria-label={menuOpen ? "Close menu" : "Open menu"}
              aria-expanded={menuOpen}
              aria-controls="dashboard-sidebar"
              onClick={() => setMenuOpen((open) => !open)}
            >
              <Icon name="menu" size={20} />
            </button>
            <div className="breadcrumb"><span>Workspace</span><span className="breadcrumb-divider">/</span><strong>Credit</strong></div>
          </div>
          <div className="topbar-actions">
            <div className="profile-button" id="profile">
              <span className="avatar">ZS</span>
              <span className="profile-copy"><strong>{selectedBusiness.business_name}</strong><span>{titleCase(selectedBusiness.role)} access</span></span>
            </div>
          </div>
        </header>

        <div className="page-content">
          <section className="page-heading">
            <div>
              <h1>Credit profile</h1>
              <p className="page-description">How the sales you record add up, and what would strengthen them.</p>
            </div>
            <div className="report-date">
              {businesses.length > 1 ? (
                <label className="business-switcher">
                  <span>Business</span>
                  <select
                    aria-label="Select business workspace"
                    value={selectedBusiness.merchant_id}
                    onChange={(event) => router.push(`${CREDIT_PATH}?business=${encodeURIComponent(event.target.value)}`)}
                  >
                    {businesses.map((business) => (
                      <option key={business.merchant_id} value={business.merchant_id}>{business.business_name}</option>
                    ))}
                  </select>
                </label>
              ) : <><span className="live-dot" /> {selectedBusiness.business_name}</>}
            </div>
          </section>

          {/* Score summary, or progress towards the first score */}
          {scored ? (
            <section className="analytics-grid" aria-label="Score summary">
              <article className="panel composition-panel">
                <div className="section-heading">
                  <div><p className="eyebrow">YOUR SCORE</p><h2>{profile.band}</h2></div>
                </div>
                {profile.maturity && <p className="intelligence-copy">{MATURITY_TEXT[profile.maturity]}</p>}
                <div className="insight-divider" />
                {profile.window && (
                  <div className="insight-stat">
                    <span>Weeks counted</span>
                    <strong>{formatDay(profile.window.start)} to {formatDay(profile.window.end)}</strong>
                  </div>
                )}
                <div className="insight-stat"><span>Change over 4 weeks</span><strong>{changeText(profile)}</strong></div>
                <p className="panel-description cp-note">{profile.disclaimer}</p>
              </article>

              <article className="metric-card score-card">
                <div className="metric-label"><span>ZakaScore</span><span className="metric-icon"><Icon name="scores" size={17} /></span></div>
                <div className="score-gauge" role="img" aria-label={`Credit score ${score.toFixed(0)} out of 100`}>
                  <svg className="score-gauge-arc" viewBox="0 0 124 76" aria-hidden="true">
                    <path className="score-gauge-track" d="M 8 68 A 54 54 0 0 1 116 68" pathLength="100" />
                    <path
                      className="score-gauge-progress"
                      d="M 8 68 A 54 54 0 0 1 116 68"
                      pathLength="100"
                      strokeDasharray="100"
                      strokeDashoffset={100 - Math.min(Math.max(score, 0), 100)}
                    />
                  </svg>
                  <div className="score-gauge-value">
                    <strong>{score.toFixed(0)}</strong>
                    <span>/ 100</span>
                  </div>
                </div>
                <div className="metric-footnote">
                  <span className="metric-accent"><Icon name="trend" size={14} /> {profile.band}</span>
                  <span>{profile.weeks_scored} weeks of history</span>
                </div>
              </article>
            </section>
          ) : (
            <section className="cp-row" aria-label="Score progress">
              <article className="panel composition-panel">
                <div className="section-heading">
                  <div>
                    <p className="eyebrow">{profile.state === "no_data" ? "GETTING STARTED" : "BUILDING YOUR SCORE"}</p>
                    <h2>{profile.state === "no_data" ? "Log your first sale" : "Your first score is on its way"}</h2>
                  </div>
                </div>
                {profile.progress && profile.state === "building" && (
                  <>
                    <div
                      className="cp-steps"
                      role="img"
                      aria-label={`${profile.progress.weeks_of_history} of ${profile.progress.weeks_required} weeks of history`}
                    >
                      {Array.from({ length: profile.progress.weeks_required }, (_, index) => (
                        <span key={index} className={index < (profile.progress?.weeks_of_history ?? 0) ? "done" : ""} />
                      ))}
                    </div>
                    <p className="intelligence-copy">
                      {profile.progress.weeks_of_history} of {profile.progress.weeks_required} complete weeks.
                      {profile.progress.available_from &&
                        profile.progress.weeks_remaining > 0 &&
                        ` Your first score arrives on ${formatDay(profile.progress.available_from, { weekday: "long" })}.`}
                    </p>
                  </>
                )}
                {profile.state === "no_data" && (
                  <p className="intelligence-copy">Your score is built from the sales you record. Add your first one to start your history.</p>
                )}
                <Link className="btn-lime" href="/workspace">Log a sale</Link>
                <p className="panel-description cp-note">{profile.disclaimer}</p>
              </article>
            </section>
          )}

          {/* Tips + the week in progress */}
          <section className="lower-grid cp-row" aria-label="Tips and this week">
            <article className="panel composition-panel">
              <div className="section-heading">
                <div><p className="eyebrow">WHAT WOULD HELP</p><h2>Tips</h2></div>
              </div>
              {profile.tips.map((tip, index) => (
                <div key={`${tip.factor ?? "general"}-${index}`}>
                  {index > 0 && <div className="insight-divider" />}
                  {tip.factor && (
                    <p className="eyebrow">
                      {factorLabels.get(tip.factor) ?? titleCase(tip.factor)}
                      {tip.impact_points !== null && ` · up to ${tip.impact_points} points`}
                    </p>
                  )}
                  <p className="intelligence-copy">{tip.text}</p>
                </div>
              ))}
              {isLocked("more_tips") && (
                <p className="panel-description">More tips, ranked by impact, are included in the Full plan.</p>
              )}
            </article>

            {week && (
              <article className="panel composition-panel">
                <div className="section-heading">
                  <div><p className="eyebrow">THIS WEEK SO FAR</p><h2>Week in progress</h2></div>
                  <span className="table-count">Since {formatDay(week.week_start, { weekday: "short" })}</span>
                </div>
                <div className="insight-stat"><span>Sales recorded</span><strong>{formatCurrency(week.revenue_zar)}</strong></div>
                <div className="insight-stat"><span>Days with sales</span><strong>{week.active_days}</strong></div>
                <div className="insight-stat"><span>Days left</span><strong>{week.days_left}</strong></div>
                {week.share_of_typical_week_pct !== null && (
                  <div className="insight-stat"><span>Of a typical week</span><strong>{week.share_of_typical_week_pct}%</strong></div>
                )}
                <p className="panel-description cp-note">The week in progress counts towards your score once it ends.</p>
              </article>
            )}
          </section>

          {/* Everything below needs a score */}
          {scored && (
            <>
              {profile.factors ? (
                <section className="panel intelligence-strip" aria-label="Score breakdown">
                  <div className="section-heading">
                    <div><p className="eyebrow">WHAT DRIVES YOUR SCORE</p><h2>Score breakdown</h2></div>
                    <span className="table-count">4 factors</span>
                  </div>
                  <div className="offering-list">
                    {profile.factors.map((factor) => (
                      <div className="offering-row" key={factor.key}>
                        <div className="offering-copy"><span>{factor.label}</span><strong>{factor.score} / 100</strong></div>
                        <div
                          className="offering-track"
                          role="img"
                          aria-label={`${factor.label}: ${factor.score} out of 100`}
                        >
                          <span className="offering-highlight" style={{ width: `${Math.min(Math.max(factor.score, 0), 100)}%` }} />
                        </div>
                        <p className="panel-description">
                          {factor.description} {STATUS_TEXT[factor.status]}, and it counts for {factor.weight_pct}% of your score.
                        </p>
                      </div>
                    ))}
                  </div>
                </section>
              ) : isLocked("factors") ? (
                <div className="cp-row">
                  <LockedCard
                    wide
                    title="Score breakdown"
                    text="See the four things that make up your score, how each one is doing, and which has the most room to improve."
                  />
                </div>
              ) : null}

              <section className="lower-grid cp-row" aria-label="Forecast and figures">
                {profile.forecast ? (
                  <article className="panel composition-panel">
                    <div className="section-heading">
                      <div><p className="eyebrow">LOOKING AHEAD</p><h2>Next week</h2></div>
                      {profile.forecast.direction && (
                        <span className={`status-pill${profile.forecast.direction === "up" ? " status-active" : ""}`}>
                          <span />{DIRECTION_TEXT[profile.forecast.direction]}
                        </span>
                      )}
                    </div>
                    <p className="metric-value">
                      {formatCurrency(profile.forecast.low_zar)} – {formatCurrency(profile.forecast.high_zar)}
                    </p>
                    <p className="intelligence-copy">
                      Most of your weeks land in this range, with a typical week around {formatCurrency(profile.forecast.expected_zar)}.
                    </p>
                    <p className="panel-description">
                      Based on your last {profile.forecast.based_on_weeks} weeks, {profile.forecast.confidence} confidence.
                      A simple range from your own sales, not a promise of what will happen.
                    </p>
                  </article>
                ) : isLocked("forecast") ? (
                  <LockedCard title="Next week" text="A simple range for next week’s takings, built from your own recent weeks." />
                ) : null}

                {profile.metrics ? (
                  <article className="panel composition-panel">
                    <div className="section-heading">
                      <div><p className="eyebrow">THE NUMBERS</p><h2>Supporting figures</h2></div>
                      <span className="table-count">Last {profile.metrics.weeks_scored} weeks</span>
                    </div>
                    <div className="insight-stat"><span>Sales recorded</span><strong>{formatCurrency(profile.metrics.total_revenue_zar)}</strong></div>
                    <div className="insight-stat"><span>Typical week</span><strong>{formatCurrency(profile.metrics.typical_weekly_revenue_zar)}</strong></div>
                    <div className="insight-stat"><span>Quieter week</span><strong>{formatCurrency(profile.metrics.quiet_week_revenue_zar)}</strong></div>
                    <div className="insight-stat"><span>Trading weeks</span><strong>{profile.metrics.trading_weeks} of {profile.metrics.weeks_scored}</strong></div>
                    <div className="insight-stat"><span>Weeks with no sales</span><strong>{profile.metrics.weeks_without_sales}</strong></div>
                    <div className="insight-stat">
                      <span>Recent vs earlier weeks</span>
                      <strong>
                        {profile.metrics.revenue_growth_pct === null
                          ? "Not available yet"
                          : `${profile.metrics.revenue_growth_pct > 0 ? "+" : ""}${profile.metrics.revenue_growth_pct.toFixed(1)}%`}
                      </strong>
                    </div>
                  </article>
                ) : isLocked("metrics") ? (
                  <LockedCard title="Supporting figures" text="Your typical week, your quieter weeks, trading weeks and growth, in one place." />
                ) : null}
              </section>
            </>
          )}

          <section className="panel intelligence-strip" aria-label="How your score is built">
            <div className="section-heading">
              <div><p className="eyebrow">HOW IT WORKS</p><h2>How your score is built</h2></div>
            </div>
            <p className="intelligence-copy">
              Your score comes only from the sales you record in ZakaScore. It looks at how steady your weekly
              takings are, whether your recent weeks are growing, how much you typically take in a week, and
              how consistently you trade. Weeks run Monday to Sunday, and the week in progress isn’t counted
              until it ends. Sales you haven’t recorded can’t count, so logging everything is the best way to
              show an accurate picture.
            </p>
          </section>

          <footer className="page-footer"><span>ZakaScore Financial Intelligence</span><span>South Africa · ZAR</span></footer>
        </div>
      </main>
    </div>
  );
}