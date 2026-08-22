"""pages/10_Instrumentation_Control.py — Domain 10: Process Dynamics, Instrumentation & Control."""
import streamlit as st
from utils.ui_components import inject_global_css, render_page_header, render_brand_header, render_unit_toggle
from utils.runner import render_domain_page
from domains.dom_10_instrumentation_control import REGISTRY

st.set_page_config(layout="wide", page_title="Paras Chemical Engineering Calc Suite", page_icon="📡")
inject_global_css()
with st.sidebar:
    render_brand_header(compact=True)
    render_unit_toggle()
render_page_header("📡 Instrumentation & Control", "Dynamic system response, PID tuning, control loop analysis, and signal processing.")
render_domain_page("Instrumentation & Control", "Process Dynamics, Instrumentation & Control", REGISTRY, "📡", page_path="pages/10_Instrumentation_Control.py")
