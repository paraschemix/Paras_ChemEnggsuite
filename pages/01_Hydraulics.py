"""pages/01_Hydraulics.py — Domain 1: Fluid Mechanics, Hydraulics & Piping Systems."""
import streamlit as st
from utils.ui_components import inject_global_css, render_page_header, render_brand_header, render_unit_toggle
from utils.runner import render_domain_page
from domains.dom_01_hydraulics import REGISTRY

st.set_page_config(layout="wide", page_title="Paras Chemical Engineering Calc Suite", page_icon="🔧")
inject_global_css()
with st.sidebar:
    render_brand_header(compact=True)
    render_unit_toggle()
render_page_header("🔧 Hydraulics", "Line sizing, pressure losses, multiphase hydraulics, pumps, compressors, and flow measurement.")
render_domain_page("Hydraulics", "Fluid Mechanics, Hydraulics & Piping Systems", REGISTRY, "🔧", page_path="pages/01_Hydraulics.py")
