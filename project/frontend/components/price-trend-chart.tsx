"use client";

import { useEffect, useState } from "react";
import {
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { apiClient } from "@/lib/api";

type Point = { timestamp: string; total_price: number };

/**
 * Price-vs-time trend for a tracked item (feature-006), with the catalog
 * benchmark drawn as a reference line so a user can judge whether the current
 * price is good historically.
 */
export function PriceTrendChart({ itemId, days = 90 }: { itemId: number; days?: number }) {
  const [points, setPoints] = useState<Point[]>([]);
  const [benchmark, setBenchmark] = useState<number | null>(null);
  const [median, setMedian] = useState<number | null>(null);
  const [vsMedian, setVsMedian] = useState<number | null>(null);
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

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center gap-4 flex-wrap">
        <span className="label">PRICE TREND / {days}D</span>
        {median !== null && (
          <span className="font-mono text-xs text-text-dim">
            MEDIAN ${median.toFixed(2)}
          </span>
        )}
        {vsMedian !== null && (
          <span
            className={`font-mono text-xs ${vsMedian > 0 ? "text-green-500" : "text-amber"}`}
          >
            {vsMedian > 0 ? "▼" : "▲"} {Math.abs(vsMedian * 100).toFixed(1)}% vs median
          </span>
        )}
      </div>
      <ResponsiveContainer width="100%" height={220}>
        <LineChart data={data} margin={{ top: 8, right: 16, bottom: 0, left: 0 }}>
          <XAxis dataKey="t" tick={{ fontSize: 11 }} stroke="currentColor" />
          <YAxis tick={{ fontSize: 11 }} stroke="currentColor" domain={["auto", "auto"]} />
          <Tooltip
            formatter={(v: number) => [`$${v.toFixed(2)}`, "Total"]}
            contentStyle={{ fontSize: 12 }}
          />
          {benchmark !== null && (
            <ReferenceLine
              y={benchmark}
              stroke="#f39c12"
              strokeDasharray="4 4"
              label={{ value: "benchmark", fontSize: 10, position: "insideTopRight" }}
            />
          )}
          <Line
            type="monotone"
            dataKey="total"
            stroke="#667eea"
            strokeWidth={2}
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
