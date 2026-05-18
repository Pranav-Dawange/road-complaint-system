# 🛣️ Road Complaint Management System

> A full-stack DBMS course project built with **FastAPI**, **PostgreSQL (Supabase)**, **MongoDB (GridFS)**, and **Bootstrap 5**.
> Citizens can file road-damage complaints with photo evidence and GPS coordinates, receive email confirmations with PDF reports, track complaint progress, and provide feedback. Officers manage complaints through a real-time dashboard, auto-assign workers using geolocation, monitor ward-level analytics, and broadcast public advisories. Admins get an exclusive panel to manage wards, workers, and download comprehensive analytics reports.

---

## 📁 Project Structure

```
road-complaint-system/
│
├── main.py                # FastAPI app — 33+ REST endpoints (Auth, Complaints, Analytics, Admin, PDF, etc.)
├── auth.py                # JWT authentication & role-based access control (RBAC)
├── database.py            # PostgreSQL connection helper — execute_query, execute_function, execute_in_transaction
├── models.py              # Pydantic request/response models & enum definitions
├── notifications.py       # Email notification system (Gmail SMTP) with PDF attachments
├── pdf_report.py          # PDF generator using ReportLab — complaint receipts + analytics dashboard PDF
│
├── supabase_schema.sql    # PostgreSQL schema: 11 tables, 3 triggers, cursor function, view, indexes
├── new_features.sql       # 🆕 DBMS enhancements: audit table, 2 triggers, stored proc, helper function
├── schema.sql             # Original MySQL schema (for reference)
├── seed_data.sql          # Standalone seed data (complaints, citizens, wards, officers, workers)
│
├── csv_files/             # 🆕 Sample CSVs for bulk complaint import testing (5 files × 10 records)
├── requirements.txt       # Python dependencies (pinned versions)
├── .env.example           # Template for environment variables
├── .gitignore             # Git ignore rules (.env, venv, __pycache__, etc.)
│
├── static/
│   ├── css/design.css     # Glassmorphism design system (dark mode, animations, glass cards)
│   └── js/micro.js        # Shared micro-interactions (ripple, count-up, stagger, shake)
│
└── templates/
    ├── index.html         # Citizen portal — login, register, file complaints, download PDF
    ├── dashboard.html     # Officer dashboard — manage complaints, auto-assign workers, resources
    ├── analytics.html     # Analytics dashboard — charts, ward report, SLA breaches, PDF download
    ├── map.html           # Interactive Leaflet.js map with complaint markers
    └── admin.html         # 🆕 Admin panel — Wards, Workers, Audit Log, Import Complaints tabs
```

---

## ✨ Features

### 🔐 Authentication & Security
- **JWT Token Authentication** with bcrypt password hashing
- **Role-Based Access Control (RBAC)** — Three roles: `citizen`, `officer`, `admin`
- Secure token-based API protection on all sensitive endpoints
- Admin-only routes enforce strict role checks via `require_role(["admin"])`

### 📋 Complaint Management
- File complaints with **damage type**, **severity**, **GPS coordinates**, and **photo evidence**
- **MongoDB GridFS** integration for scalable photo storage
- **Auto-assign workers** using GPS-based **Haversine distance** calculation
- Real-time status tracking: `open` → `in_progress` → `resolved`
- **Citizen feedback** system (1-5 star rating + comments) after resolution
- **Resource tracking** — log materials, quantities, and costs per complaint

### 📧 Email Notification System
- **Complaint filed confirmation** — email sent to citizen with complaint details
- **Status change notifications** — automatic email on every status update
- **PDF report attached** to all emails (styled complaint receipt with audit log)
- Runs as **background tasks** — API responses are never blocked

### 📊 Analytics Dashboard (Officer + Admin)
- **Ward-wise complaint breakdown** (stacked bar chart)
- **Damage type distribution** (doughnut chart)
- **Monthly complaint trend** (line chart — last 6 months)
- **Cursor-based Ward Performance Report** — uses PostgreSQL explicit `CURSOR`
  - Summary stat cards (total complaints, avg resolution days, SLA breaches, best ward)
  - Horizontal bar chart comparing ward performance
  - Ward Health Scores with ranked progress bars
  - Detailed table with resolution rate, health pills, and totals footer
- **Resolution rate by ward** table with animated progress bars
- **SLA breach tracking** — complaints open > 7 days flagged with pulsing indicators
- 🆕 **Download Analytics PDF** — admin-only button generates a full analytics report PDF instantly

