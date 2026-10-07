import { redirect } from "next/navigation";
import { getAuth } from "@/lib/auth/server";
import { createBackendAccessToken } from "@/lib/backend-token";
import DashboardView, {
  type CreditScore,
  type DashboardOverview,
  type Offering,
  type PaymentMethod,
  type RevenuePoint,
  type Transaction,
} from "./dashboard-view";

export const dynamic = "force-dynamic";

async function getData<T>(apiUrl: string, endpoint: string, token: string): Promise<T> {
  const response = await fetch(`${apiUrl}${endpoint}`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
    cache: "no-store",
  });

  if (response.status === 401) {
    redirect("/login");
  }
  if (response.status === 403) {
    redirect("/connect");
  }
  if (!response.ok) {
    throw new Error(`Unable to load dashboard data (${response.status})`);
  }

  return response.json() as Promise<T>;
}

export default async function DashboardPage() {
  const { data: session, error } = await getAuth().getSession();
  if (error) {
    throw new Error("Unable to verify your sign-in session");
  }
  if (!session?.user?.id) {
    redirect("/login");
  }

  const apiUrl = (process.env.BACKEND_API_URL ?? process.env.NEXT_PUBLIC_API_URL)?.replace(/\/+$/, "");
  if (!apiUrl) {
    throw new Error("Dashboard API is not configured");
  }
  const token = await createBackendAccessToken(session.user.id);

  const [transactions, revenue, topOfferings, overview, paymentMethods, creditScore] =
    await Promise.all([
      getData<Transaction[]>(apiUrl, "/api/transactions", token),
      getData<RevenuePoint[]>(apiUrl, "/api/revenue", token),
      getData<Offering[]>(apiUrl, "/api/top-offerings", token),
      getData<DashboardOverview>(apiUrl, "/api/overview", token),
      getData<PaymentMethod[]>(apiUrl, "/api/payment-methods", token),
      getData<CreditScore>(apiUrl, "/api/credit-score", token),
    ]);

  return (
    <DashboardView
      transactions={transactions}
      revenue={revenue}
      offerings={topOfferings}
      overview={overview}
      paymentMethods={paymentMethods}
      creditScore={creditScore}
    />
  );
}
