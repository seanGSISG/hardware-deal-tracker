"""Captured Shopify /products.json fixtures (feature-003).

Small, representative, HAND-AUTHORED /products.json payloads — one per onboarded
Shopify retailer. They mirror the real Shopify /products.json shape (products ->
variants with id/price/available + a handle) so the mock-transport integration
tests can assert each store's adapter normalizes correctly WITHOUT ever hitting a
live store. Keep these tiny: a couple of matching products + a noise product.
"""
from __future__ import annotations

import json
from pathlib import Path

FIXTURE_DIR = Path(__file__).resolve().parent


def load_products_json(source: str) -> dict:
    """Load a captured /products.json fixture for a Shopify source id."""
    path = FIXTURE_DIR / f"{source}_products.json"
    return json.loads(path.read_text())
