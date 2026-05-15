# REFINED SPEC.md — AI-Powered Enterprise Hardware Deal Tracker

> **Research-Enhanced Specification v1.1**  
> Based on original spec + market research (current pricing, eBay API 2025 changes, deal scoring algorithms, tech stack patterns)  
> **Date:** 2026-05-13

---

## 1. Project Overview

### 1.1 Mission
Build a self-hosted AI-assisted enterprise hardware tracking and valuation platform that continuously monitors eBay for enterprise/homelab hardware, builds historical pricing intelligence, detects unusually good deals using hybrid statistical + AI scoring, and notifies users through configurable alert channels.

### 1.2 Target Hardware Categories

| Category | Examples | Market Inefficiency |
|----------|----------|-------------------|
| Enterprise CPUs | AMD EPYC 7F72, 7443, 7452, 7543; Xeon Gold 6240, 6258R | Mislabeled, liquidation pricing |
| Server Motherboards | Supermicro H12SSL-CT, ASRock ROMED8-2T | Poor categorization, OEM confusion |
| Enterprise GPUs | RTX PRO 4000 Blackwell SFF, RTX 6000 Ada, L4, A2 | Workstation pulls, poorly titled |
| ECC Memory | Samsung M393A8G40MB2-CVF, Micron MTA36ASF8G72PZ | Bulk lots, speed mismatches |
| Enterprise Storage | Intel P5510, Micron 7450, Samsung PM9A3 (U.2) | Underpriced pulls, condition issues |
| Networking | Mellanox ConnectX-4/5, Intel X710 | Liquidation, poorly described |
| Rackmount Chassis | SilverStone RM52, RM44 | Niche market, limited listings |

### 1.3 Market Inefficiencies Addressed

- **Mispriced listings**: Seller doesn't know true market value
- **Poor categorization**: Listed in wrong eBay category
- **Poor titles**: "AMD SERVER CPU 24 CORE" instead of "AMD EPYC 7F72"
- **Liquidation**: Datacenter pulls at fire-sale prices
- **Bulk lots**: Multi-unit discounts below per-unit market price
- **OEM/vendor confusion**: "For Dell only" creating false negatives
- **Rapid fluctuations**: Time-sensitive price drops

### 1.4 Current Market Benchmarks (May 2026)

| Item | Price Range (Used) | "Deal" Threshold | Data Source |
|------|-------------------|-----------------|-------------|
| AMD EPYC 7F72 | $280 - $400 | Under $260 | eBay sold listings |
| Samsung 64GB DDR4-2933 ECC (M393A8G40MB2-CVF) | $128 - $172 | Under $115 | eBay + ServerSupply |
| Supermicro H12SSL-CT | $55 - $1,400 | Under $350 | eBay (massive spread) |
| NVIDIA T4 | $150 - $250 | Under $130 | eBay sold |
| Intel P5510 1.92TB U.2 | $80 - $150 | Under $70 | eBay sold |
| Mellanox ConnectX-4 | $25 - $80 | Under $20 | eBay sold |
| SilverStone RM52 Chassis | $300 - $450 | Under $260 | eBay new/used |

### 1.5 Vision
Self-hosted "AI arbitrage agent" for enterprise hardware markets — lightweight market intelligence platform, not a simple price alert tool.

---

## 2. MVP Feature Set

### 2.1 Must-Have (MVP)

| # | Feature | Phase | Owner |
|---|---------|-------|-------|
| 1 | eBay Browse API ingestion | Phase 3 | eBay agent |
| 2 | Historical price tracking (30/90/180 day) | Phase 4 | Scoring agent |
| 3 | Saved tracked hardware SKUs/items | Phase 2 | Backend agent |
| 4 | Price drop alerts (absolute + %) | Phase 2 + 5 | Backend + Notifications |
| 5 | Rules-based deal scoring engine (0-100) | Phase 4 | Scoring agent |
| 6 | Full n8n workflow orchestration | Phase 7 | n8n agent |
| 7 | Frontend dashboard with charts | Phase 6 | Frontend agents |
| 8 | Telegram real-time notifications | Phase 5 | Notifications agent |
| 9 | Email digest (hourly/daily) | Phase 5 | Notifications agent |
| 10 | PostgreSQL backend with pgvector | Phase 1 | Database agent |
| 11 | Self-hosted Docker Compose deployment | Phase 8 | Deploy agent |
| 12 | JWT authentication | Phase 2 | Backend agent |

