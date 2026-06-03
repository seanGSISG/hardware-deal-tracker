-- Seed data for Hardware Deal Tracker
-- GENERATED FILE — do not edit by hand.
-- Source of truth: app/services/ebay/catalog.py
-- Regenerate with: make seed-regen
--
-- OPTIONAL starter data (ADR-005): the app runs from an empty catalog.

INSERT INTO tracked_items (name, keywords, sku, mpn, category_id, marketplace, target_price, alert_threshold, min_deal_score, is_enabled, search_interval, scam_floor, benchmark_median, pcpp_product_id, notes) VALUES
    ('AMD EPYC 7F72', 'AMD EPYC 7F72 server CPU processor SP3', '100-000000336', '7F72', '164', 'ebay', 325.00, 0.15, 60, true, 300, 280.00, 375.00, NULL, 'Abundant China supply. Make offers at $320-340.'),
    ('Supermicro H12SSL-CT', 'Supermicro H12SSL-CT motherboard SP3 EPYC', 'MBD-H12SSL-CT-O', 'H12SSL-CT', '1244', 'ebay', 650.00, 0.1, 65, true, 600, 500.00, 634.00, NULL, 'Pre-owned risen from $620. Watch for open-box at $600-700.'),
    ('ASRock Rack ROMED8-2T', 'ASRock Rack ROMED8-2T motherboard SP3 EPYC', 'ROMED8-2T', 'ROMED8-2T', '1244', 'ebay', 900.00, 0.12, 60, true, 600, 800.00, 1003.00, NULL, 'New boards $1,000-1,080. Open-box rare at $825.'),
    ('NVIDIA RTX PRO 6000 Blackwell 96GB', 'NVIDIA RTX PRO 6000 Blackwell Workstation 96GB GPU', '900-5G180-2550-000', 'RTX PRO 6000', '27386', 'ebay', 6500.00, 0.1, 70, true, 1800, 7000.00, 7999.00, 'pX6000', 'SCAM WARNING: Listings below $7,000 are confirmed scams. Too new for used market.'),
    ('NVIDIA RTX 6000 Ada 48GB', 'NVIDIA RTX 6000 Ada workstation GPU 48GB', '900-5G133-2500-000', 'RTX 6000 Ada', '27386', 'ebay', 4200.00, 0.12, 65, true, 600, 3500.00, 4800.00, 'a6000A', 'Legit used $4,500-5,500. Below $3,500 = scam.'),
    ('NVIDIA RTX PRO 4000 Blackwell SFF', 'NVIDIA RTX PRO 4000 Blackwell SFF workstation GPU', '900-5G173-2550-000', 'RTX PRO 4000', '27386', 'ebay', 1350.00, 0.12, 60, true, 600, 1400.00, 1700.00, 'pR4000', 'New card, no used market yet. $1,599 retail.'),
    ('NVIDIA L4 24GB', 'NVIDIA L4 24GB GPU inference accelerator', '900-2G193-0000-000', 'L4', '27386', 'ebay', 2600.00, 0.15, 65, true, 600, 2000.00, 3400.00, 'nvL424', 'Current-gen inference GPU. $2,400+ market floor.'),
    ('NVIDIA T4 16GB', 'NVIDIA T4 16GB GPU inference accelerator', '900-2G183-0000-000', 'T4', '27386', 'ebay', 450.00, 0.2, 60, true, 300, 250.00, 637.00, 'nvT416', 'US sellers $565+. China direct $280-420.'),
    ('Samsung 64GB DDR4-2933 ECC M393A8G40MB2-CVF', 'Samsung M393A8G40MB2-CVF 64GB DDR4 ECC RDIMM server memory', 'M393A8G40MB2-CVF', 'M393A8G40MB2-CVF', '170083', 'ebay', 135.00, 0.2, 60, true, 300, 100.00, 240.00, NULL, 'DDR4 prices RISING. Buy sooner. Target OBO at 20-30% below BIN.'),
    ('Samsung 64GB DDR4-3200 ECC M393A8G40AB2-CWE', 'Samsung M393A8G40AB2-CWE 64GB DDR4 ECC RDIMM server memory', 'M393A8G40AB2-CWE', 'M393A8G40AB2-CWE', '170083', 'ebay', 115.00, 0.2, 60, true, 300, 85.00, 145.00, NULL, 'Best value. Reddit r/homelabsales lots at $90/unit.'),
    ('Micron 64GB DDR4-2933 ECC MTA36ASF8G72PZ-2G9', 'Micron MTA36ASF8G72PZ-2G9 64GB DDR4 ECC RDIMM server memory', 'MTA36ASF8G72PZ-2G9', 'MTA36ASF8G72PZ-2G9', '170083', 'ebay', 125.00, 0.2, 60, true, 300, 100.00, 185.00, NULL, 'Good availability. $125 via OBO or used pulls.'),
    ('Hynix 64GB DDR4-2933 ECC HMAA8GR7CJR4N-WM', 'SK Hynix HMAA8GR7CJR4N-WM 64GB DDR4 ECC RDIMM server memory', 'HMAA8GR7CJR4N-WM', 'HMAA8GR7CJR4N-WM', '170083', 'ebay', 120.00, 0.25, 65, true, 300, 100.00, 575.00, NULL, 'Expensive on eBay ($400-900 BIN). Watch Walmart/surplus.'),
    ('Hynix 64GB DDR4-2933 ECC HMAA8GR7AJR4N-WM', 'SK Hynix HMAA8GR7AJR4N-WM 64GB DDR4 ECC RDIMM server memory', 'HMAA8GR7AJR4N-WM', 'HMAA8GR7AJR4N-WM', '170083', 'ebay', 120.00, 0.25, 65, true, 300, 100.00, 310.00, NULL, 'eBay $400-800. Walmart pre-owned $119 (sold out).'),
    ('SilverStone RM52 5U Rackmount Chassis', 'SilverStone RM52 5U rackmount chassis server case', 'SST-RM52', 'RM52', '42014', 'ebay', 530.00, 0.1, 55, true, 1200, 450.00, 585.00, NULL, 'Niche product, no used market. Watch for seasonal sales.'),
    ('SilverStone RM44 4U Rackmount Chassis', 'SilverStone RM44 4U rackmount chassis server case', 'SST-RM44', 'RM44', '42014', 'ebay', 360.00, 0.12, 55, true, 1200, 300.00, 385.00, NULL, 'Less popular than RM52. Better chance of open-box deals.'),
    ('Alphacool Eisbaer Pro HPE Aurora 360', 'Alphacool Eisbaer Pro HPE Aurora 360 AIO CPU cooler SP3', '1019572', 'Eisbaer-Pro-HPE-Aurora-360', '42007', 'ebay', 210.00, 0.15, 55, true, 1200, 180.00, 265.00, NULL, 'Alphacool suspended US direct. Buy via Titan Rig ($227).'),
    ('Corsair HX1500i 2025 ATX 3.1', 'Corsair HX1500i 2025 ATX 3.1 power supply 1500W', 'CP-9020309-NA', 'HX1500i', '42006', 'ebay', 250.00, 0.15, 60, true, 1200, 170.00, 350.00, 'hx1500', 'Prices softening. Open-box deals increasing.'),
    ('Mellanox ConnectX-4 25GbE MCX4111A', 'Mellanox ConnectX-4 25GbE SFP28 network adapter MCX4111A', 'MCX4111A-ACAT', 'ConnectX-4', '51167', 'ebay', 30.00, 0.25, 60, true, 600, 20.00, 42.00, NULL, 'China sellers $33-40. Core4Solutions $34.95.'),
    ('Mellanox ConnectX-5 25GbE MCX512A', 'Mellanox ConnectX-5 25GbE SFP28 network adapter MCX512A', 'MCX512A-ACAT', 'ConnectX-5', '51167', 'ebay', 50.00, 0.2, 60, true, 600, 25.00, 65.00, NULL, 'EOL Jan 2025 = liquidation inventory.'),
    ('Mellanox ConnectX-6 100GbE MCX653106A', 'Mellanox ConnectX-6 100GbE QSFP28 network adapter MCX653106A', 'MCX653106A-ECAT', 'ConnectX-6', '51167', 'ebay', 550.00, 0.15, 65, true, 600, 424.00, 649.00, NULL, '100GbE holds value. $500-650 used.'),
    ('Intel P5510 1.92TB U.2', 'Intel P5510 1.92TB U.2 NVMe enterprise SSD', 'SSDPE2KX019T801', 'P5510', '56083', 'ebay', 360.00, 0.15, 60, true, 600, 300.00, 400.00, NULL, 'Consider older P4510 at $150-250 as budget alternative.'),
    ('Intel P5510 3.84TB U.2', 'Intel P5510 3.84TB U.2 NVMe enterprise SSD', 'SSDPE2KX038T801', 'P5510-4T', '56083', 'ebay', 500.00, 0.1, 60, true, 600, 400.00, 545.00, NULL, 'Best $/TB among P5510 sizes.'),
    ('Samsung PM9A3 1.92TB U.2', 'Samsung PM9A3 1.92TB U.2 NVMe enterprise SSD', 'MZQL21T9HCJR', 'PM9A3', '56083', 'ebay', 560.00, 0.1, 60, true, 600, 450.00, 607.00, NULL, 'Samsung brand premium. Offer 10% below BIN.'),
    ('Samsung PM9A3 3.84TB U.2', 'Samsung PM9A3 3.84TB U.2 NVMe enterprise SSD', 'MZQL23T8HCLS', 'PM9A3-4T', '56083', 'ebay', 920.00, 0.1, 65, true, 600, 750.00, 1023.00, NULL, 'Most expensive U.2 drive. Good performance but costly.'),
    ('Micron 7450 1.92TB U.2', 'Micron 7450 1.92TB U.2 NVMe enterprise SSD', 'MTFDKCB1T9TFS-1BC1ZABYY', '7450', '56083', 'ebay', 440.00, 0.1, 60, true, 600, 350.00, 475.00, NULL, 'Good availability. Best value current-gen U.2.'),
    ('Micron 7450 Pro 3.84TB U.2', 'Micron 7450 Pro 3.84TB U.2 NVMe enterprise SSD', 'MTFDKCB3T8TFS-1BC15ABYY', '7450-4T', '56083', 'ebay', 620.00, 0.1, 60, true, 600, 500.00, 673.00, NULL, 'Best $/TB at ~$162/TB. $500 was anomaly listing.'),
    ('Seagate Exos X16 16TB', 'Seagate Exos X16 16TB ST16000NM001G enterprise HDD SATA', 'ST16000NM001G', 'ST16000NM001G', '56083', 'ebay', 230.00, 0.15, 60, true, 600, 180.00, 268.00, 'exX16T', 'Best all-rounder. 4x RAIDZ2 = 32TB usable ~$920.'),
    ('Seagate Exos X18 18TB', 'Seagate Exos X18 18TB ST18000NM000J enterprise HDD SATA', 'ST18000NM000J', 'ST18000NM000J', '56083', 'ebay', 270.00, 0.1, 60, true, 600, 220.00, 296.00, 'exX18T', '$16.44/TB. 4x RAIDZ2 = 36TB usable ~$1,080.'),
    ('WD Ultrastar HC550 16TB', 'WD Ultrastar HC550 16TB WUH721816ALE6L4 enterprise HDD SATA', 'WUH721816ALE6L4', 'WUH721816ALE6L4', '56083', 'ebay', 265.00, 0.1, 60, true, 600, 200.00, 295.00, 'hc5516', 'Reliable alternative to Exos. $18.44/TB.'),
    ('WD Ultrastar HC550 18TB', 'WD Ultrastar HC550 18TB WUH721818ALE6L4 enterprise HDD SATA', 'WUH721818ALE6L4', 'WUH721818ALE6L4', '56083', 'ebay', 260.00, 0.1, 60, true, 600, 200.00, 280.00, 'hc5518', 'BEST $/TB at $15.56/TB! 4x RAIDZ2 = 36TB usable ~$1,040. RECOMMENDED.'),
    ('Toshiba MG08 16TB', 'Toshiba MG08 16TB MG08ACA16TE enterprise HDD SATA', 'MG08ACA16TE', 'MG08ACA16TE', '56083', 'ebay', 330.00, 0.08, 55, true, 600, 280.00, 350.00, NULL, 'Higher $/TB ($21.88) but good reliability. Less common on eBay.'),
    ('Toshiba MG09 18TB', 'Toshiba MG09 18TB MG09ACA18TE enterprise HDD SATA', 'MG09ACA18TE', 'MG09ACA18TE', '56083', 'ebay', 290.00, 0.08, 55, true, 600, 240.00, 310.00, 'mg0918', '$17.22/TB. Good middle ground between Exos and Ultrastar.'),
    ('GPU Support Bracket Anti-Sag', 'GPU support bracket anti sag holder workstation', '', '', '42014', 'ebay', 7.00, 0.3, 50, true, 1200, 4.00, 10.00, NULL, 'Pure commodity. China $4-8. Do not overpay.'),
    ('SilverStone RM52 Rack Rails', 'SilverStone RM52 rack rails mounting kit RMS05-22', 'RMS05-22', 'RMS05-22', '42014', 'ebay', 85.00, 0.15, 55, true, 1200, 70.00, 100.00, NULL, 'Proprietary, no alternatives. Consider universal rack shelf.')
