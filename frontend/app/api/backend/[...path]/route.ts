import { getAuth } from "@/lib/auth/server";

type BackendRouteContext = { params: Promise<{ path: string[] }> };

async function proxyToBackend(request: Request, context: BackendRouteContext) {
  const auth = getAuth();
  const { data: session, error } = await auth.getSession();
  if (error) {
    return Response.json({ detail: "Unable to verify session" }, { status: 502 });
  }
  if (!session?.user?.id) {
    return Response.json({ detail: "Authentication required" }, { status: 401 });
  }
  const { data: accessToken, error: tokenError } = await auth.token();
  if (tokenError) {
    return Response.json({ detail: "Unable to obtain access token" }, { status: 502 });
  }
  if (!accessToken?.token) {
    return Response.json({ detail: "Authentication required" }, { status: 401 });
  }

  const baseUrl = process.env.BACKEND_API_URL ?? process.env.NEXT_PUBLIC_API_URL;
  if (!baseUrl) {
    return Response.json({ detail: "Backend API is not configured" }, { status: 500 });
  }

  const { path } = await context.params;
  const upstreamUrl = new URL(
    `/${path.map(encodeURIComponent).join("/")}${new URL(request.url).search}`,
    baseUrl.endsWith("/") ? baseUrl : `${baseUrl}/`,
  );
  const headers = new Headers();
  const contentType = request.headers.get("content-type");
  if (contentType) headers.set("content-type", contentType);
  headers.set("Authorization", `Bearer ${accessToken.token}`);

  const method = request.method.toUpperCase();
  const body =
    method === "GET" || method === "HEAD"
      ? undefined
      : await request.arrayBuffer();

  const upstream = await fetch(upstreamUrl, {
    method,
    headers,
    body,
    cache: "no-store",
  });
  const responseHeaders = new Headers();
  const upstreamContentType = upstream.headers.get("content-type");
  if (upstreamContentType) {
    responseHeaders.set("content-type", upstreamContentType);
  }

  return new Response(upstream.body, {
    status: upstream.status,
    headers: responseHeaders,
  });
}

export const GET = proxyToBackend;
export const POST = proxyToBackend;
export const PUT = proxyToBackend;
export const PATCH = proxyToBackend;
export const DELETE = proxyToBackend;