### 2.2 Nice-to-Have (Future Phases)

| # | Feature | Priority |
|---|---------|----------|
| 1 | AI listing normalization (OpenRouter) | P1 |
| 2 | Deal classification (liquidation, mislabel, scam risk) | P1 |
| 3 | Multi-marketplace (Facebook, Craigslist, Jawa.gg) | P2 |
| 4 | Price prediction (ML-based forecasting) | P2 |
| 5 | OCR for listing images | P3 |
| 6 | Seller reputation scoring | P3 |
| 7 | AI-generated deal summaries | P3 |
| 8 | Automated bidding recommendations | P3 |
| 9 | Hardware lifecycle analytics | P4 |

---

## 3. Tech Stack (Finalized)

### 3.1 Core Stack

| Layer | Technology | Version | Justification |
|-------|-----------|---------|---------------|
| Workflow Engine | n8n | 1.80+ (self-hosted) | 400+ integrations, 70 AI nodes, visual editor, free self-hosted |
| Backend API | FastAPI | 0.115+ | Async native, Pydantic v2, OpenAPI auto-gen, SQLAlchemy 2.0 compatible |
| Database | PostgreSQL | 17+ | JSON support, time-series friendly, pgvector for embeddings |
| DB Driver | asyncpg | 0.30+ | Fastest async PostgreSQL driver |
| ORM | SQLAlchemy 2.0 | 2.0+ | Full async support, DeclarativeBase, type hints |
| Migrations | Alembic | 1.14+ | SQLAlchemy-native, async support |
| Cache/Queue | Redis | 7+ | Rate limiting, pub/sub for notifications, dedup cache |
| Frontend | Next.js | 15+ (App Router) | React 19, SSR/CSR hybrid, API routes |
| Styling | Tailwind CSS | 4.0+ | Utility-first, shadcn/ui compatible |
| Components | shadcn/ui | latest | Accessible, customizable primitives |
| Charts | Recharts | 2.15+ | React-native, responsive |
| Icons | Lucide React | latest | Consistent, lightweight |

### 3.2 External Services

| Service | Purpose | Cost Model |
|---------|---------|-----------|
| eBay Browse API | Marketplace data | 5,000 calls/day free tier |
| OpenRouter | AI listing normalization + classification | Pay-per-token (~$0.20-0.50 per 1K items) |
| Telegram Bot API | Push notifications | Free |
| SMTP (Gmail/SES) | Email digests | Free tier available |

### 3.3 AI/ML Approach

**Phase 1 (MVP): Rules-based + Statistical**
- Z-Score price anomaly detection
- Rolling median/average comparison
- Seller feedback scoring
- Shipping cost factor
- Market volatility adjustment

**Phase 2 (Post-MVP): AI-Enhanced**
- OpenRouter for listing title normalization
- Classification: liquidation, mislabel, bulk, scam risk
- Hybrid: ZID voting (Z-Score + Isolation Forest + DBSCAN)

---

## 4. eBay Browse API Integration (Critical: Updated for 2025)

### 4.1 API Selection

**ONLY the eBay Browse API is used.** The Finding API was decommissioned February 2025.

| API | Status | Limit |
|-----|--------|-------|
| Browse API (Buy APIs) | **ACTIVE** | 5,000 calls/day |
| Finding API | **DECOMMISSIONED** | N/A |

### 4.2 Key Endpoints

```
GET https://api.ebay.com/buy/browse/v1/item_summary/search
  ?q={keywords}
  &category_ids={category_id}
  &filter=buyingOptions:{FIXED_PRICE|AUCTION}
  &filter=price:[min..max],priceCurrency:USD
  &filter=conditionIds:{3000|4000|5000}  (3000=Used, 4000=Very Good, 5000=Good)
  &filter=deliveryCountry:US
  &sort=-itemEndDate
  &limit=200
  &offset=0
```

### 4.3 Rate Limiting Strategy

| Constraint | Value | Mitigation |
|------------|-------|------------|
| Daily call limit | 5,000 | Redis counter with daily reset |
| Max results per query | 10,000 | Use narrow keyword filters |
| OAuth token (client_credentials) | 1,000/day | Cache tokens, use until expiry |
| Result set max | 200 per page | Paginate with offset |

