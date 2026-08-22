# Paras Chemical Engineering Calc Suite — UX & Safety Messaging Update

Builds on the Engine Expansion release (15 live tools across 5 domains).
This round: blue/white theme, a validation-required caution banner on
every tool, and cross-page navigation — plus a real bug found and fixed
during verification, documented below rather than glossed over.

## What's new

**1. Blue-on-white theme, applied everywhere.** Because `inject_global_css()`
is called by every single page, this was a one-file change
(`utils/ui_components.py`) that now applies consistently across the
landing page and all 12 domains — headings, sidebar, buttons, tabs, and
status badges all switched from the prior teal/mint palette to blue
(#1D4ED8 primary, #2563EB accent) on a white background. PDF report
headers and HTML email templates updated to match (they had hardcoded
hex colors, not variable references — found and fixed both instances).

**2. "Validate before use" caution banner on every tool.** Added
`render_caution_banner()`, called once per tool render inside
`utils/runner.py`'s shared `render_domain_page()` — meaning it appears
on every current and future tool automatically, with zero per-page or
per-tool code required. It sits directly under the tool description,
above the inputs, so it's seen before a result is generated, not after.

**3. Cross-page navigation footer.** Added `render_domain_footer_nav()`,
also called from the shared `render_domain_page()`, rendering links to
all 11 other domains plus Home at the bottom of every page. Backed by a
new single source of truth, `DOMAIN_PAGES` in `utils/tool_roadmap.py`
(icon + label + page path for all 12 domains) — `app.py`'s domain cards
and the footer nav both read from this one list now, removing a
duplication risk that existed across the prior two releases.

## A real bug, found and fixed during verification

Initial implementation of the footer nav caused a `KeyError:
'url_pathname'` crash on **every single page** when tested. Before
"fixing" it, I checked whether this was an actual production bug or a
testing-harness artifact — they require completely different fixes, and
guessing wrong would have meant either shipping a broken feature or
wasting effort removing working code.

**Root cause:** `st.page_link()` needs Streamlit's multipage manifest to
resolve a link target, and that manifest only exists when a page is
reached through the real entrypoint (`app.py`). My test harness had been
loading each `pages/*.py` file standalone via
`AppTest.from_file('pages/01_Hydraulics.py')` — which is how every page
in this project has been tested in every prior round, and worked fine
until a page itself started calling `st.page_link()` (previously only
`app.py` did). Loading a page standalone has no sibling-page context, so
the link target lookup fails — a testing-harness limitation, not a
production bug.

**Verified by testing the correct way**: `AppTest.from_file('app.py')` →
`at.switch_page('pages/01_Hydraulics.py')` → confirmed zero exceptions,
confirming this works correctly in actual deployment (where `app.py` is
always the entrypoint). Rewrote `.github/workflows/ci.yml` to use this
`switch_page` pattern for every page test going forward — the prior
CI file would have appeared to pass (it never tested cross-page
`page_link` calls before this round) but would have started failing
the moment this feature shipped, for a reason unrelated to the actual
code being broken. Caught and fixed before that could happen.

## Verification

1. 35 files syntax-checked, zero errors.
2. Landing page + all 12 pages re-tested via the corrected
   `switch_page` navigation pattern — 0 exceptions.
3. Caution banner and cross-page nav footer confirmed present via
   markdown-content inspection on all 12 pages, not just visually assumed.
4. All previously-verified live calculators (Pressure Drop, Orifice
   Plate, FUG, Z-factor, WHSV, PSV Gas) re-confirmed producing correct
   results through the corrected test pattern — same values as every
   prior round, zero regression from the theme/banner/nav changes.
5. CI workflow's exact steps run locally in full before being committed
   — all pass, including the two new checks (nav footer presence,
   corrected page-boot pattern).

## Files touched this round

- `utils/ui_components.py` — theme colors, `render_caution_banner()`,
  `render_domain_footer_nav()`
- `utils/tool_roadmap.py` — added `DOMAIN_PAGES` shared list
- `utils/runner.py` — wired both new render functions into the shared
  page-rendering loop, added `page_path` parameter
- `pages/*.py` (all 12) — one-line change each, passing `page_path=...`
  into `render_domain_page()`
- `.github/workflows/ci.yml` — rewritten to use `switch_page` correctly

## Running it

```bash
pip install -r requirements.txt
streamlit run app.py
```

Same plug-and-play protocol as before — nothing about adding new tools
changed this round.
