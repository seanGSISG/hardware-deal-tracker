"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { toast } from "sonner";

import { SaveBar } from "@/components/save-bar";
import { TargetEditor } from "@/components/target-editor";
import { apiClient } from "@/lib/api";
import type { NotificationSettings } from "@/lib/types";

type DraftSettings = Pick<
  NotificationSettings,
  | "telegram_chat_id"
  | "telegram_enabled"
  | "email_address"
  | "email_enabled"
  | "email_digest_mode"
  | "telegram_min_score"
  | "email_min_score"
  | "ntfy_enabled"
  | "ntfy_topic"
  | "ntfy_min_score"
  | "mute_until"
>;

const DIGEST_MODES: Array<{ value: string; label: string }> = [
  { value: "instant", label: "INSTANT" },
  { value: "daily", label: "DAILY" },
];

function clampScore(v: number | null): number {
  if (v === null || Number.isNaN(v)) return 0;
  return Math.max(0, Math.min(100, Math.round(v)));
}

function toDraft(s: NotificationSettings): DraftSettings {
  return {
    telegram_chat_id: s.telegram_chat_id,
    telegram_enabled: s.telegram_enabled,
    email_address: s.email_address,
    email_enabled: s.email_enabled,
    email_digest_mode: s.email_digest_mode,
    telegram_min_score: s.telegram_min_score,
    email_min_score: s.email_min_score,
    ntfy_enabled: s.ntfy_enabled,
    ntfy_topic: s.ntfy_topic,
    ntfy_min_score: s.ntfy_min_score,
    mute_until: s.mute_until,
  };
}

/** Converts an ISO datetime to the value a datetime-local input expects. */
function isoToLocalInput(iso: string | null): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  const off = d.getTimezoneOffset();
  const local = new Date(d.getTime() - off * 60000);
  return local.toISOString().slice(0, 16);
}

function localInputToIso(value: string): string | null {
  if (!value) return null;
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return null;
  return d.toISOString();
}

