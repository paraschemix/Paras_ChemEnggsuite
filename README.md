# Paras Chemical Engineering Calc Suite — v9 Phase 1: Unit Converter Infrastructure

This round tackled the piece of the v9 spec you flagged as highest
priority *and* highest risk: a universal SI ↔ US Customary unit
conversion system. Still 40 live tools — this round is infrastructure
and one retrofit, not new domain content.

## What's actually done vs. what the full v9 spec asked for

The v9 spec's mandate is a genuinely large program (global contrast
audit, breadcrumb nav, dual-persona interpretation text on every tool,
3 new reference-data domains, a new integrated hydraulic-chain tool,
*and* a full unit-system retrofit across all 40 existing tools). Given
you prioritized the unit converter, this round is scoped to that,
done properly, rather than a shallow pass across everything. See
"Deferred to later rounds" below for the rest, unchanged in priority
from what was flagged before.

## 1. Unit conversion engine (`utils/unit_converter.py`)

Built on `pint` (a mature, independently-tested unit library) rather
than hand-rolled conversion factors — 9 quantity kinds covering
pressure, temperature, length, density, velocity, dynamic viscosity,
volumetric flow, mass flow, and power/heat duty.

**Verified against 10 known reference conversions** before touching any
tool, including the trickiest case (temperature — an offset, not purely
multiplicative, unit system): 300°F → 148.889°C, 0°C → 32°F, both exact.

**One real caveat found during testing, not glossed over:** `psi` and
`psia` currently convert as identical units in this engine — this
converter does unit-of-measure conversion only (psi↔kPa↔bar), not
gauge↔absolute conversion, which needs local atmospheric pressure as an
extra input. Documented directly in the code and flagged live in the
Unit Converter page's UI when pressure is selected, rather than left as
a silent trap.

## 2. Architecture: retrofit without touching any of the 40 verified `compute()` functions

This was the actual hard design constraint. Every domain engine's
`compute()` function keeps working in whatever unit system it was
already verified against — **nothing about the physics changed**.
`InputSpec` gained two new *optional* fields (`quantity_kind`,
`canonical_unit`); when unset (the default, true for ~145 of the
suite's ~150 input fields right now), a field renders exactly as
before. When set, `utils/runner.py` renders a paired number+unit
dropdown, converts to the tool's existing canonical unit, and only
*then* hands the value to `compute()` — which never knows the
conversion layer exists.

**Pilot retrofit:** Hydraulics → Single-Phase Pressure Drop, covering 3
different quantity kinds (density, velocity, length) across its 4 main
inputs. Verified two ways:
- Canonical-unit inputs reproduce the exact long-standing result
  (Re=200,000, ΔP=37,330.4 Pa) — zero regression.
- The *same physical scenario* re-entered in imperial units (lb/ft³,
  ft/s, ft) through the actual unit dropdowns produces the same
  physics (Re=199,998.3 vs. 200,000 — the tiny gap is my 5-digit manual
  imperial rounding when typing the test, not a conversion error).

## 3. Standalone Unit Converter (new page, not a 13th physics domain)

Per your request to "make unit conversion another domain" — implemented
as `pages/13_🔄_Unit_Converter.py`, a general-purpose converter built
directly on the same tested engine. **Deliberately not added to
`utils/tool_roadmap.py`'s `ROADMAP`/`DOMAIN_PAGES`** — it's a utility,
not an engineering calculation, so it doesn't participate in the "all
12 domains have a live tool" invariant the CI already checks. Linked
from the sidebar on the landing page and from every domain page's
footer nav instead.

## 4. WCAG contrast — audited, not just claimed

Computed actual WCAG contrast ratios (not assumed) for 9 key color
pairs across the current navy/white theme. **8 of 9 already passed**
comfortably — the theme from prior rounds was already in good shape.
The one failure (`status-soon` "Coming Soon" badge text, 4.34:1 vs. the
4.5:1 required for small text) was fixed by darkening the gray to
`#475569` (now 6.92:1). Re-audited after the fix: all 9 pairs pass.

## Verification

1. 44 files syntax-checked, zero errors.
2. Unit converter tested against 10 independent reference conversions
   across all 9 quantity kinds, including the offset-unit temperature
   edge case.
3. Pilot retrofit tested via `AppTest` two ways (canonical units,
   equivalent imperial units) — same physics, confirming the conversion
   layer works without altering any verified calculation.
4. **Full regression spot-check across all 12 domains** — one
   representative tool per domain clicked through its actual page,
   confirming the shared-file changes (`InputSpec`, `runner.py`,
   `ui_components.py`) broke nothing elsewhere in the suite.
5. Standalone Unit Converter page tested via `AppTest`.
6. WCAG contrast computed (not assumed) before and after the one fix.
7. CI workflow extended with 3 new checks (converter page, reference
   conversions, pilot tool + unit-selector count), all run locally in
   full before being committed.

## Deferred to later rounds (stated plainly, matching prior rounds' practice)

- **Retrofitting the remaining ~145 input fields** across the other 39
  tools with `quantity_kind`/`canonical_unit` — the pattern is proven;
  applying it broadly is mechanical but needs per-field verification
  like the pilot got, which is real, non-trivial effort at this
  project's standard.
- **Breadcrumb navigation** (`Home > Domain > Tool`) — not done this
  round; the existing footer cross-nav and sidebar Home/Converter links
  partially serve this need in the meantime.
- **Dual-persona "Engineering Impact & Interpretation" auto-summary
  box** on every tool — not started.
- **Reference-data domains** (CEPCI history, U-value tables, tray
  vendor/system factors) — not started. Flagging in advance: CEPCI
  specifically updates monthly and I have only moderate confidence in
  precise historical values from memory — when this is built, expect it
  shipped as a small set of well-known textbook reference points with an
  explicit "verify against the current published index" caveat, not a
  large precise historical table.
- **Domain 9 Integrated Pump & Control Valve Hydraulic Chain tool** —
  not started; all the underlying sub-calculations (friction loss, TDH,
  NPSH, Cv sizing) already exist verified elsewhere in the suite and
  would be composed into one chained tool.

## Running it

```bash
pip install -r requirements.txt
streamlit run app.py
```

New dependency this round: `pint>=0.24`.
