"""Listing relevance filtering — global banned-keyword stop-list.

eBay's Browse `q=` search is fuzzy and returns near-miss models (a search for
"AMD EPYC 7543P" surfaces unrelated CPUs like the EPYC 4542 / 7542). These pure,
dependency-free helpers drop any listing whose TITLE contains a banned token so
the noise is never persisted, scored, or shown. Matching is case-insensitive and
word-boundary-anchored so a ban on "7542" never accidentally nukes a title that
merely embeds the digits inside a longer part number.
"""
from __future__ import annotations

import re
from collections.abc import Iterable

# Cache compiled patterns per (frozenset of) banned words so the poll path does
# not recompile regexes on every search.
_PATTERN_CACHE: dict[tuple[str, ...], re.Pattern[str] | None] = {}


def _compile(banned: Iterable[str]) -> re.Pattern[str] | None:
    words = tuple(sorted({w.strip().lower() for w in banned if w and w.strip()}))
    if not words:
        return None
    if words not in _PATTERN_CACHE:
        alternation = "|".join(re.escape(w) for w in words)
        # \b is unreliable around non-word chars; wrap the alternation so a token
        # is matched only when not flanked by another alphanumeric character.
        _PATTERN_CACHE[words] = re.compile(
            rf"(?<![0-9a-z])(?:{alternation})(?![0-9a-z])", re.IGNORECASE
        )
    return _PATTERN_CACHE[words]


def title_is_banned(title: str | None, banned: Iterable[str]) -> bool:
    """True if ``title`` contains any banned token as a whole word."""
    pattern = _compile(banned)
    if pattern is None or not title:
        return False
    return pattern.search(title) is not None


def partition_banned(
    rows: list[dict], banned: Iterable[str]
) -> tuple[list[dict], list[dict]]:
    """Split listing-row dicts into (kept, dropped) by their ``title`` field."""
    pattern = _compile(banned)
    if pattern is None:
        return list(rows), []
    kept: list[dict] = []
    dropped: list[dict] = []
    for row in rows:
        if row.get("title") and pattern.search(row["title"]):
            dropped.append(row)
        else:
            kept.append(row)
    return kept, dropped