export default function SettingsPage() {
  const [original, setOriginal] = useState<DraftSettings | null>(null);
  const [draft, setDraft] = useState<DraftSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const s = await apiClient.getNotificationSettings();
      const d = toDraft(s);
      setOriginal(d);
      setDraft(d);
    } catch (e) {
      setError(e instanceof Error ? e.message : "failed to load settings");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const patch = useCallback((partial: Partial<DraftSettings>) => {
    setDraft((prev) => (prev ? { ...prev, ...partial } : prev));
  }, []);

  const { dirty, dirtyCount } = useMemo(() => {
    if (!original || !draft) return { dirty: false, dirtyCount: 0 };
    let count = 0;
    (Object.keys(original) as (keyof DraftSettings)[]).forEach((k) => {
      if (original[k] !== draft[k]) count += 1;
    });
    return { dirty: count > 0, dirtyCount: count };
  }, [original, draft]);

  const save = useCallback(async () => {
    if (!draft || !dirty) return;
    const prev = original;
    setSaving(true);
    // Optimistic: treat the draft as the new baseline immediately.
    setOriginal(draft);
    try {
      const payload: DraftSettings = {
        ...draft,
        telegram_min_score: clampScore(draft.telegram_min_score),
        email_min_score: clampScore(draft.email_min_score),
        ntfy_min_score: clampScore(draft.ntfy_min_score),
      };
      const updated = await apiClient.updateNotificationSettings(payload);
      const fresh = toDraft(updated);
      setOriginal(fresh);
      setDraft(fresh);
      toast.success("Settings saved");
    } catch (e) {
      // Revert optimistic baseline + restore the user's edits as still-dirty.
      if (prev) setOriginal(prev);
      toast.error(e instanceof Error ? e.message : "Failed to save settings");
    } finally {
      setSaving(false);
    }
  }, [draft, dirty, original]);

  const discard = useCallback(() => {
    setDraft(original);
  }, [original]);

  if (loading) {
    return <div className="p-8 label">LOADING SETTINGS…</div>;
  }

  if (error || !draft) {
    return (
      <div className="p-8 flex flex-col gap-4">
        <div className="label text-red">FAILED TO LOAD SETTINGS</div>
        <button
          type="button"
          onClick={load}
          className="label hover:text-amber transition-colors w-fit"
        >
          ‹ RETRY
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6 p-6 max-w-3xl mx-auto">
      <header className="border-b border-border pb-4">
        <h1 className="flex items-center gap-2 font-mono text-xl tracking-[0.18em] uppercase text-text">
          <span className="text-amber">▮</span>
          SETTINGS
        </h1>
        <p className="label mt-1">notification channels &amp; thresholds</p>
      </header>

      {/* TELEGRAM */}
      <section className="border border-border bg-surface p-6 flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <h2 className="label">TELEGRAM ALERTS</h2>
          <ToggleSwitch
            enabled={draft.telegram_enabled}
            onChange={(v) => patch({ telegram_enabled: v })}
            label="Telegram alerts"
          />
        </div>

        <div className="flex flex-col gap-2">
          <span className="label">CHAT ID</span>
          <input
            type="text"
            value={draft.telegram_chat_id ?? ""}
            onChange={(e) =>
              patch({
                telegram_chat_id: e.target.value === "" ? null : e.target.value,
              })
            }
            placeholder="e.g. 123456789"
            className="w-full p-3 bg-surface-2 border border-border focus:border-amber focus:outline-none font-mono text-sm text-text placeholder:text-text-dim transition-colors"
          />
        </div>

        <TargetEditor
          label="MIN SCORE"
          suffix="/100"
          min={0}
          max={100}
          step={1}
          value={draft.telegram_min_score}
          onChange={(v) => patch({ telegram_min_score: clampScore(v) })}
          helper="only alert via Telegram at or above this score"
        />
      </section>

      {/* NTFY */}
      <section className="border border-border bg-surface p-6 flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <h2 className="label">NTFY PUSH</h2>
          <ToggleSwitch
            enabled={draft.ntfy_enabled}
            onChange={(v) => patch({ ntfy_enabled: v })}
            label="ntfy push alerts"
          />
        </div>

        <div className="flex flex-col gap-2">
          <span className="label">TOPIC</span>
          <input
            type="text"
            value={draft.ntfy_topic ?? ""}
            onChange={(e) =>
              patch({
                ntfy_topic: e.target.value === "" ? null : e.target.value,
              })
            }
            placeholder="leave blank for server default"
            className="w-full p-3 bg-surface-2 border border-border focus:border-amber focus:outline-none font-mono text-sm text-text placeholder:text-text-dim transition-colors"
          />
          <span className="text-[11px] font-mono text-text-dim">
            subscribe in the ntfy app to this topic on your server
          </span>
        </div>

        <TargetEditor
          label="MIN SCORE"
          suffix="/100"
          min={0}
          max={100}
          step={1}
          value={draft.ntfy_min_score}
          onChange={(v) => patch({ ntfy_min_score: clampScore(v) })}
          helper="only push via ntfy at or above this score"
        />
      </section>

      {/* EMAIL */}
      <section className="border border-border bg-surface p-6 flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <h2 className="label">EMAIL DIGEST</h2>
          <ToggleSwitch
            enabled={draft.email_enabled}
            onChange={(v) => patch({ email_enabled: v })}
            label="Email digest"
          />
        </div>

        <div className="flex flex-col gap-2">
          <span className="label">EMAIL ADDRESS</span>
          <input
            type="email"
            value={draft.email_address ?? ""}
            onChange={(e) =>
              patch({
                email_address: e.target.value === "" ? null : e.target.value,
              })
            }
            placeholder="you@example.com"
            className="w-full p-3 bg-surface-2 border border-border focus:border-amber focus:outline-none font-mono text-sm text-text placeholder:text-text-dim transition-colors"
          />
        </div>

        <div className="flex flex-col gap-2">
          <span className="label">DIGEST MODE</span>
          <div
            className="grid grid-cols-2 gap-px border border-border bg-border"
            role="radiogroup"
            aria-label="Email digest mode"
          >
            {DIGEST_MODES.map((m) => {
              const selected = draft.email_digest_mode === m.value;
              return (
                <button
                  key={m.value}
                  type="button"
                  role="radio"
                  aria-checked={selected}
                  onClick={() => patch({ email_digest_mode: m.value })}
                  className={`flex items-center justify-center py-2 px-1 transition-colors duration-150 font-mono text-xs font-semibold tracking-wider ${
                    selected
                      ? "bg-amber text-bg"
                      : "bg-surface-2 text-text-muted hover:bg-surface-3 hover:text-text"
                  }`}
                >
                  {m.label}
                </button>
              );
            })}
          </div>
        </div>

        <TargetEditor
          label="MIN SCORE"
          suffix="/100"
          min={0}
          max={100}
          step={1}
          value={draft.email_min_score}
          onChange={(v) => patch({ email_min_score: clampScore(v) })}
          helper="only include listings at or above this score"
        />
      </section>

      {/* MUTE */}
      <section className="border border-border bg-surface p-6 flex flex-col gap-4">
        <h2 className="label">MUTE NOTIFICATIONS</h2>
        <div className="flex flex-col gap-2">
          <span className="label">MUTE UNTIL</span>
          <div className="flex items-center gap-3 flex-wrap">
            <input
              type="datetime-local"
              value={isoToLocalInput(draft.mute_until)}
              onChange={(e) =>
                patch({ mute_until: localInputToIso(e.target.value) })
              }
              className="p-3 bg-surface-2 border border-border focus:border-amber focus:outline-none font-mono text-sm text-text transition-colors"
            />
            {draft.mute_until && (
              <button
                type="button"
                onClick={() => patch({ mute_until: null })}
                className="font-mono text-xs tracking-wider uppercase text-text-muted hover:text-amber transition-colors"
              >
                CLEAR MUTE
              </button>
            )}
          </div>
          <span className="text-[11px] font-mono text-text-dim">
            {draft.mute_until
              ? `muted until ${new Date(draft.mute_until).toLocaleString()}`
              : "notifications active"}
          </span>
        </div>
      </section>

      <SaveBar
        dirty={dirty}
        dirtyCount={dirtyCount}
        saving={saving}
        onSave={save}
        onDiscard={discard}
      />
    </div>
  );
}

function ToggleSwitch({
  enabled,
  onChange,
  label,
}: {
  enabled: boolean;
  onChange: (v: boolean) => void;
  label: string;
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={enabled}
      aria-label={label}
      onClick={() => onChange(!enabled)}
      className="flex items-center gap-2"
    >
      <span className={enabled ? "dot-active" : "dot-paused"} aria-hidden="true" />
      <span
        className={`font-mono text-[10px] tracking-wider uppercase ${
          enabled ? "text-green" : "text-text-dim"
        }`}
      >
        {enabled ? "ENABLED" : "DISABLED"}
      </span>
    </button>
  );
}
