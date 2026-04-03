"""
main.py — FastAPI application for Road Complaint Management System
BACKEND: Supabase (PostgreSQL) — migrated from MySQL
UPGRADED: JWT Auth, Photo Upload, Email Notifications, GPS/Map, Auto-Assign

Run with:  uvicorn main:app --reload
Docs:      http://localhost:8000/docs
"""

import os
import math
import time
import shutil
from typing import Optional

from fastapi import (
    FastAPI, HTTPException, Query, Depends, BackgroundTasks,
    Form, File, UploadFile, status
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles

from database import execute_query, call_procedure
from models import (
    CitizenCreate, StatusUpdate, WorkerAssign,
    UserRegister, ComplaintStatus
)
from auth import (
    hash_password, verify_password,
    create_access_token, get_current_user, require_role
)
from notifications import send_notification_background

# ── App setup ──────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Road Complaint Management System",
    description="DBMS Project — FastAPI + Supabase (PostgreSQL)",
    version="3.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Static files (serves /static/uploads/ for photos) ─────────────────────────
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
UPLOAD_DIR = os.path.join(STATIC_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# ── HTML templates dir ─────────────────────────────────────────────────────────
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}
MAX_PHOTO_BYTES    = 5 * 1024 * 1024  # 5 MB


# ══════════════════════════════════════════════════════════════════════════════
# STARTUP — Create default user accounts (admin / officer1 / citizen1)
# Passwords are bcrypt-hashed at runtime so no pre-computed hash is needed.
# PostgreSQL change: table is app_user (USER is reserved); RETURNING user_id.
# ══════════════════════════════════════════════════════════════════════════════

@app.on_event("startup")
def create_default_users():
    """
    Insert the three sample users if they don't already exist.
    Runs every time the server starts — safe to call repeatedly.
    """
    defaults = [
        ("admin",    "admin123",   "admin",   None, None),
        ("officer1", "officer123", "officer", None,    1),
        ("citizen1", "citizen123", "citizen",    1, None),
    ]
    for username, password, role, citizen_id, officer_id in defaults:
        existing = execute_query(
            "SELECT user_id FROM app_user WHERE username = %s",
            (username,), fetch=True
        )
        if not existing:
            execute_query(
                """
                INSERT INTO app_user (username, hashed_password, role, citizen_id, officer_id)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING user_id
                """,
                (username, hash_password(password), role, citizen_id, officer_id)
            )
            print(f"[STARTUP] Created user → {username} ({role})")


# ── Helper ─────────────────────────────────────────────────────────────────────
def _not_found(entity: str, eid: int):
    raise HTTPException(status_code=404, detail=f"{entity} id={eid} not found")

def _dt(row: dict, *keys):
    """Convert datetime objects to strings in-place."""
    for k in keys:
        if row.get(k):
            row[k] = str(row[k])
    return row


# ══════════════════════════════════════════════════════════════════════════════
# ROOT
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/", tags=["Root"])
def root():
    return {"message": "Road Complaint API running", "docs": "/docs", "version": "3.0.0"}


# ══════════════════════════════════════════════════════════════════════════════
# HTML PAGE ROUTES
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/index", response_class=HTMLResponse, tags=["Pages"])
def serve_index():
    with open(os.path.join(TEMPLATES_DIR, "index.html"), encoding="utf-8") as f:
        return f.read()

@app.get("/dashboard", response_class=HTMLResponse, tags=["Pages"])
def serve_dashboard():
    with open(os.path.join(TEMPLATES_DIR, "dashboard.html"), encoding="utf-8") as f:
        return f.read()

@app.get("/analytics", response_class=HTMLResponse, tags=["Pages"])
def serve_analytics():
    with open(os.path.join(TEMPLATES_DIR, "analytics.html"), encoding="utf-8") as f:
        return f.read()

@app.get("/map", response_class=HTMLResponse, tags=["Pages"])
def serve_map():
    with open(os.path.join(TEMPLATES_DIR, "map.html"), encoding="utf-8") as f:
        return f.read()


# ══════════════════════════════════════════════════════════════════════════════
# AUTH — REGISTER & LOGIN
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/register", status_code=201, tags=["Auth"])
def register_user(body: UserRegister):
    """
    Register a new user account.
    SQL: INSERT INTO app_user with bcrypt-hashed password.
    Returns: {user_id, message}
    """
    existing = execute_query(
        "SELECT user_id FROM app_user WHERE username = %s",
        (body.username,), fetch=True
    )
    if existing:
        raise HTTPException(status_code=422, detail="Username already taken.")

    new_id = execute_query(
        """
        INSERT INTO app_user (username, hashed_password, role)
        VALUES (%s, %s, %s)
        RETURNING user_id
        """,
        (body.username, hash_password(body.password), body.role.value)
    )
    return {"user_id": new_id, "message": "User registered successfully"}


@app.post("/login", tags=["Auth"])
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Authenticate and return a JWT access token.
    Uses OAuth2PasswordRequestForm (username + password fields).
    SQL: SELECT hashed_password + role FROM app_user WHERE username = ?
    """
    rows = execute_query(
        "SELECT user_id, hashed_password, role FROM app_user WHERE username = %s",
        (form_data.username,), fetch=True
    )
    if not rows:
        raise HTTPException(status_code=401, detail="Invalid username or password.")

    user = rows[0]
    if not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid username or password.")

    # Create JWT with user_id, username (sub), and role embedded
    token = create_access_token({
        "sub":     form_data.username,
        "user_id": user["user_id"],
        "role":    user["role"],
    })
    return {
        "access_token": token,
        "token_type":   "bearer",
        "role":         user["role"],
        "username":     form_data.username,
        "user_id":      user["user_id"],
    }


# ══════════════════════════════════════════════════════════════════════════════
# CITIZENS
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/citizens", status_code=201, tags=["Citizens"])
def register_citizen(body: CitizenCreate):
    """Register a new citizen. SQL: INSERT INTO citizen."""
    existing = execute_query(
        "SELECT citizen_id FROM citizen WHERE phone = %s",
        (body.phone,), fetch=True
    )
    if existing:
        raise HTTPException(status_code=422, detail="Phone number already registered.")

    new_id = execute_query(
        "INSERT INTO citizen (name, phone, email, address, ward_no) VALUES (%s,%s,%s,%s,%s) RETURNING citizen_id",
        (body.name, body.phone, body.email, body.address, body.ward_no)
    )
    return {"citizen_id": new_id, "message": "Citizen registered successfully"}


@app.get("/citizens", tags=["Citizens"])
def list_citizens():
    return execute_query("SELECT * FROM citizen ORDER BY name", fetch=True)


# ══════════════════════════════════════════════════════════════════════════════
# COMPLAINTS
# NOTE: /complaints/map-data MUST be declared BEFORE /complaints/{id}
#       to prevent FastAPI routing ambiguity.
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/complaints/map-data", tags=["Map"])
def complaint_map_data(current_user: dict = Depends(get_current_user)):
    """
    Return all complaints that have GPS coordinates.
    SQL: SELECT lat/lng + joined citizen and ward info.
    Used by the Leaflet.js map page.
    Protected: all authenticated users.
    """
    rows = execute_query(
        """
        SELECT
            c.complaint_id, c.latitude, c.longitude,
            c.damage_type, c.severity, c.status,
            c.address, c.worker_id,
            ci.name AS citizen_name,
            w.ward_name, w.ward_id
        FROM  complaint c
        JOIN  citizen   ci ON c.citizen_id = ci.citizen_id
        JOIN  ward      w  ON c.ward_id    = w.ward_id
        WHERE c.latitude  IS NOT NULL
          AND c.longitude IS NOT NULL
        ORDER BY c.filed_at DESC
        """,
        fetch=True
    )
    return rows


@app.post("/complaints", status_code=201, tags=["Complaints"])
def file_complaint(
    citizen_id:  int           = Form(...),
    ward_id:     int           = Form(...),
    description: str           = Form(...),
    damage_type: str           = Form(...),
    severity:    str           = Form(...),
    address:     str           = Form(...),
    latitude:    Optional[float] = Form(None),
    longitude:   Optional[float] = Form(None),
    photo:       Optional[UploadFile] = File(None),
    current_user: dict = Depends(get_current_user),
):
    """
    File a new road-damage complaint (multipart/form-data).
    Accepts an optional photo upload (.jpg/.jpeg/.png, max 5 MB).
    SQL: INSERT INTO complaint RETURNING complaint_id.
    Protected: citizen, officer, admin.
    """
    # Validate citizen and ward exist
    if not execute_query("SELECT 1 FROM citizen WHERE citizen_id=%s", (citizen_id,), fetch=True):
        _not_found("Citizen", citizen_id)
    if not execute_query("SELECT 1 FROM ward WHERE ward_id=%s", (ward_id,), fetch=True):
        _not_found("Ward", ward_id)

    # ── Handle optional photo upload ──────────────────────────────────────────
    photo_path = None
    if photo and photo.filename:
        ext = os.path.splitext(photo.filename)[-1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=422, detail="Only .jpg/.jpeg/.png files are allowed.")

        # Read content and validate size
        content = photo.file.read()
        if len(content) > MAX_PHOTO_BYTES:
            raise HTTPException(status_code=422, detail="Photo must be smaller than 5 MB.")

        # Save with timestamp prefix to avoid filename collisions
        filename  = f"{int(time.time())}_{photo.filename}"
        save_path = os.path.join(UPLOAD_DIR, filename)
        with open(save_path, "wb") as f:
            f.write(content)
        photo_path = f"uploads/{filename}"   # relative to /static/

    new_id = execute_query(
        """
        INSERT INTO complaint
            (citizen_id, ward_id, description, damage_type, severity,
             status, address, latitude, longitude, photo_path)
        VALUES (%s, %s, %s, %s, %s, 'open', %s, %s, %s, %s)
        RETURNING complaint_id
        """,
        (citizen_id, ward_id, description, damage_type, severity,
         address, latitude, longitude, photo_path)
    )
    return {"complaint_id": new_id, "message": "Complaint filed successfully", "photo_saved": photo_path is not None}


@app.get("/complaints", tags=["Complaints"])
def list_complaints(
    status_filter: Optional[str] = Query(None, alias="status"),
    ward_id: Optional[int] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    """
    Get all complaints with optional status/ward filters.
    SQL: SELECT with dynamic WHERE clauses. Joins citizen + ward.
    Protected: all authenticated users.
    """
    sql    = """
        SELECT c.complaint_id, c.description, c.damage_type, c.severity,
               c.status, c.address, c.filed_at, c.resolved_at, c.photo_path,
               c.latitude, c.longitude, c.worker_id,
               ci.name  AS citizen_name, ci.phone AS citizen_phone,
               w.ward_name
        FROM  complaint c
        JOIN  citizen   ci ON c.citizen_id = ci.citizen_id
        JOIN  ward      w  ON c.ward_id    = w.ward_id
        WHERE 1=1
    """
    params = []
    if status_filter:
        sql += " AND c.status = %s"
        params.append(status_filter)
    if ward_id:
        sql += " AND c.ward_id = %s"
        params.append(ward_id)
    sql += " ORDER BY c.filed_at DESC"

    rows = execute_query(sql, tuple(params), fetch=True)
    for r in rows:
        _dt(r, "filed_at", "resolved_at")
    return rows


@app.get("/complaints/{complaint_id}", tags=["Complaints"])
def get_complaint(
    complaint_id: int,
    current_user: dict = Depends(get_current_user),
):
    """
    Get a single complaint by ID with full detail + audit log.
    SQL: LEFT JOIN with worker. Separate query for complaint_log.
    Protected: all authenticated users.
    """
    rows = execute_query(
        """
        SELECT c.complaint_id, c.description, c.damage_type, c.severity,
               c.status, c.address, c.photo_path, c.filed_at, c.resolved_at,
               c.latitude, c.longitude,
               ci.name  AS citizen_name,  ci.phone  AS citizen_phone,
               ci.email AS citizen_email, ci.address AS citizen_address,
               w.ward_name, w.city,
               wo.name       AS worker_name,
               wo.skill_type AS worker_skill
        FROM  complaint c
        JOIN  citizen   ci  ON c.citizen_id = ci.citizen_id
        JOIN  ward      w   ON c.ward_id    = w.ward_id
        LEFT  JOIN worker wo ON c.worker_id = wo.worker_id
        WHERE c.complaint_id = %s
        """,
        (complaint_id,), fetch=True
    )
    if not rows:
        _not_found("Complaint", complaint_id)

    row  = rows[0]
    _dt(row, "filed_at", "resolved_at")

    logs = execute_query(
        """
        SELECT log_id, old_status, new_status, changed_by, changed_at
        FROM   complaint_log
        WHERE  complaint_id = %s
        ORDER  BY changed_at ASC
        """,
        (complaint_id,), fetch=True
    )
    for log in logs:
        _dt(log, "changed_at")
    row["audit_log"] = logs
    return row


@app.patch("/complaints/{complaint_id}/status", tags=["Complaints"])
def update_complaint_status(
    complaint_id: int,
    body: StatusUpdate,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(require_role(["officer", "admin"])),
):
    """
    Update complaint status. The PostgreSQL TRIGGER fires automatically to log
    the change in complaint_log. Also:
    - Sets resolved_at when resolved
    - Frees assigned worker when resolved
    - Queues background email notification to citizen
    Protected: officer, admin.
    """
    rows = execute_query(
        """
        SELECT c.complaint_id, c.status, c.worker_id,
               ci.name AS citizen_name, ci.email AS citizen_email,
               ci.citizen_id
        FROM   complaint c
        JOIN   citizen   ci ON c.citizen_id = ci.citizen_id
        WHERE  c.complaint_id = %s
        """,
        (complaint_id,), fetch=True
    )
    if not rows:
        _not_found("Complaint", complaint_id)

    current  = rows[0]
    old_st   = current["status"]
    new_st   = body.status.value

    if old_st == new_st:
        return {"message": f"Status is already '{new_st}', no change made."}

    # Update status (+ resolved_at if resolving)
    if new_st == "resolved":
        execute_query(
            "UPDATE complaint SET status=%s, resolved_at=NOW() WHERE complaint_id=%s",
            (new_st, complaint_id)
        )
        # Free the assigned worker so they become available for new complaints
        if current["worker_id"]:
            execute_query(
                "UPDATE worker SET is_available=TRUE WHERE worker_id=%s",
                (current["worker_id"],)
            )
    else:
        execute_query(
            "UPDATE complaint SET status=%s WHERE complaint_id=%s",
            (new_st, complaint_id)
        )

    # Manual log entry with officer name (trigger also fires with 'system_trigger')
    execute_query(
        """
        INSERT INTO complaint_log (complaint_id, old_status, new_status, changed_by)
        VALUES (%s, %s, %s, %s)
        """,
        (complaint_id, old_st, new_st, body.changed_by)
    )

    # Queue email notification in background (non-blocking)
    if current.get("citizen_email"):
        background_tasks.add_task(
            send_notification_background,
            complaint_id,
            current["citizen_id"],
            current["citizen_email"],
            current["citizen_name"],
            old_st,
            new_st,
        )

    return {"message": f"Status updated to '{new_st}'", "complaint_id": complaint_id}


@app.patch("/complaints/{complaint_id}/worker", tags=["Complaints"])
def assign_worker(
    complaint_id: int,
    body: WorkerAssign,
    current_user: dict = Depends(require_role(["officer", "admin"])),
):
    """
    Manually assign a worker to a complaint.
    SQL: UPDATE complaint SET worker_id + mark worker unavailable.
    Protected: officer, admin.
    """
    if not execute_query("SELECT 1 FROM complaint WHERE complaint_id=%s", (complaint_id,), fetch=True):
        _not_found("Complaint", complaint_id)

    worker = execute_query(
        "SELECT worker_id, is_available FROM worker WHERE worker_id=%s",
        (body.worker_id,), fetch=True
    )
    if not worker:
        _not_found("Worker", body.worker_id)
    if not worker[0]["is_available"]:
        raise HTTPException(status_code=422, detail="Worker is currently unavailable.")

    execute_query(
        "UPDATE complaint SET worker_id=%s WHERE complaint_id=%s",
        (body.worker_id, complaint_id)
    )
    execute_query(
        "UPDATE worker SET is_available=FALSE WHERE worker_id=%s",
        (body.worker_id,)
    )
    return {"message": f"Worker {body.worker_id} assigned to complaint {complaint_id}"}


@app.post("/complaints/{complaint_id}/auto-assign", tags=["Map"])
def auto_assign_worker(
    complaint_id: int,
    current_user: dict = Depends(require_role(["officer", "admin"])),
):
    """
    Auto-assign the nearest available worker using the Haversine formula.
    SQL: Calculates great-circle distance for workers in the same ward,
         orders by distance_km ASC, LIMIT 1.
    PostgreSQL change: ACOS → acos, RADIANS → radians, LEAST → LEAST (same).
    Protected: officer, admin.
    """
    # Fetch complaint location and ward
    comp = execute_query(
        "SELECT latitude, longitude, ward_id FROM complaint WHERE complaint_id=%s",
        (complaint_id,), fetch=True
    )
    if not comp:
        _not_found("Complaint", complaint_id)

    c = comp[0]
    if not c["latitude"] or not c["longitude"]:
        raise HTTPException(status_code=422, detail="Complaint has no GPS coordinates.")

    lat = c["latitude"]
    lng = c["longitude"]

    # Haversine query — finds nearest available worker in same ward
    # PostgreSQL trig functions are lowercase; LEAST works the same
    workers = execute_query(
        """
        SELECT worker_id, name,
          (6371 * acos(
            LEAST(1.0, cos(radians(%s)) * cos(radians(base_latitude)) *
            cos(radians(base_longitude) - radians(%s)) +
            sin(radians(%s)) * sin(radians(base_latitude)))
          )) AS distance_km
        FROM worker
        WHERE ward_id     = %s
          AND is_available = TRUE
          AND base_latitude IS NOT NULL
        ORDER BY distance_km ASC
        LIMIT 1
        """,
        (lat, lng, lat, c["ward_id"]), fetch=True
    )
    if not workers:
        raise HTTPException(status_code=404, detail="No available worker found in this ward.")

    worker = workers[0]
    dist   = round(float(worker["distance_km"]), 2)

    execute_query(
        "UPDATE complaint SET worker_id=%s, status='in_progress' WHERE complaint_id=%s",
        (worker["worker_id"], complaint_id)
    )
    execute_query(
        "UPDATE worker SET is_available=FALSE WHERE worker_id=%s",
        (worker["worker_id"],)
    )

    return {
        "complaint_id": complaint_id,
        "worker_id":    worker["worker_id"],
        "worker_name":  worker["name"],
        "distance_km":  dist,
        "message":      f"Worker '{worker['name']}' assigned ({dist} km away)"
    }


# ══════════════════════════════════════════════════════════════════════════════
# WARDS
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/wards", tags=["Wards"])
def list_wards():
    return execute_query(
        """
        SELECT w.ward_id, w.ward_name, w.city,
               o.name AS officer_name, o.designation
        FROM   ward w LEFT JOIN officer o ON w.officer_id = o.officer_id
        ORDER  BY w.ward_id
        """,
        fetch=True
    )


@app.get("/wards/{ward_id}/summary", tags=["Wards"])
def ward_summary(
    ward_id: int,
    current_user: dict = Depends(require_role(["officer", "admin"])),
):
    """
    Calls PostgreSQL function get_ward_summary(ward_id).
    (Converted from MySQL stored procedure GetWardSummary)
    Returns: total / open / in_progress / resolved counts.
    Protected: officer, admin.
    """
    ward = execute_query(
        "SELECT ward_id, ward_name FROM ward WHERE ward_id=%s",
        (ward_id,), fetch=True
    )
    if not ward:
        _not_found("Ward", ward_id)

    results = call_procedure("get_ward_summary", (ward_id,))
    if not results:
        return {"ward_id": ward_id, "message": "No data"}

    s = results[0]
    return {
        "ward_id":                ward_id,
        "ward_name":              ward[0]["ward_name"],
        "total_complaints":       s["total_complaints"],
        "open_complaints":        s["open_complaints"],
        "in_progress_complaints": s["in_progress_complaints"],
        "resolved_complaints":    s["resolved_complaints"],
    }


# ══════════════════════════════════════════════════════════════════════════════
# WORKERS
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/workers", tags=["Workers"])
def list_workers():
    return execute_query(
        """
        SELECT w.worker_id, w.name, w.phone, w.skill_type, w.is_available,
               w.base_latitude, w.base_longitude, wd.ward_name
        FROM   worker w LEFT JOIN ward wd ON w.ward_id = wd.ward_id
        ORDER  BY w.worker_id
        """,
        fetch=True
    )


# ══════════════════════════════════════════════════════════════════════════════
# ANALYTICS (all protected: admin only)
# PostgreSQL changes:
#   DATEDIFF(NOW(), col) → EXTRACT(EPOCH FROM (NOW() - col)) / 86400
#   DATE_FORMAT(col, '%Y-%m') → TO_CHAR(col, 'YYYY-MM')
#   SUM(CASE…) → COUNT(*) FILTER (WHERE …)  [cleaner PostgreSQL idiom]
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/analytics/ward-summary", tags=["Analytics"])
def analytics_ward_summary(
    current_user: dict = Depends(require_role(["admin"])),
):
    """
    Ward-wise complaint counts grouped by status.
    Protected: admin.
    """
    return execute_query(
        """
        SELECT
            w.ward_id, w.ward_name,
            COUNT(c.complaint_id)                                           AS total,
            COUNT(c.complaint_id) FILTER (WHERE c.status = 'open')         AS open,
            COUNT(c.complaint_id) FILTER (WHERE c.status = 'in_progress')  AS in_progress,
            COUNT(c.complaint_id) FILTER (WHERE c.status = 'resolved')     AS resolved
        FROM  ward w LEFT JOIN complaint c ON w.ward_id = c.ward_id
        GROUP BY w.ward_id, w.ward_name
        ORDER BY w.ward_id
        """,
        fetch=True
    )


@app.get("/analytics/sla-breach", tags=["Analytics"])
def analytics_sla_breach(
    current_user: dict = Depends(require_role(["admin"])),
):
    """
    Complaints open for more than 7 days (SLA breach).
    PostgreSQL: DATEDIFF → EXTRACT(EPOCH FROM age(NOW(), filed_at))/86400
    Protected: admin.
    """
    rows = execute_query(
        """
        SELECT c.complaint_id,
               ci.name  AS citizen_name, ci.phone,
               w.ward_name, c.damage_type, c.severity,
               c.filed_at,
               FLOOR(EXTRACT(EPOCH FROM (NOW() - c.filed_at)) / 86400)::INT AS days_pending,
               c.address
        FROM  complaint c
        JOIN  citizen   ci ON c.citizen_id = ci.citizen_id
        JOIN  ward      w  ON c.ward_id    = w.ward_id
        WHERE c.status <> 'resolved'
          AND (NOW() - c.filed_at) > INTERVAL '7 days'
        ORDER BY days_pending DESC
        """,
        fetch=True
    )
    for r in rows:
        _dt(r, "filed_at")
    return rows


@app.get("/analytics/monthly-trend", tags=["Analytics"])
def analytics_monthly_trend(
    current_user: dict = Depends(require_role(["admin"])),
):
    """
    Monthly complaint filing counts for the last 6 months.
    PostgreSQL: DATE_FORMAT → TO_CHAR; GROUP BY the expression alias.
    Protected: admin.
    """
    return execute_query(
        """
        SELECT TO_CHAR(filed_at, 'YYYY-MM') AS month,
               COUNT(*)                     AS count
        FROM   complaint
        GROUP  BY TO_CHAR(filed_at, 'YYYY-MM')
        ORDER  BY month DESC
        LIMIT  6
        """,
        fetch=True
    )


@app.get("/analytics/damage-breakdown", tags=["Analytics"])
def analytics_damage_breakdown(
    current_user: dict = Depends(require_role(["admin"])),
):
    """
    Count and percentage of complaints per damage type.
    Protected: admin.
    """
    return execute_query(
        """
        SELECT damage_type,
               COUNT(*)                                                           AS count,
               ROUND(COUNT(*) * 100.0 / NULLIF((SELECT COUNT(*) FROM complaint), 0), 1) AS percentage
        FROM   complaint
        GROUP  BY damage_type
        ORDER  BY count DESC
        """,
        fetch=True
    )


@app.get("/analytics/resolution-rate", tags=["Analytics"])
def analytics_resolution_rate(
    current_user: dict = Depends(require_role(["admin"])),
):
    """
    Per-ward resolution rate and average days to resolve.
    PostgreSQL: DATEDIFF(resolved_at, filed_at) →
                EXTRACT(EPOCH FROM (resolved_at - filed_at)) / 86400
    Protected: admin.
    """
    return execute_query(
        """
        SELECT w.ward_name,
               COUNT(c.complaint_id)                                                AS total,
               COUNT(c.complaint_id) FILTER (WHERE c.status = 'resolved')           AS resolved_count,
               ROUND(AVG(
                 CASE WHEN c.status = 'resolved'
                      THEN EXTRACT(EPOCH FROM (c.resolved_at - c.filed_at)) / 86400.0
                 END
               )::NUMERIC, 1)                                                       AS avg_days_to_resolve
        FROM   complaint c
        JOIN   ward      w ON c.ward_id = w.ward_id
        GROUP  BY w.ward_name
        ORDER  BY w.ward_name
        """,
        fetch=True
    )


# ══════════════════════════════════════════════════════════════════════════════
# ACTIVE COMPLAINTS VIEW (queries the PostgreSQL VIEW directly)
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/active-complaints", tags=["Complaints"])
def active_complaints_view(current_user: dict = Depends(get_current_user)):
    """Query the PostgreSQL VIEW active_complaints_view. Protected: all authenticated."""
    rows = execute_query(
        "SELECT * FROM active_complaints_view ORDER BY filed_at DESC",
        fetch=True
    )
    for r in rows:
        _dt(r, "filed_at")
    return rows
