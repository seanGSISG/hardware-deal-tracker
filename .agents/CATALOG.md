# Hardware Catalog Guide

> The 34-item curated hardware catalog, scam floor methodology, and how to add new items. Read this when modifying tracked items or adding new hardware.

---

## What is the Catalog?

The catalog is the single source of truth for hardware pricing. Each entry contains:
- **Search keywords** — What to query on eBay
- **Target price** — Your "I'd buy at this price" threshold
- **Scam floor** — Minimum realistic price (below = suspicious/scam)
- **Benchmark median** — Research-validated median market price
- **eBay category ID** — Optional category filter
- **Notes** — Context for why this item was chosen

The catalog exists in two places:
1. **`backend/app/services/ebay/catalog.py`** — Python `CatalogItem` dataclasses (runtime)
2. **`backend/scripts/seed_data_v2.sql`** — Database INSERT statements (seed)

**Both must be kept in sync.**

---

## Catalog Structure

```python
@dataclass
class CatalogItem:
    name: str                    # Display name
    search_keywords: str         # eBay search query
    ebay_category_id: str | None # eBay category filter
    target_price: Decimal        # Buy-at price
    scam_floor: Decimal          # Below = suspicious
    benchmark_median: Decimal    # Market median
    notes: str                   # Context
```

---

## All 34 Catalog Items

### CPUs (2 items)

| Name | Search Keywords | Target | Scam Floor | Median | Tier |
|------|----------------|--------|------------|--------|------|
| AMD EPYC 7F72 | AMD EPYC 7F72 | $1,800 | $1,200 | $2,200 | P0 |
| AMD EPYC 7443 | AMD EPYC 7443 | $2,000 | $1,400 | $2,500 | P0 |

### Motherboards (2 items)

| Name | Search Keywords | Target | Scam Floor | Median | Tier |
|------|----------------|--------|------------|--------|------|
| Supermicro H12SSL-CT | Supermicro H12SSL-CT | $650 | $400 | $800 | P0 |
| Asrock Rack ROMED8-2T | Asrock Rack ROMED8-2T | $550 | $350 | $700 | P1 |

### Workstation GPUs (5 items)

| Name | Search Keywords | Target | Scam Floor | Median | Tier |
|------|----------------|--------|------------|--------|------|
| NVIDIA RTX PRO 6000 Blackwell | NVIDIA RTX PRO 6000 Blackwell | $6,500 | $4,500 | $7,500 | P0 |
| NVIDIA RTX 6000 Ada | NVIDIA RTX 6000 Ada Generation | $4,500 | $3,000 | $5,200 | P0 |
| NVIDIA RTX A6000 | NVIDIA RTX A6000 48GB | $2,800 | $1,800 | $3,200 | P1 |
| NVIDIA RTX A5500 | NVIDIA RTX A5500 | $1,500 | $1,000 | $1,800 | P1 |
| NVIDIA RTX A5000 | NVIDIA RTX A5000 | $1,200 | $750 | $1,500 | P1 |

### Inference GPUs (3 items)

| Name | Search Keywords | Target | Scam Floor | Median | Tier |
|------|----------------|--------|------------|--------|------|
| NVIDIA L40S | NVIDIA L40S 48GB | $3,500 | $2,500 | $4,000 | P1 |
| NVIDIA L4 | NVIDIA L4 24GB | $2,600 | $1,800 | $3,000 | P1 |
| NVIDIA T4 | NVIDIA T4 16GB | $450 | $300 | $550 | P2 |

### ECC Memory (4 items)

| Name | Search Keywords | Target | Scam Floor | Median | Tier |
|------|----------------|--------|------------|--------|------|
| 256GB DDR4-3200 ECC (8x32GB) | 32GB DDR4 3200 ECC RDIMM server | $480 | $320 | $560 | P2 |
| 512GB DDR4-3200 ECC (16x32GB) | 32GB DDR4 3200 ECC RDIMM server lot 16 | $960 | $640 | $1,120 | P2 |
| 256GB DDR4-2933 ECC (8x32GB) | 32GB DDR4 2933 ECC RDIMM server | $420 | $280 | $500 | P2 |
| 128GB DDR4-3200 ECC (4x32GB) | 32GB DDR4 3200 ECC RDIMM server lot 4 | $260 | $170 | $300 | P2 |

