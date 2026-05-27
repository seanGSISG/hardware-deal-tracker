"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { Search, Plus } from "lucide-react";
import { apiClient } from "@/lib/api";
import type { TrackedItem, TrackedItemStats } from "@/lib/types";
import { ItemCard } from "@/components/item-card";
import { CategoryIcon, CATEGORY_NAMES } from "@/components/category-icon";

type SortKey = "priority" | "name" | "target" | "status";

const CATEGORY_STORAGE_KEY = "items-page-category";
const SORT_STORAGE_KEY = "items-page-sort";

const SORT_OPTIONS: Array<{ value: SortKey; label: string }> = [
  { value: "priority", label: "Priority" },
  { value: "name", label: "Name" },
  { value: "target", label: "Target Price" },
  { value: "status", label: "Status" },
];

export default function ItemsPage() {
  const [items, setItems] = useState<TrackedItem[]>([]);
  const [stats, setStats] = useState<TrackedItemStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<SortKey>("priority");
  const [filter, setFilter] = useState("");

  // Hydrate persisted UI state on mount.
  useEffect(() => {
    if (typeof window === "undefined") return;
    const savedCat = window.localStorage.getItem(CATEGORY_STORAGE_KEY);
    if (savedCat !== null) {
      setSelectedCategory(savedCat === "__ALL__" ? null : savedCat);
    }
    const savedSort = window.localStorage.getItem(SORT_STORAGE_KEY) as SortKey | null;
    if (
      savedSort &&
      (savedSort === "priority" ||
        savedSort === "name" ||
        savedSort === "target" ||
        savedSort === "status")
    ) {
      setSortBy(savedSort);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [itemsRes, statsRes] = await Promise.all([
          apiClient.getItems({ per_page: "100" }),
          apiClient.getItemStats(),
        ]);
        if (cancelled) return;
        setItems(itemsRes.items || []);
        setStats(statsRes);
      } catch (err) {
        console.error(err);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  function handleSelectCategory(catId: string | null) {
    setSelectedCategory(catId);
    if (typeof window !== "undefined") {
      window.localStorage.setItem(CATEGORY_STORAGE_KEY, catId === null ? "__ALL__" : catId);
    }
  }

  function handleSortChange(value: SortKey) {
    setSortBy(value);
    if (typeof window !== "undefined") {
      window.localStorage.setItem(SORT_STORAGE_KEY, value);
    }
  }

  // Build category list from loaded items: only categories that have items, sorted by count desc.
  const categoryRows = useMemo(() => {
    const counts = new Map<string, number>();
    for (const item of items) {
      const id = item.category_id ?? "__OTHER__";
      counts.set(id, (counts.get(id) ?? 0) + 1);
    }
    return Array.from(counts.entries())
      .map(([id, count]) => ({
        id,
        count,
        name: id === "__OTHER__" ? "OTHER" : CATEGORY_NAMES[id] ?? "OTHER",
      }))
      .sort((a, b) => b.count - a.count || a.name.localeCompare(b.name));
  }, [items]);

  // Scope items to selected category first.
  const scopedItems = useMemo(() => {
    if (selectedCategory === null) return items;
    if (selectedCategory === "__OTHER__") {
      return items.filter(
        (i) => !i.category_id || !(i.category_id in CATEGORY_NAMES),
      );
    }
    return items.filter((i) => i.category_id === selectedCategory);
  }, [items, selectedCategory]);

  // Then apply filter (case-insensitive against name + keywords).
  const filteredItems = useMemo(() => {
    const needle = filter.trim().toLowerCase();
    if (!needle) return scopedItems;
    return scopedItems.filter(
      (i) =>
        i.name.toLowerCase().includes(needle) ||
        (i.keywords ?? "").toLowerCase().includes(needle),
    );
  }, [scopedItems, filter]);

  // Sort.
  const visibleItems = useMemo(() => {
    const sorted = [...filteredItems];
    switch (sortBy) {
      case "priority":
        sorted.sort((a, b) => a.search_interval - b.search_interval);
        break;
      case "name":
        sorted.sort((a, b) => a.name.localeCompare(b.name));
        break;
      case "target":
        sorted.sort((a, b) => {
          const av = a.target_price;
          const bv = b.target_price;
          if (av === null && bv === null) return 0;
          if (av === null) return 1;
          if (bv === null) return -1;
          return bv - av;
        });
        break;
      case "status":
        sorted.sort((a, b) => {
          if (a.is_enabled === b.is_enabled) return 0;
          return a.is_enabled ? -1 : 1;
        });
        break;
    }
    return sorted;
  }, [filteredItems, sortBy]);

  const activeCategoryName =
    selectedCategory === null
      ? "ALL ITEMS"
      : selectedCategory === "__OTHER__"
        ? "OTHER"
        : CATEGORY_NAMES[selectedCategory] ?? "OTHER";

  const headingLabel =
    selectedCategory === null
      ? `▮ ALL ITEMS / ${visibleItems.length}`
      : `▮ ${activeCategoryName} / ${visibleItems.length} ITEMS`;

  if (loading) {
    return <div className="p-8 label">LOADING…</div>;
  }

  return (
    <div className="flex flex-col">
      {/* HEADER */}
      <header className="border-b border-border pb-4 mb-4">
        <div className="flex items-center justify-between gap-6 flex-wrap">
          <h1 className="font-mono uppercase tracking-wider text-lg flex items-center gap-2">
            <span className="text-amber">▮</span>
            <span className="text-text">TRACKED ITEMS</span>
          </h1>
          <div className="flex items-center gap-3 flex-wrap">
            <span className="flex items-baseline gap-1.5">
              <span className="label">TOTAL</span>
              <span className="font-mono text-sm text-amber">
                {stats?.total_items ?? items.length}
              </span>
            </span>
            <span className="text-text-dim font-mono">·</span>
            <span className="flex items-baseline gap-1.5">
              <span className="label">ACTIVE</span>
              <span className="font-mono text-sm text-amber">
                {stats?.enabled_items ?? items.filter((i) => i.is_enabled).length}
              </span>
            </span>
            <span className="text-text-dim font-mono">·</span>
            <span className="flex items-baseline gap-1.5">
              <span className="font-mono text-sm text-amber">
                ~{stats?.estimated_daily_calls ?? 0}
              </span>
              <span className="label">CLS/DAY</span>
            </span>
          </div>
        </div>
      </header>

      {/* BODY: rail + main */}
      <div className="flex gap-6">
        {/* LEFT RAIL */}
        <aside className="w-52 shrink-0 flex flex-col">
          <div className="label mb-3 px-2">CATEGORIES</div>
          <nav className="flex flex-col">
            {/* ALL row */}
            <button
              type="button"
              onClick={() => handleSelectCategory(null)}
              className={`flex items-center gap-3 px-3 py-2 text-sm transition-colors relative ${
                selectedCategory === null
                  ? "text-text bg-surface-2"
                  : "text-text-muted hover:text-text hover:bg-surface-2"
              }`}
            >
              {selectedCategory === null && (
                <span
                  aria-hidden="true"
                  className="absolute left-0 top-0 bottom-0 w-[3px] bg-amber"
                />
              )}
              <span
                aria-hidden="true"
                className={`font-mono text-xs ${
                  selectedCategory === null ? "text-amber" : "text-text-dim"
                }`}
              >
                ●
              </span>
              <span className="font-mono uppercase tracking-wider text-xs flex-1 text-left">
                ALL
              </span>
              <span
                className={`font-mono text-xs ${
                  selectedCategory === null ? "text-amber" : "text-text-dim"
                }`}
              >
                {items.length}
              </span>
            </button>

            {categoryRows.map((row) => {
              const isActive = selectedCategory === row.id;
              return (
                <button
                  key={row.id}
                  type="button"
                  onClick={() => handleSelectCategory(row.id)}
                  className={`flex items-center gap-3 px-3 py-2 text-sm transition-colors relative ${
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
                  <CategoryIcon
                    categoryId={row.id === "__OTHER__" ? null : row.id}
                    className={`w-4 h-4 ${
                      isActive ? "text-amber" : "text-text-dim"
                    }`}
                  />
                  <span className="font-mono uppercase tracking-wider text-xs flex-1 text-left">
                    {row.name}
                  </span>
                  <span
                    className={`font-mono text-xs ${
                      isActive ? "text-amber" : "text-text-dim"
                    }`}
                  >
                    {row.count}
                  </span>
                </button>
              );
            })}
          </nav>

          <div className="mt-3 pt-3 border-t border-border">
            <Link
              href="/items/add"
              className="flex items-center gap-2 px-3 py-2 font-mono uppercase tracking-wider text-xs text-text-muted hover:text-amber transition-colors"
            >
              <Plus className="w-4 h-4" />
              <span>ADD ITEM</span>
            </Link>
          </div>
        </aside>

        {/* MAIN */}
        <main className="flex-1 min-w-0 flex flex-col gap-4">
          <div>
            <h2 className="font-mono uppercase tracking-wider text-sm text-text">
              <span className="text-amber">▮</span>{" "}
              {headingLabel.replace(/^▮\s*/, "")}
            </h2>
            <div className="border-b border-border-strong mt-3" />
          </div>

          <div className="flex items-center justify-between gap-3 flex-wrap">
            <div className="relative flex-1 max-w-md">
              <Search
                className="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-text-dim"
                aria-hidden="true"
              />
              <input
                type="text"
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                placeholder="> search items..."
                className="w-full pl-9 pr-3 py-2 border border-border bg-surface-2 font-mono text-sm text-text placeholder:text-text-dim focus:border-amber focus:outline-none"
              />
            </div>

            <label className="flex items-center gap-2">
              <span className="label">SORT:</span>
              <select
                value={sortBy}
                onChange={(e) => handleSortChange(e.target.value as SortKey)}
                className="border border-border bg-surface-2 px-3 py-2 font-mono text-sm text-text focus:border-amber focus:outline-none uppercase tracking-wider"
              >
                {SORT_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </label>
          </div>

          {visibleItems.length === 0 ? (
            filter.trim() ? (
              <div className="border border-dashed border-border p-8 text-center font-mono text-sm text-text-muted">
                &gt; NO ITEMS MATCH SEARCH &quot;{filter}&quot;
              </div>
            ) : (
              <div className="border border-dashed border-border p-8 text-center label">
                NO ITEMS IN THIS CATEGORY
              </div>
            )
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 2xl:grid-cols-3 gap-3">
              {visibleItems.map((item) => (
                <ItemCard key={item.id} item={item} />
              ))}
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
