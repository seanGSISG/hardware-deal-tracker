-- Seed data for Hardware Deal Tracker
-- GENERATED FILE — do not edit by hand.
-- Source of truth: app/services/ebay/catalog.py
-- Regenerate with: make seed-regen
--
-- OPTIONAL starter data (ADR-005): the app runs from an empty catalog.

INSERT INTO tracked_items (name, keywords, sku, mpn, category_id, marketplace, target_price, alert_threshold, min_deal_score, is_enabled, search_interval, scam_floor, benchmark_median, pcpp_product_id, notes) VALUES
    ('AMD EPYC 7F72', 'AMD EPYC 7F72 server CPU processor SP3', '100-000000336', '7F72', '164', 'ebay', 325.00, 0.15, 60, true, 300, 280.00, 375.00, NULL, 'Abundant China supply. Make offers at $320-340.'),
    ('AMD EPYC 7543P', 'AMD EPYC 7543P server CPU processor SP3', '100-000000341', '7543P', '164', 'ebay', 750.00, 0.15, 60, true, 300, 480.00, 900.00, NULL, '32C/64T Milan, 256MB L3, single-socket P-variant (cheaper than 7543). Buy <$750. Flag <$480 as suspicious (vendor-locked/fake). Combos price >$1500 so this part-only target ignores them. Build CPU — P0 5min poll.'),
    ('Supermicro H12SSL-CT', 'Supermicro H12SSL-CT motherboard SP3 EPYC', 'MBD-H12SSL-CT-O', 'H12SSL-CT', '1244', 'ebay', 650.00, 0.1, 65, true, 300, 500.00, 634.00, NULL, 'Pre-owned risen from $620. Watch for open-box at $600-700.'),
    ('Supermicro H12SSL-i', 'Supermicro H12SSL-i motherboard SP3 EPYC', 'MBD-H12SSL-i-O', 'H12SSL-i', '1244', 'ebay', 600.00, 0.12, 65, true, 300, 400.00, 720.00, NULL, 'ATX single-socket SP3, 5x PCIe4 x16 (GPU-ready). Cheaper -i variant (no onboard HBA/10GbE vs -CT). Buy <$600. Board supply thin, expect to wait for a dip. Build board — P0 5min poll.'),
    ('ASRock Rack ROMED8-2T', 'ASRock Rack ROMED8-2T motherboard SP3 EPYC', 'ROMED8-2T', 'ROMED8-2T', '1244', 'ebay', 780.00, 0.12, 60, true, 300, 520.00, 1003.00, NULL, 'Retuned target 900->780 per Sean (2026-06-19), realistic fair-price alert. Live median ~$1003. New boards $1,000-1,080. Build board — P0 5min poll.'),
    ('NVIDIA RTX PRO 6000 Blackwell 96GB', 'NVIDIA RTX PRO 6000 Blackwell Workstation 96GB GPU', '900-5G180-2550-000', 'RTX PRO 6000', '27386', 'ebay', 6500.00, 0.1, 70, true, 1800, 7000.00, 7999.00, 'pX6000', 'SCAM WARNING: Listings below $7,000 are confirmed scams. Too new for used market.'),
    ('NVIDIA RTX PRO 4000 Blackwell SFF', 'NVIDIA RTX PRO 4000 Blackwell SFF workstation GPU', '900-5G173-2550-000', 'RTX PRO 4000', '27386', 'ebay', 1350.00, 0.12, 60, true, 600, 1400.00, 1700.00, 'pR4000', 'Cheaper same-slot fallback for the build GPU. New card, no used market yet. $1,599 retail.'),
    ('Samsung 64GB DDR4-2933 ECC M393A8G40MB2-CVF', 'Samsung M393A8G40MB2-CVF 64GB DDR4 ECC RDIMM server memory', 'M393A8G40MB2-CVF', 'M393A8G40MB2-CVF', '170083', 'ebay', 350.00, 0.2, 60, true, 600, 250.00, 450.00, NULL, 'Retuned to live eBay 2026-06-30 (Browse active asks, n=28): cluster $450-521, rare dip to $89. DDR4 prices RISING.'),
    ('Samsung 64GB DDR4-3200 ECC M393A8G40AB2-CWE', 'Samsung M393A8G40AB2-CWE 64GB DDR4 ECC RDIMM server memory', 'M393A8G40AB2-CWE', 'M393A8G40AB2-CWE', '170083', 'ebay', 480.00, 0.2, 60, true, 600, 340.00, 620.00, NULL, 'Retuned to live eBay 2026-06-30 (Browse active asks, n=26): $500-668, no sub-$500 (Samsung premium). Homelab/Reddit lots ~$90/unit but rarely on eBay.'),
    ('Micron 64GB DDR4-2933 ECC MTA36ASF8G72PZ-2G9', 'Micron MTA36ASF8G72PZ-2G9 64GB DDR4 ECC RDIMM server memory', 'MTA36ASF8G72PZ-2G9', 'MTA36ASF8G72PZ-2G9', '170083', 'ebay', 365.00, 0.2, 60, true, 600, 260.00, 470.00, NULL, 'Retuned to live eBay 2026-06-30 (Browse active asks, n=13): floor $396, cluster ~$480.'),
    ('Hynix 64GB DDR4-2933 ECC HMAA8GR7CJR4N-WM', 'SK Hynix HMAA8GR7CJR4N-WM 64GB DDR4 ECC RDIMM server memory', 'HMAA8GR7CJR4N-WM', 'HMAA8GR7CJR4N-WM', '170083', 'ebay', 365.00, 0.25, 65, true, 600, 260.00, 470.00, NULL, 'Retuned to live eBay 2026-06-30 (Browse active asks, thin n=2, ~$488). Expensive/rare; watch Walmart/surplus.'),
    ('Hynix 64GB DDR4-2933 ECC HMAA8GR7AJR4N-WM', 'SK Hynix HMAA8GR7AJR4N-WM 64GB DDR4 ECC RDIMM server memory', 'HMAA8GR7AJR4N-WM', 'HMAA8GR7AJR4N-WM', '170083', 'ebay', 330.00, 0.25, 65, true, 600, 240.00, 430.00, NULL, 'Retuned to live eBay 2026-06-30 (Browse active asks, n=21): floor $281, p25 $379, cluster ~$488.'),
    ('Hynix 64GB DDR4-3200 ECC HMAA8GR7AJR4N-XN', 'SK Hynix HMAA8GR7AJR4N-XN 64GB DDR4 ECC RDIMM server memory', 'HMAA8GR7AJR4N-XN', 'HMAA8GR7AJR4N-XN', '170083', 'ebay', 460.00, 0.2, 60, true, 1200, 330.00, 590.00, NULL, 'QVL DDR4-3200 watch (2026-06-30). Priced via dev eBay Browse API 2026-06-30 (active BIN asks, floor-anchored).'),
    ('Micron 64GB DDR4-3200 ECC MTA36ASF8G72PZ-3G2E1VI', 'Micron MTA36ASF8G72PZ-3G2E1VI 64GB DDR4 ECC RDIMM server memory', 'MTA36ASF8G72PZ-3G2E1VI', 'MTA36ASF8G72PZ-3G2E1VI', '170083', 'ebay', 340.00, 0.2, 60, true, 1200, 235.00, 430.00, NULL, 'QVL DDR4-3200 watch (2026-06-30). Cell die OBE45D9XPC. Priced via dev eBay Browse API 2026-06-30 (active BIN asks, floor-anchored).'),
    ('Micron 64GB DDR4-3200 ECC MTA36ASF8G72PZ-3G2E1TI', 'Micron MTA36ASF8G72PZ-3G2E1TI 64GB DDR4 ECC RDIMM server memory', 'MTA36ASF8G72PZ-3G2E1TI', 'MTA36ASF8G72PZ-3G2E1TI', '170083', 'ebay', 310.00, 0.2, 60, true, 1200, 220.00, 400.00, NULL, 'QVL DDR4-3200 watch (2026-06-30). Cell die OAE45D9XPC. Priced via dev eBay Browse API 2026-06-30 (active BIN asks, floor-anchored).'),
    ('Crucial 32GB DDR4-3200 ECC CT32G4RFD432A.36FE2', 'Crucial CT32G4RFD432A 32GB DDR4 ECC RDIMM server memory', 'CT32G4RFD432A.36FE2', 'CT32G4RFD432A.36FE2', '170083', 'ebay', 185.00, 0.2, 60, true, 1200, 140.00, 250.00, NULL, 'QVL DDR4-3200 watch (2026-06-30). One row for both cell dies on the QVL (9CE75D9WFK / 8SE75D9WFK — same module P/N). Priced via dev eBay Browse API 2026-06-30 (active BIN asks, floor-anchored).'),
    ('Innodisk 32GB DDR4-3200 ECC M4R0-BGS2BCEM-J02', 'Innodisk M4R0-BGS2BCEM-J02 32GB DDR4 ECC RDIMM server memory', 'M4R0-BGS2BCEM-J02', 'M4R0-BGS2BCEM-J02', '170083', 'ebay', 185.00, 0.2, 60, true, 1200, 140.00, 250.00, NULL, 'QVL DDR4-3200 watch (2026-06-30). Samsung K4AAG085WA die. Priced via dev eBay Browse API 2026-06-30 (active BIN asks, floor-anchored).'),
    ('Kingston 32GB DDR4-3200 ECC KSM32RD4/32MEI', 'Kingston KSM32RD4/32MEI 32GB DDR4 ECC RDIMM server memory', 'KSM32RD4/32MEI', 'KSM32RD4/32MEI', '170083', 'ebay', 185.00, 0.2, 60, true, 1200, 140.00, 250.00, NULL, 'QVL DDR4-3200 watch (2026-06-30). Priced via dev eBay Browse API 2026-06-30 (active BIN asks, floor-anchored).'),
    ('Micron 32GB DDR4-3200 ECC MTA18ASF4G72PZ-3G2F1UI', 'Micron MTA18ASF4G72PZ-3G2F1UI 32GB DDR4 ECC RDIMM server memory', 'MTA18ASF4G72PZ-3G2F1UI', 'MTA18ASF4G72PZ-3G2F1UI', '170083', 'ebay', 185.00, 0.2, 60, true, 1200, 140.00, 250.00, NULL, 'QVL DDR4-3200 watch (2026-06-30). Cell die IRF75D8CJT. Priced via dev eBay Browse API 2026-06-30 (active BIN asks, floor-anchored).'),
    ('Micron 32GB DDR4-3200 ECC MTA18ASF4G72PDZ-3G2E1UI', 'Micron MTA18ASF4G72PDZ-3G2E1UI 32GB DDR4 ECC RDIMM server memory', 'MTA18ASF4G72PDZ-3G2E1UI', 'MTA18ASF4G72PDZ-3G2E1UI', '170083', 'ebay', 185.00, 0.2, 60, true, 1200, 140.00, 250.00, NULL, 'QVL DDR4-3200 watch (2026-06-30). Cell die OBE45D9ZFV. Priced via dev eBay Browse API 2026-06-30 (active BIN asks, floor-anchored).'),
    ('Micron 32GB DDR4-3200 ECC MTA18ASF4G72PZ-3G2F1TI', 'Micron MTA18ASF4G72PZ-3G2F1TI 32GB DDR4 ECC RDIMM server memory', 'MTA18ASF4G72PZ-3G2F1TI', 'MTA18ASF4G72PZ-3G2F1TI', '170083', 'ebay', 185.00, 0.2, 60, true, 1200, 140.00, 250.00, NULL, 'QVL DDR4-3200 watch (2026-06-30). Cell die ISF75D8CJT. Priced via dev eBay Browse API 2026-06-30 (active BIN asks, floor-anchored).'),
    ('Micron 32GB DDR4-3200 ECC MTA18ASF4G72PDZ-3G2F1VI', 'Micron MTA18ASF4G72PDZ-3G2F1VI 32GB DDR4 ECC RDIMM server memory', 'MTA18ASF4G72PDZ-3G2F1VI', 'MTA18ASF4G72PDZ-3G2F1VI', '170083', 'ebay', 185.00, 0.2, 60, true, 1200, 140.00, 250.00, NULL, 'QVL DDR4-3200 watch (2026-06-30). Cell die ISF75D8CJV. Priced via dev eBay Browse API 2026-06-30 (active BIN asks, floor-anchored).'),
    ('SMART 32GB DDR4-3200 ECC STB724G4ASR32P2-FM', 'SMART STB724G4ASR32P2-FM 32GB DDR4 ECC RDIMM server memory', 'STB724G4ASR32P2-FM', 'STB724G4ASR32P2-FM', '170083', 'ebay', 185.00, 0.2, 60, true, 1200, 140.00, 250.00, NULL, 'QVL DDR4-3200 watch (2026-06-30). Micron 3ER75D8BPH die. Priced via dev eBay Browse API 2026-06-30 (active BIN asks, floor-anchored).'),
    ('Intel P5510 1.92TB U.2', 'Intel P5510 1.92TB U.2 NVMe enterprise SSD', 'SSDPE2KX019T801', 'P5510', '175669', 'ebay', 360.00, 0.15, 60, true, 1200, 300.00, 400.00, NULL, 'Consider older P4510 at $150-250 as budget alternative.'),
    ('Intel P5510 3.84TB U.2', 'Intel P5510 3.84TB U.2 NVMe enterprise SSD', 'SSDPE2KX038T801', 'P5510-4T', '175669', 'ebay', 500.00, 0.1, 60, true, 1200, 400.00, 545.00, NULL, 'Best $/TB among P5510 sizes.'),
    ('Samsung PM9A3 1.92TB U.2', 'Samsung PM9A3 1.92TB U.2 NVMe enterprise SSD', 'MZQL21T9HCJR', 'PM9A3', '175669', 'ebay', 560.00, 0.1, 60, true, 1200, 450.00, 607.00, NULL, 'Samsung brand premium. Offer 10% below BIN.'),
    ('Samsung PM9A3 3.84TB U.2', 'Samsung PM9A3 3.84TB U.2 NVMe enterprise SSD', 'MZQL23T8HCLS', 'PM9A3-4T', '175669', 'ebay', 920.00, 0.1, 65, true, 1200, 750.00, 1023.00, NULL, 'Most expensive U.2 drive. Good performance but costly.'),
    ('Micron 7450 1.92TB U.2', 'Micron 7450 1.92TB U.2 NVMe enterprise SSD', 'MTFDKCB1T9TFS-1BC1ZABYY', '7450', '175669', 'ebay', 440.00, 0.1, 60, true, 1200, 350.00, 475.00, NULL, 'Good availability. Best value current-gen U.2.'),
    ('Micron 7450 Pro 3.84TB U.2', 'Micron 7450 Pro 3.84TB U.2 NVMe enterprise SSD', 'MTFDKCB3T8TFS-1BC15ABYY', '7450-4T', '175669', 'ebay', 620.00, 0.1, 60, true, 1200, 500.00, 673.00, NULL, 'Best $/TB at ~$162/TB. $500 was anomaly listing.'),
    ('Seagate Exos X16 16TB', 'Seagate Exos X16 16TB ST16000NM001G enterprise HDD SATA', 'ST16000NM001G', 'ST16000NM001G', '56083', 'ebay', 230.00, 0.15, 60, true, 1200, 180.00, 268.00, 'exX16T', 'Best all-rounder. 4x RAIDZ2 = 32TB usable ~$920.'),
    ('Seagate Exos X18 18TB', 'Seagate Exos X18 18TB ST18000NM000J enterprise HDD SATA', 'ST18000NM000J', 'ST18000NM000J', '56083', 'ebay', 270.00, 0.1, 60, true, 1200, 220.00, 296.00, 'exX18T', '$16.44/TB. 4x RAIDZ2 = 36TB usable ~$1,080.'),
    ('WD Ultrastar HC550 16TB', 'WD Ultrastar HC550 16TB WUH721816ALE6L4 enterprise HDD SATA', 'WUH721816ALE6L4', 'WUH721816ALE6L4', '56083', 'ebay', 265.00, 0.1, 60, true, 1200, 200.00, 295.00, 'hc5516', 'Reliable alternative to Exos. $18.44/TB.'),
    ('WD Ultrastar HC550 18TB', 'WD Ultrastar HC550 18TB WUH721818ALE6L4 enterprise HDD SATA', 'WUH721818ALE6L4', 'WUH721818ALE6L4', '56083', 'ebay', 260.00, 0.1, 60, true, 1200, 200.00, 280.00, 'hc5518', 'BEST $/TB at $15.56/TB! 4x RAIDZ2 = 36TB usable ~$1,040. RECOMMENDED.'),
    ('Toshiba MG08 16TB', 'Toshiba MG08 16TB MG08ACA16TE enterprise HDD SATA', 'MG08ACA16TE', 'MG08ACA16TE', '56083', 'ebay', 330.00, 0.08, 55, true, 1200, 280.00, 350.00, NULL, 'Higher $/TB ($21.88) but good reliability. Less common on eBay.'),
    ('Toshiba MG09 18TB', 'Toshiba MG09 18TB MG09ACA18TE enterprise HDD SATA', 'MG09ACA18TE', 'MG09ACA18TE', '56083', 'ebay', 290.00, 0.08, 55, true, 1200, 240.00, 310.00, 'mg0918', '$17.22/TB. Good middle ground between Exos and Ultrastar.')
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
