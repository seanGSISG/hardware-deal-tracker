---
title: "YYYY-MM-DD"
type: journal
tags:
  - journal
created: YYYY-MM-DD
status: active
---

# YYYY-MM-DD

| # | Focus | Key Outcome |
|---|-------|-------------|
| [S1](YYYY-MM-DD-s1.md) | Brief description | One-line result |
| [S2](YYYY-MM-DD-s2.md) | Brief description | One-line result |

---

> **The fast path is the helper, not this template.** Run
> `uv run .aidocs/journal/journal.py new --tags <topics> "<focus>"` — it numbers
> the session, stamps the frontmatter, and updates this index for you. Use the
> schema below only as a manual fallback (no `uv`/Python available) or to
> understand the format.

## Frontmatter Rules (Daily Index)

| Field | Value | Required |
|-------|-------|----------|
| `title` | Date string `"YYYY-MM-DD"` (quoted) | Yes |
| `type` | Always `journal` | Yes |
| `tags` | Always includes `journal`, plus **all** topic tags from that day's sessions | Yes |
| `created` | Date `YYYY-MM-DD` (unquoted) | Yes |
| `status` | Always `active` | Yes |
| `origin` | Hostname that generated the entry (e.g., `spark`) | Optional |

## Daily Index Rules

- The daily file is a **lightweight index** — one table row per session
- Each row links to the session file: `[S1](YYYY-MM-DD-s1.md)`
- Tags in the daily index frontmatter are the **union** of all session tags
- When appending a new session: add a table row and merge any new tags into frontmatter

---

## Session File Template

Session files live alongside the daily index: `.aidocs/journal/YYYY-MM-DD-sN.md`

```markdown
---
title: "YYYY-MM-DD Session N"
type: journal-session
tags:
  - journal
  - topic-tag
parent: "[[YYYY-MM-DD]]"
created: YYYY-MM-DD
status: active
---

# Session N — Brief description of focus area

- **Key accomplishment** — details
  - Sub-details, commands used, outcomes
- **Another item** — what happened and why
  - Technical details

### Lessons Learned
- Insight that applies beyond this session
```

## Session File Rules

| Field | Value | Required |
|-------|-------|----------|
| `title` | `"YYYY-MM-DD Session N"` (quoted) | Yes |
| `type` | Always `journal-session` | Yes |
| `tags` | Always includes `journal`, plus topic tags for **this session only** | Yes |
| `parent` | Wikilink to daily index `"[[YYYY-MM-DD]]"` | Yes |
| `created` | Date `YYYY-MM-DD` (unquoted) | Yes |
| `status` | Always `active` | Yes |

## Format Rules

- **Session headings**: `# Session N — Brief description` (use em dash `—`)
- **Bullets**: Lead with **bold key item** — then details
  - Use indented sub-bullets for technical specifics, commands, outcomes
- **Lessons Learned**: Optional `### Lessons Learned` subsection for insights that apply beyond this session
- **Tone**: Factual and concise — this is an operational log, not prose
