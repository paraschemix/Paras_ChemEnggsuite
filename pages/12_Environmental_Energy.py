"""pages/12_Environmental_Energy.py — Domain 12: Environmental & Energy (mapping partial, see README)."""
import streamlit as st
from utils.ui_components import inject_global_css, render_page_header, render_brand_header, render_unit_toggle
from utils.runner import render_domain_page
from domains.dom_12_environmental import REGISTRY

st.set_page_config(layout="wide", page_title="Paras Chemical Engineering Calc Suite", page_icon="🌍")
inject_global_css()
with st.sidebar:
    render_brand_header(compact=True)
    render_unit_toggle()
render_page_header("🌍 Environmental & Energy", "Carbon footprint, sustainability, and clean energy calculators. Content scope partial — see README.")
render_domain_page("Environmental & Energy", "Environmental & Energy", REGISTRY, "🌍")
