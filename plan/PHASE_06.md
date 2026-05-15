# PHASE 06 — Frontend Dashboard + Add Item Wizard + Interval Editor

## Objective
Build a complete React frontend with Next.js 15 App Router, Tailwind CSS, shadcn/ui, and Recharts. Features include:
- **Dashboard** with API usage bar, deal feed, stats cards, and trend charts
- **Tracked Items** page with per-item interval editor, priority badges, bulk actions
- **Add Item Wizard** — 3-step form with catalog auto-suggest, category picker, interval preset selector
- **Deals** browser with filters and score visualization
- **Price History** with Recharts area charts
- **Alert History** with channel/status filters
- **Notification Settings** with Telegram + Email config

---

## Output Location
`/mnt/agents/output/hardware-deal-tracker/project/frontend/`

---

## Dependencies
- Phase 2 (API endpoints with full contract) merged to `main`
- Branch from: `main`
- Can be split into **2-3 parallel agents**: scaffold agent + feature page agents

---

## Design System

### Color Palette
```
Primary:     #667eea (indigo)     — main accent, buttons, links
Secondary:   #764ba2 (purple)     — gradients, badges
Background:  #f8fafc (slate-50)   — page background
Surface:     #ffffff (white)       — cards, panels
Text:        #1e293b (slate-800)   — headings
Text Muted:  #64748b (slate-500)   — body text
Border:      #e2e8f0 (slate-200)   — dividers
Success:     #22c55e (green-500)   — positive indicators
Warning:     #f59e0b (amber-500)   — medium scores
Danger:      #ef4444 (red-500)     — high scores / errors
```

### Score Color Mapping
| Score Range | Color | Label |
|-------------|-------|-------|
| 85-100 | #ef4444 | Hot Deal |
| 70-84 | #f59e0b | Great Deal |
| 50-69 | #22c55e | Good Deal |
| 30-49 | #64748b | Fair Deal |
| 0-29 | #94a3b8 | Poor Deal |

---

## API Client Setup

### `frontend/lib/api.ts`
Create a typed API client that wraps fetch calls:

```typescript
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

async function api<T>(path: string, options?: RequestInit): Promise<T> {
  const token = localStorage.getItem("token");
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
  
  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }
  return response.json();
}

export const apiClient = {
  // Auth
  login: (data: { username: string; password: string }) =>
    api<{ access_token: string }>("/auth/login", { method: "POST", body: JSON.stringify(data) }),
  register: (data: { username: string; email: string; password: string }) =>
    api<{ access_token: string }>("/auth/register", { method: "POST", body: JSON.stringify(data) }),

  // Items
  getItems: (params?: { page?: number; enabled?: boolean; priority?: string; category?: string }) =>
    api("/items?" + new URLSearchParams(params as Record<string, string>)),
  createItem: (data: any) => api("/items", { method: "POST", body: JSON.stringify(data) }),
  updateItem: (id: number, data: any) => api(`/items/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  deleteItem: (id: number) => api(`/items/${id}`, { method: "DELETE" }),
  toggleItem: (id: number) => api(`/items/${id}/toggle`, { method: "PUT" }),
  bulkUpdateItems: (data: { ids: number[]; action: string; value?: any }) =>
    api("/items/bulk-update", { method: "POST", body: JSON.stringify(data) }),
  getItemStats: () => api("/items/stats"),

  // Catalog (for Add Item wizard auto-suggest)
  searchCatalog: (query: string) => api(`/catalog?q=${encodeURIComponent(query)}`),
  getCatalogItem: (id: string) => api(`/catalog/${id}`),
  getCategories: () => api("/categories"),

  // Deals
  getDeals: (params?: { min_score?: number; item_id?: number; page?: number }) =>
    api("/deals?" + new URLSearchParams(params as Record<string, string>)),

  // History
  getHistory: (itemId: number, days?: number) => api(`/history/${itemId}?days=${days || 30}`),
  getStats: (itemId: number) => api(`/history/stats/${itemId}`),

  // Alerts
  getAlerts: (params?: { page?: number; channel?: string }) =>
    api("/alerts?" + new URLSearchParams(params as Record<string, string>)),

  // Settings
  getNotificationSettings: () => api("/settings/notifications"),
  updateNotificationSettings: (data: any) => api("/settings/notifications", { method: "PUT", body: JSON.stringify(data) }),

  // Search
  triggerSearch: (itemId: number) => api(`/search/trigger/${itemId}`, { method: "POST" }),
  triggerAll: () => api("/search/trigger-all", { method: "POST" }),

  // Rate Budget (for API usage bar)
  getBudget: () => api("/search/budget"),
  getPresets: () => api("/search/presets"),
};
```

---

## Tasks (Parallelizable)

### Task 1: Scaffold + Dashboard Page (`frontend/app/page.tsx`)

**Layout** (`frontend/app/layout.tsx`):
```tsx
import "./globals.css";
import { Inter } from "next/font/google";
import { Sidebar } from "@/components/sidebar";
import { TopBar } from "@/components/top-bar";

