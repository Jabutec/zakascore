const API_URL = process.env.NEXT_PUBLIC_API_URL;

export async function requestOtp(phoneNumber: string) {
  const formData = new FormData();
  formData.append("phone_number", phoneNumber);

  const response = await fetch(`${API_URL}/auth/request-otp`, {
    method: "POST",
    body: formData,
  });

  return response.json();
}

export async function verifyOtp(phoneNumber: string, code: string) {
  const response = await fetch("/api/verify-otp", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ phoneNumber, code }),
  });

  return response.json();
}