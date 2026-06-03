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
    # Workstation / inference GPUs (current-gen, new-retail tracked).
    "NVIDIA RTX PRO 6000 Blackwell 96GB": ("pX6000", "NVIDIA RTX PRO 6000 Blackwell 96 GB"),
    "NVIDIA RTX 6000 Ada 48GB": ("a6000A", "NVIDIA RTX 6000 Ada Generation 48 GB"),
    "NVIDIA RTX PRO 4000 Blackwell SFF": ("pR4000", "NVIDIA RTX PRO 4000 Blackwell SFF 24 GB"),
    "NVIDIA L4 24GB": ("nvL424", "NVIDIA L4 24 GB"),
    "NVIDIA T4 16GB": ("nvT416", "NVIDIA T4 16 GB"),
    # Power supply (new-retail consumer/workstation PSU PCPartPicker tracks).
    "Corsair HX1500i 2025 ATX 3.1": ("hx1500", "Corsair HX1500i (2025) 1500 W 80+ Platinum ATX 3.1"),
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
    # workstation/inference GPUs, the PSU, enterprise HDDs PCPartPicker tracks).
    # Used-only / enterprise-channel SKUs (EPYC CPUs, ConnectX NICs, U.2 NVMe,
    # niche chassis/coolers) stay null and are documented as intentionally
    # unmapped in docs/PCPP_MAPPING.md. Benchmark-only — never used for scoring
    # of PCPartPicker rows (PCPartPicker.search() returns []).
    pcpp_product_id: str | None = None


