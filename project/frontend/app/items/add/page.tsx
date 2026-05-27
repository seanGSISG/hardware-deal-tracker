"use client";

import { useState, useEffect } from "react";
import { useDebounce } from "@/lib/hooks";
import { apiClient } from "@/lib/api";
import type { CatalogSuggestion as CatalogItem, Category } from "@/lib/types";
import { useRouter } from "next/navigation";
import { Search, Package, Cpu, HardDrive, Zap, ArrowLeft, Check } from "lucide-react";

interface TrackedItemForm {
  name?: string;
  keywords?: string;
  sku?: string;
  mpn?: string;
  category_id?: string;
  target_price?: number;
  alert_threshold?: number;
  search_interval?: number;
  scam_floor?: number;
  benchmark_median?: number;
  notes?: string;
  min_deal_score?: number;
  is_enabled?: boolean;
}

const INTERVAL_PRESETS = [
  { key: "hot", label: "Hot (5 min)", interval: 300, color: "bg-red-100 text-red-700 border-red-200" },
  { key: "standard", label: "Standard (10 min)", interval: 600, color: "bg-orange-100 text-orange-700 border-orange-200" },
  { key: "monitor", label: "Monitor (20 min)", interval: 1200, color: "bg-blue-100 text-blue-700 border-blue-200" },
  { key: "passive", label: "Passive (30 min)", interval: 1800, color: "bg-gray-100 text-gray-600 border-gray-200" },
];

