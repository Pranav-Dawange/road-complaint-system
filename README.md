# 🛣️ Road Complaint Management System

> A full-stack DBMS course project built with **FastAPI**, **PostgreSQL (Supabase)**, **MongoDB (GridFS)**, and **Bootstrap 5**.
> Citizens can file road-damage complaints with photo evidence and GPS coordinates, receive email confirmations with PDF reports, track complaint progress, and provide feedback. Officers manage complaints through a real-time dashboard, auto-assign workers using geolocation, monitor ward-level analytics, and broadcast public advisories. Admins get an exclusive panel to manage wards, workers, and download comprehensive analytics reports.

---

## 📁 Project Structure

```
road-complaint-system/
│
├── main.py                # FastAPI app — 30+ REST endpoints (Auth, Complaints, Analytics, Admin, PDF, etc.)
├── auth.py                # JWT authentication & role-based access control (RBAC)
├── database.py            # PostgreSQL connection helper using psycopg2 (RealDictCursor)
├── models.py              # Pydantic request/response models & enum definitions (incl. WardCreate, WorkerCreate)
├── notifications.py       # Email notification system (Gmail SMTP) with PDF attachments
├── pdf_report.py          # PDF generator using ReportLab — complaint receipts + analytics dashboard PDF
│
├── supabase_schema.sql    # PostgreSQL schema: 11 tables, 3 triggers, cursor function, view, indexes, seed data
├── schema.sql             # Original MySQL schema (for reference)
├── seed_data.sql          # Standalone seed data (complaints, citizens, wards, officers, workers)
│
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
    ├── analytics.html     # Analytics dashboard — charts, ward report, SLA breaches, PDF download (admin)
    ├── map.html           # Interactive Leaflet.js map with complaint markers
    └── admin.html         # 🆕 Admin panel — manage wards & workers, live tables
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

### 🆕 Admin Panel (`/admin`)
- **Admin-only** access — login wall for non-admin users
- **Add New Ward** — form with ward name, city, optional officer assignment; `INSERT INTO ward` SQL
- **Add New Worker** — form with name, phone, skill type, ward assignment, GPS base location; `INSERT INTO worker` SQL
- **Live Ward Table** — real-time list of all wards with officer assignments
- **Live Worker Table** — real-time list of all workers with availability status and GPS coordinates
- Toast notifications on success/error
- Tab-based interface (Wards / Workers)
- Admin nav link appears automatically in all pages when logged in as admin

### ⚡ Database Automation (Triggers & Cursor)
- **Trigger 1:** `trg_complaint_status_log` — auto-logs status changes to audit trail
- **Trigger 2:** `trg_auto_notify_on_status_change` — auto-creates notification records
- **Trigger 3:** `trg_set_resolved_timestamp` — auto-manages `resolved_at` timestamps
- **Cursor Function:** `generate_all_wards_report()` — explicit cursor iterating over all wards for aggregated statistics

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

This creates all 11 tables, 3 triggers, cursor function, view, indexes, and seed data.

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

### Tables (11)

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

### Advanced PostgreSQL Features

| Feature | Details |
|---------|---------|
| **Trigger 1** | `trg_complaint_status_log` → auto-logs status changes to `complaint_log` |
| **Trigger 2** | `trg_auto_notify_on_status_change` → auto-creates notification records on status change |
| **Trigger 3** | `trg_set_resolved_timestamp` → auto-manages `resolved_at` (BEFORE UPDATE) |
| **Cursor Function** | `generate_all_wards_report()` → explicit CURSOR iterating row-by-row over all wards |
| **Stored Function** | `get_ward_summary(ward_id)` → real-time complaint counts per ward |
| **View** | `active_complaints_view` → non-resolved complaints with citizen + ward joins |
| **Indexes** | Composite + partial indexes on `complaint(ward_id, status, filed_at)` |
| **ENUMs** | `damage_type_enum`, `severity_enum`, `complaint_status_enum`, `user_role_enum`, `skill_type_enum` |

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

### Citizens & Advisories
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `POST` | `/citizens` | Register a new citizen | Public |
| `GET` | `/citizens/{id}` | Get citizen profile | Any logged-in |
| `POST` | `/advisories` | Post a public advisory | Officer / Admin |
| `GET` | `/advisories` | List active advisories | Public |

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

## 🆕 Changelog — Latest Update

### Added
- **Admin Panel** (`/admin`) — dedicated page for ward and worker management
- **POST /wards** — admin creates new wards with SQL `INSERT INTO ward`
- **POST /workers** — admin creates new workers with SQL `INSERT INTO worker`
- **Analytics PDF Export** (`GET /analytics/report`) — admin-only download of full analytics report
- **Citizen ID in complaint PDF** — complaint receipt now includes citizen ID for reference
- **Admin nav link** — automatically shown in navbar across all pages when logged in as admin
- **Pinned dependency versions** in `requirements.txt`

---

*Road Complaint Management System — DBMS Course Project 2026*
