"""
pdf_report.py — Shared PDF report generator for Road Complaint Management System

Generates styled PDFs in-memory (returns bytes).
Functions:
  1. generate_complaint_pdf(complaint_id)  → complaint receipt
  2. generate_analytics_pdf()              → analytics dashboard report
Used by:
  - API endpoint GET /complaints/{id}/report  (download)
  - API endpoint GET /analytics/report        (download)
  - Email notification system (attachment)
"""

import io
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from database import execute_query


def _dt(row: dict, *keys):
    """Convert datetime objects to strings in-place."""
    for k in keys:
        if row.get(k):
            row[k] = str(row[k])
    return row


def generate_complaint_pdf(complaint_id: int) -> bytes | None:
    """
    Generate a styled PDF receipt for a complaint.
    Returns the PDF as bytes, or None if complaint not found.
    """

    # ── Fetch complaint data ──────────────────────────────────────────────────
    rows = execute_query(
        """
        SELECT c.complaint_id, c.description, c.damage_type, c.severity,
               c.status, c.address, c.filed_at, c.resolved_at,
               c.latitude, c.longitude,
               ci.citizen_id,
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
        return None

    c = rows[0]
    _dt(c, "filed_at", "resolved_at")

    logs = execute_query(
        """
        SELECT old_status, new_status, changed_by, changed_at
        FROM   complaint_log
        WHERE  complaint_id = %s
        ORDER  BY changed_at ASC
        """,
        (complaint_id,), fetch=True
    )
    for log in logs:
        _dt(log, "changed_at")

    # ── Colour palette ────────────────────────────────────────────────────────
    NAVY   = colors.HexColor("#0f172a")
    CYAN   = colors.HexColor("#06b6d4")
    SLATE  = colors.HexColor("#1e293b")
    LIGHT  = colors.HexColor("#f1f5f9")
    MUTED  = colors.HexColor("#64748b")
    WHITE  = colors.white
    GREEN  = colors.HexColor("#10b981")
    YELLOW = colors.HexColor("#f59e0b")
    RED    = colors.HexColor("#ef4444")
    BLUE   = colors.HexColor("#3b82f6")

    STATUS_COLORS = {
        "open":        YELLOW,
        "in_progress": BLUE,
        "resolved":    GREEN,
    }
    SEVERITY_COLORS = {
        "low":      BLUE,
        "medium":   YELLOW,
        "critical": RED,
    }

    status_color   = STATUS_COLORS.get(c.get("status", ""), MUTED)
    severity_color = SEVERITY_COLORS.get(c.get("severity", ""), MUTED)

    # ── Build PDF in memory ───────────────────────────────────────────────────
    buf = io.BytesIO()
    PAGE_W, PAGE_H = A4
    MARGIN = 20 * mm

    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN,  bottomMargin=MARGIN,
        title=f"Complaint Report #{complaint_id}",
        author="Road Complaint Management System",
    )

    styles = getSampleStyleSheet()

    def style(name, **kw):
        return ParagraphStyle(name, parent=styles["Normal"], **kw)

    s_title   = style("Title",   fontSize=22, textColor=WHITE,  leading=28, alignment=TA_CENTER, fontName="Helvetica-Bold")
    s_sub     = style("Sub",     fontSize=9,  textColor=CYAN,   leading=14, alignment=TA_CENTER, fontName="Helvetica")
    s_section = style("Section", fontSize=11, textColor=CYAN,   leading=16, fontName="Helvetica-Bold", spaceBefore=10)
    s_label   = style("Label",   fontSize=8,  textColor=MUTED,  leading=11, fontName="Helvetica-Bold")
    s_value   = style("Value",   fontSize=9,  textColor=NAVY,   leading=13, fontName="Helvetica")
    s_desc    = style("Desc",    fontSize=9,  textColor=SLATE,  leading=14, fontName="Helvetica")
    s_footer  = style("Footer",  fontSize=7,  textColor=MUTED,  leading=10, alignment=TA_CENTER)
    s_log_hdr = style("LogHdr",  fontSize=8,  textColor=WHITE,  leading=12, fontName="Helvetica-Bold", alignment=TA_CENTER)
    s_log_val = style("LogVal",  fontSize=8,  textColor=SLATE,  leading=12, alignment=TA_CENTER)
    s_badge   = style("Badge",   fontSize=9,  textColor=WHITE,  leading=12, fontName="Helvetica-Bold", alignment=TA_CENTER)

    story = []

    # ── Header banner ─────────────────────────────────────────────────────────
    header_data = [[
        Paragraph("🛣️  Road Complaint Management System", s_title),
    ]]
    header_tbl = Table(header_data, colWidths=[PAGE_W - 2 * MARGIN])
    header_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY),
        ("ROWPADDING", (0, 0), (-1, -1), 14),
        ("ROUNDEDCORNERS", [8]),
    ]))
    story.append(header_tbl)
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("Complaint Receipt — Official Document", s_sub))
    story.append(Spacer(1, 6 * mm))

    # ── Status & severity badges (side by side) ───────────────────────────────
    status_label   = (c.get("status") or "unknown").replace("_", " ").upper()
    severity_label = (c.get("severity") or "unknown").upper()

    badge_data = [[
        Paragraph(f"STATUS: {status_label}", s_badge),
        Paragraph(f"SEVERITY: {severity_label}", s_badge),
        Paragraph(f"COMPLAINT #{c['complaint_id']}", s_badge),
    ]]
    col_w = (PAGE_W - 2 * MARGIN) / 3
    badge_tbl = Table(badge_data, colWidths=[col_w, col_w, col_w])
    badge_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), status_color),
        ("BACKGROUND", (1, 0), (1, 0), severity_color),
        ("BACKGROUND", (2, 0), (2, 0), CYAN),
        ("ROWPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("ROUNDEDCORNERS", [6]),
    ]))
    story.append(badge_tbl)
    story.append(Spacer(1, 7 * mm))

    # ── Helper to build a 2-column info table ─────────────────────────────────
    def info_table(rows_data):
        col_w2 = (PAGE_W - 2 * MARGIN) / 2
        tbl = Table(rows_data, colWidths=[col_w2, col_w2])
        tbl.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0),  SLATE),
            ("BACKGROUND",    (0, 1), (-1, -1), LIGHT),
            ("ROWPADDING",    (0, 0), (-1, -1), 6),
            ("LEFTPADDING",   (0, 0), (-1, -1), 8),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
            ("LINEBELOW",     (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("VALIGN",        (0, 0), (-1, -1), "TOP"),
            ("ROUNDEDCORNERS", [6]),
        ]))
        return tbl

    def lbl(text): return Paragraph(text, s_label)
    def val(text): return Paragraph(str(text) if text else "—", s_value)

    # ── Section: Complaint Info ───────────────────────────────────────────────
    story.append(Paragraph("📋  Complaint Information", s_section))
    story.append(HRFlowable(width="100%", thickness=1, color=CYAN, spaceAfter=4))

    story.append(info_table([
        [lbl("Complaint ID"),    lbl("Damage Type")],
        [val(f"#{c['complaint_id']}"), val((c.get("damage_type") or "").capitalize())],
        [lbl("Filed At"),        lbl("Resolved At")],
        [val(c.get("filed_at")),  val(c.get("resolved_at") or "Not yet resolved")],
        [lbl("Location (Address)"), lbl("Ward / City")],
        [val(c.get("address")),  val(f"{c.get('ward_name', '')} — {c.get('city', '')}")],
        [lbl("Latitude"),        lbl("Longitude")],
        [val(c.get("latitude")), val(c.get("longitude"))],
    ]))
    story.append(Spacer(1, 4 * mm))

    # Description box
    story.append(Paragraph("Description:", s_label))
    desc_data = [[Paragraph(c.get("description") or "No description provided.", s_desc)]]
    desc_tbl = Table(desc_data, colWidths=[PAGE_W - 2 * MARGIN])
    desc_tbl.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), LIGHT),
        ("ROWPADDING",   (0, 0), (-1, -1), 10),
        ("LEFTPADDING",  (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("LINERIGHT",    (0, 0), (0, 0),   3, CYAN),
        ("ROUNDEDCORNERS", [4]),
    ]))
    story.append(desc_tbl)
    story.append(Spacer(1, 6 * mm))

    # ── Section: Citizen Info ─────────────────────────────────────────────────
    story.append(Paragraph("👤  Citizen Information", s_section))
    story.append(HRFlowable(width="100%", thickness=1, color=CYAN, spaceAfter=4))
    story.append(info_table([
        [lbl("Citizen ID  ⬅ Use this to file future complaints"), lbl("Full Name")],
        [val(f"#{c.get('citizen_id')}"),                          val(c.get("citizen_name"))],
        [lbl("Phone"),                lbl("Email")],
        [val(c.get("citizen_phone")), val(c.get("citizen_email"))],
        [lbl("Residential Address"),  lbl("")],
        [val(c.get("citizen_address")), val("")],
    ]))
    story.append(Spacer(1, 6 * mm))

    # ── Section: Assigned Worker ──────────────────────────────────────────────
    story.append(Paragraph("🔧  Assigned Worker", s_section))
    story.append(HRFlowable(width="100%", thickness=1, color=CYAN, spaceAfter=4))
    story.append(info_table([
        [lbl("Worker Name"),         lbl("Skill Type")],
        [val(c.get("worker_name")), val(c.get("worker_skill"))],
    ]))
    story.append(Spacer(1, 6 * mm))

    # ── Section: Audit Log ────────────────────────────────────────────────────
    story.append(Paragraph("📜  Status Change Audit Log", s_section))
    story.append(HRFlowable(width="100%", thickness=1, color=CYAN, spaceAfter=4))

    if logs:
        log_col_w = (PAGE_W - 2 * MARGIN) / 4
        log_header = [
            Paragraph("From Status", s_log_hdr),
            Paragraph("To Status",   s_log_hdr),
            Paragraph("Changed By",  s_log_hdr),
            Paragraph("Changed At",  s_log_hdr),
        ]
        log_rows = [log_header]
        for i, log in enumerate(logs):
            bg = LIGHT if i % 2 == 0 else WHITE
            log_rows.append([
                Paragraph((log.get("old_status") or "—").replace("_", " "), s_log_val),
                Paragraph((log.get("new_status") or "—").replace("_", " "), s_log_val),
                Paragraph(log.get("changed_by") or "system",               s_log_val),
                Paragraph(str(log.get("changed_at") or "—"),               s_log_val),
            ])

        log_tbl = Table(log_rows, colWidths=[log_col_w] * 4)
        log_style = [
            ("BACKGROUND",   (0, 0), (-1, 0),  SLATE),
            ("ROWPADDING",   (0, 0), (-1, -1), 6),
            ("LEFTPADDING",  (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("LINEBELOW",    (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [LIGHT, WHITE]),
            ("ROUNDEDCORNERS", [4]),
        ]
        log_tbl.setStyle(TableStyle(log_style))
        story.append(log_tbl)
    else:
        story.append(Paragraph("No status changes recorded yet.", s_desc))

    story.append(Spacer(1, 8 * mm))

    # ── Footer ────────────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.5, color=MUTED))
    story.append(Spacer(1, 3 * mm))
    generated_at = datetime.now().strftime("%d %B %Y, %I:%M %p")
    story.append(Paragraph(
        f"This is an auto-generated document by the Road Complaint Management System · Generated on {generated_at}",
        s_footer
    ))
    story.append(Paragraph(
        "Pune Municipal Corporation — complaints@pune.gov.in",
        s_footer
    ))

    # ── Build ─────────────────────────────────────────────────────────────────
    doc.build(story)
    buf.seek(0)
    return buf.read()


# ══════════════════════════════════════════════════════════════════════════════
# ANALYTICS PDF
# ══════════════════════════════════════════════════════════════════════════════

def generate_analytics_pdf() -> bytes:
    """
    Generate a styled analytics summary PDF.
    Includes:
      - Ward-wise complaint counts
      - Monthly filing trend (last 6 months)
      - Damage-type breakdown
      - Per-ward resolution rate & avg days to resolve
      - SLA breaches (open > 7 days)
    """

    # ── Colour palette ────────────────────────────────────────────────────────
    NAVY   = colors.HexColor("#0f172a")
    CYAN   = colors.HexColor("#06b6d4")
    SLATE  = colors.HexColor("#1e293b")
    LIGHT  = colors.HexColor("#f1f5f9")
    MUTED  = colors.HexColor("#64748b")
    WHITE  = colors.white
    GREEN  = colors.HexColor("#10b981")
    YELLOW = colors.HexColor("#f59e0b")
    RED    = colors.HexColor("#ef4444")
    BLUE   = colors.HexColor("#3b82f6")

    # ── Fetch data ────────────────────────────────────────────────────────────
    ward_summary = execute_query(
        """
        SELECT w.ward_name,
               COUNT(c.complaint_id)                                           AS total,
               COUNT(c.complaint_id) FILTER (WHERE c.status = 'open')         AS open,
               COUNT(c.complaint_id) FILTER (WHERE c.status = 'in_progress')  AS in_progress,
               COUNT(c.complaint_id) FILTER (WHERE c.status = 'resolved')     AS resolved
        FROM  ward w LEFT JOIN complaint c ON w.ward_id = c.ward_id
        GROUP BY w.ward_id, w.ward_name
        ORDER BY total DESC
        """,
        fetch=True
    ) or []

    monthly_trend = execute_query(
        """
        SELECT TO_CHAR(filed_at, 'YYYY-MM') AS month, COUNT(*) AS count
        FROM   complaint
        GROUP  BY TO_CHAR(filed_at, 'YYYY-MM')
        ORDER  BY month DESC
        LIMIT  6
        """,
        fetch=True
    ) or []

    damage_breakdown = execute_query(
        """
        SELECT damage_type,
               COUNT(*) AS count,
               ROUND(COUNT(*) * 100.0 / NULLIF((SELECT COUNT(*) FROM complaint), 0), 1) AS percentage
        FROM   complaint
        GROUP  BY damage_type
        ORDER  BY count DESC
        """,
        fetch=True
    ) or []

    resolution_rate = execute_query(
        """
        SELECT w.ward_name,
               COUNT(c.complaint_id)                                                AS total,
               COUNT(c.complaint_id) FILTER (WHERE c.status = 'resolved')           AS resolved_count,
               ROUND(AVG(
                 CASE WHEN c.status = 'resolved'
                      THEN EXTRACT(EPOCH FROM (c.resolved_at - c.filed_at)) / 86400.0
                 END
               )::NUMERIC, 1) AS avg_days
        FROM   complaint c
        JOIN   ward      w ON c.ward_id = w.ward_id
        GROUP  BY w.ward_name
        ORDER  BY w.ward_name
        """,
        fetch=True
    ) or []

    sla_breaches = execute_query(
        """
        SELECT c.complaint_id,
               ci.name AS citizen_name,
               w.ward_name, c.damage_type, c.severity,
               FLOOR(EXTRACT(EPOCH FROM (NOW() - c.filed_at)) / 86400)::INT AS days_pending
        FROM  complaint c
        JOIN  citizen   ci ON c.citizen_id = ci.citizen_id
        JOIN  ward      w  ON c.ward_id    = w.ward_id
        WHERE c.status <> 'resolved'
          AND (NOW() - c.filed_at) > INTERVAL '7 days'
        ORDER BY days_pending DESC
        LIMIT 20
        """,
        fetch=True
    ) or []

    # ── Build PDF ─────────────────────────────────────────────────────────────
    buf = io.BytesIO()
    PAGE_W, PAGE_H = A4
    MARGIN = 20 * mm

    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN,  bottomMargin=MARGIN,
        title="Analytics Report — Road Complaint Management System",
        author="Road Complaint Management System",
    )

    styles = getSampleStyleSheet()

    def style(name, **kw):
        return ParagraphStyle(name, parent=styles["Normal"], **kw)

    s_title   = style("ATitle",   fontSize=20, textColor=WHITE,  leading=26, alignment=TA_CENTER, fontName="Helvetica-Bold")
    s_sub     = style("ASub",     fontSize=9,  textColor=CYAN,   leading=14, alignment=TA_CENTER)
    s_section = style("ASection", fontSize=11, textColor=CYAN,   leading=16, fontName="Helvetica-Bold", spaceBefore=10)
    s_label   = style("ALabel",   fontSize=8,  textColor=MUTED,  leading=11, fontName="Helvetica-Bold")
    s_value   = style("AValue",   fontSize=9,  textColor=NAVY,   leading=13)
    s_desc    = style("ADesc",    fontSize=9,  textColor=SLATE,  leading=14)
    s_footer  = style("AFooter",  fontSize=7,  textColor=MUTED,  leading=10, alignment=TA_CENTER)
    s_hdr     = style("AHdr",     fontSize=8,  textColor=WHITE,  leading=12, fontName="Helvetica-Bold", alignment=TA_CENTER)
    s_cell    = style("ACell",    fontSize=8,  textColor=SLATE,  leading=12, alignment=TA_CENTER)
    s_alert   = style("AAlert",   fontSize=8,  textColor=WHITE,  leading=12, fontName="Helvetica-Bold", alignment=TA_CENTER)

    story = []

    # ── Header ────────────────────────────────────────────────────────────────
    hdr_data = [[Paragraph("📊  Analytics Report — Road Complaint System", s_title)]]
    hdr_tbl = Table(hdr_data, colWidths=[PAGE_W - 2 * MARGIN])
    hdr_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY),
        ("ROWPADDING", (0, 0), (-1, -1), 14),
        ("ROUNDEDCORNERS", [8]),
    ]))
    story.append(hdr_tbl)
    story.append(Spacer(1, 4 * mm))
    generated_at = datetime.now().strftime("%d %B %Y, %I:%M %p")
    story.append(Paragraph(f"Generated on {generated_at}", s_sub))
    story.append(Spacer(1, 8 * mm))

    def tbl_style(has_header=True):
        base = [
            ("ROWPADDING",   (0, 0), (-1, -1), 6),
            ("LEFTPADDING",  (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("LINEBELOW",    (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("ROWBACKGROUNDS", (0, 1 if has_header else 0), (-1, -1), [LIGHT, WHITE]),
            ("ROUNDEDCORNERS", [4]),
        ]
        if has_header:
            base.append(("BACKGROUND", (0, 0), (-1, 0), SLATE))
        return TableStyle(base)

    col_w = PAGE_W - 2 * MARGIN

    # ── 1. Ward Summary ───────────────────────────────────────────────────────
    story.append(Paragraph("🏘️  Ward-wise Complaint Summary", s_section))
    story.append(HRFlowable(width="100%", thickness=1, color=CYAN, spaceAfter=4))
    if ward_summary:
        ws_cols = [col_w * 0.34, col_w * 0.165, col_w * 0.165, col_w * 0.165, col_w * 0.165]
        ws_header = [
            Paragraph("Ward", s_hdr),
            Paragraph("Total", s_hdr),
            Paragraph("Open", s_hdr),
            Paragraph("In Progress", s_hdr),
            Paragraph("Resolved", s_hdr),
        ]
        ws_rows = [ws_header]
        for r in ward_summary:
            ws_rows.append([
                Paragraph(str(r.get("ward_name", "")), s_cell),
                Paragraph(str(r.get("total", 0)), s_cell),
                Paragraph(str(r.get("open", 0)), s_cell),
                Paragraph(str(r.get("in_progress", 0)), s_cell),
                Paragraph(str(r.get("resolved", 0)), s_cell),
            ])
        ws_tbl = Table(ws_rows, colWidths=ws_cols)
        ws_tbl.setStyle(tbl_style())
        story.append(ws_tbl)
    else:
        story.append(Paragraph("No ward data available.", s_desc))
    story.append(Spacer(1, 6 * mm))

    # ── 2. Monthly Trend ──────────────────────────────────────────────────────
    story.append(Paragraph("📅  Monthly Filing Trend (Last 6 Months)", s_section))
    story.append(HRFlowable(width="100%", thickness=1, color=CYAN, spaceAfter=4))
    if monthly_trend:
        mt_cols = [col_w * 0.5, col_w * 0.5]
        mt_rows = [[Paragraph("Month", s_hdr), Paragraph("Complaints Filed", s_hdr)]]
        for r in monthly_trend:
            mt_rows.append([
                Paragraph(str(r.get("month", "")), s_cell),
                Paragraph(str(r.get("count", 0)), s_cell),
            ])
        mt_tbl = Table(mt_rows, colWidths=mt_cols)
        mt_tbl.setStyle(tbl_style())
        story.append(mt_tbl)
    else:
        story.append(Paragraph("No trend data available.", s_desc))
    story.append(Spacer(1, 6 * mm))

    # ── 3. Damage Breakdown ───────────────────────────────────────────────────
    story.append(Paragraph("🔩  Damage Type Breakdown", s_section))
    story.append(HRFlowable(width="100%", thickness=1, color=CYAN, spaceAfter=4))
    if damage_breakdown:
        db_cols = [col_w * 0.5, col_w * 0.25, col_w * 0.25]
        db_rows = [
            [Paragraph("Damage Type", s_hdr), Paragraph("Count", s_hdr), Paragraph("% Share", s_hdr)]
        ]
        for r in damage_breakdown:
            db_rows.append([
                Paragraph((r.get("damage_type") or "").capitalize(), s_cell),
                Paragraph(str(r.get("count", 0)), s_cell),
                Paragraph(f"{r.get('percentage', 0)}%", s_cell),
            ])
        db_tbl = Table(db_rows, colWidths=db_cols)
        db_tbl.setStyle(tbl_style())
        story.append(db_tbl)
    else:
        story.append(Paragraph("No damage data available.", s_desc))
    story.append(Spacer(1, 6 * mm))

    # ── 4. Resolution Rate ────────────────────────────────────────────────────
    story.append(Paragraph("✅  Per-Ward Resolution Rate", s_section))
    story.append(HRFlowable(width="100%", thickness=1, color=CYAN, spaceAfter=4))
    if resolution_rate:
        rr_cols = [col_w * 0.34, col_w * 0.22, col_w * 0.22, col_w * 0.22]
        rr_rows = [
            [
                Paragraph("Ward", s_hdr),
                Paragraph("Total", s_hdr),
                Paragraph("Resolved", s_hdr),
                Paragraph("Avg Days", s_hdr),
            ]
        ]
        for r in resolution_rate:
            rr_rows.append([
                Paragraph(str(r.get("ward_name", "")), s_cell),
                Paragraph(str(r.get("total", 0)), s_cell),
                Paragraph(str(r.get("resolved_count", 0)), s_cell),
                Paragraph(str(r.get("avg_days") or "—"), s_cell),
            ])
        rr_tbl = Table(rr_rows, colWidths=rr_cols)
        rr_tbl.setStyle(tbl_style())
        story.append(rr_tbl)
    else:
        story.append(Paragraph("No resolution data available.", s_desc))
    story.append(Spacer(1, 6 * mm))

    # ── 5. SLA Breaches ───────────────────────────────────────────────────────
    story.append(Paragraph("⚠️  SLA Breach — Open > 7 Days", s_section))
    story.append(HRFlowable(width="100%", thickness=1, color=RED, spaceAfter=4))
    if sla_breaches:
        sla_cols = [col_w * 0.1, col_w * 0.25, col_w * 0.22, col_w * 0.2, col_w * 0.12, col_w * 0.11]
        sla_rows = [
            [
                Paragraph("ID", s_hdr),
                Paragraph("Citizen", s_hdr),
                Paragraph("Ward", s_hdr),
                Paragraph("Damage", s_hdr),
                Paragraph("Severity", s_hdr),
                Paragraph("Days", s_hdr),
            ]
        ]
        sla_style = tbl_style()
        for i, r in enumerate(sla_breaches):
            days = r.get("days_pending", 0)
            day_color = RED if days > 14 else YELLOW
            sla_rows.append([
                Paragraph(f"#{r.get('complaint_id')}", s_cell),
                Paragraph(str(r.get("citizen_name", "")), s_cell),
                Paragraph(str(r.get("ward_name", "")), s_cell),
                Paragraph((r.get("damage_type") or "").capitalize(), s_cell),
                Paragraph((r.get("severity") or "").upper(), s_cell),
                Paragraph(str(days), style(f"DayCell{i}", fontSize=8, textColor=day_color, leading=12, alignment=TA_CENTER, fontName="Helvetica-Bold")),
            ])
        sla_tbl = Table(sla_rows, colWidths=sla_cols)
        sla_tbl.setStyle(sla_style)
        story.append(sla_tbl)
    else:
        story.append(Paragraph("✅  No SLA breaches — all complaints within 7-day window!", s_desc))
    story.append(Spacer(1, 8 * mm))

    # ── Footer ────────────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.5, color=MUTED))
    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph(
        f"Auto-generated Analytics Report · Road Complaint Management System · {generated_at}",
        s_footer
    ))
    story.append(Paragraph("Pune Municipal Corporation — complaints@pune.gov.in", s_footer))

    doc.build(story)
    buf.seek(0)
    return buf.read()
