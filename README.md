# 🛣️ Road Complaint Management System

> A full-stack DBMS college project built with **FastAPI**, **MySQL**, and **Bootstrap 5**.
> Citizens can file road-damage complaints; officers manage and resolve them through a live dashboard.

---

## 📁 Project Structure

```
road_complaint_system/
├── main.py               # FastAPI app — all REST endpoints
├── database.py           # MySQL connection helper (no ORM)
├── models.py             # Pydantic request/response models
├── schema.sql            # CREATE TABLEs + trigger + procedure + view + indexes
├── seed_data.sql         # Sample data (Pune wards, citizens, complaints)
├── requirements.txt      # Python dependencies
└── templates/
    ├── index.html        # Citizen complaint form
    ├── dashboard.html    # Officer admin dashboard
    └── analytics.html    # Analytics + bar chart + SLA breach table
```

---

## ⚙️ Setup Instructions

### Prerequisites

| Tool | Version |
|------|---------|
| Python | 3.9+ |
| MySQL Server | 8.0+ |
| pip | Latest |

---

### Step 1 — Create the Database

Open **MySQL Workbench** or the `mysql` CLI and run the two SQL files in order:

```sql
-- In MySQL Workbench / CLI:
source path/to/road_complaint_system/schema.sql;
source path/to/road_complaint_system/seed_data.sql;
```

Or from the command line:

```bash
mysql -u root -p < schema.sql
mysql -u root -p road_complaint_db < seed_data.sql
```

---

### Step 2 — Configure the Database Connection

Open **`database.py`** and update these three values to match your MySQL setup:

```python
DB_CONFIG = {
    "host":     "localhost",
    "port":     3306,
    "user":     "root",      # ← your MySQL username
    "password": "",          # ← your MySQL password
    "database": "road_complaint_db",
    ...
}
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
| 📖 API Docs (Swagger) | http://localhost:8000/docs |

---

## 🗄️ Database Design

### Tables

| Table | Purpose |
|-------|---------|
| `CITIZEN` | Registered citizens who file complaints |
| `WARD` | Administrative wards in Pune |
| `OFFICER` | Officers responsible for each ward |
| `WORKER` | Field workers with skill types |
| `COMPLAINT` | Core complaint records |
| `COMPLAINT_LOG` | Audit trail of all status changes |

### Advanced SQL Features

| Feature | Details |
|---------|---------|
| **Trigger** | `trg_complaint_status_log` — auto-logs status changes into `COMPLAINT_LOG` |
| **Stored Procedure** | `GetWardSummary(ward_id)` — returns open/in_progress/resolved counts |
| **View** | `active_complaints_view` — non-resolved complaints with citizen + ward info |
| **Indexes** | On `COMPLAINT.ward_id`, `COMPLAINT.status`, `COMPLAINT.filed_at` |

---

## 🔌 API Endpoints

| Method | Route | Description |
|--------|-------|-------------|
| GET | `/` | Health check |
| POST | `/citizens` | Register a citizen |
| GET | `/citizens` | List all citizens |
| POST | `/complaints` | File a complaint |
| GET | `/complaints` | List complaints (filter by `status`, `ward_id`) |
| GET | `/complaints/{id}` | Get complaint details + audit log |
| PATCH | `/complaints/{id}/status` | Update complaint status (triggers auto-log) |
| PATCH | `/complaints/{id}/worker` | Assign a worker |
| GET | `/wards` | List all wards |
| GET | `/wards/{id}/summary` | Ward stats via stored procedure |
| GET | `/analytics/ward-summary` | Ward-wise grouped complaint counts |
| GET | `/analytics/sla-breach` | Open complaints older than 7 days |
| GET | `/active-complaints` | Query the MySQL VIEW directly |
| GET | `/workers` | List all workers |

---

## 🎯 Key Design Decisions

- **No ORM** — All SQL is written manually using `mysql-connector-python` (DBMS project requirement)
- **Trigger demonstration** — Every `PATCH /complaints/{id}/status` call fires the MySQL trigger
- **Stored procedure** — `GET /wards/{id}/summary` calls `CALL GetWardSummary(?)` via `cursor.callproc()`
- **CORS enabled** — The API allows requests from any origin so the HTML frontend works seamlessly
- **Circular FK** — `OFFICER ↔ WARD` is a deliberate circular reference (common in real schemas); handled by inserting `OFFICER` first with `NULL ward_id`, then `WARD`, then updating `OFFICER`

---

## 📦 Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI (Python) |
| Database | MySQL 8 |
| DB Connector | mysql-connector-python |
| Validation | Pydantic v2 |
| Frontend | HTML5 + Bootstrap 5 CDN + Chart.js CDN |
| Server | Uvicorn (ASGI) |

---

*Road Complaint Management System — DBMS College Project 2024*