### NVMe Storage — U.2 (4 items)

| Name | Search Keywords | Target | Scam Floor | Median | Tier |
|------|----------------|--------|------------|--------|------|
| Intel Optane P5800X 1.6TB U.2 | Intel Optane P5800X 1.6TB | $920 | $650 | $1,100 | P1 |
| Intel Optane P4800X 750GB U.2 | Intel Optane P4800X 750GB | $360 | $250 | $420 | P1 |
| Samsung PM1733 7.68TB U.2 | Samsung PM1733 7.68TB | $880 | $600 | $1,000 | P2 |
| Kioxia CD6 7.68TB U.2 | Kioxia CD6 7.68TB | $720 | $500 | $820 | P2 |

### Enterprise HDDs 16TB+ (6 items)

| Name | Search Keywords | Target | Scam Floor | Median | Tier |
|------|----------------|--------|------------|--------|------|
| Seagate Exos X16 16TB | Seagate Exos X16 16TB SATA | $210 | $140 | $260 | P2 |
| Seagate Exos X18 18TB | Seagate Exos X18 18TB SATA | $260 | $175 | $310 | P2 |
| WD Ultrastar HC550 16TB | WD Ultrastar HC550 16TB | $200 | $130 | $250 | P2 |
| WD Ultrastar HC550 18TB | WD Ultrastar HC550 18TB | $240 | $160 | $290 | P2 |
| Toshiba MG08 16TB | Toshiba MG08ACA16TE 16TB | $190 | $125 | $240 | P3 |
| Toshiba MG09 18TB | Toshiba MG09ACA18TE 18TB | $230 | $155 | $280 | P3 |

### Chassis & Cooling (3 items)

| Name | Search Keywords | Target | Scam Floor | Median | Tier |
|------|----------------|--------|------------|--------|------|
| Supermicro 846E16-R1200B | Supermicro 846E16-R1200B | $650 | $400 | $800 | P2 |
| Noctua NH-U14S TR4-SP3 | Noctua NH-U14S TR4-SP3 | $85 | $55 | $100 | P3 |
| Arctic Freezer 4U-SP5 | Arctic Freezer 4U-SP5 | $70 | $45 | $85 | P3 |

### Networking (2 items)

| Name | Search Keywords | Target | Scam Floor | Median | Tier |
|------|----------------|--------|------------|--------|------|
| Mellanox ConnectX-5 100GbE | Mellanox ConnectX-5 MCX516A | $320 | $210 | $380 | P2 |
| Intel X710-DA4 10GbE SFP+ | Intel X710-DA4 10GbE | $180 | $120 | $220 | P2 |

### Power Supplies (2 items)

| Name | Search Keywords | Target | Scam Floor | Median | Tier |
|------|----------------|--------|------------|--------|------|
| Supermicro PWS-1K21P-1R 1200W | Supermicro PWS-1K21P-1R | $120 | $80 | $150 | P3 |
| Seasonic Prime TX-1600 | Seasonic Prime TX-1600 | $380 | $250 | $450 | P3 |

### Accessories (1 item)

| Name | Search Keywords | Target | Scam Floor | Median | Tier |
|------|----------------|--------|------------|--------|------|
| SlimSAS to U.2 Cable | SlimSAS 4i to U.2 cable | $25 | $15 | $32 | P3 |

---

## Scam Floor Methodology

Scam floors are set at approximately **55-65% of benchmark_median** based on component category:

| Category | Scam Floor Range | Rationale |
|----------|-----------------|-----------|
| CPUs | ~55% of median | High fraud risk, fakes exist |
| GPUs | ~60% of median | Very high fraud risk |
| Memory | ~57% of median | Moderate fraud risk |
| NVMe SSDs | ~60% of median | Counterfeit risk |
| HDDs | ~60% of median | Shucked drive risk |
| Motherboards | ~50% of median | DOA risk at very low prices |
| Networking | ~55% of median | Counterfeit risk |
| PSUs | ~55% of median | Safety risk with fakes |
| Chassis | ~50% of median | Shipping damage risk |
| Accessories | ~47% of median | Low fraud risk |

