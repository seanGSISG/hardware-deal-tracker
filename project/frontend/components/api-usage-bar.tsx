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

  const barColor = budget.status === "critical" ? "bg-red-500" : budget.status === "warning" ? "bg-amber-500" : "bg-green-500";

  return (
    <div className="bg-white rounded-lg border px-4 py-2 shadow-sm min-w-[280px]">
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs font-medium text-slate-500">eBay API</span>
        <span className={`text-xs font-bold ${budget.status === "critical" ? "text-red-600" : budget.status === "warning" ? "text-amber-600" : "text-green-600"}`}>
          {budget.calls_today.toLocaleString()} / {budget.daily_limit.toLocaleString()} ({Math.round(budget.utilization_pct)}%)
        </span>
      </div>
      <div className="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden">
        <div className={`h-full rounded-full transition-all duration-500 ${barColor}`} style={{ width: `${Math.min(budget.utilization_pct, 100)}%` }} />
      </div>
    </div>
  );
}
