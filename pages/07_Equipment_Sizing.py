"""pages/07_Equipment_Sizing.py — Domain 7: Equipment Sizing (mapping unconfirmed, see README)."""
import streamlit as st
from utils.ui_components import inject_global_css, render_page_header, render_brand_header, render_unit_toggle
from utils.runner import render_domain_page
from domains.dom_07_equipment_sizing import REGISTRY

st.set_page_config(layout="wide", page_title="Paras Chemical Engineering Calc Suite", page_icon="⚙️")
inject_global_css()
with st.sidebar:
    render_brand_header(compact=True)
    render_unit_toggle()
render_page_header("⚙️ Equipment Sizing", "General equipment sizing tools. Content scope not yet confirmed against source taxonomy — see README.")
render_domain_page("Equipment Sizing", "Equipment Sizing", REGISTRY, "⚙️", page_path="pages/07_Equipment_Sizing.py")
