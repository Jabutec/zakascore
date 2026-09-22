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
  const [transactions, revenue, topOfferings] = await Promise.all([
    getData("/api/transactions"),
    getData("/api/revenue"),
    getData("/api/top-offerings"),
  ]);

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <h1 className="text-2xl font-semibold text-gray-900">Dashboard</h1>
      <p className="text-gray-500 mt-2 mb-8">Welcome — you're logged in.</p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
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