"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useRef, useState } from "react";
import { authClient } from "@/lib/auth/client";
import { redeemConnectCode } from "@/lib/connect-code";
import {
  AuthShell,
  CheckboxField,
  ConnectCodeField,
  Field,
  FormAlert,
  PasswordField,
  limeButton,
  textLink,
} from "@/components/auth-ui";

export default function SignUpPage() {
  const router = useRouter();
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [code, setCode] = useState("");
  // If the account was created but the connect code failed, a retry must not sign up again.
  const accountCreated = useRef(false);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");

    const form = new FormData(event.currentTarget);

    if (!accountCreated.current) {
      const password = String(form.get("password"));
      const confirmPassword = String(form.get("confirmPassword"));
      if (password !== confirmPassword) {
        setError("Passwords do not match. Please check both fields and try again.");
        return;
      }
    }

    setLoading(true);

    try {
      if (!accountCreated.current) {
        const result = await authClient.signUp.email({
          name: String(form.get("name")),
          email: String(form.get("email")),
          password: String(form.get("password")),
        });

        if (result.error) {
          setError(result.error.message || "Unable to create your account.");
          return;
        }
        accountCreated.current = true;
      }

      const session = await authClient.getSession();
      if (!session.data?.user) {
        router.replace("/login?account-created=1");
        return;
      }

      // Optional: join a business with a one-time connect code instead of creating one.
      const connectCode = code.trim();
      if (connectCode) {
        const redeemed = await redeemConnectCode(connectCode);
        if (!redeemed.ok) {
          setError(
            `Your account was created, but the connect code could not be used (${redeemed.message}). Fix the code and try again, or clear it to set up a business instead.`,
          );
          return;
        }
        router.replace("/workspace");
        router.refresh();
        return;
      }

      router.replace("/connect");
      router.refresh();
    } catch {
      setError("Could not reach Neon Auth. Check your connection and try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthShell
      title="Create Your Account"
      subtitle="Create your own secure account to manage an authorized business."
      footer={
        <>
          Already have an account?{" "}
          <Link href="/login" className={textLink}>
            Sign In
          </Link>
        </>
      }
    >
      {error && <FormAlert>{error}</FormAlert>}

      <form onSubmit={handleSubmit} className="space-y-4">
        <Field label="Name" name="name" autoComplete="name" required />
        <Field label="Email" name="email" type="email" autoComplete="email" required />
        <PasswordField
          label="Password"
          name="password"
          autoComplete="new-password"
          minLength={8}
          required
          placeholder="At least 8 characters"
        />
        <PasswordField
          label="Confirm Password"
          name="confirmPassword"
          autoComplete="new-password"
          minLength={8}
          required
          placeholder="Re-enter your password"
        />
        <ConnectCodeField value={code} onChange={setCode} />

        <div className="space-y-3 pt-1">
          <CheckboxField name="acceptPrivacy" required>
            I have read and accept the{" "}
            <Link href="/privacy" target="_blank" rel="noopener noreferrer" className={textLink}>
              Privacy Policy
            </Link>
            .
          </CheckboxField>
          <CheckboxField name="acceptTerms" required>
            I agree to the{" "}
            <Link href="/terms" target="_blank" rel="noopener noreferrer" className={textLink}>
              Terms of Service
            </Link>
            .
          </CheckboxField>
        </div>

        <button type="submit" disabled={loading} className={limeButton}>
          {loading ? "Creating Account…" : "Create Account"}
        </button>
      </form>
    </AuthShell>
  );
}