class HardwareCatalog:
    """Pre-loaded catalog of 34 validated enterprise hardware SKUs."""

    ITEMS: list[CatalogItem] = [
        # CPU
        CatalogItem("AMD EPYC 7F72", "AMD EPYC 7F72 server CPU processor SP3",
            "100-000000336", "7F72", "164", 325.0, 0.15, 300, 375.0, 280.0,
            "Abundant China supply. Make offers at $320-340."),

        # Motherboards
        CatalogItem("Supermicro H12SSL-CT", "Supermicro H12SSL-CT motherboard SP3 EPYC",
            "MBD-H12SSL-CT-O", "H12SSL-CT", "1244", 650.0, 0.10, 600, 634.0, 500.0,
            "Pre-owned risen from $620. Watch for open-box at $600-700."),
        CatalogItem("ASRock Rack ROMED8-2T", "ASRock Rack ROMED8-2T motherboard SP3 EPYC",
            "ROMED8-2T", "ROMED8-2T", "1244", 900.0, 0.12, 600, 1003.0, 800.0,
            "New boards $1,000-1,080. Open-box rare at $825."),

        # Workstation GPUs
        CatalogItem("NVIDIA RTX PRO 6000 Blackwell 96GB",
            "NVIDIA RTX PRO 6000 Blackwell Workstation 96GB GPU",
            "900-5G180-2550-000", "RTX PRO 6000", "27386", 6500.0, 0.10, 1800, 7999.0, 7000.0,
            "SCAM WARNING: Listings below $7,000 are confirmed scams. Too new for used market."),
        CatalogItem("NVIDIA RTX 6000 Ada 48GB", "NVIDIA RTX 6000 Ada workstation GPU 48GB",
            "900-5G133-2500-000", "RTX 6000 Ada", "27386", 4200.0, 0.12, 600, 4800.0, 3500.0,
            "Legit used $4,500-5,500. Below $3,500 = scam."),
        CatalogItem("NVIDIA RTX PRO 4000 Blackwell SFF",
            "NVIDIA RTX PRO 4000 Blackwell SFF workstation GPU",
            "900-5G173-2550-000", "RTX PRO 4000", "27386", 1350.0, 0.12, 600, 1700.0, 1400.0,
            "New card, no used market yet. $1,599 retail."),

        # Inference GPUs
        CatalogItem("NVIDIA L4 24GB", "NVIDIA L4 24GB GPU inference accelerator",
            "900-2G193-0000-000", "L4", "27386", 2600.0, 0.15, 600, 3400.0, 2000.0,
            "Current-gen inference GPU. $2,400+ market floor."),
        CatalogItem("NVIDIA T4 16GB", "NVIDIA T4 16GB GPU inference accelerator",
            "900-2G183-0000-000", "T4", "27386", 450.0, 0.20, 300, 637.0, 250.0,
            "US sellers $565+. China direct $280-420."),

        # ECC Memory
        CatalogItem("Samsung 64GB DDR4-2933 ECC M393A8G40MB2-CVF",
            "Samsung M393A8G40MB2-CVF 64GB DDR4 ECC RDIMM server memory",
            "M393A8G40MB2-CVF", "M393A8G40MB2-CVF", "170083", 135.0, 0.20, 300, 240.0, 100.0,
            "DDR4 prices RISING. Buy sooner. Target OBO at 20-30% below BIN."),
        CatalogItem("Samsung 64GB DDR4-3200 ECC M393A8G40AB2-CWE",
            "Samsung M393A8G40AB2-CWE 64GB DDR4 ECC RDIMM server memory",
            "M393A8G40AB2-CWE", "M393A8G40AB2-CWE", "170083", 115.0, 0.20, 300, 145.0, 85.0,
            "Best value. Reddit r/homelabsales lots at $90/unit."),
        CatalogItem("Micron 64GB DDR4-2933 ECC MTA36ASF8G72PZ-2G9",
            "Micron MTA36ASF8G72PZ-2G9 64GB DDR4 ECC RDIMM server memory",
            "MTA36ASF8G72PZ-2G9", "MTA36ASF8G72PZ-2G9", "170083", 125.0, 0.20, 300, 185.0, 100.0,
            "Good availability. $125 via OBO or used pulls."),
        CatalogItem("Hynix 64GB DDR4-2933 ECC HMAA8GR7CJR4N-WM",
            "SK Hynix HMAA8GR7CJR4N-WM 64GB DDR4 ECC RDIMM server memory",
            "HMAA8GR7CJR4N-WM", "HMAA8GR7CJR4N-WM", "170083", 120.0, 0.25, 300, 575.0, 100.0,
            "Expensive on eBay ($400-900 BIN). Watch Walmart/surplus."),
        CatalogItem("Hynix 64GB DDR4-2933 ECC HMAA8GR7AJR4N-WM",
            "SK Hynix HMAA8GR7AJR4N-WM 64GB DDR4 ECC RDIMM server memory",
            "HMAA8GR7AJR4N-WM", "HMAA8GR7AJR4N-WM", "170083", 120.0, 0.25, 300, 310.0, 100.0,
            "eBay $400-800. Walmart pre-owned $119 (sold out)."),

        # Chassis / Cooling / PSU
        CatalogItem("SilverStone RM52 5U Rackmount Chassis",
            "SilverStone RM52 5U rackmount chassis server case",
            "SST-RM52", "RM52", "42014", 530.0, 0.10, 1200, 585.0, 450.0,
            "Niche product, no used market. Watch for seasonal sales."),
        CatalogItem("SilverStone RM44 4U Rackmount Chassis",
            "SilverStone RM44 4U rackmount chassis server case",
            "SST-RM44", "RM44", "42014", 360.0, 0.12, 1200, 385.0, 300.0,
            "Less popular than RM52. Better chance of open-box deals."),
        CatalogItem("Alphacool Eisbaer Pro HPE Aurora 360",
            "Alphacool Eisbaer Pro HPE Aurora 360 AIO CPU cooler SP3",
            "1019572", "Eisbaer-Pro-HPE-Aurora-360", "42007", 210.0, 0.15, 1200, 265.0, 180.0,
            "Alphacool suspended US direct. Buy via Titan Rig ($227)."),
        CatalogItem("Corsair HX1500i 2025 ATX 3.1",
            "Corsair HX1500i 2025 ATX 3.1 power supply 1500W",
            "CP-9020309-NA", "HX1500i", "42006", 250.0, 0.15, 1200, 350.0, 170.0,
            "Prices softening. Open-box deals increasing."),

        # Networking
        CatalogItem("Mellanox ConnectX-4 25GbE MCX4111A",
            "Mellanox ConnectX-4 25GbE SFP28 network adapter MCX4111A",
            "MCX4111A-ACAT", "ConnectX-4", "51167", 30.0, 0.25, 600, 42.0, 20.0,
            "China sellers $33-40. Core4Solutions $34.95."),
        CatalogItem("Mellanox ConnectX-5 25GbE MCX512A",
            "Mellanox ConnectX-5 25GbE SFP28 network adapter MCX512A",
            "MCX512A-ACAT", "ConnectX-5", "51167", 50.0, 0.20, 600, 65.0, 25.0,
            "EOL Jan 2025 = liquidation inventory."),
        CatalogItem("Mellanox ConnectX-6 100GbE MCX653106A",
            "Mellanox ConnectX-6 100GbE QSFP28 network adapter MCX653106A",
            "MCX653106A-ECAT", "ConnectX-6", "51167", 550.0, 0.15, 600, 649.0, 424.0,
            "100GbE holds value. $500-650 used."),

        # U.2 NVMe Storage
        # eBay US 'Internal Solid State Drives' leaf = 175669 (verified live at
        # ebay.com/b/.../175669). HDDs stay on 56083 ('Internal Hard Disk Drives')
        # so enterprise-HDD searches aren't polluted by SSDs and vice-versa (D3).
        CatalogItem("Intel P5510 1.92TB U.2",
            "Intel P5510 1.92TB U.2 NVMe enterprise SSD",
            "SSDPE2KX019T801", "P5510", "175669", 360.0, 0.15, 600, 400.0, 300.0,
            "Consider older P4510 at $150-250 as budget alternative."),
        CatalogItem("Intel P5510 3.84TB U.2",
            "Intel P5510 3.84TB U.2 NVMe enterprise SSD",
            "SSDPE2KX038T801", "P5510-4T", "175669", 500.0, 0.10, 600, 545.0, 400.0,
            "Best $/TB among P5510 sizes."),
        CatalogItem("Samsung PM9A3 1.92TB U.2",
            "Samsung PM9A3 1.92TB U.2 NVMe enterprise SSD",
            "MZQL21T9HCJR", "PM9A3", "175669", 560.0, 0.10, 600, 607.0, 450.0,
            "Samsung brand premium. Offer 10% below BIN."),
        CatalogItem("Samsung PM9A3 3.84TB U.2",
            "Samsung PM9A3 3.84TB U.2 NVMe enterprise SSD",
            "MZQL23T8HCLS", "PM9A3-4T", "175669", 920.0, 0.10, 600, 1023.0, 750.0,
            "Most expensive U.2 drive. Good performance but costly."),
        CatalogItem("Micron 7450 1.92TB U.2",
            "Micron 7450 1.92TB U.2 NVMe enterprise SSD",
            "MTFDKCB1T9TFS-1BC1ZABYY", "7450", "175669", 440.0, 0.10, 600, 475.0, 350.0,
            "Good availability. Best value current-gen U.2."),
        CatalogItem("Micron 7450 Pro 3.84TB U.2",
            "Micron 7450 Pro 3.84TB U.2 NVMe enterprise SSD",
            "MTFDKCB3T8TFS-1BC15ABYY", "7450-4T", "175669", 620.0, 0.10, 600, 673.0, 500.0,
            "Best $/TB at ~$162/TB. $500 was anomaly listing."),

        # HDD 16TB+
        CatalogItem("Seagate Exos X16 16TB",
            "Seagate Exos X16 16TB ST16000NM001G enterprise HDD SATA",
            "ST16000NM001G", "ST16000NM001G", "56083", 230.0, 0.15, 600, 268.0, 180.0,
            "Best all-rounder. 4x RAIDZ2 = 32TB usable ~$920."),
        CatalogItem("Seagate Exos X18 18TB",
            "Seagate Exos X18 18TB ST18000NM000J enterprise HDD SATA",
            "ST18000NM000J", "ST18000NM000J", "56083", 270.0, 0.10, 600, 296.0, 220.0,
            "$16.44/TB. 4x RAIDZ2 = 36TB usable ~$1,080."),
        CatalogItem("WD Ultrastar HC550 16TB",
            "WD Ultrastar HC550 16TB WUH721816ALE6L4 enterprise HDD SATA",
            "WUH721816ALE6L4", "WUH721816ALE6L4", "56083", 265.0, 0.10, 600, 295.0, 200.0,
            "Reliable alternative to Exos. $18.44/TB."),
        CatalogItem("WD Ultrastar HC550 18TB",
            "WD Ultrastar HC550 18TB WUH721818ALE6L4 enterprise HDD SATA",
            "WUH721818ALE6L4", "WUH721818ALE6L4", "56083", 260.0, 0.10, 600, 280.0, 200.0,
            "BEST $/TB at $15.56/TB! 4x RAIDZ2 = 36TB usable ~$1,040. RECOMMENDED."),
        CatalogItem("Toshiba MG08 16TB",
            "Toshiba MG08 16TB MG08ACA16TE enterprise HDD SATA",
            "MG08ACA16TE", "MG08ACA16TE", "56083", 330.0, 0.08, 600, 350.0, 280.0,
            "Higher $/TB ($21.88) but good reliability. Less common on eBay."),
        CatalogItem("Toshiba MG09 18TB",
            "Toshiba MG09 18TB MG09ACA18TE enterprise HDD SATA",
            "MG09ACA18TE", "MG09ACA18TE", "56083", 290.0, 0.08, 600, 310.0, 240.0,
            "$17.22/TB. Good middle ground between Exos and Ultrastar."),

        # Accessories
        CatalogItem("GPU Support Bracket Anti-Sag", "GPU support bracket anti sag holder workstation",
            "", "", "42014", 7.0, 0.30, 1200, 10.0, 4.0,
            "Pure commodity. China $4-8. Don't overpay."),
        CatalogItem("SilverStone RM52 Rack Rails", "SilverStone RM52 rack rails mounting kit RMS05-22",
            "RMS05-22", "RMS05-22", "42014", 85.0, 0.15, 1200, 100.0, 70.0,
            "Proprietary, no alternatives. Consider universal rack shelf."),
    ]

    # Per-item minimum deal score overrides (research-validated). Items not
    # listed keep the CatalogItem default. Applied below so each ITEMS entry
    # stays compact while the catalog remains the single source of truth.
    _MIN_DEAL_SCORE_OVERRIDES = {
        "Supermicro H12SSL-CT": 65,
        "NVIDIA RTX PRO 6000 Blackwell 96GB": 70,
        "NVIDIA RTX 6000 Ada 48GB": 65,
        "NVIDIA L4 24GB": 65,
        "Hynix 64GB DDR4-2933 ECC HMAA8GR7CJR4N-WM": 65,
        "Hynix 64GB DDR4-2933 ECC HMAA8GR7AJR4N-WM": 65,
        "SilverStone RM52 5U Rackmount Chassis": 55,
        "SilverStone RM44 4U Rackmount Chassis": 55,
        "Alphacool Eisbaer Pro HPE Aurora 360": 55,
        "GPU Support Bracket Anti-Sag": 50,
        "SilverStone RM52 Rack Rails": 55,
        "Mellanox ConnectX-6 100GbE MCX653106A": 65,
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
            {"id": "42014", "name": "Computer Cases"},
            {"id": "42006", "name": "Power Supplies"},
            {"id": "42007", "name": "CPU Fans & Heatsinks"},
            {"id": "51167", "name": "Enterprise Networking"},
            {"id": "56083", "name": "Internal Hard Disk Drives (HDD)"},
            {"id": "175669", "name": "Internal Solid State Drives (SSD)"},
        ]


# Apply per-item min_deal_score overrides at import time so the catalog is the
# single source of truth consumed by scripts/generate_seed.py.
HardwareCatalog._apply_min_deal_score_overrides()
# Stamp PCPartPicker product-id mappings (feature-003, story-4) at import time so
# they round-trip into the generated seed and into TrackedItem.pcpp_product_id.
HardwareCatalog._apply_pcpp_mappings()
