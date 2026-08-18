"""
utils/styling.py
==================
Injects a clean, enterprise-grade CSS theme (slate grey / navy blue
accents, HYSYS-like professional feel) into every Streamlit page. Call
`inject_global_css()` once near the top of every page after
`st.set_page_config(...)`.

MOBILE UPDATE: added responsive breakpoints (@media max-width: 768px and
480px) so the suite is usable on phones/tablets, not just desktop-wide
layout. Streamlit's built-in column stacking on narrow screens was being
undermined by fixed paddings, oversized brand header flex items, and a
metric-card grid that never reflowed — all addressed below. No class
names or function signatures changed, so this is a drop-in replacement
for the existing file; nothing else needs to change.
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
        /* ---------- Hide default Streamlit chrome for a SaaS feel ---------- */
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        header[data-testid="stHeader"] {{background: transparent;}}
        div[data-testid="stToolbar"] {{visibility: hidden; height: 0; position: fixed;}}
        div[data-testid="stDecoration"] {{visibility: hidden; height: 0; position: fixed;}}
        div[data-testid="stStatusWidget"] {{visibility: hidden; height: 0; position: fixed;}}

        /* ---------- App background & base typography ---------- */
        .stApp {{
            background-color: {SLATE_BG};
        }}
        html, body, [class*="css"] {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        }}

        /* ---------- Main content padding (tighter on mobile by default) ---------- */
        .block-container {{
            padding-top: 2rem;
            padding-left: 3rem;
            padding-right: 3rem;
            max-width: 100%;
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

        /* ---------- Brand header block ---------- */
        .brand-header {{
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 6px 0 14px 0;
            border-bottom: 1px solid #334155;
            margin-bottom: 14px;
            flex-wrap: wrap;
        }}
        .brand-logo-badge {{
            width: 40px; height: 40px;
            background: linear-gradient(135deg, {ACCENT_BLUE}, {PRIMARY_NAVY});
            border-radius: 8px;
            display: flex; align-items: center; justify-content: center;
            font-size: 20px; font-weight: 800; color: white;
            flex-shrink: 0;
        }}

        /* ---------- Headers ---------- */
        h1 {{
            color: {PRIMARY_NAVY};
            font-weight: 800;
            border-bottom: 3px solid {ACCENT_BLUE};
            padding-bottom: 0.4rem;
            font-size: 1.9rem;
            word-wrap: break-word;
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
            font-size: 0.8rem !important;
        }}
        div[data-testid="stMetricValue"] {{
            color: {PRIMARY_NAVY} !important;
            font-size: 1.4rem !important;
            word-break: break-word;
        }}

        /* ---------- Buttons ---------- */
        .stButton > button, .stDownloadButton > button {{
            background-color: {ACCENT_BLUE};
            color: white;
            font-weight: 600;
            border-radius: 6px;
            border: none;
            padding: 0.5rem 1.2rem;
            width: 100%;
        }}
        .stButton > button:hover, .stDownloadButton > button:hover {{
            background-color: {PRIMARY_NAVY};
            color: white;
        }}

        /* ---------- Tabs (horizontally scrollable instead of overflowing/wrapping badly) ---------- */
        div[data-baseweb="tab-list"] {{
            overflow-x: auto;
            overflow-y: hidden;
            flex-wrap: nowrap !important;
            scrollbar-width: thin;
            -webkit-overflow-scrolling: touch;
        }}
        button[data-baseweb="tab"] {{
            font-weight: 600;
            color: #475569;
            white-space: nowrap;
            flex-shrink: 0;
        }}
        button[data-baseweb="tab"][aria-selected="true"] {{
            color: {ACCENT_BLUE};
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
            overflow-x: auto;
            display: block;
        }}

        /* ---------- Status pill badges (Live / Coming Soon) ---------- */
        .status-live {{
            background: #dcfce7; color: #166534; font-size: 0.7rem; font-weight: 700;
            padding: 2px 8px; border-radius: 9999px; display: inline-block;
        }}
        .status-soon {{
            background: #f1f5f9; color: #64748b; font-size: 0.7rem; font-weight: 700;
            padding: 2px 8px; border-radius: 9999px; display: inline-block;
        }}

        /* =====================================================================
           MOBILE / TABLET RESPONSIVE OVERRIDES
           ===================================================================== */

        /* --- Tablet and below (portrait tablets, large phones landscape) --- */
        @media (max-width: 768px) {{
            .block-container {{
                padding-top: 1rem;
                padding-left: 1rem;
                padding-right: 1rem;
                padding-bottom: 2rem;
            }}

            h1 {{
                font-size: 1.4rem;
                padding-bottom: 0.3rem;
                border-bottom-width: 2px;
            }}
            h2 {{ font-size: 1.15rem; }}
            h3 {{ font-size: 1rem; }}

            /* Force st.columns to stack vertically instead of squeezing side
               by side — Streamlit's own responsive breakpoint is narrower
               than this, so metric rows built with 3-4 columns were still
               cramming on tablets. */
            div[data-testid="stHorizontalBlock"] {{
                flex-direction: column !important;
            }}
            div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {{
                width: 100% !important;
                flex: 1 1 100% !important;
                min-width: 100% !important;
                margin-bottom: 0.5rem;
            }}

            div[data-testid="stMetric"] {{
                padding: 10px 12px;
            }}
            div[data-testid="stMetricValue"] {{
                font-size: 1.2rem !important;
            }}

            .brand-header {{
                gap: 8px;
                padding: 4px 0 10px 0;
            }}
            .brand-logo-badge {{
                width: 34px; height: 34px; font-size: 16px;
            }}

            .stButton > button, .stDownloadButton > button {{
                padding: 0.6rem 1rem;
                font-size: 0.9rem;
            }}

            /* Number/text inputs and selects: comfortable tap targets */
            input, select, textarea {{
                font-size: 16px !important; /* prevents iOS auto-zoom on focus */
            }}

            /* Sidebar: full-width when open, and don't let long tool titles
               force horizontal scroll */
            section[data-testid="stSidebar"] {{
                min-width: 100% !important;
                max-width: 100% !important;
            }}
            section[data-testid="stSidebar"] .block-container {{
                padding-left: 1rem;
                padding-right: 1rem;
            }}
        }}

        /* --- Phones (portrait) --- */
        @media (max-width: 480px) {{
            .block-container {{
                padding-left: 0.75rem;
                padding-right: 0.75rem;
            }}

            h1 {{ font-size: 1.2rem; }}

            .brand-header > div > div:first-child {{
                font-size: 0.9rem !important;
            }}
            .brand-header > div > div:last-child {{
                font-size: 0.68rem !important;
            }}

            div[data-testid="stMetric"] {{
                padding: 8px 10px;
            }}
            div[data-testid="stMetricLabel"] {{
                font-size: 0.72rem !important;
            }}
            div[data-testid="stMetricValue"] {{
                font-size: 1.05rem !important;
            }}

            button[data-baseweb="tab"] {{
                font-size: 0.8rem;
                padding: 8px 10px;
            }}

            .status-live, .status-soon {{
                font-size: 0.62rem;
                padding: 1px 6px;
            }}
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


def render_brand_header(compact: bool = False) -> None:
    """
    Sidebar (or main-page, if compact=False and called outside the
    sidebar) branding block: logo badge + suite name. Replace the badge
    text/gradient with an actual <img> tag once a real logo asset exists
    — this is a clearly-marked placeholder per the branding requirement.
    """
    target = st.sidebar if compact else st
    target.markdown(
        f"""
        <div class="brand-header">
            <div class="brand-logo-badge">P</div>
            <div>
                <div style="font-weight:800;font-size:{'0.95rem' if compact else '1.4rem'};color:{'#e2e8f0' if compact else PRIMARY_NAVY};">
                    Paras Chemical Engineering
                </div>
                <div style="font-size:0.75rem;color:{'#94a3b8' if compact else '#64748b'};">
                    Calc Suite &middot; Enterprise Edition
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )