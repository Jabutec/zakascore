"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { authClient } from "@/lib/auth/client";
import { AUTH_MSG, isOffline } from "@/lib/auth/friendly-errors";
import { AuthShell, FormAlert, PasswordField, limeButton, textLink } from "@/components/auth-ui";

type ResetArgs = { newPassword: string; token: string };
type ResetClient = {
  resetPassword?: (args: ResetArgs) => Promise<{ error?: { status?: number; code?: string; message?: string } | null }>;
};

export default function ResetPasswordPage() {
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);
  const [linkBad, setLinkBad] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  // The reset link brings ?token=... (or ?error=... if it was already invalid).
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const found = params.get("token");
    if (!found || params.get("error")) setLinkBad(true);
    else setToken(found);
  }, []);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");

    const form = new FormData(event.currentTarget);
    const password = String(form.get("password"));
    const confirm = String(form.get("confirmPassword"));

    if (password !== confirm) {
      setError("Your passwords don’t match. Check both fields and try again.");
      return;
    }
    if (isOffline()) {
      setError(AUTH_MSG.network);
      return;
    }

    const client = authClient as unknown as ResetClient;
    if (!client.resetPassword || !token) {
      console.error("resetPassword unavailable or token missing");
      setError(AUTH_MSG.generic);
      return;
    }

    setLoading(true);
    try {
      const result = await client.resetPassword({ newPassword: password, token });

      if (result?.error) {
        console.error("Password reset failed", result.error);
        const text = `${result.error.code ?? ""} ${result.error.message ?? ""}`.toLowerCase();
        if (text.includes("token") || text.includes("expired") || text.includes("invalid")) {
          setLinkBad(true);
          return;
        }
        if (text.includes("short")) {
          setError("Your password needs at least 8 characters.");
          return;
        }
        if (result.error.status === 429) {
          setError(AUTH_MSG.tooMany);
          return;
        }
        setError(
          typeof result.error.status === "number" && result.error.status >= 500
            ? AUTH_MSG.server
            : AUTH_MSG.generic,
        );
        return;
      }

      router.replace("/login");
    } catch (caught) {
      console.error("Password reset threw", caught);
      setError(AUTH_MSG.network);
    } finally {
      setLoading(false);
    }
  }

  if (linkBad) {
    return (
      <AuthShell
        title="This Link Has Expired"
        subtitle="Reset links only work for a short time, and only once. Request a new one to continue."
        heading="Back In"
        panel="right"
        footer={
          <Link href="/login" className={textLink}>
            Back to Sign In
          </Link>
        }
      >
        <Link href="/forgot-password" className={limeButton}>
          Request a New Link
        </Link>
      </AuthShell>
    );
  }

  return (
    <AuthShell
      title="Choose a New Password"
      subtitle="Pick something you’ll remember. At least 8 characters."
      heading="Back In"
      panel="right"
      footer={
        <Link href="/login" className={textLink}>
          Back to Sign In
        </Link>
      }
    >
      {error && <FormAlert>{error}</FormAlert>}
      <form onSubmit={handleSubmit} className="space-y-5">
        <PasswordField
          label="New Password"
          name="password"
          autoComplete="new-password"
          minLength={8}
          required
          placeholder="At least 8 characters"
        />
        <PasswordField
          label="Confirm New Password"
          name="confirmPassword"
          autoComplete="new-password"
          minLength={8}
          required
          placeholder="Re-enter your new password"
        />
        <button type="submit" disabled={loading || !token} className={limeButton}>
          {loading ? "Saving…" : "Save New Password"}
        </button>
      </form>
    </AuthShell>
  );
}