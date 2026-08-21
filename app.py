"""
app.py
=======
Landing page. Global search and domain navigation live on the MAIN page
(not the sidebar, which Streamlit collapses on mobile) — stats -> search
-> domain cards. Sidebar is minimal: branding + unit toggle only.

Caching: the merged live-tool-key set across all 12 domain REGISTRYs is
wrapped in st.cache_data, keyed off a lightweight tuple signature
(domain label, registry size) rather than the raw ToolSpec dicts, which
aren't hashable.
"""

import streamlit as st

from utils.ui_components import inject_global_css, render_page_header, render_brand_header, render_unit_toggle, get_unit_system
from utils.tool_roadmap import ROADMAP, get_domain_order

from domains.dom_01_hydraulics import REGISTRY as HYDRAULICS_REGISTRY
from domains.dom_02_thermodynamics import REGISTRY as THERMODYNAMICS_REGISTRY
from domains.dom_03_heat_transfer import REGISTRY as HEAT_TRANSFER_REGISTRY
from domains.dom_04_mass_transfer import REGISTRY as MASS_TRANSFER_REGISTRY
from domains.dom_05_reaction import REGISTRY as REACTION_REGISTRY
from domains.dom_06_process_safety import REGISTRY as PROCESS_SAFETY_REGISTRY
from domains.dom_07_equipment_sizing import REGISTRY as EQUIPMENT_SIZING_REGISTRY
from domains.dom_08_solids_handling import REGISTRY as SOLIDS_HANDLING_REGISTRY
from domains.dom_09_utility_systems import REGISTRY as UTILITY_SYSTEMS_REGISTRY
from domains.dom_10_instrumentation_control import REGISTRY as INSTRUMENTATION_CONTROL_REGISTRY
from domains.dom_11_economics import REGISTRY as ECONOMICS_REGISTRY
from domains.dom_12_environmental import REGISTRY as ENVIRONMENTAL_REGISTRY

st.set_page_config(
    layout="wide",
    page_title="Paras Chemical Engineering Calc Suite",
    page_icon="⚙️",
    initial_sidebar_state="collapsed",
)
inject_global_css()

# ---------------------------------------------------------------------
# Domain label -> (REGISTRY, page file path). Order and labels must
# match utils/tool_roadmap.py's DOMAIN_LABELS exactly (1:1 by position)
# so ROADMAP entries cross-reference correctly.
# ---------------------------------------------------------------------
DOMAIN_REGISTRIES = {
    "🔧 Hydraulics": (HYDRAULICS_REGISTRY, "pages/01_Hydraulics.py"),
    "⚛️ Thermodynamics": (THERMODYNAMICS_REGISTRY, "pages/02_Thermodynamics.py"),
    "🔥 Heat Transfer": (HEAT_TRANSFER_REGISTRY, "pages/03_Heat_Transfer.py"),
    "⚗️ Mass Transfer": (MASS_TRANSFER_REGISTRY, "pages/04_Mass_Transfer.py"),
    "🧪 Reaction Engineering": (REACTION_REGISTRY, "pages/05_Reaction_Engineering.py"),
    "🛡️ Process Safety": (PROCESS_SAFETY_REGISTRY, "pages/06_Process_Safety.py"),
    "⚙️ Equipment Sizing": (EQUIPMENT_SIZING_REGISTRY, "pages/07_Equipment_Sizing.py"),
    "🪨 Solids Handling": (SOLIDS_HANDLING_REGISTRY, "pages/08_Solids_Handling.py"),
    "💧 Utility Systems": (UTILITY_SYSTEMS_REGISTRY, "pages/09_Utility_Systems.py"),
    "📡 Instrumentation & Control": (INSTRUMENTATION_CONTROL_REGISTRY, "pages/10_Instrumentation_Control.py"),
    "💰 Economics & Optimization": (ECONOMICS_REGISTRY, "pages/11_Economics_Optimization.py"),
    "🌍 Environmental & Energy": (ENVIRONMENTAL_REGISTRY, "pages/12_Environmental_Energy.py"),
}


@st.cache_data(show_spinner=False)
def build_live_key_set(_registries_signature: tuple) -> frozenset:
    """Merges every domain's live REGISTRY keys into one set. Cached off
    a hashable signature since dicts of ToolSpec objects aren't hashable."""
    live_keys = set()
    for registry, _page in DOMAIN_REGISTRIES.values():
        live_keys.update(registry.keys())
    if "hy_002a" in live_keys or "hy_002b" in live_keys:
        live_keys.add("hy_002ab")
    return frozenset(live_keys)


registries_signature = tuple((label, len(registry)) for label, (registry, _page) in DOMAIN_REGISTRIES.items())
LIVE_KEYS = build_live_key_set(registries_signature)

