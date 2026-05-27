import { ReactNode } from "react";

type Tone = "amber" | "green" | "blue" | "red" | "muted";

interface StatsCardProps {
  title: string;
  value: string | number;
  icon: ReactNode;
  tone?: Tone;
}

const TONE_STYLES: Record<Tone, { border: string; text: string }> = {
  amber: { border: "border-l-amber", text: "text-amber" },
  green: { border: "border-l-green", text: "text-green" },
  blue: { border: "border-l-blue", text: "text-blue" },
  red: { border: "border-l-red", text: "text-red" },
  muted: { border: "border-l-border-strong", text: "text-text" },
};

export function StatsCard({ title, value, icon, tone = "muted" }: StatsCardProps) {
  const styles = TONE_STYLES[tone];
  return (
    <div className={`border border-border bg-surface p-5 border-l-2 ${styles.border}`}>
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <p className="label">{title}</p>
          <p className={`mt-2 font-mono text-2xl ${styles.text}`}>{value}</p>
        </div>
        <div className={`shrink-0 ${styles.text} opacity-80`}>{icon}</div>
      </div>
    </div>
  );
}
