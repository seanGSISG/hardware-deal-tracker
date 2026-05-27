"use client";

interface SaveBarProps {
  dirty: boolean;
  dirtyCount: number;
  saving: boolean;
  onSave: () => void;
  onDiscard: () => void;
}

export function SaveBar({
  dirty,
  dirtyCount,
  saving,
  onSave,
  onDiscard,
}: SaveBarProps) {
  if (!dirty) return null;

  return (
    <div className="sticky bottom-0 z-10 flex items-center justify-between gap-4 px-4 py-3 border-t border-border-strong bg-surface-2 backdrop-blur">
      <div className="flex items-center gap-2">
        <span className="dot-active" aria-hidden="true" />
        <span className="label !text-text">
          {dirtyCount} unsaved {dirtyCount === 1 ? "change" : "changes"}
        </span>
      </div>

      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={onDiscard}
          disabled={saving}
          className="font-mono text-xs tracking-wider uppercase text-text-muted hover:text-red transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Discard
        </button>
        <button
          type="button"
          onClick={onSave}
          disabled={saving}
          className="bg-amber text-bg hover:bg-amber-dim px-4 py-1.5 font-mono text-sm font-semibold tracking-wider uppercase transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
        >
          {saving ? "Saving..." : "Save"}
        </button>
      </div>
    </div>
  );
}
