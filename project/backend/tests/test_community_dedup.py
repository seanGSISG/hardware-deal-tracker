"""feature-007 story-4: sold/traded filter + dedup (deterministic, no network/LLM)."""
from app.services.community.dedup import dedup_leads, filter_stale
from app.services.community.types import CommunityLead


def _lead(post_id, status="for-sale", title="[USA][H] EPYC [W] PayPal"):
    return CommunityLead(
        source="reddit_homelabsales", source_post_id=post_id, title=title,
        url=f"http://x/{post_id}", model="EPYC 7F72", price=200.0, status=status,
    )


def test_sold_status_filtered_out():
    leads = [_lead("p1", status="for-sale"), _lead("p2", status="sold")]
    kept = filter_stale(leads)
    assert [lead.source_post_id for lead in kept] == ["p1"]


def test_traded_and_pending_filtered_out():
    leads = [
        _lead("p1", status="for-sale"),
        _lead("p2", status="traded"),
        _lead("p3", status="pending"),
    ]
    assert [lead.source_post_id for lead in filter_stale(leads)] == ["p1"]


def test_title_sold_marker_filtered_even_if_status_missed():
    # Status parsed as unknown but the title clearly says SOLD -> drop it.
    lead = _lead("p1", status="unknown", title="[USA-TX][H] Xeon Gold 6248 — SOLD")
    assert filter_stale([lead]) == []


def test_unknown_status_survives():
    assert len(filter_stale([_lead("p1", status="unknown", title="[H] EPYC [W] cash")])) == 1


def test_dedup_collapses_repeated_post_id():
    leads = [_lead("p1"), _lead("p1"), _lead("p2")]
    out = dedup_leads(leads)
    assert [lead.source_post_id for lead in out] == ["p1", "p2"]


def test_dedup_keeps_first_occurrence():
    first = _lead("p1")
    first.price = 100.0
    second = _lead("p1")
    second.price = 999.0
    out = dedup_leads([first, second])
    assert len(out) == 1
    assert out[0].price == 100.0
