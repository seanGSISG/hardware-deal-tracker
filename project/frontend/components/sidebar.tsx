"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, Package, Zap, Bell, Settings, PlusCircle, ScrollText } from "lucide-react";

const navItems = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/items", label: "Tracked Items", icon: Package },
  { href: "/items/add", label: "Add Item", icon: PlusCircle },
  { href: "/deals", label: "Deals", icon: Zap },
  { href: "/activity", label: "Activity", icon: ScrollText },
  { href: "/alerts", label: "Alerts", icon: Bell },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 bg-surface border-r border-border flex flex-col">
      <div className="p-6 border-b border-border">
        <div className="flex items-center gap-2">
          <span className="text-amber font-mono text-lg leading-none">▮</span>
          <h1 className="font-mono text-sm font-semibold tracking-wider text-text uppercase">
            DEAL TRACKER
          </h1>
        </div>
        <p className="label mt-2 text-text-dim">ENTERPRISE HARDWARE / v0.2</p>
      </div>
      <nav className="flex-1 py-4">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href || (item.href !== "/" && pathname?.startsWith(item.href));
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-4 py-2.5 text-sm transition-colors relative ${
                isActive
                  ? "text-text bg-surface-2"
                  : "text-text-muted hover:text-text hover:bg-surface-2"
              }`}
            >
              {isActive && (
                <span
                  aria-hidden="true"
                  className="absolute left-0 top-0 bottom-0 w-[3px] bg-amber"
                />
              )}
              <Icon className="w-4 h-4" />
              {item.label}
            </Link>
          );
        })}
      </nav>
      <div className="px-4 py-3 border-t border-border flex items-center gap-2">
        <span className="dot-active"></span>
        <span className="label">SYSTEM ONLINE</span>
      </div>
    </aside>
  );
}
