"""
pages/3_🔥_Heat_Transfer.py
==============================
Dynamic UI loader for the Heat Transfer domain (tools #151-225). Same
pattern as pages/1_🌊_Fluid_Dynamics.py.
"""

import streamlit as st
from utils.styling import inject_global_css, render_page_header
from calculators.heat_transfer_engine import REGISTRY

st.set_page_config(layout="wide", page_title="PetroProcess Suite 500+", page_icon="🔥")
inject_global_css()
render_page_header("🔥 Heat Transfer", "Exchanger rating, fired heaters, and utility balances.")

if not REGISTRY:
    st.info("Tools for this domain are being built out (target: #151-225). "
             "Follow the pattern in calculators/fluid_dynamics_engine.py to add them.")
else:
    st.write(f"{len(REGISTRY)} tool(s) available.")
