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
  pwaMode?: boolean;
}

async function getData<T>(
  apiUrl: string,
  endpoint: string,
  token: string,
  merchantId?: string,
  loginPath = "/login?next=%2Fdashboard",
): Promise<T> {
  const headers = new Headers({ Authorization: `Bearer ${token}` });
  if (merchantId) headers.set("X-Merchant-Id", merchantId);
  const response = await fetch(`${apiUrl}${endpoint}`, {
    headers,
    cache: "no-store",
  });

  if (response.status === 401) {
    redirect(loginPath);
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
  pwaMode = false,
}: {
  searchParams: Promise<{ business?: string }>;
  pwaMode?: boolean;
}) {
  const loginPath = pwaMode ? "/login?next=%2Fworkspace%2Fdashboard" : "/login?next=%2Fdashboard";
  const auth = getAuth();
  const { data: session, error } = await auth.getSession();
  if (error) {
    throw new Error("Unable to verify your sign-in session");
  }
  if (!session?.user?.id) {
    redirect(loginPath);
  }
  const { data: accessToken, error: tokenError } = await auth.token();
  if (tokenError) {
    throw new Error("Unable to obtain an access token");
  }
  if (!accessToken?.token) {
    redirect(loginPath);
  }

  const apiUrl = (
    process.env.BACKEND_API_URL ?? process.env.NEXT_PUBLIC_API_URL
  )?.replace(/\/+$/, "");
  if (!apiUrl) {
    throw new Error("Dashboard API is not configured");
  }

  const token = accessToken.token;
  const { business: requestedBusinessId } = await searchParams;
  const workspace = await getData<BusinessList>(apiUrl, "/api/businesses", token, undefined, loginPath);
  const selectedBusiness = requestedBusinessId
    ? workspace.businesses.find((business) => business.merchant_id === requestedBusinessId)
    : workspace.businesses.find(
        (business) => business.merchant_id === workspace.selected_merchant_id,
      );
  if (!selectedBusiness) {
    redirect(pwaMode ? "/workspace/dashboard" : "/dashboard");
  }
  const selectedMerchantId = selectedBusiness.merchant_id;
  const [transactions, revenue, topOfferings, overview, paymentMethods, creditScore] =
    await Promise.all([
      getData<Transaction[]>(apiUrl, "/api/transactions", token, selectedMerchantId, loginPath),
      getData<RevenuePoint[]>(apiUrl, "/api/revenue", token, selectedMerchantId, loginPath),
      getData<Offering[]>(apiUrl, "/api/top-offerings", token, selectedMerchantId, loginPath),
      getData<DashboardOverview>(apiUrl, "/api/overview", token, selectedMerchantId, loginPath),
      getData<PaymentMethod[]>(apiUrl, "/api/payment-methods", token, selectedMerchantId, loginPath),
      getData<CreditScore>(apiUrl, "/api/credit-score", token, selectedMerchantId, loginPath),
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
      pwaMode={pwaMode}
    />
  );
}
