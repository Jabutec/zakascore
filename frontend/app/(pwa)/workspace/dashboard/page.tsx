import Link from "next/link";
import { redirect } from "next/navigation";
import { getAuth } from "@/lib/auth/server";
import DashboardView, {
  type Business,
  type CreditScore,
  type DashboardOverview,
  type Offering,
  type PaymentMethod,
  type RevenuePoint,
  type Transaction,
} from "./dashboard";

export const dynamic = "force-dynamic";

interface BusinessList {
  selected_merchant_id: string;
  businesses: Business[];
}

export interface DashboardPageProps {
  searchParams: Promise<{ business?: string }>;
}

const DASHBOARD_PATH = "/workspace/dashboard";
const LOGIN_PATH = "/login?next=%2Fworkspace%2Fdashboard";
const CONNECT_PATH = "/workspace/connect";

// Patient on purpose: a waking database or slow backend gets plenty of time.
const API_TIMEOUT_MS = 30_000;

function wait(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

// Hard stop for calls that can otherwise stall for minutes without ever failing
// (the sign-in service can accept a connection and then never answer).
const AUTH_TIMEOUT_MS = 12_000;

function withTimeout<T>(promise: Promise<T>, ms: number): Promise<T> {
  return new Promise<T>((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error(`Timed out after ${ms}ms`)), ms);
    promise.then(
      (value) => {
        clearTimeout(timer);
        resolve(value);
      },
      (error) => {
        clearTimeout(timer);
        reject(error);
      },
    );
  });
}

// Temporary diagnostics: prints when a step starts and how long it took. If a step prints
// "start" but never "done", that's where the page is stuck. Safe to delete later.
async function timed<T>(label: string, run: () => Promise<T>): Promise<T> {
  const startedAt = Date.now();
  console.log(`[dashboard] ${label}: start`);
  try {
    return await run();
  } finally {
    console.log(`[dashboard] ${label}: done in ${Date.now() - startedAt}ms`);
  }
}

/*
  Neon Auth returns { data, error } rather than throwing, and its network calls
  can time out transiently. One retry smooths over those blips.
*/
async function retryAuth<T extends { error: unknown }>(
  call: () => Promise<T>,
  attempts = 3,
): Promise<T> {
  let result!: T;
  for (let i = 0; i < attempts; i++) {
    try {
      result = await withTimeout(call(), AUTH_TIMEOUT_MS);
      if (!result.error) return result;
    } catch (error) {
      result = { data: null, error } as unknown as T;
    }
    if (i < attempts - 1) await wait(800);
  }
  return result;
}

function AuthUnavailable() {
  return (
    <main className="dashboard-state">
      <div className="dashboard-state-card">
        <h1>We couldn’t verify your sign-in</h1>
        <p>The sign-in service didn’t respond in time. Your data is safe. Please try again.</p>
        <Link
          className="state-retry-button"
          href={DASHBOARD_PATH}
          prefetch={false}
        >
          Try again
        </Link>
      </div>
    </main>
  );
}

async function getData<T>(
  apiUrl: string,
  endpoint: string,
  token: string,
  merchantId?: string,
): Promise<T> {
  const headers = new Headers({ Authorization: `Bearer ${token}` });
  if (merchantId) headers.set("X-Merchant-Id", merchantId);

  // Retry once on a network error or 5xx (e.g. the database waking up), after a calm pause.
  // No redirects happen inside this loop.
  let response: Response | null = null;
  for (let attempt = 0; attempt < 2; attempt++) {
    try {
      response = await fetch(`${apiUrl}${endpoint}`, {
        headers,
        cache: "no-store",
        signal: AbortSignal.timeout(API_TIMEOUT_MS),
      });
      if (response.status < 500) break;
    } catch {
      response = null;
    }
    if (attempt === 0) await wait(1500);
  }

  if (!response) {
    throw new Error("Unable to reach the dashboard API");
  }
  if (response.status === 401) {
    redirect(LOGIN_PATH);
  }
  if (response.status === 403) {
    redirect(CONNECT_PATH);
  }
  if (!response.ok) {
    throw new Error(`Unable to load dashboard data (${response.status})`);
  }

  return response.json() as Promise<T>;
}

export default async function DashboardPage({ searchParams }: DashboardPageProps) {
  const auth = getAuth();
  const { data: session, error } = await timed("getSession", () => retryAuth(() => auth.getSession()));
  if (error) {
    return <AuthUnavailable />;
  }
  if (!session?.user?.id) {
    redirect(LOGIN_PATH);
  }
  const { data: accessToken, error: tokenError } = await timed("auth token", () => retryAuth(() => auth.token()));
  if (tokenError) {
    return <AuthUnavailable />;
  }
  if (!accessToken?.token) {
    redirect(LOGIN_PATH);
  }

  const apiUrl = (
    process.env.BACKEND_API_URL ?? process.env.NEXT_PUBLIC_API_URL
  )?.replace(/\/+$/, "");
  if (!apiUrl) {
    throw new Error("Dashboard API is not configured");
  }

  const token = accessToken.token;
  const { business: requestedBusinessId } = await searchParams;
  const workspace = await timed("businesses", () => getData<BusinessList>(apiUrl, "/api/businesses", token));
  const selectedBusiness = requestedBusinessId
    ? workspace.businesses.find((business) => business.merchant_id === requestedBusinessId)
    : workspace.businesses.find(
      (business) => business.merchant_id === workspace.selected_merchant_id,
    );
  if (!selectedBusiness) {
    redirect(DASHBOARD_PATH);
  }
  const selectedMerchantId = selectedBusiness.merchant_id;
  const [transactions, revenue, topOfferings, overview, paymentMethods, creditScore] =
    await timed("backend batch", () => Promise.all([
      getData<Transaction[]>(apiUrl, "/api/transactions", token, selectedMerchantId),
      getData<RevenuePoint[]>(apiUrl, "/api/revenue", token, selectedMerchantId),
      getData<Offering[]>(apiUrl, "/api/top-offerings", token, selectedMerchantId),
      getData<DashboardOverview>(apiUrl, "/api/overview", token, selectedMerchantId),
      getData<PaymentMethod[]>(apiUrl, "/api/payment-methods", token, selectedMerchantId),
      getData<CreditScore>(apiUrl, "/api/credit-score", token, selectedMerchantId),
    ]));

  return (
    <DashboardView
      transactions={transactions}
      revenue={revenue}
      offerings={topOfferings}
      overview={overview}
      paymentMethods={paymentMethods}
      creditScore={creditScore}
      businesses={workspace.businesses}
      selectedBusiness={selectedBusiness}
    />
  );
}