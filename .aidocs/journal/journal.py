#!/usr/bin/env python3
"""journal.py — create and maintain the daily-session journal.

Lives at <repo>/.aidocs/journal/journal.py. The journal directory is this
file's own parent, so the script works regardless of the current directory.

Run via uv (zero third-party deps — pure stdlib, so no `--with` is needed):

    uv run .aidocs/journal/journal.py new --tags vllm,monitoring "Tuned gpu_mem_util"
    uv run .aidocs/journal/journal.py reindex            # repair today's index
    uv run .aidocs/journal/journal.py reindex --all      # repair every day's index
    uv run .aidocs/journal/journal.py check              # validate, exit 1 on findings

Why a script instead of doing this in-prompt: numbering the session, stamping
~20 lines of frontmatter, and merging the daily-index tag union are
deterministic, fragile, and repeated every session. Doing them here is more
reliable than regenerating the steps each time and keeps the on-disk format
byte-compatible with what docs-doctor and journal-dream expect — the only thing
the agent writes is the body prose.

On-disk contract (do NOT change without updating docs-doctor + journal-dream):
  - session files are named YYYY-MM-DD-sN.md
  - session frontmatter carries: title, type=journal-session, tags (incl.
    `journal`), parent=[[YYYY-MM-DD]], created, status=active, origin?
  - the daily index YYYY-MM-DD.md links every session and its `tags` is the
    union of that day's session tags.
"""

from __future__ import annotations

import argparse
import re
import socket
import sys
from datetime import date
from pathlib import Path

JOURNAL_DIR = Path(__file__).resolve().parent

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SESSION_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-s(\d+)\.md$")
# A `- item` line inside a YAML block list (two-space indent is what we emit).
BLOCK_ITEM_RE = re.compile(r"^\s*-\s+(.+?)\s*$")

INDEX_TABLE_HEADER = "| # | Focus | Key Outcome |\n|---|-------|-------------|\n"
# A daily-index data row: | [S3](2026-06-17-s3.md) | focus | outcome |
INDEX_ROW_RE = re.compile(r"^\|\s*\[S\d+\]\(")


# --------------------------------------------------------------------------- io


def today_str() -> str:
    return date.today().isoformat()


def detect_origin() -> str:
    """Best-effort short hostname; useful for cross-machine journals."""
    return socket.gethostname().split(".")[0]


def split_frontmatter(text: str) -> tuple[str, str]:
    """Return (frontmatter_block_without_fences, body). Empty fm if none."""
    if not text.startswith("---"):
        return "", text
    lines = text.splitlines()
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return "\n".join(lines[1:i]), "\n".join(lines[i + 1 :])
    return "", text


def read_tags(text: str) -> list[str]:
    """Parse `tags:` from canonical block-list form; also tolerate flow form
    (`tags: [a, b]`). Returns [] when there is no parseable tags key — which is
    correct for `check`, since an empty contribution can never widen the union."""
    fm, _ = split_frontmatter(text)
    if not fm:
        return []
    lines = fm.splitlines()
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("tags:"):
            after = stripped[len("tags:") :].strip()
            if after.startswith("[") and after.endswith("]"):  # flow list
                inner = after[1:-1]
                return [t.strip().strip("'\"") for t in inner.split(",") if t.strip()]
            # block list: collect following `- item` lines
            tags: list[str] = []
            for follow in lines[idx + 1 :]:
                m = BLOCK_ITEM_RE.match(follow)
                if not m:
                    break
                tags.append(m.group(1).strip().strip("'\""))
            return tags
    return []


def dedupe(seq) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for x in seq:
        if x and x not in seen:
            seen.add(x)
            out.append(x)
    return out


def fmt_tag_block(tags: list[str]) -> str:
    return "\n".join(f"  - {t}" for t in tags)


def escape_cell(text: str) -> str:
    """Pipes would break the markdown table cell."""
    return text.replace("|", "\\|").strip()


# ----------------------------------------------------------------------- builders


def session_filename(day: str, n: int) -> str:
    return f"{day}-s{n}.md"


def next_session_number(day: str) -> int:
    n = 0
    for f in JOURNAL_DIR.glob(f"{day}-s*.md"):
        m = SESSION_RE.match(f.name)
        if m:
            n = max(n, int(m.group(2)))
    return n + 1


