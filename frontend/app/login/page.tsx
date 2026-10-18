"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { authClient } from "@/lib/auth/client";
import { AUTH_MSG, friendlyConnectCodeError, friendlySignInError, isOffline } from "@/lib/auth/friendly-errors";
import { redeemConnectCode } from "@/lib/connect-code";
import { AuthShell, ConnectCodeField, Field, FormAlert, PasswordField, limeButton, textLink } from "@/components/auth-ui";

const RETRY_DELAYS_MS = [0, 3000, 6000];

const wait = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

/* Signing in is safe to repeat. If the service is asleep or briefly unreachable, try again
   a couple of times. Wrong credentials (4xx) are returned straight away, never retried. */
async function signInWithRetry(email: string, password: string, onWaking: () => void) {
  let lastError: unknown;
  for (let attempt = 0; attempt < RETRY_DELAYS_MS.length; attempt++) {
    if (RETRY_DELAYS_MS[attempt] > 0) {
      onWaking();
      await wait(RETRY_DELAYS_MS[attempt]);
    }
    const isLast = attempt === RETRY_DELAYS_MS.length - 1;
    try {
      const result = await authClient.signIn.email({ email, password });
      const status = result.error?.status;
      if (result.error && typeof status === "number" && status >= 500 && !isLast) {
        lastError = result.error;
        continue;
      }
      return result;
    } catch (caught) {
      lastError = caught;
      if (isLast) throw caught;
    }
  }
  throw lastError;
}

export default function LoginPage() {
  const router = useRouter();
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [waking, setWaking] = useState(false);
  const [code, setCode] = useState("");

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");

    if (isOffline()) {
      setError(AUTH_MSG.network);
      return;
    }

    setLoading(true);
    setWaking(false);

    try {
      const form = new FormData(event.currentTarget);
      const result = await signInWithRetry(
        String(form.get("email")).trim(),
        String(form.get("password")),
        () => setWaking(true),
      );

      if (result.error) {
        setError(friendlySignInError(result.error));
        return;
      }

      const nextPath = new URLSearchParams(window.location.search).get("next");
      const destination = nextPath && (nextPath === "/workspace" || nextPath.startsWith("/workspace/"))
        ? nextPath
        : nextPath && (nextPath === "/app" || nextPath.startsWith("/app/"))
          ? `/workspace${nextPath.slice(4)}`
          : "/workspace";

      // Optional: join a business with a one-time connect code.
      const connectCode = code.trim();
      if (connectCode) {
        const redeemed = await redeemConnectCode(connectCode);
        if (!redeemed.ok) {
          setError(
            `You’re signed in, but ${friendlyConnectCodeError(redeemed.message).replace(/^./, (c) => c.toLowerCase())} Fix the code, or clear it to continue.`,
          );
          return;
        }
      }

      router.replace(destination);
      router.refresh();
    } catch (caught) {
      console.error("Sign-in request failed", caught);
      setError(AUTH_MSG.network);
    } finally {
      setLoading(false);
      setWaking(false);
    }
  }

  return (
    <AuthShell
      title="Sign In to Your Account"
      subtitle="Welcome back. Sign in to manage your business."
      footer={
        <>
          New to ZakaScore?{" "}
          <Link href="/signup" className={textLink}>
            Create an Account
          </Link>
        </>
      }
    >
      {error && <FormAlert>{error}</FormAlert>}

      <form onSubmit={handleSubmit} className="space-y-5">
        <Field label="Email" name="email" type="email" autoComplete="email" required />
        <div>
          <PasswordField label="Password" name="password" autoComplete="current-password" required />
          <div className="mt-2 text-right">
            <Link href="/forgot-password" className={`text-sm ${textLink}`}>
              Forgot password?
            </Link>
          </div>
        </div>
        <ConnectCodeField value={code} onChange={setCode} />
        <button type="submit" disabled={loading} className={limeButton}>
          {waking ? "Waking things up…" : loading ? "Signing In…" : "Sign In"}
        </button>
        {waking && (
          <p className="text-center text-xs text-slate-500" role="status">
            This can take a few seconds the first time. Hang tight.
          </p>
        )}
      </form>
    </AuthShell>
  );
}