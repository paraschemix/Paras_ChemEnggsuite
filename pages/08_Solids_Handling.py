"""pages/08_Solids_Handling.py — Domain 8: Particle Technology & Bulk Solid Handling."""
import streamlit as st
from utils.ui_components import inject_global_css, render_page_header, render_brand_header, render_unit_toggle
from utils.runner import render_domain_page
from domains.dom_08_solids_handling import REGISTRY

st.set_page_config(layout="wide", page_title="Paras Chemical Engineering Calc Suite", page_icon="🪨")
inject_global_css()
with st.sidebar:
    render_brand_header(compact=True)
    render_unit_toggle()
render_page_header("🪨 Solids Handling", "Particle sizing, fluidization/conveying, solid-liquid separation, and bulk storage.")
render_domain_page("Solids Handling", "Particle Technology & Bulk Solid Handling", REGISTRY, "🪨", page_path="pages/08_Solids_Handling.py")
