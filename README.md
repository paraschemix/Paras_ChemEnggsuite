# PetroProcess Suite — Scalable Streamlit Calculation Platform

Enterprise-grade, multi-page Streamlit suite architected to scale to
**500+ calculation tools** without code bloat, via a Dynamic
Dictionary-Registry pattern. This deliverable includes the complete
foundational architecture plus **3 fully implemented, tested
calculators** in the Fluid Dynamics domain.

## Verified working

- Every file parses cleanly (`ast.parse`, 0 syntax errors across 14 files).
- All 3 calculation engines tested directly with real inputs — results
  cross-checked against the earlier JS/Python toolkit versions (e.g.
  liquid valve Cv = 21.213, matching prior verified output exactly).
- The app was **actually launched** (`streamlit run app.py`) and
  confirmed to boot and serve HTTP 200 with a clean log — not just
  syntax-checked.

## Architecture — how this scales to 500+ tools

```
petro_calc_suite/
├── app.py                          # Landing page + global master search index
├── requirements.txt
├── utils/
│   ├── conversions.py               # SI <-> Imperial unit conversion functions
│   ├── validators.py                # Physical-limit input validation (ValidationResult)
│   ├── mailer.py                    # SMTP email report dispatcher + Streamlit widget
│   └── styling.py                   # Slate/navy industrial theme + shared UI helpers
├── calculators/
│   ├── registry_base.py             # ToolSpec / InputSpec — the core scaling pattern
│   ├── fluid_dynamics_engine.py     # Tools #1-75 — 3 FULLY IMPLEMENTED + registry pattern
│   ├── distillation_engine.py       # Tools #76-150 — stubbed, ready for population
│   ├── heat_transfer_engine.py      # Tools #151-225 — stubbed
│   └── operations_analytics_engine.py  # Tools #426-500 — stubbed
└── pages/
    ├── 1_🌊_Fluid_Dynamics.py        # Dynamic UI loader — zero tool-specific code
    ├── 2_⚗️_Distillation.py
    ├── 3_🔥_Heat_Transfer.py
    └── 4_📊_Operations_Analytics.py
```

### The core pattern: `ToolSpec` + `REGISTRY`

Every calculation tool is defined **once**, in its domain's `*_engine.py`
file, as:
1. A pure `compute_xxx(values: dict) -> dict` function — no Streamlit
   code, just math + validation. Easy to unit-test in isolation (see
   the verification commands below).
2. A `ToolSpec` — a declarative bundle of `InputSpec` objects (label,
   default, min/max, unit), the `compute` function reference, and
   documentation metadata (formula, standard references, assumptions).

The domain's `REGISTRY: dict[str, ToolSpec]` collects these. The page
file (`pages/1_🌊_Fluid_Dynamics.py`) then **never contains any
tool-specific code** — it:
- lists `REGISTRY.keys()` in a selectbox (grouped by `category`),
- generically renders one `st.number_input` per `InputSpec`,
- calls `tool.compute(values)`,
- renders results via `st.metric`,
- renders the "📚 Engineering Basis & Limitations" expander from
  `tool.formula_md` / `references` / `assumptions`,
- renders the email-report widget.

**Adding tool #501 means:** write one `compute_xxx()` function, one
`ToolSpec`, add it to `REGISTRY`. Nothing else changes — not the page,
not `app.py`, not the styling. This is what prevents 500 tools from
becoming 500 hardcoded `if/else` blocks or 500 near-duplicate page files.

### Global search

`app.py` merges every domain's `REGISTRY` into one flat `MASTER_INDEX`
and powers a sidebar search box that matches on title/description/
category across all domains at once — regardless of which page a tool's
UI actually lives on.

## The 3 fully implemented calculators (Fluid Dynamics)

1. **Single-Phase Pressure Drop** — Darcy-Weisbach with the Swamee-Jain
   explicit friction factor approximation (avoids the iterative solve,
   matches the prompt's specified method exactly).
2. **Control Valve Sizing (Cv)** — split into liquid and gas/vapor
   variants per ISA-75.01, both with choked-flow detection.
3. **NPSH Available vs. Required** — margin check with a configurable
   target and an automatic cavitation-risk warning.

Each has a full "📚 Engineering Basis & Limitations" expander citing
real standards (ISA-75.01, GPSA, Crane TP-410, Hydraulic Institute
ANSI/HI 9.6.1, API 610) and stated assumptions/limitations — not generic
placeholder text.

## Running it

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Email setup (optional)

Create `.streamlit/secrets.toml`:
```toml
[smtp]
host = "smtp.gmail.com"
port = 587
username = "your_email@gmail.com"
password = "your_app_password"
sender_name = "PetroProcess Suite"
```
(For Gmail, use an [App Password](https://myaccount.google.com/apppasswords),
not your regular password.) Without this configured, the "Send Report"
button will show a clear message telling the user email isn't set up
yet, rather than failing silently.

## Extending toward 500+ tools

1. Open (or create) the relevant `calculators/*_engine.py`.
2. Write `compute_yourtool(values: dict) -> dict` — pure function,
   validate inputs via `utils/validators.py` helpers, raise `ValueError`
   with a clear message on invalid input.
3. Define a `ToolSpec` with its `InputSpec` list and documentation.
4. Add it to that engine's `REGISTRY` dict.
5. Done — it will appear in its domain page's selectbox and in global
   search automatically. No other file needs to change.

## Verification commands (for maintainers)

```bash
# Syntax-check every file
python3 -c "import ast; [ast.parse(open(f, encoding='utf-8').read()) for f in [...]]"

# Test the calculation engines directly (no Streamlit needed)
python3 -c "
from calculators.fluid_dynamics_engine import compute_valve_cv_liquid
print(compute_valve_cv_liquid({'flow':150,'p1':150,'p2':100,'sg':1.0,'pv':0.5,'pc':3208,'fl':0.9}))
"

# Confirm the app actually boots
streamlit run app.py --server.headless true &
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8501
```
