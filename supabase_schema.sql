-- ============================================================
-- Road Complaint Management System — Supabase / PostgreSQL Schema
-- Converted from MySQL by Antigravity (senior DB architect mode)
-- Run this on a FRESH Supabase project (SQL Editor → New Query)
-- ============================================================

-- ============================================================
-- SECTION 1 — ENUM TYPE DEFINITIONS
-- PostgreSQL requires ENUMs to be declared before first use.
-- ============================================================

CREATE TYPE skill_type_enum      AS ENUM ('road', 'drainage', 'electrical');
CREATE TYPE damage_type_enum     AS ENUM ('pothole', 'crack', 'waterlogging', 'subsidence');
CREATE TYPE severity_enum        AS ENUM ('low', 'medium', 'critical');
CREATE TYPE complaint_status_enum AS ENUM ('open', 'in_progress', 'resolved');
CREATE TYPE user_role_enum       AS ENUM ('citizen', 'officer', 'admin');


-- ============================================================
-- SECTION 2 — TABLE CREATION (dependency-ordered)
-- ============================================================

-- ----------------------------------------------------------
-- TABLE 1: OFFICER
-- Created before WARD because WARD references OFFICER.
-- The circular dependency (OFFICER.ward_id ↔ WARD.officer_id)
-- is broken by adding OFFICER first with ward_id nullable, then
-- adding the FK after WARD is created (same pattern as MySQL).
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS officer (
    officer_id   SERIAL        PRIMARY KEY,
    name         VARCHAR(100)  NOT NULL,
    phone        VARCHAR(15)   NOT NULL,
    designation  VARCHAR(100)  NOT NULL,
    ward_id      INT           -- FK added after WARD is created
);

-- ----------------------------------------------------------
-- TABLE 2: WARD
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS ward (
    ward_id    SERIAL        PRIMARY KEY,
    ward_name  VARCHAR(100)  NOT NULL,
    city       VARCHAR(100)  NOT NULL DEFAULT 'Pune',
    officer_id INT           REFERENCES officer(officer_id)
                             ON DELETE SET NULL
);

-- ----------------------------------------------------------
-- Now safe to add the FK from OFFICER back to WARD
-- ----------------------------------------------------------
ALTER TABLE officer
    ADD CONSTRAINT fk_officer_ward
        FOREIGN KEY (ward_id)
        REFERENCES ward(ward_id)
        ON DELETE SET NULL;

-- ----------------------------------------------------------
-- TABLE 3: CITIZEN
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS citizen (
    citizen_id  SERIAL        PRIMARY KEY,
    name        VARCHAR(100)  NOT NULL,
    phone       VARCHAR(15)   NOT NULL,
    email       VARCHAR(150),
    address     TEXT,
    ward_no     INT,
    CONSTRAINT uq_citizen_phone UNIQUE (phone)
);

-- ----------------------------------------------------------
-- TABLE 4: WORKER  (includes GPS base location)
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS worker (
    worker_id       SERIAL           PRIMARY KEY,
    name            VARCHAR(100)     NOT NULL,
    phone           VARCHAR(15)      NOT NULL,
    skill_type      skill_type_enum  NOT NULL,
    ward_id         INT              REFERENCES ward(ward_id) ON DELETE SET NULL,
    is_available    BOOLEAN          NOT NULL DEFAULT TRUE,
    base_latitude   DOUBLE PRECISION,
    base_longitude  DOUBLE PRECISION
);

-- ----------------------------------------------------------
-- TABLE 5: COMPLAINT  (includes GPS)
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS complaint (
    complaint_id  SERIAL               PRIMARY KEY,
    citizen_id    INT                  NOT NULL  REFERENCES citizen(citizen_id)  ON DELETE CASCADE,
    ward_id       INT                  NOT NULL  REFERENCES ward(ward_id)         ON DELETE CASCADE,
    worker_id     INT                            REFERENCES worker(worker_id)     ON DELETE SET NULL,
    description   TEXT                 NOT NULL,
    damage_type   damage_type_enum     NOT NULL,
    severity      severity_enum        NOT NULL,
    status        complaint_status_enum NOT NULL DEFAULT 'open',
    address       TEXT                 NOT NULL,
    photo_path    VARCHAR(255),
    latitude      DOUBLE PRECISION,
    longitude     DOUBLE PRECISION,
    filed_at      TIMESTAMPTZ          NOT NULL DEFAULT NOW(),
    resolved_at   TIMESTAMPTZ
);