### 4.4 Production Access Requirements

> **IMPORTANT:** eBay Buy APIs require production approval. Must complete:
> 1. Join eBay Developers Program (free)
> 2. Complete Application Growth Check
> 3. Sign additional contract for Buy API access

**Development workaround:** Mock eBay client with sample data for testing.

### 4.5 eBay Category IDs for Enterprise Hardware

| Category | eBay Category ID |
|----------|-----------------|
| CPUs/Processors | 164 (Computer Components) → subcategory |
| Server Memory (RAM) | 170083 (Memory RAM) |
| Motherboards | 1244 (Motherboards) |
| Graphics Cards | 27386 (Graphics Cards) |
| Enterprise Networking | 51167 (Enterprise Networking) |
| Hard Drives | 56083 (Hard Drives HDD SDD) |
| Computer Cases | 42014 (Computer Cases) |

### 4.6 Polling Schedule

| Tracked Item Count | Poll Interval | Calls per Day |
|-------------------|---------------|---------------|
| 1-10 | 5 minutes | ~2,880 |
| 11-25 | 5 minutes | ~7,200 (exceeds limit) |
| 11-25 | 10 minutes | ~3,600 |
| 26-50 | 15 minutes | ~4,800 |
| 50+ | 30 minutes | ~2,400 |

**Strategy:** Rotate through tracked items, don't poll all simultaneously.

---

## 5. Deal Scoring Engine (Rules-Based MVP)

### 5.1 Scoring Algorithm: Hybrid Statistical

Based on research (ZID voting system achieves 97.1% precision):

```
DEAL_SCORE = weighted_average(
  price_zscore_component,      # 30% weight
  historical_discount_component, # 25% weight
  seller_quality_component,    # 15% weight
  listing_quality_component,   # 15% weight
  market_timing_component,     # 10% weight
  bulk_discount_component      # 5% weight
)
```

### 5.2 Component Details

**1. Price Z-Score (30%)**
```python
z_score = (listing_price - historical_mean) / historical_stddev
score = clamp(100 - (z_score * 20), 0, 100)  # lower price = higher score
```

**2. Historical Discount (25%)**
```python
discount_pct = (median_price - listing_price) / median_price
score = clamp(discount_pct * 100, 0, 100)
# >50% discount = 100 points
# 30% discount = 60 points
# 10% discount = 20 points
```

**3. Seller Quality (15%)**
```python
score = seller_feedback_score / 100 * seller_positive_pct
# >1000 feedback + 99%+ positive = 100 points
# 100-1000 feedback + 98%+ positive = 80 points
# <100 feedback or <95% positive = 40 points
```

**4. Listing Quality (15%)**
```python
# Penalties:
# - Missing photos: -20
# - Poor description: -15
# - "For Dell/HP only": -30 (OEM lock risk)
# - "Untested": -20
# - "As-is": -25
# - Free returns: +10
```

**5. Market Timing (10%)**
```python
# Based on price volatility
time_score = 50  # neutral
if price_dropping_7d:
    time_score += 30
if price_volatile:
    time_score += 20
```

**6. Bulk Discount (5%)**
```python
if quantity > 1:
    per_unit_price = total_price / quantity
    bulk_discount = (median_single - per_unit_price) / median_single
    score = min(bulk_discount * 100 * 1.5, 100)  # 1.5x multiplier
```

### 5.3 Confidence Score

```python
confidence = base_confidence(30%) + data_points_bonus(5% per 10 data points, max 40%) + recency_bonus(30% if data within 7 days)
```

### 5.4 Thresholds

| Deal Score | Classification | Action |
|------------|---------------|--------|
| 0-30 | Poor deal | No action |
| 30-50 | Fair deal | Log only |
| 50-70 | Good deal | Email digest |
| 70-85 | Great deal | Telegram alert |
| 85-100 | Hot deal | Instant Telegram + email |

---

## 6. Notification System

### 6.1 Telegram (Instant)

