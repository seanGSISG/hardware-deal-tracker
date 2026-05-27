import type { ReactNode } from "react";

export interface SpecRow {
  label: string;
  value: ReactNode;
}

interface SpecTableProps {
  rows: SpecRow[];
}

export function SpecTable({ rows }: SpecTableProps) {
  return (
    <dl className="divide-y divide-border border-y border-border">
      {rows.map((row, idx) => (
        <div
          key={`${row.label}-${idx}`}
          className="flex items-start gap-4 py-2.5"
        >
          <dt className="label w-24 shrink-0 pt-0.5">{row.label}</dt>
          <dd className="font-mono text-sm text-text break-words min-w-0 flex-1">
            {row.value}
          </dd>
        </div>
      ))}
    </dl>
  );
}
