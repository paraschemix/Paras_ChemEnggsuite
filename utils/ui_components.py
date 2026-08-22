"""
utils/ui_components.py
========================
Consolidated UI + validation utilities. This release's file tree lists
only three files under utils/ (tool_roadmap.py, ui_components.py,
runner.py) — a deliberate slimming from the prior release's separate
styling.py / validators.py / mailer.py / report.py / unit_system.py.

Rather than silently dropping previously-verified capability (PDF/CSV
export, email reports, SI/Imperial toggle, physical-limit validation),
everything was folded into this one file. Flagged explicitly here and in
the README as a consolidation decision, not an oversight.

Sections in this file:
  1. Theme / CSS injection (teal/mint, matched to calculators.profitsfirst.in)
  2. Branding + page header helpers
  3. Global unit-system toggle (SI/Imperial)
  4. Physical-limit input validators
  5. Engineering Basis & Limitations expander
  6. CSV/PDF design-report export
  7. Email report dispatcher
"""

import io
import smtplib
from dataclasses import dataclass
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional, Any

import streamlit as st
import pandas as pd
from fpdf import FPDF


# =======================================================================
# 1. THEME / CSS — blue accent on a white background, per explicit
#    request. Previously teal/mint (matched to a reference site); this
#    supersedes that with a simpler, higher-contrast blue-on-white theme
#    used consistently across every page via the shared inject_global_css().
# =======================================================================

PRIMARY_TEAL = "#1D4ED8"        # blue-700 - headings, sidebar bg
PRIMARY_TEAL_DARK = "#1E3A8A"   # blue-900 - button hover, active states
ACCENT_MINT = "#2563EB"         # blue-600 - buttons, links, active tabs
ACCENT_MINT_LIGHT = "#DBEAFE"   # blue-100 - icon/status badge backgrounds
SLATE_BG = "#FFFFFF"            # white page background, as requested
CARD_BG = "#ffffff"
TEXT_BODY = "#334155"           # slate-700 - body text, readable on white
SUCCESS_GREEN = "#16a34a"
WARNING_AMBER = "#d97706"
ERROR_RED = "#dc2626"
CAUTION_BG = "#FFFBEB"          # amber-50 - caution banner background
CAUTION_BORDER = "#F59E0B"      # amber-500 - caution banner border
CAUTION_TEXT = "#92400E"        # amber-800 - caution banner text


