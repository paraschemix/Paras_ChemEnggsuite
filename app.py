"""
app.py
=======
Landing / home page for the PetroProcess Suite. Builds a centralized
MASTER_REGISTRY across all domain engines (currently just fluid_dynamics_
engine; distillation_engine, heat_transfer_engine, etc. plug in the same
way as they're built out toward 500+ tools) and renders a global search
bar in the sidebar so any tool can be found and jumped to instantly,
regardless of which page it physically lives on.
"""

import streamlit as st

from utils.styling import inject_global_css, render_page_header
from calculators.fluid_dynamics_engine import REGISTRY as FLUID_DYNAMICS_REGISTRY

# As new engine modules are built out, import and merge them here:
# from calculators.distillation_engine import REGISTRY as DISTILLATION_REGISTRY
# from calculators.heat_transfer_engine import REGISTRY as HEAT_TRANSFER_REGISTRY
# from calculators.operations_analytics_engine import REGISTRY as OPS_ANALYTICS_REGISTRY

st.set_page_config(
    layout="wide",
    page_title="PetroProcess Suite 500+",
    page_icon="⚙️",
    initial_sidebar_state="expanded",
)
inject_global_css()

# ---------------------------------------------------------------------
# MASTER REGISTRY — merges every domain's REGISTRY dict into one lookup.
# This is what powers global search: it's a flat map of
#   tool_key -> (ToolSpec, domain_label, page_path)
# regardless of which page.py file a tool's UI actually renders on.
# ---------------------------------------------------------------------
DOMAIN_REGISTRIES = {
    "🌊 Fluid Dynamics": (FLUID_DYNAMICS_REGISTRY, "pages/1_🌊_Fluid_Dynamics.py"),
    # "⚗️ Distillation": (DISTILLATION_REGISTRY, "pages/2_⚗️_Distillation.py"),
    # "🔥 Heat Transfer": (HEAT_TRANSFER_REGISTRY, "pages/3_🔥_Heat_Transfer.py"),
    # "📊 Operations Analytics": (OPS_ANALYTICS_REGISTRY, "pages/4_📊_Operations_Analytics.py"),
}


def build_master_index() -> dict:
    """Flattens all domain registries into a single {key: (spec, domain, page)} dict."""
    master = {}
    for domain_label, (registry, page_path) in DOMAIN_REGISTRIES.items():
        for key, spec in registry.items():
            master[key] = {"spec": spec, "domain": domain_label, "page": page_path}
    return master


MASTER_INDEX = build_master_index()
TOTAL_TOOLS_LIVE = len(MASTER_INDEX)
TOTAL_TOOLS_TARGET = 500


# ---------------------------------------------------------------------
# Sidebar — Global Search
# ---------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🔎 Global Tool Search")
    search_query = st.text_input(
        "Search all 500+ tools", placeholder="e.g. 'Cv', 'NPSH', 'pressure drop'...",
        label_visibility="collapsed",
    )

    if search_query:
        query_lower = search_query.lower()
        matches = [
            entry for entry in MASTER_INDEX.values()
            if query_lower in entry["spec"].title.lower()
            or query_lower in entry["spec"].description.lower()
            or query_lower in entry["spec"].category.lower()
        ]
        st.markdown(f"**{len(matches)} result(s):**")
        for entry in matches:
            spec = entry["spec"]
            st.markdown(f"- **{spec.title}**  \n  _{entry['domain']} → {spec.category}_")
            st.caption(f"Open via the **{entry['domain']}** page in the sidebar navigation above.")
    else:
        st.caption("Type to search across every tool in the suite, live or planned.")

    st.divider()
    st.markdown("### 📂 Domains")
    for domain_label, (registry, page_path) in DOMAIN_REGISTRIES.items():
        st.markdown(f"- {domain_label} — {len(registry)} tool(s) live")


# ---------------------------------------------------------------------
# Main landing content
# ---------------------------------------------------------------------
render_page_header(
    "⚙️ PetroProcess Suite",
    "Enterprise-grade petrochemical & process engineering calculations — GPSA, Perry's, API 520/521, ISA-75.01",
)

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Tools Live", TOTAL_TOOLS_LIVE)
with col2:
    st.metric("Target Scale", f"{TOTAL_TOOLS_TARGET}+")
with col3:
    st.metric("Domains Active", len(DOMAIN_REGISTRIES))

st.markdown("---")
st.markdown("### Getting Started")
st.markdown(
    """
    Use the **sidebar navigation** to jump into a domain page (Fluid Dynamics,
    Distillation, Heat Transfer, Operations Analytics, and more as the suite
    grows), or use the **Global Tool Search** box in the sidebar to find a
    specific calculator by name across every domain at once.
    """
)

st.markdown("### Architecture Note (for maintainers)")
with st.expander("How this suite scales to 500+ tools without code bloat"):
    st.markdown(
        """
        Every domain (`calculators/*_engine.py`) exposes a `REGISTRY` dict
        mapping a unique tool key to a `ToolSpec` — a declarative bundle of
        inputs, a pure `compute()` function, and documentation metadata
        (see `calculators/registry_base.py`).

        Domain pages (`pages/*.py`) are **thin dynamic loaders**: they list
        `REGISTRY.keys()` in a selectbox, render `st.number_input` widgets
        generically from each tool's `InputSpec` list, call `compute()`,
        and render the results — with zero tool-specific UI code. Adding
        tool #501 means adding one `compute_xxx()` function and one
        `ToolSpec` entry to the relevant engine file; **no page file, no
        app.py, and no styling code ever needs to change.**

        This file's `MASTER_INDEX` then just merges every domain's
        `REGISTRY` into one flat lookup so the global search bar works
        across all of them uniformly.
        """
    )
