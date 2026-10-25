import Link from "next/link";
import { redirect } from "next/navigation";
import { getAuth } from "@/lib/auth/server";
import CreditProfileView, { type Business, type CreditProfile } from "./credit";

export const dynamic = "force-dynamic";

interface BusinessList {
  selected_merchant_id: string;
  businesses: Business[];
}

export interface CreditPageProps {
  searchParams: Promise<{ business?: string }>;
}

const CREDIT_PATH = "/workspace/credit";
const LOGIN_PATH = "/login?next=%2Fworkspace%2Fcredit";
const CONNECT_PATH = "/workspace/connect";

// Patient on purpose: a waking database or slow backend gets plenty of time.
const API_TIMEOUT_MS = 30_000;

// Hard stop for calls that can otherwise stall without ever failing
// (the sign-in service can accept a connection and then never answer).
const AUTH_TIMEOUT_MS = 12_000;

function wait(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

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

/*
  Neon Auth returns { data, error } rather than throwing, and its network calls
  can time out transiently. A couple of retries smooth over those blips.
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
        <Link className="state-retry-button" href={CREDIT_PATH} prefetch={false}>
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
    throw new Error("Unable to reach the credit API");
  }
  if (response.status === 401) {
    redirect(LOGIN_PATH);
  }
  if (response.status === 403) {
    redirect(CONNECT_PATH);
  }
  if (!response.ok) {
    throw new Error(`Unable to load credit data (${response.status})`);
  }

  return response.json() as Promise<T>;
}

export default async function CreditPage({ searchParams }: CreditPageProps) {
  const auth = getAuth();
  const { data: session, error } = await retryAuth(() => auth.getSession());
  if (error) {
    return <AuthUnavailable />;
  }
  if (!session?.user?.id) {
    redirect(LOGIN_PATH);
  }
  const { data: accessToken, error: tokenError } = await retryAuth(() => auth.token());
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
    throw new Error("Credit API is not configured");
  }

  const token = accessToken.token;
  const { business: requestedBusinessId } = await searchParams;
  const workspace = await getData<BusinessList>(apiUrl, "/api/businesses", token);
  const selectedBusiness = requestedBusinessId
    ? workspace.businesses.find((business) => business.merchant_id === requestedBusinessId)
    : workspace.businesses.find(
      (business) => business.merchant_id === workspace.selected_merchant_id,
    );
  if (!selectedBusiness) {
    redirect(CREDIT_PATH);
  }

  const profile = await getData<CreditProfile>(
    apiUrl,
    "/api/credit-profile",
    token,
    selectedBusiness.merchant_id,
  );

  return (
    <CreditProfileView
      profile={profile}
      businesses={workspace.businesses}
      selectedBusiness={selectedBusiness}
    />
  );
}