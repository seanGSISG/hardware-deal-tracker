from dataclasses import dataclass

# PCPartPicker product mapping (feature-003, story-4).
#   catalog name -> (pcpp_product_id, pcpp_product_name)
# pcpp_product_id is PCPartPicker's stable 6-char product slug (the segment in
# https://pcpartpicker.com/product/<id>/). The product NAME is recorded alongside
# for traceability so a future operator can verify no item is mis-mapped to an
# unrelated id. These are the items with a stable NEW-RETAIL PCPartPicker page;
# all other (used-only / enterprise-channel) catalog SKUs stay unmapped.
#
# NOTE: ids below are representative mappings to be confirmed against the live
# PCPartPicker product pages before PCPartPicker benchmarking is enabled (it is
# OFF by default; see docs/PCPP_MAPPING.md + docs/PCPARTPICKER_EGRESS.md).
PCPP_MAPPINGS: dict[str, tuple[str, str]] = {
    # Workstation GPUs (current-gen, new-retail tracked) — the EPYC build's GPU slot.
    "NVIDIA RTX PRO 6000 Blackwell 96GB": ("pX6000", "NVIDIA RTX PRO 6000 Blackwell 96 GB"),
    "NVIDIA RTX PRO 4000 Blackwell SFF": ("pR4000", "NVIDIA RTX PRO 4000 Blackwell SFF 24 GB"),
    # Enterprise HDDs (PCPartPicker tracks these as internal hard drives).
    "Seagate Exos X16 16TB": ("exX16T", "Seagate Exos X16 16 TB ST16000NM001G"),
    "Seagate Exos X18 18TB": ("exX18T", "Seagate Exos X18 18 TB ST18000NM000J"),
    "WD Ultrastar HC550 16TB": ("hc5516", "WD Ultrastar DC HC550 16 TB WUH721816ALE6L4"),
    "WD Ultrastar HC550 18TB": ("hc5518", "WD Ultrastar DC HC550 18 TB WUH721818ALE6L4"),
    "Toshiba MG09 18TB": ("mg0918", "Toshiba MG09 18 TB MG09ACA18TE"),
}


@dataclass
class CatalogItem:
    name: str
    keywords: str
    sku: str
    mpn: str
    category_id: str
    target_price: float
    alert_threshold: float
    search_interval: int
    benchmark_median: float
    scam_floor: float
    notes: str = ""
    marketplace: str = "ebay"
    is_enabled: bool = True
    # Minimum deal score (0-100) at which a listing is surfaced/alerted.
    # Defaults match the TrackedItem model default; per-item overrides applied
    # below so the catalog stays the single source of truth for seed generation.
    min_deal_score: int = 50
    # Optional PCPartPicker product mapping (feature-003, story-4). Non-null only
    # for items with a stable NEW-RETAIL PCPartPicker product page (current-gen
    # workstation GPUs, the enterprise HDDs PCPartPicker tracks). Used-only /
    # enterprise-channel SKUs (EPYC CPUs, U.2 NVMe) stay null and are documented
    # as intentionally unmapped in docs/PCPP_MAPPING.md. Benchmark-only — never
    # used for scoring of PCPartPicker rows (PCPartPicker.search() returns []).
    pcpp_product_id: str | None = None