const inter = Inter({ subsets: ["latin"] });

export const metadata = {
  title: "Hardware Deal Tracker",
  description: "AI-Powered Enterprise Hardware Arbitrage",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={`${inter.className} bg-slate-50`}>
        <div className="flex h-screen">
          <Sidebar />
          <div className="flex-1 flex flex-col overflow-hidden">
            <TopBar />
            <main className="flex-1 overflow-y-auto p-6">{children}</main>
          </div>
        </div>
      </body>
    </html>
  );
}
```

**Dashboard** (`frontend/app/page.tsx`):
```tsx
"use client";

import { useEffect, useState } from "react";
import { apiClient } from "@/lib/api";
import { StatsCard } from "@/components/stats-card";
import { DealsTable } from "@/components/deals-table";
import { ActivityFeed } from "@/components/activity-feed";
import { TrendChart } from "@/components/trend-chart";

export default function DashboardPage() {
  const [stats, setStats] = useState({ items: 0, deals: 0, alerts: 0, searches: 0 });
  const [deals, setDeals] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [itemsRes, dealsRes, alertsRes] = await Promise.all([
          apiClient.getItems(),
          apiClient.getDeals({ min_score: 70, per_page: 10 }),
          apiClient.getAlerts(),
        ]);
        setStats({
          items: itemsRes.total || 0,
          deals: dealsRes.total || 0,
          alerts: alertsRes.total || 0,
          searches: 0,
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

  if (loading) return <div className="p-8 text-center">Loading dashboard...</div>;

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-slate-800">Dashboard</h1>
      
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatsCard title="Tracked Items" value={stats.items} icon="box" color="indigo" />
        <StatsCard title="Active Deals" value={stats.deals} icon="zap" color="amber" />
        <StatsCard title="Alerts Sent" value={stats.alerts} icon="bell" color="green" />
        <StatsCard title="Searches Today" value={stats.searches} icon="search" color="purple" />
      </div>

      {/* Charts + Feed */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-white rounded-xl shadow-sm border p-6">
          <h2 className="text-lg font-semibold text-slate-800 mb-4">Price Trends</h2>
          <TrendChart />
        </div>
        <div className="bg-white rounded-xl shadow-sm border p-6">
          <h2 className="text-lg font-semibold text-slate-800 mb-4">Recent Activity</h2>
          <ActivityFeed />
        </div>
      </div>

      {/* Deals Table */}
      <div className="bg-white rounded-xl shadow-sm border p-6">
        <h2 className="text-lg font-semibold text-slate-800 mb-4">Top Deals</h2>
        <DealsTable deals={deals} />
      </div>
    </div>
  );
}
```

### Task 2: Sidebar + Navigation (`frontend/components/sidebar.tsx`)

```tsx
"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, Package, Zap, Bell, BarChart3, Settings, Search } from "lucide-react";

const navItems = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/items", label: "Tracked Items", icon: Package },
  { href: "/deals", label: "Deals", icon: Zap },
  { href: "/alerts", label: "Alerts", icon: Bell },
  { href: "/history", label: "History", icon: BarChart3 },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  
  return (
    <aside className="w-64 bg-white border-r border-slate-200 flex flex-col">
      <div className="p-6 border-b border-slate-200">
        <h1 className="text-xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
          Deal Tracker
        </h1>
        <p className="text-xs text-slate-500 mt-1">Enterprise Hardware</p>
      </div>
      <nav className="flex-1 p-4 space-y-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? "bg-indigo-50 text-indigo-700"
                  : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
              }`}
            >
              <Icon className="w-4 h-4" />
              {item.label}
            </Link>
          );
        })}
      </nav>
      <div className="p-4 border-t border-slate-200">
        <div className="flex items-center gap-3 px-3 py-2">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center text-white text-xs font-bold">
            A
          </div>
          <div>
            <p className="text-sm font-medium text-slate-700">Admin</p>
            <p className="text-xs text-slate-500">admin@localhost</p>
          </div>
        </div>
      </div>
    </aside>
  );
}
```

### Task 3: Tracked Items Page (`frontend/app/items/page.tsx`)

CRUD page for tracked items:
- Table view with name, keywords, target price, alert threshold, enabled status
- Add new item modal (form with name, keywords, SKU, target price, threshold)
- Edit item inline
- Toggle enable/disable
- Delete with confirmation
- Search/filter
- Pagination

### Task 4: Deals Page (`frontend/app/deals/page.tsx`)

Dedicated deals browsing:
- Filter by score range (slider: 0-100)
- Filter by item
- Sort by score (descending default)
- Card grid layout with:
  - Image thumbnail
  - Title (truncated)
  - Price + shipping
  - Score badge with color
  - Classification label
  - Seller info (feedback %)
  - Direct eBay link
  - "View Details" button

### Task 5: Price History Page (`frontend/app/history/page.tsx`)

Per-item price history with charts:
- Item selector dropdown
- Time period toggle (7d / 30d / 90d)
- Recharts line chart: min/avg/max per day
- Statistics panel: median, lowest, volatility
- Table of recent listings

### Task 6: Alerts Page (`frontend/app/alerts/page.tsx`)

Notification history:
- Filter by channel (Telegram/Email)
- Filter by status (sent/pending/failed)
- Table: listing title, score, channel, sent time, status
- Pagination

### Task 7: Settings Page (`frontend/app/settings/page.tsx`)

Notification configuration:
- Telegram: bot token, chat ID, enable toggle, min score slider
- Email: SMTP host, port, user, password, digest mode dropdown
- Mute until datetime picker
- Save button with toast notification

### Task 8: Shared Components

**`frontend/components/score-badge.tsx`**:
```tsx
export function ScoreBadge({ score }: { score: number }) {
  const getColor = () => {
    if (score >= 85) return "bg-red-500 text-white";
    if (score >= 70) return "bg-amber-500 text-white";
    if (score >= 50) return "bg-green-500 text-white";
    return "bg-slate-400 text-white";
  };
  return (
    <span className={`inline-flex items-center justify-center w-12 h-12 rounded-full text-lg font-bold ${getColor()}`}>
      {score}
    </span>
  );
}
```

**`frontend/components/deals-table.tsx`**: Sortable table for deals  
**`frontend/components/trend-chart.tsx`**: Recharts area chart for price trends  
**`frontend/components/stats-card.tsx`**: Dashboard stat card with icon  
**`frontend/components/activity-feed.tsx`**: Recent events list

**`frontend/components/api-usage-bar.tsx`** — Real-time eBay API budget tracker:
```tsx
"use client";

import { useEffect, useState } from "react";
import { apiClient } from "@/lib/api";

interface BudgetStatus {
  calls_today: number;
  daily_limit: number;
  remaining: number;
  utilization_pct: number;
  status: "ok" | "warning" | "critical";
}

export function ApiUsageBar() {
  const [budget, setBudget] = useState<BudgetStatus | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const data = await apiClient.getBudget();
        setBudget(data);
      } catch (err) {
        console.error("Failed to load budget:", err);
      }
    }
    load();
    const interval = setInterval(load, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  if (!budget) return null;

  const barColor = budget.status === "critical" ? "bg-red-500" :
                   budget.status === "warning" ? "bg-amber-500" : "bg-green-500";

  return (
    <div className="bg-white rounded-lg border p-3 shadow-sm">
      <div className="flex items-center justify-between mb-1.5">
        <span className="text-xs font-medium text-slate-600">
          eBay API Usage Today
        </span>
        <span className={`text-xs font-bold ${budget.status === "critical" ? "text-red-600" : budget.status === "warning" ? "text-amber-600" : "text-green-600"}`}>
          {budget.calls_today.toLocaleString()} / {budget.daily_limit.toLocaleString()}
          {" "}({budget.utilization_pct}%)
        </span>
      </div>
      <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${barColor}`}
          style={{ width: `${Math.min(budget.utilization_pct, 100)}%` }}
        />
      </div>
      <div className="flex justify-between mt-1">
        <span className="text-[10px] text-slate-400">
          {budget.remaining.toLocaleString()} remaining
        </span>
        {budget.status !== "ok" && (
          <span className="text-[10px] font-medium text-amber-600">
            {budget.status === "critical" ? "API limit reached — low-priority items paused" : "Approaching limit"}
          </span>
        )}
      </div>
    </div>
  );
}
```

### Task 9: Add Item Wizard (`frontend/app/items/add/page.tsx`)

Three-step wizard for adding new tracked items with catalog auto-suggest.

**Step 1: Search & Select**
```tsx
"use client";

