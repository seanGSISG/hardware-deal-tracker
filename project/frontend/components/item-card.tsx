"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Check } from "lucide-react";
import type { TrackedItem } from "@/lib/types";
import { apiClient } from "@/lib/api";
import { formatPrice } from "@/lib/format";
import { CATEGORY_NAMES, CategoryIcon } from "./category-icon";

interface ItemCardProps {
  item: TrackedItem;
  // Selection mode (bulk actions on the items list). When `selectable` is true the
  // card no longer navigates to the detail page; clicking it toggles selection.
  selectable?: boolean;
  selected?: boolean;
  onToggleSelect?: (id: number) => void;
}

interface PriorityMeta {
  label: string;
  className: string;
}

function getPriority(searchInterval: number): PriorityMeta {
  if (searchInterval <= 360) {
    return {
      label: "HOT",
      className: "chip border-l-2 border-l-red text-red",
    };
  }
  if (searchInterval <= 600) {
    return {
      label: "STD",
      className: "chip border-l-2 border-l-amber text-amber",
    };
  }
  if (searchInterval <= 1200) {
    return {
      label: "MON",
      className: "chip border-l-2 border-l-blue text-blue",
    };
  }
  return {
    label: "PSV",
    className: "chip text-text-dim",
  };
}

export function ItemCard({
  item,
  selectable = false,
  selected = false,
  onToggleSelect,
}: ItemCardProps) {
  const priority = getPriority(item.search_interval);
  const categoryName =
    (item.category_id && CATEGORY_NAMES[item.category_id]) || "OTHER";
  const identifier = item.mpn || item.sku || "—";

  // Optimistic enable/disable toggle: flip immediately, revert + error toast on
  // failure. Auth via the session cookie through apiClient (ADR-002).
  const [enabled, setEnabled] = useState(item.is_enabled);
  const [toggling, setToggling] = useState(false);

  // Keep the local toggle in sync when the parent hands us a refreshed item
  // (e.g. after a bulk pause/resume re-fetches the list). Single-card toggles
  // don't change the parent prop, so this won't clobber their optimistic state.
  useEffect(() => {
    setEnabled(item.is_enabled);
  }, [item.is_enabled]);

  async function handleToggle(e: React.MouseEvent) {
    // The card is a Link (or a selection target); keep the toggle from
    // navigating or selecting.
    e.preventDefault();
    e.stopPropagation();
    if (toggling) return;
    const previous = enabled;
    const next = !previous;
    setEnabled(next); // optimistic
    setToggling(true);
    try {
      const res = await apiClient.toggleItem(item.id);
      setEnabled(res.is_enabled);
      toast.success(res.is_enabled ? "Item activated" : "Item paused");
    } catch (err) {
      setEnabled(previous); // revert
      toast.error(err instanceof Error ? err.message : "Failed to toggle item");
    } finally {
      setToggling(false);
    }
  }

  // Shared inner content — rendered identically whether the card is a navigation
  // Link or a selection target. In select mode a leading checkbox is prepended.
  const body = (
    <>
      {selectable && (
        <span
          aria-hidden="true"
          className={`shrink-0 self-center w-5 h-5 border flex items-center justify-center transition-colors ${
            selected
              ? "bg-amber border-amber text-bg"
              : "border-border-strong text-transparent"
          }`}
        >
          <Check className="w-3.5 h-3.5" strokeWidth={3} />
        </span>
      )}

      <div className="w-24 h-24 shrink-0 bg-surface-2 border border-border flex items-center justify-center">
        <CategoryIcon
          categoryId={item.category_id}
          className="w-10 h-10 text-text-dim"
        />
      </div>

      <div className="flex-1 min-w-0 flex flex-col gap-2">
        <h3 className="text-base font-medium text-text leading-tight line-clamp-2">
          {item.name}
        </h3>

        <p className="text-[11px] font-mono text-text-dim tracking-wider uppercase truncate">
          {identifier} · {categoryName}
        </p>

        <div className="flex items-center gap-4 mt-auto">
          <div className="flex items-baseline gap-1.5">
            <span className="label">TARGET</span>
            <span
              className={`font-mono text-sm ${
                item.target_price !== null ? "text-amber" : "text-text-dim"
              }`}
            >
              {formatPrice(item.target_price, 0)}
            </span>
          </div>
          <div className="flex items-baseline gap-1.5">
            <span className="label">FLOOR</span>
            <span
              className={`font-mono text-sm ${
                item.scam_floor !== null ? "text-red-dim" : "text-text-dim"
              }`}
            >
              {formatPrice(item.scam_floor, 0)}
            </span>
          </div>

          <div className="ml-auto flex items-center gap-2">
            <span className={priority.className}>{priority.label}</span>
            <button
              type="button"
              role="switch"
              aria-checked={enabled}
              aria-label={enabled ? "Pause item" : "Activate item"}
              onClick={handleToggle}
              disabled={toggling}
              className="flex items-center gap-1.5 disabled:opacity-50"
            >
              <span
                className={enabled ? "dot-active" : "dot-paused"}
                aria-hidden="true"
              />
              <span
                className={`font-mono text-[10px] tracking-wider uppercase ${
                  enabled ? "text-green" : "text-text-dim"
                }`}
              >
                {enabled ? "ACT" : "PAU"}
              </span>
            </button>
          </div>
        </div>
      </div>
    </>
  );

  // Selection mode: the card is a checkbox, not a link.
  if (selectable) {
    return (
      <div
        role="checkbox"
        aria-checked={selected}
        aria-label={`Select ${item.name}`}
        tabIndex={0}
        onClick={() => onToggleSelect?.(item.id)}
        onKeyDown={(e) => {
          if (e.key === " " || e.key === "Enter") {
            e.preventDefault();
            onToggleSelect?.(item.id);
          }
        }}
        className={`flex gap-4 p-4 border bg-surface cursor-pointer transition-colors duration-150 ${
          selected
            ? "border-amber bg-surface-2"
            : "border-border hover:bg-surface-2 hover:border-border-strong"
        }`}
      >
        {body}
      </div>
    );
  }

  return (
    <Link
      href={`/items/${item.id}`}
      className="flex gap-4 p-4 border border-border bg-surface hover:bg-surface-2 hover:border-border-strong transition-colors duration-150 group"
    >
      {body}
    </Link>
  );
}
