"""
utils/styling.py
==================
Injects a clean, enterprise-grade CSS theme (slate grey / navy blue
accents, HYSYS-like professional feel) into every Streamlit page. Call
`inject_global_css()` once near the top of every page after
`st.set_page_config(...)`.
"""

import streamlit as st


PRIMARY_NAVY = "#1e3a5f"
ACCENT_BLUE = "#2563eb"
SLATE_BG = "#f1f5f9"
SLATE_DARK = "#0f172a"
SUCCESS_GREEN = "#16a34a"
WARNING_AMBER = "#d97706"
ERROR_RED = "#dc2626"


def inject_global_css() -> None:
    st.markdown(
        f"""
        <style>
        /* ---------- App background & base typography ---------- */
        .stApp {{
            background-color: {SLATE_BG};
        }}
        html, body, [class*="css"] {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        }}

        /* ---------- Sidebar ---------- */
        section[data-testid="stSidebar"] {{
            background-color: {SLATE_DARK};
        }}
        section[data-testid="stSidebar"] * {{
            color: #e2e8f0 !important;
        }}
        section[data-testid="stSidebar"] input {{
            color: #0f172a !important;
        }}

        /* ---------- Headers ---------- */
        h1 {{
            color: {PRIMARY_NAVY};
            font-weight: 800;
            border-bottom: 3px solid {ACCENT_BLUE};
            padding-bottom: 0.4rem;
        }}
        h2, h3 {{
            color: {PRIMARY_NAVY};
            font-weight: 700;
        }}

        /* ---------- Metric cards ---------- */
        div[data-testid="stMetric"] {{
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-left: 4px solid {ACCENT_BLUE};
            border-radius: 8px;
            padding: 14px 16px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        }}
        div[data-testid="stMetricLabel"] {{
            color: #64748b !important;
            font-weight: 600;
        }}
        div[data-testid="stMetricValue"] {{
            color: {PRIMARY_NAVY} !important;
        }}

        /* ---------- Buttons ---------- */
        .stButton > button {{
            background-color: {ACCENT_BLUE};
            color: white;
            font-weight: 600;
            border-radius: 6px;
            border: none;
            padding: 0.5rem 1.2rem;
        }}
        .stButton > button:hover {{
            background-color: {PRIMARY_NAVY};
            color: white;
        }}

        /* ---------- Expanders (Engineering Basis panels) ---------- */
        details {{
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
        }}
        summary {{
            font-weight: 600;
            color: {PRIMARY_NAVY};
        }}

        /* ---------- Cards / containers ---------- */
        div[data-testid="stVerticalBlockBorderWrapper"] {{
            border-radius: 10px;
        }}

        /* ---------- Dataframes / tables ---------- */
        [data-testid="stTable"] {{
            border-radius: 8px;
            overflow: hidden;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_page_header(title: str, subtitle: str = "") -> None:
    """Consistent page header block used across all domain pages."""
    st.markdown(
        f"""
        <div style="padding:4px 0 12px 0;">
            <h1 style="margin-bottom:2px;">{title}</h1>
            <p style="color:#64748b;font-size:0.95rem;margin-top:0;">{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_engineering_basis(formula_md: str, references: list[str], assumptions: list[str]) -> None:
    """
    Standardized "📚 Engineering Basis & Limitations" expander used by
    every calculator. Pass the formula as a Markdown string (LaTeX via
    $...$ is supported by st.markdown), plus lists of reference standards
    and stated assumptions/limitations.
    """
    with st.expander("📚 Engineering Basis & Limitations"):
        st.markdown("**Governing Formula(s):**")
        st.markdown(formula_md)
        st.markdown("**Standard References:**")
        for ref in references:
            st.markdown(f"- {ref}")
        st.markdown("**Assumptions & Limitations:**")
        for a in assumptions:
            st.markdown(f"- {a}")
