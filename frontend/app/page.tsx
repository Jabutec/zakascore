import Link from "next/link";

export default function Home() {
  return (
    <main className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-4xl font-bold">ZakaScore</h1>

        <p className="mt-4 text-gray-600">
          Financial data and credit scoring for South African SMEs.
        </p>

        <Link
          href="/login"
          className="inline-block mt-6 rounded-lg bg-gray-900 px-6 py-3 text-white"
        >
          Login
        </Link>
      </div>
    </main>
  );
}