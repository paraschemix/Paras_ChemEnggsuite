"""pages/11_Economics_Optimization.py — Domain 11: Process Economics, Costing & Optimization."""
import streamlit as st
from utils.ui_components import inject_global_css, render_page_header, render_brand_header, render_unit_toggle
from utils.runner import render_domain_page
from domains.dom_11_economics import REGISTRY

st.set_page_config(layout="wide", page_title="Paras Chemical Engineering Calc Suite", page_icon="💰")
inject_global_css()
with st.sidebar:
    render_brand_header(compact=True)
    render_unit_toggle()
render_page_header("💰 Economics & Optimization", "CAPEX/OPEX estimation, profitability metrics, and optimization.")
render_domain_page("Economics & Optimization", "Process Economics, Costing & Optimization", REGISTRY, "💰", page_path="pages/11_Economics_Optimization.py")
