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
} from "./dashboard-view";

export const dynamic = "force-dynamic";

interface BusinessList {
  selected_merchant_id: string;
  businesses: Business[];
}

async function getData<T>(
  apiUrl: string,
  endpoint: string,
  token: string,
  merchantId?: string,
): Promise<T> {
  const headers = new Headers({ Authorization: `Bearer ${token}` });
  if (merchantId) headers.set("X-Merchant-Id", merchantId);
  const response = await fetch(`${apiUrl}${endpoint}`, {
    headers,
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

export default async function DashboardPage({
  searchParams,
}: {
  searchParams: Promise<{ business?: string }>;
}) {
  const { data: session, error } = await getAuth().getSession();
  if (error) {
    throw new Error("Unable to verify your sign-in session");
  }
  if (!session?.user?.id || !session.session?.token) {
    redirect("/login");
  }

  const apiUrl = (
    process.env.BACKEND_API_URL ?? process.env.NEXT_PUBLIC_API_URL
  )?.replace(/\/+$/, "");
  if (!apiUrl) {
    throw new Error("Dashboard API is not configured");
  }

  const token = session.session.token;
  const { business: requestedBusinessId } = await searchParams;
  const workspace = await getData<BusinessList>(apiUrl, "/api/businesses", token);
  const selectedBusiness = requestedBusinessId
    ? workspace.businesses.find((business) => business.merchant_id === requestedBusinessId)
    : workspace.businesses.find(
        (business) => business.merchant_id === workspace.selected_merchant_id,
      );
  if (!selectedBusiness) {
    redirect("/dashboard");
  }
  const selectedMerchantId = selectedBusiness.merchant_id;
  const [transactions, revenue, topOfferings, overview, paymentMethods, creditScore] =
    await Promise.all([
      getData<Transaction[]>(apiUrl, "/api/transactions", token, selectedMerchantId),
      getData<RevenuePoint[]>(apiUrl, "/api/revenue", token, selectedMerchantId),
      getData<Offering[]>(apiUrl, "/api/top-offerings", token, selectedMerchantId),
      getData<DashboardOverview>(apiUrl, "/api/overview", token, selectedMerchantId),
      getData<PaymentMethod[]>(apiUrl, "/api/payment-methods", token, selectedMerchantId),
      getData<CreditScore>(apiUrl, "/api/credit-score", token, selectedMerchantId),
    ]);

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
