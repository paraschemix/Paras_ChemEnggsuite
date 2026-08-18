"""
utils/styling.py
==================
Injects the suite's visual theme, matched to the reference design at
calculators.profitsfirst.in: deep teal sidebar, mint-green accents,
white rounded cards with soft shadows, light gray page background.
Call `inject_global_css()` once near the top of every page after
`st.set_page_config(...)`.

Includes mobile/tablet responsive breakpoints (max-width: 768px, 480px)
so the suite works on phones, not just desktop-wide layout.

No class names or function signatures changed from the previous version
— this is a drop-in replacement for the existing file.
"""

import streamlit as st


# ---------------------------------------------------------------------
# Palette — matched to the Profits First reference screenshots:
# dark teal sidebar/headings, mint-green accent for icons/buttons/links,
# white cards on a light gray page background.
# ---------------------------------------------------------------------
PRIMARY_TEAL = "#0A4B68"        # their "secondary" - dark teal, sidebar bg / headings
PRIMARY_TEAL_DARK = "#083b52"   # darker teal - button hover, active states
ACCENT_MINT = "#10C89C"         # their "primary" - mint/teal-green, buttons/links/active icons
ACCENT_MINT_LIGHT = "#d1fae5"   # emerald-100 equivalent - icon badge backgrounds
SLATE_BG = "#f8fafc"            # page background, light gray
CARD_BG = "#ffffff"
TEXT_BODY = "#64748b"           # secondary/body gray text
SUCCESS_GREEN = "#16a34a"
WARNING_AMBER = "#d97706"
ERROR_RED = "#dc2626"

