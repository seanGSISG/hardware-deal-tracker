import type { ListingSource } from "@/lib/types";

interface SourceBadgeProps {
  source?: ListingSource | null;
}

interface SourceMeta {
  label: string;
  /** Extra classes layered on top of the base `chip` token. */
  className: string;
}

/**
 * Maps a per-listing origin `source` to a short SOURCE badge in the amber/mono
 * chip style. Unknown / missing sources degrade to a neutral chip.
 */
function sourceMeta(source?: ListingSource | null): SourceMeta {
  switch ((source ?? "").toLowerCase()) {
    case "ebay":
      return { label: "EBAY", className: "border-l-2 border-l-blue text-blue" };
    case "shopify":
      return { label: "SHOPIFY", className: "border-l-2 border-l-green text-green" };
    case "pcpartpicker":
      return { label: "PCPP", className: "border-l-2 border-l-amber text-amber" };
    default:
      return { label: source ? source.toUpperCase() : "UNKNOWN", className: "text-text-dim" };
  }
}

export function SourceBadge({ source }: SourceBadgeProps) {
  const meta = sourceMeta(source);
  return (
    <span className={`chip shrink-0 ${meta.className}`} title={`Source: ${meta.label}`}>
      {meta.label}
    </span>
  );
}
