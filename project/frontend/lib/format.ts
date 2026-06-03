/**
 * Shared formatting helpers (feature-005, story-7). Extracted to de-duplicate
 * the per-component formatPrice implementations introduced while surfacing
 * listings/history/settings. Pure functions, no side effects.
 */

/**
 * Formats a numeric USD amount. `null`/`undefined` render as an em dash.
 * `maxFractionDigits` defaults to 2 (cents shown only when present); pass 0 for
 * whole-dollar display.
 */
export function formatPrice(
  value: number | null | undefined,
  maxFractionDigits = 2,
): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return `$${value.toLocaleString("en-US", {
    minimumFractionDigits: 0,
    maximumFractionDigits: maxFractionDigits,
  })}`;
}
