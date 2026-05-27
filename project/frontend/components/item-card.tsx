import Link from "next/link";
import type { TrackedItem } from "@/lib/types";
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

function formatPrice(value: number | null): string {
  if (value === null || value === undefined) return "—";
  return `$${value.toLocaleString("en-US", { maximumFractionDigits: 0 })}`;
}

export function ItemCard({ item }: ItemCardProps) {
  const priority = getPriority(item.search_interval);
  const categoryName =
    (item.category_id && CATEGORY_NAMES[item.category_id]) || "OTHER";
  const identifier = item.mpn || item.sku || "—";

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
              {formatPrice(item.target_price)}
            </span>
          </div>
          <div className="flex items-baseline gap-1.5">
            <span className="label">FLOOR</span>
            <span
              className={`font-mono text-sm ${
                item.scam_floor !== null ? "text-red-dim" : "text-text-dim"
              }`}
            >
              {formatPrice(item.scam_floor)}
            </span>
          </div>

          <div className="ml-auto flex items-center gap-2">
            <span className={priority.className}>{priority.label}</span>
            <span className="flex items-center gap-1.5">
              <span
                className={item.is_enabled ? "dot-active" : "dot-paused"}
                aria-hidden="true"
              />
              <span
                className={`font-mono text-[10px] tracking-wider uppercase ${
                  item.is_enabled ? "text-green" : "text-text-dim"
                }`}
              >
                {item.is_enabled ? "ACT" : "PAU"}
              </span>
            </span>
          </div>
        </div>
      </div>
    </Link>
  );
}
