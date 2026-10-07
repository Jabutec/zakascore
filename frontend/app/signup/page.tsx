"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { authClient } from "@/lib/auth/client";

export default function SignUpPage() {
  const router = useRouter();
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setLoading(true);

    try {
      const form = new FormData(event.currentTarget);
      const result = await authClient.signUp.email({
        name: String(form.get("name")),
        email: String(form.get("email")),
        password: String(form.get("password")),
      });

      if (result.error) {
        setError(result.error.message || "Unable to create your account.");
        return;
      }

      const session = await authClient.getSession();
      if (session.data?.user) {
        router.replace("/connect");
        router.refresh();
        return;
      }
      router.replace("/login?account-created=1");
    } catch {
      setError("Could not reach Neon Auth. Check your connection and try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
      <section className="w-full max-w-sm rounded-2xl border border-gray-200 bg-white p-8 shadow-sm">
        <h1 className="mb-1 text-2xl font-semibold text-gray-900">Create your account</h1>
        <p className="mb-6 text-sm text-gray-500">Create your own secure account to manage an authorized business.</p>

        {error && (
          <p role="alert" className="mb-4 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
            {error}
          </p>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <label className="block text-sm text-gray-700">
            Name
            <input name="name" autoComplete="name" required className="mt-1 w-full rounded-lg border border-gray-300 px-4 py-2.5" />
          </label>
          <label className="block text-sm text-gray-700">
            Email
            <input name="email" type="email" autoComplete="email" required className="mt-1 w-full rounded-lg border border-gray-300 px-4 py-2.5" />
          </label>
          <label className="block text-sm text-gray-700">
            Password
            <input name="password" type="password" autoComplete="new-password" minLength={8} required className="mt-1 w-full rounded-lg border border-gray-300 px-4 py-2.5" />
          </label>
          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-lg bg-gray-900 py-2.5 text-sm font-medium text-white disabled:opacity-50"
          >
            {loading ? "Creating account..." : "Create account"}
          </button>
        </form>
        <p className="mt-5 text-center text-sm text-gray-600">
          Already have an account?{" "}
          <Link href="/login" className="font-medium text-gray-900 underline">
            Sign in
          </Link>
        </p>
      </section>
    </main>
  );
}