-- ----------------------------------------------------------
-- TABLE 6: COMPLAINT_LOG  (auto-populated by trigger)
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS complaint_log (
    log_id       SERIAL       PRIMARY KEY,
    complaint_id INT          NOT NULL REFERENCES complaint(complaint_id) ON DELETE CASCADE,
    old_status   TEXT         NOT NULL,
    new_status   TEXT         NOT NULL,
    changed_by   VARCHAR(100) NOT NULL DEFAULT 'system_trigger',
    changed_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- ----------------------------------------------------------
-- TABLE 7: "user" — JWT Auth (note: quoted to avoid clash with
-- PostgreSQL reserved word; alternatively named app_user below)
-- DESIGN NOTE: Renamed to app_user to avoid quoting everywhere.
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS app_user (
    user_id         SERIAL          PRIMARY KEY,
    username        VARCHAR(100)    NOT NULL,
    hashed_password VARCHAR(255)    NOT NULL,
    role            user_role_enum  NOT NULL DEFAULT 'citizen',
    citizen_id      INT             REFERENCES citizen(citizen_id)  ON DELETE SET NULL,
    officer_id      INT             REFERENCES officer(officer_id)  ON DELETE SET NULL,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_username UNIQUE (username)
);

-- ----------------------------------------------------------
-- TABLE 8: NOTIFICATION  (Email audit trail)
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS notification (
    notification_id  SERIAL       PRIMARY KEY,
    complaint_id     INT          NOT NULL REFERENCES complaint(complaint_id)  ON DELETE CASCADE,
    citizen_id       INT          NOT NULL REFERENCES citizen(citizen_id)      ON DELETE CASCADE,
    message          TEXT         NOT NULL,
    sent_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    is_sent          BOOLEAN      NOT NULL DEFAULT FALSE
);


-- ============================================================
-- SECTION 3 — CONSTRAINTS & NAMED FOREIGN KEYS
-- (All FKs already declared inline above; listed here for docs)
-- Summary:
--   officer.ward_id       → ward.ward_id        ON DELETE SET NULL
--   ward.officer_id       → officer.officer_id   ON DELETE SET NULL
--   worker.ward_id        → ward.ward_id         ON DELETE SET NULL
--   complaint.citizen_id  → citizen.citizen_id   ON DELETE CASCADE
--   complaint.ward_id     → ward.ward_id         ON DELETE CASCADE
--   complaint.worker_id   → worker.worker_id     ON DELETE SET NULL
--   complaint_log.complaint_id → complaint.complaint_id ON DELETE CASCADE
--   app_user.citizen_id   → citizen.citizen_id   ON DELETE SET NULL
--   app_user.officer_id   → officer.officer_id   ON DELETE SET NULL
--   notification.complaint_id → complaint.complaint_id ON DELETE CASCADE
--   notification.citizen_id   → citizen.citizen_id    ON DELETE CASCADE
-- ============================================================


-- ============================================================
-- SECTION 4 — INDEXES
-- ============================================================

-- Original MySQL indexes preserved
CREATE INDEX IF NOT EXISTS idx_complaint_ward_id  ON complaint(ward_id);
CREATE INDEX IF NOT EXISTS idx_complaint_status   ON complaint(status);
CREATE INDEX IF NOT EXISTS idx_complaint_filed_at ON complaint(filed_at);

-- Improvement: partial index for non-resolved complaints (used by the view)
CREATE INDEX IF NOT EXISTS idx_complaint_active   ON complaint(ward_id, filed_at)
    WHERE status <> 'resolved';

-- Improvement: index for notification lookup by citizen
CREATE INDEX IF NOT EXISTS idx_notification_citizen ON notification(citizen_id);

-- Improvement: index for user role lookups (auth/RBAC queries)
CREATE INDEX IF NOT EXISTS idx_app_user_role ON app_user(role);


-- ============================================================
-- SECTION 5 — TRIGGER + TRIGGER FUNCTION
-- Equivalent of MySQL: trg_complaint_status_log
-- In PostgreSQL, triggers require a FUNCTION returning TRIGGER.
-- ============================================================

CREATE OR REPLACE FUNCTION fn_log_complaint_status_change()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    -- Only write a log row when status actually changes
    IF OLD.status IS DISTINCT FROM NEW.status THEN
        INSERT INTO complaint_log (complaint_id, old_status, new_status, changed_by)
        VALUES (NEW.complaint_id, OLD.status::TEXT, NEW.status::TEXT, 'system_trigger');
    END IF;
    RETURN NEW;
END;
$$;

-- Attach the trigger to the complaint table
CREATE OR REPLACE TRIGGER trg_complaint_status_log
AFTER UPDATE ON complaint
FOR EACH ROW
EXECUTE FUNCTION fn_log_complaint_status_change();


-- ============================================================
-- SECTION 6 — FUNCTION (converted stored procedure)
-- MySQL:    CALL GetWardSummary(p_ward_id)
-- PostgreSQL: SELECT * FROM get_ward_summary(p_ward_id)
--
-- NOTE: PostgreSQL does not have stored procedures that return
-- result sets the same way MySQL does. The cleanest equivalent
-- is a SETOF RECORD function or a TABLE function. We use
-- RETURNS TABLE for type-safety and easy use in Supabase RPC.
-- ============================================================

CREATE OR REPLACE FUNCTION get_ward_summary(p_ward_id INT)
RETURNS TABLE (
    total_complaints      BIGINT,
    open_complaints       BIGINT,
    in_progress_complaints BIGINT,
    resolved_complaints   BIGINT
)
LANGUAGE sql
STABLE
AS $$
    SELECT
        COUNT(*)                                                               AS total_complaints,
        COUNT(*) FILTER (WHERE status = 'open')                               AS open_complaints,
        COUNT(*) FILTER (WHERE status = 'in_progress')                        AS in_progress_complaints,
        COUNT(*) FILTER (WHERE status = 'resolved')                           AS resolved_complaints
    FROM complaint
    WHERE ward_id = p_ward_id;
$$;

-- Usage in Supabase:  SELECT * FROM get_ward_summary(1);
-- Usage via RPC:      supabase.rpc('get_ward_summary', { p_ward_id: 1 })


-- ============================================================
-- SECTION 7 — VIEW
-- active_complaints_view: non-resolved complaints with joins
-- Preserved exactly; PostgreSQL CREATE OR REPLACE VIEW works as-is.
-- ============================================================

CREATE OR REPLACE VIEW active_complaints_view AS
    SELECT
        c.complaint_id,
        c.description,
        c.damage_type,
        c.severity,
        c.status,
        c.address        AS complaint_address,
        c.filed_at,
        c.latitude,
        c.longitude,
        ci.name          AS citizen_name,
        ci.phone         AS citizen_phone,
        w.ward_name,
        w.city
    FROM  complaint  c
    JOIN  citizen    ci ON c.citizen_id = ci.citizen_id
    JOIN  ward       w  ON c.ward_id    = w.ward_id
    WHERE c.status <> 'resolved';


-- ============================================================
-- SECTION 8 — SEED DATA (converted from seed_data.sql)
-- DATE_SUB(NOW(), INTERVAL N DAY) → NOW() - INTERVAL 'N days'
-- TRUE/FALSE → PostgreSQL booleans (same syntax, works fine)
-- ============================================================

-- 1. Officers (ward_id NULL initially)
INSERT INTO officer (name, phone, designation, ward_id) VALUES
('Rajesh Kumar',  '9876540001', 'Ward Officer',     NULL),
('Sunita Patil',  '9876540002', 'Senior Inspector', NULL),
('Mohan Desai',   '9876540003', 'Ward Officer',     NULL),
('Priya Sharma',  '9876540004', 'Junior Officer',   NULL),
('Anil Bhosale',  '9876540005', 'Senior Inspector', NULL);

-- 2. Wards
INSERT INTO ward (ward_name, city, officer_id) VALUES
('Shivajinagar', 'Pune', 1),
('Kothrud',      'Pune', 2),
('Hadapsar',     'Pune', 3),
('Warje',        'Pune', 4),
('Aundh',        'Pune', 5);

-- Link officers back to their wards
UPDATE officer SET ward_id = 1 WHERE officer_id = 1;
UPDATE officer SET ward_id = 2 WHERE officer_id = 2;
UPDATE officer SET ward_id = 3 WHERE officer_id = 3;
UPDATE officer SET ward_id = 4 WHERE officer_id = 4;
UPDATE officer SET ward_id = 5 WHERE officer_id = 5;

-- 3. Workers (with GPS base coords)
INSERT INTO worker (name, phone, skill_type, ward_id, is_available, base_latitude, base_longitude) VALUES
('Suresh Kale',     '9000000001', 'road',       1, TRUE,  18.5308, 73.8474),
('Dinesh Wagh',     '9000000002', 'drainage',   1, TRUE,  18.5250, 73.8500),
('Kavita Jagtap',   '9000000003', 'electrical', 2, TRUE,  18.5074, 73.8077),
('Ravi More',       '9000000004', 'road',       2, FALSE, 18.5040, 73.8120),
('Santosh Gaikwad', '9000000005', 'road',       3, TRUE,  18.5089, 73.9260),
('Pooja Nikam',     '9000000006', 'drainage',   3, TRUE,  18.5000, 73.9200),
('Mahesh Salve',    '9000000007', 'road',       4, TRUE,  18.4854, 73.8026),
('Vijay Jadhav',    '9000000008', 'electrical', 5, FALSE, 18.5579, 73.8076);

-- 4. Citizens
INSERT INTO citizen (name, phone, email, address, ward_no) VALUES
('Aarav Mehta',      '9100000001', 'aarav@email.com',   '12 MG Road, Shivajinagar',        1),
('Sneha Joshi',      '9100000002', 'sneha@email.com',   '34 Paud Road, Kothrud',           2),
('Rahul Pawar',      '9100000003', 'rahul@email.com',   '5 Hadapsar Link Rd, Hadapsar',    3),
('Divya Kulkarni',   '9100000004', 'divya@email.com',   '78 Sus Road, Warje',              4),
('Amit Shinde',      '9100000005', 'amit@email.com',    '22 ITI Road, Aundh',              5),
('Priya Naik',       '9100000006', 'priya@email.com',   '9 Deccan Gymkhana, Shivajinagar', 1),
('Vishal Deshpande', '9100000007', 'vishal@email.com',  '11 Karve Road, Kothrud',          2),
('Anita Bapat',      '9100000008', 'anita@email.com',   '56 Undri Road, Hadapsar',         3),
('Suraj Tiwari',     '9100000009', 'suraj@email.com',   '30 Warje Road, Warje',            4),
('Meera Chopra',     '9100000010', 'meera@email.com',   '15 Baner Road, Aundh',            5);

-- 5. Complaints (MySQL DATE_SUB → PostgreSQL interval arithmetic)
INSERT INTO complaint
  (citizen_id, ward_id, worker_id, description, damage_type, severity, status,
   address, latitude, longitude, filed_at, resolved_at)
VALUES
-- Ward 1: Shivajinagar
(1, 1, 1, 'Large pothole near bus stop causing accidents',       'pothole',      'critical', 'resolved',    '12 MG Road, Shivajinagar',          18.5310, 73.8476, NOW() - INTERVAL '15 days', NOW() - INTERVAL '5 days'),
(6, 1, NULL,'Multiple cracks on footpath near Deccan',          'crack',        'low',      'open',        '9 Deccan Gymkhana, Shivajinagar',    18.5200, 73.8400, NOW() - INTERVAL '12 days', NULL),
(3, 1, 2,  'Waterlogging near society gate every monsoon',      'waterlogging', 'medium',   'resolved',    'FC Road, Shivajinagar',              18.5260, 73.8530, NOW() - INTERVAL '25 days', NOW() - INTERVAL '15 days'),
-- Ward 2: Kothrud
(2, 2, 3,  'Road crack spreading across 20m on Paud Road',      'crack',        'medium',   'in_progress', '34 Paud Road, Kothrud',              18.5074, 73.8077, NOW() - INTERVAL '10 days', NULL),
(7, 2, 4,  'Severe pothole causing bike accidents on Karve Rd', 'pothole',      'critical', 'resolved',    '11 Karve Road, Kothrud',             18.5050, 73.8100, NOW() - INTERVAL '20 days', NOW() - INTERVAL '8 days'),
(1, 2, NULL,'Pothole near school gate worsening',               'pothole',      'medium',   'open',        '40 Karve Road, Kothrud',             18.5070, 73.8060, NOW() - INTERVAL '1 day',   NULL),
-- Ward 3: Hadapsar
(3, 3, 5,  'Waterlogging blocking colony entrance after rain',  'waterlogging', 'critical', 'open',        '5 Hadapsar Link Rd, Hadapsar',       18.5089, 73.9260, NOW() - INTERVAL '9 days',  NULL),
(8, 3, 6,  'Drainage overflow causing waterlogging on road',    'waterlogging', 'medium',   'in_progress', '56 Undri Road, Hadapsar',            18.4900, 73.9200, NOW() - INTERVAL '6 days',  NULL),
(5, 3, NULL,'Big crack developed after rain near hospital',     'crack',        'critical', 'open',        'Hadapsar Hospital Road, Hadapsar',   18.5150, 73.9350, NOW() - INTERVAL '9 days',  NULL),
-- Ward 4: Warje
(4, 4, 7,  'Road surface subsidence near market',               'subsidence',   'critical', 'open',        '78 Sus Road, Warje',                 18.4854, 73.8026, NOW() - INTERVAL '3 days',  NULL),
(9, 4, NULL,'Road crack at main junction',                      'crack',        'medium',   'open',        '30 Warje Road, Warje',               18.4800, 73.7900, NOW() - INTERVAL '2 days',  NULL),
(6, 4, 7,  'Multiple potholes after heavy rainfall',            'pothole',      'medium',   'in_progress', 'Maharashtra Housing, Warje',          18.4820, 73.7960, NOW() - INTERVAL '4 days',  NULL),
-- Ward 5: Aundh
(5, 5, NULL,'Pothole on main road near school',                 'pothole',      'critical', 'open',        '22 ITI Road, Aundh',                 18.5579, 73.8076, NOW() - INTERVAL '8 days',  NULL),
(10,5, 8,  'Subsidence near old building — road depression',    'subsidence',   'critical', 'in_progress', '15 Baner Road, Aundh',               18.5600, 73.7850, NOW() - INTERVAL '7 days',  NULL),
(8, 5, NULL,'New subsidence point forming near park entrance',  'subsidence',   'low',      'open',        'Aundh Park Road, Aundh',             18.5630, 73.8120, NOW() - INTERVAL '10 days', NULL);

-- 6. Complaint Log (manual pre-trigger audit entries)
INSERT INTO complaint_log (complaint_id, old_status, new_status, changed_by, changed_at) VALUES
(1,  'open',        'in_progress', 'Officer_Rajesh', NOW() - INTERVAL '12 days'),
(1,  'in_progress', 'resolved',    'Officer_Rajesh', NOW() - INTERVAL '5 days'),
(4,  'open',        'in_progress', 'Officer_Sunita', NOW() - INTERVAL '7 days'),
(5,  'open',        'in_progress', 'Officer_Sunita', NOW() - INTERVAL '15 days'),
(5,  'in_progress', 'resolved',    'Officer_Sunita', NOW() - INTERVAL '8 days'),
(8,  'open',        'in_progress', 'Officer_Mohan',  NOW() - INTERVAL '4 days'),
(14, 'open',        'in_progress', 'Officer_Anil',   NOW() - INTERVAL '5 days'),
(3,  'open',        'in_progress', 'Officer_Rajesh', NOW() - INTERVAL '20 days'),
(3,  'in_progress', 'resolved',    'Officer_Rajesh', NOW() - INTERVAL '15 days'),
(12, 'open',        'in_progress', 'Officer_Priya',  NOW() - INTERVAL '2 days');

-- NOTE: app_user rows (admin/officer/citizen accounts) are still seeded
-- programmatically by FastAPI startup (main.py). No SQL needed here.
-- If you want to pre-seed them, insert hashed passwords via pgcrypto:
--   INSERT INTO app_user (username, hashed_password, role) VALUES
--   ('admin', crypt('your_password', gen_salt('bf')), 'admin');
