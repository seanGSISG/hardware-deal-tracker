#!/usr/bin/env python3
"""Generate scripts/seed_data_v2.sql from the Python HardwareCatalog.

The catalog (`app/services/ebay/catalog.py`) is the single source of truth for
the 34 research-validated starter items. This script renders a deterministic,
idempotent SQL seed file from it so the two never drift.

The generated seed is OPTIONAL starter data (ADR-005): the app runs correctly
from an empty catalog. Re-run via `make seed-regen` (or directly with
`uv run python scripts/generate_seed.py`) after editing the catalog, then commit
the regenerated SQL. A parity test (`tests/test_seed_parity.py`) guards drift.

Idempotency: tracked_items INSERTs use `ON CONFLICT (name) DO UPDATE` so the
seed can be re-applied safely and picks up catalog edits.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Allow running as a standalone script (`python scripts/generate_seed.py`).
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.services.ebay.catalog import HardwareCatalog  # noqa: E402

SEED_PATH = BACKEND_DIR / "scripts" / "seed_data_v2.sql"

# Column order for the tracked_items INSERT.
TRACKED_COLUMNS = (
    "name, keywords, sku, mpn, category_id, marketplace, target_price, "
    "alert_threshold, min_deal_score, is_enabled, search_interval, scam_floor, "
    "benchmark_median, notes"
)

# Columns updated on conflict (everything except the unique key `name`).
_UPDATE_COLUMNS = [
    "keywords", "sku", "mpn", "category_id", "marketplace", "target_price",
    "alert_threshold", "min_deal_score", "is_enabled", "search_interval",
    "scam_floor", "benchmark_median", "notes",
]


def _sql_str(value: str) -> str:
    """Single-quoted SQL string literal with quote-escaping."""
    return "'" + value.replace("'", "''") + "'"


def _sql_money(value) -> str:
    """Render a numeric as a fixed 2-decimal literal (or NULL)."""
    if value is None:
        return "NULL"
    return f"{float(value):.2f}"


def _sql_ratio(value) -> str:
    if value is None:
        return "NULL"
    return f"{float(value):g}"


def _sql_bool(value: bool) -> str:
    return "true" if value else "false"


def _row(item) -> str:
    notes = item.notes.replace("Don't", "Do not")
    fields = [
        _sql_str(item.name),
        _sql_str(item.keywords),
        _sql_str(item.sku),
        _sql_str(item.mpn),
        _sql_str(item.category_id),
        _sql_str(item.marketplace),
        _sql_money(item.target_price),
        _sql_ratio(item.alert_threshold),
        str(int(item.min_deal_score)),
        _sql_bool(item.is_enabled),
        str(int(item.search_interval)),
        _sql_money(item.scam_floor),
        _sql_money(item.benchmark_median),
        _sql_str(notes),
    ]
    return "    (" + ", ".join(fields) + ")"


def render_sql() -> str:
    """Return the full deterministic seed SQL as a string."""
    lines: list[str] = []
    lines.append("-- Seed data for Hardware Deal Tracker")
    lines.append("-- GENERATED FILE — do not edit by hand.")
    lines.append("-- Source of truth: app/services/ebay/catalog.py")
    lines.append("-- Regenerate with: make seed-regen")
    lines.append("--")
    lines.append("-- OPTIONAL starter data (ADR-005): the app runs from an empty catalog.")
    lines.append("")
    lines.append(f"INSERT INTO tracked_items ({TRACKED_COLUMNS}) VALUES")

    rows = [_row(item) for item in HardwareCatalog.ITEMS]
    lines.append(",\n".join(rows))

    update_set = ",\n".join(
        f"    {col} = EXCLUDED.{col}" for col in _UPDATE_COLUMNS
    )
    lines.append("ON CONFLICT (name) DO UPDATE SET")
    lines.append(update_set + ";")
    lines.append("")

    # Default admin user (password: admin123). Preserved from the prior seed.
    lines.append("-- Default admin user (password: admin123)")
    lines.append("INSERT INTO users (username, email, hashed_password, is_admin) VALUES")
    lines.append(
        "    ('admin', 'admin@localhost', "
        "'$2b$12$X.hvC98a9KtnrqRDFGl0FOKZ9abfWb.jKFdLJOHhjbHmW9YfrzDSy', true)"
    )
    lines.append("    ON CONFLICT (username) DO NOTHING;")
    lines.append("")

    # Default notification settings for the admin user.
    lines.append("-- Default notification settings")
    lines.append(
        "INSERT INTO notification_settings (user_id, telegram_enabled, email_enabled, "
        "email_digest_mode, telegram_min_score, email_min_score)"
    )
    lines.append("    VALUES (1, false, false, 'daily', 70, 50)")
    lines.append("    ON CONFLICT (user_id) DO NOTHING;")
    lines.append("")

    return "\n".join(lines)


def main() -> None:
    sql = render_sql()
    SEED_PATH.write_text(sql)
    print(f"Wrote {len(HardwareCatalog.ITEMS)} tracked items to {SEED_PATH}")


if __name__ == "__main__":
    main()