**Message format:**
```
🔥 DEAL ALERT — Score: 87/100

📦 {listing_title}
💰 Price: ${price} (Est. value: ${fair_value})
📉 Discount: {discount_pct}% below median
🏪 Seller: {seller_name} ({feedback_score} | {positive_pct}%)
📍 Shipping: ${shipping_cost}
🔗 {listing_url}

📊 Historical: ${median_30d} (30d median)
📊 Lowest seen: ${lowest_price}
```

### 6.2 Email Digest

| Mode | Schedule | Content |
|------|----------|---------|
| Instant | Immediate | Single deal with full details |
| Hourly | Top of hour | All deals from past hour (top 10) |
| Daily | 8:00 AM | Full market summary, all deals (top 20) |

---

## 7. Database Schema (Complete)

### 7.1 Core Tables

**`tracked_items`**
```sql
id              SERIAL PRIMARY KEY
name            VARCHAR(255) NOT NULL          -- "AMD EPYC 7F72"
keywords        TEXT NOT NULL                   -- search keywords
sku             VARCHAR(100)                    -- manufacturer SKU
mpn             VARCHAR(100)                    -- manufacturer part number
category_id     VARCHAR(20)                     -- eBay category ID
marketplace     VARCHAR(20) DEFAULT 'ebay'      -- ebay, amazon, etc.
target_price    DECIMAL(10,2)                   -- user's desired price
alert_threshold DECIMAL(5,2) DEFAULT 0.20       -- 0.20 = alert at 20% below median
min_deal_score  INTEGER DEFAULT 50              -- minimum score to alert
is_enabled      BOOLEAN DEFAULT true
created_at      TIMESTAMPTZ DEFAULT NOW()
updated_at      TIMESTAMPTZ DEFAULT NOW()
last_searched   TIMESTAMPTZ                     -- last time we polled for this item
search_interval INTEGER DEFAULT 300             -- seconds between searches (min 300)
```

**`listings`**
```sql
id              SERIAL PRIMARY KEY
marketplace_id  VARCHAR(50) NOT NULL UNIQUE     -- eBay itemId
tracked_item_id INTEGER REFERENCES tracked_items(id)
title           VARCHAR(500) NOT NULL
normalized_title VARCHAR(500)
price           DECIMAL(10,2) NOT NULL
shipping        DECIMAL(10,2) DEFAULT 0
seller          VARCHAR(200) NOT NULL
seller_feedback INTEGER DEFAULT 0
seller_positive_pct DECIMAL(5,2) DEFAULT 100.0
condition       VARCHAR(50)                     -- Used, New, etc.
condition_id    VARCHAR(20)                     -- eBay condition ID
category_id     VARCHAR(20)
url             TEXT NOT NULL
image_url       TEXT
is_auction      BOOLEAN DEFAULT false
quantity        INTEGER DEFAULT 1
buying_options  VARCHAR(100)[]                  -- ["FIXED_PRICE"] or ["AUCTION"]
listing_date    TIMESTAMPTZ NOT NULL            -- when listing was created
end_date        TIMESTAMPTZ                     -- auction end date
is_deduped      BOOLEAN DEFAULT false
raw_data        JSONB                           -- full eBay response for debugging
created_at      TIMESTAMPTZ DEFAULT NOW()
```

**`price_history`**
```sql
id              SERIAL PRIMARY KEY
listing_id      INTEGER REFERENCES listings(id)
tracked_item_id INTEGER REFERENCES tracked_items(id)
observed_price  DECIMAL(10,2) NOT NULL
shipping        DECIMAL(10,2) DEFAULT 0
total_price     DECIMAL(10,2) NOT NULL          -- price + shipping
timestamp       TIMESTAMPTZ DEFAULT NOW()
```

**`listing_scores`**
```sql
id              SERIAL PRIMARY KEY
listing_id      INTEGER REFERENCES listings(id)
tracked_item_id INTEGER REFERENCES tracked_items(id)
overall_score   INTEGER NOT NULL                -- 0-100
deal_score      INTEGER NOT NULL                -- 0-100
confidence      DECIMAL(5,2) NOT NULL           -- 0.00-1.00
classification  VARCHAR(50)                     -- "hot_deal", "good_deal", "fair", "poor"
price_zscore    DECIMAL(8,4)                    -- statistical z-score
vs_median_pct   DECIMAL(8,4)                    -- % vs median (-0.30 = 30% below)
vs_lowest_pct   DECIMAL(8,4)                    -- % vs lowest seen
est_fair_value  DECIMAL(10,2)                   -- AI-estimated fair value
scored_at       TIMESTAMPTZ DEFAULT NOW()
```

