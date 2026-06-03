"""story-C: cross-source dedup on (source, source_listing_id).

The same listing id can legitimately exist under two different sources
(e.g. TechMikeNY appears in both its own site feed and the eBay feed), so dedup
must key on the (source, source_listing_id) pair, not the raw id alone.
"""
from datetime import datetime

from app.models.listing import Listing
from app.services.ebay.dedup import DeduplicationEngine


def _listing_row(source: str, listing_id: str, price: float = 100.0) -> dict:
    return {
        "source": source,
        "marketplace_id": listing_id,
        "title": f"{source} {listing_id}",
        "price": price,
        "shipping": 0,
        "seller": "seller",
        "url": f"https://example.com/{source}/{listing_id}",
        "listing_date": datetime.utcnow(),
    }


async def test_same_id_different_source_is_not_a_duplicate(db):
    # Pre-existing eBay listing with id "abc".
    db.add(Listing(**_listing_row("ebay", "abc")))
    await db.flush()

    dedup = DeduplicationEngine()
    # techmikeny:abc shares the raw id but is a different source -> NOT a dup.
    new_listings, dups = await dedup.dedup_batch(db, [_listing_row("techmikeny", "abc")])

    assert dups == 0
    assert len(new_listings) == 1


async def test_same_id_same_source_is_a_duplicate(db):
    db.add(Listing(**_listing_row("ebay", "abc")))
    await db.flush()

    dedup = DeduplicationEngine()
    new_listings, dups = await dedup.dedup_batch(db, [_listing_row("ebay", "abc")])

    assert dups == 1
    assert len(new_listings) == 0


async def test_dedup_within_batch_across_sources(db):
    dedup = DeduplicationEngine()
    batch = [
        _listing_row("ebay", "1"),
        _listing_row("techmikeny", "1"),  # same id, different source -> kept
        _listing_row("ebay", "1"),        # in-batch duplicate of the first -> dropped
    ]
    new_listings, dups = await dedup.dedup_batch(db, batch)

    assert len(new_listings) == 2
    assert dups == 1


async def test_missing_source_defaults_to_ebay(db):
    # Backward-compat: legacy rows / eBay parser output without an explicit
    # source key are treated as source="ebay".
    db.add(Listing(**_listing_row("ebay", "legacy")))
    await db.flush()

    dedup = DeduplicationEngine()
    row = _listing_row("ebay", "legacy")
    del row["source"]  # no source key
    new_listings, dups = await dedup.dedup_batch(db, [row])

    assert dups == 1
    assert len(new_listings) == 0
