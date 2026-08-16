"""
pages/1_🌊_Fluid_Dynamics.py
==============================
Dynamic UI loader for the Fluid Dynamics domain (tools #1-75). This file
contains ZERO tool-specific logic — it reads calculators/fluid_dynamics_
engine.py's REGISTRY and generically renders whichever tool the user
selects: inputs from ToolSpec.inputs, results from ToolSpec.compute(),
and documentation from ToolSpec.formula_md / references / assumptions.

This is the pattern every future domain page (Distillation, Heat
Transfer, Operations Analytics, ...) follows identically — only the
imported REGISTRY changes.
"""

import streamlit as st

from utils.styling import inject_global_css, render_page_header, render_engineering_basis
from utils.mailer import render_email_widget
from calculators.fluid_dynamics_engine import REGISTRY

st.set_page_config(layout="wide", page_title="PetroProcess Suite 500+", page_icon="🌊")
inject_global_css()

render_page_header(
    "🌊 Fluid Dynamics",
    "Piping hydraulics, control valve sizing, and rotating equipment checks.",
)

# -----------------------------------------------------------------
# Group tools by category for a cleaner selectbox (purely cosmetic —
# the underlying lookup is still the flat REGISTRY dict).
# -----------------------------------------------------------------
categories: dict[str, list[str]] = {}
for key, spec in REGISTRY.items():
    categories.setdefault(spec.category, []).append(key)

col_select, col_spacer = st.columns([2, 1])
with col_select:
    category = st.selectbox("Category", sorted(categories.keys()))
    tool_keys_in_category = categories[category]
    tool_titles = {k: REGISTRY[k].title for k in tool_keys_in_category}
    selected_key = st.selectbox(
        "Tool",
        options=tool_keys_in_category,
        format_func=lambda k: tool_titles[k],
    )

tool = REGISTRY[selected_key]
st.caption(tool.description)
st.markdown("---")

# -----------------------------------------------------------------
# Generic input rendering — one st.number_input per InputSpec.
# This block never needs to change as new tools are added; it only
# reads whatever `tool.inputs` declares.
# -----------------------------------------------------------------
st.markdown("#### Inputs")
input_cols = st.columns(2)
values: dict = {}
for i, inp in enumerate(tool.inputs):
    with input_cols[i % 2]:
        if inp.input_type == "select" and inp.options:
            values[inp.name] = st.selectbox(inp.display_label(), options=inp.options, key=f"{tool.key}_{inp.name}")
        else:
            kwargs = {}
            if inp.min_value is not None:
                kwargs["min_value"] = inp.min_value
            if inp.max_value is not None:
                kwargs["max_value"] = inp.max_value
            if inp.step is not None:
                kwargs["step"] = inp.step
            values[inp.name] = st.number_input(
                inp.display_label(),
                value=inp.default,
                help=inp.help or None,
                key=f"{tool.key}_{inp.name}",
                **kwargs,
            )

st.markdown("")
calculate = st.button("🧮 Calculate", type="primary", key=f"{tool.key}_calc_btn")

# -----------------------------------------------------------------
# Generic compute + result rendering
# -----------------------------------------------------------------
if calculate:
    try:
        results = tool.compute(values)
        warnings = results.pop("_warnings", [])

        st.markdown("#### Results")
        result_cols = st.columns(3)
        i = 0
        for label, val in results.items():
            with result_cols[i % 3]:
                st.metric(label, val)
            i += 1

        for w in warnings:
            st.warning(f"⚠️ {w}")

        # Store last results in session state so the email widget below
        # (rendered on every rerun) has something to send.
        st.session_state[f"{tool.key}_last_results"] = results
        st.session_state[f"{tool.key}_last_inputs"] = values

    except ValueError as e:
        st.error(f"❌ {e}")

# -----------------------------------------------------------------
# Engineering Basis expander (always visible, not just after calc)
# -----------------------------------------------------------------
render_engineering_basis(tool.formula_md, tool.references, tool.assumptions)

# -----------------------------------------------------------------
# Email report widget — only meaningful once a calculation has run
# -----------------------------------------------------------------
last_results = st.session_state.get(f"{tool.key}_last_results")
last_inputs = st.session_state.get(f"{tool.key}_last_inputs")
if last_results and last_inputs:
    render_email_widget(tool.title, last_inputs, last_results, key_prefix=tool.key)
else:
    st.caption("Run a calculation above to enable emailing a report.")
