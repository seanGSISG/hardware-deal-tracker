# Hardware Deal Tracker — Price Validation Report

**Date:** 2026-05-16
**Method:** 8 parallel research agents scanning eBay sold listings, Buy It Now prices, and bulk lot data
**Build:** EPYC 7F72 + H12SSL-CT + RTX PRO 6000 Blackwell Homelab

---

## Executive Summary

| Metric | Value |
|--------|-------|
| Total tracked items | 34 (28 original + 6 new HDDs) |
| Original build target | $13,135 |
| Validated build target | $24,707 |
| Target adjustment | +$11,572 (+88%) |
| Items at/close to original target | 6 |
| Items requiring moderate adjustment | 9 |
| Items requiring major adjustment | 12 |
| New items added (HDD 16TB+) | 6 |

### Key Insights

1. **EPYC 7F72 CPU target is realistic** ($300→$325) — abundant China supply
2. **Motherboards cost 60% more than planned** ($950→$1,550) — H12SSL-CT and ROMED8-2T both risen
3. **Workstation GPUs are the biggest delta** ($8,200→$12,050) — RTX PRO 6000 too new for used, RTX 6000 Ada holds value
4. **Inference GPUs (L4/T4) are 3x more expensive** than planned — strong AI demand keeps prices high
5. **U.2 NVMe SSDs cost 5x more** than planned — enterprise SSDs hold value, no used fire sales
6. **ECC memory targets are close** ($590→$615) — best deals via Reddit bulk lots and China sellers
7. **Corsair HX1500i beats target** ($350→$250) — prices softening, open-box deals common
8. **Networking (ConnectX) targets achievable** ($280→$630 for all 3) — China sellers 30-50% cheaper
9. **16TB used HDDs: $15-18/TB floor** — WD HC550 18TB offers best $/TB usable for RAIDZ2
10. **DDR4 ECC prices RISING** — buy memory sooner rather than later (+10-20% in Q4 2025)

---

## CPU

| Item | Orig Target | Valid Target | Median Market | Lowest Seen | Status | Notes |
|------|-------------|--------------|---------------|-------------|--------|-------|
| AMD EPYC 7F72 | $300 | $325 | $375 | $360 | 🟢 ACHIEVABLE | China sellers (tugm4470, cheng3930) at $360-430. Make offers...

## Motherboards

| Item | Orig Target | Valid Target | Median Market | Lowest Seen | Status | Notes |
|------|-------------|--------------|---------------|-------------|--------|-------|
| Supermicro H12SSL-CT | $450 | $650 | $634 | $624 | 🟡 ADJUSTED | Pre-owned boards $624-770. Active BIN starts $1,439+. Watch ...
| ASRock Rack ROMED8-2T | $500 | $900 | $1,003 | $825 | 🟡 ADJUSTED | Brand new from China sellers $1,008-1,107. Open-box rare at ...

## Workstation GPUs

| Item | Orig Target | Valid Target | Median Market | Lowest Seen | Status | Notes |
|------|-------------|--------------|---------------|-------------|--------|-------|
| NVIDIA RTX PRO 6000 Blackwell 96GB | $4,500 | $6,500 | $7,999 | $7,999 | 🔴 ADJUSTED | Launched March 2025. Prices dropping ~10-15%/quarter. Revisi...
| NVIDIA RTX 6000 Ada 48GB | $2,800 | $4,200 | $4,800 | $4,500 | 🟡 ADJUSTED | Reputable sellers: cloud_storage_corp, egoods.supply. Refurb...
| NVIDIA RTX PRO 4000 Blackwell SFF | $900 | $1,350 | $1,700 | $1,546 | 🟡 ADJUSTED | Best retail: $1,599 at Microcenter. SFF niche — used may sof...

## Inference GPUs

| Item | Orig Target | Valid Target | Median Market | Lowest Seen | Status | Notes |
|------|-------------|--------------|---------------|-------------|--------|-------|
| NVIDIA L4 24GB | $800 | $2,600 | $3,400 | $2,443 | 🔴 ADJUSTED | Cheapest auction $2,443 (1 bid). Typical used $2,800-3,500. ...
| NVIDIA T4 16GB | $150 | $450 | $637 | $280 | 🔴 ADJUSTED | Legacy but popular. China direct best value. US eBay $565+. ...

## ECC Memory

