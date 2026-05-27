"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import { CATEGORY_NAMES, CategoryIcon } from "@/components/category-icon";
import { IntervalSlider } from "@/components/interval-slider";
import { ListingRow } from "@/components/listing-row";
import { SaveBar } from "@/components/save-bar";
import { TargetEditor } from "@/components/target-editor";
import { apiClient } from "@/lib/api";
import type { Deal, TrackedItem } from "@/lib/types";

type TabKey = "tracking" | "listings" | "history" | "notes";

const DIRTY_FIELDS: (keyof TrackedItem)[] = [
  "target_price",
  "alert_threshold",
  "scam_floor",
  "benchmark_median",
  "min_deal_score",
  "search_interval",
  "is_enabled",
  "notes",
];

async function fetchItem(id: number): Promise<TrackedItem> {
  const token =
    typeof window !== "undefined" ? localStorage.getItem("token") : null;
  const res = await fetch(
    `${process.env.NEXT_PUBLIC_API_URL || "/api"}/items/${id}`,
    {
      headers: { ...(token ? { Authorization: `Bearer ${token}` } : {}) },
    },
  );
  if (!res.ok) throw new Error(`Failed to load item ${id}`);
  return res.json();
}

function formatRelative(iso: string | null): string {
  if (!iso) return "NEVER";
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return "NEVER";
  const diff = Date.now() - then;
  if (diff < 0) return "JUST NOW";
  const s = Math.floor(diff / 1000);
  if (s < 60) return `${s}S AGO`;
  const m = Math.floor(s / 60);
  if (m < 60) return `${m}M AGO`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}H AGO`;
  const d = Math.floor(h / 24);
  return `${d}D AGO`;
}

function formatPrice(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  return `$${value.toLocaleString("en-US", { maximumFractionDigits: 0 })}`;
}

function formatIntervalShort(seconds: number): string {
  if (seconds < 60) return `${seconds}S`;
  const m = Math.round(seconds / 60);
  if (m < 60) return `${m}M`;
  const h = Math.round(m / 60);
  return `${h}H`;
}

interface PriorityMeta {
  label: string;
  className: string;
}

function getPriority(searchInterval: number): PriorityMeta {
  if (searchInterval <= 360) {
    return {
      label: "HOT",
      className: "chip border-l-2 border-l-red text-red",
    };
  }
  if (searchInterval <= 600) {
    return {
      label: "STD",
      className: "chip border-l-2 border-l-amber text-amber",
    };
  }
  if (searchInterval <= 1200) {
    return {
      label: "MON",
      className: "chip border-l-2 border-l-blue text-blue",
    };
  }
  return {
    label: "PSV",
    className: "chip text-text-dim",
  };
}

export default function ItemDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const idStr = Array.isArray(params?.id) ? params.id[0] : params?.id;
  const id = idStr ? Number(idStr) : NaN;

  const [original, setOriginal] = useState<TrackedItem | null>(null);
  const [form, setForm] = useState<TrackedItem | null>(null);
  const [deals, setDeals] = useState<Deal[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [tab, setTab] = useState<TabKey>("tracking");

  const reload = useCallback(async () => {
    if (Number.isNaN(id)) {
      setError("invalid id");
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const [item, dealsResp] = await Promise.all([
        fetchItem(id),
        apiClient
          .getDeals({ item_id: String(id), per_page: "10" })
          .catch(() => ({ deals: [], total: 0, page: 1, per_page: 10 })),
      ]);
      setOriginal(item);
      setForm(item);
      setDeals(dealsResp.deals || []);
    } catch (e) {
      setError(e instanceof Error ? e.message : "load failed");
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    reload();
  }, [reload]);

  const patch = useCallback((partial: Partial<TrackedItem>) => {
    setForm((prev) => (prev ? { ...prev, ...partial } : prev));
  }, []);

  const { dirty, dirtyCount, diff } = useMemo(() => {
    if (!original || !form) {
      return { dirty: false, dirtyCount: 0, diff: {} as Partial<TrackedItem> };
    }
    const d: Partial<TrackedItem> = {};
    let count = 0;
    for (const k of DIRTY_FIELDS) {
      if (original[k] !== form[k]) {
        // @ts-expect-error indexed assignment across heterogeneous fields is safe here
        d[k] = form[k];
        count += 1;
      }
    }
    return { dirty: count > 0, dirtyCount: count, diff: d };
  }, [original, form]);

  const save = useCallback(async () => {
    if (!form || Number.isNaN(id) || !dirty) return;
    setSaving(true);
    try {
      await apiClient.updateItem(id, diff);
      await reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : "save failed");
    } finally {
      setSaving(false);
    }
  }, [form, id, dirty, diff, reload]);

  const discard = useCallback(() => {
    setForm(original);
  }, [original]);

  const onDelete = useCallback(async () => {
    if (Number.isNaN(id)) return;
    if (
      !confirm(
        "Delete this tracked item? This will also remove its listings and scores.",
      )
    ) {
      return;
    }
    try {
      await apiClient.deleteItem(id);
      router.push("/items");
    } catch (e) {
      setError(e instanceof Error ? e.message : "delete failed");
    }
  }, [id, router]);

  if (loading) {
    return <div className="p-8 label">LOADING ITEM…</div>;
  }

  if (error || !form || !original) {
    return (
      <div className="p-8 flex flex-col gap-4">
        <div className="label text-red">
          ITEM #{Number.isNaN(id) ? "—" : id} NOT FOUND
        </div>
        <Link
          href="/items"
          className="label hover:text-amber transition-colors w-fit"
        >
          ‹ BACK TO ITEMS
        </Link>
      </div>
    );
  }

  const categoryName =
    (form.category_id && CATEGORY_NAMES[form.category_id]) || "OTHER";
  const identifier = form.mpn || form.sku || "—";
  const priority = getPriority(form.search_interval);
  const heroImage = deals[0]?.image_url || null;
  const bestPrice = deals[0]?.price ?? null;

  const targetVsMedianHelper = (() => {
    if (form.target_price == null || form.benchmark_median == null) return null;
    const pct =
      ((form.target_price - form.benchmark_median) / form.benchmark_median) *
      100;
    const sign = pct >= 0 ? "+" : "";
    return `${sign}${pct.toFixed(1)}% vs benchmark`;
  })();

  return (
    <div className="flex flex-col gap-6 p-6 max-w-7xl mx-auto">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 font-mono text-xs tracking-wider uppercase">
        <Link
          href="/items"
          className="text-text-muted hover:text-amber transition-colors"
        >
          ‹ ITEMS
        </Link>
        <span className="text-text-dim">/</span>
        <span className="text-text-muted">{categoryName}</span>
      </div>

      {/* Hero band */}
      <div className="border border-border bg-surface p-6 flex gap-6">
        <div className="w-48 h-32 shrink-0 bg-surface-2 border border-border flex items-center justify-center overflow-hidden">
          {heroImage ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={heroImage}
              alt=""
              className="w-full h-full object-cover"
            />
          ) : (
            <CategoryIcon
              categoryId={form.category_id}
              className="w-16 h-16 text-text-dim"
            />
          )}
        </div>

        <div className="flex-1 min-w-0 flex flex-col gap-2">
          <h1 className="text-2xl font-mono tracking-tight text-text leading-tight">
            {form.name}
          </h1>

          <p className="font-mono text-[11px] tracking-wider uppercase text-text-dim truncate">
            {identifier} · {categoryName} · LAST SEARCHED{" "}
            {formatRelative(form.last_searched)}
          </p>

          <div className="flex items-center gap-2 mt-1">
            <span className="flex items-center gap-1.5">
              <span
                className={form.is_enabled ? "dot-active" : "dot-paused"}
                aria-hidden="true"
              />
              <span
                className={`font-mono text-[10px] tracking-wider uppercase ${
                  form.is_enabled ? "text-green" : "text-text-dim"
                }`}
              >
                {form.is_enabled ? "ACT" : "PAU"}
              </span>
            </span>
            <span className={priority.className}>{priority.label}</span>
            <span className="chip">
              {formatIntervalShort(form.search_interval)}
            </span>
          </div>

          <div className="border-t border-border my-2" />

          <div className="grid grid-cols-4 gap-4">
            <div className="flex flex-col gap-1">
              <span className="label">TARGET</span>
              <span className="font-mono text-base text-amber">
                {formatPrice(form.target_price)}
              </span>
            </div>
            <div className="flex flex-col gap-1">
              <span className="label">BEST</span>
              <span className="font-mono text-base text-amber inline-flex items-baseline gap-1">
                {formatPrice(bestPrice)}
                {bestPrice != null &&
                  form.target_price != null &&
                  bestPrice < form.target_price && (
                    <span className="text-green text-xs">▼</span>
                  )}
              </span>
            </div>
            <div className="flex flex-col gap-1">
              <span className="label">MEDIAN</span>
              <span className="font-mono text-base text-text">
                {formatPrice(form.benchmark_median)}
              </span>
            </div>
            <div className="flex flex-col gap-1">
              <span className="label">FLOOR</span>
              <span className="font-mono text-base text-red-dim">
                {formatPrice(form.scam_floor)}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs bar */}
      <div className="mt-2 border-b border-border flex items-center gap-1">
        {(
          [
            { key: "tracking", label: "TRACKING" },
            { key: "listings", label: `LIVE LISTINGS (${deals.length})` },
            { key: "history", label: "HISTORY" },
            { key: "notes", label: "NOTES" },
          ] as { key: TabKey; label: string }[]
        ).map((t) => {
          const active = tab === t.key;
          return (
            <button
              key={t.key}
              type="button"
              onClick={() => setTab(t.key)}
              className={`font-mono text-xs tracking-wider uppercase px-4 py-2.5 border-b-2 transition-colors ${
                active
                  ? "border-amber text-text"
                  : "border-transparent text-text-muted hover:text-text"
              }`}
            >
              {t.label}
            </button>
          );
        })}
      </div>

      {/* Tab content */}
      {tab === "tracking" && (
        <>
          <div className="border border-border bg-surface p-6 flex flex-col gap-6 mt-4">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* PRICING TARGETS */}
              <div className="flex flex-col gap-4">
                <h2 className="label">PRICING TARGETS</h2>
                <div className="flex flex-col gap-4">
                  <TargetEditor
                    label="TARGET PRICE"
                    prefix="$"
                    value={form.target_price}
                    onChange={(v) => patch({ target_price: v })}
                    helper={targetVsMedianHelper}
                  />
                  <TargetEditor
                    label="ALERT THRESHOLD"
                    suffix="%"
                    value={
                      form.alert_threshold != null
                        ? Math.round(form.alert_threshold * 1000) / 10
                        : null
                    }
                    onChange={(v) =>
                      patch({
                        alert_threshold:
                          v != null ? v / 100 : (0 as unknown as number),
                      })
                    }
                    helper="alert when price drops below target × (1 - threshold)"
                  />
                  <TargetEditor
                    label="SCAM FLOOR"
                    prefix="$"
                    value={form.scam_floor}
                    onChange={(v) => patch({ scam_floor: v })}
                    helper="reject listings priced below this"
                  />
                  <TargetEditor
                    label="BENCHMARK MEDIAN"
                    prefix="$"
                    value={form.benchmark_median}
                    onChange={(v) => patch({ benchmark_median: v })}
                  />
                  <TargetEditor
                    label="MIN DEAL SCORE"
                    suffix="/100"
                    min={0}
                    max={100}
                    step={1}
                    value={form.min_deal_score}
                    onChange={(v) =>
                      patch({
                        min_deal_score: v != null ? Math.round(v) : 50,
                      })
                    }
                  />
                </div>
              </div>

              {/* POLLING & STATUS */}
              <div className="flex flex-col gap-4">
                <h2 className="label">POLLING &amp; STATUS</h2>

                <div className="flex flex-col gap-2">
                  <span className="label">SEARCH INTERVAL</span>
                  <IntervalSlider
                    value={form.search_interval}
                    onChange={(s) => patch({ search_interval: s })}
                  />
                </div>

                <div className="flex flex-col gap-2">
                  <span className="label">STATUS</span>
                  <div
                    className="grid grid-cols-2 gap-px border border-border bg-border"
                    role="radiogroup"
                    aria-label="Item status"
                  >
                    {(
                      [
                        { val: true, label: "ACTIVE" },
                        { val: false, label: "PAUSED" },
                      ] as { val: boolean; label: string }[]
                    ).map((opt) => {
                      const selected = form.is_enabled === opt.val;
                      return (
                        <button
                          key={String(opt.val)}
                          type="button"
                          role="radio"
                          aria-checked={selected}
                          onClick={() => patch({ is_enabled: opt.val })}
                          className={`flex items-center justify-center py-2 px-1 transition-colors duration-150 font-mono text-xs font-semibold tracking-wider ${
                            selected
                              ? "bg-amber text-bg"
                              : "bg-surface-2 text-text-muted hover:bg-surface-3 hover:text-text"
                          }`}
                        >
                          {opt.label}
                        </button>
                      );
                    })}
                  </div>
                </div>

                <div className="flex flex-col gap-2">
                  <span className="label">NOTES</span>
                  <textarea
                    value={form.notes ?? ""}
                    onChange={(e) =>
                      patch({
                        notes: e.target.value === "" ? null : e.target.value,
                      })
                    }
                    placeholder="catalog notes, search hints, scam patterns…"
                    className="w-full min-h-24 p-3 bg-surface-2 border border-border focus:border-amber focus:outline-none font-mono text-sm text-text placeholder:text-text-dim resize-y transition-colors"
                  />
                </div>

                <div className="border-t border-border mt-2 pt-4">
                  <button
                    type="button"
                    onClick={onDelete}
                    className="font-mono text-xs tracking-wider uppercase text-red hover:text-red-dim transition-colors"
                  >
                    DELETE THIS ITEM
                  </button>
                </div>
              </div>
            </div>
          </div>

          <SaveBar
            dirty={dirty}
            dirtyCount={dirtyCount}
            saving={saving}
            onSave={save}
            onDiscard={discard}
          />
        </>
      )}

      {tab === "listings" && (
        <div className="border border-border bg-surface p-6 flex flex-col gap-4 mt-4">
          <h2 className="label">TOP LISTINGS BY DEAL SCORE</h2>
          {deals.length === 0 ? (
            <div className="border border-dashed border-border p-8 text-center label">
              NO LISTINGS YET — POLLING WILL POPULATE SHORTLY
            </div>
          ) : (
            <div className="flex flex-col gap-2">
              {deals.map((d) => (
                <ListingRow key={d.id} deal={d} />
              ))}
            </div>
          )}
        </div>
      )}

      {tab === "history" && (
        <div className="border border-border bg-surface p-6 flex flex-col gap-4 mt-4">
          <div className="label">PRICE HISTORY 90D · COMING SOON</div>
          <div className="font-mono text-text-dim text-sm tracking-wider select-none">
            ___╱╲___╱╲╱╲___╱╲___╲╱___╱╲╱╲___╱╲___
          </div>
        </div>
      )}

      {tab === "notes" && (
        <div className="border border-border bg-surface p-6 flex flex-col gap-3 mt-4">
          <h2 className="label">CATALOG NOTES</h2>
          {form.notes && form.notes.trim() !== "" ? (
            <pre className="font-mono text-sm text-text whitespace-pre-wrap break-words">
              {form.notes}
            </pre>
          ) : (
            <div className="border border-dashed border-border p-8 text-center label">
              NO NOTES — ADD SOME IN THE TRACKING TAB
            </div>
          )}
        </div>
      )}
    </div>
  );
}
