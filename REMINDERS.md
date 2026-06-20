# Reminders

Date-based reminders for this repo. **At the start of every session, Claude reads this file and surfaces any row whose `Due` is on/before today** (see the `<reminders>` pointer in `CLAUDE.md`).

This is the **time-triggered** surface. It complements — does not replace — the other two parking places:

| File | Triggered by | Holds |
|------|--------------|-------|
| **`REMINDERS.md`** (this file) | a **date** | "nudge me on/by YYYY-MM-DD" |
| `.aidocs/ideas/README.md` | a **condition/event** | half-baked ideas, deferred decisions, research ("revisit when corpus ≥ N", "if X recurs") |
| the scoped backlog | nothing (just a queue) | scoped/committed backlog work |

Every row here is a **thin pointer** — the real content lives in the linked file. Don't duplicate detail.

## How to use

- **Add** — when the user asks to be reminded of something on/by a date, add a row to the table below, sorted by `Due` ascending. Convert relative dates to absolute (`YYYY-MM-DD`). If a reminder has *no* date — only a condition — it belongs in `.aidocs/ideas/`, not here.
- **Surface** — at session start, if any `Due ≤ today`, tell the user before other work. Don't auto-act on it unless they say so.
- **Complete** — once a reminder is handled, **delete its row entirely**. Don't keep a done/fired log — this file stays lean, holding only live, future-dated reminders. If it's only rescheduled, bump its `Due` instead. (The lasting record of *what happened* lives in the journal / the linked pointer file, not here.)

## Reminders

| Due | Topic | Pointer | Why then |
|-----|-------|---------|----------|
| _(none yet)_ | | | |
