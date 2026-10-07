import { createNeonAuth } from "@neondatabase/auth/next/server";

let authInstance: ReturnType<typeof createNeonAuth> | undefined;

export function getAuth() {
  if (authInstance) return authInstance;

  const baseUrl = process.env.NEON_AUTH_BASE_URL;
  const cookieSecret = process.env.NEON_AUTH_COOKIE_SECRET;

  if (!baseUrl) {
    throw new Error("NEON_AUTH_BASE_URL is not configured");
  }
  if (!cookieSecret || cookieSecret.length < 32) {
    throw new Error("NEON_AUTH_COOKIE_SECRET must contain at least 32 characters");
  }

  authInstance = createNeonAuth({
    baseUrl,
    cookies: { secret: cookieSecret },
  });
  return authInstance;
}
