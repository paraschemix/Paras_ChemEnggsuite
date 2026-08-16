"""
pages/2_⚗️_Distillation.py
=============================
Dynamic UI loader for the Distillation domain (tools #76-150). Identical
pattern to pages/1_🌊_Fluid_Dynamics.py — reads calculators/distillation_
engine.REGISTRY generically. Currently empty pending tools #76-150 being
added to that engine module; the page itself needs no changes when they
are.
"""

import streamlit as st
from utils.styling import inject_global_css, render_page_header
from calculators.distillation_engine import REGISTRY

st.set_page_config(layout="wide", page_title="PetroProcess Suite 500+", page_icon="⚗️")
inject_global_css()
render_page_header("⚗️ Distillation", "Short-cut & rigorous separation calculations.")

if not REGISTRY:
    st.info("Tools for this domain are being built out (target: #76-150). "
             "Follow the pattern in calculators/fluid_dynamics_engine.py to add them — "
             "this page will render them automatically once REGISTRY is populated.")
else:
    st.write(f"{len(REGISTRY)} tool(s) available.")
    # Identical dynamic-loader body as pages/1_🌊_Fluid_Dynamics.py once populated.