### 📄 PDF Report Generation
- **Complaint Receipt PDF** — branded, in-memory PDF with complaint details, citizen ID, assigned worker, status, audit log
- 🆕 **Analytics Dashboard PDF** — comprehensive 5-section report: Ward Summary, Monthly Trend, Damage Breakdown, Resolution Rates, SLA Breaches
- Both available as direct download from the UI
- Complaint receipt also sent as email attachment on filing

### 🗺️ Interactive Map
- **Leaflet.js** map with complaint markers (color-coded by severity)
- Click markers to view complaint details and auto-assign workers
- Floating filter panel: filter by ward, severity, and resolved status
- Stats bar showing real-time total/open/in-progress/resolved counts

### 📢 Public Advisories
- Officers can broadcast ward/city-level announcements
- Citizens see active advisories on the complaint portal

### 🆕 Admin Panel — System Control Panel (`/admin`)
- **Admin-only** access — login wall for non-admin users
- **Wards tab** — add/view wards with officer assignments
- **Workers tab** — add/view workers with skill, availability, GPS
- **Audit Log tab** — real-time view of all admin actions (ward/worker creation via DB triggers, status changes, bulk imports via Python)
- **Import Complaints tab** — bulk CSV upload with drag-and-drop; calls `file_complaint_proc()` per row inside a single `BEGIN/COMMIT` transaction
- Toast notifications on success/error; tab-pill navigation
- Admin nav link appears automatically across all pages when logged in as admin

### ⚡ Database Automation (Triggers, Stored Procedures & Cursor)
- **Trigger 1:** `trg_complaint_status_log` — auto-logs status changes to `complaint_log`
- **Trigger 2:** `trg_auto_notify_on_status_change` — auto-creates notification records
- **Trigger 3:** `trg_set_resolved_timestamp` — auto-manages `resolved_at` timestamps
- **🆕 Trigger 4:** `trg_log_ward_creation` — auto-logs ward creation to `admin_audit_log`
- **🆕 Trigger 5:** `trg_log_worker_creation` — auto-logs worker creation to `admin_audit_log`
- **🆕 Stored Procedure:** `file_complaint_proc()` — atomic complaint insertion with validation
- **Cursor Function:** `generate_all_wards_report()` — explicit cursor iterating over all wards
- **🆕 Audit Log:** `admin_audit_log` table tracks all admin actions (ward/worker creation, status changes, bulk imports)

---

## ⚙️ Setup Instructions

### Prerequisites

| Tool | Version |
|------|---------|
| Python | 3.9+ |
| PostgreSQL / Supabase | Latest |
| MongoDB (Optional) | Local or Atlas |
| pip | Latest |

---

### Step 1 — Clone & Create Virtual Environment

```bash
git clone https://github.com/Pranav-Dawange/road-complaint-system.git
cd road-complaint-system
python -m venv venv
source venv/bin/activate       # Linux/Mac
# venv\Scripts\activate        # Windows
```

---

### Step 2 — Install Dependencies

```bash
pip install -r requirements.txt
```

---

### Step 3 — Create the Database

Create a Supabase project (or local PostgreSQL instance), then run the schema:

```sql
-- In Supabase SQL Editor or psql CLI:
\i supabase_schema.sql
```

This creates all 11 tables, 3 triggers, cursor function, view, and indexes.

> **🆕 Also run `new_features.sql`** in Supabase SQL Editor after the schema:
> This adds the `admin_audit_log` table, 2 audit triggers, `file_complaint_proc()` stored procedure, and `citizen_phone_exists()` helper function.

---

### Step 4 — Configure Environment Variables

Copy the example and fill in your credentials:

```bash
cp .env.example .env
```

```env
DATABASE_URL="postgresql://postgres:<PASSWORD>@db.<REF>.supabase.co:5432/postgres"
SECRET_KEY="your-jwt-secret-key"
MONGO_URI="mongodb+srv://<user>:<pass>@cluster0.mongodb.net/road_complaints"   # Optional
EMAIL_USER="your-gmail@gmail.com"          # For email notifications
EMAIL_PASS="your-gmail-app-password"       # Gmail App Password (not regular password)
```

> **Note:** Email notifications require a Gmail App Password. Go to Google Account → Security → 2-Step Verification → App Passwords to generate one.

---

### Step 5 — Start the Server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Server is live at **`http://localhost:8000`**

---

### Step 6 — Open the Frontend

| Page | URL | Access |
|------|-----|--------|
| 📋 Citizen Portal | http://localhost:8000/index | Public |
| 🖥️ Officer Dashboard | http://localhost:8000/dashboard | Officer + Admin |
| 📊 Analytics | http://localhost:8000/analytics | Officer + Admin |
| 🗺️ Complaint Map | http://localhost:8000/map | All logged-in users |
| 🛡️ Admin Panel | http://localhost:8000/admin | **Admin only** |
| 📖 API Docs (Swagger) | http://localhost:8000/docs | Public |

