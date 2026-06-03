"use client";

import { usePathname } from "next/navigation";
import { Sidebar } from "@/components/sidebar";

/**
 * Layout shell (ADR-002 / feature-002).
 *
 * Route PROTECTION now lives in middleware.ts (server-side, no flash). This
 * component no longer reads localStorage or redirects; it only chooses the
 * chrome: public routes (e.g. /login) render bare, everything else gets the
 * Sidebar + main layout. The `session` cookie is httpOnly and invisible to JS,
 * so there is nothing for the client to check here.
 */

const PUBLIC_ROUTES = ["/login"];

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isPublic = PUBLIC_ROUTES.includes(pathname);

  if (isPublic) {
    return <>{children}</>;
  }

  return (
    <div className="flex h-screen">
      <Sidebar />
      <main className="flex-1 overflow-y-auto p-6">{children}</main>
    </div>
  );
}
