# 👥 Team Work Distribution Plan

To ensure every 4 members get a balanced learning experience across the full stack (DBMS, Backend, and Frontend), the project features are divided "vertically". This means each member takes full ownership of a specific data flow, handling its database tables, server-side APIs, and user interface.

## 🟢 Member 1: Citizen Experience & Core Ingestion
**Focus:** Public data entry, user experience, and baseline schema.
* **DBMS / Schema:**
  * Design, script, and manage the `CITIZEN` and `COMPLAINT` tables.
  * Implement **Indexes** on frequently searched/filtered columns (e.g., `status`, `filed_at`, `ward_id`).
* **Backend (FastAPI):**
  * Develop the `/citizens` (Registration & Listing) endpoints.
  * Develop the `/complaints` (Submission via POST) endpoints.
* **Frontend (HTML/JS):**
  * Build the Citizen Complaint Submission Form (`templates/index.html`).
  * Ensure the form successfully sends POST requests and gracefully displays success/error alerts to the user.

## 🔵 Member 2: Admin Dashboard & Routing
**Focus:** Administrative operations, filtering, and the core officer view.
* **DBMS / Schema:**
  * Design, script, and manage the `WARD` and `OFFICER` tables.
  * Handle the database design pattern for the **Circular Foreign Keys** between Wards and Officers (insertion logic).
* **Backend (FastAPI):**
  * Develop endpoints for `/wards` listing.
  * Develop the `/complaints` list endpoints with filtering logic (by `status` or `ward_id`).
* **Frontend (HTML/JS):**
  * Build the Officer Admin Dashboard (`templates/dashboard.html`).
  * Implement the frontend logic to dynamically fetch and display active complaints in a table, allowing the officer to filter by ward.

## 🟣 Member 3: Advanced DB Features & Analytics
**Focus:** Complex queries, data aggregation, and data visualization.
* **DBMS / Schema:**
  * Develop the MySQL **Stored Procedure**: `GetWardSummary(ward_id)` to calculate open/in-progress counts inside the database.
  * Create the MySQL **View**: `active_complaints_view` to join complaint data cleanly with citizen and ward names.
* **Backend (FastAPI):**
  * Develop analytics API endpoints: `/analytics/ward-summary` and `/wards/{id}/summary` (calling the stored procedure).
  * Create the endpoint to directly query the View (`/active-complaints`).
* **Frontend (HTML/JS):**
  * Build the Analytics & Reporting Page (`templates/analytics.html`).
  * Integrate an external library like **Chart.js** to render visual bar/pie charts using data from the analytics APIs.

## 🟠 Member 4: Workflow Automation & Auditing
**Focus:** State management, database macros, and Service Level Agreement (SLA) monitoring.
* **DBMS / Schema:**
  * Design and manage the `COMPLAINT_LOG` and `WORKER` tables.
  * Develop the MySQL **Trigger**: `trg_complaint_status_log` to automatically record an audit trail on row update.
* **Backend (FastAPI):**
  * Develop the update endpoints: `PATCH /complaints/{id}/status` and `PATCH /complaints/{id}/worker`.
  * Develop the endpoint to detect SLA breaches (`/analytics/sla-breach` - fetching complaints unresolved down a timeline).
* **Frontend (HTML/JS):**
  * Build the UI modals for officers to update statuses and assign workers on the dashboard.
  * Display the "Audit Trail" (driven by the trigger) on the frontend.
  * Build the SLA Breach warning table/section.

---

### 🤝 Shared Collaboration Points
- **Database Connection (`database.py`):** Set up the Python-MySQL connection globally as a team.
- **Pydantic Models (`models.py`):** Everyone writes the specific Pydantic schemas needed for their assigned endpoints in this shared file.
- **UI Design (`static/css` & Bootstrap):** The entire team should agree on a shared color palette and use standard Bootstrap 5 utility classes to ensure the app doesn't look pieced together.
