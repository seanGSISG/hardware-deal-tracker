"""Banned-keyword relevance filter + China-origin flag.

eBay Browse `q=` is fuzzy, so a search for the 7543P pulls back near-miss CPUs
(EPYC 4542 / 7542). The global stop-list drops those by TITLE before they are
persisted/scored, while the China-origin flag is stamped from itemLocation.
"""
from app.services.ebay.parser import ListingParser
from app.services.filters import partition_banned, title_is_banned

BANNED = ["4542", "7542"]


def test_title_is_banned_whole_word_only():
    assert title_is_banned("AMD EPYC 4542 32C server CPU", BANNED) is True
    assert title_is_banned("AMD EPYC 7542 32C server CPU", BANNED) is True
    # The wanted part is NOT banned even though it is numerically adjacent.
    assert title_is_banned("AMD EPYC 7543P 32C/64T Milan", BANNED) is False
    # A banned token embedded inside a longer alnum run must not match.
    assert title_is_banned("PART-X45420 widget", BANNED) is False


def test_title_is_banned_is_case_insensitive_and_safe_on_empty():
    assert title_is_banned("amd epyc 4542", BANNED) is True
    assert title_is_banned("", BANNED) is False
    assert title_is_banned(None, BANNED) is False
    assert title_is_banned("anything", []) is False


def test_partition_banned_splits_rows():
    rows = [
        {"title": "AMD EPYC 7543P 32C", "marketplace_id": "a"},
        {"title": "AMD EPYC 4542 32C", "marketplace_id": "b"},
        {"title": "AMD EPYC 7542 32C", "marketplace_id": "c"},
    ]
    kept, dropped = partition_banned(rows, BANNED)
    assert [r["marketplace_id"] for r in kept] == ["a"]
    assert [r["marketplace_id"] for r in dropped] == ["b", "c"]


def test_partition_banned_empty_list_keeps_everything():
    rows = [{"title": "AMD EPYC 4542"}]
    kept, dropped = partition_banned(rows, [])
    assert kept == rows
    assert dropped == []


def _item(title: str, country: str | None) -> dict:
    item = {
        "itemId": "x1",
        "title": title,
        "price": {"value": "100", "currency": "USD"},
        "seller": {"username": "s", "feedbackScore": 1, "feedbackPercentage": "100"},
        "buyingOptions": ["FIXED_PRICE"],
        "itemWebUrl": "https://ebay.com/itm/x1",
    }
    if country is not None:
        item["itemLocation"] = {"country": country}
    return item


def test_parser_flags_china_origin():
    parser = ListingParser()
    cn = parser.parse_item(_item("AMD EPYC 7543P", "CN"))
    assert cn["item_country"] == "CN"
    assert cn["is_china"] is True

    us = parser.parse_item(_item("AMD EPYC 7543P", "US"))
    assert us["item_country"] == "US"
    assert us["is_china"] is False

    unknown = parser.parse_item(_item("AMD EPYC 7543P", None))
    assert unknown["item_country"] is None
    assert unknown["is_china"] is False
