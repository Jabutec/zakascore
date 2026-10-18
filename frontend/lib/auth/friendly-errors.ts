type AuthErrorLike = { code?: string; message?: string; status?: number } | null | undefined;

export const AUTH_MSG = {
  network: "We couldn’t connect. Check your internet and try again.",
  server: "Something went wrong on our side. Please try again in a moment.",
  tooMany: "Too many attempts. Please wait a minute and try again.",
  generic: "Something went wrong. Please try again.",
} as const;

function has(error: AuthErrorLike, ...needles: string[]) {
  const text = `${error?.code ?? ""} ${error?.message ?? ""}`.toLowerCase();
  return needles.some((needle) => text.includes(needle));
}

function common(error: AuthErrorLike): string | null {
  if (error?.status === 429 || has(error, "too_many", "too many", "rate limit")) return AUTH_MSG.tooMany;
  if (typeof error?.status === "number" && error.status >= 500) return AUTH_MSG.server;
  return null;
}

export function friendlySignInError(error: AuthErrorLike): string {
  console.error("Sign-in failed", error);
  if (
    error?.status === 401 ||
    has(error, "invalid_email_or_password", "invalid_password", "user_not_found", "invalid email or password", "incorrect")
  ) {
    return "Incorrect email or password. Check both and try again.";
  }
  if (has(error, "email_not_verified", "not verified")) {
    return "Please verify your email first. Check your inbox for the link.";
  }
  if (has(error, "invalid_email")) return "That email address doesn’t look right.";
  return common(error) ?? AUTH_MSG.generic;
}

export function friendlySignUpError(error: AuthErrorLike): string {
  console.error("Sign-up failed", error);
  if (has(error, "user_already_exists", "already exists", "already registered", "already in use")) {
    return "An account with this email already exists. Try signing in instead.";
  }
  if (has(error, "invalid_email")) return "That email address doesn’t look right.";
  if (has(error, "password_too_short", "too short")) return "Your password needs at least 8 characters.";
  if (has(error, "password_too_long", "too long")) return "That password is too long. Please use a shorter one.";
  return common(error) ?? "We couldn’t create your account. Please check your details and try again.";
}

/* Connect code failures: the server text is never shown, only a matching plain message. */
export function friendlyConnectCodeError(raw: string | undefined): string {
  console.error("Connect code failed", raw);
  const text = (raw ?? "").toLowerCase();
  if (text.includes("expire")) return "That connect code has expired. Ask your team for a new one.";
  if (text.includes("used") || text.includes("redeemed") || text.includes("already")) {
    return "That connect code has already been used. Ask your team for a new one.";
  }
  if (text.includes("invalid") || text.includes("not found") || text.includes("unknown")) {
    return "That connect code isn’t right. Check it and try again.";
  }
  return "We couldn’t use that connect code. Check it and try again.";
}

export function isOffline() {
  return typeof navigator !== "undefined" && !navigator.onLine;
}