**`alerts`**
```sql
id              SERIAL PRIMARY KEY
listing_id      INTEGER REFERENCES listings(id)
tracked_item_id INTEGER REFERENCES tracked_items(id)
score_id        INTEGER REFERENCES listing_scores(id)
channel         VARCHAR(20) NOT NULL            -- "telegram", "email"
alert_type      VARCHAR(20) NOT NULL            -- "instant", "digest", "threshold"
was_sent        BOOLEAN DEFAULT false
sent_at         TIMESTAMPTZ
template_used   VARCHAR(50)                     -- template identifier
telegram_msg_id VARCHAR(100)                    -- Telegram message ID
error_message   TEXT
created_at      TIMESTAMPTZ DEFAULT NOW()
```

**`notification_settings`**
```sql
id              SERIAL PRIMARY KEY
user_id         INTEGER REFERENCES users(id)
telegram_chat_id VARCHAR(100)
telegram_enabled BOOLEAN DEFAULT true
email_address   VARCHAR(255)
email_enabled   BOOLEAN DEFAULT true
email_digest_mode VARCHAR(20) DEFAULT 'daily'   -- instant, hourly, daily
telegram_min_score INTEGER DEFAULT 70
email_min_score  INTEGER DEFAULT 50
mute_until      TIMESTAMPTZ
created_at      TIMESTAMPTZ DEFAULT NOW()
updated_at      TIMESTAMPTZ DEFAULT NOW()
```

**`users`**
```sql
id              SERIAL PRIMARY KEY
username        VARCHAR(100) NOT NULL UNIQUE
email           VARCHAR(255) NOT NULL UNIQUE
hashed_password VARCHAR(255) NOT NULL
is_active       BOOLEAN DEFAULT true
is_admin        BOOLEAN DEFAULT false
created_at      TIMESTAMPTZ DEFAULT NOW()
updated_at      TIMESTAMPTZ DEFAULT NOW()
```

### 7.2 Indexes

```sql
CREATE INDEX idx_listings_marketplace_id ON listings(marketplace_id);
CREATE INDEX idx_listings_tracked_item ON listings(tracked_item_id);
CREATE INDEX idx_listings_price ON listings(price);
CREATE INDEX idx_listings_created ON listings(created_at);
CREATE INDEX idx_price_history_tracked_item ON price_history(tracked_item_id);
CREATE INDEX idx_price_history_timestamp ON price_history(timestamp);
CREATE INDEX idx_scores_listing ON listing_scores(listing_id);
CREATE INDEX idx_scores_overall ON listing_scores(overall_score DESC);
CREATE INDEX idx_alerts_pending ON alerts(was_sent) WHERE was_sent = false;
CREATE INDEX idx_alerts_created ON alerts(created_at);
```

---

## 8. n8n Workflows (4 Core Workflows)

### 8.1 Workflow 1: Marketplace Poller

```
Trigger: Cron (every 5 minutes)
  |
  ├── PostgreSQL: Get enabled tracked_items with last_searched + interval < NOW
  |
  ├── HTTP Request: Call backend /api/v1/search/trigger/{item_id}
  |
  ├── Backend: eBay Browse API search → normalize → dedup → store
  |
  └── PostgreSQL: Update last_searched timestamp
```

### 8.2 Workflow 2: Deal Scorer

```
Trigger: Webhook (called by backend after new listings stored)
  |
  ├── HTTP Request: Call backend /api/v1/deals/score/{listing_id}
  |
  ├── Backend: Calculate statistics, apply scoring rules, store score
  |
  ├── IF: score >= notification_settings.min_score
  |   └── HTTP Request: Call Workflow 3 webhook
  |
  └── PostgreSQL: Record score
```

### 8.3 Workflow 3: Notification Router

```
Trigger: Webhook (called by Workflow 2)
  |
  ├── PostgreSQL: Get notification settings
  |
  ├── IF: telegram_enabled AND score >= telegram_min_score
  |   ├── Build Telegram payload
  |   └── Telegram: send message
  |
  ├── IF: email_enabled AND score >= email_min_score
  |   ├── Add to pending email digest OR send instant
  |   └── Email: send (via SMTP)
  |
  └── PostgreSQL: Record alert sent
```

