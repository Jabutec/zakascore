import { cookies } from "next/headers";
import DashboardView, {
  type CreditScore,
  type DashboardOverview,
  type Offering,
  type PaymentMethod,
  type RevenuePoint,
  type Transaction,
} from "./dashboard-view";

async function getData<T>(endpoint: string): Promise<T> {
  const cookieStore = await cookies();
  const token = cookieStore.get("access_token");
  const response = await fetch(
    `${process.env.NEXT_PUBLIC_API_URL}${endpoint}`,
    {
      headers: {
        Authorization: `Bearer ${token?.value}`,
      },
      cache: "no-store",
    },
  );

  if (!response.ok) {
    throw new Error(`Unable to load dashboard data (${response.status})`);
  }

  return response.json() as Promise<T>;
}

export default async function DashboardPage() {
  const [transactions, revenue, topOfferings, overview, paymentMethods, creditScore] =
    await Promise.all([
      getData<Transaction[]>("/api/transactions"),
      getData<RevenuePoint[]>("/api/revenue"),
      getData<Offering[]>("/api/top-offerings"),
      getData<DashboardOverview>("/api/overview"),
      getData<PaymentMethod[]>("/api/payment-methods"),
      getData<CreditScore>("/api/credit-score"),
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
