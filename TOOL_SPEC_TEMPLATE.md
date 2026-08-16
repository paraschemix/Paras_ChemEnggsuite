# TOOL SPEC TEMPLATE

Use this template when requesting the AI agent to generate a new tool module.

TOOL SPECIFICATION
- Tool Name: [Human-friendly name]
- Target File Path: tools/dom_XX_category/your_tool.py
- Domain: DOM-XX (see taxonomy)
- Governing Standards: [e.g., ISO 5167, API 520]

REQUIREMENTS
1. Wrap the UI and calculation inside `def run():`.
2. Check `st.session_state.get('unit_system', 'SI')` to toggle units.
3. Inputs: provide labeled inputs with engineering-appropriate non-zero defaults.
4. Outputs: key results via `st.metric()` and an expandable section with intermediate values.
5. Include a CSV/JSON download button summarizing inputs & results.
6. Add inline references to standards or literature used.
7. Add at least one pytest in `tests/tools/` for core math functions.

ADDITIONAL NOTES
- Keep imports minimal; heavy operations belong in helper functions.
- Follow the repo's linting and formatting rules.
