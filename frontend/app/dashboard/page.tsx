import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import DashboardView, {
  type CreditScore,
  type DashboardOverview,
  type Offering,
  type PaymentMethod,
  type RevenuePoint,
  type Transaction,
} from "./dashboard-view";

export const dynamic = "force-dynamic";

async function getData<T>(apiUrl: string, endpoint: string): Promise<T> {
  const cookieStore = await cookies();
  const token = cookieStore.get("access_token");
  if (!token) {
    redirect("/login");
  }

  const response = await fetch(`${apiUrl}${endpoint}`, {
    headers: {
      Authorization: `Bearer ${token.value}`,
    },
    cache: "no-store",
  });

  if (response.status === 401) {
    redirect("/login");
  }
  if (!response.ok) {
    throw new Error(`Unable to load dashboard data (${response.status})`);
  }

  return response.json() as Promise<T>;
}

export default async function DashboardPage() {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL?.replace(/\/+$/, "");
  if (!apiUrl) {
    throw new Error("Dashboard API is not configured");
  }

  const [transactions, revenue, topOfferings, overview, paymentMethods, creditScore] =
    await Promise.all([
      getData<Transaction[]>(apiUrl, "/api/transactions"),
      getData<RevenuePoint[]>(apiUrl, "/api/revenue"),
      getData<Offering[]>(apiUrl, "/api/top-offerings"),
      getData<DashboardOverview>(apiUrl, "/api/overview"),
      getData<PaymentMethod[]>(apiUrl, "/api/payment-methods"),
      getData<CreditScore>(apiUrl, "/api/credit-score"),
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
