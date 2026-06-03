import { NextRequest, NextResponse } from "next/server";

/**
 * Server-side route guard (ADR-002 / feature-002).
 *
 * Replaces the old client-side localStorage AuthGuard. It runs on the edge
 * BEFORE any page markup is sent, so an unauthenticated user is redirected to
 * /login with NO flash-of-dashboard.
 *
 * Auth source: the httpOnly `session` cookie issued by the backend on login.
 * The cookie is httpOnly, so it is invisible to client JS but fully readable
 * here in middleware via request.cookies.
 *
 * Routing rules:
 *  - Public routes (/login) always pass through.
 *  - Any other matched route requires the `session` cookie; missing it -> 302 /login.
 *  - Next internals (_next), static assets, favicon, and /api are excluded by the
 *    matcher below so they are never gated.
 *
 * NOTE: middleware only checks for the cookie's PRESENCE (it cannot verify the
 * JWT signature without the server secret). Actual token validation happens on
 * the backend via get_current_user; an expired/forged cookie still yields 401s
 * from the API. This is the standard Next.js middleware-guard pattern.
 */

const SESSION_COOKIE = "session";
const PUBLIC_ROUTES = ["/login"];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Public routes are always allowed.
  if (PUBLIC_ROUTES.some((route) => pathname === route || pathname.startsWith(`${route}/`))) {
    return NextResponse.next();
  }

  const hasSession = request.cookies.has(SESSION_COOKIE);
  if (!hasSession) {
    const loginUrl = new URL("/login", request.url);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  // Run on everything EXCEPT Next internals, static assets, the API proxy, and
  // the favicon. Those must never be redirected to /login.
  matcher: ["/((?!_next/static|_next/image|api|favicon.ico|.*\\..*).*)"],
};
