"use client";

import { useEffect, useState } from "react";
import { apiClient } from "@/lib/api";
import { ApiUsageBar } from "@/components/api-usage-bar";
import { StatsCard } from "@/components/stats-card";
import { Package, Zap, Bell, Search, TrendingDown, TrendingUp, DollarSign } from "lucide-react";

export default function DashboardPage() {
  const [stats, setStats] = useState({ items: 0, deals: 0, alerts: 0, searches: 0 });
  const [deals, setDeals] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [itemsRes, dealsRes, budgetRes] = await Promise.all([
          apiClient.getItemStats().catch(() => ({ total_items: 0 })),
          apiClient.getDeals({ min_score: "50", per_page: "5" }).catch(() => ({ deals: [], total: 0 })),
          apiClient.getBudget().catch(() => ({ calls_today: 0, utilization_pct: 0 })),
        ]);
        setStats({
          items: itemsRes.total_items || 0,
          deals: dealsRes.total || 0,
          alerts: 0,
          searches: budgetRes.calls_today || 0,
        });
        setDeals(dealsRes.deals || []);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) return <div className="p-8 text-center text-slate-500">Loading dashboard...</div>;

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-slate-800">Dashboard</h1>
        <ApiUsageBar />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatsCard title="Tracked Items" value={stats.items} icon={<Package className="w-5 h-5" />} color="indigo" />
        <StatsCard title="Active Deals" value={stats.deals} icon={<Zap className="w-5 h-5" />} color="amber" />
        <StatsCard title="Searches Today" value={stats.searches} icon={<Search className="w-5 h-5" />} color="purple" />
        <StatsCard title="Budget Used" value={`${Math.min(Math.round((stats.searches / 5000) * 100), 100)}%`} icon={<DollarSign className="w-5 h-5" />} color="green" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl shadow-sm border p-6">
          <h2 className="text-lg font-semibold text-slate-800 mb-4">Top Deals</h2>
          {deals.length === 0 ? (
            <p className="text-slate-400 text-sm">No deals found yet. Start tracking items and searching.</p>
          ) : (
            <div className="space-y-3">
              {deals.slice(0, 5).map((deal: any, i: number) => (
                <div key={i} className="flex items-center gap-3 p-3 rounded-lg border hover:bg-slate-50 transition-colors">
                  <ScoreBadge score={deal.score?.overall_score || 0} />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{deal.title}</p>
                    <p className="text-xs text-slate-500">
                      ${deal.price} — {deal.seller} ({deal.seller_positive_pct}%)
                    </p>
                  </div>
                  <a href={deal.url} target="_blank" rel="noopener noreferrer" className="text-indigo-600 hover:underline text-xs">View</a>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="bg-white rounded-xl shadow-sm border p-6">
          <h2 className="text-lg font-semibold text-slate-800 mb-4">Quick Actions</h2>
          <div className="grid grid-cols-2 gap-3">
            <QuickActionCard href="/items/add" label="Add Item" description="Track new hardware" icon={<Package className="w-4 h-4" />} />
            <QuickActionCard href="/items" label="View Items" description="Manage tracked items" icon={<Search className="w-4 h-4" />} />
            <QuickActionCard href="/deals" label="Browse Deals" description="Scored listings" icon={<Zap className="w-4 h-4" />} />
            <QuickActionCard href="/settings" label="Settings" description="Notifications config" icon={<Bell className="w-4 h-4" />} />
          </div>
        </div>
      </div>
    </div>
  );
}

function ScoreBadge({ score }: { score: number }) {
  const color = score >= 85 ? "bg-red-500" : score >= 70 ? "bg-orange-500" : score >= 50 ? "bg-green-500" : "bg-slate-400";
  return (
    <span className={`inline-flex items-center justify-center w-10 h-10 rounded-full text-white text-sm font-bold ${color}`}>
      {score}
    </span>
  );
}

function QuickActionCard({ href, label, description, icon }: { href: string; label: string; description: string; icon: React.ReactNode }) {
  return (
    <a href={href} className="flex flex-col items-center gap-2 p-4 rounded-lg border hover:border-indigo-300 hover:bg-indigo-50 transition-all text-center">
      <div className="text-indigo-600">{icon}</div>
      <span className="font-medium text-sm">{label}</span>
      <span className="text-xs text-slate-500">{description}</span>
    </a>
  );
}
