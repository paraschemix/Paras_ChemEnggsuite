"""pages/02_Thermodynamics.py — Domain 2: Thermodynamics, VLE & Transport Properties."""
import streamlit as st
from utils.ui_components import inject_global_css, render_page_header, render_brand_header, render_unit_toggle
from utils.runner import render_domain_page
from domains.dom_02_thermodynamics import REGISTRY

st.set_page_config(layout="wide", page_title="Paras Chemical Engineering Calc Suite", page_icon="⚛️")
inject_global_css()
with st.sidebar:
    render_brand_header(compact=True)
    render_unit_toggle()
render_page_header("⚛️ Thermodynamics", "Equations of state, activity coefficients, phase equilibria, and physical property estimation.")
render_domain_page("Thermodynamics", "Thermodynamics, VLE & Transport Properties", REGISTRY, "⚛️")
