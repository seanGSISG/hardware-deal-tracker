"use client";

import { useEffect, useState } from "react";
import { apiClient } from "@/lib/api";
import type { Deal } from "@/lib/types";

export default function DealsPage() {
  const [deals, setDeals] = useState<Deal[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiClient.getDeals({ min_score: "1" }).then(d => { setDeals(d.deals || []); setLoading(false); }).catch(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-8 text-center text-text-muted">Loading deals...</div>;

  return (
    <div className="max-w-7xl mx-auto space-y-4">
      <h1 className="text-2xl font-bold text-text">Deals</h1>
      {deals.length === 0 ? (
        <div className="bg-surface rounded-xl border border-border p-8 text-center text-text-muted">
          <p>No deals found yet. Run a search to score listings.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {deals.map((deal, i) => (
            <div key={i} className="bg-surface rounded-xl border border-border p-4 hover:shadow-md transition-shadow">
              <div className="flex items-center gap-3 mb-3">
                <span className={`w-12 h-12 rounded-full flex items-center justify-center text-white font-bold ${(deal.score?.overall_score || 0) >= 70 ? "bg-red-500" : (deal.score?.overall_score || 0) >= 50 ? "bg-green-500" : "bg-slate-400"}`}>
                  {deal.score?.overall_score || 0}
                </span>
                <div>
                  <p className="font-medium text-sm line-clamp-2">
                    {deal.is_china && (
                      <span title={`Ships from ${deal.item_country || "China"}`} className="mr-1">🇨🇳</span>
                    )}
                    {deal.title}
                  </p>
                  <p className="text-xs text-text-muted">{deal.score?.classification || "unknown"}</p>
                </div>
              </div>
              <p className="text-lg font-bold text-text">${deal.price}</p>
              <p className="text-xs text-text-muted">{deal.seller}</p>
              <a href={deal.url} target="_blank" rel="noopener noreferrer" className="text-xs text-blue hover:underline mt-2 inline-block">View on eBay</a>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
