"""pages/05_Reaction_Engineering.py — Domain 5: Chemical Reaction Engineering & Kinetics."""
import streamlit as st
from utils.ui_components import inject_global_css, render_page_header, render_brand_header, render_unit_toggle
from utils.runner import render_domain_page
from domains.dom_05_reaction import REGISTRY

st.set_page_config(layout="wide", page_title="Paras Chemical Engineering Calc Suite", page_icon="🧪")
inject_global_css()
with st.sidebar:
    render_brand_header(compact=True)
    render_unit_toggle()
render_page_header("🧪 Reaction Engineering", "Reactor sizing, kinetic regression, catalyst effectiveness, and reactor thermal safety.")
render_domain_page("Reaction Engineering", "Chemical Reaction Engineering & Kinetics", REGISTRY, "🧪", page_path="pages/05_Reaction_Engineering.py")
