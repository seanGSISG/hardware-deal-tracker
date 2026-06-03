"use client";

import { Activity, AlertTriangle, Cpu, Database, Gauge } from "lucide-react";
import { StatsCard } from "./stats-card";

type Tone = "amber" | "green" | "blue" | "red" | "muted";

interface MetricSpec {
  key: string;
  title: string;
  tone: Tone;
  icon: React.ReactNode;
}

const METRIC_SPECS: MetricSpec[] = [
  {
    key: "hdt_poll_cycles_total",
    title: "Poll Cycles",
    tone: "blue",
    icon: <Activity className="w-5 h-5" strokeWidth={1.5} />,
  },
  {
    key: "hdt_listings_ingested_total",
    title: "Listings Ingested",
    tone: "amber",
    icon: <Database className="w-5 h-5" strokeWidth={1.5} />,
  },
  {
    key: "hdt_scoring_runs_total",
    title: "Scoring Runs",
    tone: "green",
    icon: <Cpu className="w-5 h-5" strokeWidth={1.5} />,
  },
  {
    key: "hdt_ebay_errors_total",
    title: "eBay Errors",
    tone: "red",
    icon: <AlertTriangle className="w-5 h-5" strokeWidth={1.5} />,
  },
  {
    key: "hdt_ebay_rate_limited_total",
    title: "Rate Limited",
    tone: "red",
    icon: <Gauge className="w-5 h-5" strokeWidth={1.5} />,
  },
];

function formatCount(v: number): string {
  return Number.isInteger(v) ? v.toLocaleString() : v.toFixed(2);
}

/**
 * Renders the key hdt_* Prometheus counters as StatsCards. When `metrics` is
 * null (e.g. /metrics unavailable/unparsable) it renders nothing so the
 * dashboard degrades gracefully.
 */
export function MetricsCards({ metrics }: { metrics: Record<string, number> | null }) {
  if (!metrics) return null;

  const cards = METRIC_SPECS.filter((spec) => spec.key in metrics);
  if (cards.length === 0) return null;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
      {cards.map((spec) => (
        <StatsCard
          key={spec.key}
          title={spec.title}
          value={formatCount(metrics[spec.key])}
          icon={spec.icon}
          tone={spec.tone}
        />
      ))}
    </div>
  );
}
