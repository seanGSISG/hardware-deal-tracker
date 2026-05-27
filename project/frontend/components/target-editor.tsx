"use client";

import { useEffect, useState, type ReactNode } from "react";

interface TargetEditorProps {
  label: string;
  value: number | null;
  onChange: (v: number | null) => void;
  prefix?: string;
  suffix?: string;
  placeholder?: string;
  min?: number;
  max?: number;
  step?: number;
  helper?: ReactNode;
}

export function TargetEditor({
  label,
  value,
  onChange,
  prefix,
  suffix,
  placeholder,
  min,
  max,
  step,
  helper,
}: TargetEditorProps) {
  const [raw, setRaw] = useState<string>(value !== null ? String(value) : "");

  useEffect(() => {
    setRaw(value !== null ? String(value) : "");
  }, [value]);

  const handleChange = (next: string) => {
    setRaw(next);
    if (next.trim() === "") {
      onChange(null);
      return;
    }
    const parsed = Number(next);
    if (Number.isNaN(parsed) || !Number.isFinite(parsed)) {
      onChange(null);
      return;
    }
    onChange(parsed);
  };

  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex items-center justify-between gap-4">
        <span className="label">{label}</span>
        <div className="flex items-stretch border border-border bg-surface-2 focus-within:border-amber transition-colors">
          {prefix && (
            <span className="flex items-center px-2 font-mono text-sm text-text-dim border-r border-border">
              {prefix}
            </span>
          )}
          <input
            type="number"
            inputMode="decimal"
            value={raw}
            onChange={(e) => handleChange(e.target.value)}
            placeholder={placeholder}
            min={min}
            max={max}
            step={step}
            className="bg-transparent focus:outline-none px-3 py-2 font-mono text-text text-sm w-32 text-right"
          />
          {suffix && (
            <span className="flex items-center px-2 font-mono text-sm text-text-dim border-l border-border">
              {suffix}
            </span>
          )}
        </div>
      </div>
      {helper && (
        <div className="text-right text-[11px] font-mono text-text-dim">
          {helper}
        </div>
      )}
    </div>
  );
}