---

### Default Credentials

| Role | Username | Password |
|------|----------|----------|
| Admin | `admin` | `admin123` |
| Officer | `officer1` | `officer123` |
| Citizen | `citizen1` | `citizen123` |

---

## 🗄️ Database Design

### Tables (12)

| Table | Purpose |
|-------|---------|
| `app_user` | JWT-authenticated user accounts (Citizen / Officer / Admin) |
| `citizen` | Registered citizens who file complaints |
| `ward` | Administrative wards in Pune (15 wards) |
| `officer` | Ward officers with admin privileges |
| `worker` | Field workers with skill types and GPS base locations |
| `complaint` | Core complaint records with geolocation and photo references |
| `complaint_log` | Audit trail of all status changes (auto-populated by trigger) |
| `complaint_feedback` | Citizen satisfaction ratings (1-5 stars) post-resolution |
| `resource_usage` | Material expenditure logs per complaint |
| `notification` | Email notification audit trail |
| `public_advisory` | Ward/city-level announcements |
| `admin_audit_log` | 🆕 Admin action audit log (ward/worker creation, status changes, bulk imports) |

### Advanced PostgreSQL Features

| Feature | Details |
|---------|---------|
| **Trigger 1** | `trg_complaint_status_log` → auto-logs status changes to `complaint_log` |
| **Trigger 2** | `trg_auto_notify_on_status_change` → auto-creates notification records on status change |
| **Trigger 3** | `trg_set_resolved_timestamp` → auto-manages `resolved_at` (BEFORE UPDATE) |
| **🆕 Trigger 4** | `trg_log_ward_creation` → auto-logs ward creation to `admin_audit_log` (AFTER INSERT on ward) |
| **🆕 Trigger 5** | `trg_log_worker_creation` → auto-logs worker creation to `admin_audit_log` (AFTER INSERT on worker) |
| **Cursor Function** | `generate_all_wards_report()` → explicit CURSOR iterating row-by-row over all wards |
| **🆕 Stored Procedure** | `file_complaint_proc()` → atomic complaint insertion with citizen/ward validation |
| **Stored Function** | `get_ward_summary(ward_id)` → real-time complaint counts per ward |
| **🆕 Helper Function** | `citizen_phone_exists(phone)` → phone duplicate check for bulk operations |
| **View** | `active_complaints_view` → non-resolved complaints with citizen + ward joins |
| **Indexes** | Composite + partial indexes on `complaint(ward_id, status, filed_at)` + audit log indexes |
| **ENUMs** | `damage_type_enum`, `severity_enum`, `complaint_status_enum`, `user_role_enum`, `skill_type_enum` |
| **JSONB** | `admin_audit_log.details` stores structured metadata per action |

---

## 🔌 API Endpoints

### Authentication
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `POST` | `/register` | Register a new user (citizen/officer) | Public |
| `POST` | `/login` | Login and receive JWT token | Public |

### Pages
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `GET` | `/index` | Citizen portal | Public |
| `GET` | `/dashboard` | Officer dashboard | Public (auth in JS) |
| `GET` | `/analytics` | Analytics page | Public (auth in JS) |
| `GET` | `/map` | Map view | Public (auth in JS) |
| `GET` | `/admin` | 🆕 Admin panel | Public (auth in JS) |

### Complaints
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `POST` | `/complaints` | File a complaint (multipart form + photo) | Any logged-in |
| `GET` | `/complaints` | List complaints (filterable by status/ward) | Any logged-in |
| `GET` | `/complaints/{id}` | Get complaint details + audit log | Any logged-in |
| `PATCH` | `/complaints/{id}/status` | Update status (triggers email) | Officer / Admin |
| `POST` | `/complaints/{id}/auto-assign` | Auto-assign nearest worker (Haversine) | Officer / Admin |
| `GET` | `/complaints/{id}/report` | Download PDF receipt (includes Citizen ID) | Any logged-in |
| `GET` | `/complaints/map-data` | GeoJSON data for Leaflet.js map | Any logged-in |

### Feedback & Resources
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `POST` | `/complaints/{id}/feedback` | Submit post-resolution feedback | Citizen |
| `GET` | `/complaints/{id}/feedback` | Get feedback for a complaint | Any logged-in |
| `POST` | `/complaints/{id}/resources` | Log materials used for repair | Officer / Admin |
| `GET` | `/complaints/{id}/resources` | Get resource usage for a complaint | Officer / Admin |

