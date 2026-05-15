-- Seed data for Hardware Deal Tracker
-- Based on actual build plan: EPYC 7F72 + H12SSL-CT + RTX PRO 6000

INSERT INTO tracked_items (name, keywords, sku, mpn, category_id, target_price, alert_threshold, min_deal_score, is_enabled, search_interval) VALUES
    ('AMD EPYC 7F72', 'AMD EPYC 7F72 server CPU processor SP3', '100-000000336', '7F72', '164', 300.0, 0.25, 50, true, 300),
    ('Supermicro H12SSL-CT', 'Supermicro H12SSL-CT motherboard SP3 EPYC', 'MBD-H12SSL-CT-O', 'H12SSL-CT', '1244', 450.0, 0.2, 50, true, 600),
    ('ASRock Rack ROMED8-2T', 'ASRock Rack ROMED8-2T motherboard SP3 EPYC', 'ROMED8-2T', 'ROMED8-2T', '1244', 500.0, 0.2, 50, true, 600),
    ('NVIDIA RTX PRO 6000 Blackwell', 'NVIDIA RTX PRO 6000 Blackwell Workstation 96GB GPU', '900-5G180-2550-000', 'RTX PRO 6000', '27386', 4500.0, 0.1, 50, true, 1200),
    ('NVIDIA RTX PRO 4000 Blackwell SFF', 'NVIDIA RTX PRO 4000 Blackwell SFF workstation GPU', '900-5G173-2550-000', 'RTX PRO 4000', '27386', 900.0, 0.15, 50, true, 600),
    ('NVIDIA RTX 6000 Ada', 'NVIDIA RTX 6000 Ada workstation GPU 48GB', '900-5G133-2500-000', 'RTX 6000 Ada', '27386', 2800.0, 0.12, 50, true, 600),
    ('NVIDIA L4', 'NVIDIA L4 GPU inference accelerator 24GB', '900-2G193-0000-000', 'L4', '27386', 800.0, 0.2, 50, true, 600),
    ('NVIDIA T4', 'NVIDIA T4 GPU inference accelerator 16GB', '900-2G183-0000-000', 'T4', '27386', 150.0, 0.25, 50, true, 300),
    ('Samsung 64GB DDR4-2933 ECC M393A8G40MB2-CVF', 'Samsung M393A8G40MB2-CVF 64GB DDR4 ECC RDIMM server memory', 'M393A8G40MB2-CVF', 'M393A8G40MB2-CVF', '170083', 120.0, 0.25, 50, true, 300),
    ('Samsung 64GB DDR4-3200 ECC M393A8G40AB2-CWE', 'Samsung M393A8G40AB2-CWE 64GB DDR4 ECC RDIMM server memory', 'M393A8G40AB2-CWE', 'M393A8G40AB2-CWE', '170083', 125.0, 0.25, 50, true, 300),
    ('Micron 64GB DDR4-2933 ECC MTA36ASF8G72PZ-2G9', 'Micron MTA36ASF8G72PZ-2G9 64GB DDR4 ECC RDIMM server memory', 'MTA36ASF8G72PZ-2G9', 'MTA36ASF8G72PZ-2G9', '170083', 115.0, 0.25, 50, true, 300),
    ('Hynix 64GB DDR4-2933 ECC HMAA8GR7CJR4N-WM', 'SK Hynix HMAA8GR7CJR4N-WM 64GB DDR4 ECC RDIMM server memory', 'HMAA8GR7CJR4N-WM', 'HMAA8GR7CJR4N-WM', '170083', 115.0, 0.25, 50, true, 300),
    ('Hynix 64GB DDR4-2933 ECC HMAA8GR7AJR4N-WM', 'SK Hynix HMAA8GR7AJR4N-WM 64GB DDR4 ECC RDIMM server memory', 'HMAA8GR7AJR4N-WM', 'HMAA8GR7AJR4N-WM', '170083', 115.0, 0.25, 50, true, 300),
    ('SilverStone RM52 5U Rackmount Chassis', 'SilverStone RM52 5U rackmount chassis server case', 'SST-RM52', 'RM52', '42014', 300.0, 0.2, 50, true, 1200),
    ('SilverStone RM44 4U Rackmount Chassis', 'SilverStone RM44 4U rackmount chassis server case', 'SST-RM44', 'RM44', '42014', 250.0, 0.2, 50, true, 1200),
    ('Alphacool Eisbaer Pro HPE Aurora 360', 'Alphacool Eisbaer Pro HPE Aurora 360 AIO CPU cooler SP3', '1019572', 'Eisbaer-Pro-HPE-Aurora-360', '42007', 200.0, 0.15, 50, true, 1200),
    ('Corsair HX1500i 2025 ATX 3.1', 'Corsair HX1500i 2025 ATX 3.1 power supply 1500W', 'CP-9020309-NA', 'HX1500i', '42006', 350.0, 0.15, 50, true, 1200),
    ('Mellanox ConnectX-4 25GbE', 'Mellanox ConnectX-4 25GbE SFP28 network adapter MCX4111A', 'MCX4111A-ACAT', 'ConnectX-4', '51167', 30.0, 0.3, 50, true, 600),
    ('Mellanox ConnectX-5 25GbE', 'Mellanox ConnectX-5 25GbE SFP28 network adapter MCX512A', 'MCX512A-ACAT', 'ConnectX-5', '51167', 50.0, 0.25, 50, true, 600),
    ('Mellanox ConnectX-6 100GbE', 'Mellanox ConnectX-6 100GbE QSFP28 network adapter MCX653106A', 'MCX653106A-ECAT', 'ConnectX-6', '51167', 200.0, 0.25, 50, true, 600),
    ('Intel P5510 1.92TB U.2', 'Intel P5510 1.92TB U.2 NVMe enterprise SSD', 'SSDPE2KX019T801', 'P5510', '56083', 85.0, 0.25, 50, true, 600),
    ('Intel P5510 3.84TB U.2', 'Intel P5510 3.84TB U.2 NVMe enterprise SSD', 'SSDPE2KX038T801', 'P5510-4T', '56083', 150.0, 0.25, 50, true, 600),
    ('Samsung PM9A3 1.92TB U.2', 'Samsung PM9A3 1.92TB U.2 NVMe enterprise SSD', 'MZQL21T9HCJR', 'PM9A3', '56083', 90.0, 0.25, 50, true, 600),
    ('Samsung PM9A3 3.84TB U.2', 'Samsung PM9A3 3.84TB U.2 NVMe enterprise SSD', 'MZQL23T8HCLS', 'PM9A3-4T', '56083', 160.0, 0.25, 50, true, 600),
    ('Micron 7450 1.92TB U.2', 'Micron 7450 1.92TB U.2 NVMe enterprise SSD', 'MTFDKCB1T9TFS-1BC1ZABYY', '7450', '56083', 80.0, 0.25, 50, true, 600),
    ('Micron 7450 Pro 3.84TB U.2', 'Micron 7450 Pro 3.84TB U.2 NVMe enterprise SSD', 'MTFDKCB3T8TFS-1BC15ABYY', '7450-4T', '56083', 145.0, 0.25, 50, true, 600),
    ('GPU Support Bracket Anti-Sag', 'GPU support bracket anti sag holder workstation', '', '', '42014', 15.0, 0.3, 50, true, 1200),
    ('SilverStone RM52 Rack Rails', 'SilverStone RM52 rack rails mounting kit', '', '', '42014', 40.0, 0.2, 50, true, 1200);

-- Default admin user (password: admin123)
INSERT INTO users (username, email, hashed_password, is_admin) VALUES
    ('admin', 'admin@localhost', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', true)
    ON CONFLICT (username) DO NOTHING;

-- Default notification settings
INSERT INTO notification_settings (user_id, telegram_enabled, email_enabled, email_digest_mode, telegram_min_score, email_min_score)
    VALUES (1, false, false, 'daily', 70, 50)
    ON CONFLICT (user_id) DO NOTHING;