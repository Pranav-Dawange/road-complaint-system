# 🛣️ Road Complaint Management System

> A full-stack DBMS course project built with **FastAPI**, **PostgreSQL (Supabase)**, **MongoDB (GridFS)**, and **Bootstrap 5**.
> Citizens can file road-damage complaints with photo evidence and GPS coordinates, receive email confirmations with PDF reports, track complaint progress, and provide feedback. Officers manage complaints through a real-time dashboard, auto-assign workers using geolocation, monitor ward-level analytics, and broadcast public advisories.

---

## 📁 Project Structure

```
road-complaint-system/
│
├── main.py                # FastAPI app — 25+ REST endpoints (Auth, Complaints, Analytics, PDF, etc.)
├── auth.py                # JWT authentication & role-based access control (RBAC)
├── database.py            # PostgreSQL connection helper using psycopg2 (RealDictCursor)
├── models.py              # Pydantic request/response models & enum definitions
├── notifications.py       # Email notification system (Gmail SMTP) with PDF attachments
├── pdf_report.py          # Shared PDF report generator using ReportLab (complaint receipts)
│
├── supabase_schema.sql    # PostgreSQL schema: 11 tables, 3 triggers, cursor function, view, indexes, seed data
├── schema.sql             # Original MySQL schema (for reference)
├── seed_data.sql          # Standalone seed data (complaints, citizens, wards, officers, workers)
│
├── requirements.txt       # Python dependencies
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
    ├── analytics.html     # Analytics dashboard — charts, cursor-based ward report, SLA breaches
    └── map.html           # Interactive Leaflet.js map with complaint markers
```

---

## ✨ Features

### 🔐 Authentication & Security
- **JWT Token Authentication** with bcrypt password hashing
- **Role-Based Access Control (RBAC)** — Citizens and Officers (officers have admin privileges)
- Secure token-based API protection on all endpoints

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

### 📊 Analytics Dashboard
- **Ward-wise complaint breakdown** (bar chart)
- **Damage type distribution** (doughnut chart)
- **Monthly complaint trend** (line chart — last 6 months)
- **Cursor-based Ward Performance Report** — uses PostgreSQL explicit `CURSOR` to iterate over all wards
  - Summary stat cards (total complaints, avg resolution days, SLA breaches, best ward)
  - Horizontal stacked bar chart comparing ward performance
  - Ward Health Scores with ranked progress bars
  - Detailed table with resolution rate progress bars, health pills, and totals footer
- **Resolution rate by ward** table
- **SLA breach tracking** — complaints open > 7 days flagged with pulsing indicators

### 📄 PDF Report Generation
- Styled, branded PDF receipts generated in-memory using **ReportLab**
- Includes: complaint details, citizen info, assigned worker, status badges, audit log
- Available as direct download and as email attachment

### 🗺️ Interactive Map
- **Leaflet.js** map with complaint markers (color-coded by severity)
- Click markers to view complaint details
- Real-time data from the API

### 📢 Public Advisories
- Officers can broadcast ward/city-level announcements
- Citizens see active advisories on the complaint portal

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
uvicorn main:app --reload
```

Server is live at **`http://localhost:8000`**

---

### Step 6 — Open the Frontend

| Page | URL |
|------|-----|
| 📋 Citizen Portal | http://localhost:8000/index |
| 🖥️ Officer Dashboard | http://localhost:8000/dashboard |
| 📊 Analytics | http://localhost:8000/analytics |
| 🗺️ Complaint Map | http://localhost:8000/map |
| 📖 API Docs (Swagger) | http://localhost:8000/docs |

---

## 🗄️ Database Design

### Tables (11)

| Table | Purpose |
|-------|---------|
| `app_user` | JWT-authenticated user accounts (Citizen / Officer) |
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
| **ENUMs** | `damage_type_enum`, `severity_enum`, `complaint_status_enum`, `user_role_enum` |

---

## 🔌 Core API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/register` | Register a new user (citizen/officer) |
| `POST` | `/login` | Login and receive JWT token |

### Complaints
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/complaints` | File a complaint (multipart form + photo) |
| `GET` | `/complaints` | List complaints (filterable by status/ward) |
| `GET` | `/complaints/{id}` | Get complaint details + audit log |
| `PATCH` | `/complaints/{id}/status` | Update status (triggers email notification) |
| `POST` | `/complaints/{id}/auto-assign` | Auto-assign nearest worker via Haversine |
| `GET` | `/complaints/{id}/report` | Download PDF receipt |
| `GET` | `/complaints/map-data` | GeoJSON data for Leaflet.js map |

### Feedback & Resources
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/complaints/{id}/feedback` | Submit post-resolution feedback (1-5 stars) |
| `GET` | `/complaints/{id}/feedback` | Get feedback for a complaint |
| `POST` | `/complaints/{id}/resources` | Log materials used for repair |
| `GET` | `/complaints/{id}/resources` | Get resource usage for a complaint |

### Analytics (Officer/Admin only)
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/analytics/ward-summary` | Ward-wise complaint counts by status |
| `GET` | `/analytics/sla-breach` | Complaints open > 7 days |
| `GET` | `/analytics/monthly-trend` | Monthly filing counts (last 6 months) |
| `GET` | `/analytics/damage-breakdown` | Damage type distribution |
| `GET` | `/analytics/resolution-rate` | Per-ward resolution rates |
| `GET` | `/analytics/all-wards-report` | Cursor-based comprehensive ward report |

### Advisories
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/advisories` | Post a public advisory |
| `GET` | `/advisories` | List active advisories |

---

## 📦 Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | FastAPI (Python 3.9+) |
| **Database** | PostgreSQL 15+ (Supabase) |
| **File Storage** | MongoDB GridFS (photo uploads) |
| **DB Driver** | psycopg2 (RealDictCursor) + pymongo |
| **Authentication** | JWT (python-jose) + bcrypt (passlib) |
| **Validation** | Pydantic v2 |
| **Email** | Gmail SMTP (smtplib) with HTML templates |
| **PDF Generation** | ReportLab |
| **Frontend** | HTML5 + Bootstrap 5 + Chart.js + Leaflet.js |
| **Design System** | Custom glassmorphism CSS (dark mode) |

---

## 👥 Roles

| Role | Capabilities |
|------|-------------|
| **Citizen** | Register, login, file complaints, upload photos, download PDF receipts, submit feedback, view advisories |
| **Officer** | All citizen capabilities + manage complaints, update status, auto-assign workers, log resources, post advisories, access analytics dashboard |

> Officers have full administrative privileges including analytics access, complaint management, worker assignment, and advisory management.

---

*Road Complaint Management System — DBMS Course Project 2026*