**Never set scam_floor below 40% of benchmark_median.** Anything lower catches legitimate bulk sellers.

---

## Priority Tier Assignment

| Tier | Interval | Count | Criteria |
|------|----------|-------|----------|
| P0 | 5 min | 4 | CPU, top GPU, critical motherboard |
| P1 | 10 min | 10 | Other GPUs, fast NVMe |
| P2 | 20 min | 12 | Memory, slower NVMe, HDDs, network |
| P3 | 30 min | 8 | Chassis, cooling, PSU, accessories, HDDs |

**Total API calls:** ~3,840/day (77% of 5,000 limit)

---

## Adding a New Item

### Step 1: Research the Item

1. Check current eBay sold listings for the last 30 days
2. Determine realistic median price (ignore extreme outliers)
3. Set target price at ~80% of median
4. Set scam_floor at 55-60% of median (see table above)
5. Write effective search keywords (specific enough to filter noise)

### Step 2: Add to `catalog.py`

```python
# In services/ebay/catalog.py, in the appropriate category list
CatalogItem(
    name="My New Component",
    search_keywords="specific search terms for ebay",
    ebay_category_id="12576",  # optional, look up eBay category
    target_price=Decimal("150.00"),
    scam_floor=Decimal("90.00"),
    benchmark_median=Decimal("200.00"),
    notes="Why this item, what to watch for",
)
```

### Step 3: Add to `seed_data_v2.sql`

```sql
INSERT INTO tracked_items (
    name, search_keywords, ebay_category_id, target_price,
    search_interval, is_active, scam_floor, benchmark_median, notes
) VALUES (
    'My New Component',
    'specific search terms for ebay',
    '12576',
    150.00,
    600,  -- interval in seconds (600=P1, 1200=P2, 1800=P3)
    true,
    90.00,
    200.00,
    'Why this item, what to watch for'
);
```

### Step 4: Recalculate API Usage

After adding an item, check if total daily calls still fit within the budget:

```
New item interval: X seconds
Daily calls added: 86400 / X
Current total + new item < 4800?  (leave 200 buffer)
```

If over budget, increase intervals for lower-priority items.

### Step 5: Test

```bash
make seed        # Load updated seed data
make logs service=backend  # Watch poller search the new item
```

---

## Catalog Auto-Suggest API

The Add Item Wizard uses `GET /catalog?q=search-term` to suggest items.

This endpoint searches the in-memory catalog (not the database) and returns matching items. It enables users to add tracked items without manually typing search keywords.

### Response Format

```json
[
  {
    "name": "AMD EPYC 7F72",
    "search_keywords": "AMD EPYC 7F72",
    "target_price": 1800.00,
    "scam_floor": 1200.00,
    "benchmark_median": 2200.00,
    "notes": "24-core, 192MB L3 cache"
  }
]
```

---

## Price Updates

Market prices change over time. To update pricing for all items:

1. Run pricing research (web search current sold listings)
2. Update `target_price`, `scam_floor`, and `benchmark_median` in both:
   - `catalog.py` (for runtime)
   - `seed_data_v2.sql` (for new installs)
3. For existing deployments, use the API:
   ```bash
   curl -X PUT http://localhost:8000/api/v1/items/1 \
     -H "Authorization: Bearer $TOKEN" \
     -d '{"target_price": 1900, "scam_floor": 1300, "benchmark_median": 2300}'
   ```

---

## Categories and eBay Category IDs

To find eBay category IDs for new items:
1. Go to eBay and browse to the category
2. The category ID is in the URL: `.../bn_1234567890`
3. Or use the eBay API Taxonomy API to look up

Common categories:
- CPUs/Processors: `164`
- Memory (RAM): `170083`
- Motherboards: "Computer Components": `175673"
- Hard Drives: "Hard Drives (HDD, SSD & NAS)": "56083"
- Graphics/Video Cards: `27386`
- Networking: `58261`
- Power Supplies: `42028`

If unsure, leave `ebay_category_id` as `None` — the keyword search is usually sufficient.