### Wards
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `GET` | `/wards` | List all wards with officer info | Public |
| `🆕 POST` | `/wards` | Create a new ward (`INSERT INTO ward`) | **Admin only** |
| `GET` | `/wards/{id}/summary` | Ward complaint summary | Officer / Admin |

### Workers
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `GET` | `/workers` | List all workers with ward info | Public |
| `🆕 POST` | `/workers` | Create a new worker (`INSERT INTO worker`) | **Admin only** |

### Analytics
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `GET` | `/analytics/ward-summary` | Ward-wise complaint counts by status | Officer / Admin |
| `GET` | `/analytics/sla-breach` | Complaints open > 7 days | Officer / Admin |
| `GET` | `/analytics/monthly-trend` | Monthly filing counts (last 6 months) | Officer / Admin |
| `GET` | `/analytics/damage-breakdown` | Damage type distribution with % | Officer / Admin |
| `GET` | `/analytics/resolution-rate` | Per-ward resolution rates + avg days | Officer / Admin |
| `GET` | `/analytics/all-wards-report` | Cursor-based comprehensive ward report | Officer / Admin |
| `🆕 GET` | `/analytics/report` | Download full Analytics Dashboard PDF | **Admin only** |

### Citizens, Advisories & 🆕 Bulk Import
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `POST` | `/citizens` | Register a new citizen | Public |
| `GET` | `/citizens/{id}` | Get citizen profile | Any logged-in |
| `POST` | `/advisories` | Post a public advisory | Officer / Admin |
| `GET` | `/advisories` | List active advisories | Public |
| `🆕 POST` | `/complaints/bulk-import` | Bulk import complaints from CSV (calls stored proc per row, single transaction) | **Admin only** |
| `🆕 GET` | `/admin/audit-log` | View admin audit log (ward/worker triggers + Python-logged actions) | **Admin only** |

---

## 📦 Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | FastAPI 0.136 (Python 3.9+) |
| **Database** | PostgreSQL 15+ (Supabase) |
| **File Storage** | MongoDB GridFS (photo uploads) |
| **DB Driver** | psycopg2-binary 2.9 + pymongo 4.17 |
| **Authentication** | JWT (python-jose 3.5) + bcrypt (passlib 1.7) |
| **Validation** | Pydantic v2 |
| **Email** | Gmail SMTP (smtplib) with HTML templates + PDF attachments |
| **PDF Generation** | ReportLab 4.4 — complaint receipts & analytics reports |
| **Frontend** | HTML5 + Bootstrap 5.3 + Chart.js 4.4 + Leaflet.js 1.9 |
| **Design System** | Custom glassmorphism CSS (dark mode, micro-animations) |

---

## 👥 Roles & Permissions

| Role | Capabilities |
|------|-------------|
| **Citizen** | Register, login, file complaints, upload photos, download PDF receipts, submit feedback, view advisories |
| **Officer** | All citizen capabilities + manage complaints, update status, auto-assign workers, log resources, post advisories, access analytics dashboard |
| **Admin** | All officer capabilities + access Admin Panel, create wards, create workers, download Analytics PDF report |

---

## 🆕 Changelog — Latest Update (DBMS Enhancements)

### Added
- **`new_features.sql`** — run in Supabase to activate all DBMS features below
- **`admin_audit_log` table** — tracks all admin actions with JSONB details
- **Trigger: `trg_log_ward_creation`** — auto-fires on `INSERT INTO ward`, logs to audit table
- **Trigger: `trg_log_worker_creation`** — auto-fires on `INSERT INTO worker`, logs to audit table
- **Stored Procedure: `file_complaint_proc()`** — atomic complaint insertion with citizen/ward validation
- **`POST /complaints/bulk-import`** — upload CSV, pre-validates each row, calls stored proc per row, wraps all in `BEGIN/COMMIT`
- **`GET /admin/audit-log`** — returns all audit log entries (triggers + Python-logged)
- **`log_admin_action()` Python helper** — logs `COMPLAINT_STATUS_CHANGED` and `COMPLAINTS_BULK_IMPORTED` to audit table
- **Admin Panel — Audit Log tab** — real-time table of all admin actions with JSONB details
- **Admin Panel — Import Complaints tab** — drag-and-drop CSV upload with results table
- **5 sample CSV files** in `csv_files/` for bulk import testing
- **Pre-validation** of `citizen_id` / `ward_id` before transaction (invalid rows → error list, valid rows → atomic insert)
- Renamed Admin nav link to **"System Control Panel"**; removed File Complaint from admin navbar

---

*Road Complaint Management System — DBMS Course Project 2026*
