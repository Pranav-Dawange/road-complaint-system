-- ============================================================
-- Road Complaint Management System — Seed Data (with GPS)
-- Run AFTER schema.sql on a FRESH database
-- NOTE: Sample USER accounts are created automatically by the
--       FastAPI startup event (main.py) — no SQL needed here.
-- ============================================================

USE road_complaint_db;

-- ============================================================
-- 1. OFFICER (ward_id set NULL initially — updated after WARD insert)
-- ============================================================
INSERT INTO OFFICER (name, phone, designation, ward_id) VALUES
('Rajesh Kumar',  '9876540001', 'Ward Officer',     NULL),
('Sunita Patil',  '9876540002', 'Senior Inspector', NULL),
('Mohan Desai',   '9876540003', 'Ward Officer',     NULL),
('Priya Sharma',  '9876540004', 'Junior Officer',   NULL),
('Anil Bhosale',  '9876540005', 'Senior Inspector', NULL);

-- ============================================================
-- 2. WARD
-- ============================================================
INSERT INTO WARD (ward_name, city, officer_id) VALUES
('Shivajinagar', 'Pune', 1),
('Kothrud',      'Pune', 2),
('Hadapsar',     'Pune', 3),
('Warje',        'Pune', 4),
('Aundh',        'Pune', 5),
('Yerwada',      'Pune', 1),
('Kasba Peth',   'Pune', 2),
('Bhavani Peth', 'Pune', 3),
('Wanwadi',      'Pune', 4),
('Kondhwa',      'Pune', 5),
('Dhankawadi',   'Pune', 1),
('Sahakarnagar', 'Pune', 2),
('Tilak Road',   'Pune', 3),
('Baner',        'Pune', 4),
('Viman Nagar',  'Pune', 5);

-- Link officers back to their wards
UPDATE OFFICER SET ward_id = 1 WHERE officer_id = 1;
UPDATE OFFICER SET ward_id = 2 WHERE officer_id = 2;
UPDATE OFFICER SET ward_id = 3 WHERE officer_id = 3;
UPDATE OFFICER SET ward_id = 4 WHERE officer_id = 4;
UPDATE OFFICER SET ward_id = 5 WHERE officer_id = 5;

-- ============================================================
-- 3. WORKER  (with base GPS coords for Upgrade 4 auto-assign)
-- ============================================================
INSERT INTO WORKER (name, phone, skill_type, ward_id, is_available, base_latitude, base_longitude) VALUES
('Suresh Kale',     '9000000001', 'road',       1, TRUE,  18.5308, 73.8474),
('Dinesh Wagh',     '9000000002', 'drainage',   1, TRUE,  18.5250, 73.8500),
('Kavita Jagtap',   '9000000003', 'electrical', 2, TRUE,  18.5074, 73.8077),
('Ravi More',       '9000000004', 'road',       2, FALSE, 18.5040, 73.8120),
('Santosh Gaikwad', '9000000005', 'road',       3, TRUE,  18.5089, 73.9260),
('Pooja Nikam',     '9000000006', 'drainage',   3, TRUE,  18.5000, 73.9200),
('Mahesh Salve',    '9000000007', 'road',       4, TRUE,  18.4854, 73.8026),
('Vijay Jadhav',    '9000000008', 'electrical', 5, FALSE, 18.5579, 73.8076);

-- ============================================================
-- 4. CITIZEN (10 citizens)
-- ============================================================
INSERT INTO CITIZEN (name, phone, email, address, ward_no) VALUES
('Aarav Mehta',      '9100000001', 'aarav@email.com',   '12 MG Road, Shivajinagar',       1),
('Sneha Joshi',      '9100000002', 'sneha@email.com',   '34 Paud Road, Kothrud',          2),
('Rahul Pawar',      '9100000003', 'rahul@email.com',   '5 Hadapsar Link Rd, Hadapsar',   3),
('Divya Kulkarni',   '9100000004', 'divya@email.com',   '78 Sus Road, Warje',             4),
('Amit Shinde',      '9100000005', 'amit@email.com',    '22 ITI Road, Aundh',             5),
('Priya Naik',       '9100000006', 'priya@email.com',   '9 Deccan Gymkhana, Shivajinagar',1),
('Vishal Deshpande', '9100000007', 'vishal@email.com',  '11 Karve Road, Kothrud',         2),
('Anita Bapat',      '9100000008', 'anita@email.com',   '56 Undri Road, Hadapsar',        3),
('Suraj Tiwari',     '9100000009', 'suraj@email.com',   '30 Warje Road, Warje',           4),
('Meera Chopra',     '9100000010', 'meera@email.com',   '15 Baner Road, Aundh',           5);

-- ============================================================
-- 5. COMPLAINT (15 complaints — with Pune GPS coordinates)
-- Pune Ward GPS reference:
--   Shivajinagar: 18.5308, 73.8474
--   Kothrud:      18.5074, 73.8077
--   Hadapsar:     18.5089, 73.9260
--   Warje:        18.4854, 73.8026
--   Aundh:        18.5579, 73.8076
-- ============================================================
INSERT INTO COMPLAINT
  (citizen_id, ward_id, worker_id, description, damage_type, severity, status,
   address, latitude, longitude, filed_at, resolved_at)
