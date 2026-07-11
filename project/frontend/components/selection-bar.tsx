"use client";

import { useEffect, useState } from "react";

interface SelectionBarProps {
  count: number;
  busy: boolean;
  onPause: () => void;
  onResume: () => void;
  onRemove: () => void;
  onClear: () => void;
}

// Floating action bar for bulk operations on selected items. Mirrors the
// sticky-bottom pattern of SaveBar. The Remove action is a two-click confirm
// (REMOVE -> CONFIRM REMOVE N) so a destructive bulk delete never fires on a
// single click; no native confirm() dialog.
export function SelectionBar({
  count,
  busy,
  onPause,
  onResume,
  onRemove,
  onClear,
}: SelectionBarProps) {
  const [confirming, setConfirming] = useState(false);

  // Reset the confirm state whenever the selection empties (e.g. after a
  // successful remove or a Clear) so it never lingers armed.
  useEffect(() => {
    if (count === 0) setConfirming(false);
  }, [count]);

  if (count === 0) return null;

  return (
    <div className="sticky bottom-0 z-10 flex items-center justify-between gap-4 px-4 py-3 border-t border-border-strong bg-surface-2 backdrop-blur">
      <div className="flex items-center gap-2">
        <span className="dot-active" aria-hidden="true" />
        <span className="label !text-text">{count} selected</span>
      </div>

      {confirming ? (
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => setConfirming(false)}
            disabled={busy}
            className="font-mono text-xs tracking-wider uppercase text-text-muted hover:text-text transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={onRemove}
            disabled={busy}
            className="bg-red text-bg hover:bg-red-dim px-4 py-1.5 font-mono text-sm font-semibold tracking-wider uppercase transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
          >
            {busy ? "Removing..." : `Confirm Remove ${count}`}
          </button>
        </div>
      ) : (
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={onPause}
            disabled={busy}
            className="font-mono text-xs tracking-wider uppercase text-text-muted hover:text-text transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Pause
          </button>
          <button
            type="button"
            onClick={onResume}
            disabled={busy}
            className="font-mono text-xs tracking-wider uppercase text-text-muted hover:text-text transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Resume
          </button>
          <button
            type="button"
            onClick={onClear}
            disabled={busy}
            className="font-mono text-xs tracking-wider uppercase text-text-muted hover:text-text transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Clear
          </button>
          <button
            type="button"
            onClick={() => setConfirming(true)}
            disabled={busy}
            className="bg-red text-bg hover:bg-red-dim px-4 py-1.5 font-mono text-sm font-semibold tracking-wider uppercase transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
          >
            Remove
          </button>
        </div>
      )}
    </div>
  );
}
