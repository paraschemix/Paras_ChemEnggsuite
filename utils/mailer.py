"""
utils/mailer.py
=================
Email dispatcher for calculation reports. Uses smtplib (stdlib) against
any standard SMTP provider (Gmail, Office365, SendGrid SMTP relay, etc.)
so no extra third-party SDK is a hard dependency. Swap the transport
function for an API-based provider (SendGrid/Resend) later by replacing
only `_send_via_smtp` — the report-building function stays the same.

SMTP credentials are read from Streamlit secrets (st.secrets), never
hardcoded. Expected secrets.toml structure:

    [smtp]
    host = "smtp.gmail.com"
    port = 587
    username = "your_email@gmail.com"
    password = "your_app_password"
    sender_name = "PetroProcess Suite"
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from typing import Dict, Any

import streamlit as st


def _build_html_report(calc_title: str, input_params: Dict[str, Any], results_dict: Dict[str, Any]) -> str:
    """Builds a clean HTML email body summarizing inputs and results."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    input_rows = "".join(
        f"<tr><td style='padding:6px 12px;color:#475569;'>{k.replace('_', ' ').title()}</td>"
        f"<td style='padding:6px 12px;font-weight:600;color:#0f172a;'>{v}</td></tr>"
        for k, v in input_params.items()
    )
    result_rows = "".join(
        f"<tr><td style='padding:6px 12px;color:#475569;'>{k.replace('_', ' ').title()}</td>"
        f"<td style='padding:6px 12px;font-weight:700;color:#1d4ed8;'>{v}</td></tr>"
        for k, v in results_dict.items()
        if v is not None
    )

    html = f"""
    <html>
    <body style="font-family: -apple-system, Segoe UI, Roboto, sans-serif; background:#f1f5f9; padding:24px;">
      <div style="max-width:600px;margin:0 auto;background:#ffffff;border-radius:10px;overflow:hidden;border:1px solid #e2e8f0;">
        <div style="background:#0f172a;color:#fff;padding:20px 24px;">
          <h2 style="margin:0;font-size:18px;">⚙️ PetroProcess Suite — Calculation Report</h2>
          <p style="margin:4px 0 0;color:#cbd5e1;font-size:13px;">{calc_title} &middot; {timestamp}</p>
        </div>
        <div style="padding:20px 24px;">
          <h3 style="font-size:14px;color:#334155;margin-bottom:8px;">Input Parameters</h3>
          <table style="width:100%;border-collapse:collapse;font-size:13px;background:#f8fafc;border-radius:6px;">
            {input_rows}
          </table>
          <h3 style="font-size:14px;color:#334155;margin:20px 0 8px;">Results</h3>
          <table style="width:100%;border-collapse:collapse;font-size:13px;background:#f0fdf4;border-radius:6px;">
            {result_rows}
          </table>
        </div>
        <div style="padding:14px 24px;background:#f8fafc;color:#94a3b8;font-size:11px;">
          Screening-level calculation for engineering estimation. Verify critical designs
          against certified engineering packages and applicable codes/standards.
        </div>
      </div>
    </body>
    </html>
    """
    return html


def _build_text_report(calc_title: str, input_params: Dict[str, Any], results_dict: Dict[str, Any]) -> str:
    """Plain-text fallback body for mail clients that don't render HTML."""
    lines = [f"PetroProcess Suite — Calculation Report", f"{calc_title}", "=" * 40, "", "INPUTS:"]
    for k, v in input_params.items():
        lines.append(f"  {k.replace('_', ' ').title()}: {v}")
    lines.append("")
    lines.append("RESULTS:")
    for k, v in results_dict.items():
        if v is not None:
            lines.append(f"  {k.replace('_', ' ').title()}: {v}")
    lines.append("")
    lines.append("Screening-level calculation for engineering estimation. Verify critical")
    lines.append("designs against certified engineering packages and applicable codes.")
    return "\n".join(lines)


def _send_via_smtp(recipient_email: str, subject: str, html_body: str, text_body: str) -> None:
    """Sends the report using SMTP credentials from st.secrets['smtp']."""
    smtp_cfg = st.secrets["smtp"]
    host = smtp_cfg["host"]
    port = int(smtp_cfg["port"])
    username = smtp_cfg["username"]
    password = smtp_cfg["password"]
    sender_name = smtp_cfg.get("sender_name", "PetroProcess Suite")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{sender_name} <{username}>"
    msg["To"] = recipient_email

    msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP(host, port, timeout=15) as server:
        server.starttls()
        server.login(username, password)
        server.sendmail(username, recipient_email, msg.as_string())


def send_calculation_email(
    recipient_email: str,
    calc_title: str,
    input_params: Dict[str, Any],
    results_dict: Dict[str, Any],
) -> tuple[bool, str]:
    """
    Sends a formatted calculation report by email.

    Returns (success: bool, message: str) — the caller (Streamlit page)
    is responsible for surfacing `message` via st.success/st.error.
    """
    if not recipient_email or "@" not in recipient_email:
        return False, "Please enter a valid email address."

    if "smtp" not in st.secrets:
        return False, (
            "Email is not configured yet. Add an [smtp] section to "
            ".streamlit/secrets.toml with host, port, username, password."
        )

    subject = f"PetroProcess Suite Report: {calc_title}"
    html_body = _build_html_report(calc_title, input_params, results_dict)
    text_body = _build_text_report(calc_title, input_params, results_dict)

    try:
        _send_via_smtp(recipient_email, subject, html_body, text_body)
        return True, f"Report sent to {recipient_email}."
    except smtplib.SMTPAuthenticationError:
        return False, "SMTP authentication failed — check username/password (use an app password for Gmail)."
    except Exception as e:
        return False, f"Failed to send email: {e}"


def render_email_widget(calc_title: str, input_params: Dict[str, Any], results_dict: Dict[str, Any], key_prefix: str) -> None:
    """
    Drop-in Streamlit UI block for any calculator page: an email input and
    "Send Report" button wired to send_calculation_email(). Call this at
    the bottom of a calculator's result section once results exist.
    """
    with st.expander("📧 Email this report"):
        email = st.text_input("Recipient email", key=f"{key_prefix}_email")
        if st.button("Send Report", key=f"{key_prefix}_send_btn"):
            with st.spinner("Sending..."):
                success, message = send_calculation_email(email, calc_title, input_params, results_dict)
            if success:
                st.success(message)
            else:
                st.error(message)
