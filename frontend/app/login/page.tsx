"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { authClient } from "@/lib/auth/client";
import { redeemConnectCode } from "@/lib/connect-code";
import { AuthShell, ConnectCodeField, Field, FormAlert, limeButton, textLink } from "@/components/auth-ui";

export default function LoginPage() {
  const router = useRouter();
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [code, setCode] = useState("");

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setLoading(true);

    try {
      const form = new FormData(event.currentTarget);
      const result = await authClient.signIn.email({
        email: String(form.get("email")),
        password: String(form.get("password")),
      });

      if (result.error) {
        setError(result.error.message || "Unable to sign in.");
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
            `You’re signed in, but the connect code could not be used (${redeemed.message}). Fix the code and try again, or clear it to continue.`,
          );
          return;
        }
      }

      router.replace(destination);
      router.refresh();
    } catch {
      setError("Could not reach Neon Auth. Check your connection and try again.");
    } finally {
      setLoading(false);
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
        <Field label="Password" name="password" type="password" autoComplete="current-password" required />
        <ConnectCodeField value={code} onChange={setCode} />
        <button type="submit" disabled={loading} className={limeButton}>
          {loading ? "Signing In…" : "Sign In"}
        </button>
      </form>
    </AuthShell>
  );
}