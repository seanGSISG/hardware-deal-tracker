@AGENTS.md
<!-- journal-bootstrap:pointers (sentinel — do not remove; marks the journal system as wired) -->

<reminders>
At the **start of every session**, read `REMINDERS.md` and surface any row whose **Due** date is on/before today before starting other work. Whenever the user asks to be reminded of something on/by a date, add a dated row there. Keep it lean: delete a row once its reminder is handled.
</reminders>

## Self-documentation & journal

This repo keeps a mandatory per-session journal plus a condition-triggered ideas
parking lot and a date-triggered reminders surface. The rule that enforces them
is `.claude/rules/self-documentation.md`.

| Domain | File | When to read |
|--------|------|--------------|
| Daily journal | `.aidocs/journal/` | **End of every session (mandatory).** Create the entry with `uv run .aidocs/journal/journal.py new --tags <topics> "<focus>"`, then fill the body |
| Journal template / schema | `.aidocs/templates/journal.md` | Manual fallback when `uv`/Python is unavailable, or to understand the frontmatter schema |
| Ideas / parking lot | `.aidocs/ideas/` | Before committing to non-trivial new work, or when deferring an idea — see `.aidocs/ideas/README.md` for the lifecycle |
| Reminders | `REMINDERS.md` | Start of every session — surface any row whose `Due` is on/before today |
