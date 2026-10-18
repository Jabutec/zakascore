"use client";

import Link from "next/link";
import { useState } from "react";
import { authClient } from "@/lib/auth/client";
import { AUTH_MSG, isOffline } from "@/lib/auth/friendly-errors";
import { AuthShell, Field, FormAlert, limeButton, textLink } from "@/components/auth-ui";

type RequestArgs = { email: string; redirectTo: string };
type ResetClient = {
  requestPasswordReset?: (args: RequestArgs) => Promise<{ error?: { status?: number } | null }>;
  forgetPassword?: (args: RequestArgs) => Promise<{ error?: { status?: number } | null }>;
};

export default function ForgotPasswordPage() {
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [sentTo, setSentTo] = useState("");

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");

    if (isOffline()) {
      setError(AUTH_MSG.network);
      return;
    }

    const email = String(new FormData(event.currentTarget).get("email")).trim();
    const client = authClient as unknown as ResetClient;
    const send = client.requestPasswordReset ?? client.forgetPassword;

    if (!send) {
      console.error("No password reset method found on authClient");
      setError(AUTH_MSG.generic);
      return;
    }

    setLoading(true);
    try {
      const result = await send.call(client, {
        email,
        redirectTo: `${window.location.origin}/reset-password`,
      });

      if (result?.error) {
        console.error("Password reset request failed", result.error);
        if (result.error.status === 429) {
          setError(AUTH_MSG.tooMany);
          return;
        }
        if (typeof result.error.status === "number" && result.error.status >= 500) {
          setError(AUTH_MSG.server);
          return;
        }
        // Anything else: show the same success message, so nobody can use this form
        // to find out which emails have accounts.
      }
      setSentTo(email);
    } catch (caught) {
      console.error("Password reset request threw", caught);
      setError(AUTH_MSG.network);
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthShell
      title={sentTo ? "Check Your Email" : "Forgot Your Password?"}
      subtitle={
        sentTo
          ? undefined
          : "Enter your email and we’ll send you a link to choose a new one."
      }
      heading="Back In"
      panel="right"
      footer={
        <Link href="/login" className={textLink}>
          Back to Sign In
        </Link>
      }
    >
      {sentTo ? (
        <div className="rounded-xl border border-[#65a30d]/30 bg-[#f7fee7] px-4 py-4 text-sm leading-relaxed text-[#0B0F19]">
          <p>
            If an account exists for <strong className="break-all">{sentTo}</strong>, a reset link is on its way.
          </p>
          <p className="mt-2 text-slate-600">
            It can take a few minutes. Check your spam folder too. The link expires after a short while.
          </p>
          <button
            type="button"
            onClick={() => setSentTo("")}
            className={`mt-4 ${textLink}`}
          >
            Use a different email
          </button>
        </div>
      ) : (
        <>
          {error && <FormAlert>{error}</FormAlert>}
          <form onSubmit={handleSubmit} className="space-y-5">
            <Field label="Email" name="email" type="email" autoComplete="email" required />
            <button type="submit" disabled={loading} className={limeButton}>
              {loading ? "Sending…" : "Send Reset Link"}
            </button>
          </form>
        </>
      )}
    </AuthShell>
  );
}