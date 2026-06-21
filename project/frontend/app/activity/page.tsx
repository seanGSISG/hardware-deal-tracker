"use client";

import { useCallback, useEffect, useState } from "react";
import { apiClient } from "@/lib/api";
import type { SearchLogEntry, ActivitySummary } from "@/lib/api";

const STATUS_FILTERS = [
  { key: "", label: "All" },
  { key: "ok", label: "OK" },
  { key: "skipped", label: "Skipped" },
  { key: "error", label: "Error" },
];

const PER_PAGE = 50;

function statusBadge(status: string): string {
  if (status === "ok") return "bg-green-500/15 text-green-400 border-green-500/30";
  if (status === "skipped") return "bg-amber/15 text-amber border-amber/30";
  if (status === "error") return "bg-red-500/15 text-red-400 border-red-500/30";
  return "bg-surface-2 text-text-muted border-border";
}

function fmtTime(iso: string | null): string {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleString(undefined, {
    month: "short", day: "2-digit", hour: "2-digit", minute: "2-digit", second: "2-digit",
  });
}

function relTime(iso: string | null): string {
  if (!iso) return "never";
  const secs = Math.max(0, (Date.now() - new Date(iso).getTime()) / 1000);
  if (secs < 60) return `${Math.floor(secs)}s ago`;
  if (secs < 3600) return `${Math.floor(secs / 60)}m ago`;
  if (secs < 86400) return `${Math.floor(secs / 3600)}h ago`;
  return `${Math.floor(secs / 86400)}d ago`;
}

function StatCard({ label, value, hint }: { label: string; value: string | number; hint?: string }) {
  return (
    <div className="bg-surface rounded-xl border border-border p-4">
      <p className="label text-text-dim">{label}</p>
      <p className="text-2xl font-bold text-text mt-1">{value}</p>
      {hint && <p className="text-xs text-text-muted mt-0.5">{hint}</p>}
    </div>
  );
}

export default function ActivityPage() {
  const [entries, setEntries] = useState<SearchLogEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [summary, setSummary] = useState<ActivitySummary | null>(null);
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const params: Record<string, string> = { page: String(page), per_page: String(PER_PAGE) };
      if (status) params.status = status;
      const [list, sum] = await Promise.all([
        apiClient.getActivity(params),
        apiClient.getActivitySummary(),
      ]);
      setEntries(list.entries || []);
      setTotal(list.total || 0);
      setSummary(sum);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load activity");
    } finally {
      setLoading(false);
    }
  }, [page, status]);

  useEffect(() => {
    setLoading(true);
    load();
  }, [load]);

  // Auto-refresh every 30s (the poller ticks every 5 min, so this stays fresh).
  useEffect(() => {
    const id = setInterval(load, 30_000);
    return () => clearInterval(id);
  }, [load]);

  const pages = Math.max(1, Math.ceil(total / PER_PAGE));

  return (
    <div className="max-w-7xl mx-auto space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-text">Activity</h1>
        {summary && (
          <p className="text-xs text-text-muted">
            Last search <span className="text-text">{relTime(summary.last_search_at)}</span>
            <span className="text-text-dim"> · auto-refresh 30s</span>
          </p>
        )}
      </div>

      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          <StatCard label="SEARCHES / 1H" value={summary.searches_last_hour} />
          <StatCard label="SEARCHES / 24H" value={summary.searches_last_24h} />
          <StatCard label="EBAY CALLS / 24H" value={summary.calls_last_24h} hint="of 5,000/day" />
          <StatCard label="OK / 24H" value={summary.ok_last_24h} />
          <StatCard
            label="SKIP · ERR / 24H"
            value={`${summary.skipped_last_24h} · ${summary.error_last_24h}`}
          />
        </div>
      )}

      <div className="flex items-center gap-2">
        {STATUS_FILTERS.map((f) => (
          <button
            key={f.key}
            onClick={() => { setPage(1); setStatus(f.key); }}
            className={`px-3 py-1.5 rounded-lg text-sm border transition-colors ${
              status === f.key
                ? "bg-surface-2 text-text border-border"
                : "text-text-muted border-transparent hover:text-text hover:bg-surface-2"
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {error && (
        <div className="bg-surface rounded-xl border border-red-500/30 p-4 text-sm text-red-400">
          {error}
        </div>
      )}

      <div className="bg-surface rounded-xl border border-border overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left label text-text-dim border-b border-border">
                <th className="px-4 py-3 font-normal">Time</th>
                <th className="px-4 py-3 font-normal">Item</th>
                <th className="px-4 py-3 font-normal">Source</th>
                <th className="px-4 py-3 font-normal">Status</th>
                <th className="px-4 py-3 font-normal text-right">Found</th>
                <th className="px-4 py-3 font-normal text-right">New</th>
                <th className="px-4 py-3 font-normal text-right">Calls</th>
                <th className="px-4 py-3 font-normal text-right">ms</th>
                <th className="px-4 py-3 font-normal">Detail</th>
              </tr>
            </thead>
            <tbody>
              {loading && entries.length === 0 ? (
                <tr><td colSpan={9} className="px-4 py-10 text-center text-text-muted">Loading activity…</td></tr>
              ) : entries.length === 0 ? (
                <tr><td colSpan={9} className="px-4 py-10 text-center text-text-muted">
                  No searches logged yet. The poller runs every 5 minutes — check back shortly.
                </td></tr>
              ) : (
                entries.map((e) => (
                  <tr key={e.id} className="border-b border-border/50 hover:bg-surface-2/50">
                    <td className="px-4 py-2.5 whitespace-nowrap text-text-muted" title={e.created_at || ""}>
                      {fmtTime(e.created_at)}
                    </td>
                    <td className="px-4 py-2.5 text-text">{e.item_name}</td>
                    <td className="px-4 py-2.5 text-text-muted">{e.source}</td>
                    <td className="px-4 py-2.5">
                      <span className={`inline-block px-2 py-0.5 rounded-full text-xs border ${statusBadge(e.status)}`}>
                        {e.status}
                      </span>
                    </td>
                    <td className="px-4 py-2.5 text-right tabular-nums text-text-muted">{e.listings_found}</td>
                    <td className="px-4 py-2.5 text-right tabular-nums text-text">{e.new_listings || ""}</td>
                    <td className="px-4 py-2.5 text-right tabular-nums text-text-muted">{e.calls_used}</td>
                    <td className="px-4 py-2.5 text-right tabular-nums text-text-dim">{e.duration_ms || ""}</td>
                    <td className="px-4 py-2.5 text-text-muted max-w-xs truncate" title={e.detail || ""}>
                      {e.detail || ""}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      <div className="flex items-center justify-between text-sm text-text-muted">
        <span>{total.toLocaleString()} total searches logged</span>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page <= 1}
            className="px-3 py-1.5 rounded-lg border border-border disabled:opacity-40 hover:bg-surface-2"
          >
            Prev
          </button>
          <span className="text-text-dim">Page {page} / {pages}</span>
          <button
            onClick={() => setPage((p) => Math.min(pages, p + 1))}
            disabled={page >= pages}
            className="px-3 py-1.5 rounded-lg border border-border disabled:opacity-40 hover:bg-surface-2"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}