| Item | Orig Target | Valid Target | Median Market | Lowest Seen | Status | Notes |
|------|-------------|--------------|---------------|-------------|--------|-------|
| Samsung 64GB DDR4-2933 ECC M393A8G40MB2-CVF | $120 | $135 | $240 | $120 | 🟡 ADJUSTED | DDR4 prices RISING (+10-20% Q4 2025). Buy sooner. Target OBO...
| Samsung 64GB DDR4-3200 ECC M393A8G40AB2-CWE | $125 | $115 | $145 | $90 | 🟢 ACHIEVABLE | Best value of all 64GB modules. Watch r/homelabsales for $90...
| Micron 64GB DDR4-2933 ECC MTA36ASF8G72PZ-2G9 | $115 | $125 | $185 | $124 | 🟡 ADJUSTED | Technology-Traderz at $231 BIN — offer $125-140....
| Hynix 64GB DDR4-2933 ECC HMAA8GR7CJR4N-WM | $115 | $120 | $575 | $119 | 🟡 ADJUSTED | Low confidence pricing. Very wide spread. Best deals from no...
| Hynix 64GB DDR4-2933 ECC HMAA8GR7AJR4N-WM | $115 | $120 | $310 | $119 | 🟡 ADJUSTED | Check Walmart used, surplus sites. eBay sellers overprice th...

## Chassis / Cooling / PSU / Accessories