class HardwareCatalog:
    """Pre-loaded catalog of 35 validated SKUs for Sean's EPYC build.

    Scoped (2026-06-20) to the EPYC 7543P build platform — CPU + motherboards +
    ECC RAM — plus the build's GPU slot (RTX PRO 6000 path) and a lighter U.2 /
    HDD price watch. Networking NICs, chassis/cooling/PSU, inference GPUs (L4/T4)
    and accessories were retired from the watchlist; re-add from git history if
    the build scope widens. Polling tiers: build-critical CPU + boards at 5 min
    (P0), RAM at 10 min (does not move faster), storage at 20 min (price watch).
    """

    ITEMS: list[CatalogItem] = [
        # CPU
        CatalogItem("AMD EPYC 7F72", "AMD EPYC 7F72 server CPU processor SP3",
            "100-000000336", "7F72", "164", 325.0, 0.15, 300, 375.0, 280.0,
            "Abundant China supply. Make offers at $320-340."),
        CatalogItem("AMD EPYC 7543P", "AMD EPYC 7543P server CPU processor SP3",
            "100-000000341", "7543P", "164", 750.0, 0.15, 300, 900.0, 480.0,
            "32C/64T Milan, 256MB L3, single-socket P-variant (cheaper than 7543). "
            "Buy <$750. Flag <$480 as suspicious (vendor-locked/fake). Combos price "
            ">$1500 so this part-only target ignores them. Build CPU — P0 5min poll."),

        # Motherboards
        CatalogItem("Supermicro H12SSL-CT", "Supermicro H12SSL-CT motherboard SP3 EPYC",
            "MBD-H12SSL-CT-O", "H12SSL-CT", "1244", 650.0, 0.10, 300, 634.0, 500.0,
            "Pre-owned risen from $620. Watch for open-box at $600-700."),
        CatalogItem("Supermicro H12SSL-i", "Supermicro H12SSL-i motherboard SP3 EPYC",
            "MBD-H12SSL-i-O", "H12SSL-i", "1244", 600.0, 0.12, 300, 720.0, 400.0,
            "ATX single-socket SP3, 5x PCIe4 x16 (GPU-ready). Cheaper -i variant "
            "(no onboard HBA/10GbE vs -CT). Buy <$600. Board supply thin, expect to "
            "wait for a dip. Build board — P0 5min poll."),
        CatalogItem("ASRock Rack ROMED8-2T", "ASRock Rack ROMED8-2T motherboard SP3 EPYC",
            "ROMED8-2T", "ROMED8-2T", "1244", 780.0, 0.12, 300, 1003.0, 520.0,
            "Retuned target 900->780 per Sean (2026-06-19), realistic fair-price "
            "alert. Live median ~$1003. New boards $1,000-1,080. Build board — P0 5min poll."),

        # Workstation GPUs (the EPYC build's GPU slot — RTX PRO 6000 target + fallbacks)
        CatalogItem("NVIDIA RTX PRO 6000 Blackwell 96GB",
            "NVIDIA RTX PRO 6000 Blackwell Workstation 96GB GPU",
            "900-5G180-2550-000", "RTX PRO 6000", "27386", 6500.0, 0.10, 1800, 7999.0, 7000.0,
            "SCAM WARNING: Listings below $7,000 are confirmed scams. Too new for used market."),
        CatalogItem("NVIDIA RTX PRO 4000 Blackwell SFF",
            "NVIDIA RTX PRO 4000 Blackwell SFF workstation GPU",
            "900-5G173-2550-000", "RTX PRO 4000", "27386", 1350.0, 0.12, 600, 1700.0, 1400.0,
            "Cheaper same-slot fallback for the build GPU. New card, no used market yet. $1,599 retail."),

        # Intel Arc Pro B70 32GB (added 2026-08-26, Sean's request). Two entries by
        # design: the exact ASRock Creator board he wants, plus a brand-agnostic watch
        # that catches Sparkle/Gunnir/Intel-reference listings of the same silicon.
        # Alert geometry: benchmark_median 1199.99 is the "anything above this is a bad
        # deal" line; with no price history the engine seeds std_dev at 15% of median, so
        # a listing at $1,000 scores ~66 and a listing at $1,050 scores ~58 - i.e. the
        # sub-$1,000 alert Sean asked for falls out of the median, not a separate knob
        # (there is no absolute price trigger in the scorer; target_price is UI-only).
        # scam_floor 720 = 60% of median, the documented GPU rate: it keeps the whole
        # $720-$1,000 window alertable (a scam flag caps overall at 30 and would MUTE the
        # alert) while still catching the sub-$720 fakes this card will attract.
        # Prices PROVISIONAL - retune once live medians accumulate.
        CatalogItem("ASRock Intel Arc Pro B70 Creator 32GB",
            "ASRock Intel Arc Pro B70 Creator 32GB GDDR6 workstation GPU",
            "B70CT32G", "B70CT32G", "27386",
            1000.0, 0.17, 600, 1199.99, 720.0,
            "Sean's target card. BUY under $1,000. $1,199.99 confirmed by Sean 2026-08-26 as "
            "the live Micro Center Denver in-store price, which is also the good-deal line - "
            "above it is a bad deal. MPN B70CT32G verified off a live eBay listing title "
            "(ASRock part 306636). Deliberately NOT in keywords: only 1 of 5 live listings "
            "carries the model code, so requiring it would cut recall. New product, no used "
            "market, expect scams - sub-$720 is flagged. P1 10min poll."),
        CatalogItem("Intel Arc Pro B70 32GB (any brand)",
            "Intel Arc Pro B70 32GB GDDR6 workstation GPU",
            "Arc Pro B70", "Arc Pro B70", "27386",
            1000.0, 0.17, 1200, 1199.99, 720.0,
            "Brand-agnostic B70 watch - catches Sparkle/Gunnir/Intel-reference and OEM-pull "
            "listings the ASRock-specific entry misses. Same $1,000 buy line / $1,199.99 "
            "median. Deliberately overlaps the ASRock entry - a card matching both surfaces "
            "twice, which is the intended safety net. P2 20min poll to protect the eBay budget."),

        # ECC Memory
        CatalogItem("Samsung 64GB DDR4-2933 ECC M393A8G40MB2-CVF",
            "Samsung M393A8G40MB2-CVF 64GB DDR4 ECC RDIMM server memory",
            "M393A8G40MB2-CVF", "M393A8G40MB2-CVF", "170083", 350.0, 0.20, 600, 450.0, 250.0,
            "Retuned to live eBay 2026-06-30 (Browse active asks, n=28): cluster $450-521, rare dip to $89. DDR4 prices RISING."),
        CatalogItem("Samsung 64GB DDR4-3200 ECC M393A8G40AB2-CWE",
            "Samsung M393A8G40AB2-CWE 64GB DDR4 ECC RDIMM server memory",
            "M393A8G40AB2-CWE", "M393A8G40AB2-CWE", "170083", 480.0, 0.20, 600, 620.0, 340.0,
            "Retuned to live eBay 2026-06-30 (Browse active asks, n=26): $500-668, no sub-$500 (Samsung premium). Homelab/Reddit lots ~$90/unit but rarely on eBay."),
        CatalogItem("Micron 64GB DDR4-2933 ECC MTA36ASF8G72PZ-2G9",
            "Micron MTA36ASF8G72PZ-2G9 64GB DDR4 ECC RDIMM server memory",
            "MTA36ASF8G72PZ-2G9", "MTA36ASF8G72PZ-2G9", "170083", 365.0, 0.20, 600, 470.0, 260.0,
            "Retuned to live eBay 2026-06-30 (Browse active asks, n=13): floor $396, cluster ~$480."),
        CatalogItem("Hynix 64GB DDR4-2933 ECC HMAA8GR7CJR4N-WM",
            "SK Hynix HMAA8GR7CJR4N-WM 64GB DDR4 ECC RDIMM server memory",
            "HMAA8GR7CJR4N-WM", "HMAA8GR7CJR4N-WM", "170083", 365.0, 0.25, 600, 470.0, 260.0,
            "Retuned to live eBay 2026-06-30 (Browse active asks, thin n=2, ~$488). Expensive/rare; watch Walmart/surplus."),
        CatalogItem("Hynix 64GB DDR4-2933 ECC HMAA8GR7AJR4N-WM",
            "SK Hynix HMAA8GR7AJR4N-WM 64GB DDR4 ECC RDIMM server memory",
            "HMAA8GR7AJR4N-WM", "HMAA8GR7AJR4N-WM", "170083", 330.0, 0.25, 600, 430.0, 240.0,
            "Retuned to live eBay 2026-06-30 (Browse active asks, n=21): floor $281, p25 $379, cluster ~$488."),

        # ECC Memory — DDR4-3200 QVL part-number watch (added 2026-06-30, Sean's QVL list).
        # Exact module P/Ns from the build QVL. P2 20min poll (1200s) to stay within the
        # eBay 5k/day budget; memory doesn't move fast. WHOLE memory section retuned 2026-06-30
        # from a live eBay Browse API pass (real creds via the dev backend). NOTE: Browse returns
        # ACTIVE BIN asks only (sold comps need approval-gated Marketplace Insights), so median ≈
        # ask cluster, target ≈ low-quartile "good deal" line, floor ≈ ~55% median. DDR4-3200/2933
        # ECC is expensive mid-2026: 64GB asks $250-936 (Samsung/Hynix premium > Micron), 32GB
        # $100-360. Homelab/Reddit channels run far cheaper but rarely surface on eBay. Once sold
        # access lands, re-anchor target/median to realized prices (will drop these materially).
        # 64GB DDR4-3200 RDIMM
        CatalogItem("Hynix 64GB DDR4-3200 ECC HMAA8GR7AJR4N-XN",
            "SK Hynix HMAA8GR7AJR4N-XN 64GB DDR4 ECC RDIMM server memory",
            "HMAA8GR7AJR4N-XN", "HMAA8GR7AJR4N-XN", "170083", 460.0, 0.20, 1200, 590.0, 330.0,
            "QVL DDR4-3200 watch (2026-06-30). Priced via dev eBay Browse API 2026-06-30 (active BIN asks, floor-anchored)."),
        CatalogItem("Micron 64GB DDR4-3200 ECC MTA36ASF8G72PZ-3G2E1VI",
            "Micron MTA36ASF8G72PZ-3G2E1VI 64GB DDR4 ECC RDIMM server memory",
            "MTA36ASF8G72PZ-3G2E1VI", "MTA36ASF8G72PZ-3G2E1VI", "170083", 340.0, 0.20, 1200, 430.0, 235.0,
            "QVL DDR4-3200 watch (2026-06-30). Cell die OBE45D9XPC. Priced via dev eBay Browse API 2026-06-30 (active BIN asks, floor-anchored)."),
        CatalogItem("Micron 64GB DDR4-3200 ECC MTA36ASF8G72PZ-3G2E1TI",
            "Micron MTA36ASF8G72PZ-3G2E1TI 64GB DDR4 ECC RDIMM server memory",
            "MTA36ASF8G72PZ-3G2E1TI", "MTA36ASF8G72PZ-3G2E1TI", "170083", 310.0, 0.20, 1200, 400.0, 220.0,
            "QVL DDR4-3200 watch (2026-06-30). Cell die OAE45D9XPC. Priced via dev eBay Browse API 2026-06-30 (active BIN asks, floor-anchored)."),
        # 32GB DDR4-3200 RDIMM
        CatalogItem("Crucial 32GB DDR4-3200 ECC CT32G4RFD432A.36FE2",
            "Crucial CT32G4RFD432A 32GB DDR4 ECC RDIMM server memory",
            "CT32G4RFD432A.36FE2", "CT32G4RFD432A.36FE2", "170083", 185.0, 0.20, 1200, 250.0, 140.0,
            "QVL DDR4-3200 watch (2026-06-30). One row for both cell dies on the QVL "
            "(9CE75D9WFK / 8SE75D9WFK — same module P/N). Priced via dev eBay Browse API 2026-06-30 (active BIN asks, floor-anchored)."),
        CatalogItem("Innodisk 32GB DDR4-3200 ECC M4R0-BGS2BCEM-J02",
            "Innodisk M4R0-BGS2BCEM-J02 32GB DDR4 ECC RDIMM server memory",
            "M4R0-BGS2BCEM-J02", "M4R0-BGS2BCEM-J02", "170083", 185.0, 0.20, 1200, 250.0, 140.0,
            "QVL DDR4-3200 watch (2026-06-30). Samsung K4AAG085WA die. Priced via dev eBay Browse API 2026-06-30 (active BIN asks, floor-anchored)."),
        CatalogItem("Kingston 32GB DDR4-3200 ECC KSM32RD4/32MEI",
            "Kingston KSM32RD4/32MEI 32GB DDR4 ECC RDIMM server memory",
            "KSM32RD4/32MEI", "KSM32RD4/32MEI", "170083", 185.0, 0.20, 1200, 250.0, 140.0,
            "QVL DDR4-3200 watch (2026-06-30). Priced via dev eBay Browse API 2026-06-30 (active BIN asks, floor-anchored)."),
        CatalogItem("Micron 32GB DDR4-3200 ECC MTA18ASF4G72PZ-3G2F1UI",
            "Micron MTA18ASF4G72PZ-3G2F1UI 32GB DDR4 ECC RDIMM server memory",
            "MTA18ASF4G72PZ-3G2F1UI", "MTA18ASF4G72PZ-3G2F1UI", "170083", 185.0, 0.20, 1200, 250.0, 140.0,
            "QVL DDR4-3200 watch (2026-06-30). Cell die IRF75D8CJT. Priced via dev eBay Browse API 2026-06-30 (active BIN asks, floor-anchored)."),
        CatalogItem("Micron 32GB DDR4-3200 ECC MTA18ASF4G72PDZ-3G2E1UI",
            "Micron MTA18ASF4G72PDZ-3G2E1UI 32GB DDR4 ECC RDIMM server memory",
            "MTA18ASF4G72PDZ-3G2E1UI", "MTA18ASF4G72PDZ-3G2E1UI", "170083", 185.0, 0.20, 1200, 250.0, 140.0,
            "QVL DDR4-3200 watch (2026-06-30). Cell die OBE45D9ZFV. Priced via dev eBay Browse API 2026-06-30 (active BIN asks, floor-anchored)."),
        CatalogItem("Micron 32GB DDR4-3200 ECC MTA18ASF4G72PZ-3G2F1TI",
            "Micron MTA18ASF4G72PZ-3G2F1TI 32GB DDR4 ECC RDIMM server memory",
            "MTA18ASF4G72PZ-3G2F1TI", "MTA18ASF4G72PZ-3G2F1TI", "170083", 185.0, 0.20, 1200, 250.0, 140.0,
            "QVL DDR4-3200 watch (2026-06-30). Cell die ISF75D8CJT. Priced via dev eBay Browse API 2026-06-30 (active BIN asks, floor-anchored)."),
        CatalogItem("Micron 32GB DDR4-3200 ECC MTA18ASF4G72PDZ-3G2F1VI",
            "Micron MTA18ASF4G72PDZ-3G2F1VI 32GB DDR4 ECC RDIMM server memory",
            "MTA18ASF4G72PDZ-3G2F1VI", "MTA18ASF4G72PDZ-3G2F1VI", "170083", 185.0, 0.20, 1200, 250.0, 140.0,
            "QVL DDR4-3200 watch (2026-06-30). Cell die ISF75D8CJV. Priced via dev eBay Browse API 2026-06-30 (active BIN asks, floor-anchored)."),
        CatalogItem("SMART 32GB DDR4-3200 ECC STB724G4ASR32P2-FM",
            "SMART STB724G4ASR32P2-FM 32GB DDR4 ECC RDIMM server memory",
            "STB724G4ASR32P2-FM", "STB724G4ASR32P2-FM", "170083", 185.0, 0.20, 1200, 250.0, 140.0,
            "QVL DDR4-3200 watch (2026-06-30). Micron 3ER75D8BPH die. Priced via dev eBay Browse API 2026-06-30 (active BIN asks, floor-anchored)."),

        # U.2 NVMe Storage (price watch — P2 20min)
        # eBay US 'Internal Solid State Drives' leaf = 175669 (verified live at
        # ebay.com/b/.../175669). HDDs stay on 56083 ('Internal Hard Disk Drives')
        # so enterprise-HDD searches aren't polluted by SSDs and vice-versa (D3).
        CatalogItem("Intel P5510 1.92TB U.2",
            "Intel P5510 1.92TB U.2 NVMe enterprise SSD",
            "SSDPE2KX019T801", "P5510", "175669", 360.0, 0.15, 1200, 400.0, 300.0,
            "Consider older P4510 at $150-250 as budget alternative."),
        CatalogItem("Intel P5510 3.84TB U.2",
            "Intel P5510 3.84TB U.2 NVMe enterprise SSD",
            "SSDPE2KX038T801", "P5510-4T", "175669", 500.0, 0.10, 1200, 545.0, 400.0,
            "Best $/TB among P5510 sizes."),
        CatalogItem("Samsung PM9A3 1.92TB U.2",
            "Samsung PM9A3 1.92TB U.2 NVMe enterprise SSD",
            "MZQL21T9HCJR", "PM9A3", "175669", 560.0, 0.10, 1200, 607.0, 450.0,
            "Samsung brand premium. Offer 10% below BIN."),
        CatalogItem("Samsung PM9A3 3.84TB U.2",
            "Samsung PM9A3 3.84TB U.2 NVMe enterprise SSD",
            "MZQL23T8HCLS", "PM9A3-4T", "175669", 920.0, 0.10, 1200, 1023.0, 750.0,
            "Most expensive U.2 drive. Good performance but costly."),
        CatalogItem("Micron 7450 1.92TB U.2",
            "Micron 7450 1.92TB U.2 NVMe enterprise SSD",
            "MTFDKCB1T9TFS-1BC1ZABYY", "7450", "175669", 440.0, 0.10, 1200, 475.0, 350.0,
            "Good availability. Best value current-gen U.2."),
        CatalogItem("Micron 7450 Pro 3.84TB U.2",
            "Micron 7450 Pro 3.84TB U.2 NVMe enterprise SSD",
            "MTFDKCB3T8TFS-1BC15ABYY", "7450-4T", "175669", 620.0, 0.10, 1200, 673.0, 500.0,
            "Best $/TB at ~$162/TB. $500 was anomaly listing."),

        # HDD 16TB+ (price watch — P2 20min)
        CatalogItem("Seagate Exos X16 16TB",
            "Seagate Exos X16 16TB ST16000NM001G enterprise HDD SATA",
            "ST16000NM001G", "ST16000NM001G", "56083", 230.0, 0.15, 1200, 268.0, 180.0,
            "Best all-rounder. 4x RAIDZ2 = 32TB usable ~$920."),
        CatalogItem("Seagate Exos X18 18TB",
            "Seagate Exos X18 18TB ST18000NM000J enterprise HDD SATA",
            "ST18000NM000J", "ST18000NM000J", "56083", 270.0, 0.10, 1200, 296.0, 220.0,
            "$16.44/TB. 4x RAIDZ2 = 36TB usable ~$1,080."),
        CatalogItem("WD Ultrastar HC550 16TB",
            "WD Ultrastar HC550 16TB WUH721816ALE6L4 enterprise HDD SATA",
            "WUH721816ALE6L4", "WUH721816ALE6L4", "56083", 265.0, 0.10, 1200, 295.0, 200.0,
            "Reliable alternative to Exos. $18.44/TB."),
        CatalogItem("WD Ultrastar HC550 18TB",
            "WD Ultrastar HC550 18TB WUH721818ALE6L4 enterprise HDD SATA",
            "WUH721818ALE6L4", "WUH721818ALE6L4", "56083", 260.0, 0.10, 1200, 280.0, 200.0,
            "BEST $/TB at $15.56/TB! 4x RAIDZ2 = 36TB usable ~$1,040. RECOMMENDED."),
        CatalogItem("Toshiba MG08 16TB",
            "Toshiba MG08 16TB MG08ACA16TE enterprise HDD SATA",
            "MG08ACA16TE", "MG08ACA16TE", "56083", 330.0, 0.08, 1200, 350.0, 280.0,
            "Higher $/TB ($21.88) but good reliability. Less common on eBay."),
        CatalogItem("Toshiba MG09 18TB",
            "Toshiba MG09 18TB MG09ACA18TE enterprise HDD SATA",
            "MG09ACA18TE", "MG09ACA18TE", "56083", 290.0, 0.08, 1200, 310.0, 240.0,
            "$17.22/TB. Good middle ground between Exos and Ultrastar."),

        # Chassis & CPU cooling (EPYC build completion — P1 15min)
        # Added 2026-07-25: the EPYC 7742 + ROMED8-2T + 256GB build is parts-complete
        # except the case. category_id left None deliberately — an unverified eBay
        # category filter returns zero results, and keyword search is accurate enough
        # for these. All three price sets are PROVISIONAL; retune once live medians land.
        CatalogItem("Fractal Design Define 7 XL",
            "Fractal Design Define 7 XL full tower case",
            "FD-C-DEF7X-01", "FD-C-DEF7X-01", None, 150.0, 0.12, 900, 200.0, 75.0,
            "EPYC build case — QUIET pick (sound-dampened front). Takes ATX->SSI-EEB, "
            "185mm cooler clearance, 9x140mm fan mounts. New retail ~$220-230; the deal "
            "is used/open-box. Heavy item — watch shipping cost, and treat local-pickup-only "
            "listings as the real bargains."),
        CatalogItem("Fractal Design Meshify 2 XL",
            "Fractal Design Meshify 2 XL full tower case",
            "FD-C-MES2X-01", "FD-C-MES2X-01", None, 145.0, 0.12, 900, 190.0, 70.0,
            "EPYC build case — AIRFLOW pick. Identical chassis to Define 7 XL, mesh front "
            "instead of dampened. Better for sustained 2-GPU load (~825W). New retail "
            "$204.99 confirmed 2026-07-25. Same shipping caveat as the Define."),
        CatalogItem("Noctua NH-U14S TR4-SP3",
            "Noctua NH-U14S TR4-SP3 cooler SP3 TR4",
            "NH-U14S TR4-SP3", "NH-U14S TR4-SP3", None, 70.0, 0.12, 900, 95.0, 35.0,
            "EPYC 7742 (225W) quiet cooler. 165mm tall — fits the 185mm clearance in both "
            "Fractal XL cases. SP3-native mounting. New ~$100. Verify the SecuFirm2 SP3 "
            "bracket is included on used listings — missing hardware is the usual gotcha."),
    ]

    # Per-item minimum deal score overrides (research-validated). Items not
    # listed keep the CatalogItem default. Applied below so each ITEMS entry
    # stays compact while the catalog remains the single source of truth.
    _MIN_DEAL_SCORE_OVERRIDES = {
        "Supermicro H12SSL-CT": 65,
        "Supermicro H12SSL-i": 65,
        "NVIDIA RTX PRO 6000 Blackwell 96GB": 70,
        "Hynix 64GB DDR4-2933 ECC HMAA8GR7CJR4N-WM": 65,
        "Hynix 64GB DDR4-2933 ECC HMAA8GR7AJR4N-WM": 65,
        "Samsung PM9A3 3.84TB U.2": 65,
        "Toshiba MG08 16TB": 55,
        "Toshiba MG09 18TB": 55,
    }

    @classmethod
    def _apply_min_deal_score_overrides(cls) -> None:
        for item in cls.ITEMS:
            if item.name in cls._MIN_DEAL_SCORE_OVERRIDES:
                item.min_deal_score = cls._MIN_DEAL_SCORE_OVERRIDES[item.name]
            else:
                item.min_deal_score = 60

    @classmethod
    def _apply_pcpp_mappings(cls) -> None:
        """Stamp pcpp_product_id onto the mappable items (feature-003, story-4)."""
        for item in cls.ITEMS:
            mapping = PCPP_MAPPINGS.get(item.name)
            item.pcpp_product_id = mapping[0] if mapping else None

    @classmethod
    def search(cls, query: str) -> list[CatalogItem]:
        query_lower = query.lower()
        results = []
        for item in cls.ITEMS:
            if (query_lower in item.name.lower() or
                    query_lower in item.keywords.lower() or
                    query_lower in item.sku.lower() or
                    query_lower in item.mpn.lower()):
                results.append(item)
        return results

    @classmethod
    def get_by_name(cls, name: str) -> CatalogItem | None:
        for item in cls.ITEMS:
            if item.name == name:
                return item
        return None

    @classmethod
    def get_categories(cls) -> list[dict]:
        return [
            {"id": "164", "name": "CPUs/Processors"},
            {"id": "1244", "name": "Motherboards"},
            {"id": "27386", "name": "Graphics/Video Cards"},
            {"id": "170083", "name": "Enterprise Memory (RAM)"},
            {"id": "56083", "name": "Internal Hard Disk Drives (HDD)"},
            {"id": "175669", "name": "Internal Solid State Drives (SSD)"},
        ]


# Apply per-item min_deal_score overrides at import time so the catalog is the
# single source of truth consumed by scripts/generate_seed.py.
HardwareCatalog._apply_min_deal_score_overrides()
# Stamp PCPartPicker product-id mappings (feature-003, story-4) at import time so
# they round-trip into the generated seed and into TrackedItem.pcpp_product_id.
HardwareCatalog._apply_pcpp_mappings()
