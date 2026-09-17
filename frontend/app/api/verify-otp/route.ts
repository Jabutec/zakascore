import { NextRequest, NextResponse } from "next/server";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

export async function POST(request: NextRequest) {
  const { phoneNumber, code } = await request.json();

  const formData = new FormData();
  formData.append("phone_number", phoneNumber);
  formData.append("code", code);

  const backendResponse = await fetch(`${API_URL}/auth/verify-otp`, {
    method: "POST",
    body: formData,
  });

  const data = await backendResponse.json();

  if (data.error) {
    return NextResponse.json({ error: data.error }, { status: 401 });
  }

  const response = NextResponse.json({ success: true });
  response.cookies.set("access_token", data.access_token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    maxAge: 60 * 60 * 24, // 24 hours, matches your JWT_EXPIRY_HOURS
    path: "/",
  });

  return response;
}