# `.aidocs/ideas/` — half-baked ideas, deferred decisions, research parking lot

This folder holds **un-spec'd improvements** — things worth doing eventually but missing the design clarity, corpus, or concrete trigger needed to commit to building right now. The goal is to capture the *thought* so neither human nor future-Claude has to re-derive it, without polluting the scoped backlog (committed work) or `plans/` (executable plans).

## When to file an idea here

File an idea in this folder when **any** of the following is true:

- An improvement was discussed but you (or the user) explicitly chose to defer it pending more research
- A design has open questions whose answers will change the implementation shape
- The trigger condition to revisit is conditional (e.g. "when corpus ≥ N entries", "if pattern X recurs")
- Building now would be premature optimization or speculative engineering

## When NOT to file here

- **Scoped work that's been deferred** → add to the backlog instead ("we WILL do this, just not now"). Ideas folder is for "we MIGHT do this, after more thought".
- **Active multi-phase work** → `.aidocs/plans/` instead.
- **Completed work** → `.aidocs/journal/` session files.

## Lifecycle

```
idea filed (status: idea)
  └─→ researching (open questions getting answered)
        └─→ ready (graduate to the backlog or plans/)
        └─→ abandoned (status: abandoned, kept for reference)
```

When an idea graduates, leave a stub here with `status: graduated` and a link to its new home — that way the search history remains intact.

## File naming

`<area>-<short-slug>.md` — area first, since the folder will be browsed by topic.

Examples:
- `infra-expose-service-behind-sso.md`
- `tooling-rag-corpus.md`
- `docs-weekly-pattern-audit.md`

## Template

See `_TEMPLATE.md` for the required structure. Every idea file MUST include:

| Field | Purpose |
|---|---|
| `status` | `idea` / `researching` / `ready` / `graduated` / `abandoned` |
| `filed` | YYYY-MM-DD the idea was first written down |
| `revisit` | The trigger condition to come back to this |
| `origin_session` | Wikilink to the journal session this came from (e.g. `"[[YYYY-MM-DD-sN]]"`) |
| **Origin** section | One sentence on what prompted filing, with a clickable relative link to the journal session (`../journal/YYYY-MM-DD-sN.md`) |
| **Trigger to revisit** section | Plain-English version of `revisit` |
| **Open questions** section | What you'd need to answer before building |
| **Proposed design (sketch)** section | What it might look like |
| **Blast radius** section | What it touches |

## Current ideas

| File | Area | Status | Revisit when |
|---|---|---|---|
| [build-reproducible-from-uv-lock](build-reproducible-from-uv-lock.md) | build / CI | idea | Next backend image rebuild, or before MVP4 |
| [sources-microcenter-coverage](sources-microcenter-coverage.md) | sources | idea | Sean picks Slickdeals-RSS vs residential-egress browser, or MC ships a feed |