def build_session(day: str, n: int, focus: str, tags: list[str], origin: str | None) -> str:
    tag_lines = fmt_tag_block(dedupe(["journal", *tags]))
    origin_line = f"\norigin: {origin}" if origin else ""
    return (
        f"---\n"
        f'title: "{day} Session {n}"\n'
        f"type: journal-session\n"
        f"tags:\n{tag_lines}\n"
        f'parent: "[[{day}]]"\n'
        f"created: {day}\n"
        f"status: active{origin_line}\n"
        f"---\n\n"
        f"# Session {n} — {focus}\n\n"
        f"- **<key accomplishment>** — details\n"
        f"  - sub-details, commands used, outcomes\n\n"
        f"### Lessons Learned\n"
        f"- <insight that applies beyond this session>\n"
    )


def build_index(day: str, tags: list[str], origin: str | None, rows: list[str]) -> str:
    tag_lines = fmt_tag_block(dedupe(["journal", *tags]))
    origin_line = f"\norigin: {origin}" if origin else ""
    body_rows = "".join(r if r.endswith("\n") else r + "\n" for r in rows)
    return (
        f"---\n"
        f'title: "{day}"\n'
        f"type: journal\n"
        f"tags:\n{tag_lines}\n"
        f"created: {day}\n"
        f"status: active{origin_line}\n"
        f"---\n\n"
        f"# {day}\n\n"
        f"{INDEX_TABLE_HEADER}"
        f"{body_rows}"
    )


def make_row(day: str, n: int, focus: str, outcome: str = "—") -> str:
    return f"| [S{n}]({session_filename(day, n)}) | {escape_cell(focus)} | {escape_cell(outcome)} |"


def focus_from_session(path: Path) -> str:
    """Pull the focus phrase from a session H1: `# Session N — <focus>`."""
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("# Session "):
            parts = re.split(r"\s[—-]\s", line[2:].strip(), maxsplit=1)
            return parts[1].strip() if len(parts) == 2 else line[2:].strip()
    return ""


# --------------------------------------------------------------------------- index


def set_index_tags(index_text: str, tags: list[str]) -> str:
    """Rewrite the `tags:` block of an existing index to the given union."""
    fm, body = split_frontmatter(index_text)
    if not fm:
        return index_text
    lines = fm.splitlines()
    out: list[str] = []
    i = 0
    replaced = False
    while i < len(lines):
        if lines[i].strip().startswith("tags:") and not replaced:
            out.append("tags:")
            out.append(fmt_tag_block(tags))
            i += 1
            while i < len(lines) and BLOCK_ITEM_RE.match(lines[i]):
                i += 1
            replaced = True
            continue
        out.append(lines[i])
        i += 1
    return f"---\n" + "\n".join(out) + "\n---\n" + body


def append_index_row(index_text: str, row: str) -> str:
    """Insert a row right after the last existing table data row."""
    lines = index_text.splitlines()
    last = -1
    for i, line in enumerate(lines):
        if INDEX_ROW_RE.match(line):
            last = i
    if last == -1:  # no rows yet — append after the header separator if present
        for i, line in enumerate(lines):
            if line.strip().startswith("|---"):
                last = i
                break
    lines.insert(last + 1, row)
    return "\n".join(lines) + "\n"


# ----------------------------------------------------------------------- commands


def cmd_new(args: argparse.Namespace) -> int:
    day = args.date or today_str()
    if not DATE_RE.match(day):
        sys.stderr.write(f"error: --date must be YYYY-MM-DD, got {day!r}\n")
        return 2
    JOURNAL_DIR.mkdir(parents=True, exist_ok=True)

    tags = dedupe([t.strip() for t in (args.tags or "").split(",") if t.strip()])
    origin = None if args.no_origin else (args.origin or detect_origin())

    n = next_session_number(day)
    session_path = JOURNAL_DIR / session_filename(day, n)
    session_path.write_text(build_session(day, n, args.focus, tags, origin), encoding="utf-8")

    index_path = JOURNAL_DIR / f"{day}.md"
    row = make_row(day, n, args.focus)
    union = dedupe(["journal", *tags])
    if not index_path.exists():
        index_path.write_text(build_index(day, tags, origin, [row]), encoding="utf-8")
    else:
        text = index_path.read_text(encoding="utf-8")
        if session_path.name not in text:
            text = append_index_row(text, row)
        text = set_index_tags(text, dedupe([*read_tags(text), *union]))
        index_path.write_text(text, encoding="utf-8")

    # The printed path is the one actionable output: open it and fill the body.
    print(session_path)
    return 0