### 8.4 Workflow 4: Daily Analytics

```
Trigger: Cron (daily at 8:00 AM)
  |
  ├── PostgreSQL: Generate market summary
  |   ├── Price trends per tracked_item
  |   ├── Deal count and quality distribution
  |   ├── Market volatility indicators
  |   └── New listings count
  |
  ├── Code: Format daily digest
  |
  ├── IF: email digest subscribers > 0
  |   └── Email: Send daily summary
  |
  └── PostgreSQL: Store analytics snapshot
```

---

## 9. API Specification (Complete)

### 9.1 Authentication

```
POST /api/v1/auth/register
  Body: { username, email, password }
  Response: { access_token, token_type: "bearer" }

POST /api/v1/auth/login
  Body: { username, password }
  Response: { access_token, token_type: "bearer" }

GET /api/v1/me
  Headers: Authorization: Bearer {token}
  Response: { id, username, email, is_admin }
```

### 9.2 Tracked Items

```
GET /api/v1/items?page=1&per_page=20&enabled=true
  Response: { items: [...], total, page, per_page }

POST /api/v1/items
  Body: { name, keywords, sku?, mpn?, category_id?, target_price?, alert_threshold? }
  Response: { ...item object... }

GET /api/v1/items/{id}
  Response: { ...item with stats: { median_30d, lowest_30d, listing_count } }

PUT /api/v1/items/{id}
  Body: { name?, keywords?, target_price?, alert_threshold?, is_enabled?, search_interval? }
  Response: { ...updated item... }

DELETE /api/v1/items/{id}
  Response: 204 No Content
```

### 9.3 Listings

```
GET /api/v1/listings?item_id=&page=1&per_page=50&sort=newest
  Response: { listings: [...], total, page }

GET /api/v1/listings/{id}
  Response: { ...listing with score, price history }
```

### 9.4 Price History

```
GET /api/v1/history/{item_id}?days=30
  Response: { data_points: [{ date, avg_price, min_price, max_price, count }, ...] }

GET /api/v1/history/stats/{item_id}
  Response: {
    median_7d, median_30d, median_90d,
    lowest_ever, lowest_30d,
    highest_30d,
    volatility_30d,
    total_listings_30d,
    active_listings
  }
```

### 9.5 Deals

```
GET /api/v1/deals?min_score=50&max_score=100&item_id=&page=1
  Response: { deals: [{ ...listing, score: {...} }], total }

GET /api/v1/deals/{id}
  Response: { ...listing with full score breakdown }
```

### 9.6 Alerts

```
GET /api/v1/alerts?page=1&per_page=20&channel=&sent=
  Response: { alerts: [...], total }

PUT /api/v1/alerts/{id}/read
  Response: { ...updated alert... }
```

### 9.7 Settings

```
GET /api/v1/settings/notifications
  Response: { telegram_enabled, telegram_chat_id, email_address, email_digest_mode, ... }

PUT /api/v1/settings/notifications
  Body: { telegram_enabled?, email_digest_mode?, telegram_min_score?, ... }
  Response: { ...updated settings... }
```

### 9.8 Search / Trigger

```
POST /api/v1/search/trigger/{item_id}
  Response: { listings_found, new_listings, duplicates_skipped, duration_ms }

POST /api/v1/search/trigger-all
  Response: { items_processed, total_listings, total_new, total_duplicates }
```

---

## 10. Initial Seed Data

### 10.1 Default Tracked Items

