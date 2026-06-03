"use client";

import { useEffect, useState } from "react";
import {
  Line,
  ComposedChart,
  ReferenceArea,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { apiClient } from "@/lib/api";
import { TrendChip } from "./trend-chip";

type Point = { timestamp: string; total_price: number };

type Baseline = NonNullable<
  Awaited<ReturnType<typeof apiClient.getPriceHistory>>["baseline"]
>;

/**
 * Price-vs-time trend for a tracked item (feature-006), with the catalog
 * benchmark drawn as a reference line and, when available, the sold-comps
 * baseline median line + IQR (q1..q3) band, a vs-median delta, and a TREND chip
 * (feature-001 baseline block). Everything degrades gracefully: when the
 * baseline block is null/insufficient, falls back to points + benchmark line.
 */
export function PriceTrendChart({ itemId, days = 90 }: { itemId: number; days?: number }) {
  const [points, setPoints] = useState<Point[]>([]);
  const [benchmark, setBenchmark] = useState<number | null>(null);
  const [median, setMedian] = useState<number | null>(null);
  const [vsMedian, setVsMedian] = useState<number | null>(null);
  const [baseline, setBaseline] = useState<Baseline | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await apiClient.getPriceHistory(itemId, days);
        if (cancelled) return;
        setPoints(res.points.map((p) => ({ timestamp: p.timestamp, total_price: p.total_price })));
        setBenchmark(res.benchmark_median);
        setMedian(res.median_total);
        setVsMedian(res.vs_median_pct);
        setBaseline(res.baseline ?? null);
      } catch {
        // Non-fatal: the chart simply renders its empty state.
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [itemId, days]);

  if (loading) return <div className="label p-4">LOADING PRICE HISTORY…</div>;

  if (points.length === 0) {
    return (
      <div className="border border-dashed border-border p-6 text-center label">
        NO PRICE HISTORY YET
      </div>
    );
  }

  const data = points.map((p) => ({
    t: new Date(p.timestamp).toLocaleDateString(),
    total: p.total_price,
  }));

  // Prefer the baseline median for the headline delta when present; fall back to
  // the response-level median_total / vs_median_pct.
  const headlineMedian = baseline?.median ?? median;
  const headlineVsMedian = baseline?.vs_median_pct ?? vsMedian;

  const hasIqrBand =
    baseline != null &&
    typeof baseline.q1 === "number" &&
    typeof baseline.q3 === "number";
  const baselineMedianLine =
    baseline != null && typeof baseline.median === "number" ? baseline.median : null;

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center gap-4 flex-wrap">
        <span className="label">PRICE TREND / {days}D</span>
        {headlineMedian !== null && (
          <span className="font-mono text-xs text-text-dim">
            MEDIAN ${headlineMedian.toFixed(2)}
          </span>
        )}
        {headlineVsMedian !== null && (
          <span
            className={`font-mono text-xs ${headlineVsMedian > 0 ? "text-green" : "text-amber"}`}
          >
            {headlineVsMedian > 0 ? "▼" : "▲"} {Math.abs(headlineVsMedian * 100).toFixed(1)}% vs median
          </span>
        )}
        {baseline && (
          <TrendChip
            direction={baseline.trend_direction}
            slopePct={baseline.trend_slope_pct}
          />
        )}
        {hasIqrBand && (
          <span className="font-mono text-[11px] text-text-dim tracking-wider uppercase">
            IQR ${baseline!.q1!.toFixed(0)}–${baseline!.q3!.toFixed(0)}
          </span>
        )}
      </div>
      <ResponsiveContainer width="100%" height={220}>
        <ComposedChart data={data} margin={{ top: 8, right: 16, bottom: 0, left: 0 }}>
          <XAxis dataKey="t" tick={{ fontSize: 11 }} stroke="currentColor" />
          <YAxis tick={{ fontSize: 11 }} stroke="currentColor" domain={["auto", "auto"]} />
          <Tooltip
            formatter={(v: number) => [`$${v.toFixed(2)}`, "Total"]}
            contentStyle={{ fontSize: 12 }}
          />
          {/* IQR band (q1..q3) drawn as a translucent horizontal reference area. */}
          {hasIqrBand && (
            <ReferenceArea
              y1={baseline!.q1!}
              y2={baseline!.q3!}
              fill="#FFB534"
              fillOpacity={0.08}
              stroke="none"
              ifOverflow="extendDomain"
              label={{ value: "IQR", fontSize: 10, position: "insideTopLeft", fill: "#7E8895" }}
            />
          )}
          {/* Sold-comps baseline median line. */}
          {baselineMedianLine !== null && (
            <ReferenceLine
              y={baselineMedianLine}
              stroke="#00E5A0"
              strokeDasharray="2 2"
              label={{ value: "median", fontSize: 10, position: "insideBottomRight", fill: "#00E5A0" }}
            />
          )}
          {benchmark !== null && (
            <ReferenceLine
              y={benchmark}
              stroke="#FFB534"
              strokeDasharray="4 4"
              label={{ value: "benchmark", fontSize: 10, position: "insideTopRight", fill: "#FFB534" }}
            />
          )}
          <Line
            type="monotone"
            dataKey="total"
            stroke="#5BA3F5"
            strokeWidth={2}
            dot={false}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
