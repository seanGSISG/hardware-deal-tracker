"use client";

import Link from "next/link";
import { useState } from "react";
import { toast } from "sonner";
import type { TrackedItem } from "@/lib/types";
import { apiClient } from "@/lib/api";
import { formatPrice } from "@/lib/format";
import { CATEGORY_NAMES, CategoryIcon } from "./category-icon";

interface ItemCardProps {
  item: TrackedItem;
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

export function ItemCard({ item }: ItemCardProps) {
  const priority = getPriority(item.search_interval);
  const categoryName =
    (item.category_id && CATEGORY_NAMES[item.category_id]) || "OTHER";
  const identifier = item.mpn || item.sku || "—";

  // Optimistic enable/disable toggle: flip immediately, revert + error toast on
  // failure. Auth via the session cookie through apiClient (ADR-002).
  const [enabled, setEnabled] = useState(item.is_enabled);
  const [toggling, setToggling] = useState(false);

  async function handleToggle(e: React.MouseEvent) {
    // The card is a Link; keep the toggle from navigating.
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

  return (
    <Link
      href={`/items/${item.id}`}
      className="flex gap-4 p-4 border border-border bg-surface hover:bg-surface-2 hover:border-border-strong transition-colors duration-150 group"
    >
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
    </Link>
  );
}
