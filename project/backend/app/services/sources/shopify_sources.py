"""Per-source Shopify registry + robots.txt/ToS gating (feature-003, ADR-003).

The generic `ShopifyJsonLdAdapter` is driven entirely by a per-retailer
`ShopifySourceConfig`. This module is the curated registry of the six onboarded
US used-server retailers plus, for each, a recorded robots.txt/ToS verification
that GATES enablement:

    a store is polled only when it is (a) globally enabled
    (settings.ENABLE_SHOPIFY_SOURCES), (b) per-store enabled
    (settings.SHOPIFY_<STORE>_ENABLED), AND (c) robots/ToS-verified here.

A store whose `verification.enabled` is False (robots disallow / ToS forbid)
stays dark even when both enable flags are true. The verification records are the
machine-readable twin of the human ledger in docs/SOURCE_ONBOARDING.md.

Primaries (LIVE):   TechMikeNY, UnixSurplus, ServerMonkey
Secondaries:        Cloud Ninjas, Natex, SaveMyServer (low-cadence price MEMORY)

Tests inject a transport + fixtures; this module never makes a live call.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.core.config import settings
from app.services.sources.rate_budget import SourceRateBudget
from app.services.sources.shopify import ShopifyJsonLdAdapter, ShopifySourceConfig

# Polite default daily buckets (separate from eBay's 5000/day).
PRIMARY_DAILY_LIMIT = 100
# SaveMyServer is a price-MEMORY signal: poll it rarely, not as a hot feed.
MEMORY_DAILY_LIMIT = 20


@dataclass(frozen=True)
class SourceVerification:
    """Recorded robots.txt/ToS check that gates a source's enablement.

    `enabled` is the authoritative gate: a source with `enabled=False` is never
    built/polled regardless of the config enable flags. Mirrors one row of the
    docs/SOURCE_ONBOARDING.md ledger.
    """

    platform: str
    products_json_url: str
    robots_allows_products_json: bool
    tos_forbids: bool
    tos_checked_on: str  # ISO date (YYYY-MM-DD)
    enabled: bool
    notes: str = ""


@dataclass(frozen=True)
class ShopifySourceEntry:
    """A registry row: per-store config + its verification + cadence metadata."""

    config: ShopifySourceConfig
    verification: SourceVerification
    daily_limit: int = PRIMARY_DAILY_LIMIT
    #: True for low-cadence price-memory sources (SaveMyServer), not hot feeds.
    is_price_memory: bool = False


def _verified(products_json_url: str, *, checked_on: str, notes: str = "") -> SourceVerification:
    """Build a passing verification (robots allows /products.json, ToS OK)."""
    return SourceVerification(
        platform="Shopify",
        products_json_url=products_json_url,
        robots_allows_products_json=True,
        tos_forbids=False,
        tos_checked_on=checked_on,
        enabled=True,
        notes=notes,
    )


# Verification date for this onboarding round.
_CHECKED = "2026-06-02"

SHOPIFY_SOURCES: dict[str, ShopifySourceEntry] = {
    # -- Primaries (LIVE) ----------------------------------------------------
    "techmikeny": ShopifySourceEntry(
        config=ShopifySourceConfig(
            source="techmikeny",
            base_url="https://techmikeny.com",
            merchant="TechMikeNY",
            default_condition="Refurbished",
        ),
        verification=_verified(
            "https://techmikeny.com/products.json", checked_on=_CHECKED,
            notes="robots.txt allows /products.json; ToS permits public catalog browsing.",
        ),
        daily_limit=PRIMARY_DAILY_LIMIT,
    ),
    "unixsurplus": ShopifySourceEntry(
        config=ShopifySourceConfig(
            source="unixsurplus",
            base_url="https://unixsurplus.com",
            merchant="UNIXSurplus",
            default_condition="Used",
        ),
        verification=_verified(
            "https://unixsurplus.com/products.json", checked_on=_CHECKED,
            notes="robots.txt allows /products.json; ToS permits public catalog browsing.",
        ),
        daily_limit=PRIMARY_DAILY_LIMIT,
    ),
    "servermonkey": ShopifySourceEntry(
        config=ShopifySourceConfig(
            source="servermonkey",
            base_url="https://www.servermonkey.com",
            merchant="ServerMonkey",
            default_condition="Refurbished",
        ),
        verification=_verified(
            "https://www.servermonkey.com/products.json", checked_on=_CHECKED,
            notes="robots.txt allows /products.json; ToS permits public catalog browsing.",
        ),
        daily_limit=PRIMARY_DAILY_LIMIT,
    ),
    # -- Secondaries (configured-and-verified this round) --------------------
    "cloud_ninjas": ShopifySourceEntry(
        config=ShopifySourceConfig(
            source="cloud_ninjas",
            base_url="https://cloudninjas.com",
            merchant="Cloud Ninjas",
            default_condition="Refurbished",
        ),
        verification=_verified(
            "https://cloudninjas.com/products.json", checked_on=_CHECKED,
            notes="robots.txt allows /products.json; ToS permits public catalog browsing.",
        ),
        daily_limit=PRIMARY_DAILY_LIMIT,
    ),
    "natex": ShopifySourceEntry(
        config=ShopifySourceConfig(
            source="natex",
            base_url="https://natex.us",
            merchant="Natex",
            default_condition="Used",
        ),
        verification=_verified(
            "https://natex.us/products.json", checked_on=_CHECKED,
            notes="robots.txt allows /products.json; ToS permits public catalog browsing.",
        ),
        daily_limit=PRIMARY_DAILY_LIMIT,
    ),
    "savemyserver": ShopifySourceEntry(
        config=ShopifySourceConfig(
            source="savemyserver",
            base_url="https://savemyserver.com",
            merchant="SaveMyServer",
            default_condition="Refurbished",
        ),
        verification=_verified(
            "https://savemyserver.com/products.json", checked_on=_CHECKED,
            notes="Low-cadence price-MEMORY source; robots allows /products.json, ToS OK.",
        ),
        daily_limit=MEMORY_DAILY_LIMIT,
        is_price_memory=True,
    ),
}

PRIMARY_SOURCES: tuple[str, ...] = ("techmikeny", "unixsurplus", "servermonkey")
SECONDARY_SOURCES: tuple[str, ...] = ("cloud_ninjas", "natex", "savemyserver")

# Map source id -> the settings.* attribute names for its per-store overrides.
_CONFIG_ATTR = {
    "techmikeny": "TECHMIKENY",
    "unixsurplus": "UNIXSURPLUS",
    "servermonkey": "SERVERMONKEY",
    "cloud_ninjas": "CLOUD_NINJAS",
    "natex": "NATEX",
    "savemyserver": "SAVEMYSERVER",
}


def _per_store_enabled_from_settings() -> dict[str, bool]:
    return {
        src: getattr(settings, f"SHOPIFY_{_CONFIG_ATTR[src]}_ENABLED", True)
        for src in SHOPIFY_SOURCES
    }


def _base_url_for(source: str) -> str:
    override = getattr(settings, f"SHOPIFY_{_CONFIG_ATTR[source]}_BASE_URL", "")
    return override or SHOPIFY_SOURCES[source].config.base_url


def _daily_limit_for(source: str) -> int:
    override = getattr(settings, f"SHOPIFY_{_CONFIG_ATTR[source]}_DAILY_LIMIT", 0)
    return override or SHOPIFY_SOURCES[source].daily_limit


def build_shopify_adapters(
    transport,
    *,
    global_enabled: bool | None = None,
    per_store_enabled: dict[str, bool] | None = None,
    verification_overrides: dict[str, bool] | None = None,
    budget: SourceRateBudget | None = None,
) -> list[ShopifyJsonLdAdapter]:
    """Build adapters for every enabled-and-verified Shopify source.

    A source is included only when ALL hold:
      * `global_enabled` (defaults to settings.ENABLE_SHOPIFY_SOURCES),
      * its per-store enable flag (defaults from settings),
      * its registry robots/ToS verification passes (override via
        `verification_overrides` in tests).

    All built adapters share one `SourceRateBudget` instance, but each draws from
    its OWN named bucket (configured to the per-store daily limit), so exhausting
    one store never touches another or eBay's 5000/day budget.
    """
    if global_enabled is None:
        global_enabled = settings.ENABLE_SHOPIFY_SOURCES
    if not global_enabled:
        return []

    if per_store_enabled is None:
        per_store_enabled = _per_store_enabled_from_settings()
    verification_overrides = verification_overrides or {}
    budget = budget or SourceRateBudget()

    adapters: list[ShopifyJsonLdAdapter] = []
    for source, entry in SHOPIFY_SOURCES.items():
        verified = verification_overrides.get(source, entry.verification.enabled)
        if not verified:
            continue
        if not per_store_enabled.get(source, True):
            continue

        config = entry.config
        base_url = _base_url_for(source)
        if base_url != config.base_url:
            config = ShopifySourceConfig(
                source=config.source,
                base_url=base_url,
                merchant=config.merchant,
                currency=config.currency,
                default_condition=config.default_condition,
            )
        adapters.append(
            ShopifyJsonLdAdapter(
                config,
                transport=transport,
                enabled=True,
                daily_limit=_daily_limit_for(source),
                budget=budget,
            )
        )
    return adapters
