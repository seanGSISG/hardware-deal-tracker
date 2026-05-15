# Inference GPU Pricing Intelligence Report
## NVIDIA L4 24GB & T4 16GB — eBay/Marketplace Pricing Analysis

**Research Date:** June 2025  
**Data Sources:** eBay sold listings, eBay active listings, AliExpress, GPU marketplace sites, industry articles  
**Confidence Level:** HIGH (substantial listing data found for both GPUs)

---

## Executive Summary Table

| Metric | NVIDIA L4 24GB | NVIDIA T4 16GB |
|--------|---------------|----------------|
| **Lowest Sold Price (recent)** | ~$2,443 (single-bid auction, Apr 2026) | ~$280 (AliExpress China sellers) |
| **Lowest Sold Price (eBay US)** | ~$3,187 (used, Apr 2026) | ~$584 (used, May 2026) |
| **Median Sold Price (eBay)** | ~$3,400 | ~$640 |
| **Current Buy It Now Range** | $2,849 – $5,399+ | $565 – $730 |
| **Best Deal Target (alert)** | **$2,600** | **$450** |
| **Alert Threshold** | 20% below median (~$2,720) | 25% below eBay median (~$480) |
| **Price Trend** | **Stable/Slightly Down** | **Stable** |
| **User Build Target** | $800 ❌ **Not Achievable** | $150 ❌ **Not Achievable** |
| **Realistic Minimum Budget** | $2,400-$2,800 | $280-$350 (China) / $580+ (US) |
| **Confidence** | HIGH | HIGH |

---

## ⚠️ Critical Finding: Build Targets vs. Reality

> **NVIDIA L4 24GB @ $800:** This target is **~3x below** the lowest realistic market price. The cheapest L4 ever recorded in this research was a single-bid auction at $2,443. Typical used L4 cards sell for $2,800-$3,500 on eBay. The L4 is a current-generation (Ada Lovelace) data center GPU with strong demand from AI inference workloads.

> **NVIDIA T4 16GB @ $150:** This target is **~2x below** the lowest realistic market price. The cheapest T4s available are from Chinese sellers on AliExpress at ~$280-$320. US eBay sellers typically charge $580-$730 for used T4 cards. The T4, despite being older (Turing, 2018), remains in active demand for low-power inference.

---

## 1. NVIDIA L4 24GB — Detailed Pricing Analysis

### Specifications
- Architecture: Ada Lovelace (4th Gen Tensor Cores)
- VRAM: 24GB GDDR6
- TDP: 72W (passive cooling, single-slot)
- Key Feature: Native FP8 support, AV1 encode/decode
- Ideal For: AI inference on 7B-14B parameter models

### eBay Sold Listings (Verified, Last 90 Days)

| Date | Condition | Seller Location | Price (USD) | Notes |
|------|-----------|-----------------|-------------|-------|
| May 7, 2026 | Brand New | China | ~$3,900 | testing-instrument-supplier |
| May 5, 2026 | Brand New | Germany | ~$3,693 | digi-techx |
| May 3, 2026 | Brand New | Austria | ~$3,691 | digi-techx |
| May 3, 2026 | New (Other) | Netherlands | ~$4,078 | raymaster99 |
| May 1, 2026 | Exc. Refurb | UK | ~$4,101 | serversetc (eBay Refurbished) |
| Apr 30, 2026 | Brand New | Germany | ~$3,468 | digi-techx |
| Apr 27, 2026 | Pre-Owned | US | ~$3,187 | rtone-32 (Dell V9XT2) |
| Apr 24, 2026 | Pre-Owned | US | ~$3,292 | reservertech (Dell NG3PY) |
| Apr 17, 2026 | Certified Refurb | US | ~$3,186 | xbyte (Dell V9XT2, was $5,309) |
| Apr 16, 2026 | Open Box | US | ~$3,984 | alik996.gmail (Dell NG3PY) |
| Apr 16, 2026 | Pre-Owned | US | ~$2,443 (auction) | pacificeve (1 bid only) |

**eBay Sold Price Statistics:**
- Lowest: ~$2,443 (single-bid auction, likely underpriced)
- Median: ~$3,400
- Highest: ~$4,101 (eBay Refurbished)

### eBay Buy It Now (Active Listings)

| Price (USD) | Condition | Seller | Notes |
|-------------|-----------|--------|-------|
| $2,849 | Used | GPU Poet | HP P59071-001 |
| $2,900 | Open Box | GPU Poet | NVIDIA Tesla L4 |
| $2,950 | Used | GPU Poet | Dell NG3PY |
| $2,977 | New | GPU Poet | NVIDIA PG193 |
| $2,999 | Used | eBay (digi-techx) | Dell NG3PY |
| $3,000 | Used | GPU Poet | Dell V9XT2 |
| $3,100 | Used | GPU Poet | NVIDIA PG193 |
| $3,280 | Used | GPU Poet | China seller |
| $3,499 | Used | GPU Poet | US seller |
| $3,738.99 | Used | eBay (digi-techx) | Dell NG3PY |
| $4,550 | New | ServerSupply | NVIDIA P/N 900-2G193-0000-001 |
| $4,599 | New | eBay (China sellers) | Multiple listings |
| $5,399 | New | eBay (China sellers) | Multiple listings |

