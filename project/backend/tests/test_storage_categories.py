"""eBay HDD vs SSD category correctness (DEFERRED_ISSUES D3).

Enterprise HDDs belong in eBay US 'Internal Hard Disk Drives' (56083); enterprise
U.2 NVMe SSDs belong in 'Internal Solid State Drives' (175669). They must NOT share
a category id, or HDD searches get polluted by SSDs (and vice-versa).
"""
from app.services.ebay.catalog import HardwareCatalog

HDD_CATEGORY_ID = "56083"
SSD_CATEGORY_ID = "175669"


def _is_ssd(item) -> bool:
    text = f"{item.name} {item.keywords}".upper()
    return "SSD" in text or "NVME" in text or "U.2" in text


def _is_hdd(item) -> bool:
    text = f"{item.name} {item.keywords}".upper()
    return "HDD" in text and not _is_ssd(item)


def test_storage_items_are_class_correct():
    ssd_items = [i for i in HardwareCatalog.ITEMS if _is_ssd(i)]
    hdd_items = [i for i in HardwareCatalog.ITEMS if _is_hdd(i)]

    assert ssd_items, "expected enterprise SSD catalog entries"
    assert hdd_items, "expected enterprise HDD catalog entries"

    for item in ssd_items:
        assert item.category_id == SSD_CATEGORY_ID, (
            f"SSD '{item.name}' should use Internal-SSD {SSD_CATEGORY_ID}, "
            f"got {item.category_id}"
        )
    for item in hdd_items:
        assert item.category_id == HDD_CATEGORY_ID, (
            f"HDD '{item.name}' should use Internal-HDD {HDD_CATEGORY_ID}, "
            f"got {item.category_id}"
        )


def test_hdd_and_ssd_do_not_share_a_category_id():
    ssd_ids = {i.category_id for i in HardwareCatalog.ITEMS if _is_ssd(i)}
    hdd_ids = {i.category_id for i in HardwareCatalog.ITEMS if _is_hdd(i)}
    assert ssd_ids.isdisjoint(hdd_ids), (
        f"HDD and SSD device classes share category id(s): {ssd_ids & hdd_ids}"
    )


def test_categories_list_distinguishes_hdd_and_ssd():
    cat_ids = {c["id"] for c in HardwareCatalog.get_categories()}
    assert HDD_CATEGORY_ID in cat_ids
    assert SSD_CATEGORY_ID in cat_ids


def test_specific_ssd_entries_use_ssd_category():
    expected_ssds = {
        "Intel P5510 1.92TB U.2",
        "Intel P5510 3.84TB U.2",
        "Samsung PM9A3 1.92TB U.2",
        "Samsung PM9A3 3.84TB U.2",
        "Micron 7450 1.92TB U.2",
        "Micron 7450 Pro 3.84TB U.2",
    }
    by_name = {i.name: i for i in HardwareCatalog.ITEMS}
    for name in expected_ssds:
        assert by_name[name].category_id == SSD_CATEGORY_ID


def test_specific_hdd_entries_use_hdd_category():
    expected_hdds = {
        "Seagate Exos X16 16TB",
        "Seagate Exos X18 18TB",
        "WD Ultrastar HC550 16TB",
        "WD Ultrastar HC550 18TB",
        "Toshiba MG08 16TB",
        "Toshiba MG09 18TB",
    }
    by_name = {i.name: i for i in HardwareCatalog.ITEMS}
    for name in expected_hdds:
        assert by_name[name].category_id == HDD_CATEGORY_ID
