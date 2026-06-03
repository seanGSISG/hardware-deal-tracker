# PCPartPicker Catalog Mapping (feature-003, story-4)

`pcpp_product_id` links a catalog item to its **new-retail** PCPartPicker product
page so the benchmark-only `PcPartPickerAdapter.refresh_benchmark()` can refresh a
"vs retail" reference price. The mapping is the single source of truth in
`app/services/ebay/catalog.py` (`PCPP_MAPPINGS`); it round-trips into the
generated seed (`scripts/seed_data_v2.sql`) and into
`TrackedItem.pcpp_product_id` (column pre-exists; no migration).

PCPartPicker is **benchmark-only** and **OFF by default** (`ENABLE_PCPARTPICKER`,
plus a residential egress flag — see `docs/PCPARTPICKER_EGRESS.md`). Its rows
NEVER enter the scoring / dedup / notification pipeline.

> The `pcpp_product_id` slugs in `PCPP_MAPPINGS` are **representative mappings to
> be verified** against the live PCPartPicker product pages before benchmarking
> is enabled. Each is recorded with its PCPartPicker product **name** for
> traceability so no item is silently mis-mapped to an unrelated id.

## Mapped items (11)

| Catalog item | PCPartPicker product name |
|--------------|---------------------------|
| NVIDIA RTX PRO 6000 Blackwell 96GB | NVIDIA RTX PRO 6000 Blackwell 96 GB |
| NVIDIA RTX 6000 Ada 48GB | NVIDIA RTX 6000 Ada Generation 48 GB |
| NVIDIA RTX PRO 4000 Blackwell SFF | NVIDIA RTX PRO 4000 Blackwell SFF 24 GB |
| NVIDIA L4 24GB | NVIDIA L4 24 GB |
| NVIDIA T4 16GB | NVIDIA T4 16 GB |
| Corsair HX1500i 2025 ATX 3.1 | Corsair HX1500i (2025) 1500 W 80+ Platinum ATX 3.1 |
| Seagate Exos X16 16TB | Seagate Exos X16 16 TB ST16000NM001G |
| Seagate Exos X18 18TB | Seagate Exos X18 18 TB ST18000NM000J |
| WD Ultrastar HC550 16TB | WD Ultrastar DC HC550 16 TB WUH721816ALE6L4 |
| WD Ultrastar HC550 18TB | WD Ultrastar DC HC550 18 TB WUH721818ALE6L4 |
| Toshiba MG09 18TB | Toshiba MG09 18 TB MG09ACA18TE |

## Intentionally unmapped (and why)

These catalog items are left `pcpp_product_id = NULL` because they have no stable
new-retail PCPartPicker product page (used-only / enterprise grey-channel SKUs):

- **CPUs** — AMD EPYC 7F72: server CPU sold used/grey-market; not a PCPartPicker
  retail SKU.
- **Server motherboards** — Supermicro H12SSL-CT, ASRock Rack ROMED8-2T: server
  boards, not tracked at consumer retail.
- **ECC server memory** — all Samsung/Micron/Hynix RDIMM SKUs: enterprise RDIMMs
  bought used/in lots, no consumer-retail PCPartPicker page.
- **Networking** — Mellanox ConnectX-4/-5/-6 NICs: enterprise NICs, no retail page.
- **U.2 NVMe** — Intel P5510, Samsung PM9A3, Micron 7450: U.2 enterprise SSDs,
  not in PCPartPicker's consumer SSD catalog.
- **Toshiba MG08 16TB** — older enterprise HDD without a current PCPartPicker
  page (the MG09 18 TB is mapped instead).
- **Chassis / cooling / accessories** — SilverStone RM52/RM44, Alphacool Eisbaer
  Pro HPE, GPU support bracket, rack rails: niche/server-specific items.

To add or correct a mapping, edit `PCPP_MAPPINGS` in `catalog.py`, then run
`make seed-regen` and commit the regenerated `seed_data_v2.sql` (a parity test
guards drift).