# Kept for backward compatibility with any code still referencing the old names
PRIMARY_NAVY = PRIMARY_TEAL
ACCENT_BLUE = ACCENT_MINT
SLATE_DARK = PRIMARY_TEAL


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

        /* ---------- Main content padding ---------- */
        .block-container {{
            padding-top: 2rem;
            padding-left: 3rem;
            padding-right: 3rem;
            max-width: 100%;
        }}

        /* ---------- Sidebar: deep teal, matching reference nav drawer ---------- */
        section[data-testid="stSidebar"] {{
            background-color: {PRIMARY_TEAL};
        }}
        section[data-testid="stSidebar"] * {{
            color: #e6f4f1 !important;
        }}
        section[data-testid="stSidebar"] input {{
            color: {PRIMARY_TEAL} !important;
        }}
        /* Sidebar radio/selectbox "pill" active state, mint accent */
        section[data-testid="stSidebar"] label[data-baseweb="radio"] {{
            border-radius: 8px;
        }}

        /* ---------- Brand header block ---------- */
        .brand-header {{
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 6px 0 14px 0;
            border-bottom: 1px solid rgba(255,255,255,0.15);
            margin-bottom: 14px;
            flex-wrap: wrap;
        }}
        .brand-logo-badge {{
            width: 40px; height: 40px;
            background: #ffffff;
            border-radius: 8px;
            display: flex; align-items: center; justify-content: center;
            font-size: 20px; font-weight: 800; color: {PRIMARY_TEAL};
            flex-shrink: 0;
        }}

        /* ---------- Headers ---------- */
        h1 {{
            color: {PRIMARY_TEAL};
            font-weight: 800;
            font-size: 2rem;
            word-wrap: break-word;
        }}
        h2, h3 {{
            color: {PRIMARY_TEAL};
            font-weight: 700;
        }}
        p, .stMarkdown p {{
            color: {TEXT_BODY};
        }}

        /* ---------- Cards (tool cards, metric cards) - white, rounded, soft shadow ---------- */
        div[data-testid="stMetric"] {{
            background: {CARD_BG};
            border: 1px solid #e2e8f0;
            border-radius: 16px;
            padding: 16px 18px;
            box-shadow: 0 4px 6px -1px rgba(10, 75, 104, 0.1), 0 2px 4px -2px rgba(10, 75, 104, 0.1);
        }}
        div[data-testid="stMetricLabel"] {{
            color: {TEXT_BODY} !important;
            font-weight: 600;
            font-size: 0.8rem !important;
        }}
        div[data-testid="stMetricValue"] {{
            color: {PRIMARY_TEAL} !important;
            font-size: 1.4rem !important;
            word-break: break-word;
        }}

        /* Generic bordered containers (st.container(border=True)) styled as
           soft-shadow rounded cards to match the reference tool-list cards */
        div[data-testid="stVerticalBlockBorderWrapper"] {{
            border-radius: 16px !important;
            border: 1px solid #edf2f4 !important;
            box-shadow: 0 4px 6px -1px rgba(10, 75, 104, 0.1), 0 2px 4px -2px rgba(10, 75, 104, 0.1);
        }}

        /* ---------- Buttons: mint accent, matching reference CTAs ---------- */
        .stButton > button, .stDownloadButton > button {{
            background-color: {ACCENT_MINT};
            color: white;
            font-weight: 600;
            border-radius: 8px;
            border: none;
            padding: 0.55rem 1.2rem;
            width: 100%;
        }}
        .stButton > button:hover, .stDownloadButton > button:hover {{
            background-color: #0d9488;
            color: white;
        }}

        /* ---------- Tabs (horizontally scrollable, mint active underline) ---------- */
        div[data-baseweb="tab-list"] {{
            overflow-x: auto;
            overflow-y: hidden;
            flex-wrap: nowrap !important;
            scrollbar-width: thin;
            -webkit-overflow-scrolling: touch;
        }}
        button[data-baseweb="tab"] {{
            font-weight: 600;
            color: {TEXT_BODY};
            white-space: nowrap;
            flex-shrink: 0;
        }}
        button[data-baseweb="tab"][aria-selected="true"] {{
            color: {ACCENT_MINT};
        }}
        div[data-baseweb="tab-highlight"] {{
            background-color: {ACCENT_MINT} !important;
        }}

        /* ---------- Expanders (Engineering Basis panels) ---------- */
        details {{
            background: {CARD_BG};
            border: 1px solid #e2e8f0;
            border-radius: 12px;
        }}
        summary {{
            font-weight: 600;
            color: {PRIMARY_TEAL};
        }}

        /* ---------- Dataframes / tables ---------- */
        [data-testid="stTable"] {{
            border-radius: 12px;
            overflow-x: auto;
            display: block;
        }}

        /* ---------- Icon badge helper (mint, for use alongside tool titles) ---------- */
        .icon-badge {{
            background: {ACCENT_MINT_LIGHT};
            color: {ACCENT_MINT};
            width: 44px; height: 44px;
            border-radius: 10px;
            display: inline-flex; align-items: center; justify-content: center;
            font-size: 20px;
        }}

        /* ---------- Status pill badges (Live / Coming Soon) ---------- */
        .status-live {{
            background: {ACCENT_MINT_LIGHT}; color: #0d7d6f; font-size: 0.7rem; font-weight: 700;
            padding: 2px 8px; border-radius: 9999px; display: inline-block;
        }}
        .status-soon {{
            background: #f1f5f9; color: #64748b; font-size: 0.7rem; font-weight: 700;
            padding: 2px 8px; border-radius: 9999px; display: inline-block;
        }}

        /* =====================================================================
           MOBILE / TABLET RESPONSIVE OVERRIDES
           ===================================================================== */

        @media (max-width: 768px) {{
            .block-container {{
                padding-top: 1rem;
                padding-left: 1rem;
                padding-right: 1rem;
                padding-bottom: 2rem;
            }}

            h1 {{ font-size: 1.5rem; }}
            h2 {{ font-size: 1.15rem; }}
            h3 {{ font-size: 1rem; }}

            /* Force st.columns to stack vertically instead of squeezing
               side by side on tablets */
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
                padding: 12px 14px;
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

            input, select, textarea {{
                font-size: 16px !important; /* prevents iOS auto-zoom on focus */
            }}

            section[data-testid="stSidebar"] {{
                min-width: 100% !important;
                max-width: 100% !important;
            }}
            section[data-testid="stSidebar"] .block-container {{
                padding-left: 1rem;
                padding-right: 1rem;
            }}
        }}

        @media (max-width: 480px) {{
            .block-container {{
                padding-left: 0.75rem;
                padding-right: 0.75rem;
            }}

            h1 {{ font-size: 1.25rem; }}

            .brand-header > div > div:first-child {{
                font-size: 0.9rem !important;
            }}
            .brand-header > div > div:last-child {{
                font-size: 0.68rem !important;
            }}

            div[data-testid="stMetric"] {{
                padding: 10px 12px;
                border-radius: 12px;
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
            <p style="color:{TEXT_BODY};font-size:0.95rem;margin-top:0;">{subtitle}</p>
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
    Sidebar (or main-page, if compact=False) branding block: logo badge +
    suite name, matched to the reference site's white-badge-on-teal
    header treatment. Replace the badge text with an actual <img> tag
    once a real logo asset exists.
    """
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