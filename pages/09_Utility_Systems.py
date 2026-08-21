"""pages/09_Utility_Systems.py — Domain 9: Plant Utilities, Energy & Power Generation."""
import streamlit as st
from utils.ui_components import inject_global_css, render_page_header, render_brand_header, render_unit_toggle
from utils.runner import render_domain_page
from domains.dom_09_utility_systems import REGISTRY

st.set_page_config(layout="wide", page_title="Paras Chemical Engineering Calc Suite", page_icon="💧")
inject_global_css()
with st.sidebar:
    render_brand_header(compact=True)
    render_unit_toggle()
render_page_header("💧 Utility Systems", "Steam/condensate networks, cooling water, compressed air, and pinch analysis.")
render_domain_page("Utility Systems", "Plant Utilities, Energy & Power Generation", REGISTRY, "💧")
