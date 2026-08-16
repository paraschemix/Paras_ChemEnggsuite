# Paras Chemical Engineering Calc Suite

Enterprise-grade rebuild matching the "Paras Chemical Engineering Calc
Suite" branding and requirements: SaaS-grade UI (hidden Streamlit
chrome, navy/slate theme), a persistent global SI/Imperial unit toggle,
sensible non-zero defaults, dropdown material databases, categorized
tabs, and a PDF/CSV "Generate Design Report" export — on top of the
existing scalable Dynamic Registry architecture.

## What's new vs. the previous `petro_calc_suite` delivery

| Requirement | Implementation |
|---|---|
| Hidden Streamlit menu/footer, corporate theme | `utils/styling.py` - `#MainMenu`, `footer`, toolbar all hidden; navy/slate/blue palette |
| Branding placeholders (logo + header) | `render_brand_header()` - gradient badge + suite name, sidebar (compact) and main page |
| Tabs to avoid scroll fatigue | Domain pages use `st.tabs()` per tool category, not one long scroll |
| Global SI/Imperial toggle | `utils/unit_system.py` - `st.session_state`-backed, persists across every page/rerun |
| Global search (all 50+ tools, live or planned) | `calculators/tool_roadmap.py` + `app.py` sidebar search - searches the full 51-tool roadmap, flags Live vs Coming Soon |
| Non-zero, realistic defaults | Every `InputSpec.default` is a working value (e.g. water at 998 kg/m3, not 0.0) |
| Material dropdowns | Water Hammer tool's pipe-material selector (Steel/Ductile Iron/Copper/PVC/HDPE) pulls real elastic modulus values, not manual entry |
| PDF/CSV Design Report export | `utils/report.py` - `render_report_widget()`, dropped into every tool page next to the email widget |
| Two fully-coded complex tools | **Shortcut Distillation (Fenske-Underwood-Gilliland)** and **Water Hammer & Surge Pressure** - both below |

## The two flagship tools

### Shortcut Distillation (Fenske-Underwood-Gilliland)
`calculators/distillation_engine.py` - combines all three correlations
into one design sequence (Fenske -> Nmin, Underwood -> Rmin, Gilliland ->
actual N at your chosen reflux), since that's how an engineer actually
runs a FUG short-cut in practice. Includes an automatic warning if R/Rmin
is uneconomically close to 1.0 or unusually high above the typical 1.1-1.5
optimum range.

### Water Hammer & Surge Pressure Peak Analysis
`calculators/fluid_dynamics_engine.py` - Joukowsky surge pressure with
the **Korteweg wave-speed correction** for pipe wall elasticity (a
material dropdown drives the elastic modulus), plus an **Allievi rapid-
vs-slow closure check**: compares the actual valve closure time against
the pipe's critical reflection time (2L/a) and applies the correct
formula branch, flagging rapid closures as a cavitation/surge risk.

## Verification - this was actually run, not just written

This is the important part given how much surface area a UI framework
like this has for silent breakage:

1. **Standalone function tests** - every `compute_*` function called
   directly with real numbers; Shortcut Distillation matched the earlier
   verified toolkit exactly (Nmin=7.49, Rmin=1.24); Water Hammer checked
   for physical sanity (steel wave speed 1303 m/s vs HDPE 188 m/s - softer
   pipe correctly gives slower wave speed / lower surge).
2. **PDF generation crash found and fixed** - the initial `utils/report.py`
   crashed on the first real run because fpdf2's base Helvetica font is
   latin-1 only and the suite's formulas are full of unicode (Delta, deg,
   sqrt, em-dash). Added a sanitizer and re-verified with the actual
   unicode strings used elsewhere in the app, not a sanitized test string.
3. **App actually launched** - `streamlit run app.py`, confirmed HTTP 200
   with a clean boot log.
4. **Streamlit's official `AppTest` framework used to simulate real user
   interaction** - not just "does it parse":
   - Landing page: loaded, correctly reports 5/51 tools live.
   - Fluid Dynamics page: **a real bug was caught and fixed here** - a
     classic Python closure late-binding bug in the tab/selectbox loop
     (`format_func=lambda k: tool_titles[k]` captured the loop variable
     by reference, so every tab's dropdown ended up using the *last*
     tab's title mapping once actually invoked, crashing with a
     `ValueError` the moment more than one category tab existed). Fixed
     via the standard default-argument binding trick
     (`lambda k, _titles=tool_titles: _titles[k]`), then **re-tested and
     confirmed all 3 Fluid Dynamics tabs' Calculate buttons work
     correctly**, including explicitly switching to and running the
     Water Hammer tool through the actual rendered dropdown+button flow.
   - Distillation page: Calculate button clicked, correct FUG results
     rendered as `st.metric` cards.
   - Both stub pages (Heat Transfer, Operations Analytics) load without
     error.
   - Confirmed the CSV/PDF download buttons build their file data without
     exception inside the live app context (not just the standalone
     report module test).

This is worth being direct about: the closure bug would **not** have
been caught by syntax checking or by running each `compute_*` function
in isolation - it only shows up when the actual Streamlit widget tree is
exercised with more than one tab. That's why the `AppTest` pass mattered
here, not just as a formality.

## File structure

Same as `petro_calc_suite`, plus:
```
paras_calc_suite/
├── utils/
│   ├── unit_system.py     # NEW - SI/Imperial toggle + NPS/DN pipe size tables
│   └── report.py           # NEW - CSV/PDF design report generator
├── calculators/
│   └── tool_roadmap.py     # NEW - static 51-tool roadmap, cross-referenced for Live/Coming Soon
```
`fluid_dynamics_engine.py` gained the Water Hammer tool (`fd_006`).
`distillation_engine.py` gained Shortcut Distillation (`mt_011`), was
previously an empty stub.

## Running it

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Extending toward 50+ / 500+ tools

Identical pattern to before - see the earlier README's "Extending"
section. The one addition: also add a `RoadmapEntry` to
`calculators/tool_roadmap.py` with a matching `key` so the new tool shows
as "Live" in search and the tabbed roadmap view automatically.

## Known scope limits (stated plainly)

- Only 2 of the 51 roadmap tools have real calculation logic behind them
  (Shortcut Distillation, Water Hammer) plus the 3 carried over from the
  prior delivery (Pressure Drop, Control Valve Liquid/Gas, NPSH) - 5
  live total. The other 46 are roadmap placeholders with titles only, by
  design, matching the "architect the framework, then write the
  calculation logic for the prioritized tools" instruction.
- Email sending requires SMTP secrets to be configured (unchanged from
  before) - untested end-to-end since that requires real credentials,
  but the failure path (missing secrets) was verified to show a clear
  message rather than crash.
- PDF/CSV export tested for successful generation, not for exact visual
  layout fidelity across all possible result value types.
