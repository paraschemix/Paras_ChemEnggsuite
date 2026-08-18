import streamlit as st
from streamlit_option_menu import option_menu

# --- Core Suite Imports ---
from utils.styling import inject_global_css, render_page_header, render_brand_header
from utils.unit_system import render_unit_toggle, get_unit_system
from calculators.fluid_dynamics_engine import REGISTRY as FLUID_DYNAMICS_REGISTRY
from calculators.distillation_engine import REGISTRY as DISTILLATION_REGISTRY
from calculators.heat_transfer_engine import REGISTRY as HEAT_TRANSFER_REGISTRY
from calculators.operations_analytics_engine import REGISTRY as OPS_ANALYTICS_REGISTRY
from calculators.tool_roadmap import ROADMAP, get_domain_order

# ---------------------------------------------------------------------
# 1. PAGE CONFIGURATION
# ---------------------------------------------------------------------
st.set_page_config(
    layout="wide",
    page_title="Paras Chemical Engineering Calc Suite",
    page_icon="⚙️",
    initial_sidebar_state="expanded",
)

inject_global_css()

# Inject Custom Navy Blue & White Theme Overrides
st.markdown("""
    <style>
    /* White Main Canvas Background */
    .stApp {
        background-color: #ffffff !important;
        color: #0f172a !important;
    }

    /* Force Core Text Elements to Deep Navy */
    h1, h2, h3, h4, h5, h6, p, label, span, div {
        color: #0f172a;
    }

    /* Dark Navy Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #0f172a !important;
        border-right: 1px solid #1e293b;
    }

    /* Modern White Card UI with Navy Text */
    .dashboard-card {
        background-color: #ffffff;
        border: 1px solid #cbd5e1;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 1px 3px 0 rgba(15, 23, 42, 0.08);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        margin-bottom: 16px;
    }

    .dashboard-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 6px -1px rgba(15, 23, 42, 0.12), 0 2px 4px -1px rgba(15, 23, 42, 0.08);
    }

    /* Card Text Specifics */
    .card-title {
        color: #0f172a !important;
        font-weight: 700;
        font-size: 1rem;
    }

    .card-key {
        color: #1e3a8a !important;
        font-size: 0.85rem;
        margin-top: 4px;
    }

    /* Custom Badges */
    .card-badge-live {
        background-color: #dcfce7;
        color: #166534 !important;
        font-size: 0.75rem;
        font-weight: 700;
        padding: 2px 8px;
        border-radius: 9999px;
    }

    .card-badge-soon {
        background-color: #f1f5f9;
        color: #475569 !important;
        font-size: 0.75rem;
        font-weight: 600;
        padding: 2px 8px;
        border-radius: 9999px;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------
# 2. MERGE LIVE REGISTRIES & STATUS CHECK
# ---------------------------------------------------------------------
ALL_LIVE_REGISTRIES = {
    "🌊 Fluid Dynamics & Hydraulics": (FLUID_DYNAMICS_REGISTRY, "pages/1_🌊_Fluid_Dynamics.py"),
    "⚗️ Mass Transfer & Aromatics": (DISTILLATION_REGISTRY, "pages/2_⚗️_Distillation.py"),
    "🔥 Heat Transfer": (HEAT_TRANSFER_REGISTRY, "pages/3_🔥_Heat_Transfer.py"),
    "📊 Operations Analytics": (OPS_ANALYTICS_REGISTRY, "pages/4_📊_Operations_Analytics.py"),
}

LIVE_KEYS = set()
for registry, _page in ALL_LIVE_REGISTRIES.values():
    LIVE_KEYS.update(registry.keys())

# fd_002ab handles both liquid & gas variants
if "fd_002a" in LIVE_KEYS or "fd_002b" in LIVE_KEYS:
    LIVE_KEYS.add("fd_002ab")

TOTAL_LIVE = sum(1 for e in ROADMAP if e.key in LIVE_KEYS)
TOTAL_ROADMAP = len(ROADMAP)

# ---------------------------------------------------------------------
# 3. SIDEBAR — BRANDING, NAVIGATION, UNITS, SEARCH
# ---------------------------------------------------------------------
with st.sidebar:
    render_brand_header(compact=True)
    render_unit_toggle()
    st.divider()

    selected_view = option_menu(
        menu_title=None,
        options=["Dashboard / Roadmap", "Global Search", "Domain Index"],
        icons=["grid-fill", "search", "diagram-3"],
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"color": "#94a3b8", "font-size": "15px"},
            "nav-link": {
                "font-size": "14px",
                "text-align": "left",
                "margin": "4px 0px",
                "color": "#cbd5e1",
                "border-radius": "8px",
                "padding": "10px 14px"
            },
            "nav-link-selected": {
                "background-color": "rgba(255, 255, 255, 0.15)",
                "color": "#ffffff",
                "font-weight": "600",
            },
        }
    )

    st.divider()

    if selected_view == "Global Search":
        st.markdown("<h3 style='color: #ffffff;'>🔎 Search Roadmap</h3>", unsafe_allow_html=True)
        search_query = st.text_input(
            "Search 51 tools...", placeholder="e.g. 'Cv', 'NPSH', 'TOC'...",
            label_visibility="collapsed"
        )
    else:
        st.markdown(f"<span style='color: #94a3b8;'>⚡ <b>{TOTAL_LIVE} of {TOTAL_ROADMAP}</b> tools active.</span>", unsafe_allow_html=True)

# ---------------------------------------------------------------------
# 4. MAIN BODY ROUTING
# ---------------------------------------------------------------------
render_brand_header(compact=False)
render_page_header(
    "Enterprise Process Engineering Toolkit",
    "GPSA · Perry's · API 520/521 · ISA-75.01 standards, with full engineering-basis transparency on every tool.",
)

# Metrics Grid
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Tools Live", TOTAL_LIVE)
with col2:
    st.metric("Full Roadmap", TOTAL_ROADMAP)
with col3:
    st.metric("Domains", len(get_domain_order()))
with col4:
    st.metric("Unit System", get_unit_system())

st.markdown("---")

# VIEW 1: DASHBOARD & ROADMAP TABS
if selected_view == "Dashboard / Roadmap":
    st.markdown("<h3 style='color: #0f172a;'>📋 Tool Roadmap</h3>", unsafe_allow_html=True)
    domain_tabs = st.tabs([d.split(" ", 1)[1] if " " in d else d for d in get_domain_order()])

    for tab, domain in zip(domain_tabs, get_domain_order()):
        with tab:
            domain_tools = [e for e in ROADMAP if e.domain == domain]
            for e in domain_tools:
                is_live = e.key in LIVE_KEYS
                badge_html = (
                    '<span class="card-badge-live">LIVE</span>' 
                    if is_live else 
                    '<span class="card-badge-soon">COMING SOON</span>'
                )
                
                st.markdown(
                    f"""
                    <div class="dashboard-card">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span class="card-title">#{e.number}. {e.title}</span>
                            {badge_html}
                        </div>
                        <div class="card-key">Key: <code>{e.key}</code></div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

# VIEW 2: GLOBAL SEARCH
elif selected_view == "Global Search":
    st.markdown("<h3 style='color: #0f172a;'>🔎 Global Tool Search Results</h3>", unsafe_allow_html=True)
    if 'search_query' in locals() and search_query:
        q = search_query.lower()
        matches = [e for e in ROADMAP if q in e.title.lower() or q in e.domain.lower() or q in e.key.lower()]
        st.markdown(f"**Found {len(matches)} tool(s) matching:** *'{search_query}'*")
        
        for e in matches:
            is_live = e.key in LIVE_KEYS
            badge_html = '<span class="card-badge-live">LIVE</span>' if is_live else '<span class="card-badge-soon">COMING SOON</span>'
            
            st.markdown(
                f"""
                <div class="dashboard-card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span class="card-title">#{e.number}. {e.title}</span>
                        {badge_html}
                    </div>
                    <div class="card-key">Domain: {e.domain}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
    else:
        st.info("Type a query in the sidebar search box to filter across all 51 roadmap tools.")

# VIEW 3: DOMAIN SUMMARY INDEX
elif selected_view == "Domain Index":
    st.markdown("<h3 style='color: #0f172a;'>📂 Domain Summary</h3>", unsafe_allow_html=True)
    for domain in get_domain_order():
        domain_tools = [e for e in ROADMAP if e.domain == domain]
        live_count = sum(1 for e in domain_tools if e.key in LIVE_KEYS)
        
        with st.expander(f"{domain} ({live_count}/{len(domain_tools)} Live)"):
            for e in domain_tools:
                status_icon = "🟢" if e.key in LIVE_KEYS else "⚪"
                st.write(f"{status_icon} **#{e.number}. {e.title}**")

st.markdown("---")

# Getting Started & Architecture
st.markdown("<h3 style='color: #0f172a;'>Getting Started</h3>", unsafe_allow_html=True)
st.markdown(
    """
    Use the **sidebar navigation** to explore roadmap modules or search tools by keyword.
    To execute live tools, open the corresponding domain page via the Streamlit sidebar page browser.
    Your **SI / Imperial** unit selection dynamically configures unit displays across all active tool modules.
    """
)

with st.expander("🏗️ Architecture note: how this suite scales to 500+ tools"):
    st.markdown(
        """
        Every domain (`calculators/*_engine.py`) exposes a `REGISTRY` dict mapping a unique tool key to a `ToolSpec`.

        Domain pages (`pages/*.py`) are thin dynamic loaders that render input controls generically from each tool's `InputSpec` list, execute calculations via `compute()`, and present formatted metrics and reports.

        `calculators/tool_roadmap.py` tracks all planned modules and automatically cross-references against live `REGISTRY` dicts inside `app.py`.
        """
    )
