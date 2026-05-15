"use client";

import { useEffect, useState } from "react";
import { apiClient } from "@/lib/api";
import Link from "next/link";
import { Plus, Pause, Play, Trash2, Clock, Search } from "lucide-react";

interface TrackedItem {
  id: number;
  name: string;
  keywords: string;
  target_price: number | null;
  alert_threshold: number;
  search_interval: number;
  is_enabled: boolean;
  scam_floor: number | null;
  benchmark_median: number | null;
  notes: string | null;
}

function getPriorityBadge(interval: number) {
  if (interval <= 360) return <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-red-100 text-red-700">HOT</span>;
  if (interval <= 600) return <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-orange-100 text-orange-700">STD</span>;
  if (interval <= 1200) return <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-blue-100 text-blue-700">MON</span>;
  return <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-gray-100 text-gray-600">PSV</span>;
}

function formatInterval(seconds: number) {
  if (seconds <= 60) return `${seconds}s`;
  if (seconds < 3600) return `${Math.round(seconds / 60)}m`;
  return `${Math.round(seconds / 3600)}h`;
}

export default function ItemsPage() {
  const [items, setItems] = useState<TrackedItem[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("");

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    try {
      const [itemsRes, statsRes] = await Promise.all([
        apiClient.getItems({ per_page: "100" }),
        apiClient.getItemStats(),
      ]);
      setItems(itemsRes.items || []);
      setStats(statsRes);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  async function toggleItem(id: number) {
    await apiClient.toggleItem(id);
    setItems(prev => prev.map(i => i.id === id ? { ...i, is_enabled: !i.is_enabled } : i));
  }

  async function deleteItem(id: number) {
    if (!confirm("Delete this item?")) return;
    await apiClient.deleteItem(id);
    setItems(prev => prev.filter(i => i.id !== id));
  }

  async function updateInterval(id: number, interval: number) {
    await apiClient.updateItem(id, { search_interval: interval });
    setItems(prev => prev.map(i => i.id === id ? { ...i, search_interval: interval } : i));
  }

  const filtered = items.filter(i =>
    i.name.toLowerCase().includes(filter.toLowerCase()) ||
    i.keywords.toLowerCase().includes(filter.toLowerCase())
  );

  if (loading) return <div className="p-8 text-center text-slate-500">Loading...</div>;

  return (
    <div className="max-w-7xl mx-auto space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-800">Tracked Items ({items.length})</h1>
        <Link href="/items/add" className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors text-sm font-medium">
          <Plus className="w-4 h-4" /> Add Item
        </Link>
      </div>

      <div className="flex items-center gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            value={filter}
            onChange={e => setFilter(e.target.value)}
            placeholder="Search items..."
            className="w-full pl-9 pr-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
          />
        </div>
        {stats && (
          <div className="flex items-center gap-2 text-xs text-slate-500">
            <span className="px-2 py-0.5 rounded bg-red-100 text-red-700 font-bold">{stats.p0_count} Hot</span>
            <span className="px-2 py-0.5 rounded bg-orange-100 text-orange-700 font-bold">{stats.p1_count} Std</span>
            <span className="px-2 py-0.5 rounded bg-blue-100 text-blue-700 font-bold">{stats.p2_count} Mon</span>
            <span className="px-2 py-0.5 rounded bg-gray-100 text-gray-600 font-bold">{stats.p3_count} Psv</span>
            <span className="ml-2">~{stats.estimated_daily_calls} calls/day</span>
          </div>
        )}
      </div>

      <div className="bg-white rounded-xl border shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 border-b">
            <tr>
              <th className="text-left px-4 py-3 font-medium text-slate-500">Name</th>
              <th className="text-left px-4 py-3 font-medium text-slate-500">Target</th>
              <th className="text-left px-4 py-3 font-medium text-slate-500">Interval</th>
              <th className="text-left px-4 py-3 font-medium text-slate-500">Status</th>
              <th className="text-right px-4 py-3 font-medium text-slate-500">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {filtered.map(item => (
              <tr key={item.id} className={`hover:bg-slate-50 transition-colors ${!item.is_enabled ? "opacity-50" : ""}`}>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    {getPriorityBadge(item.search_interval)}
                    <div>
                      <p className="font-medium text-slate-800">{item.name}</p>
                      {item.notes && <p className="text-xs text-slate-400 truncate max-w-[300px]">{item.notes}</p>}
                    </div>
                  </div>
                </td>
                <td className="px-4 py-3">
                  {item.target_price ? (
                    <span className="font-mono text-sm">${item.target_price}</span>
                  ) : "—"}
                  {item.scam_floor ? (
                    <span className="text-xs text-red-500 ml-1">floor: ${item.scam_floor}</span>
                  ) : null}
                </td>
                <td className="px-4 py-3">
                  <select
                    value={item.search_interval}
                    onChange={e => updateInterval(item.id, parseInt(e.target.value))}
                    className="text-xs border rounded px-1 py-0.5 bg-white"
                  >
                    <option value={300}>5 min (Hot)</option>
                    <option value={600}>10 min (Std)</option>
                    <option value={1200}>20 min (Mon)</option>
                    <option value={1800}>30 min (Psv)</option>
                  </select>
                </td>
                <td className="px-4 py-3">
                  <span className={`text-xs font-medium px-2 py-0.5 rounded ${item.is_enabled ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-600"}`}>
                    {item.is_enabled ? "Active" : "Paused"}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center justify-end gap-1">
                    <button onClick={() => toggleItem(item.id)} className="p-1 rounded hover:bg-slate-100 text-slate-500">
                      {item.is_enabled ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                    </button>
                    <button onClick={() => deleteItem(item.id)} className="p-1 rounded hover:bg-red-50 text-red-500">
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {filtered.length === 0 && (
          <div className="p-8 text-center text-slate-400">
            {filter ? "No items match your search." : "No items yet. Add your first item to start tracking!"}
          </div>
        )}
      </div>
    </div>
  );
}