ON CONFLICT (name) DO UPDATE SET
    keywords = EXCLUDED.keywords,
    sku = EXCLUDED.sku,
    mpn = EXCLUDED.mpn,
    category_id = EXCLUDED.category_id,
    marketplace = EXCLUDED.marketplace,
    target_price = EXCLUDED.target_price,
    alert_threshold = EXCLUDED.alert_threshold,
    min_deal_score = EXCLUDED.min_deal_score,
    is_enabled = EXCLUDED.is_enabled,
    search_interval = EXCLUDED.search_interval,
    scam_floor = EXCLUDED.scam_floor,
    benchmark_median = EXCLUDED.benchmark_median,
    pcpp_product_id = EXCLUDED.pcpp_product_id,
    notes = EXCLUDED.notes;

-- Default admin user (password: admin123)
INSERT INTO users (username, email, hashed_password, is_admin) VALUES
    ('admin', 'admin@localhost', '$2b$12$X.hvC98a9KtnrqRDFGl0FOKZ9abfWb.jKFdLJOHhjbHmW9YfrzDSy', true)
    ON CONFLICT (username) DO NOTHING;

-- Default notification settings
INSERT INTO notification_settings (user_id, telegram_enabled, email_enabled, email_digest_mode, telegram_min_score, email_min_score)
    VALUES (1, false, false, 'daily', 70, 50)
    ON CONFLICT (user_id) DO NOTHING;