import { useState, useCallback, useEffect } from "react";
import { useDebounce } from "@/lib/hooks";
import { apiClient } from "@/lib/api";
import { Search, Package, Cpu, HardDrive, Zap } from "lucide-react";

interface CatalogItem {
  name: string;
  keywords: string;
  sku: string;
  mpn: string;
  category_id: string;
  target_price: number;
  alert_threshold: number;
  search_interval: number;
  benchmark_median: number;
  scam_floor: number;
  notes: string;
}

export function AddItemStep1({ onSelect }: { onSelect: (item: CatalogItem) => void }) {
  const [query, setQuery] = useState("");
  const [suggestions, setSuggestions] = useState<CatalogItem[]>([]);
  const [loading, setLoading] = useState(false);
  const debouncedQuery = useDebounce(query, 300);

  useEffect(() => {
    if (debouncedQuery.length < 2) {
      setSuggestions([]);
      return;
    }
    async function search() {
      setLoading(true);
      try {
        const results = await apiClient.searchCatalog(debouncedQuery);
        setSuggestions(results);
      } catch (err) {
        setSuggestions([]);
      }
      setLoading(false);
    }
    search();
  }, [debouncedQuery]);

  const categoryIcon = (catId: string) => {
    if (catId === "164") return <Cpu className="w-4 h-4" />;
    if (catId === "56083") return <HardDrive className="w-4 h-4" />;
    if (catId === "27386") return <Zap className="w-4 h-4" />;
    return <Package className="w-4 h-4" />;
  };

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">Search for hardware to track</h2>
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Try: RTX PRO 6000, H12SSL, Exos 16TB, M393A8G40..."
          className="w-full pl-10 pr-4 py-3 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
        />
        {loading && (
          <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-slate-400">Searching...</span>
        )}
      </div>

      {suggestions.length > 0 && (
        <div className="border rounded-lg divide-y">
          {suggestions.map((item, idx) => (
            <button
              key={idx}
              onClick={() => onSelect(item)}
              className="w-full flex items-center gap-3 p-3 hover:bg-slate-50 text-left transition-colors"
            >
              <div className="w-8 h-8 rounded bg-indigo-50 flex items-center justify-center text-indigo-600">
                {categoryIcon(item.category_id)}
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-medium text-sm truncate">{item.name}</p>
                <p className="text-xs text-slate-500">
                  Target: ${item.target_price} | Est. median: ${item.benchmark_median}
                  {item.scam_floor > 0 && (
                    <span className="ml-2 text-red-500">
                      Scam floor: ${item.scam_floor}
                    </span>
                  )}
                </p>
              </div>
            </button>
          ))}
        </div>
      )}

      {query.length >= 2 && suggestions.length === 0 && !loading && (
        <div className="text-center py-8 text-slate-500">
          <p>No catalog match found.</p>
          <button
            onClick={() => onSelect({
              name: query,
              keywords: query,
              sku: "", mpn: "", category_id: "56083",
              target_price: 0, alert_threshold: 0.20,
              search_interval: 600, benchmark_median: 0,
              scam_floor: 0, notes: ""
            })}
            className="mt-2 text-indigo-600 hover:underline text-sm"
          >
            Create custom item with "{query}"
          </button>
        </div>
      )}
    </div>
  );
}
```

**Step 2: Configure**
```tsx
const INTERVAL_PRESETS = [
  { key: "hot", label: "Hot (5 min)", interval: 300, color: "bg-red-100 text-red-700 border-red-200" },
  { key: "standard", label: "Standard (10 min)", interval: 600, color: "bg-orange-100 text-orange-700 border-orange-200" },
  { key: "monitor", label: "Monitor (20 min)", interval: 1200, color: "bg-blue-100 text-blue-700 border-blue-200" },
  { key: "passive", label: "Passive (30 min)", interval: 1800, color: "bg-gray-100 text-gray-600 border-gray-200" },
  { key: "custom", label: "Custom", interval: 0, color: "bg-slate-100 text-slate-600 border-slate-200" },
];

