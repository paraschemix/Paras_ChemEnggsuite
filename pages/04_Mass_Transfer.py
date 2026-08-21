"""pages/04_Mass_Transfer.py — Domain 4: Mass Transfer & Separation Operations."""
import streamlit as st
from utils.ui_components import inject_global_css, render_page_header, render_brand_header, render_unit_toggle
from utils.runner import render_domain_page
from domains.dom_04_mass_transfer import REGISTRY

st.set_page_config(layout="wide", page_title="Paras Chemical Engineering Calc Suite", page_icon="⚗️")
inject_global_css()
with st.sidebar:
    render_brand_header(compact=True)
    render_unit_toggle()
render_page_header("⚗️ Mass Transfer", "Distillation, absorption/stripping, extraction, adsorption, drying, and membranes.")
render_domain_page("Mass Transfer", "Mass Transfer & Separation Operations", REGISTRY, "⚗️")
