"""
utils/report.py
=================
Generates a "Design Basis" report (CSV or PDF) from any tool's inputs
and results. Used by the "📄 Generate Design Report" button that every
dynamic tool page renders after a calculation - same pattern as
utils/mailer.py, deliberately kept generic so it works for all 50+
tools without any tool-specific code.
"""

from datetime import datetime
from typing import Dict, Any
import io

import pandas as pd
from fpdf import FPDF


def _clean_value(v: Any) -> str:
    return str(v)


def _sanitize_pdf_text(text: str) -> str:
    """
    fpdf2's base Helvetica font only supports latin-1. Tool results/
    formulas frequently contain unicode symbols (°, Δ, →, √, ², ³, α, η,
    ρ, etc.) from the engineering notation used elsewhere in the suite.
    Replace the common ones with ASCII-safe equivalents rather than
    crashing or requiring a bundled unicode font.
    """
    replacements = {
        "\u2014": "-", "\u2013": "-",       # em/en dash
        "\u2192": "->", "\u2190": "<-",     # arrows
        "\u00b0": "deg", "\u0394": "Delta", # degree, Delta
        "\u221a": "sqrt", "\u00b2": "^2", "\u00b3": "^3",
        "\u03b1": "alpha", "\u03b7": "eta", "\u03c1": "rho",
        "\u03bc": "mu", "\u03c3": "sigma", "\u2265": ">=", "\u2264": "<=",
        "\u2019": "'", "\u2018": "'", "\u201c": '"', "\u201d": '"',
        "\u2026": "...", "\u00d7": "x", "\u00b7": ".",
    }
    for uni, ascii_eq in replacements.items():
        text = text.replace(uni, ascii_eq)
    # Final safety net: drop any remaining non-latin-1 characters rather
    # than crash the whole report generation.
    return text.encode("latin-1", errors="replace").decode("latin-1")


def build_report_dataframe(calc_title: str, input_params: Dict[str, Any], results_dict: Dict[str, Any]) -> pd.DataFrame:
    """Builds a flat DataFrame combining inputs and results with a Section column."""
    rows = []
    for k, v in input_params.items():
        rows.append({"Section": "Input", "Parameter": k.replace("_", " ").title(), "Value": _clean_value(v)})
    for k, v in results_dict.items():
        if v is None or k == "_warnings":
            continue
        rows.append({"Section": "Result", "Parameter": k.replace("_", " ").title(), "Value": _clean_value(v)})
    return pd.DataFrame(rows)


def generate_csv_bytes(calc_title: str, input_params: Dict[str, Any], results_dict: Dict[str, Any]) -> bytes:
    df = build_report_dataframe(calc_title, input_params, results_dict)
    buf = io.StringIO()
    buf.write(f"# Paras Chemical Engineering Calc Suite - Design Basis Report\n")
    buf.write(f"# Tool: {calc_title}\n")
    buf.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    buf.write(f"# NOTE: Screening-level calculation for engineering estimation. "
              f"Verify against certified engineering packages and applicable codes.\n\n")
    df.to_csv(buf, index=False)
    return buf.getvalue().encode("utf-8")


def generate_pdf_bytes(calc_title: str, input_params: Dict[str, Any], results_dict: Dict[str, Any],
                        formula_note: str = "") -> bytes:
    """Builds a clean one-page PDF design basis report."""
    pdf = FPDF()
    pdf.add_page()

    # Header band
    pdf.set_fill_color(15, 23, 42)  # slate-900
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

    def _section(title: str, items: Dict[str, Any], value_color=(29, 78, 216)):
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


def render_report_widget(calc_title: str, input_params: Dict[str, Any], results_dict: Dict[str, Any],
                          key_prefix: str, formula_note: str = "") -> None:
    """
    Drop-in Streamlit UI block: two download buttons (CSV, PDF) for the
    current tool's inputs/results. Call after a calculation has produced
    results - mirrors utils.mailer.render_email_widget's pattern.
    """
    import streamlit as st

    col1, col2 = st.columns(2)
    with col1:
        csv_bytes = generate_csv_bytes(calc_title, input_params, results_dict)
        st.download_button(
            "⬇️ Download CSV", data=csv_bytes,
            file_name=f"{key_prefix}_design_basis.csv", mime="text/csv",
            key=f"{key_prefix}_csv_dl",
        )
    with col2:
        pdf_bytes = generate_pdf_bytes(calc_title, input_params, results_dict, formula_note)
        st.download_button(
            "⬇️ Download PDF", data=pdf_bytes,
            file_name=f"{key_prefix}_design_basis.pdf", mime="application/pdf",
            key=f"{key_prefix}_pdf_dl",
        )
