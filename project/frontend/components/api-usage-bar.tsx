"use client";

import { useEffect, useState } from "react";
import { apiClient } from "@/lib/api";

interface BudgetStatus {
  calls_today: number;
  daily_limit: number;
  remaining: number;
  utilization_pct: number;
  status: "ok" | "warning" | "critical";
}

export function ApiUsageBar() {
  const [budget, setBudget] = useState<BudgetStatus | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const data = await apiClient.getBudget();
        setBudget(data);
      } catch {
        // silent fail
      }
    }
    load();
    const interval = setInterval(load, 30000);
    return () => clearInterval(interval);
  }, []);

  if (!budget) return null;

  const statusClass =
    budget.status === "critical"
      ? "text-red"
      : budget.status === "warning"
      ? "text-amber"
      : "text-green";
  const barClass =
    budget.status === "critical"
      ? "bg-red"
      : budget.status === "warning"
      ? "bg-amber"
      : "bg-green";

  return (
    <div className="border border-border bg-surface px-4 py-2 min-w-[300px]">
      <div className="flex items-center justify-between mb-2">
        <span className="label">ebay api</span>
        <span className={`font-mono text-xs ${statusClass}`}>
          {budget.calls_today.toLocaleString()} / {budget.daily_limit.toLocaleString()} (
          {Math.round(budget.utilization_pct)}%)
        </span>
      </div>
      <div className="w-full h-[3px] bg-surface-2 overflow-hidden">
        <div
          className={`h-full ${barClass} transition-all duration-500`}
          style={{ width: `${Math.min(budget.utilization_pct, 100)}%` }}
        />
      </div>
    </div>
  );
}
