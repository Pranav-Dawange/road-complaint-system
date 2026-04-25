-- ============================================================
-- Road Complaint Management System - Database Schema
-- FULL SCHEMA including all 6 original tables + Upgrade additions
-- Run this on a FRESH database (DROP DATABASE first if re-running)
-- ============================================================

CREATE DATABASE IF NOT EXISTS road_complaint_db;
USE road_complaint_db;

-- ============================================================
-- TABLE 1: OFFICER (defined before WARD - WARD references OFFICER)
-- ============================================================
CREATE TABLE IF NOT EXISTS OFFICER (
    officer_id   INT           NOT NULL AUTO_INCREMENT,
    name         VARCHAR(100)  NOT NULL,
    phone        VARCHAR(15)   NOT NULL,
    designation  VARCHAR(100)  NOT NULL,
    ward_id      INT,
    PRIMARY KEY (officer_id)
);

-- ============================================================
-- TABLE 2: WARD
-- ============================================================
CREATE TABLE IF NOT EXISTS WARD (
    ward_id     INT           NOT NULL AUTO_INCREMENT,
    ward_name   VARCHAR(100)  NOT NULL,
    city        VARCHAR(100)  NOT NULL DEFAULT 'Pune',
    officer_id  INT,
    PRIMARY KEY (ward_id),
    CONSTRAINT fk_ward_officer FOREIGN KEY (officer_id)
        REFERENCES OFFICER(officer_id)
        ON DELETE SET NULL ON UPDATE CASCADE
);

ALTER TABLE OFFICER
    ADD CONSTRAINT fk_officer_ward FOREIGN KEY (ward_id)
        REFERENCES WARD(ward_id)
        ON DELETE SET NULL ON UPDATE CASCADE;

-- ============================================================
-- TABLE 3: CITIZEN
-- ============================================================
CREATE TABLE IF NOT EXISTS CITIZEN (
    citizen_id  INT           NOT NULL AUTO_INCREMENT,
    name        VARCHAR(100)  NOT NULL,
    phone       VARCHAR(15)   NOT NULL,
    email       VARCHAR(150),
    address     TEXT,
    ward_no     INT,
    PRIMARY KEY (citizen_id),
    CONSTRAINT uq_citizen_phone UNIQUE (phone)
);

-- ============================================================
-- TABLE 4: WORKER (includes GPS base location for Upgrade 4)
-- ============================================================
CREATE TABLE IF NOT EXISTS WORKER (
    worker_id      INT          NOT NULL AUTO_INCREMENT,
    name           VARCHAR(100) NOT NULL,
    phone          VARCHAR(15)  NOT NULL,
    skill_type     ENUM('road', 'drainage', 'electrical') NOT NULL,
    ward_id        INT,
    is_available   BOOLEAN      NOT NULL DEFAULT TRUE,
    base_latitude  FLOAT        NULL,
    base_longitude FLOAT        NULL,
    PRIMARY KEY (worker_id),
    CONSTRAINT fk_worker_ward FOREIGN KEY (ward_id)
        REFERENCES WARD(ward_id)
        ON DELETE SET NULL ON UPDATE CASCADE
);

-- ============================================================
-- TABLE 5: COMPLAINT (includes GPS for Upgrade 4)
-- ============================================================
CREATE TABLE IF NOT EXISTS COMPLAINT (
    complaint_id  INT          NOT NULL AUTO_INCREMENT,
    citizen_id    INT          NOT NULL,
    ward_id       INT          NOT NULL,
    worker_id     INT,
    description   TEXT         NOT NULL,
    damage_type   ENUM('pothole', 'crack', 'waterlogging', 'subsidence') NOT NULL,
    severity      ENUM('low', 'medium', 'critical') NOT NULL,
    status        ENUM('open', 'in_progress', 'resolved') NOT NULL DEFAULT 'open',
    address       TEXT         NOT NULL,
    photo_path    VARCHAR(255),
    latitude      FLOAT        NULL,
    longitude     FLOAT        NULL,
    filed_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved_at   TIMESTAMP    NULL,
    PRIMARY KEY (complaint_id),
    CONSTRAINT fk_complaint_citizen FOREIGN KEY (citizen_id)
        REFERENCES CITIZEN(citizen_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_complaint_ward    FOREIGN KEY (ward_id)
        REFERENCES WARD(ward_id)    ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_complaint_worker  FOREIGN KEY (worker_id)
        REFERENCES WORKER(worker_id) ON DELETE SET NULL ON UPDATE CASCADE
);

-- ============================================================
-- TABLE 6: COMPLAINT_LOG (auto-populated by trigger)
-- ============================================================
CREATE TABLE IF NOT EXISTS COMPLAINT_LOG (
    log_id       INT          NOT NULL AUTO_INCREMENT,
    complaint_id INT          NOT NULL,
    old_status   VARCHAR(20)  NOT NULL,
    new_status   VARCHAR(20)  NOT NULL,
    changed_by   VARCHAR(100) NOT NULL,
    changed_at   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (log_id),
    CONSTRAINT fk_log_complaint FOREIGN KEY (complaint_id)
        REFERENCES COMPLAINT(complaint_id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- ============================================================
-- TABLE 7: USER (Upgrade 1 — JWT Auth)
-- Stores login credentials and role; links to citizen or officer
-- ============================================================
CREATE TABLE IF NOT EXISTS USER (
    user_id         INT           NOT NULL AUTO_INCREMENT,
    username        VARCHAR(100)  NOT NULL,
    hashed_password VARCHAR(255)  NOT NULL,
    role            ENUM('citizen', 'officer', 'admin') NOT NULL DEFAULT 'citizen',
    citizen_id      INT           NULL,
    officer_id      INT           NULL,
    created_at      TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id),
    CONSTRAINT uq_username UNIQUE (username),
    CONSTRAINT fk_user_citizen FOREIGN KEY (citizen_id)
        REFERENCES CITIZEN(citizen_id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT fk_user_officer FOREIGN KEY (officer_id)
        REFERENCES OFFICER(officer_id) ON DELETE SET NULL ON UPDATE CASCADE
);

-- ============================================================
-- TABLE 8: NOTIFICATION (Upgrade 3 — Email audit trail)
-- ============================================================
CREATE TABLE IF NOT EXISTS NOTIFICATION (
    notification_id INT          NOT NULL AUTO_INCREMENT,
    complaint_id    INT          NOT NULL,
    citizen_id      INT          NOT NULL,
    message         TEXT         NOT NULL,
    sent_at         TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_sent         BOOLEAN      NOT NULL DEFAULT FALSE,
    PRIMARY KEY (notification_id),
    CONSTRAINT fk_notif_complaint FOREIGN KEY (complaint_id)
        REFERENCES COMPLAINT(complaint_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_notif_citizen   FOREIGN KEY (citizen_id)
        REFERENCES CITIZEN(citizen_id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- ============================================================
-- INDEXES — Speed up common queries
-- ============================================================
CREATE INDEX idx_complaint_ward_id  ON COMPLAINT(ward_id);
CREATE INDEX idx_complaint_status   ON COMPLAINT(status);
CREATE INDEX idx_complaint_filed_at ON COMPLAINT(filed_at);

-- ============================================================
-- TRIGGER: trg_complaint_status_log
-- After any UPDATE on COMPLAINT where status changed,
-- automatically insert a row into COMPLAINT_LOG.
-- ============================================================
DELIMITER $$

CREATE TRIGGER trg_complaint_status_log
AFTER UPDATE ON COMPLAINT
FOR EACH ROW
BEGIN
    IF OLD.status <> NEW.status THEN
        INSERT INTO COMPLAINT_LOG (complaint_id, old_status, new_status, changed_by)
        VALUES (NEW.complaint_id, OLD.status, NEW.status, 'system_trigger');
    END IF;
END$$

DELIMITER ;

-- ============================================================
-- TRIGGER 2: trg_auto_notify_on_status_change
-- Automatically inserts a notification row when complaint
-- status changes, so the citizen is informed via the system.
-- ============================================================
DELIMITER $$

CREATE TRIGGER trg_auto_notify_on_status_change
AFTER UPDATE ON COMPLAINT
FOR EACH ROW
BEGIN
    DECLARE v_message TEXT;

    IF OLD.status <> NEW.status THEN
        SET v_message = CONCAT(
            'Your complaint #', NEW.complaint_id,
            ' status changed from "', OLD.status, '" to "', NEW.status, '".'
        );

        IF NEW.status = 'resolved' THEN
            SET v_message = CONCAT(v_message,
                ' Thank you for your patience — the issue has been resolved.');
        END IF;

        INSERT INTO NOTIFICATION (complaint_id, citizen_id, message, is_sent)
        VALUES (NEW.complaint_id, NEW.citizen_id, v_message, FALSE);
    END IF;
END$$

DELIMITER ;

-- ============================================================
-- TRIGGER 3: trg_set_resolved_timestamp
-- BEFORE UPDATE trigger that auto-manages resolved_at:
--   • Sets resolved_at = NOW() when status → 'resolved'
--   • Clears resolved_at = NULL if complaint is reopened
-- ============================================================
DELIMITER $$

CREATE TRIGGER trg_set_resolved_timestamp
BEFORE UPDATE ON COMPLAINT
FOR EACH ROW
BEGIN
    -- Complaint is being resolved
    IF NEW.status = 'resolved' AND OLD.status <> 'resolved' THEN
        SET NEW.resolved_at = NOW();
    END IF;

    -- Complaint is being reopened
    IF NEW.status <> 'resolved' AND OLD.status = 'resolved' THEN
        SET NEW.resolved_at = NULL;
    END IF;
END$$

DELIMITER ;

-- ============================================================
-- CURSOR-BASED PROCEDURE: GenerateAllWardsReport
-- Uses an explicit CURSOR to iterate over all wards and compute
-- a detailed per-ward report: total, open, in_progress, resolved,
-- avg resolution days, and SLA breaches.
-- ============================================================
DELIMITER $$

CREATE PROCEDURE GenerateAllWardsReport()
BEGIN
    -- Variables to hold cursor row values
    DECLARE v_ward_id    INT;
    DECLARE v_ward_name  VARCHAR(100);
    DECLARE v_done       INT DEFAULT 0;

    -- Declare the cursor
    DECLARE ward_cursor CURSOR FOR
        SELECT ward_id, ward_name FROM WARD ORDER BY ward_id;

    -- Handler for end-of-cursor
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_done = 1;

    -- Temporary table to collect results
    DROP TEMPORARY TABLE IF EXISTS tmp_ward_report;
    CREATE TEMPORARY TABLE tmp_ward_report (
        ward_id              INT,
        ward_name            VARCHAR(100),
        total_complaints     INT,
        open_complaints      INT,
        in_progress_complaints INT,
        resolved_complaints  INT,
        avg_resolution_days  DECIMAL(10,1),
        sla_breaches         INT
    );

    -- Open cursor and iterate
    OPEN ward_cursor;

    ward_loop: LOOP
        FETCH ward_cursor INTO v_ward_id, v_ward_name;
        IF v_done = 1 THEN
            LEAVE ward_loop;
        END IF;

        INSERT INTO tmp_ward_report
        SELECT
            v_ward_id,
            v_ward_name,
            COUNT(*),
            SUM(CASE WHEN status = 'open'        THEN 1 ELSE 0 END),
            SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END),
            SUM(CASE WHEN status = 'resolved'    THEN 1 ELSE 0 END),
            ROUND(AVG(
                CASE WHEN status = 'resolved' AND resolved_at IS NOT NULL
                     THEN DATEDIFF(resolved_at, filed_at)
                END
            ), 1),
            SUM(CASE WHEN status <> 'resolved'
                      AND DATEDIFF(NOW(), filed_at) > 7
                     THEN 1 ELSE 0 END)
        FROM COMPLAINT
        WHERE ward_id = v_ward_id;
    END LOOP;

    -- Close the cursor
    CLOSE ward_cursor;

    -- Return the collected report
    SELECT * FROM tmp_ward_report ORDER BY ward_id;

    -- Cleanup
    DROP TEMPORARY TABLE IF EXISTS tmp_ward_report;
END$$

DELIMITER ;

-- ============================================================
-- STORED PROCEDURE: GetWardSummary(IN p_ward_id INT)
-- Returns total/open/in_progress/resolved counts for a ward.
-- Called via API at GET /wards/{id}/summary
-- ============================================================
DELIMITER $$

CREATE PROCEDURE GetWardSummary(IN p_ward_id INT)
BEGIN
    SELECT
        COUNT(*)                                                 AS total_complaints,
        SUM(CASE WHEN status = 'open'        THEN 1 ELSE 0 END) AS open_complaints,
        SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) AS in_progress_complaints,
        SUM(CASE WHEN status = 'resolved'    THEN 1 ELSE 0 END) AS resolved_complaints
    FROM COMPLAINT
    WHERE ward_id = p_ward_id;
END$$

DELIMITER ;

-- ============================================================
-- VIEW: active_complaints_view
-- Non-resolved complaints with citizen name and ward name.
-- ============================================================
CREATE OR REPLACE VIEW active_complaints_view AS
    SELECT
        c.complaint_id,
        c.description,
        c.damage_type,
        c.severity,
        c.status,
        c.address       AS complaint_address,
        c.filed_at,
        c.latitude,
        c.longitude,
        ci.name         AS citizen_name,
        ci.phone        AS citizen_phone,
        w.ward_name,
        w.city
    FROM  COMPLAINT c
    JOIN  CITIZEN   ci ON c.citizen_id = ci.citizen_id
    JOIN  WARD      w  ON c.ward_id    = w.ward_id
    WHERE c.status <> 'resolved';
