"""pages/06_Process_Safety.py — Domain 6: Process Safety, Relief & Loss Prevention."""
import streamlit as st
from utils.ui_components import inject_global_css, render_page_header, render_brand_header, render_unit_toggle
from utils.runner import render_domain_page
from domains.dom_06_process_safety import REGISTRY

st.set_page_config(layout="wide", page_title="Paras Chemical Engineering Calc Suite", page_icon="🛡️")
inject_global_css()
with st.sidebar:
    render_brand_header(compact=True)
    render_unit_toggle()
render_page_header("🛡️ Process Safety", "PSV sizing (API 520/521/2000), flare systems, dispersion modeling, and risk analysis. Phase 2 priority.")
render_domain_page("Process Safety", "Process Safety, Relief & Loss Prevention", REGISTRY, "🛡️")
