"use client";

import { useEffect, useState } from "react";
import { apiClient } from "@/lib/api";
import type { CommunityLead } from "@/lib/api";

const STATUS_STYLES: Record<string, string> = {
  "for-sale": "bg-green-100 text-green-700",
  unknown: "bg-slate-100 text-slate-600",
};

export default function CommunityPage() {
  const [leads, setLeads] = useState<CommunityLead[]>([]);
  const [enabled, setEnabled] = useState(true);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiClient
      .getCommunityLeads()
      .then((res) => {
        setEnabled(res.enabled);
        setLeads(res.leads || []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-8 text-center text-slate-500">Loading community leads...</div>;

  return (
    <div className="max-w-7xl mx-auto space-y-4">
      <div className="flex items-center gap-3">
        <h1 className="text-2xl font-bold text-slate-800">Community</h1>
        <span className="text-[10px] font-mono font-bold tracking-wider uppercase px-2 py-1 rounded bg-amber-100 text-amber-800 border border-amber-300">
          Community
        </span>
      </div>
      <p className="text-sm text-slate-500">
        Peer-to-peer leads from r/homelabsales — AI-extracted, not scored. Separate from eBay deal listings.
      </p>

      {!enabled ? (
        <div className="bg-white rounded-xl border p-8 text-center text-slate-400">
          <p>Community-signal ingestion is disabled.</p>
          <p className="text-xs mt-1">Set ENABLE_COMMUNITY_SIGNAL=true and configure Reddit creds to enable.</p>
        </div>
      ) : leads.length === 0 ? (
        <div className="bg-white rounded-xl border p-8 text-center text-slate-400">
          <p>No community leads yet.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {leads.map((lead) => (
            <div key={lead.id} className="bg-white rounded-xl border p-4 hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between mb-2">
                <span className="text-[10px] font-mono font-bold tracking-wider uppercase px-2 py-0.5 rounded bg-amber-100 text-amber-800 border border-amber-300">
                  Community
                </span>
                <span
                  className={`text-[10px] font-medium px-2 py-0.5 rounded ${
                    STATUS_STYLES[lead.status] || "bg-slate-100 text-slate-600"
                  }`}
                >
                  {lead.status}
                </span>
              </div>
              <p className="font-medium text-sm line-clamp-2 mb-2">{lead.title}</p>
              <div className="space-y-1 text-xs text-slate-600">
                {lead.model && (
                  <p>
                    <span className="text-slate-400">Model:</span> {lead.model}
                  </p>
                )}
                {lead.price != null && (
                  <p className="text-lg font-bold text-slate-800">${lead.price}</p>
                )}
                {lead.condition && (
                  <p>
                    <span className="text-slate-400">Condition:</span> {lead.condition}
                  </p>
                )}
                {lead.location && (
                  <p>
                    <span className="text-slate-400">Location:</span> {lead.location}
                  </p>
                )}
                {lead.catalog_item_id != null && (
                  <p className="text-indigo-600">Matched tracked item #{lead.catalog_item_id}</p>
                )}
              </div>
              <a
                href={lead.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-indigo-600 hover:underline mt-2 inline-block"
              >
                View post
              </a>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
