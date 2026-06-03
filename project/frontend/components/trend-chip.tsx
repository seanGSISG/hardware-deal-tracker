import { Minus, TrendingDown, TrendingUp } from "lucide-react";

interface TrendChipProps {
  /** baseline.trend_direction: 'rising' | 'falling' | 'stable' (or unknown). */
  direction?: string | null;
  /** baseline.trend_slope_pct — optional helper magnitude. */
  slopePct?: number | null;
}

/**
 * TREND chip derived from the sold-comps baseline trend_direction, in the
 * amber/mono chip style. Renders nothing when no direction is available.
 */
export function TrendChip({ direction, slopePct }: TrendChipProps) {
  if (!direction) return null;
  const dir = direction.toLowerCase();

  let className = "text-text-dim";
  let label = dir.toUpperCase();
  let Icon = Minus;

  if (dir === "rising") {
    className = "border-l-2 border-l-red text-red";
    label = "RISING";
    Icon = TrendingUp;
  } else if (dir === "falling") {
    className = "border-l-2 border-l-green text-green";
    label = "FALLING";
    Icon = TrendingDown;
  } else if (dir === "stable") {
    className = "border-l-2 border-l-blue text-blue";
    label = "STABLE";
    Icon = Minus;
  }

  const slope =
    typeof slopePct === "number" && Number.isFinite(slopePct)
      ? ` ${slopePct > 0 ? "+" : ""}${slopePct.toFixed(1)}%`
      : "";

  return (
    <span className={`chip inline-flex items-center gap-1 ${className}`} title={`Trend: ${label}${slope}`}>
      <Icon className="w-3 h-3" strokeWidth={2} aria-hidden="true" />
      TREND {label}
      {slope && <span className="text-text-dim">{slope}</span>}
    </span>
  );
}
