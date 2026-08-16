# GitHub Copilot Instructions for Paras Chemical Engineering Calc Suite

## Architectural Rules
1. Project Context: "Paras Chemical Engineering Calc Suite" (deployed on Streamlit Community Cloud).
2. Modular Structure:
   - Every tool must be a standalone Python file in `tools/<domain_folder>/<tool_name>.py`.
   - Every file must expose an entrypoint function: `def run():`.
   - Tools are dynamically registered in `core/registry.py`.

## UI & Design System
- Modern corporate theme: clean typography, `st.container()`, `st.columns()`, and `st.tabs()`.
- Avoid vertical scroll fatigue by using multi-column input layouts.
- Display primary engineering outputs using `st.metric()` cards.
- Place intermediate parameters (e.g., Reynolds Number, friction factor, Z-factor) inside `with st.expander("Intermediate Parameters & Calculations"):`.

## Unit System & Data Integrity
- Check `st.session_state.get('unit_system', 'SI')` at the start of `run()`.
- Toggle labels, units, and conversion factors dynamically (SI: bar, m³/hr, °C, mm | Imperial: psi, GPM, °F, inches NPS).
- NEVER use 0.0 as default for physical properties or geometry. Pre-populate realistic values (e.g., Water at 20°C, Commercial Steel roughness = 0.045 mm / 0.0018 in).
- Include material and fluid dropdown pickers (`st.selectbox`) instead of requiring manual numerical inputs where possible.

## Calculation Engine
- Ensure strict adherence to standards: API 520/526, GPSA Engineering Data Book, Perry's Chemical Engineers' Handbook, ISA-75, ASME B31.3/VIII.
- Input validation: Set explicit `min_value` and `max_value` on `st.number_input`.
- Provide a button at the bottom of the tool to download calculation results as a CSV summary report.
