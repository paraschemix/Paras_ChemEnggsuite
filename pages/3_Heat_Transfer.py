"""
pages/3_🔥_Heat_Transfer.py
==============================
Dynamic UI loader for the Heat Transfer domain. Same pattern as
pages/1_🌊_Fluid_Dynamics.py. Currently empty (REGISTRY populated as
tools #21-28 are built out).
"""

import streamlit as st
from utils.styling import inject_global_css, render_page_header, render_brand_header
from utils.unit_system import render_unit_toggle
from calculators.heat_transfer_engine import REGISTRY

st.set_page_config(layout="wide", page_title="Paras Chemical Engineering Calc Suite", page_icon="🔥")
inject_global_css()

with st.sidebar:
    render_brand_header(compact=True)
    render_unit_toggle()

render_page_header("🔥 Heat Transfer", "Exchanger rating, fired heaters, and utility balances.")

if not REGISTRY:
    st.info("Tools for this domain are being built out (roadmap #21-28). "
             "Follow the pattern in calculators/fluid_dynamics_engine.py to add them.")
else:
    st.write(f"{len(REGISTRY)} tool(s) available.")
