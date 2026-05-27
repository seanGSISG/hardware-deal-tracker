import { ExternalLink, Package } from "lucide-react";
import type { Deal } from "@/lib/types";

interface ListingRowProps {
  deal: Deal;
}

function formatPrice(value: number): string {
  return `$${value.toLocaleString("en-US", {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  })}`;
}

function scoreClass(score: number): string {
  if (score >= 85) return "chip border-l-2 border-l-red text-red";
  if (score >= 70) return "chip border-l-2 border-l-amber text-amber";
  if (score >= 50) return "chip border-l-2 border-l-green text-green";
  return "chip text-text-dim";
}

export function ListingRow({ deal }: ListingRowProps) {
  const score = deal.score?.overall_score;

  return (
    <div className="flex items-center gap-3 p-3 border border-border bg-surface hover:bg-surface-2 transition-colors">
      <div className="w-10 h-10 shrink-0 border border-border bg-surface-2 flex items-center justify-center overflow-hidden">
        {deal.image_url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={deal.image_url}
            alt=""
            loading="lazy"
            className="w-full h-full object-cover"
          />
        ) : (
          <Package
            className="w-5 h-5 text-text-dim"
            strokeWidth={1.5}
            aria-hidden="true"
          />
        )}
      </div>

      <div className="flex-1 min-w-0">
        <p className="text-sm text-text truncate">{deal.title}</p>
        <p className="text-[11px] font-mono text-text-dim tracking-wider uppercase truncate">
          {deal.seller || "—"}
          {deal.seller_feedback ? ` · ${deal.seller_feedback}` : ""}
        </p>
      </div>

      <div className="shrink-0 font-mono text-sm text-amber">
        {formatPrice(deal.price)}
      </div>

      {deal.condition && (
        <span className="chip shrink-0">{deal.condition}</span>
      )}

      {typeof score === "number" && (
        <span className={`${scoreClass(score)} shrink-0`}>
          {Math.round(score)}
        </span>
      )}

      <a
        href={deal.url}
        target="_blank"
        rel="noopener noreferrer"
        className="shrink-0 p-1.5 text-text-dim hover:text-amber transition-colors"
        aria-label="Open listing"
      >
        <ExternalLink className="w-4 h-4" strokeWidth={1.5} />
      </a>
    </div>
  );
}