VALUES
-- Ward 1: Shivajinagar
(1, 1, 1, 'Large pothole near bus stop causing accidents',         'pothole',      'critical', 'resolved',    '12 MG Road, Shivajinagar',         18.5310, 73.8476, DATE_SUB(NOW(), INTERVAL 15 DAY), DATE_SUB(NOW(), INTERVAL 5 DAY)),
(6, 1, NULL,'Multiple cracks on footpath near Deccan',            'crack',        'low',      'open',        '9 Deccan Gymkhana, Shivajinagar',   18.5200, 73.8400, DATE_SUB(NOW(), INTERVAL 12 DAY), NULL),
(3, 1, 2, 'Waterlogging near society gate every monsoon',         'waterlogging', 'medium',   'resolved',    'FC Road, Shivajinagar',             18.5260, 73.8530, DATE_SUB(NOW(), INTERVAL 25 DAY), DATE_SUB(NOW(), INTERVAL 15 DAY)),

-- Ward 2: Kothrud
(2, 2, 3, 'Road crack spreading across 20m on Paud Road',         'crack',        'medium',   'in_progress', '34 Paud Road, Kothrud',             18.5074, 73.8077, DATE_SUB(NOW(), INTERVAL 10 DAY), NULL),
(7, 2, 4, 'Severe pothole causing bike accidents on Karve Road',  'pothole',      'critical', 'resolved',    '11 Karve Road, Kothrud',            18.5050, 73.8100, DATE_SUB(NOW(), INTERVAL 20 DAY), DATE_SUB(NOW(), INTERVAL 8 DAY)),
(1, 2, NULL,'Pothole near school gate worsening',                 'pothole',      'medium',   'open',        '40 Karve Road, Kothrud',            18.5070, 73.8060, DATE_SUB(NOW(), INTERVAL 1 DAY),  NULL),

-- Ward 3: Hadapsar
(3, 3, 5, 'Waterlogging blocking colony entrance after rain',     'waterlogging', 'critical', 'open',        '5 Hadapsar Link Rd, Hadapsar',      18.5089, 73.9260, DATE_SUB(NOW(), INTERVAL 9 DAY),  NULL),
(8, 3, 6, 'Drainage overflow causing waterlogging on road',       'waterlogging', 'medium',   'in_progress', '56 Undri Road, Hadapsar',           18.4900, 73.9200, DATE_SUB(NOW(), INTERVAL 6 DAY),  NULL),
(5, 3, NULL,'Big crack developed after rain near hospital',       'crack',        'critical', 'open',        'Hadapsar Hospital Road, Hadapsar',  18.5150, 73.9350, DATE_SUB(NOW(), INTERVAL 9 DAY),  NULL),

-- Ward 4: Warje
(4, 4, 7, 'Road surface subsidence near market',                  'subsidence',   'critical', 'open',        '78 Sus Road, Warje',                18.4854, 73.8026, DATE_SUB(NOW(), INTERVAL 3 DAY),  NULL),
(9, 4, NULL,'Road crack at main junction',                        'crack',        'medium',   'open',        '30 Warje Road, Warje',              18.4800, 73.7900, DATE_SUB(NOW(), INTERVAL 2 DAY),  NULL),
(6, 4, 7, 'Multiple potholes after heavy rainfall',               'pothole',      'medium',   'in_progress', 'Maharashtra Housing, Warje',         18.4820, 73.7960, DATE_SUB(NOW(), INTERVAL 4 DAY),  NULL),

-- Ward 5: Aundh
(5, 5, NULL,'Pothole on main road near school',                   'pothole',      'critical', 'open',        '22 ITI Road, Aundh',                18.5579, 73.8076, DATE_SUB(NOW(), INTERVAL 8 DAY),  NULL),
(10,5, 8, 'Subsidence near old building — road depression',       'subsidence',   'critical', 'in_progress', '15 Baner Road, Aundh',              18.5600, 73.7850, DATE_SUB(NOW(), INTERVAL 7 DAY),  NULL),
(8, 5, NULL,'New subsidence point forming near park entrance',    'subsidence',   'low',      'open',        'Aundh Park Road, Aundh',            18.5630, 73.8120, DATE_SUB(NOW(), INTERVAL 10 DAY), NULL);

-- ============================================================
-- 6. COMPLAINT_LOG (manual audit entries for pre-changed complaints)
-- Future changes will be handled by the trigger automatically.
-- ============================================================
INSERT INTO COMPLAINT_LOG (complaint_id, old_status, new_status, changed_by, changed_at) VALUES
(1,  'open',        'in_progress', 'Officer_Rajesh',  DATE_SUB(NOW(), INTERVAL 12 DAY)),
(1,  'in_progress', 'resolved',    'Officer_Rajesh',  DATE_SUB(NOW(), INTERVAL 5 DAY)),
(4,  'open',        'in_progress', 'Officer_Sunita',  DATE_SUB(NOW(), INTERVAL 7 DAY)),
(5,  'open',        'in_progress', 'Officer_Sunita',  DATE_SUB(NOW(), INTERVAL 15 DAY)),
(5,  'in_progress', 'resolved',    'Officer_Sunita',  DATE_SUB(NOW(), INTERVAL 8 DAY)),
(8,  'open',        'in_progress', 'Officer_Mohan',   DATE_SUB(NOW(), INTERVAL 4 DAY)),
(14, 'open',        'in_progress', 'Officer_Anil',    DATE_SUB(NOW(), INTERVAL 5 DAY)),
(3,  'open',        'in_progress', 'Officer_Rajesh',  DATE_SUB(NOW(), INTERVAL 20 DAY)),
(3,  'in_progress', 'resolved',    'Officer_Rajesh',  DATE_SUB(NOW(), INTERVAL 15 DAY)),
(12, 'open',        'in_progress', 'Officer_Priya',   DATE_SUB(NOW(), INTERVAL 2 DAY));

-- ============================================================
-- NOTE: USER accounts (admin/officer1/citizen1) are created
-- automatically by the FastAPI startup event in main.py.
-- You do NOT need to insert them manually here.
-- ============================================================
