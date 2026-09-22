import { cookies } from "next/headers";

async function getTransactions() {
  const cookieStore = await cookies();
  const token = cookieStore.get("access_token");

  const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/transactions`, {
    headers: {
      Authorization: `Bearer ${token?.value}`,
    },
    cache: "no-store",
  });

  return res.json();
}

export default async function DashboardPage() {
  const transactions = await getTransactions();

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <h1 className="text-2xl font-semibold text-gray-900">Dashboard</h1>
      <p className="text-gray-500 mt-2">Welcome — you're logged in.</p>

      <div className="mt-6 space-y-2">
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