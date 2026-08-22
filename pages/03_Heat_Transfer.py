"""pages/03_Heat_Transfer.py — Domain 3: Heat Transfer & Thermal Equipment."""
import streamlit as st
from utils.ui_components import inject_global_css, render_page_header, render_brand_header, render_unit_toggle
from utils.runner import render_domain_page
from domains.dom_03_heat_transfer import REGISTRY

st.set_page_config(layout="wide", page_title="Paras Chemical Engineering Calc Suite", page_icon="🔥")
inject_global_css()
with st.sidebar:
    render_brand_header(compact=True)
    render_unit_toggle()
render_page_header("🔥 Heat Transfer", "Exchanger rating, fired heaters, air coolers, and insulation/heat loss.")
render_domain_page("Heat Transfer", "Heat Transfer & Thermal Equipment", REGISTRY, "🔥", page_path="pages/03_Heat_Transfer.py")
