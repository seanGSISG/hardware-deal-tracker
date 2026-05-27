"use client";

interface IntervalSliderProps {
  value: number;
  onChange: (seconds: number) => void;
}

interface Tier {
  seconds: number;
  label: string;
  dailyCalls: number;
}

const TIERS: Tier[] = [
  { seconds: 300, label: "P0 5M", dailyCalls: 288 },
  { seconds: 600, label: "P1 10M", dailyCalls: 144 },
  { seconds: 1200, label: "P2 20M", dailyCalls: 72 },
  { seconds: 1800, label: "P3 30M", dailyCalls: 48 },
];

export function IntervalSlider({ value, onChange }: IntervalSliderProps) {
  return (
    <div
      className="grid grid-cols-4 gap-px border border-border bg-border"
      role="radiogroup"
      aria-label="Polling interval"
    >
      {TIERS.map((tier) => {
        const selected = value === tier.seconds;
        return (
          <button
            key={tier.seconds}
            type="button"
            role="radio"
            aria-checked={selected}
            onClick={() => onChange(tier.seconds)}
            className={`flex flex-col items-center justify-center py-2 px-1 transition-colors duration-150 ${
              selected
                ? "bg-amber text-bg"
                : "bg-surface-2 text-text-muted hover:bg-surface-3 hover:text-text"
            }`}
          >
            <span className="font-mono text-xs font-semibold tracking-wider">
              {tier.label}
            </span>
            <span
              className={`font-mono text-[10px] tracking-wider mt-0.5 ${
                selected ? "text-bg/80" : "text-text-dim"
              }`}
            >
              ≈{tier.dailyCalls} cls/d
            </span>
          </button>
        );
      })}
    </div>
  );
}
