import type {
  TokenData,
  TrackedItem,
  TrackedItemStats,
  ItemsListResponse,
  ToggleResponse,
  BulkUpdateResponse,
  DealsListResponse,
  BudgetStatus,
  PresetsResponse,
  AlertsListResponse,
  NotificationSettings,
  CatalogSuggestion,
  Category,
  SearchTriggerResponse,
  SearchTriggerAllResponse,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "/api";

async function api<T>(path: string, options?: RequestInit): Promise<T> {
  // Auth is carried by the httpOnly `session` cookie (ADR-002). credentials:
  // "include" makes the browser send it automatically; we no longer read a token
  // from localStorage or attach an Authorization header.
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
    credentials: "include",
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || `API error: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export const apiClient = {
  login: (data: { username: string; password: string }) =>
    api<TokenData>("/auth/login", { method: "POST", body: JSON.stringify(data) }),
  register: (data: { username: string; email: string; password: string }) =>
    api<TokenData>("/auth/register", { method: "POST", body: JSON.stringify(data) }),
  // Clears the backend-set httpOnly `session` cookie.
  logout: () => api<{ detail: string }>("/auth/logout", { method: "POST" }),

  getItems: (params?: Record<string, string>) =>
    api<ItemsListResponse>(`/items?${new URLSearchParams(params)}`),
  createItem: (data: unknown) =>
    api<TrackedItem>("/items", { method: "POST", body: JSON.stringify(data) }),
  updateItem: (id: number, data: unknown) =>
    api<TrackedItem>(`/items/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  deleteItem: (id: number) =>
    api<{ detail: string }>(`/items/${id}`, { method: "DELETE" }),
  toggleItem: (id: number) =>
    api<ToggleResponse>(`/items/${id}/toggle`, { method: "PUT" }),
  bulkUpdateItems: (data: unknown) =>
    api<BulkUpdateResponse>("/items/bulk-update", { method: "POST", body: JSON.stringify(data) }),
  getItemStats: () => api<TrackedItemStats>("/items/stats"),

  searchCatalog: (query: string) =>
    api<CatalogSuggestion[]>(`/catalog?q=${encodeURIComponent(query)}`),
  getCategories: () => api<Category[]>("/catalog/categories"),

  getDeals: (params?: Record<string, string>) =>
    api<DealsListResponse>(`/deals?${new URLSearchParams(params)}`),

  getBudget: () => api<BudgetStatus>("/search/budget"),
  getPresets: () => api<PresetsResponse>("/search/presets"),

  getAlerts: (params?: Record<string, string>) =>
    api<AlertsListResponse>(`/alerts?${new URLSearchParams(params)}`),

  getNotificationSettings: () => api<NotificationSettings>("/settings/notifications"),
  updateNotificationSettings: (data: unknown) =>
    api<NotificationSettings>("/settings/notifications", { method: "PUT", body: JSON.stringify(data) }),

  triggerSearch: (itemId: number) =>
    api<SearchTriggerResponse>(`/search/trigger/${itemId}`, { method: "POST" }),
  triggerAll: () => api<SearchTriggerAllResponse>("/search/trigger-all", { method: "POST" }),

  getPriceHistory: (itemId: number, days = 90) =>
    api<{
      item_id: number;
      days: number;
      count: number;
      points: { timestamp: string; observed_price: number; shipping: number; total_price: number }[];
      median_total: number | null;
      latest_total: number | null;
      vs_median_pct: number | null;
      benchmark_median: number | null;
      // Sold-comps baseline block (feature-001). Additive: absent/null when the
      // baseline service has insufficient data, in which case the chart degrades
      // to points + benchmark reference line only.
      baseline?: {
        median: number | null;
        avg: number | null;
        std_dev: number | null;
        min: number | null;
        q1: number | null;
        q3: number | null;
        data_points: number;
        lookback_days: number;
        vs_median_pct: number | null;
        source: string | null;
        trend_direction: "rising" | "falling" | "stable" | string | null;
        trend_slope_pct: number | null;
        computed_at: string | null;
        benchmark_median: number | null;
      } | null;
    }>(`/price-history/${itemId}?days=${days}`),

  // Prometheus text-format metrics live at the app root (/metrics), NOT under
  // /api/v1. We parse the hdt_* counters/gauges for the dashboard. Degrades
  // gracefully: returns null when /metrics is unavailable or unparsable so the
  // metrics cards are simply omitted. Auth still via the session cookie.
  getMetrics: async (): Promise<Record<string, number> | null> => {
    try {
      // API_BASE is typically "/api"; strip a trailing "/api" (or "/api/v1") to
      // reach the app root where /metrics is served.
      const root = API_BASE.replace(/\/api(\/v1)?$/, "");
      const res = await fetch(`${root}/metrics`, { credentials: "include" });
      if (!res.ok) return null;
      const text = await res.text();
      const out: Record<string, number> = {};
      for (const line of text.split("\n")) {
        const trimmed = line.trim();
        if (!trimmed || trimmed.startsWith("#")) continue;
        // Match: metric_name{labels} value   OR   metric_name value
        const m = trimmed.match(/^([a-zA-Z_:][a-zA-Z0-9_:]*)(\{[^}]*\})?\s+([0-9eE+\-.]+)$/);
        if (!m) continue;
        const name = m[1];
        const value = Number(m[3]);
        if (!name.startsWith("hdt_") || Number.isNaN(value)) continue;
        // Sum across label permutations for the same counter name.
        out[name] = (out[name] ?? 0) + value;
      }
      return Object.keys(out).length > 0 ? out : null;
    } catch {
      return null;
    }
  },

  getListingAnalysis: (listingId: number) =>
    api<{
      analysis: null | {
        deal_grade: string | null;
        reasoning: string | null;
        scam_signal: boolean;
        scam_reasons: string[] | null;
        extracted_specs: Record<string, unknown> | null;
        provider: string;
        model: string;
        created_at: string | null;
      };
    }>(`/ai/${listingId}`),

  // Community-signal leads (feature-007, ADR-007). A SEPARATE surface from scored
  // listings; returns { enabled:false, leads:[] } when ENABLE_COMMUNITY_SIGNAL is off.
  getCommunityLeads: (params?: Record<string, string>) =>
    api<CommunityLeadsResponse>(`/community-signal/leads?${new URLSearchParams(params)}`),

  // Activity log — durable per-item search audit (search_log table).
  getActivity: (params?: Record<string, string>) =>
    api<ActivityListResponse>(`/activity?${new URLSearchParams(params)}`),
  getActivitySummary: () => api<ActivitySummary>("/activity/summary"),
};

export interface SearchLogEntry {
  id: number;
  tracked_item_id: number | null;
  item_name: string;
  source: string;
  status: "ok" | "skipped" | "error" | string;
  priority: string | null;
  listings_found: number;
  new_listings: number;
  duplicates: number;
  calls_used: number;
  duration_ms: number;
  detail: string | null;
  created_at: string | null;
}

export interface ActivityListResponse {
  total: number;
  page: number;
  per_page: number;
  entries: SearchLogEntry[];
}

export interface ActivitySummary {
  last_search_at: string | null;
  searches_last_hour: number;
  searches_last_24h: number;
  ok_last_24h: number;
  skipped_last_24h: number;
  error_last_24h: number;
  calls_last_24h: number;
}

export interface CommunityLead {
  id: number;
  source: string;
  source_post_id: string;
  catalog_item_id: number | null;
  title: string;
  url: string;
  author: string | null;
  model: string | null;
  price: number | null;
  condition: string | null;
  location: string | null;
  status: string;
  confidence: number | null;
  ai_reason: string | null;
  posted_at: string | null;
  ingested_at: string | null;
}

export interface CommunityLeadsResponse {
  enabled: boolean;
  count: number;
  leads: CommunityLead[];
}
