"""
app.py
=======
Landing page for the Paras Chemical Engineering Calc Suite. Renders:
  - branding header + hidden Streamlit chrome (utils/styling.py)
  - the persistent global SI/Imperial unit toggle (utils/unit_system.py)
  - a categorized sidebar tool index (from calculators/tool_roadmap.py),
    cross-referenced against live REGISTRY dicts to show Live/Coming Soon
  - a global search bar covering ALL 51 roadmap tools, live or planned
"""

import streamlit as st

from utils.styling import inject_global_css, render_page_header, render_brand_header
from utils.unit_system import render_unit_toggle, get_unit_system
from calculators.fluid_dynamics_engine import REGISTRY as FLUID_DYNAMICS_REGISTRY
from calculators.distillation_engine import REGISTRY as DISTILLATION_REGISTRY
from calculators.heat_transfer_engine import REGISTRY as HEAT_TRANSFER_REGISTRY
from calculators.operations_analytics_engine import REGISTRY as OPS_ANALYTICS_REGISTRY
from calculators.tool_roadmap import ROADMAP, get_domain_order

st.set_page_config(
    layout="wide",
    page_title="Paras Chemical Engineering Calc Suite",
    page_icon="⚙️",
    initial_sidebar_state="expanded",
)
inject_global_css()

# ---------------------------------------------------------------------
# Merge every domain's live REGISTRY into one flat lookup of live keys,
# used only to determine Live vs Coming Soon status against ROADMAP.
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
# fd_002ab in the roadmap represents both fd_002a and fd_002b (liquid + gas
# variants delivered as one roadmap item) — treat it live if either exists.
if "fd_002a" in LIVE_KEYS or "fd_002b" in LIVE_KEYS:
    LIVE_KEYS.add("fd_002ab")

TOTAL_LIVE = sum(1 for e in ROADMAP if e.key in LIVE_KEYS)
TOTAL_ROADMAP = len(ROADMAP)

# ---------------------------------------------------------------------
# Sidebar — Branding, Unit Toggle, Search, Categorized Navigation
# ---------------------------------------------------------------------
with st.sidebar:
    render_brand_header(compact=True)
    render_unit_toggle()
    st.divider()

    st.markdown("### 🔎 Global Tool Search")
    search_query = st.text_input(
        "Search all 51 tools", placeholder="e.g. 'Cv', 'NPSH', 'water hammer'...",
        label_visibility="collapsed",
    )

    if search_query:
        q = search_query.lower()
        matches = [e for e in ROADMAP if q in e.title.lower() or q in e.domain.lower()]
        st.markdown(f"**{len(matches)} result(s):**")
        for e in matches:
            status = "🟢 Live" if e.key in LIVE_KEYS else "⚪ Coming Soon"
            st.markdown(f"**#{e.number}. {e.title}**")
            st.caption(f"{e.domain} &middot; {status}")
    else:
        st.caption(f"{TOTAL_LIVE} of {TOTAL_ROADMAP} tools live. Type to search the full roadmap.")

    st.divider()
    st.markdown("### 📂 Domains")
    for domain in get_domain_order():
        domain_tools = [e for e in ROADMAP if e.domain == domain]
        live_count = sum(1 for e in domain_tools if e.key in LIVE_KEYS)
        st.markdown(f"**{domain}**")
        st.caption(f"{live_count}/{len(domain_tools)} live &middot; open via page navigation above")

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
    st.metric("Full Roadmap", TOTAL_ROADMAP)
with col3:
    st.metric("Domains", len(get_domain_order()))
with col4:
    st.metric("Unit System", get_unit_system())

st.markdown("---")

# ---------------------------------------------------------------------
# Categorized roadmap table, using tabs per domain (per the "avoid
# vertical scrolling fatigue" UI requirement).
# ---------------------------------------------------------------------
st.markdown("### 📋 Tool Roadmap")
domain_tabs = st.tabs([d.split(" ", 1)[1] for d in get_domain_order()])

for tab, domain in zip(domain_tabs, get_domain_order()):
    with tab:
        domain_tools = [e for e in ROADMAP if e.domain == domain]
        for e in domain_tools:
            is_live = e.key in LIVE_KEYS
            badge = '<span class="status-live">LIVE</span>' if is_live else '<span class="status-soon">COMING SOON</span>'
            st.markdown(
                f"**#{e.number}. {e.title}** &nbsp; {badge}",
                unsafe_allow_html=True,
            )

st.markdown("---")
st.markdown("### Getting Started")
st.markdown(
    """
    Use the **sidebar page navigation** to open a domain (Fluid Dynamics,
    Mass Transfer & Aromatics, Heat Transfer, Operations Analytics), or
    use the **Global Tool Search** box in the sidebar to find any of the
    51 roadmap tools by name — including ones still marked "Coming Soon".
    Your **SI / Imperial** unit choice in the sidebar persists across
    every page and tool.
    """
)

with st.expander("🏗️ Architecture note: how this suite scales to 500+ tools"):
    st.markdown(
        """
        Every domain (`calculators/*_engine.py`) exposes a `REGISTRY` dict
        mapping a unique tool key to a `ToolSpec` — a declarative bundle of
        inputs, a pure `compute()` function, and documentation metadata.

        Domain pages (`pages/*.py`) are thin dynamic loaders with **zero
        tool-specific UI code** — they render `st.number_input`/`st.selectbox`
        generically from each tool's `InputSpec` list, call `compute()`,
        and render results via `st.metric`, the shared "📚 Engineering
        Basis & Limitations" expander, the email widget, and the CSV/PDF
        report widget.

        `calculators/tool_roadmap.py` is a separate, static list of all 51
        planned tools — cross-referenced against the live `REGISTRY` dicts
        here in `app.py` to compute Live/Coming Soon status, so the
        roadmap list and the actual shipped code can never silently drift
        apart from each other's *shape*, only from what's actually built.

        **Adding tool #52 (or #501):** write one `compute_xxx()` function,
        one `ToolSpec`, add it to the domain's `REGISTRY`. No page file,
        no `app.py`, no styling code ever needs to change.
        """
    )