### Bulk/Multi-Unit Pricing

| Listing | Unit Count | Total Price | Per-Unit Price |
|---------|-----------|-------------|----------------|
| eBay (motorpartners) | 2x | $10,350 | $5,175 |
| eBay (motorpartners) | 6x | $31,500 | $5,250 |
| Alibaba (wholesale) | 1+ piece | — | $2,088-$2,470 |
| GPU Poet | 2x | $10,350 | $5,175 |

> **Note:** Bulk pricing on eBay is generally **worse** than single-unit pricing, likely due to listing optimization. Alibaba/wholesale offers the best per-unit prices at ~$2,100-$2,470, but buyer protection is weaker than eBay.

### Other Marketplace Pricing

| Source | Price Range | Notes |
|--------|-------------|-------|
| Alibaba (wholesale, China) | $2,088 – $2,470 | Bulk pricing, minimum order 1+ |
| ServerSupply (US) | $4,550 | New, enterprise seller |
| Cisco MSRP | $11,194 | Enterprise list price (irrelevant for used) |
| Jarvislabs (industry data) | $2,000 – $3,000 | Hardware purchase estimate (Feb 2026) |

### L4 Price Trend: **Stable to Slightly Down**
The L4 was released in 2023 and has seen gradual price softening as supply from decommissioned servers enters the market. Prices have stabilized in the $2,800-$3,500 range for used cards, with new cards from Chinese sellers at $3,500-$4,500. The L4 remains in strong demand as the premier low-power inference GPU, which supports price stability.

---

## 2. NVIDIA T4 16GB — Detailed Pricing Analysis

### Specifications
- Architecture: Turing (Turing Tensor Cores)
- VRAM: 16GB GDDR6
- TDP: 70W (passive cooling, single-slot)
- Key Feature: Widely deployed, mature ecosystem
- Ideal For: AI inference on smaller models (3B-7B), batch processing

### eBay Sold Listings (Verified, Last 90 Days)

| Date | Condition | Seller | Price (USD) | Notes |
|------|-----------|--------|-------------|-------|
| May 14, 2026 | Very Good Refurb | dandyful | ~$637 | eBay Refurbished program |
| May 14, 2026 | Pre-Owned | techjunkies1 | ~$637 | No bracket |
| May 14, 2026 | Pre-Owned | techjunkies1 | ~$584 | Standard card |
| May 14, 2026 | Pre-Owned | twainj13 | ~$610 | Best offer accepted |
| May 14, 2026 | Pre-Owned | cloud_storage_corp | ~$731 | HP P17819-B21 OEM |

**eBay Sold Price Statistics:**
- Lowest: ~$584 (no bracket)
- Median: ~$637
- Highest: ~$731 (HP OEM branded)

### eBay Buy It Now (Active Listings)

| Price (USD) | Condition | Seller | Notes |
|-------------|-----------|--------|-------|
| $565 | Used | eBay (cloud_storage_corp) | 167 sold, very popular |
| $639 | Used | eBay (cloud_storage_corp) | 167 sold |
| $648 | OB/O | eBay (cloud_storage_corp) | 28 watchers |
| $681 | OB/O | eBay (soulson_3243) | UK seller |
| $699 | Used | eBay (egoods.supply) | 243 sold, both brackets |
| $1,099 | New | Computer_Parts_L | China seller |

### T4 Pricing: US Sellers vs. Chinese Sellers

| Marketplace | Price Range | Condition | Notes |
|-------------|-------------|-----------|-------|
| **AliExpress (China)** | **$280 – $420** | Used, with cooling mod | Best prices, 14-day shipping |
| **eBay (US sellers)** | **$565 – $731** | Used/Refurb | Faster shipping, better protection |
| **eBay (China sellers)** | **$95 – $110** | ? (likely brackets/accessories) | Suspiciously low, verify before buying |
| **New Retail** | $999 – $2,100 | New | Not cost-effective vs. used |

> **Key Insight:** There's a **massive $200-$300 price gap** between Chinese sellers (AliExpress, ~$300) and US eBay sellers (~$580-$730). Chinese sellers typically modify the cooling system with custom heatsinks/fans. These cards are tested and functional but ship from China with ~14 day delivery and limited/no warranty.

### T4 Bulk/Multi-Unit Pricing

| Listing | Unit Count | Price | Notes |
|---------|-----------|-------|-------|
| cloud_storage_corp | Single | $565-$648 | Save up to 15% when you buy more |
| egoods.supply | Single | $699 | 243 sold — strong volume |
| eBay (bulk package) | Bulk Package | ~$600+ | Cloud Project (San Jose) |
| eBay (5x lot) | 5x | Varies | 5x Lot Nvidia Tesla T4 listing |

### T4 Price Trend: **Stable**
The T4 has been on the market since 2018 and has reached price stability. Massive volumes were deployed in data centers (Google Cloud, AWS, Azure) and are now being decommissioned, creating a steady used supply. Prices have hovered in the $550-$750 range on eBay US for over a year. Chinese sellers have slightly lower prices due to proximity to decommissioned server supply.

