"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

export default function ConnectPage() {
  const router = useRouter();
  const [code, setCode] = useState("");
  const [businessName, setBusinessName] = useState("");
  const [storeName, setStoreName] = useState("");
  const [newConnectCode, setNewConnectCode] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function redeemCode(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setLoading(true);

    try {
      const response = await fetch("/api/backend/api/connect-codes/redeem", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code }),
      });
      const result = await response.json();
      if (!response.ok) {
        setError(result.detail || "Unable to connect this account.");
        return;
      }
      router.replace("/dashboard");
      router.refresh();
    } catch {
      setError("Could not reach ZakaScore. Check your connection and try again.");
    } finally {
      setLoading(false);
    }
  }

  async function createBusiness(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setLoading(true);

    try {
      const response = await fetch("/api/backend/api/onboarding/dashboard", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ business_name: businessName, store_name: storeName || null }),
      });
      const result = await response.json();
      if (!response.ok) {
        setError(result.detail || "Unable to create your business.");
        return;
      }
      setNewConnectCode(result.connect_code);
    } catch {
      setError("Could not reach ZakaScore. Check your connection and try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
      <section className="w-full max-w-lg rounded-2xl border border-gray-200 bg-white p-8 shadow-sm">
        <h1 className="mb-2 text-2xl font-semibold text-gray-900">Set up your business</h1>
        <p className="mb-6 text-sm text-gray-600">
          Create a business profile or join a business with a one-time invite code. Each team member signs in with their own account.
        </p>
        {error && <p role="alert" className="mb-4 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
        <div className="grid gap-8 md:grid-cols-2">
          <form onSubmit={redeemCode} className="space-y-4">
            <h2 className="font-medium text-gray-900">I have a connect code</h2>
            <label className="block text-sm text-gray-700">
              Connect code
              <input
                value={code}
                onChange={(event) => setCode(event.target.value.toUpperCase())}
                autoComplete="off"
                required
                maxLength={32}
                className="mt-1 w-full rounded-lg border border-gray-300 px-4 py-2.5 uppercase tracking-widest"
              />
            </label>
            <button type="submit" disabled={loading} className="w-full rounded-lg bg-gray-900 py-2.5 text-sm font-medium text-white disabled:opacity-50">
              {loading ? "Connecting..." : "Connect store"}
            </button>
          </form>
          <form onSubmit={createBusiness} className="space-y-4">
            <h2 className="font-medium text-gray-900">Create a business profile</h2>
            <label className="block text-sm text-gray-700">
              Business name
              <input value={businessName} onChange={(event) => setBusinessName(event.target.value)} required maxLength={100} className="mt-1 w-full rounded-lg border border-gray-300 px-4 py-2.5" />
            </label>
            <label className="block text-sm text-gray-700">
              Store name (optional)
              <input value={storeName} onChange={(event) => setStoreName(event.target.value)} maxLength={100} className="mt-1 w-full rounded-lg border border-gray-300 px-4 py-2.5" />
            </label>
            <button type="submit" disabled={loading} className="w-full rounded-lg border border-gray-300 py-2.5 text-sm font-medium text-gray-700 disabled:opacity-50">
              {loading ? "Creating..." : "Create business"}
            </button>
          </form>
        </div>
        {newConnectCode && (
          <div className="mt-6 rounded-xl border border-emerald-200 bg-emerald-50 p-4">
            <p className="text-sm text-emerald-900">Share this one-time employee invite code with a team member:</p>
            <p className="mt-2 text-2xl font-semibold tracking-widest text-emerald-950">{newConnectCode}</p>
            <p className="mt-2 text-xs text-emerald-800">This code expires after 24 hours and can be used once.</p>
            <button type="button" onClick={() => router.replace("/dashboard")} className="mt-4 rounded-lg bg-gray-900 px-4 py-2 text-sm font-medium text-white">
              Continue to dashboard
            </button>
          </div>
        )}
      </section>
    </main>
  );
}
