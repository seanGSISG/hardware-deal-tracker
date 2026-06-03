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
    }>(`/price-history/${itemId}?days=${days}`),

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
};
