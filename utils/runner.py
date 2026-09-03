"""
utils/runner.py
=================
Generic UI & Runner (Pattern A). One function, `render_domain_page()`,
implements the entire tool-rendering loop: category tabs, generic input
widgets from InputSpec, the Calculate button, result metrics, the
Engineering Basis expander, and the report/email export widgets.

Every domain page (pages/*.py) is now just:
    from domains.dom_XX_name import REGISTRY
    from utils.runner import render_domain_page
    render_domain_page("Domain Title", "description", REGISTRY, "🔧")

This replaces the ~90 lines of identical loader code that used to be
copy-pasted into every one of the 12 page files — a single bug fix or
UI improvement here now applies to all 12 domains at once, which is the
whole point of "Generic UI & Runner" as a named architectural component.
"""

import streamlit as st

from utils.ui_components import (
    render_engineering_basis, render_report_widget, render_email_widget,
    render_caution_banner, render_domain_footer_nav,
)
from utils.unit_converter import get_unit_options, convert_to_canonical


def render_domain_page(domain_title: str, description: str, registry: dict, icon: str = "", page_path: str = "") -> None:
    """Renders a full domain page body (everything below the page header).

    `page_path` (e.g. "pages/01_Hydraulics.py") lets the cross-page
    navigation footer exclude the current page from its own link list —
    pass the page's own filename when calling this from pages/*.py.
    """
    if not registry:
        st.info(
            "Tools for this domain are being built out. Follow the pattern in "
            "domains/dom_01_hydraulics/fluid_dynamics_engine.py to add them — this page "
            "renders them automatically once the domain's REGISTRY is populated."
        )
        render_domain_footer_nav(page_path)
        return

    categories: dict[str, list[str]] = {}
    for key, spec in registry.items():
        categories.setdefault(spec.category, []).append(key)

    category_tabs = st.tabs(sorted(categories.keys()))

    for tab, category in zip(category_tabs, sorted(categories.keys())):
        with tab:
            tool_keys_in_category = categories[category]
            tool_titles = {k: registry[k].title for k in tool_keys_in_category}
            selected_key = st.selectbox(
                "Select Tool", options=tool_keys_in_category,
                format_func=lambda k, _titles=tool_titles: _titles[k],
                key=f"select_{category}",
            )
            tool = registry[selected_key]
            st.caption(tool.description)
            render_caution_banner()
            st.markdown("---")

            st.markdown("#### Inputs")
            input_cols = st.columns(2)
            values: dict = {}
            for i, inp in enumerate(tool.inputs):
                with input_cols[i % 2]:
                    if inp.input_type == "select" and inp.options:
                        values[inp.name] = st.selectbox(
                            inp.display_label(), options=inp.options, key=f"{tool.key}_{inp.name}"
                        )
                    elif inp.input_type == "text":
                        values[inp.name] = st.text_input(
                            inp.display_label(), value=str(inp.default_text or ""), help=inp.help or None,
                            key=f"{tool.key}_{inp.name}",
                        )
                    else:
                        kwargs = {}
                        if inp.min_value is not None:
                            kwargs["min_value"] = inp.min_value
                        if inp.max_value is not None:
                            kwargs["max_value"] = inp.max_value
                        if inp.step is not None:
                            kwargs["step"] = inp.step

                        if inp.quantity_kind and inp.canonical_unit:
                            # v9 unit-aware input: paired number field + unit
                            # dropdown. The number is stored/entered in
                            # whatever unit the dropdown says; conversion to
                            # this tool's canonical unit happens right here,
                            # so `values[inp.name]` is ALWAYS in canonical
                            # units by the time compute() sees it - compute()
                            # functions are completely unaware this exists.
                            unit_options = get_unit_options(inp.quantity_kind)
                            sub_cols = st.columns([3, 2])
                            with sub_cols[0]:
                                raw_value = st.number_input(
                                    inp.label, value=inp.default, help=inp.help or None,
                                    key=f"{tool.key}_{inp.name}", **kwargs,
                                )
                            with sub_cols[1]:
                                default_unit_index = unit_options.index(inp.canonical_unit) if inp.canonical_unit in unit_options else 0
                                selected_unit = st.selectbox(
                                    "Unit", options=unit_options, index=default_unit_index,
                                    key=f"{tool.key}_{inp.name}_unit", label_visibility="collapsed",
                                )
                            values[inp.name] = convert_to_canonical(
                                raw_value, inp.quantity_kind, selected_unit, inp.canonical_unit
                            )
                        else:
                            values[inp.name] = st.number_input(
                                inp.display_label(), value=inp.default, help=inp.help or None,
                                key=f"{tool.key}_{inp.name}", **kwargs,
                            )

            st.markdown("")
            calculate = st.button("🧮 Calculate", type="primary", key=f"{tool.key}_calc_btn")

            if calculate:
                try:
                    results = tool.compute(values)
                    warnings = results.pop("_warnings", [])

                    st.markdown("#### Results")
                    result_cols = st.columns(3)
                    for i, (label, val) in enumerate(results.items()):
                        with result_cols[i % 3]:
                            st.metric(label, val)

                    for w in warnings:
                        st.warning(f"⚠️ {w}")

                    results["_warnings"] = warnings
                    st.session_state[f"{tool.key}_last_results"] = results
                    st.session_state[f"{tool.key}_last_inputs"] = values

                except ValueError as e:
                    st.error(f"❌ {e}")

            render_engineering_basis(tool.formula_md, tool.references, tool.assumptions)

            last_results = st.session_state.get(f"{tool.key}_last_results")
            last_inputs = st.session_state.get(f"{tool.key}_last_inputs")
            if last_results and last_inputs:
                st.markdown("#### 📄 Export & Share")
                render_report_widget(tool.title, last_inputs, last_results, key_prefix=tool.key)
                render_email_widget(tool.title, last_inputs, last_results, key_prefix=tool.key)
            else:
                st.caption("Run a calculation above to enable exporting or emailing a report.")

    render_domain_footer_nav(page_path)
