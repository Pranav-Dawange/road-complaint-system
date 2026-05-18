-- ============================================================
-- new_features.sql
-- Road Complaint Management System — DBMS Enhancements
--
-- Run this entire file in the Supabase SQL Editor.
-- Safe to re-run (uses IF NOT EXISTS / OR REPLACE).
-- ============================================================


-- ============================================================
-- PART 1: AUDIT LOG TABLE + TRIGGERS
-- ============================================================

-- 1a. Admin Audit Log table
-- Tracks all admin panel actions: ward creation, worker creation
CREATE TABLE IF NOT EXISTS admin_audit_log (
    log_id      SERIAL          PRIMARY KEY,
    action      VARCHAR(50)     NOT NULL,   -- e.g. 'WARD_CREATED', 'WORKER_CREATED'
    entity_type VARCHAR(50)     NOT NULL,   -- 'ward' or 'worker'
    entity_id   INT             NOT NULL,   -- ward_id or worker_id
    entity_name VARCHAR(200),              -- ward_name or worker name
    details     JSONB,                     -- extra info as JSON
    created_at  TIMESTAMP       NOT NULL DEFAULT NOW()
);

-- Index for fast time-based queries
CREATE INDEX IF NOT EXISTS idx_audit_log_created
    ON admin_audit_log (created_at DESC);

CREATE INDEX IF NOT EXISTS idx_audit_log_action
    ON admin_audit_log (action);


-- 1b. Trigger function: log when a new WARD is inserted
CREATE OR REPLACE FUNCTION log_ward_creation()
RETURNS TRIGGER
LANGUAGE plpgsql AS $$
BEGIN
    INSERT INTO admin_audit_log (action, entity_type, entity_id, entity_name, details)
    VALUES (
        'WARD_CREATED',
        'ward',
        NEW.ward_id,
        NEW.ward_name,
        jsonb_build_object(
            'city',       NEW.city,
            'officer_id', NEW.officer_id
        )
    );
    RETURN NEW;
END;
$$;

-- Drop if exists and recreate (idempotent)
DROP TRIGGER IF EXISTS trg_log_ward_creation ON ward;
CREATE TRIGGER trg_log_ward_creation
    AFTER INSERT ON ward
    FOR EACH ROW
    EXECUTE FUNCTION log_ward_creation();


-- 1c. Trigger function: log when a new WORKER is inserted
CREATE OR REPLACE FUNCTION log_worker_creation()
RETURNS TRIGGER
LANGUAGE plpgsql AS $$
BEGIN
    INSERT INTO admin_audit_log (action, entity_type, entity_id, entity_name, details)
    VALUES (
        'WORKER_CREATED',
        'worker',
        NEW.worker_id,
        NEW.name,
        jsonb_build_object(
            'phone',      NEW.phone,
            'skill_type', NEW.skill_type,
            'ward_id',    NEW.ward_id
        )
    );
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_log_worker_creation ON worker;
CREATE TRIGGER trg_log_worker_creation
    AFTER INSERT ON worker
    FOR EACH ROW
    EXECUTE FUNCTION log_worker_creation();


-- ============================================================
-- PART 2: STORED PROCEDURE (FUNCTION) FOR COMPLAINT FILING
-- ============================================================
-- PostgreSQL FUNCTION that atomically inserts a new complaint.
-- Called via: SELECT file_complaint_proc(...) FROM main.py
-- Returns the new complaint_id.
-- ============================================================

CREATE OR REPLACE FUNCTION file_complaint_proc(
    p_citizen_id  INT,
    p_ward_id     INT,
    p_description TEXT,
    p_damage_type TEXT,
    p_severity    TEXT,
    p_address     TEXT,
    p_latitude    DOUBLE PRECISION DEFAULT NULL,
    p_longitude   DOUBLE PRECISION DEFAULT NULL,
    p_photo_path  TEXT             DEFAULT NULL
)
RETURNS INT
LANGUAGE plpgsql AS $$
DECLARE
    v_complaint_id INT;
BEGIN
    -- Validate citizen exists
    IF NOT EXISTS (SELECT 1 FROM citizen WHERE citizen_id = p_citizen_id) THEN
        RAISE EXCEPTION 'Citizen with id % not found', p_citizen_id;
    END IF;

    -- Validate ward exists
    IF NOT EXISTS (SELECT 1 FROM ward WHERE ward_id = p_ward_id) THEN
        RAISE EXCEPTION 'Ward with id % not found', p_ward_id;
    END IF;

    -- Insert the complaint atomically
    INSERT INTO complaint (
        citizen_id, ward_id, description,
        damage_type, severity, status,
        address, latitude, longitude, photo_path
    )
    VALUES (
        p_citizen_id, p_ward_id, p_description,
        p_damage_type::damage_type_enum,
        p_severity::severity_enum,
        'open',
        p_address, p_latitude, p_longitude, p_photo_path
    )
    RETURNING complaint_id INTO v_complaint_id;

    RETURN v_complaint_id;
END;
$$;


-- ============================================================
-- PART 3: HELPER FUNCTION FOR BULK CITIZEN VALIDATION
-- ============================================================
-- Returns TRUE if a phone number already exists in citizen table.
-- Used by the bulk import endpoint to skip duplicates gracefully.
-- ============================================================

CREATE OR REPLACE FUNCTION citizen_phone_exists(p_phone TEXT)
RETURNS BOOLEAN
LANGUAGE plpgsql AS $$
BEGIN
    RETURN EXISTS (SELECT 1 FROM citizen WHERE phone = p_phone);
END;
$$;


-- ============================================================
-- VERIFY
-- ============================================================
-- After running, you should see these in Supabase:
--   Tables:    admin_audit_log
--   Functions: log_ward_creation, log_worker_creation,
--              file_complaint_proc, citizen_phone_exists
--   Triggers:  trg_log_ward_creation (on ward)
--              trg_log_worker_creation (on worker)
-- ============================================================