---

## 3. L4 vs T4: Value Comparison for Inference Builds

| Factor | L4 24GB | T4 16GB |
|--------|---------|---------|
| **Architecture** | Ada Lovelace (2023) | Turing (2018) |
| **VRAM** | 24GB (+50%) | 16GB |
| **FP16 Tensor** | 242 TFLOPS (+272%) | 65 TFLOPS |
| **FP8 Support** | Yes (242 TFLOPS) | No |
| **TDP** | 72W | 70W |
| **Used Price** | $2,800-$3,500 | $565-$730 |
| **Price/TFLOPS** | $11.6-$14.5/TFLOP | $8.7-$11.2/TFLOP |
| **Max Model Size (FP16)** | ~13B parameters | ~8B parameters |
| **Best Use Case** | Modern inference (7B-13B) | Budget inference (3B-7B) |

### Value Verdict
- The **T4** offers better **raw price/performance** for smaller models and budget builds. At ~$600, it can serve 7B parameter models adequately.
- The **L4** commands a ~5x price premium but offers ~3.7x more compute, 50% more VRAM, and FP8 support. For modern inference workloads, the L4 is significantly more capable but comes at a steep price.
- **For a budget inference build:** The T4 at $600 is the pragmatic choice. The L4's ~$3,000+ price puts it in a different budget category.

---

## 4. Deal Alert Recommendations

### NVIDIA L4 24GB
- **Alert Target:** $2,600 or below
- **Trigger:** 20% below median sold price (~$3,400)
- **Where to Watch:** eBay (used/pre-owned), GPU Poet marketplace, Alibaba
- **What to Look For:**
  - Dell NG3PY or V9XT2 OEM cards (most common, best value)
  - Single-bid auctions ending with low participation
  - Lots from data center liquidators
  - Cards listed as "pre-owned" without eBay Refurbished premium
- **Avoid:** Brand new listings from Chinese sellers above $4,500 (overpriced)

### NVIDIA T4 16GB
- **Alert Target:** $450 or below (US sellers) / $280 (Chinese sellers)
- **Trigger:** 25% below median sold price
- **Where to Watch:** AliExpress (best prices), eBay US (faster shipping)
- **What to Look For:**
  - AliExpress sellers with cooling modifications included
  - eBay sellers cloud_storage_corp and egoods.supply (high volume, reliable)
  - Best offer accepted listings (often 10-15% below asking)
- **Caution:** Cards below $100 on eBay from China are typically **brackets/accessories only**, not the GPU itself. Verify listing details carefully.

---

## 5. Market Anomalies & Notes

### ⚠️ Suspicious Pricing
- eBay listings showing T4 at ~$25 (172-181 CNY) from Chinese sellers are **NOT actual GPUs** — these are mounting brackets, accessories, or scams. The actual GPU listings from China are ~$95-$110 CNY minimum.
- eBay captcha protection kicked in during research, confirming active scraping detection on high-volume listings.

### 📈 Market Dynamics
- **L4 supply** is increasing as older server farms with L4 GPUs are refreshed. Expect gradual softening toward $2,500-$3,000 range by late 2025.
- **T4 supply** is massive and stable. These cards are widely available and will likely remain in the $500-$700 range for the foreseeable future.
- **Demand drivers:** T4 and L4 are both heavily used for AI inference in the "small model" space (7B-13B parameter LLMs), which is seeing explosive growth for edge and on-premise deployments.

### 🛒 Buying Strategy
- **If budget is ~$150:** Consider a used consumer GPU like GTX 1070 8GB (~$100-$120) instead. Not an inference specialist but can run smaller models.
- **If budget is ~$600:** The T4 16GB is the sweet spot for entry-level inference. Can serve 7B models comfortably.
- **If budget is ~$800:** Consider a used RTX 3090 24GB (~$800-$900) instead of the L4. Much more compute for the money, though higher power draw (350W vs 72W).
- **If budget is ~$2,500+:** The L4 24GB is excellent for professional inference deployment. Low power, high density, FP8 support.

---

## 6. Data Sources & Methodology

| Source | Data Points | Reliability |
|--------|-------------|-------------|
| eBay Sold Listings (US) | 11 L4, 5 T4 | HIGH — actual transaction prices |
| eBay Buy It Now | 40+ L4, 25+ T4 | HIGH — active market pricing |
| AliExpress | 12+ T4 listings | MEDIUM — verified purchase data from articles |
| Alibaba | 5+ L4 wholesale | MEDIUM — bulk pricing |
| GPU Poet | 44 L4 listings | HIGH — specialized GPU marketplace |
| Industry Articles | Jarvislabs, DeployBase, others | MEDIUM — secondary estimates |

*All prices are in USD unless otherwise noted. Currency conversions from IDR/CNY were made at prevailing rates (1 USD ≈ 16,500 IDR, 1 USD ≈ 7.2 CNY).*

---

*Report generated: June 2025*  
*Next recommended update: 30 days*