```sql
INSERT INTO tracked_items (name, keywords, sku, mpn, category_id, target_price, alert_threshold, search_interval) VALUES
('AMD EPYC 7F72', 'AMD EPYC 7F72 server CPU processor', '100-000000336', '7F72', '164', 300.00, 0.25, 300),
('AMD EPYC 7443', 'AMD EPYC 7443 server CPU processor', '100-000000343', '7443', '164', 400.00, 0.20, 300),
('AMD EPYC 7452', 'AMD EPYC 7452 server CPU processor', '100-000000080', '7452', '164', 350.00, 0.20, 300),
('AMD EPYC 7543', 'AMD EPYC 7543 server CPU processor', '100-000000345', '7543', '164', 500.00, 0.20, 300),
('Xeon Gold 6240', 'Intel Xeon Gold 6240 server CPU processor', 'CD8069504284003', '6240', '164', 150.00, 0.25, 300),
('Xeon Gold 6258R', 'Intel Xeon Gold 6258R server CPU processor', 'CD8069504449800', '6258R', '164', 300.00, 0.20, 300),
('Supermicro H12SSL-CT', 'Supermicro H12SSL-CT motherboard SP3 EPYC', 'MBD-H12SSL-CT-O', 'H12SSL-CT', '1244', 400.00, 0.30, 600),
('ASRock ROMED8-2T', 'ASRock Rack ROMED8-2T motherboard SP3', 'ROMED8-2T', 'ROMED8-2T', '1244', 500.00, 0.25, 600),
('Gigabyte MZ32-AR0', 'Gigabyte MZ32-AR0 motherboard SP3 EPYC', 'MZ32-AR0', 'MZ32-AR0', '1244', 450.00, 0.25, 600),
('RTX PRO 4000 Blackwell SFF', 'NVIDIA RTX PRO 4000 Blackwell SFF workstation GPU', '900-5G173-2550-000', 'RTX PRO 4000', '27386', 800.00, 0.20, 600),
('RTX 6000 Ada', 'NVIDIA RTX 6000 Ada workstation GPU', '900-5G133-2500-000', 'RTX 6000 Ada', '27386', 2500.00, 0.15, 600),
('NVIDIA L4', 'NVIDIA L4 GPU inference accelerator', '900-2G193-0000-000', 'L4', '27386', 800.00, 0.20, 600),
('NVIDIA T4', 'NVIDIA T4 GPU inference accelerator', '900-2G183-0000-000', 'T4', '27386', 130.00, 0.25, 300),
('Samsung 64GB DDR4-2933 ECC', 'Samsung M393A8G40MB2-CVF 64GB DDR4 ECC RDIMM server memory', 'M393A8G40MB2-CVF', 'M393A8G40MB2-CVF', '170083', 115.00, 0.25, 300),
('Samsung 64GB DDR4-3200 ECC', 'Samsung M393A8G40AB2-CWE 64GB DDR4 ECC RDIMM server memory', 'M393A8G40AB2-CWE', 'M393A8G40AB2-CWE', '170083', 120.00, 0.25, 300),
('Micron 64GB DDR4-2933 ECC', 'Micron MTA36ASF8G72PZ-2G9 64GB DDR4 ECC RDIMM server memory', 'MTA36ASF8G72PZ-2G9', 'MTA36ASF8G72PZ-2G9', '170083', 110.00, 0.25, 300),
('Hynix 64GB DDR4-2933 ECC', 'SK Hynix HMAA8GR7AJR4N-WM 64GB DDR4 ECC RDIMM server memory', 'HMAA8GR7AJR4N-WM', 'HMAA8GR7AJR4N-WM', '170083', 110.00, 0.25, 300),
('Intel P5510 1.92TB', 'Intel P5510 1.92TB U.2 NVMe enterprise SSD', 'SSDPE2KX019T801', 'P5510', '56083', 80.00, 0.25, 600),
('Samsung PM9A3 1.92TB', 'Samsung PM9A3 1.92TB U.2 NVMe enterprise SSD', 'MZQL21T9HCJR', 'PM9A3', '56083', 85.00, 0.25, 600),
('Mellanox ConnectX-4', 'Mellanox ConnectX-4 25GbE SFP28 network adapter', 'MCX4111A-ACAT', 'ConnectX-4', '51167', 25.00, 0.30, 600),
('Mellanox ConnectX-5', 'Mellanox ConnectX-5 25GbE SFP28 network adapter', 'MCX512A-ACAT', 'ConnectX-5', '51167', 45.00, 0.25, 600),
('SilverStone RM52', 'SilverStone RM52 5U rackmount chassis server case', 'SST-RM52', 'RM52', '42014', 280.00, 0.20, 1200);
```

### 10.2 Default Admin User

```sql
INSERT INTO users (username, email, hashed_password, is_admin) VALUES
('admin', 'admin@localhost', '$2b$12$...hash...', true);
```

---

## 11. Docker Compose Services

