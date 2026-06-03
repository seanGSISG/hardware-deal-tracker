"""Community-signal ingestion (feature-007, ADR-007).

A DISTINCT, fully-gated leads pipeline that pulls unstructured peer-to-peer deal
posts (Reddit r/homelabsales; STH optional) and AI-extracts structured fields
into a separate LEADS surface. It is ADJACENT to — never part of — the structured
SourceAdapter price-poll path: it does NOT emit NormalizedListing, never touches
DealScoringEngine / ListingScore / PriceHistory / NotificationDispatcher, and
runs on its own polite per-source rate bucket distinct from eBay's 5000/day
RateBudgetManager.

Everything is gated behind ENABLE_COMMUNITY_SIGNAL=false so the app, scheduler,
and the existing test suite behave identically when the feature is off.
"""
from app.services.community.source import CommunitySignalSource
from app.services.community.types import CommunityLead, CommunityPost

__all__ = ["CommunitySignalSource", "CommunityPost", "CommunityLead"]
