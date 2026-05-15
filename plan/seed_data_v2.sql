-- Seed data for Hardware Deal Tracker
-- UPDATED with research-validated prices (May 2026)
-- Source: 8 parallel research agents scanning eBay sold listings
--
-- Categories: CPU, Motherboards, Workstation GPUs, Inference GPUs, ECC Memory,
--   Chassis/Cooling/PSU, Networking, U.2 NVMe Storage, HDD 16TB+

-- Tracked items with validated deal alert targets
INSERT INTO tracked_items (name, keywords, sku, mpn, category_id, target_price, alert_threshold, min_deal_score, is_enabled, search_interval) VALUES
    ('AMD EPYC 7F72', 'AMD EPYC 7F72 server CPU processor SP3', '100-000000336', '7F72', '164', 325.0, 0.15, 60, true, 300),
    ('Supermicro H12SSL-CT', 'Supermicro H12SSL-CT motherboard SP3 EPYC', 'MBD-H12SSL-CT-O', 'H12SSL-CT', '1244', 650.0, 0.1, 65, true, 600),
    ('ASRock Rack ROMED8-2T', 'ASRock Rack ROMED8-2T motherboard SP3 EPYC', 'ROMED8-2T', 'ROMED8-2T', '1244', 900.0, 0.12, 60, true, 600),
    ('NVIDIA RTX PRO 6000 Blackwell 96GB', 'NVIDIA RTX PRO 6000 Blackwell Workstation 96GB GPU', '900-5G180-2550-000', 'RTX PRO 6000', '27386', 6500.0, 0.1, 70, true, 1200),
    ('NVIDIA RTX 6000 Ada 48GB', 'NVIDIA RTX 6000 Ada workstation GPU 48GB', '900-5G133-2500-000', 'RTX 6000 Ada', '27386', 4200.0, 0.12, 65, true, 600),
    ('NVIDIA RTX PRO 4000 Blackwell SFF', 'NVIDIA RTX PRO 4000 Blackwell SFF workstation GPU', '900-5G173-2550-000', 'RTX PRO 4000', '27386', 1350.0, 0.12, 60, true, 600),
    ('NVIDIA L4 24GB', 'NVIDIA L4 24GB GPU inference accelerator', '900-2G193-0000-000', 'L4', '27386', 2600.0, 0.15, 65, true, 600),
    ('NVIDIA T4 16GB', 'NVIDIA T4 16GB GPU inference accelerator', '900-2G183-0000-000', 'T4', '27386', 450.0, 0.2, 60, true, 300),
    ('Samsung 64GB DDR4-2933 ECC M393A8G40MB2-CVF', 'Samsung M393A8G40MB2-CVF 64GB DDR4 ECC RDIMM server memory', 'M393A8G40MB2-CVF', 'M393A8G40MB2-CVF', '170083', 135.0, 0.2, 60, true, 300),
    ('Samsung 64GB DDR4-3200 ECC M393A8G40AB2-CWE', 'Samsung M393A8G40AB2-CWE 64GB DDR4 ECC RDIMM server memory', 'M393A8G40AB2-CWE', 'M393A8G40AB2-CWE', '170083', 115.0, 0.2, 60, true, 300),
    ('Micron 64GB DDR4-2933 ECC MTA36ASF8G72PZ-2G9', 'Micron MTA36ASF8G72PZ-2G9 64GB DDR4 ECC RDIMM server memory', 'MTA36ASF8G72PZ-2G9', 'MTA36ASF8G72PZ-2G9', '170083', 125.0, 0.2, 60, true, 300),
    ('Hynix 64GB DDR4-2933 ECC HMAA8GR7CJR4N-WM', 'SK Hynix HMAA8GR7CJR4N-WM 64GB DDR4 ECC RDIMM server memory', 'HMAA8GR7CJR4N-WM', 'HMAA8GR7CJR4N-WM', '170083', 120.0, 0.25, 65, true, 300),
    ('Hynix 64GB DDR4-2933 ECC HMAA8GR7AJR4N-WM', 'SK Hynix HMAA8GR7AJR4N-WM 64GB DDR4 ECC RDIMM server memory', 'HMAA8GR7AJR4N-WM', 'HMAA8GR7AJR4N-WM', '170083', 120.0, 0.25, 65, true, 300),
    ('SilverStone RM52 5U Rackmount Chassis', 'SilverStone RM52 5U rackmount chassis server case', 'SST-RM52', 'RM52', '42014', 530.0, 0.1, 55, true, 1200),
    ('SilverStone RM44 4U Rackmount Chassis', 'SilverStone RM44 4U rackmount chassis server case', 'SST-RM44', 'RM44', '42014', 360.0, 0.12, 55, true, 1200),
    ('Alphacool Eisbaer Pro HPE Aurora 360', 'Alphacool Eisbaer Pro HPE Aurora 360 AIO CPU cooler SP3', '1019572', 'Eisbaer-Pro-HPE-Aurora-360', '42007', 210.0, 0.15, 55, true, 1200),
    ('Corsair HX1500i 2025 ATX 3.1', 'Corsair HX1500i 2025 ATX 3.1 power supply 1500W', 'CP-9020309-NA', 'HX1500i', '42006', 250.0, 0.15, 60, true, 1200),
    ('GPU Support Bracket Anti-Sag', 'GPU support bracket anti sag holder workstation', '', '', '42014', 7.0, 0.3, 50, true, 1200),
    ('SilverStone RM52 Rack Rails', 'SilverStone RM52 rack rails mounting kit RMS05-22', 'RMS05-22', 'RMS05-22', '42014', 85.0, 0.15, 55, true, 1200),
    ('Mellanox ConnectX-4 25GbE MCX4111A', 'Mellanox ConnectX-4 25GbE SFP28 network adapter MCX4111A', 'MCX4111A-ACAT', 'ConnectX-4', '51167', 30.0, 0.25, 60, true, 600),
    ('Mellanox ConnectX-5 25GbE MCX512A', 'Mellanox ConnectX-5 25GbE SFP28 network adapter MCX512A', 'MCX512A-ACAT', 'ConnectX-5', '51167', 50.0, 0.2, 60, true, 600),
    ('Mellanox ConnectX-6 100GbE MCX653106A', 'Mellanox ConnectX-6 100GbE QSFP28 network adapter MCX653106A', 'MCX653106A-ECAT', 'ConnectX-6', '51167', 550.0, 0.15, 65, true, 600),
    ('Intel P5510 1.92TB U.2', 'Intel P5510 1.92TB U.2 NVMe enterprise SSD', 'SSDPE2KX019T801', 'P5510', '56083', 360.0, 0.15, 60, true, 600),
    ('Intel P5510 3.84TB U.2', 'Intel P5510 3.84TB U.2 NVMe enterprise SSD', 'SSDPE2KX038T801', 'P5510-4T', '56083', 500.0, 0.1, 60, true, 600),
    ('Samsung PM9A3 1.92TB U.2', 'Samsung PM9A3 1.92TB U.2 NVMe enterprise SSD', 'MZQL21T9HCJR', 'PM9A3', '56083', 560.0, 0.1, 60, true, 600),
    ('Samsung PM9A3 3.84TB U.2', 'Samsung PM9A3 3.84TB U.2 NVMe enterprise SSD', 'MZQL23T8HCLS', 'PM9A3-4T', '56083', 920.0, 0.1, 65, true, 600),
    ('Micron 7450 1.92TB U.2', 'Micron 7450 1.92TB U.2 NVMe enterprise SSD', 'MTFDKCB1T9TFS-1BC1ZABYY', '7450', '56083', 440.0, 0.1, 60, true, 600),
    ('Micron 7450 Pro 3.84TB U.2', 'Micron 7450 Pro 3.84TB U.2 NVMe enterprise SSD', 'MTFDKCB3T8TFS-1BC15ABYY', '7450-4T', '56083', 620.0, 0.1, 60, true, 600),
    ('Seagate Exos X16 16TB SATA', 'Seagate Exos X16 16TB ST16000NM001G enterprise HDD SATA', 'ST16000NM001G', 'ST16000NM001G', '56083', 230.0, 0.15, 60, true, 600),
    ('Seagate Exos X18 18TB SATA', 'Seagate Exos X18 18TB ST18000NM000J enterprise HDD SATA', 'ST18000NM000J', 'ST18000NM000J', '56083', 270.0, 0.1, 60, true, 600),
    ('WD Ultrastar HC550 16TB SATA', 'WD Ultrastar HC550 16TB WUH721816ALE6L4 enterprise HDD SATA', 'WUH721816ALE6L4', 'WUH721816ALE6L4', '56083', 265.0, 0.1, 60, true, 600),
    ('WD Ultrastar HC550 18TB SATA', 'WD Ultrastar HC550 18TB WUH721818ALE6L4 enterprise HDD SATA', 'WUH721818ALE6L4', 'WUH721818ALE6L4', '56083', 260.0, 0.1, 60, true, 600),
    ('Toshiba MG08 16TB SATA', 'Toshiba MG08 16TB MG08ACA16TE enterprise HDD SATA', 'MG08ACA16TE', 'MG08ACA16TE', '56083', 330.0, 0.08, 55, true, 600),
    ('Toshiba MG09 18TB SATA', 'Toshiba MG09 18TB MG09ACA18TE enterprise HDD SATA', 'MG09ACA18TE', 'MG09ACA18TE', '56083', 290.0, 0.08, 55, true, 600);

-- Default admin user (password: admin123)
INSERT INTO users (username, email, hashed_password, is_admin) VALUES
    ('admin', 'admin@localhost', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', true)
    ON CONFLICT (username) DO NOTHING;

-- Default notification settings
INSERT INTO notification_settings (user_id, telegram_enabled, email_enabled, email_digest_mode, telegram_min_score, email_min_score)
    VALUES (1, false, false, 'daily', 70, 50)
    ON CONFLICT (user_id) DO NOTHING;