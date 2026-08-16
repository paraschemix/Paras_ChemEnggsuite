"""
pages/1_🌊_Fluid_Dynamics.py
==============================
Dynamic UI loader for the Fluid Dynamics & Hydraulics domain. Contains
ZERO tool-specific logic — reads calculators/fluid_dynamics_engine.py's
REGISTRY and generically renders whichever tool the user selects. Every
future domain page follows this identical pattern.
"""

import streamlit as st

from utils.styling import inject_global_css, render_page_header, render_engineering_basis, render_brand_header
from utils.unit_system import render_unit_toggle
from utils.mailer import render_email_widget
from utils.report import render_report_widget
from calculators.fluid_dynamics_engine import REGISTRY

st.set_page_config(layout="wide", page_title="Paras Chemical Engineering Calc Suite", page_icon="🌊")
inject_global_css()

with st.sidebar:
    render_brand_header(compact=True)
    render_unit_toggle()

render_page_header(
    "🌊 Fluid Dynamics & Hydraulics",
    "Piping hydraulics, control valve sizing, surge analysis, and rotating equipment checks.",
)

# -----------------------------------------------------------------
# Group tools by category, rendered as tabs (avoids vertical scroll
# fatigue per the UI requirement) with a tool selector inside each tab.
# -----------------------------------------------------------------
categories: dict[str, list[str]] = {}
for key, spec in REGISTRY.items():
    categories.setdefault(spec.category, []).append(key)

category_tabs = st.tabs(sorted(categories.keys()))

for tab, category in zip(category_tabs, sorted(categories.keys())):
    with tab:
        tool_keys_in_category = categories[category]
        tool_titles = {k: REGISTRY[k].title for k in tool_keys_in_category}
        selected_key = st.selectbox(
            "Select Tool", options=tool_keys_in_category,
            format_func=lambda k, _titles=tool_titles: _titles[k], key=f"select_{category}",
        )
        tool = REGISTRY[selected_key]
        st.caption(tool.description)
        st.markdown("---")

        # ---------------------------------------------------------
        # Generic input rendering — one widget per InputSpec. Never
        # needs to change as new tools are added; it only reads
        # whatever `tool.inputs` declares.
        # ---------------------------------------------------------
        st.markdown("#### Inputs")
        input_cols = st.columns(2)
        values: dict = {}
        for i, inp in enumerate(tool.inputs):
            with input_cols[i % 2]:
                if inp.input_type == "select" and inp.options:
                    values[inp.name] = st.selectbox(
                        inp.display_label(), options=inp.options, key=f"{tool.key}_{inp.name}"
                    )
                else:
                    kwargs = {}
                    if inp.min_value is not None:
                        kwargs["min_value"] = inp.min_value
                    if inp.max_value is not None:
                        kwargs["max_value"] = inp.max_value
                    if inp.step is not None:
                        kwargs["step"] = inp.step
                    values[inp.name] = st.number_input(
                        inp.display_label(), value=inp.default, help=inp.help or None,
                        key=f"{tool.key}_{inp.name}", **kwargs,
                    )

        st.markdown("")
        calculate = st.button("🧮 Calculate", type="primary", key=f"{tool.key}_calc_btn")

        # ---------------------------------------------------------
        # Generic compute + result rendering (with input-result caching)
        # ---------------------------------------------------------
        @st.cache_data
        def _cached_compute(spec_key: str, inputs_items: tuple) -> dict:
            # inputs_items is a tuple of (key, value) pairs sorted — reconstruct dict
            inputs = dict(inputs_items)
            spec = REGISTRY[spec_key]
            return spec.compute(inputs)

        if calculate:
            try:
                # Use a stable, hashable cache key derived from sorted input items
                cache_key = tuple(sorted(values.items()))
                results = _cached_compute(tool.key, cache_key)
                warnings = results.pop("_warnings", [])

                st.markdown("#### Results")
                result_cols = st.columns(3)
                for i, (label, val) in enumerate(results.items()):
                    with result_cols[i % 3]:
                        st.metric(label, val)

                for w in warnings:
                    st.warning(f"⚠️ {w}")

                results["_warnings"] = warnings  # restore for report/email widgets
                st.session_state[f"{tool.key}_last_results"] = results
                st.session_state[f"{tool.key}_last_inputs"] = values

            except ValueError as e:
                st.error(f"❌ {e}")

        # ---------------------------------------------------------
        # Engineering Basis expander (always visible)
        # ---------------------------------------------------------
        render_engineering_basis(tool.formula_md, tool.references, tool.assumptions)

        # ---------------------------------------------------------
        # Report (PDF/CSV) + Email widgets — only meaningful once a
        # calculation has run
        # ---------------------------------------------------------
        last_results = st.session_state.get(f"{tool.key}_last_results")
        last_inputs = st.session_state.get(f"{tool.key}_last_inputs")
        if last_results and last_inputs:
            st.markdown("#### 📄 Export & Share")
            render_report_widget(tool.title, last_inputs, last_results, key_prefix=tool.key)
            render_email_widget(tool.title, last_inputs, last_results, key_prefix=tool.key)
        else:
            st.caption("Run a calculation above to enable exporting or emailing a report.")
