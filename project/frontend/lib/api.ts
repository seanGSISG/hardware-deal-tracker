const API_BASE = process.env.NEXT_PUBLIC_API_URL || "/api";

async function api<T>(path: string, options?: RequestInit): Promise<T> {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };

  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || `API error: ${response.status}`);
  }
  return response.json();
}

export const apiClient = {
  login: (data: { username: string; password: string }) =>
    api<{ access_token: string }>("/auth/login", { method: "POST", body: JSON.stringify(data) }),
  register: (data: { username: string; email: string; password: string }) =>
    api<{ access_token: string }>("/auth/register", { method: "POST", body: JSON.stringify(data) }),

  getItems: (params?: Record<string, string>) =>
    api(`/items?${new URLSearchParams(params)}`),
  createItem: (data: unknown) => api("/items", { method: "POST", body: JSON.stringify(data) }),
  updateItem: (id: number, data: unknown) => api(`/items/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  deleteItem: (id: number) => api(`/items/${id}`, { method: "DELETE" }),
  toggleItem: (id: number) => api(`/items/${id}/toggle`, { method: "PUT" }),
  bulkUpdateItems: (data: unknown) => api("/items/bulk-update", { method: "POST", body: JSON.stringify(data) }),
  getItemStats: () => api("/items/stats"),

  searchCatalog: (query: string) => api(`/catalog?q=${encodeURIComponent(query)}`),
  getCategories: () => api("/categories"),

  getDeals: (params?: Record<string, string>) =>
    api(`/deals?${new URLSearchParams(params)}`),

  getBudget: () => api("/search/budget"),
  getPresets: () => api("/search/presets"),

  getAlerts: (params?: Record<string, string>) =>
    api(`/alerts?${new URLSearchParams(params)}`),

  getNotificationSettings: () => api("/settings/notifications"),
  updateNotificationSettings: (data: unknown) => api("/settings/notifications", { method: "PUT", body: JSON.stringify(data) }),

  triggerSearch: (itemId: number) => api(`/search/trigger/${itemId}`, { method: "POST" }),
  triggerAll: () => api("/search/trigger-all", { method: "POST" }),
};