```yaml
# See PHASE_08.md for complete docker-compose.yml
# Key services:
# - frontend (Next.js)    → port 3000
# - backend (FastAPI)     → port 8000
# - postgres (PostgreSQL) → port 5432
# - redis (Redis)         → port 6379
# - n8n (Workflow engine) → port 5678
```

---

## 12. File Structure

```
hardware-deal-tracker/
├── docker-compose.yml
├── .env.example
├── Makefile
├── README.md
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py
│   │   │   └── security.py
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── session.py
│   │   │   └── base.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── tracked_item.py
│   │   │   ├── listing.py
│   │   │   ├── price_history.py
│   │   │   ├── listing_score.py
│   │   │   ├── alert.py
│   │   │   └── notification_setting.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── tracked_item.py
│   │   │   ├── listing.py
│   │   │   ├── price_history.py
│   │   │   ├── deal.py
│   │   │   ├── alert.py
│   │   │   └── settings.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── deps.py
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       ├── endpoints/
│   │   │       │   ├── __init__.py
│   │   │       │   ├── auth.py
│   │   │       │   ├── items.py
│   │   │       │   ├── listings.py
│   │   │       │   ├── history.py
│   │   │       │   ├── deals.py
│   │   │       │   ├── alerts.py
│   │   │       │   ├── settings.py
│   │   │       │   └── search.py
│   │   │       └── router.py
│   │   └── services/
│   │       ├── __init__.py
│   │       ├── ebay/
│   │       │   ├── __init__.py
│   │       │   ├── client.py
│   │       │   ├── parser.py
│   │       │   ├── poller.py
│   │       │   ├── dedup.py
│   │       │   └── mock.py
│   │       ├── scoring/
│   │       │   ├── __init__.py
│   │       │   ├── engine.py
│   │       │   ├── historical.py
│   │       │   └── normalizer.py
│   │       └── notifications/
│   │           ├── __init__.py
│   │           ├── telegram.py
│   │           ├── email.py
│   │           ├── templates.py
│   │           └── dispatcher.py
│   ├── alembic/
│   │   ├── versions/
│   │   ├── env.py
│   │   └── alembic.ini
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_auth.py
│   │   ├── test_items.py
│   │   ├── test_listings.py
│   │   ├── test_scoring.py
│   │   └── test_notifications.py
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── requirements.txt
├── frontend/
│   ├── app/
│   ├── components/
│   ├── lib/
│   ├── public/
│   ├── Dockerfile
│   └── package.json
├── workflows/
│   ├── marketplace-poller.json
│   ├── deal-scorer.json
│   ├── notification-router.json
│   └── daily-analytics.json
└── scripts/
    ├── init-db.sh
    ├── seed-data.sql
    └── healthcheck.sh
```

---

## 13. Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | - | PostgreSQL async connection string |
| `SECRET_KEY` | Yes | - | JWT signing key (min 32 chars) |
| `EBAY_APP_ID` | For prod | - | eBay OAuth app ID |
| `EBAY_CERT_ID` | For prod | - | eBay OAuth cert ID |
| `EBAY_DEV_ID` | For prod | - | eBay developer ID |
| `EBAY_REDIRECT_URI` | For prod | - | OAuth redirect URI |
| `OPENROUTER_API_KEY` | No | - | AI inference key |
| `OPENROUTER_MODEL` | No | mistralai/mistral-small-3.1-24b-instruct | Default model |
| `TELEGRAM_BOT_TOKEN` | No | - | Telegram bot token |
| `TELEGRAM_CHAT_ID` | No | - | Default chat ID |
| `SMTP_HOST` | No | - | Email server host |
| `SMTP_PORT` | No | 587 | Email server port |
| `SMTP_USER` | No | - | SMTP username |
| `SMTP_PASSWORD` | No | - | SMTP password |
| `REDIS_URL` | Yes | redis://redis:6379/0 | Redis connection |
| `N8N_WEBHOOK_URL` | No | http://n8n:5678/webhook | n8n webhook base URL |
| `USE_MOCK_EBAY` | No | true (dev) / false (prod) | Use mock eBay client |
| `LOG_LEVEL` | No | INFO | Application log level |
| `FRONTEND_URL` | No | http://localhost:3000 | CORS origin |
| `BACKEND_PORT` | No | 8000 | FastAPI port |