def inject_global_css() -> None:
    st.markdown(
        f"""
        <style>
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        header[data-testid="stHeader"] {{background: transparent;}}
        div[data-testid="stToolbar"] {{visibility: hidden; height: 0; position: fixed;}}
        div[data-testid="stDecoration"] {{visibility: hidden; height: 0; position: fixed;}}
        div[data-testid="stStatusWidget"] {{visibility: hidden; height: 0; position: fixed;}}

        .stApp {{ background-color: {SLATE_BG}; }}
        html, body, [class*="css"] {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        }}

        .block-container {{
            padding-top: 2rem; padding-left: 3rem; padding-right: 3rem; max-width: 100%;
        }}

        section[data-testid="stSidebar"] {{ background-color: {PRIMARY_TEAL}; }}
        section[data-testid="stSidebar"] * {{ color: #e6f4f1 !important; }}
        section[data-testid="stSidebar"] input {{ color: {PRIMARY_TEAL} !important; }}

        .brand-header {{
            display: flex; align-items: center; gap: 12px;
            padding: 6px 0 14px 0; border-bottom: 1px solid rgba(255,255,255,0.15);
            margin-bottom: 14px; flex-wrap: wrap;
        }}
        .brand-logo-badge {{
            width: 40px; height: 40px; background: #ffffff; border-radius: 8px;
            display: flex; align-items: center; justify-content: center;
            font-size: 20px; font-weight: 800; color: {PRIMARY_TEAL}; flex-shrink: 0;
        }}

        h1 {{ color: {PRIMARY_TEAL}; font-weight: 800; font-size: 2rem; word-wrap: break-word; }}
        h2, h3 {{ color: {PRIMARY_TEAL}; font-weight: 700; }}
        p, .stMarkdown p {{ color: {TEXT_BODY}; }}

        div[data-testid="stMetric"] {{
            background: {CARD_BG}; border: 1px solid #e2e8f0; border-radius: 16px;
            padding: 16px 18px;
            box-shadow: 0 4px 6px -1px rgba(29, 78, 216, 0.1), 0 2px 4px -2px rgba(29, 78, 216, 0.1);
        }}
        div[data-testid="stMetricLabel"] {{ color: {TEXT_BODY} !important; font-weight: 600; font-size: 0.8rem !important; }}
        div[data-testid="stMetricValue"] {{ color: {PRIMARY_TEAL} !important; font-size: 1.4rem !important; word-break: break-word; }}

        div[data-testid="stVerticalBlockBorderWrapper"] {{
            border-radius: 16px !important; border: 1px solid #edf2f4 !important;
            box-shadow: 0 4px 6px -1px rgba(29, 78, 216, 0.1), 0 2px 4px -2px rgba(29, 78, 216, 0.1);
        }}

        .stButton > button, .stDownloadButton > button {{
            background-color: {ACCENT_MINT}; color: white; font-weight: 600;
            border-radius: 8px; border: none; padding: 0.55rem 1.2rem; width: 100%;
        }}
        .stButton > button:hover, .stDownloadButton > button:hover {{ background-color: #0d9488; color: white; }}

        div[data-baseweb="tab-list"] {{
            overflow-x: auto; overflow-y: hidden; flex-wrap: nowrap !important;
            scrollbar-width: thin; -webkit-overflow-scrolling: touch;
        }}
        button[data-baseweb="tab"] {{ font-weight: 600; color: {TEXT_BODY}; white-space: nowrap; flex-shrink: 0; }}
        button[data-baseweb="tab"][aria-selected="true"] {{ color: {ACCENT_MINT}; }}
        div[data-baseweb="tab-highlight"] {{ background-color: {ACCENT_MINT} !important; }}

        details {{ background: {CARD_BG}; border: 1px solid #e2e8f0; border-radius: 12px; }}
        summary {{ font-weight: 600; color: {PRIMARY_TEAL}; }}

        [data-testid="stTable"] {{ border-radius: 12px; overflow-x: auto; display: block; }}

        .status-live {{
            background: {ACCENT_MINT_LIGHT}; color: #1E3A8A; font-size: 0.7rem; font-weight: 700;
            padding: 2px 8px; border-radius: 9999px; display: inline-block;
        }}
        .status-soon {{
            background: #f1f5f9; color: #64748b; font-size: 0.7rem; font-weight: 700;
            padding: 2px 8px; border-radius: 9999px; display: inline-block;
        }}

        /* ---------- Caution banner (validation-required notice) ---------- */
        .caution-banner {{
            background: {CAUTION_BG}; border: 1px solid {CAUTION_BORDER}; border-left: 4px solid {CAUTION_BORDER};
            border-radius: 8px; padding: 10px 14px; margin: 10px 0; color: {CAUTION_TEXT};
            font-size: 0.85rem; font-weight: 500;
        }}

        /* ---------- Cross-page navigation footer ---------- */
        .page-nav-footer {{
            margin-top: 24px; padding-top: 16px; border-top: 1px solid #e2e8f0;
        }}

        @media (max-width: 768px) {{
            .block-container {{ padding-top: 1rem; padding-left: 1rem; padding-right: 1rem; padding-bottom: 2rem; }}
            h1 {{ font-size: 1.5rem; }} h2 {{ font-size: 1.15rem; }} h3 {{ font-size: 1rem; }}
            div[data-testid="stHorizontalBlock"] {{ flex-direction: column !important; }}
            div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {{
                width: 100% !important; flex: 1 1 100% !important; min-width: 100% !important; margin-bottom: 0.5rem;
            }}
            div[data-testid="stMetric"] {{ padding: 12px 14px; }}
            div[data-testid="stMetricValue"] {{ font-size: 1.2rem !important; }}
            .brand-header {{ gap: 8px; padding: 4px 0 10px 0; }}
            .brand-logo-badge {{ width: 34px; height: 34px; font-size: 16px; }}
            .stButton > button, .stDownloadButton > button {{ padding: 0.6rem 1rem; font-size: 0.9rem; }}
            input, select, textarea {{ font-size: 16px !important; }}
            section[data-testid="stSidebar"] {{ min-width: 100% !important; max-width: 100% !important; }}
            section[data-testid="stSidebar"] .block-container {{ padding-left: 1rem; padding-right: 1rem; }}
        }}

        @media (max-width: 480px) {{
            .block-container {{ padding-left: 0.75rem; padding-right: 0.75rem; }}
            h1 {{ font-size: 1.25rem; }}
            div[data-testid="stMetric"] {{ padding: 10px 12px; border-radius: 12px; }}
            div[data-testid="stMetricLabel"] {{ font-size: 0.72rem !important; }}
            div[data-testid="stMetricValue"] {{ font-size: 1.05rem !important; }}
            button[data-baseweb="tab"] {{ font-size: 0.8rem; padding: 8px 10px; }}
            .status-live, .status-soon {{ font-size: 0.62rem; padding: 1px 6px; }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# =======================================================================
# 2. BRANDING + PAGE HEADER HELPERS
# =======================================================================

def render_brand_header(compact: bool = False) -> None:
    target = st.sidebar if compact else st
    title_color = "#e6f4f1" if compact else PRIMARY_TEAL
    subtitle_color = "#a8d9d1" if compact else TEXT_BODY
    target.markdown(
        f"""
        <div class="brand-header">
            <div class="brand-logo-badge">P</div>
            <div>
                <div style="font-weight:800;font-size:{'0.95rem' if compact else '1.4rem'};color:{title_color};">
                    Paras Chemical Engineering
                </div>
                <div style="font-size:0.75rem;color:{subtitle_color};">
                    Calc Suite &middot; Enterprise Edition
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_page_header(title: str, subtitle: str = "") -> None:
    st.markdown(
        f"""
        <div style="padding:4px 0 12px 0;">
            <h1 style="margin-bottom:2px;">{title}</h1>
            <p style="color:{TEXT_BODY};font-size:0.95rem;margin-top:0;">{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_caution_banner(custom_message: str = "") -> None:
    """
    Prominent validation-required notice, rendered for every tool via
    utils/runner.py so it appears consistently across all 12 domains
    without each page needing to remember to add it.
    """
    message = custom_message or (
        "⚠️ <strong>Screening-level engineering tool — validate before use.</strong> "
        "Results are for early-stage estimation only. Verify against certified engineering "
        "packages, applicable codes/standards, and vendor data before using in safety, "
        "regulatory, or capital-commitment decisions."
    )
    st.markdown(f'<div class="caution-banner">{message}</div>', unsafe_allow_html=True)


def render_domain_footer_nav(current_page_path: str = "") -> None:
    """
    Cross-page navigation footer: links to Home plus every other domain
    page, so no domain is a dead end. Rendered once per page via
    utils/runner.py's render_domain_page() — every page gets this
    automatically, no per-page edits needed beyond passing the page's
    own path so it can exclude itself from the list.
    """
    from utils.tool_roadmap import DOMAIN_PAGES  # local import avoids a circular import at module load time

    st.markdown('<div class="page-nav-footer">', unsafe_allow_html=True)
    st.markdown("##### 🔗 Explore other domains")

    other_pages = [(label, path) for label, path in DOMAIN_PAGES if path != current_page_path]
    nav_cols = st.columns(4)
    for i, (label, path) in enumerate(other_pages):
        with nav_cols[i % 4]:
            st.page_link(path, label=label, use_container_width=True)

    st.page_link("app.py", label="🏠 Home", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)


# =======================================================================
# 3. GLOBAL UNIT SYSTEM TOGGLE (SI / Imperial)
# =======================================================================

SI = "SI"
IMPERIAL = "Imperial"


def get_unit_system() -> str:
    if "unit_system" not in st.session_state:
        st.session_state["unit_system"] = SI
    return st.session_state["unit_system"]


def render_unit_toggle() -> None:
    st.sidebar.markdown("### 🌐 Unit System")
    current = get_unit_system()
    choice = st.sidebar.radio(
        "Unit System", options=[SI, IMPERIAL], index=[SI, IMPERIAL].index(current),
        horizontal=True, label_visibility="collapsed", key="unit_system_radio",
    )
    st.session_state["unit_system"] = choice


# =======================================================================
# 4. PHYSICAL-LIMIT INPUT VALIDATORS
# =======================================================================

@dataclass
class ValidationResult:
    is_valid: bool
    severity: str
    message: Optional[str] = None


def check_positive(value: float, name: str) -> ValidationResult:
    if value <= 0:
        return ValidationResult(False, "error", f"{name} must be greater than zero (got {value}).")
    return ValidationResult(True, "warning", None)


def check_non_negative(value: float, name: str) -> ValidationResult:
    if value < 0:
        return ValidationResult(False, "error", f"{name} cannot be negative (got {value}).")
    return ValidationResult(True, "warning", None)


def check_fraction_0_1(value: float, name: str) -> ValidationResult:
    if not (0 <= value <= 1):
        return ValidationResult(False, "error", f"{name} must be between 0 and 1 (got {value}).")
    return ValidationResult(True, "warning", None)


def check_pressure_drop(p1: float, p2: float, label: str = "pressure") -> ValidationResult:
    if p2 >= p1:
        return ValidationResult(False, "error", f"Downstream {label} ({p2}) must be less than upstream {label} ({p1}).")
    return ValidationResult(True, "warning", None)


def check_specific_gravity(sg: float) -> ValidationResult:
    if sg <= 0:
        return ValidationResult(False, "error", f"Specific gravity must be positive (got {sg}).")
    if sg > 3.0:
        return ValidationResult(True, "warning", f"SG = {sg} is unusually high - confirm this isn't a density value entered by mistake.")
    return ValidationResult(True, "warning", None)


def check_reynolds_regime(re: float) -> str:
    if re < 2300:
        return "Laminar"
    elif re < 4000:
        return "Transitional"
    return "Turbulent"


def run_validators(*results: ValidationResult):
    errors = [r.message for r in results if not r.is_valid and r.message]
    warnings = [r.message for r in results if r.is_valid and r.severity == "warning" and r.message]
    return len(errors) > 0, len(warnings) > 0, errors, warnings


# =======================================================================
# 5. ENGINEERING BASIS & LIMITATIONS EXPANDER
# =======================================================================

def render_engineering_basis(formula_md: str, references: list[str], assumptions: list[str]) -> None:
    with st.expander("📚 Engineering Basis & Limitations"):
        st.markdown("**Governing Formula(s):**")
        st.markdown(formula_md)
        st.markdown("**Standard References:**")
        for ref in references:
            st.markdown(f"- {ref}")
        st.markdown("**Assumptions & Limitations:**")
        for a in assumptions:
            st.markdown(f"- {a}")


# =======================================================================
# 6. CSV / PDF DESIGN-REPORT EXPORT
# =======================================================================

def _sanitize_pdf_text(text: str) -> str:
    """fpdf2's base Helvetica font is latin-1 only; the suite's formulas
    use unicode symbols throughout, so sanitize before writing to PDF."""
    replacements = {
        "\u2014": "-", "\u2013": "-", "\u2192": "->", "\u2190": "<-",
        "\u00b0": "deg", "\u0394": "Delta", "\u221a": "sqrt", "\u00b2": "^2", "\u00b3": "^3",
        "\u03b1": "alpha", "\u03b7": "eta", "\u03c1": "rho", "\u03bc": "mu", "\u03c3": "sigma",
        "\u2265": ">=", "\u2264": "<=", "\u2019": "'", "\u2018": "'", "\u201c": '"', "\u201d": '"',
        "\u2026": "...", "\u00d7": "x", "\u00b7": ".",
    }
    for uni, ascii_eq in replacements.items():
        text = text.replace(uni, ascii_eq)
    return text.encode("latin-1", errors="replace").decode("latin-1")


def _build_report_dataframe(input_params: dict, results_dict: dict) -> pd.DataFrame:
    rows = []
    for k, v in input_params.items():
        rows.append({"Section": "Input", "Parameter": str(k).replace("_", " ").title(), "Value": str(v)})
    for k, v in results_dict.items():
        if v is None or k == "_warnings":
            continue
        rows.append({"Section": "Result", "Parameter": str(k).replace("_", " ").title(), "Value": str(v)})
    return pd.DataFrame(rows)


def generate_csv_bytes(calc_title: str, input_params: dict, results_dict: dict) -> bytes:
    df = _build_report_dataframe(input_params, results_dict)
    buf = io.StringIO()
    buf.write("# Paras Chemical Engineering Calc Suite - Design Basis Report\n")
    buf.write(f"# Tool: {calc_title}\n")
    buf.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    buf.write("# NOTE: Screening-level calculation for engineering estimation. "
               "Verify against certified engineering packages and applicable codes.\n\n")
    df.to_csv(buf, index=False)
    return buf.getvalue().encode("utf-8")


def generate_pdf_bytes(calc_title: str, input_params: dict, results_dict: dict, formula_note: str = "") -> bytes:
    pdf = FPDF()
    pdf.add_page()

    pdf.set_fill_color(29, 78, 216)  # PRIMARY_TEAL (blue-700) as RGB
    pdf.rect(0, 0, 210, 26, style="F")
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_xy(10, 6)
    pdf.cell(0, 8, _sanitize_pdf_text("Paras Chemical Engineering Calc Suite"), ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_xy(10, 15)
    pdf.cell(0, 6, _sanitize_pdf_text(f"Design Basis Report - {calc_title}"), ln=True)

    pdf.set_text_color(30, 41, 59)
    pdf.set_xy(10, 30)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 6, _sanitize_pdf_text(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"), ln=True)
    pdf.ln(4)

    def _section(title: str, items: dict, value_color=(29, 78, 216)):
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(30, 41, 59)
        pdf.cell(0, 8, _sanitize_pdf_text(title), ln=True)
        pdf.set_draw_color(226, 232, 240)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(2)
        pdf.set_font("Helvetica", "", 10)
        for k, v in items.items():
            if v is None or k == "_warnings":
                continue
            pdf.set_text_color(71, 85, 105)
            pdf.cell(90, 7, _sanitize_pdf_text(str(k).replace("_", " ").title()), border=0)
            pdf.set_text_color(*value_color)
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(0, 7, _sanitize_pdf_text(str(v)), ln=True)
            pdf.set_font("Helvetica", "", 10)
        pdf.ln(4)

    _section("Input Parameters", input_params, value_color=(15, 23, 42))
    _section("Results", results_dict, value_color=(29, 78, 216))

    warnings = results_dict.get("_warnings") or []
    if warnings:
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(153, 27, 27)
        pdf.cell(0, 8, _sanitize_pdf_text("Warnings"), ln=True)
        pdf.set_font("Helvetica", "", 9)
        for w in warnings:
            pdf.multi_cell(0, 5, _sanitize_pdf_text(f"- {w}"))
        pdf.ln(2)

    if formula_note:
        pdf.set_font("Helvetica", "I", 8)
        pdf.set_text_color(100, 116, 139)
        pdf.multi_cell(0, 5, _sanitize_pdf_text(formula_note))

    pdf.ln(6)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(148, 163, 184)
    pdf.multi_cell(
        0, 5,
        "Screening-level calculation for engineering estimation. Verify critical designs "
        "against certified engineering packages and applicable codes/standards."
    )

    return bytes(pdf.output())


def render_report_widget(calc_title: str, input_params: dict, results_dict: dict, key_prefix: str, formula_note: str = "") -> None:
    col1, col2 = st.columns(2)
    with col1:
        csv_bytes = generate_csv_bytes(calc_title, input_params, results_dict)
        st.download_button("⬇️ Download CSV", data=csv_bytes, file_name=f"{key_prefix}_design_basis.csv",
                            mime="text/csv", key=f"{key_prefix}_csv_dl")
    with col2:
        pdf_bytes = generate_pdf_bytes(calc_title, input_params, results_dict, formula_note)
        st.download_button("⬇️ Download PDF", data=pdf_bytes, file_name=f"{key_prefix}_design_basis.pdf",
                            mime="application/pdf", key=f"{key_prefix}_pdf_dl")


# =======================================================================
# 7. EMAIL REPORT DISPATCHER
# =======================================================================

def _build_html_report(calc_title: str, input_params: dict, results_dict: dict) -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    input_rows = "".join(
        f"<tr><td style='padding:6px 12px;color:#475569;'>{str(k).replace('_',' ').title()}</td>"
        f"<td style='padding:6px 12px;font-weight:600;color:#0f172a;'>{v}</td></tr>"
        for k, v in input_params.items()
    )
    result_rows = "".join(
        f"<tr><td style='padding:6px 12px;color:#475569;'>{str(k).replace('_',' ').title()}</td>"
        f"<td style='padding:6px 12px;font-weight:700;color:#1D4ED8;'>{v}</td></tr>"
        for k, v in results_dict.items() if v is not None and k != "_warnings"
    )
    return f"""
    <html><body style="font-family:-apple-system,Segoe UI,Roboto,sans-serif;background:#f1f5f9;padding:24px;">
      <div style="max-width:600px;margin:0 auto;background:#fff;border-radius:10px;overflow:hidden;border:1px solid #e2e8f0;">
        <div style="background:#1D4ED8;color:#fff;padding:20px 24px;">
          <h2 style="margin:0;font-size:18px;">Paras Chemical Engineering Calc Suite</h2>
          <p style="margin:4px 0 0;color:#cbd5e1;font-size:13px;">{calc_title} - {timestamp}</p>
        </div>
        <div style="padding:20px 24px;">
          <h3 style="font-size:14px;color:#334155;margin-bottom:8px;">Input Parameters</h3>
          <table style="width:100%;border-collapse:collapse;font-size:13px;background:#f8fafc;border-radius:6px;">{input_rows}</table>
          <h3 style="font-size:14px;color:#334155;margin:20px 0 8px;">Results</h3>
          <table style="width:100%;border-collapse:collapse;font-size:13px;background:#f0fdf4;border-radius:6px;">{result_rows}</table>
        </div>
        <div style="padding:14px 24px;background:#f8fafc;color:#94a3b8;font-size:11px;">
          Screening-level calculation for engineering estimation. Verify critical designs
          against certified engineering packages and applicable codes/standards.
        </div>
      </div>
    </body></html>
    """


def _build_text_report(calc_title: str, input_params: dict, results_dict: dict) -> str:
    lines = [f"Paras Chemical Engineering Calc Suite - {calc_title}", "=" * 40, "", "INPUTS:"]
    for k, v in input_params.items():
        lines.append(f"  {str(k).replace('_',' ').title()}: {v}")
    lines.append(""); lines.append("RESULTS:")
    for k, v in results_dict.items():
        if v is not None and k != "_warnings":
            lines.append(f"  {str(k).replace('_',' ').title()}: {v}")
    lines.append("")
    lines.append("Screening-level calculation for engineering estimation. Verify critical")
    lines.append("designs against certified engineering packages and applicable codes.")
    return "\n".join(lines)


def send_calculation_email(recipient_email: str, calc_title: str, input_params: dict, results_dict: dict):
    if not recipient_email or "@" not in recipient_email:
        return False, "Please enter a valid email address."
    if "smtp" not in st.secrets:
        return False, "Email is not configured yet. Add an [smtp] section to .streamlit/secrets.toml."

    smtp_cfg = st.secrets["smtp"]
    subject = f"PetroProcess Suite Report: {calc_title}"
    html_body = _build_html_report(calc_title, input_params, results_dict)
    text_body = _build_text_report(calc_title, input_params, results_dict)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{smtp_cfg.get('sender_name', 'PetroProcess Suite')} <{smtp_cfg['username']}>"
    msg["To"] = recipient_email
    msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(smtp_cfg["host"], int(smtp_cfg["port"]), timeout=15) as server:
            server.starttls()
            server.login(smtp_cfg["username"], smtp_cfg["password"])
            server.sendmail(smtp_cfg["username"], recipient_email, msg.as_string())
        return True, f"Report sent to {recipient_email}."
    except smtplib.SMTPAuthenticationError:
        return False, "SMTP authentication failed - check username/password."
    except Exception as e:
        return False, f"Failed to send email: {e}"


def render_email_widget(calc_title: str, input_params: dict, results_dict: dict, key_prefix: str) -> None:
    with st.expander("📧 Email this report"):
        email = st.text_input("Recipient email", key=f"{key_prefix}_email")
        if st.button("Send Report", key=f"{key_prefix}_send_btn"):
            with st.spinner("Sending..."):
                success, message = send_calculation_email(email, calc_title, input_params, results_dict)
            if success:
                st.success(message)
            else:
                st.error(message)
