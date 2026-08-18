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

# Inject Custom Tailwind-Inspired Modern UI Overrides
st.markdown("""
    <style>
    /* Main Canvas Background */
    .stApp {
        background-color: #f8fafc;
    }

    /* Dark Navy Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #0f172a !important;
        border-right: 1px solid #1e293b;
    }

    /* Custom Metric & Tool Cards */
    .dashboard-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        margin-bottom: 16px;
    }

    .dashboard-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }

    .card-badge-live {
        background-color: #dcfce7;
        color: #166534;
        font-size: 0.75rem;
        font-weight: 600;
        padding: 2px 8px;
        border-radius: 9999px;
    }

    .card-badge-soon {
        background-color: #f1f5f9;
        color: #64748b;
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

    # Streamlit Option Menu Integration
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
                "background-color": "rgba(255, 255, 255, 0.1)",
                "color": "#ffffff",
                "font-weight": "600",
            },
        }
    )

    st.divider()

    if selected_view == "Global Search":
        st.markdown("### 🔎 Search Roadmap")
        search_query = st.text_input(
            "Search 51 tools...", placeholder="e.g. 'Cv', 'NPSH', 'TOC'...",
            label_visibility="collapsed"
        )
    else:
        st.caption(f"⚡ **{TOTAL_LIVE} of {TOTAL_ROADMAP}** tools active.")

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
    st.markdown("### 📋 Tool Roadmap")
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
                            <strong style="color: #0f172a; font-size: 1rem;">#{e.number}. {e.title}</strong>
                            {badge_html}
                        </div>
                        <div style="color: #64748b; font-size: 0.85rem; margin-top: 4px;">Key: <code>{e.key}</code></div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

# VIEW 2: GLOBAL SEARCH
elif selected_view == "Global Search":
    st.markdown("### 🔎 Global Tool Search Results")
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
                        <strong style="color: #0f172a;">#{e.number}. {e.title}</strong>
                        {badge_html}
                    </div>
                    <div style="color: #64748b; font-size: 0.85rem; margin-top: 4px;">Domain: {e.domain}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
    else:
        st.info("Type a query in the sidebar search box to filter across all 51 roadmap tools.")

# VIEW 3: DOMAIN SUMMARY INDEX
elif selected_view == "Domain Index":
    st.markdown("### 📂 Domain Summary")
    for domain in get_domain_order():
        domain_tools = [e for e in ROADMAP if e.domain == domain]
        live_count = sum(1 for e in domain_tools if e.key in LIVE_KEYS)
        
        with st.expander(f"{domain} ({live_count}/{len(domain_tools)} Live)"):
            for e in domain_tools:
                status_icon = "🟢" if e.key in LIVE_KEYS else "⚪"
                st.write(f"{status_icon} **#{e.number}. {e.title}**")

st.markdown("---")

# Getting Started & Architecture
st.markdown("### Getting Started")
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