| Item | Orig Target | Valid Target | Median Market | Lowest Seen | Status | Notes |
|------|-------------|--------------|---------------|-------------|--------|-------|
| SilverStone RM52 5U Rackmount Chassis | $300 | $530 | $585 | $570 | 🔴 ADJUSTED | Newegg $570, no used availability. Watch for seasonal sales....
| SilverStone RM44 4U Rackmount Chassis | $250 | $360 | $385 | $350 | 🟡 ADJUSTED | Less popular than RM52. Better chance of open-box/return dea...
| Alphacool Eisbaer Pro HPE Aurora 360 | $200 | $210 | $265 | $228 | 🟢 CLOSE | Alphacool suspended US direct shipping. Buy via Titan Rig ($...
| Corsair HX1500i 2025 ATX 3.1 | $350 | $250 | $350 | $170 | 🟢 ACHIEVABLE | Prices softening. Corsair MSRP dropped $390→$350. Open-box d...
| GPU Support Bracket Anti-Sag | $15 | $7 | $10 | $4 | 🟢 ACHIEVABLE | Buy from AliExpress/China eBay sellers. $5-8 with free shipp...
| SilverStone RM52 Rack Rails | $40 | $85 | $100 | $83 | 🔴 ADJUSTED | Proprietary = no third-party options. Consider universal rac...

## Networking

| Item | Orig Target | Valid Target | Median Market | Lowest Seen | Status | Notes |
|------|-------------|--------------|---------------|-------------|--------|-------|
| Mellanox ConnectX-4 25GbE MCX4111A | $30 | $30 | $42 | $25 | 🟢 ACHIEVABLE | Consider MCX4121A-ACAT (dual-port) at $58 — only $20 more fo...
| Mellanox ConnectX-5 25GbE MCX512A | $50 | $50 | $65 | $25 | 🟢 ACHIEVABLE | Best sellers: jiawen2018, zetainc.ai, core4solutions. ACUT v...
| Mellanox ConnectX-6 100GbE MCX653106A | $200 | $550 | $649 | $424 | 🔴 ADJUSTED | Best current BIN: $574.99 (cloud_storage_corp). HP-branded a...

## U.2 NVMe Storage

| Item | Orig Target | Valid Target | Median Market | Lowest Seen | Status | Notes |
|------|-------------|--------------|---------------|-------------|--------|-------|
| Intel P5510 1.92TB U.2 | $85 | $360 | $400 | $329 | 🔴 ADJUSTED | Consider older P4510 or P4511 at $150-250 as budget alternat...
| Intel P5510 3.84TB U.2 | $150 | $500 | $545 | $500 | 🔴 ADJUSTED | Best $/TB among P5510 sizes. Watch for datacenter pulls....
| Samsung PM9A3 1.92TB U.2 | $90 | $560 | $607 | $559 | 🔴 ADJUSTED | Samsung brand premium. Offer 10% below BIN on $630 listings....
| Samsung PM9A3 3.84TB U.2 | $160 | $920 | $1,023 | $920 | 🔴 ADJUSTED | Most expensive of the U.2 drives. Good performance but costl...
| Micron 7450 1.92TB U.2 | $80 | $440 | $475 | $450 | 🔴 ADJUSTED | Good availability. Often best value for current-gen U.2....
| Micron 7450 Pro 3.84TB U.2 | $145 | $620 | $673 | $500 | 🔴 ADJUSTED | Best $/TB among current-gen U.2 drives. $500 was anomaly (si...

## HDD 16TB+ (NEW)

| Item | Orig Target | Valid Target | Median Market | Lowest Seen | Status | Notes |
|------|-------------|--------------|---------------|-------------|--------|-------|
| Seagate Exos X16 16TB SATA | — | $230 | $268 | $200 | 🟢 NEW | Most actively traded 16TB drive. High confidence pricing. Wa...
| Seagate Exos X18 18TB SATA | — | $270 | $296 | $250 | 🟢 NEW | Slightly better $/TB than X16. Good availability....
| WD Ultrastar HC550 16TB SATA | — | $265 | $295 | $225 | 🟢 NEW | WD reliability good. Slightly higher $/TB than Exos but prov...
| WD Ultrastar HC550 18TB SATA | — | $260 | $280 | $250 | 🟢 NEW | RECOMMENDED for build. Best $/TB usable. 18TB sweet spot for...
| Toshiba MG08 16TB SATA | — | $330 | $350 | $320 | 🟢 NEW | Toshiba drives less liquid on used market. Prices firmer....
| Toshiba MG09 18TB SATA | — | $290 | $310 | $260 | 🟢 NEW | 18TB Toshiba less common than Seagate/WD equivalents....

---

## Scam Alerts & Risk Warnings

| Item | Risk Level | Warning |
|------|------------|---------|
| RTX PRO 6000 below $7,000 | **CRITICAL** | Confirmed scam listings at $5,999. Any price below $7,000 is fraudulent. |
| RTX 6000 Ada below $3,500 | **HIGH** | Legitimate floor is $4,500. Listings below $3,500 are scams. |
| L4 below $2,000 | **HIGH** | Market floor $2,400+. Sub-$2,000 listings are fake. |
| T4 below $250 | **MEDIUM** | China sellers at $280 are legitimate; US listings below $400 may be refurbished/poor condition. |
| Any U.2 SSD below $200 | **MEDIUM** | Enterprise SSDs don't sell this cheap. Check power-on hours and health %. |
| H12SSL-CT below $500 | **MEDIUM** | Working boards start at $600+. Sub-$500 may be damaged, missing accessories, or replica boards. |

---

## Recommended Buying Strategy

### Phase 1: Buy Immediately (prices rising or stable at floor)
- Samsung M393A8G40AB2-CWE 64GB ECC — $90-115 via Reddit r/homelabsales lots
- Corsair HX1500i — $250 open-box on eBay (prices softening, good time to buy)
- Mellanox ConnectX-4/5 — $30-50 from China sellers (stable, abundant)
- GPU Support Bracket — $5-8 from China (commodity)

### Phase 2: Set Deal Alerts & Wait
- AMD EPYC 7F72 — Alert at $325 (make offers at $320-340)
- Supermicro H12SSL-CT — Alert at $650 (watch for open-box at $600-700)
- Seagate Exos X16 16TB — Alert at $230 (4-pack bulk deals)
- WD Ultrastar HC550 18TB — Alert at $260 (best $/TB for RAIDZ2)
- Alphacool Eisbaer Pro — Alert at $210 (watch Titan Rig sales)

### Phase 3: Monitor for Future Drops
- RTX PRO 6000 — Wait 3-6 months (dropping 10-15%/quarter)
- RTX PRO 4000 SFF — Wait for used market to develop
- NVIDIA L4 — Monitor for datacenter liquidation events
- U.2 NVMe SSDs — Watch for datacenter decommissioning waves
- ConnectX-6 100GbE — Stable, set alert at $550 and be patient

---

## RAIDZ2 HDD Recommendation

| Model | Capacity | Deal Target | 4x Cost | Usable (RAIDZ2) | $/TB Usable |
|-------|----------|-------------|---------|-----------------|-------------|
| **WD Ultrastar HC550 18TB** | 18TB | $260 | $1,040 | 36TB | **$28.89** |
| Seagate Exos X18 18TB | 18TB | $270 | $1,080 | 36TB | $30.00 |
| Toshiba MG09 18TB | 18TB | $290 | $1,160 | 36TB | $32.22 |
| Seagate Exos X16 16TB | 16TB | $230 | $920 | 32TB | $28.75 |
| WD Ultrastar HC550 16TB | 16TB | $265 | $1,060 | 32TB | $33.13 |
| Toshiba MG08 16TB | 16TB | $330 | $1,320 | 32TB | $41.25 |

**Winner: WD Ultrastar HC550 18TB** — Best $/TB usable, proven reliability, good availability.

**Budget pick: Seagate Exos X16 16TB** — Lowest total cost ($920 for 32TB usable), most liquid used market.

---

## Files Generated

| File | Description |
|------|-------------|
| `plan/seed_data_v2.sql` | Updated PostgreSQL seed with 34 validated items |
| `plan/seed_data.sql` | Original seed (28 items, pre-validation) |
| `plan/tracked_items.json` | JSON config with polling strategy |
| `research/pricing_cpu_motherboard.md` | CPU + motherboard pricing research |
| `research/pricing_gpu_workstation.md` | Workstation GPU pricing research |
| `research/pricing_gpu_inference.md` | Inference GPU pricing research |
| `research/pricing_memory_ecc.md` | ECC memory pricing research |
| `research/pricing_chassis_cooling_psu.md` | Chassis/PSU/cooling research |
| `research/pricing_networking.md` | Mellanox networking research |
| `research/pricing_storage_u2.md` | U.2 NVMe SSD research |
| `research/pricing_hdd_16tb_plus.md` | 16TB+ HDD research (NEW) |
