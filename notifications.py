"""
notifications.py — Email Notifications via Gmail SMTP
Road Complaint Management System

Requires .env with EMAIL_USER and EMAIL_PASS (Gmail App Password).
"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

from dotenv import load_dotenv

from database import execute_query

load_dotenv()

EMAIL_USER = os.getenv("EMAIL_USER", "")
EMAIL_PASS = os.getenv("EMAIL_PASS", "")

# Colour map for status badges in email
STATUS_COLORS = {
    "open":        "#ef4444",
    "in_progress": "#f59e0b",
    "resolved":    "#22c55e",
}


def log_notification(complaint_id: int, citizen_id: int, message: str) -> int:
    """
    INSERT a new row into the NOTIFICATION table and return its notification_id.
    is_sent is set to FALSE; it will be updated to TRUE after email sends.
    """
    notification_id = execute_query(
        """
        INSERT INTO notification (complaint_id, citizen_id, message, is_sent)
        VALUES (%s, %s, %s, FALSE)
        RETURNING notification_id
        """,
        (complaint_id, citizen_id, message)
    )
    return notification_id


def send_status_email(
    to_email: str,
    citizen_name: str,
    complaint_id: int,
    old_status: str,
    new_status: str,
):
    """
    Send an HTML status-change email to the citizen using Gmail SMTP (port 587, STARTTLS).
    Attaches the complaint PDF report as a file.
    Silently skips if EMAIL_USER / EMAIL_PASS are not configured.
    """
    if not EMAIL_USER or not EMAIL_PASS:
        print("[NOTIFICATION] Email credentials not set — skipping email send.")
        return

    old_color = STATUS_COLORS.get(old_status, "#6b7280")
    new_color = STATUS_COLORS.get(new_status, "#6b7280")

    resolved_note = (
        "<p style='color:#22c55e;font-weight:700;'>✅ Great news! Your complaint has been resolved. "
        "Thank you for reporting it.</p>"
        if new_status == "resolved" else ""
    )

    html_body = f"""
    <html>
    <body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;color:#1f2937;">
      <div style="background:linear-gradient(135deg,#0d47a1,#1a73e8);padding:28px;border-radius:10px 10px 0 0;">
        <h2 style="color:#fff;margin:0;font-size:22px;">🛣️ Road Complaint Update</h2>
        <p style="color:rgba(255,255,255,.8);margin:6px 0 0;">Pune Municipal Corporation</p>
      </div>
      <div style="padding:28px;background:#f9fafb;border:1px solid #e5e7eb;">
        <p>Dear <strong>{citizen_name}</strong>,</p>
        <p>Your road damage complaint <strong>#{complaint_id}</strong> has been updated by our team.</p>
        <div style="display:flex;align-items:center;gap:12px;margin:24px 0;flex-wrap:wrap;">
          <span style="background:{old_color};color:#fff;padding:8px 20px;border-radius:999px;font-size:14px;font-weight:600;">
            {old_status.replace('_', ' ').title()}
          </span>
          <span style="font-size:22px;color:#6b7280;">→</span>
          <span style="background:{new_color};color:#fff;padding:8px 20px;border-radius:999px;font-size:14px;font-weight:600;">
            {new_status.replace('_', ' ').title()}
          </span>
        </div>
        {resolved_note}
        <p style="color:#6b7280;font-size:13px;">
          📎 Your complaint report is attached as a PDF for your records.
        </p>
        <p style="color:#6b7280;font-size:13px;">
          If you have further concerns, please file a new complaint or contact your ward office.
        </p>
      </div>
      <div style="background:#374151;padding:16px;border-radius:0 0 10px 10px;text-align:center;">
        <p style="color:#d1d5db;font-size:12px;margin:0;">
          Road Complaint Management System · Pune Municipal Corporation<br/>
          This is an automated message — please do not reply.
        </p>
      </div>
    </body>
    </html>
    """

    try:
        msg            = MIMEMultipart("mixed")
        msg["Subject"] = f"Your Complaint #{complaint_id} Status Updated — {new_status.replace('_', ' ').title()}"
        msg["From"]    = EMAIL_USER
        msg["To"]      = to_email

        # Attach the HTML body
        msg.attach(MIMEText(html_body, "html"))

        # ── Generate and attach the PDF report ────────────────────────────────
        try:
            from pdf_report import generate_complaint_pdf
            pdf_bytes = generate_complaint_pdf(complaint_id)
            if pdf_bytes:
                pdf_part = MIMEBase("application", "pdf")
                pdf_part.set_payload(pdf_bytes)
                encoders.encode_base64(pdf_part)
                pdf_part.add_header(
                    "Content-Disposition",
                    f'attachment; filename="complaint_report_{complaint_id}.pdf"'
                )
                msg.attach(pdf_part)
                print(f"[NOTIFICATION] 📎 PDF report attached for complaint #{complaint_id}")
            else:
                print(f"[NOTIFICATION] ⚠️ Could not generate PDF for complaint #{complaint_id} — sending without attachment")
        except Exception as pdf_err:
            print(f"[NOTIFICATION] ⚠️ PDF generation failed: {pdf_err} — sending email without attachment")

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.ehlo()
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASS)
            server.sendmail(EMAIL_USER, to_email, msg.as_string())

        print(f"[NOTIFICATION] ✅ Email sent → {to_email} for complaint #{complaint_id}")

    except Exception as e:
        print(f"[NOTIFICATION] ❌ Email failed for complaint #{complaint_id}: {e}")


def send_notification_background(
    complaint_id: int,
    citizen_id: int,
    to_email: str,
    citizen_name: str,
    old_status: str,
    new_status: str,
):
    """
    Background task: log notification record, send email, then mark as sent.
    Called via FastAPI BackgroundTasks so the API response is not blocked.
    """
    # 1. Log the notification (is_sent = FALSE)
    notification_id = log_notification(
        complaint_id, citizen_id,
        f"Status changed from '{old_status}' to '{new_status}'"
    )

    # 2. Send the email
    if to_email:
        send_status_email(to_email, citizen_name, complaint_id, old_status, new_status)

    # 3. Mark as sent in the notification table
    execute_query(
        "UPDATE notification SET is_sent = TRUE WHERE notification_id = %s",
        (notification_id,)
    )


def send_complaint_filed_email(
    to_email: str,
    citizen_name: str,
    complaint_id: int,
    damage_type: str,
    severity: str,
    address: str,
    ward_name: str,
):
    """
    Send a confirmation email when a citizen files a new complaint.
    Attaches the complaint PDF report.
    Silently skips if EMAIL_USER / EMAIL_PASS are not configured.
    """
    if not EMAIL_USER or not EMAIL_PASS:
        print("[NOTIFICATION] Email credentials not set — skipping filed-email send.")
        return

    severity_colors = {"low": "#3b82f6", "medium": "#f59e0b", "critical": "#ef4444"}
    sev_color = severity_colors.get(severity, "#6b7280")

    html_body = f"""
    <html>
    <body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;color:#1f2937;">
      <div style="background:linear-gradient(135deg,#0d47a1,#1a73e8);padding:28px;border-radius:10px 10px 0 0;">
        <h2 style="color:#fff;margin:0;font-size:22px;">🛣️ Complaint Registered Successfully</h2>
        <p style="color:rgba(255,255,255,.8);margin:6px 0 0;">Pune Municipal Corporation</p>
      </div>
      <div style="padding:28px;background:#f9fafb;border:1px solid #e5e7eb;">
        <p>Dear <strong>{citizen_name}</strong>,</p>
        <p>Thank you for reporting a road issue. Your complaint has been <strong>registered successfully</strong> and assigned the following ID:</p>

        <div style="text-align:center;margin:24px 0;">
          <span style="background:linear-gradient(135deg,#06b6d4,#3b82f6);color:#fff;padding:12px 32px;border-radius:999px;font-size:18px;font-weight:700;letter-spacing:.5px;">
            Complaint #{complaint_id}
          </span>
        </div>

        <table style="width:100%;border-collapse:collapse;margin:20px 0;">
          <tr>
            <td style="padding:10px 14px;background:#f1f5f9;border:1px solid #e5e7eb;font-weight:600;color:#64748b;width:40%;">Damage Type</td>
            <td style="padding:10px 14px;border:1px solid #e5e7eb;">{damage_type.replace('_', ' ').title()}</td>
          </tr>
          <tr>
            <td style="padding:10px 14px;background:#f1f5f9;border:1px solid #e5e7eb;font-weight:600;color:#64748b;">Severity</td>
            <td style="padding:10px 14px;border:1px solid #e5e7eb;">
              <span style="background:{sev_color};color:#fff;padding:4px 14px;border-radius:999px;font-size:13px;font-weight:600;">{severity.upper()}</span>
            </td>
          </tr>
          <tr>
            <td style="padding:10px 14px;background:#f1f5f9;border:1px solid #e5e7eb;font-weight:600;color:#64748b;">Location</td>
            <td style="padding:10px 14px;border:1px solid #e5e7eb;">{address}</td>
          </tr>
          <tr>
            <td style="padding:10px 14px;background:#f1f5f9;border:1px solid #e5e7eb;font-weight:600;color:#64748b;">Ward</td>
            <td style="padding:10px 14px;border:1px solid #e5e7eb;">{ward_name}</td>
          </tr>
          <tr>
            <td style="padding:10px 14px;background:#f1f5f9;border:1px solid #e5e7eb;font-weight:600;color:#64748b;">Status</td>
            <td style="padding:10px 14px;border:1px solid #e5e7eb;">
              <span style="background:#f59e0b;color:#fff;padding:4px 14px;border-radius:999px;font-size:13px;font-weight:600;">OPEN</span>
            </td>
          </tr>
        </table>

        <p style="color:#1f2937;font-size:14px;">
          <strong>What happens next?</strong><br/>
          Our team will review your complaint and assign a worker. You will receive email updates when the status changes.
        </p>

        <p style="color:#6b7280;font-size:13px;">
          📎 Your complaint report is attached as a PDF for your records.
        </p>
      </div>
      <div style="background:#374151;padding:16px;border-radius:0 0 10px 10px;text-align:center;">
        <p style="color:#d1d5db;font-size:12px;margin:0;">
          Road Complaint Management System · Pune Municipal Corporation<br/>
          This is an automated message — please do not reply.
        </p>
      </div>
    </body>
    </html>
    """

    try:
        msg            = MIMEMultipart("mixed")
        msg["Subject"] = f"Complaint #{complaint_id} Registered — {damage_type.replace('_', ' ').title()} at {ward_name}"
        msg["From"]    = EMAIL_USER
        msg["To"]      = to_email

        # Attach the HTML body
        msg.attach(MIMEText(html_body, "html"))

        # ── Generate and attach the PDF report ────────────────────────────────
        try:
            from pdf_report import generate_complaint_pdf
            pdf_bytes = generate_complaint_pdf(complaint_id)
            if pdf_bytes:
                pdf_part = MIMEBase("application", "pdf")
                pdf_part.set_payload(pdf_bytes)
                encoders.encode_base64(pdf_part)
                pdf_part.add_header(
                    "Content-Disposition",
                    f'attachment; filename="complaint_report_{complaint_id}.pdf"'
                )
                msg.attach(pdf_part)
                print(f"[NOTIFICATION] 📎 PDF report attached for new complaint #{complaint_id}")
            else:
                print(f"[NOTIFICATION] ⚠️ Could not generate PDF for complaint #{complaint_id}")
        except Exception as pdf_err:
            print(f"[NOTIFICATION] ⚠️ PDF generation failed: {pdf_err}")

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.ehlo()
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASS)
            server.sendmail(EMAIL_USER, to_email, msg.as_string())

        print(f"[NOTIFICATION] ✅ Filed-email sent → {to_email} for complaint #{complaint_id}")

    except Exception as e:
        print(f"[NOTIFICATION] ❌ Filed-email failed for complaint #{complaint_id}: {e}")


def send_filed_notification_background(
    complaint_id: int,
    citizen_id: int,
    to_email: str,
    citizen_name: str,
    damage_type: str,
    severity: str,
    address: str,
    ward_name: str,
):
    """
    Background task: log notification + send confirmation email when complaint is filed.
    Called via FastAPI BackgroundTasks so the API response is not blocked.
    """
    # 1. Log the notification
    notification_id = log_notification(
        complaint_id, citizen_id,
        f"Complaint #{complaint_id} registered successfully — {damage_type} ({severity}) at {address}"
    )

    # 2. Send the email
    if to_email:
        send_complaint_filed_email(
            to_email, citizen_name, complaint_id,
            damage_type, severity, address, ward_name
        )

    # 3. Mark as sent
    execute_query(
        "UPDATE notification SET is_sent = TRUE WHERE notification_id = %s",
        (notification_id,)
    )
