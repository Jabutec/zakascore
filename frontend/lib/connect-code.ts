// Redeems a one-time connect code for the signed-in user.
// Same endpoint and error handling the old connect page used; shared by sign in and sign up.
export async function redeemConnectCode(
  code: string,
): Promise<{ ok: true } | { ok: false; message: string }> {
  try {
    const response = await fetch("/api/backend/api/connect-codes/redeem", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code }),
    });
    const result: unknown = await response.json().catch(() => ({}));
    if (!response.ok) {
      const detail =
        result &&
        typeof result === "object" &&
        "detail" in result &&
        typeof (result as { detail: unknown }).detail === "string"
          ? (result as { detail: string }).detail
          : "Unable to connect this account";
      return { ok: false, message: detail };
    }
    return { ok: true };
  } catch {
    return { ok: false, message: "Could not reach ZakaScore. Check your connection and try again" };
  }
}