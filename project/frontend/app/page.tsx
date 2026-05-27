"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiClient } from "@/lib/api";
import type { Deal } from "@/lib/types";
import { ApiUsageBar } from "@/components/api-usage-bar";
import { StatsCard } from "@/components/stats-card";
import { Package, Zap, Bell, Search, DollarSign, ExternalLink } from "lucide-react";

export default function DashboardPage() {
  const [stats, setStats] = useState({ items: 0, deals: 0, alerts: 0, searches: 0 });
  const [deals, setDeals] = useState<Deal[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [itemsRes, dealsRes, budgetRes] = await Promise.all([
          apiClient.getItemStats().catch(() => null),
          apiClient.getDeals({ min_score: "50", per_page: "5" }).catch(() => null),
          apiClient.getBudget().catch(() => null),
        ]);
        setStats({
          items: itemsRes?.total_items ?? 0,
          deals: dealsRes?.total ?? 0,
          alerts: 0,
          searches: budgetRes?.calls_today ?? 0,
        });
        setDeals(dealsRes?.deals ?? []);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return <div className="p-8 label">LOADING DASHBOARD…</div>;
  }

  const budgetPct = Math.min(Math.round((stats.searches / 5000) * 100), 100);

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h1 className="flex items-center gap-2 font-mono text-xl tracking-[0.18em] uppercase text-text">
            <span className="text-amber">▮</span>
            Dashboard
          </h1>
          <p className="label mt-1">enterprise hardware monitoring</p>
        </div>
        <ApiUsageBar />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatsCard title="Tracked Items" value={stats.items} icon={<Package className="w-5 h-5" strokeWidth={1.5} />} tone="blue" />
        <StatsCard title="Active Deals" value={stats.deals} icon={<Zap className="w-5 h-5" strokeWidth={1.5} />} tone="amber" />
        <StatsCard title="Searches Today" value={stats.searches} icon={<Search className="w-5 h-5" strokeWidth={1.5} />} tone="muted" />
        <StatsCard title="Budget Used" value={`${budgetPct}%`} icon={<DollarSign className="w-5 h-5" strokeWidth={1.5} />} tone="green" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <section className="border border-border bg-surface">
          <header className="flex items-center justify-between px-5 py-3 border-b border-border">
            <h2 className="flex items-center gap-2 font-mono text-sm tracking-[0.18em] uppercase text-text">
              <span className="text-amber">▮</span>
              Top Deals
            </h2>
            <Link href="/deals" className="label hover:text-amber transition-colors">
              view all →
            </Link>
          </header>
          <div className="p-5">
            {deals.length === 0 ? (
              <p className="text-sm text-text-muted">
                No deals found yet. Start tracking items and let the poller find some.
              </p>
            ) : (
              <ul className="divide-y divide-border -my-2">
                {deals.slice(0, 5).map((deal, i) => (
                  <li key={i} className="flex items-center gap-3 py-3">
                    <ScoreBadge score={deal.score?.overall_score ?? 0} />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-text truncate">{deal.title}</p>
                      <p className="font-mono text-[11px] tracking-wider text-text-dim uppercase truncate">
                        ${deal.price} · {deal.seller || "—"}
                        {deal.seller_positive_pct ? ` · ${deal.seller_positive_pct}%` : ""}
                      </p>
                    </div>
                    <a
                      href={deal.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="shrink-0 text-text-dim hover:text-amber transition-colors p-1.5"
                      aria-label="Open listing"
                    >
                      <ExternalLink className="w-4 h-4" strokeWidth={1.5} />
                    </a>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </section>

        <section className="border border-border bg-surface">
          <header className="px-5 py-3 border-b border-border">
            <h2 className="flex items-center gap-2 font-mono text-sm tracking-[0.18em] uppercase text-text">
              <span className="text-amber">▮</span>
              Quick Actions
            </h2>
          </header>
          <div className="grid grid-cols-2 gap-px bg-border">
            <QuickActionCard href="/items/add" label="Add Item" description="Track new hardware" icon={<Package className="w-4 h-4" strokeWidth={1.5} />} />
            <QuickActionCard href="/items" label="View Items" description="Manage tracked items" icon={<Search className="w-4 h-4" strokeWidth={1.5} />} />
            <QuickActionCard href="/deals" label="Browse Deals" description="Scored listings" icon={<Zap className="w-4 h-4" strokeWidth={1.5} />} />
            <QuickActionCard href="/settings" label="Settings" description="Notifications config" icon={<Bell className="w-4 h-4" strokeWidth={1.5} />} />
          </div>
        </section>
      </div>
    </div>
  );
}

function ScoreBadge({ score }: { score: number }) {
  const tone =
    score >= 85 ? "border-l-red text-red"
    : score >= 70 ? "border-l-amber text-amber"
    : score >= 50 ? "border-l-green text-green"
    : "border-l-border-strong text-text-dim";
  return (
    <span className={`inline-flex items-center justify-center w-10 h-10 border border-border border-l-2 bg-surface-2 font-mono text-sm ${tone}`}>
      {Math.round(score)}
    </span>
  );
}

function QuickActionCard({
  href,
  label,
  description,
  icon,
}: {
  href: string;
  label: string;
  description: string;
  icon: React.ReactNode;
}) {
  return (
    <Link
      href={href}
      className="flex flex-col items-center gap-2 p-5 bg-surface hover:bg-surface-2 transition-colors text-center group"
    >
      <div className="text-text-muted group-hover:text-amber transition-colors">{icon}</div>
      <span className="font-mono text-sm tracking-wider uppercase text-text">{label}</span>
      <span className="label">{description}</span>
    </Link>
  );
}
