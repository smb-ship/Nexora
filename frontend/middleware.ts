import { NextRequest, NextResponse } from "next/server";

const PUBLIC_PATHS = ["/login", "/register", "/accept-invite"];
const BACKEND_ORIGIN = "https://app-5ece80c1-c79e-4117-be7d-1e54e2ca190f.cleverapps.io";

export function middleware(request: NextRequest) {
  const { pathname, search } = request.nextUrl;

  // Proxy every /api/* request straight through to the backend, preserving
  // the exact path (including trailing slash) and query string as-is.
  if (pathname.startsWith("/api/")) {
    const url = new URL(pathname + search, BACKEND_ORIGIN);
    return NextResponse.rewrite(url);
  }

  const hasSession = request.cookies.has("access_token");
  const isPublicPath = PUBLIC_PATHS.includes(pathname);

  if (!hasSession && !isPublicPath) {
    const loginUrl = new URL("/login", request.url);
    return NextResponse.redirect(loginUrl);
  }

  if (hasSession && isPublicPath) {
    const dashboardUrl = new URL("/dashboard", request.url);
    return NextResponse.redirect(dashboardUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|chat-widget.js).*)"],
};