def cmd_reindex(args: argparse.Namespace) -> int:
    days: list[str]
    if args.all:
        days = sorted({m.group(1) for f in JOURNAL_DIR.glob("*-s*.md")
                       if (m := SESSION_RE.match(f.name))})
    else:
        day = args.date or today_str()
        if not DATE_RE.match(day):
            sys.stderr.write(f"error: --date must be YYYY-MM-DD, got {day!r}\n")
            return 2
        days = [day]

    for day in days:
        sessions = sorted(
            (f for f in JOURNAL_DIR.glob(f"{day}-s*.md") if SESSION_RE.match(f.name)),
            key=lambda p: int(SESSION_RE.match(p.name).group(2)),
        )
        if not sessions:
            continue
        index_path = JOURNAL_DIR / f"{day}.md"
        session_union: list[str] = ["journal"]
        for sf in sessions:
            session_union.extend(read_tags(sf.read_text(encoding="utf-8")))
        session_union = dedupe(session_union)

        if not index_path.exists():
            origin = detect_origin()
            rows = [make_row(day, int(SESSION_RE.match(sf.name).group(2)),
                             focus_from_session(sf)) for sf in sessions]
            index_path.write_text(build_index(day, session_union, origin, rows), encoding="utf-8")
            print(f"created {index_path.name}")
            continue

        # Purely additive: preserve existing rows, outcomes, and tag order; only
        # add missing rows and append session tags the index is missing. Never
        # drop or reorder a curated index tag, so a consistent day is a no-op.
        original = index_path.read_text(encoding="utf-8")
        text = original
        for sf in sessions:
            if sf.name not in text:
                n = int(SESSION_RE.match(sf.name).group(2))
                text = append_index_row(text, make_row(day, n, focus_from_session(sf)))
        merged = dedupe([*read_tags(text), *session_union])
        text = set_index_tags(text, merged)
        # set_index_tags drops the trailing newline (splitlines); re-match the
        # original's convention so an already-correct day produces no diff.
        out = text + "\n" if original.endswith("\n") else text
        if out != original:
            index_path.write_text(out, encoding="utf-8")
            print(f"reindexed {index_path.name}")
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    """Mirror docs-doctor's journal_gaps check (missing_index / orphan_session /
    tag_union_gap). docs-doctor stays authoritative where installed."""
    import json

    findings: list[dict] = []
    by_day: dict[str, list[Path]] = {}
    for f in JOURNAL_DIR.glob("*.md"):
        m = SESSION_RE.match(f.name)
        if m:
            by_day.setdefault(m.group(1), []).append(f)

    for day, sessions in sorted(by_day.items()):
        index = JOURNAL_DIR / f"{day}.md"
        if not index.exists():
            findings.append({"type": "missing_index", "file": f"{day}.md",
                             "detail": f"{len(sessions)} session file(s) but no daily index"})
            continue
        index_text = index.read_text(encoding="utf-8")
        index_tags = set(read_tags(index_text))
        session_tags: set[str] = set()
        for sf in sorted(sessions):
            if sf.name not in index_text:
                findings.append({"type": "orphan_session", "file": sf.name,
                                 "detail": f"no row linking {sf.name} in {day}.md"})
            session_tags |= set(read_tags(sf.read_text(encoding="utf-8")))
        missing = session_tags - index_tags
        if missing:
            findings.append({"type": "tag_union_gap", "file": f"{day}.md",
                             "detail": f"index tags missing union members: {sorted(missing)}"})

    print(json.dumps({"journal_gaps": findings, "count": len(findings)}, indent=2))
    return 1 if findings else 0


# ------------------------------------------------------------------------------ cli


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="journal.py", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_new = sub.add_parser("new", help="create the next session file + update the daily index")
    p_new.add_argument("focus", help="short focus line for the session (goes in the H1 + index row)")
    p_new.add_argument("--tags", default="", help="comma-separated topic tags (journal is added automatically)")
    p_new.add_argument("--date", help="override the date (default: today, YYYY-MM-DD)")
    p_new.add_argument("--origin", help="override the origin hostname")
    p_new.add_argument("--no-origin", action="store_true", help="omit the origin field")
    p_new.set_defaults(func=cmd_new)

    p_re = sub.add_parser("reindex", help="rebuild/repair a daily index from its session files")
    g = p_re.add_mutually_exclusive_group()
    g.add_argument("--date", help="day to reindex (default: today)")
    g.add_argument("--all", action="store_true", help="reindex every day with session files")
    p_re.set_defaults(func=cmd_reindex)

    p_ck = sub.add_parser("check", help="validate the journal; exit 1 if any findings")
    p_ck.set_defaults(func=cmd_check)

    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
