import Link from "next/link";

export default function AppHomePage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-gray-50 px-5">
      <section className="w-full max-w-lg rounded-2xl border border-gray-200 bg-white p-8 shadow-sm">
        <p className="text-sm font-medium text-gray-500">ZakaScore app</p>
        <h1 className="mt-2 text-3xl font-semibold text-gray-900">Your business workspace</h1>
        <p className="mt-4 text-gray-600">
          This installable app shell is ready. Sign in while online to access your dashboard.
          Offline transaction capture and the on-device assistant will be added in the next frontend pass.
        </p>
        <div className="mt-6 flex flex-wrap gap-3">
          <Link href="/login" className="rounded-lg bg-gray-900 px-5 py-3 text-sm font-medium text-white">
            Sign in
          </Link>
          <Link href="/" className="rounded-lg border border-gray-300 px-5 py-3 text-sm font-medium text-gray-700">
            Visit ZakaScore
          </Link>
        </div>
      </section>
    </main>
  );
}
