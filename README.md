# Paras Chemical Engineering Calc Suite — v8: 40 Live Tools

**40 live tools now, up from 36.** First round since v7 focused purely on
*deepening* domains rather than closing gaps — every one of the 4 new
tools this round went into a domain that already had live content.

## What's new this round

| Domain | New tools | Hand-verified reference value |
|---|---|---|
| 🔥 Heat Transfer (`dom_03`) | Cylindrical Pipe Insulation Heat Loss, Air-Cooled Exchanger (Fin-Fan) Air-Side Sizing | 79.28 Btu/hr-ft heat loss, 85.1°F surface temp; 78.36 ft2 face area |
| 💧 Utility Systems (`dom_09`) | Cooling Tower Evaporation, Blowdown & Makeup | E=170 gpm, M=214.5 gpm at COC=5 |
| 📡 Instrumentation & Control (`dom_10`) | Frequency Response (Bode Point) for FOPDT | \|G(jw)\|=1.789, phase=-32.29° at ω=0.05 rad/time |

## Two real bugs, found and fixed by testing

**1. Missing import, caught immediately on first run.** The new Cooling
Tower tool used `run_validators` and `check_positive`, but
`dom_09_utility_systems/steam_engine.py` had never needed those helpers
before (the original 2 steam tools used inline checks) — so the import
was never there. Running the verification script threw `NameError:
name 'run_validators' is not defined` on the very first test call. Fixed
by adding the import; re-verified all 4 new tools afterward, not just
the one that broke.

**2. A parsing bug in my own new bullet text — again.** I wrote "Cooling
tower evaporation, blowdown, and drift loss calculator" as a roadmap
key, not initially noticing this exact phrase already existed as a
*source-taxonomy* bullet with the same comma-list construction that's
broken the parser twice before (v6, v7). This time it wasn't inside
parentheses — it's a plain "X, Y, and Z" list — so my previous fix
(scanning for commas *inside parens*) wouldn't have caught it. Widened
the corpus scan to catch comma-before-"and" list constructions generally,
confirmed zero remaining instances, then fixed this one by removing the
internal commas. Third time this class of bug has surfaced; the scan is
now written to catch the broader pattern, not just the narrower one from
before.

## Verification

1. 42 files syntax-checked, zero errors.
2. All 4 new functions hand-derived and hand-computed *before* any code
   was written — insulation heat loss cross-checked two ways (heat loss
   rate AND resulting surface temperature, both physically sensible:
   ~85°F surface on a 300°F pipe with 2" insulation is a believable,
   safe-to-touch result).
3. Roadmap cross-referencing: 40/40 live tools confirmed, 0 duplicate
   keys across 232 total entries.
4. All 12 pages + all 4 new tools clicked through their actual rendered
   pages via the `switch_page` pattern, each one explicitly selected via
   its dropdown (not relying on tab-default ordering).
5. CI workflow extended with 4 new tool checks, run locally in full
   before being committed.

## Realistic roadmap, updated

| Package | Live tools | Domains populated |
|---|---|---|
| v7 | 36 | 12 of 12 |
| **v8 (this delivery)** | **40** | **12 of 12** |
| v9 | ~55 | 12 of 12, deeper |
| v10 | 100+ | full depth per domain |

## Still open / natural next picks

- Domain 6 (Process Safety): two-phase flashing relief (DIERS/Omega
  method) — still the natural highest-value pick, deliberately deferred
  again this round due to the complexity/verification-confidence tradeoff
  flagged in v7.
- Domain 8 (Solids Handling): only 2 tools — cyclone separator
  efficiency (Lapple correlation) is a well-defined next addition.
- Domain 11 (Economics): only 3 tools — IRR (via bisection root-finding,
  building on the existing NPV tool) is a natural, low-risk extension.

## Running it

```bash
pip install -r requirements.txt
streamlit run app.py
```
