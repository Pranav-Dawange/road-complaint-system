# 🛣️ Road Complaint Management System

> A full-stack DBMS project built with **FastAPI**, **PostgreSQL (Supabase)**, and **Bootstrap 5**.
> Citizens can file road-damage complaints, give feedback on resolved issues, view public advisories; officers manage and resolve complaints through a live dashboard and track resource usage.

---

## 📁 Project Structure

```
road_complaint_system/
├── main.py               # FastAPI app — all REST endpoints (Auth, Complaints, Analytics, PDF)
├── database.py           # PostgreSQL connection helper using psycopg2
├── models.py             # Pydantic request/response models
├── supabase_schema.sql   # PostgreSQL schema: tables, trigger, function, view, ENUMs
├── requirements.txt      # Python dependencies
├── .env                  # Environment Variables (Database URL, JWT Secret, MongoDB URI)
└── templates/            # Frontend HTML Views
    ├── index.html        # Citizen complaint form
    ├── dashboard.html    # Officer admin dashboard
    ├── analytics.html    # Analytics + bar chart + SLA breach table
    └── map.html          # Interactive Leaflet Map for complaints
```

---

## ✨ Features Added

- **Migration to PostgreSQL (Supabase)**: Switched from local MySQL to a cloud-based Supabase PostgreSQL instance.
- **JWT Authentication System**: Secure Role-Based Access Control (RBAC) separating Citizens, Officers, and Admins.
- **Complaint Feedback**: Citizens can leave a 1-5 star rating and comments upon issue resolution.
- **Public Advisories**: Officers can broadcast ward/city level announcements to citizens.
- **Resource Tracking**: Detailed resource costing (materials/quantity) attached to complaint resolution.
- **MongoDB GridFS Integraton**: Scalable photo uploads using MongoDB.
- **Auto Assignment via GPS**: Distance-based worker auto-assignment to complaints via the Haversine formula.
- **Dynamic PDF Generation**: On-the-fly downloadable PDF receipts for citizens upon submitting complaints, generated with ReportLab.

---

## ⚙️ Setup Instructions

### Prerequisites

| Tool | Version |
|------|---------|
| Python | 3.9+ |
| PostgreSQL / Supabase | Latest |
| MongoDB (Optional) | User's choice (local or atlas) |
| pip | Latest |

---

### Step 1 — Create the Database on Supabase

Create a new Supabase project or spin up your local PostgreSQL instance, then execute the schema and seed file:

```sql
-- In Supabase SQL Editor or PSQL CLI:
\i path/to/road_complaint_system/supabase_schema.sql
```

---

### Step 2 — Configure the Environment Values

Create a `.env` file in the root folder and add your connection variables:

```env
DATABASE_URL="postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-SUPABASE-REF].supabase.co:5432/postgres"
JWT_SECRET_KEY="your-secret-key"
MONGO_URI="mongodb+srv://<user>:<password>@cluster0.mongodb.net/road_complaints" # Optional
```

---

### Step 3 — Install Python Dependencies

```bash
cd road_complaint_system
pip install -r requirements.txt
```

---

### Step 4 — Start the API Server

```bash
uvicorn main:app --reload
```

The API is now live at **`http://localhost:8000`**

---

### Step 5 — Open the Frontend Pages

| Page | URL |
|------|-----|
| 📋 File a Complaint | http://localhost:8000/index |
| 🖥️ Officer Dashboard | http://localhost:8000/dashboard |
| 📊 Analytics | http://localhost:8000/analytics |
| 🗺️ Interactive Maps | http://localhost:8000/map |
| 📖 API Docs (Swagger) | http://localhost:8000/docs |

---

## 🗄️ Database Design

### Tables

| Table | Purpose |
|-------|---------|
| `app_user` | JWT-Authenticated User Accounts (Citizen, Officer, Admin) |
| `citizen` | Registered citizens who file complaints |
| `ward` | Administrative wards in Pune |
| `officer` | Officers responsible for each ward |
| `worker` | Field workers with skill types and GPS bases |
| `complaint` | Core complaint records with geolocation |
| `complaint_log` | Audit trail of all status changes |
| `complaint_feedback`| Citizen satisfaction ratings post-resolution |
| `resource_usage` | Logs of material expenditure by workers |
| `public_advisory` | Announcements at the ward/city level |

### Advanced PostgreSQL Features

| Feature | Details |
|---------|---------|
| **Trigger + Function** | `trg_complaint_status_log` — Calls `fn_log_complaint_status_change()` to auto-populate `complaint_log` |
| **Custom Function** | `get_ward_summary(ward_id)` — Returns real-time counts of open/in_progress/resolved issues |
| **View** | `active_complaints_view` — Non-resolved complaints with citizen + ward info joined |
| **Geospatial Math** | Standard Haversine distance computations via `acos` & `radians` to find nearest workers |
| **Indexes** | Partial indexing on unresolved complaints |

---

## 🔌 Core API Endpoints

### Auth
- `POST /register` \| `POST /login`

### Complaints & Maps
- `POST /complaints` — File a complaint (supports Multipart Form with Photos)
- `GET /complaints` — Filtered list
- `GET /complaints/map-data` — GeoJSON-like feed for Leaflet.js
- `POST /complaints/{id}/auto-assign` — Geo-locates the closest available worker
- `GET /complaints/{id}/report` — Downloads PDF receipt
- `PATCH /complaints/{id}/status` — Toggles state and emits asynchronous SMTP emails

### Infrastructure Extensions
- `POST /complaints/{id}/feedback` — Submit post-resolution feedback
- `POST /complaints/{id}/resources` — Log materials used
- `POST /advisories` / `GET /advisories` — Manage Public Bulletins

---

## 📦 Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | FastAPI (Python) |
| **Database** | PostgreSQL 15+ (Supabase) + MongoDB (GridFS) |
| **DB Driver** | psycopg2 + pymongo |
| **Validation** | Pydantic v2 |
| **Frontend** | HTML5 + Bootstrap 5 + Leaflet.js + Chart.js |
| **PDF Generation** | ReportLab |

---

*Road Complaint Management System — DBMS Project 2026*