export default function AddItemPage() {
  const router = useRouter();
  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [query, setQuery] = useState("");
  const [suggestions, setSuggestions] = useState<CatalogItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [selected, setSelected] = useState<CatalogItem | null>(null);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [form, setForm] = useState<TrackedItemForm>({});
  const [categories, setCategories] = useState<Category[]>([]);
  const [preset, setPreset] = useState("standard");
  const debouncedQuery = useDebounce(query, 300);

  useEffect(() => {
    apiClient.getCategories().then(setCategories).catch(() => {});
  }, []);

  useEffect(() => {
    if (debouncedQuery.length < 2) {
      setSuggestions([]);
      return;
    }
    async function search() {
      setLoading(true);
      try {
        const results = await apiClient.searchCatalog(debouncedQuery);
        setSuggestions(results || []);
      } catch {
        setSuggestions([]);
      }
      setLoading(false);
    }
    search();
  }, [debouncedQuery]);

  function selectItem(item: CatalogItem) {
    setSelected(item);
    setForm({
      name: item.name,
      keywords: item.keywords,
      sku: item.sku,
      mpn: item.mpn,
      category_id: item.category_id,
      target_price: item.target_price,
      alert_threshold: item.alert_threshold,
      search_interval: item.search_interval,
      scam_floor: item.scam_floor,
      benchmark_median: item.benchmark_median,
      notes: item.notes,
      min_deal_score: 60,
      is_enabled: true,
    });
    const p = item.search_interval <= 300 ? "hot" : item.search_interval <= 600 ? "standard" : item.search_interval <= 1200 ? "monitor" : "passive";
    setPreset(p);
    setStep(2);
  }

  async function handleSubmit() {
    setSaving(true);
    try {
      await apiClient.createItem(form);
      setSaved(true);
      setStep(3);
    } catch (err) {
      alert("Failed to add item: " + (err as Error).message);
    } finally {
      setSaving(false);
    }
  }

  const dailyCalls = Math.ceil(86400 / (form.search_interval || 600));

  function Step1() {
    return (
      <div className="space-y-4">
        <h2 className="text-lg font-semibold text-slate-800">Step 1: Search for hardware</h2>
        <p className="text-sm text-slate-500">Type a product name, SKU, or keyword to search our catalog.</p>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="Try: RTX PRO 6000, H12SSL, Exos 16TB, M393A8G40..."
            className="w-full pl-10 pr-4 py-3 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            autoFocus
          />
        </div>
        {loading && <p className="text-xs text-slate-400">Searching catalog...</p>}
        {suggestions.length > 0 && (
          <div className="border rounded-lg divide-y max-h-96 overflow-y-auto">
            {suggestions.map((item, idx) => (
              <button key={idx} onClick={() => selectItem(item)} className="w-full flex items-center gap-3 p-3 hover:bg-slate-50 text-left transition-colors">
                <div className="w-8 h-8 rounded bg-indigo-50 flex items-center justify-center text-indigo-600 shrink-0">
                  {item.category_id === "164" ? <Cpu className="w-4 h-4" /> : item.category_id === "56083" ? <HardDrive className="w-4 h-4" /> : item.category_id === "27386" ? <Zap className="w-4 h-4" /> : <Package className="w-4 h-4" />}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-sm truncate">{item.name}</p>
                  <p className="text-xs text-slate-500">
                    Target: ${item.target_price} | Est. median: ${item.benchmark_median}
                    {item.scam_floor > 0 && <span className="ml-2 text-red-500 font-medium">Scam floor: ${item.scam_floor}</span>}
                  </p>
                </div>
              </button>
            ))}
          </div>
        )}
        {query.length >= 2 && suggestions.length === 0 && !loading && (
          <div className="text-center py-8 text-slate-500">
            <p>No catalog match. You can still create a custom item.</p>
          </div>
        )}
        <div className="border-t pt-4">
          <p className="text-xs text-slate-400 mb-2">Or create custom item:</p>
          <button
            onClick={() => selectItem({ name: query, keywords: query, sku: "", mpn: "", category_id: "56083", target_price: 0, alert_threshold: 0.20, search_interval: 600, benchmark_median: 0, scam_floor: 0, notes: "" })}
            className="text-sm text-indigo-600 hover:underline"
          >
            Create &quot;{query || "custom item"}&quot; manually
          </button>
        </div>
      </div>
    );
  }

  function Step2() {
    if (!selected) return null;
    return (
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <button onClick={() => setStep(1)} className="p-1 rounded hover:bg-slate-100"><ArrowLeft className="w-4 h-4" /></button>
          <h2 className="text-lg font-semibold text-slate-800">Step 2: Configure tracking</h2>
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Name</label>
          <input value={form.name ?? ""} onChange={e => setForm({ ...form, name: e.target.value })} className="w-full px-3 py-2 border rounded-lg text-sm" />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Search Keywords</label>
          <textarea value={form.keywords ?? ""} onChange={e => setForm({ ...form, keywords: e.target.value })} className="w-full px-3 py-2 border rounded-lg text-sm" rows={2} />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Target Price ($)</label>
            <input type="number" step="0.01" value={form.target_price ?? ""} onChange={e => setForm({ ...form, target_price: parseFloat(e.target.value) })} className="w-full px-3 py-2 border rounded-lg text-sm" />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Alert Threshold (% below median)</label>
            <input type="number" step="0.05" min="0" max="1" value={form.alert_threshold ?? 0.20} onChange={e => setForm({ ...form, alert_threshold: parseFloat(e.target.value) })} className="w-full px-3 py-2 border rounded-lg text-sm" />
          </div>
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-2">Polling Frequency ({dailyCalls} calls/day)</label>
          <div className="grid grid-cols-4 gap-2">
            {INTERVAL_PRESETS.map(p => (
              <button key={p.key} onClick={() => { setPreset(p.key); setForm({ ...form, search_interval: p.interval }); }}
                className={`px-3 py-2 rounded-lg border text-xs font-medium transition-colors ${preset === p.key ? `${p.color} ring-2 ring-offset-1 ring-indigo-500` : "bg-white border-slate-200 text-slate-600 hover:bg-slate-50"}`}>
                {p.label}
              </button>
            ))}
          </div>
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">eBay Category</label>
          <select value={form.category_id ?? ""} onChange={e => setForm({ ...form, category_id: e.target.value })} className="w-full px-3 py-2 border rounded-lg text-sm">
            {categories.map(cat => <option key={cat.id} value={cat.id}>{cat.name}</option>)}
          </select>
        </div>
        {selected.scam_floor > 0 && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-3">
            <p className="text-sm font-medium text-red-700">Scam Floor: ${selected.scam_floor}</p>
            <p className="text-xs text-red-600 mt-1">Listings below this price will be flagged as suspicious.</p>
          </div>
        )}
        {selected.notes && <div className="bg-blue-50 border border-blue-200 rounded-lg p-3"><p className="text-xs text-blue-700">{selected.notes}</p></div>}
        <button onClick={handleSubmit} disabled={saving} className="w-full py-3 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 transition-colors disabled:opacity-50">
          {saving ? "Adding..." : "Add Item to Tracker"}
        </button>
      </div>
    );
  }

  function Step3() {
    return (
      <div className="text-center py-12 space-y-4">
        <div className="w-16 h-16 rounded-full bg-green-100 flex items-center justify-center mx-auto">
          <Check className="w-8 h-8 text-green-600" />
        </div>
        <h2 className="text-xl font-semibold text-slate-800">Item Added!</h2>
        <p className="text-sm text-slate-500">{form.name} is now being tracked.</p>
        <div className="flex justify-center gap-3">
          <button onClick={() => { setStep(1); setQuery(""); setSuggestions([]); setSelected(null); setSaved(false); }} className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm hover:bg-indigo-700">
            Add Another
          </button>
          <button onClick={() => router.push("/items")} className="px-4 py-2 border rounded-lg text-sm hover:bg-slate-50">
            View Items
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="bg-white rounded-xl border shadow-sm p-6">
        <div className="flex items-center gap-2 mb-6">
          {[1, 2, 3].map(s => (
            <div key={s} className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold ${step >= s ? "bg-indigo-600 text-white" : "bg-slate-100 text-slate-400"}`}>
              {s}
            </div>
          ))}
          <div className="flex-1 h-px bg-slate-200" />
        </div>
        {step === 1 && <Step1 />}
        {step === 2 && <Step2 />}
        {step === 3 && <Step3 />}
      </div>
    </div>
  );
}
