import { cookies } from "next/headers";

async function getData(endpoint: string) {
  const cookieStore = await cookies();
  const token = cookieStore.get("access_token");

  const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}${endpoint}`, {
    headers: {
      Authorization: `Bearer ${token?.value}`,
    },
    cache: "no-store",
  });

  return res.json();
}

export default async function DashboardPage() {
  const [transactions, revenue, topOfferings, overview, paymentMethods, creditScore] = await Promise.all([
    getData("/api/transactions"),
    getData("/api/revenue"),
    getData("/api/top-offerings"),
    getData("/api/overview"),
    getData("/api/payment-methods"),
    getData("/api/credit-score"),
  ]);

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <h1 className="text-2xl font-semibold text-gray-900">Dashboard</h1>
      <p className="text-gray-500 mt-2 mb-8">Welcome — you're logged in.</p>

      <div className="bg-white rounded-lg border border-gray-200 p-6 mb-8">
        <h2 className="text-sm font-medium text-gray-500 mb-4">Business Health</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4 text-sm">
          <div>
            <p className="text-gray-500">Total Revenue</p>
            <p className="font-semibold text-lg">R{overview.total_revenue}</p>
          </div>
          <div>
            <p className="text-gray-500">Transactions</p>
            <p className="font-semibold text-lg">{overview.transaction_count}</p>
          </div>
          <div>
            <p className="text-gray-500">Avg. Transaction</p>
            <p className="font-semibold text-lg">R{overview.average_transaction}</p>
          </div>
          <div>
            <p className="text-gray-500">Growth</p>
            <p className="font-semibold text-lg">
              {overview.revenue_growth_pct !== null ? `${overview.revenue_growth_pct}%` : "N/A"}
            </p>
          </div>
        </div>
        <div className="space-y-1">
          {overview.insights.map((insight: string, i: number) => (
            <p key={i} className="text-sm text-gray-700">• {insight}</p>
          ))}
        </div>
      </div>
      <div className="bg-white rounded-lg border border-gray-200 p-6 mb-8">
        <h2 className="text-sm font-medium text-gray-500 mb-4">Credit Score</h2>
        <p className="text-3xl font-bold">
          {creditScore.credit_score !== null ? creditScore.credit_score : "N/A"}
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-sm font-medium text-gray-500 mb-4">Top Offerings</h2>
          <div className="space-y-3">
            {topOfferings.map((o: any) => (
              <div key={o.offering} className="flex justify-between text-sm">
                <span className="text-gray-700">{o.offering}</span>
                <span className="font-medium">R{o.revenue}</span>
              </div>
            ))}
          </div>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-sm font-medium text-gray-500 mb-4">Payment Methods</h2>
          <div className="space-y-2">
            {paymentMethods.map((p: any) => (
              <div key={p.payment_method} className="flex justify-between text-sm">
                <span className="text-gray-700 capitalize">{p.payment_method}</span>
                <span className="font-medium">R{p.amount}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-sm font-medium text-gray-500 mb-4">Revenue by Day</h2>
          <div className="space-y-2">
            {revenue.map((r: any) => (
              <div key={r.date} className="flex justify-between text-sm">
                <span className="text-gray-500">{r.date}</span>
                <span className="font-medium">R{r.revenue}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <h2 className="text-sm font-medium text-gray-500 mb-4">Recent Transactions</h2>
      <div className="space-y-2">
        {transactions.map((t: any) => (
          <div key={t.transaction_id} className="bg-white rounded-lg border border-gray-200 p-4">
            <p className="font-medium">R{t.amount_zar}</p>
            <p className="text-sm text-gray-500">{t.transaction_date}</p>
          </div>
        ))}
      </div>
    </div>
  );
}