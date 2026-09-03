"""
pages/13_🔄_Unit_Converter.py
================================
Standalone general-purpose unit converter, built directly on
utils/unit_converter.py (the same engine used for the per-field unit
selectors being rolled out across the 12 physics domains).

Deliberately NOT one of the 12 engineering domains and NOT counted in
utils/tool_roadmap.py's ROADMAP or DOMAIN_PAGES list - it's a general
utility, not a domain-specific calculation, so it doesn't participate in
the "all 12 domains have a live tool" roadmap/CI invariant. It's linked
from the sidebar on every page instead.
"""

import streamlit as st

from utils.ui_components import inject_global_css, render_page_header, render_brand_header, render_unit_toggle
from utils.unit_converter import QUANTITY_KINDS, get_unit_options, convert

st.set_page_config(layout="wide", page_title="Paras Chemical Engineering Calc Suite", page_icon="🔄")
inject_global_css()

with st.sidebar:
    render_brand_header(compact=True)
    render_unit_toggle()

render_page_header(
    "🔄 Unit Converter",
    "General-purpose unit conversion, independent of any specific calculation tool - powered by the same conversion engine used throughout the suite.",
)

quantity_kind_labels = {
    "pressure": "Pressure",
    "temperature": "Temperature",
    "length": "Length",
    "density": "Density",
    "velocity": "Velocity",
    "viscosity_dynamic": "Dynamic Viscosity",
    "flow_volumetric": "Volumetric Flow",
    "flow_mass": "Mass Flow",
    "power_heat_duty": "Power / Heat Duty",
}

col1, col2 = st.columns([1, 2])
with col1:
    selected_kind = st.selectbox(
        "Quantity Type", options=list(quantity_kind_labels.keys()),
        format_func=lambda k: quantity_kind_labels[k],
    )

unit_options = get_unit_options(selected_kind)

st.markdown("---")
input_col, arrow_col, output_col = st.columns([2, 0.5, 2])

with input_col:
    st.markdown("#### From")
    from_value = st.number_input("Value", value=1.0, key=f"conv_from_{selected_kind}")
    from_unit = st.selectbox("Unit", options=unit_options, key=f"conv_from_unit_{selected_kind}")

with arrow_col:
    st.markdown("<div style='text-align:center;font-size:2rem;padding-top:2.2rem;'>→</div>", unsafe_allow_html=True)

with output_col:
    st.markdown("#### To")
    to_unit = st.selectbox("Unit", options=unit_options, index=min(1, len(unit_options) - 1), key=f"conv_to_unit_{selected_kind}")
    try:
        result = convert(from_value, selected_kind, from_unit, to_unit)
        st.metric("Converted Value", f"{result:,.6g} {to_unit}")
    except Exception as e:
        st.error(f"Conversion error: {e}")

st.markdown("---")

with st.expander("📋 Quick reference - all units for this quantity type"):
    st.markdown(f"**{quantity_kind_labels[selected_kind]}** supports: " + ", ".join(unit_options))
    st.caption(
        "Conversions use the `pint` unit library. Temperature conversions correctly account for "
        "the offset (non-multiplicative) nature of °F/°C/°R scales, unlike a naive multiply-by-factor approach."
    )

st.markdown("---")
st.caption(
    "This standalone converter is independent of the 12 engineering domains. Several domain tools "
    "(starting with Hydraulics → Single-Phase Pressure Drop) also have inline per-field unit "
    "selectors using this same engine - look for a unit dropdown next to a numeric input."
)
if selected_kind == "pressure":
    st.caption(
        "⚠️ Note: this converter performs unit-of-measure conversion only (e.g. psi↔kPa↔bar). "
        "'psi' and 'psia' convert identically here - gauge↔absolute conversion is NOT performed, "
        "since that requires knowing local atmospheric pressure. Add/subtract ~14.7 psi (sea level) "
        "separately if you need psig↔psia."
    )

# Simple cross-navigation back to the dashboard, consistent with domain pages
st.page_link("app.py", label="🏠 Return to Main Dashboard", use_container_width=False)
