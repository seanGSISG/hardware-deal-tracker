"use client";

import { useEffect, useState } from "react";
import { Sparkles, AlertTriangle } from "lucide-react";
import { apiClient } from "@/lib/api";
import { SpecTable, type SpecRow } from "./spec-table";
import type { AiAnalysis } from "@/lib/types";

interface AiAnalysisPanelProps {
  listingId: number;
}

function gradeClass(grade: string): string {
  const g = grade.trim().toUpperCase();
  if (g.startsWith("A")) return "border-l-2 border-l-green text-green";
  if (g.startsWith("B")) return "border-l-2 border-l-amber text-amber";
  if (g.startsWith("C")) return "border-l-2 border-l-blue text-blue";
  return "border-l-2 border-l-red text-red";
}

function specRows(specs: Record<string, unknown> | null): SpecRow[] {
  if (!specs) return [];
  return Object.entries(specs).map(([key, value]) => ({
    label: key.replace(/[_-]+/g, " ").toUpperCase(),
    value:
      value === null || value === undefined
        ? "—"
        : typeof value === "object"
          ? JSON.stringify(value)
          : String(value),
  }));
}

/**
 * AI ANALYSIS panel for a listing (feature-006). Reads GET /api/v1/ai/{id}.
 * When { analysis: null } (no analysis / AI disabled) it renders a quiet
 * unavailable note — never an error/crash (graceful degradation).
 */
export function AiAnalysisPanel({ listingId }: AiAnalysisPanelProps) {
  const [analysis, setAnalysis] = useState<AiAnalysis | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    (async () => {
      try {
        const res = await apiClient.getListingAnalysis(listingId);
        if (!cancelled) setAnalysis(res.analysis ?? null);
      } catch {
        // AI is optional: any failure is treated as "no analysis", never an error.
        if (!cancelled) setAnalysis(null);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [listingId]);

  if (loading) {
    return <div className="label p-4">LOADING AI ANALYSIS…</div>;
  }

  if (!analysis) {
    return (
      <div className="border border-dashed border-border p-6 text-center label">
        AI ANALYSIS UNAVAILABLE
      </div>
    );
  }

  const rows = specRows(analysis.extracted_specs);

  return (
    <div className="border border-border bg-surface p-5 flex flex-col gap-4">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <h3 className="flex items-center gap-2 label !text-text">
          <Sparkles className="w-4 h-4 text-amber" strokeWidth={1.5} aria-hidden="true" />
          AI ANALYSIS
        </h3>
        <div className="flex items-center gap-2">
          {analysis.deal_grade && (
            <span className={`chip ${gradeClass(analysis.deal_grade)}`}>
              GRADE {analysis.deal_grade.toUpperCase()}
            </span>
          )}
          {analysis.scam_signal && (
            <span className="chip border-l-2 border-l-red text-red inline-flex items-center gap-1">
              <AlertTriangle className="w-3 h-3" strokeWidth={2} aria-hidden="true" />
              SCAM SIGNAL
            </span>
          )}
        </div>
      </div>

      {analysis.reasoning && (
        <p className="font-mono text-sm text-text leading-relaxed whitespace-pre-wrap break-words">
          {analysis.reasoning}
        </p>
      )}

      {analysis.scam_signal &&
        analysis.scam_reasons &&
        analysis.scam_reasons.length > 0 && (
          <div className="flex flex-col gap-1">
            <span className="label text-red">SCAM REASONS</span>
            <ul className="list-disc list-inside font-mono text-xs text-red-dim space-y-0.5">
              {analysis.scam_reasons.map((reason, i) => (
                <li key={i}>{reason}</li>
              ))}
            </ul>
          </div>
        )}

      {rows.length > 0 && (
        <div className="flex flex-col gap-2">
          <span className="label">EXTRACTED SPECS</span>
          <SpecTable rows={rows} />
        </div>
      )}

      <p className="font-mono text-[10px] text-text-dim tracking-wider uppercase">
        {analysis.provider}
        {analysis.model ? ` · ${analysis.model}` : ""}
        {analysis.created_at
          ? ` · ${new Date(analysis.created_at).toLocaleString()}`
          : ""}
      </p>
    </div>
  );
}
