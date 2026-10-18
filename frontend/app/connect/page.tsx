"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { AUTH_MSG, isOffline } from "@/lib/auth/friendly-errors";
import { AuthShell, Field, FormAlert, limeButton, textLink } from "@/components/auth-ui";

const DEFAULT_STORE_NAME = "Main Store";

export default function ConnectPage() {
  const router = useRouter();
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function createBusiness(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");

    const form = new FormData(event.currentTarget);
    const businessName = String(form.get("businessName")).trim();
    const storeName = String(form.get("storeName")).trim();

    if (!businessName) {
      setError("Please enter your business name.");
      return;
    }
    if (isOffline()) {
      setError(AUTH_MSG.network);
      return;
    }

    setLoading(true);
    try {
      const response = await fetch("/api/backend/api/onboarding/dashboard", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          business_name: businessName,
          store_name: storeName || DEFAULT_STORE_NAME,
        }),
      });

      if (response.ok) {
        router.replace("/workspace");
        router.refresh();
        return;
      }

      console.error("Create business failed", response.status, await response.text().catch(() => ""));

      if (response.status === 401) {
        setError("Your session has ended. Please sign in again.");
        router.replace("/login");
        return;
      }
      if (response.status === 409) {
        // This account already has a business, so there is nothing to set up.
        router.replace("/workspace");
        router.refresh();
        return;
      }
      if (response.status === 429) {
        setError("Too many attempts. Please wait a minute and try again.");
        return;
      }
      if (response.status >= 500) {
        setError(AUTH_MSG.server);
        return;
      }
      setError("We couldn’t set up your business. Check the names and try again.");
    } catch (caught) {
      console.error("Create business request failed", caught);
      setError(AUTH_MSG.network);
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthShell
      title="Set Up Your Business"
      subtitle="Tell us what to call your business. You can start logging sales right after."
      heading="Almost There"
      panel="right"
      footer={
        <>
          Joining a team instead?{" "}
          <Link href="/login" className={textLink}>
            Sign In With a Connect Code
          </Link>
        </>
      }
    >
      {error && <FormAlert>{error}</FormAlert>}

      <form onSubmit={createBusiness} className="space-y-5">
        <Field
          label="Business Name"
          name="businessName"
          autoComplete="organization"
          maxLength={100}
          required
          placeholder="e.g. Thandi’s Tuck Shop"
        />
        <Field
          label="Store Name (Optional)"
          name="storeName"
          autoComplete="off"
          maxLength={100}
          placeholder={DEFAULT_STORE_NAME}
          hint={`Leave blank to use “${DEFAULT_STORE_NAME}”. You can add more stores later.`}
        />
        <button type="submit" disabled={loading} className={limeButton}>
          {loading ? "Setting Up…" : "Create Business"}
        </button>
      </form>
    </AuthShell>
  );
}