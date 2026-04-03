"""
notifications.py — Email Notifications via Gmail SMTP
Road Complaint Management System

Requires .env with EMAIL_USER and EMAIL_PASS (Gmail App Password).
"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

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
        msg            = MIMEMultipart("alternative")
        msg["Subject"] = f"Your Complaint #{complaint_id} Status Updated — {new_status.replace('_', ' ').title()}"
        msg["From"]    = EMAIL_USER
        msg["To"]      = to_email
        msg.attach(MIMEText(html_body, "html"))

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