export function AddItemStep2({
  catalogItem,
  onConfirm
}: {
  catalogItem: CatalogItem;
  onConfirm: (data: any) => void;
}) {
  const [form, setForm] = useState({
    name: catalogItem.name,
    keywords: catalogItem.keywords,
    sku: catalogItem.sku,
    mpn: catalogItem.mpn,
    category_id: catalogItem.category_id,
    target_price: catalogItem.target_price,
    alert_threshold: catalogItem.alert_threshold,
    search_interval: catalogItem.search_interval,
    min_deal_score: 60,
    is_enabled: true,
  });
  const [selectedPreset, setSelectedPreset] = useState(
    catalogItem.search_interval <= 300 ? "hot" :
    catalogItem.search_interval <= 600 ? "standard" :
    catalogItem.search_interval <= 1200 ? "monitor" : "passive"
  );
  const [customInterval, setCustomInterval] = useState(catalogItem.search_interval);
  const [categories, setCategories] = useState<{id: string; name: string}[]>([]);

  useEffect(() => {
    apiClient.getCategories().then(setCategories);
  }, []);

  const handlePresetChange = (preset: string) => {
    setSelectedPreset(preset);
    if (preset !== "custom") {
      const p = INTERVAL_PRESETS.find(ip => ip.key === preset);
      if (p) setForm(f => ({ ...f, search_interval: p.interval }));
    }
  };

  const dailyCalls = Math.ceil(86400 / form.search_interval);

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">Configure tracking</h2>

      {/* Name */}
      <div>
        <label className="block text-sm font-medium text-slate-700 mb-1">Name</label>
        <input
          value={form.name}
          onChange={(e) => setForm(f => ({ ...f, name: e.target.value }))}
          className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
        />
      </div>

      {/* Keywords */}
      <div>
        <label className="block text-sm font-medium text-slate-700 mb-1">Search Keywords</label>
        <textarea
          value={form.keywords}
          onChange={(e) => setForm(f => ({ ...f, keywords: e.target.value }))}
          className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
          rows={2}
        />
      </div>

      {/* Target Price + Alert Threshold */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Target Price ($)</label>
          <input
            type="number"
            step="0.01"
            value={form.target_price}
            onChange={(e) => setForm(f => ({ ...f, target_price: parseFloat(e.target.value) }))}
            className="w-full px-3 py-2 border rounded-lg"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">
            Alert Threshold (% below median)
          </label>
          <input
            type="number"
            step="0.05"
            min="0"
            max="1"
            value={form.alert_threshold}
            onChange={(e) => setForm(f => ({ ...f, alert_threshold: parseFloat(e.target.value) }))}
            className="w-full px-3 py-2 border rounded-lg"
          />
        </div>
      </div>

      {/* Polling Interval Presets */}
      <div>
        <label className="block text-sm font-medium text-slate-700 mb-2">
          Polling Frequency
          <span className="ml-2 text-xs text-slate-400">
            ({dailyCalls} calls/day)
          </span>
        </label>
        <div className="grid grid-cols-5 gap-2">
          {INTERVAL_PRESETS.map(preset => (
            <button
              key={preset.key}
              onClick={() => handlePresetChange(preset.key)}
              className={`px-3 py-2 rounded-lg border text-xs font-medium transition-colors ${
                selectedPreset === preset.key
                  ? `${preset.color} ring-2 ring-offset-1 ring-indigo-500`
                  : "bg-white border-slate-200 text-slate-600 hover:bg-slate-50"
              }`}
            >
              {preset.label}
            </button>
          ))}
        </div>
        {selectedPreset === "custom" && (
          <div className="mt-2 flex items-center gap-2">
            <input
              type="number"
              value={customInterval}
              onChange={(e) => {
                setCustomInterval(parseInt(e.target.value));
                setForm(f => ({ ...f, search_interval: parseInt(e.target.value) }));
              }}
              min="60"
              max="86400"
              className="w-24 px-2 py-1 border rounded text-sm"
            />
            <span className="text-sm text-slate-500">seconds</span>
          </div>
        )}
      </div>

      {/* eBay Category */}
      <div>
        <label className="block text-sm font-medium text-slate-700 mb-1">eBay Category</label>
        <select
          value={form.category_id}
          onChange={(e) => setForm(f => ({ ...f, category_id: e.target.value }))}
          className="w-full px-3 py-2 border rounded-lg"
        >
          {categories.map(cat => (
            <option key={cat.id} value={cat.id}>{cat.name}</option>
          ))}
        </select>
      </div>

      {/* Scam floor warning */}
      {catalogItem.scam_floor > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3">
          <p className="text-sm font-medium text-red-700">Scam Floor: ${catalogItem.scam_floor}</p>
          <p className="text-xs text-red-600 mt-1">
            Listings below this price will be flagged as suspicious. Typical scam listings
            use unrealistically low prices to attract buyers.
          </p>
        </div>
      )}

      {/* Notes */}
      {catalogItem.notes && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
          <p className="text-xs text-blue-700">{catalogItem.notes}</p>
        </div>
      )}

      <button
        onClick={() => onConfirm(form)}
        className="w-full py-3 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 transition-colors"
      >
        Add Item to Tracker
      </button>
    </div>
  );
}
```

### Task 10: Items Page with Interval Editor (`frontend/app/items/page.tsx`)

Enhanced items list with per-row interval editing, priority badges, and API budget footer.

**Priority badge component:**
```tsx
function PriorityBadge({ interval }: { interval: number }) {
  if (interval <= 360) return <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-red-100 text-red-700">HOT</span>;
  if (interval <= 600) return <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-orange-100 text-orange-700">STD</span>;
  if (interval <= 1200) return <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-blue-100 text-blue-700">MON</span>;
  return <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-gray-100 text-gray-600">PSV</span>;
}
```

**Inline interval editor (dropdown per row):**
```tsx
function IntervalEditor({ item, onChange }: { item: any; onChange: (id: number, interval: number) => void }) {
  const presets = [
    { value: 300, label: "5 min" },
    { value: 600, label: "10 min" },
    { value: 1200, label: "20 min" },
    { value: 1800, label: "30 min" },
  ];

  return (
    <select
      value={item.search_interval}
      onChange={(e) => onChange(item.id, parseInt(e.target.value))}
      className="text-xs border rounded px-1 py-0.5 bg-white"
    >
      {presets.map(p => (
        <option key={p.value} value={p.value}>{p.label}</option>
      ))}
      <option value={item.search_interval} disabled>Custom ({Math.round(item.search_interval/60)}m)</option>
    </select>
  );
}
```

**API Budget Footer (sticky at bottom of items page):**
```tsx
function BudgetFooter() {
  const [stats, setStats] = useState<any>(null);

  useEffect(() => {
    apiClient.getItemStats().then(setStats).catch(() => {});
  }, []);

  if (!stats) return null;

  const totalCalls = stats.items?.reduce((sum: number, item: any) =>
    sum + Math.ceil(86400 / item.search_interval), 0) || 0;

  return (
    <div className="sticky bottom-0 bg-white border-t p-3 shadow-lg">
      <div className="flex items-center justify-between max-w-7xl mx-auto">
        <div className="flex items-center gap-4">
          <span className="text-sm font-medium">
            {stats.total_items} items
          </span>
          <span className="text-xs px-2 py-0.5 rounded bg-red-100 text-red-700">
            {stats.p0_count || 0} Hot
          </span>
          <span className="text-xs px-2 py-0.5 rounded bg-orange-100 text-orange-700">
            {stats.p1_count || 0} Std
          </span>
          <span className="text-xs px-2 py-0.5 rounded bg-blue-100 text-blue-700">
            {stats.p2_count || 0} Mon
          </span>
          <span className="text-xs px-2 py-0.5 rounded bg-gray-100 text-gray-600">
            {stats.p3_count || 0} Psv
          </span>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs text-slate-500">
            Est. {totalCalls.toLocaleString()} calls/day
          </span>
          <span className={`text-xs font-bold ${totalCalls > 5000 ? "text-red-600" : totalCalls > 4000 ? "text-amber-600" : "text-green-600"}`}>
            {Math.round(totalCalls/5000*100)}% of budget
          </span>
        </div>
      </div>
    </div>
  );
}
```

### Task 11: Bulk Actions Bar

Sticky action bar for selecting and bulk-updating items:

```tsx
function BulkActionsBar({
  selectedIds,
  onEnable,
  onDisable,
  onSetInterval,
  onDelete,
  onClear
}: {
  selectedIds: number[];
  onEnable: () => void;
  onDisable: () => void;
  onSetInterval: (interval: number) => void;
  onDelete: () => void;
  onClear: () => void;
}) {
  if (selectedIds.length === 0) return null;

  return (
    <div className="sticky top-0 z-10 bg-indigo-600 text-white px-4 py-2 shadow-md">
      <div className="flex items-center justify-between max-w-7xl mx-auto">
        <span className="text-sm font-medium">{selectedIds.length} selected</span>
        <div className="flex items-center gap-2">
          <button onClick={onEnable} className="text-xs px-2 py-1 bg-white/20 rounded hover:bg-white/30">Enable</button>
          <button onClick={onDisable} className="text-xs px-2 py-1 bg-white/20 rounded hover:bg-white/30">Disable</button>
          <select onChange={(e) => onSetInterval(parseInt(e.target.value))} className="text-xs text-slate-800 rounded px-2 py-1">
            <option value="">Set interval...</option>
            <option value={300}>5 min (Hot)</option>
            <option value={600}>10 min (Std)</option>
            <option value={1200}>20 min (Mon)</option>
            <option value={1800}>30 min (Psv)</option>
          </select>
          <button onClick={onDelete} className="text-xs px-2 py-1 bg-red-500 rounded hover:bg-red-600">Delete</button>
          <button onClick={onClear} className="text-xs px-2 py-1 bg-white/20 rounded hover:bg-white/30">Clear</button>
        </div>
      </div>
    </div>
  );
}
```

### Task 12: Custom Hook (`frontend/lib/hooks.ts`)

```typescript
import { useState, useEffect } from "react";