TOTAL_LIVE = sum(1 for e in ROADMAP if e.key in LIVE_KEYS)
TOTAL_ROADMAP = len(ROADMAP)

# ---------------------------------------------------------------------
# Sidebar — minimal: branding + unit toggle only
# ---------------------------------------------------------------------
with st.sidebar:
    render_brand_header(compact=True)
    render_unit_toggle()
    st.caption(f"{TOTAL_LIVE} of {TOTAL_ROADMAP} tools live across {len(DOMAIN_REGISTRIES)} domains.")

# ---------------------------------------------------------------------
# Main landing content
# ---------------------------------------------------------------------
render_brand_header(compact=False)
render_page_header(
    "Enterprise Process Engineering Toolkit",
    "GPSA &middot; Perry's &middot; API 520/521 &middot; ISA-75.01 standards, with full engineering-basis transparency on every tool.",
)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Tools Live", TOTAL_LIVE)
with col2:
    st.metric("Roadmap Total", TOTAL_ROADMAP)
with col3:
    st.metric("Domains", len(DOMAIN_REGISTRIES))
with col4:
    st.metric("Unit System", get_unit_system())

st.markdown("---")

# ---------------------------------------------------------------------
# GLOBAL SEARCH — main page, mobile-reachable without opening the sidebar
# ---------------------------------------------------------------------
st.markdown("### 🔎 Find a Tool")
search_query = st.text_input(
    "Search all tools", placeholder="e.g. 'Cv', 'NPSH', 'water hammer', 'orifice', 'FUG'...",
    label_visibility="collapsed",
)

if search_query:
    q = search_query.lower()
    matches = [e for e in ROADMAP if q in e.title.lower() or q in e.domain.lower()]
    st.markdown(f"**{len(matches)} result(s)**")
    for e in matches[:25]:
        is_live = e.key in LIVE_KEYS
        badge = '<span class="status-live">LIVE</span>' if is_live else '<span class="status-soon">COMING SOON</span>'
        page_path = DOMAIN_REGISTRIES[e.domain][1]
        cols = st.columns([5, 1])
        with cols[0]:
            st.markdown(f"**{e.title}** &nbsp; {badge}", unsafe_allow_html=True)
            st.caption(e.domain)
        with cols[1]:
            if is_live:
                st.page_link(page_path, label="Open →")
    if len(matches) > 25:
        st.caption(f"...and {len(matches) - 25} more. Refine your search to narrow results.")
    if len(matches) == 0:
        st.caption("No matches. Try a shorter or more general term.")

st.markdown("---")

# ---------------------------------------------------------------------
# DOMAIN NAVIGATION — big tappable cards, one tap to a domain page
# ---------------------------------------------------------------------
st.markdown("### 📂 Browse by Domain")

domain_list = list(DOMAIN_REGISTRIES.items())
for row_start in range(0, len(domain_list), 2):
    row_domains = domain_list[row_start:row_start + 2]
    cols = st.columns(len(row_domains))
    for col, (domain_label, (registry, page_path)) in zip(cols, row_domains):
        domain_tool_count = sum(1 for e in ROADMAP if e.domain == domain_label)
        live_count = sum(1 for e in ROADMAP if e.domain == domain_label and e.key in LIVE_KEYS)
        with col:
            with st.container(border=True):
                st.markdown(f"#### {domain_label}")
                st.caption(f"{live_count} live / {domain_tool_count} planned")
                st.page_link(page_path, label="Open domain →", use_container_width=True)

st.markdown("---")

with st.expander("🏗️ Architecture & roadmap notes"):
    st.markdown(
        f"""
        **Pattern A:** every domain (`domains/dom_XX_*/`) exposes a `REGISTRY`
        dict mapping a unique tool key to a `ToolSpec` (defined in
        `utils/tool_roadmap.py`) — inputs, a pure `compute()` function with
        zero Streamlit calls, and documentation metadata. `utils/runner.py`'s
        `render_domain_page()` renders any populated `REGISTRY` generically —
        no domain page has tool-specific UI code.

        **Known mapping gaps:** two domains in this release
        (`dom_07_equipment_sizing`, `dom_12_environmental`) don't correspond
        1:1 to the original 12-domain source taxonomy. `dom_07` currently has
        zero roadmap entries rather than a guessed-at list. `dom_12` only
        carries the Clean Energy/sustainability bullets that were an
        unambiguous fit — the source taxonomy's refining/polymers/pharma
        tools and its entire Operations Diagnostics & Reliability domain
        don't have a confirmed home in this scheme yet.

        **Adding a tool:** write `compute_xxx()` + a `ToolSpec` in the
        relevant `domains/dom_XX_*/engine.py`, add it to that module's
        `REGISTRY`, add one matching `RoadmapEntry` (same key) to
        `utils/tool_roadmap.py`. Nothing else changes.
        """
    )