export function useDebounce<T>(value: T, delay: number): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);
  return debounced;
}
```

### Task 13: Global CSS

**`frontend/app/globals.css`**:
```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  body {
    @apply antialiased;
  }
}
```

### Task 10: Tailwind Config

**`frontend/tailwind.config.ts`**:
```typescript
import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: { 50: "#eef2ff", 500: "#667eea", 600: "#5a67d8", 700: "#4c51bf" },
      },
    },
  },
  plugins: [],
};
export default config;
```

---

## Deliverables

- [ ] `app/layout.tsx` — Root layout with sidebar
- [ ] `app/page.tsx` — Dashboard with stats, charts, deals, **API usage bar**
- [ ] `app/items/page.tsx` — Tracked items CRUD with **interval editor**, **priority badges**, **bulk actions**, **budget footer**
- [ ] `app/items/add/page.tsx` — **Add Item Wizard** (auto-suggest → configure → confirm)
- [ ] `app/deals/page.tsx` — Deals browser with filters
- [ ] `app/history/page.tsx` — Price history with charts
- [ ] `app/alerts/page.tsx` — Alert history
- [ ] `app/settings/page.tsx` — Notification settings
- [ ] `components/sidebar.tsx` — Navigation sidebar
- [ ] `components/top-bar.tsx` — Header with search
- [ ] `components/score-badge.tsx` — Score visualization
- [ ] `components/deals-table.tsx` — Deal listing table
- [ ] `components/trend-chart.tsx` — Recharts price chart
- [ ] `components/stats-card.tsx` — Dashboard stat card
- [ ] `components/activity-feed.tsx` — Activity list
- [ ] **`components/api-usage-bar.tsx`** — Real-time eBay API budget tracker
- [ ] **`components/interval-editor.tsx`** — Per-row interval dropdown
- [ ] **`components/priority-badge.tsx`** — Hot/Std/Mon/Psv color badges
- [ ] **`components/bulk-actions-bar.tsx`** — Multi-select bulk action bar
- [ ] **`components/add-item-wizard.tsx`** — 3-step add item wizard
- [ ] `lib/api.ts` — Typed API client with catalog + budget endpoints
- [ ] **`lib/hooks.ts`** — Custom hooks (useDebounce, etc.)
- [ ] `app/globals.css` — Global styles
- [ ] `tailwind.config.ts` — Tailwind configuration

## Git
Branch: `phase-06-frontend`
Base: `main` (after Phase 2 merge)
Commit message: `feat(phase-6): Next.js frontend, dashboard, all pages`
