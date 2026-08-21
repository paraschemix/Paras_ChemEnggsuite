"""
utils/tool_roadmap.py
=======================
Central Registry (Pattern A). Two things live here, by design:

1. `ToolSpec` / `InputSpec` — the dataclasses every domain engine uses to
   register a live, working tool (inputs, a pure `compute()` function,
   and documentation metadata). Placed here rather than a separate
   `registry_base.py` because this file's job description ("Step 2: add
   one ToolSpec dictionary entry into utils/tool_roadmap.py") already
   makes it the natural home for the type those entries are built from.

2. `ROADMAP` — the full master taxonomy list (260 individually-named
   tools across 12 domains, transcribed from the source taxonomy
   document — see the prior delivery's `_roadmap_generator.py` for the
   transcription; unchanged here except domain labels were remapped to
   this release's `dom_XX_*` folder scheme). Cross-referenced against
   each domain's live `REGISTRY` at runtime in app.py to flag Live vs
   Coming Soon.

Plug-and-play protocol: adding a new tool = (1) write compute() + a
ToolSpec in the relevant domains/dom_XX_*/*.py file, add it to that
module's REGISTRY dict; (2) add one matching RoadmapEntry here (same
key) so it flips from "Coming Soon" to "Live" everywhere automatically
— search, domain cards, the page itself.
"""

from dataclasses import dataclass, field
from typing import Callable, Optional, Any


# =======================================================================
# ToolSpec / InputSpec — the live-tool registration contract
# =======================================================================

@dataclass
class InputSpec:
    name: str                      # dict key passed into compute()
    label: str                     # UI label
    default: float                 # default value shown in the widget
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    step: Optional[float] = None
    unit: str = ""                 # appended to label for display, e.g. "(psia)"
    help: str = ""                 # tooltip
    input_type: str = "number"     # "number" | "select"
    options: Optional[list] = None  # required if input_type == "select"

    def display_label(self) -> str:
        return f"{self.label} {self.unit}".strip() if self.unit else self.label


@dataclass
class ToolSpec:
    key: str                                   # unique registry key, e.g. "fd_001"
    title: str                                  # display name in search/selectbox
    category: str                               # sub-grouping within the domain page
    description: str                            # one-line summary shown under the title
    inputs: list[InputSpec]
    compute: Callable[[dict[str, Any]], dict[str, Any]]
    formula_md: str
    references: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    validate: Optional[Callable[[dict[str, Any]], list]] = None


# =======================================================================
# RoadmapEntry — the master taxonomy list entry (live or planned)
# =======================================================================

@dataclass
class RoadmapEntry:
    key: str            # matches a ToolSpec.key once implemented, else a stable placeholder id
    number: int          # position in the master roadmap
    title: str
    domain: str           # domain label, matches DOMAIN_REGISTRIES keys in app.py


# Domain labels match the dom_XX_* folder scheme used in this release.
# NOTE on dom_07 and dom_12 — see README "Known mapping gaps": the source
# taxonomy document's 12 domains don't map 1:1 onto this release's 12
# folder names. dom_07_equipment_sizing and dom_12_environmental don't
# correspond to any single domain in the original document, so they
# currently carry NO roadmap entries rather than a guessed-at list.
# Flag preferred content for these two and they'll be populated properly.
DOMAIN_LABELS = {
    1: "🔧 Hydraulics",
    2: "⚛️ Thermodynamics",
    3: "🔥 Heat Transfer",
    4: "⚗️ Mass Transfer",
    5: "🧪 Reaction Engineering",
    6: "🛡️ Process Safety",
    7: "⚙️ Equipment Sizing",
    8: "🪨 Solids Handling",
    9: "💧 Utility Systems",
    10: "📡 Instrumentation & Control",
    11: "💰 Economics & Optimization",
    12: "🌍 Environmental & Energy",
}

# ---------------------------------------------------------------------
# Source taxonomy tool lists (unchanged transcription from the master
# document), domain-by-domain, mapped onto the new dom_XX labels above.
# dom_07 (Equipment Sizing) and dom_12 (Environmental & Energy) are
# intentionally left with only the tools that had an unambiguous fit
# (see notes inline) rather than a full invented list.
# ---------------------------------------------------------------------
_DOMAIN_1_BULLETS = [
    "Liquid pipe sizing (Darcy-Weisbach), compressible gas line sizing (Isothermal/Adiabatic), Hazen-Williams water line calculator, equivalent length (L/D) fitting estimator, pipe roughness & Colebrook-White friction factor solver, Crane TP-410 2-K and 3-K resistance factors",
    "Two-phase pressure drop (Lockhart-Martinelli), horizontal multiphase flow regime mapper (Baker chart), vertical multiphase flow regime mapper (Taitel-Dukler), Beggs & Brill multiphase piping solver, slug flow frequency & liquid holdup calculator, erosion-corrosion velocity limits (API RP 14E)",
    "Pump total dynamic head (TDH) & power rating, Net Positive Suction Head (NPSHa/NPSHr) margin estimator, pump affinity laws scaling tool, multi-pump parallel/series curve overlay, viscosity correction for centrifugal pumps (Hydraulic Institute), positive displacement pump slip & flow sizing",
    "Centrifugal compressor head & power (Polytropic vs. Isentropic), multi-stage compression with intercooling optimizer, reciprocating compressor volumetric efficiency & rod load, compressor surge line margin predictor, blower performance & air density correction",
    "Water hammer / surge pressure wave analyzer, network hydraulic solver (Hardy-Cross pipe loop analysis), control valve sizing for liquids/gases/steam (ISA-75.01 standard), orifice plate differential pressure calculator (ISO 5167), Venturi tube & flow nozzle design, Rotameter calibration & gas density corrector, pitot tube traverse flow integrator",
]
_DOMAIN_2_BULLETS = [
    "Peng-Robinson EOS PT/PV flash solver, Soave-Redlich-Kwong (SRK) EOS calculator, Benedict-Webb-Rubin-Starling (BWRS) gas property estimator, PC-SAFT polymer phase equilibrium engine, compressibility factor (Z) calculator (Standing-Katz / Hall-Yarborough)",
    "NRTL binary parameter estimator, UNIQUAC activity coefficient solver, UNIFAC group-contribution property predictor, Wilson equation VLE fitting tool, van Laar & Margules activity model solvers",
    "Isothermal PT flash calculator, Adiabatic HP flash (Joule-Thomson expansion), Bubble point pressure & temperature solver, Dew point pressure & temperature solver, Liquid-Liquid Equilibrium (LLE) tie-line generator, Solid-Liquid Equilibrium (SLE) solubility curve solver, supercritical fluid density & solubility calculator",
    "Temperature-dependent liquid density (Costald), gas viscosity estimation (Chapman-Enskog), liquid mixture viscosity (Lobe / Grunberg-Nissan), thermal conductivity predictor (liquids & gases), surface tension mixture estimator, gas diffusivity in liquids (Wilke-Chang equation)",
    "ASME steam tables (IAPWS-IF97), psychrometric chart & air property calculator, flue gas dew point & acid gas condensation solver",
]
_DOMAIN_3_BULLETS = [
    "Exchanger thermal rating (Kern method), Bell-Delaware detailed shell-side hydraulics, Log Mean Temperature Difference (LMTD) & F-factor corrector, epsilon-NTU effectiveness solver, fouling resistance impact predictor, tube-side pressure drop & velocity calculator, exchanger tube vibration analyzer (cross-flow / vortex shedding)",
    "Air cooler duty & face velocity sizing, finned tube heat transfer coefficient estimator, fan static pressure & power draft calculator, ambient air temperature derating estimator",
    "Plate Heat Exchanger (PHE) chevron angle rating, spiral heat exchanger design for slurries, double-pipe exchanger rating, jacketed vessel heat transfer coefficient solver",
    "Furnace radiant section heat flux density solver, convective section design & draft loss, fuel gas combustion efficiency & stack loss, Excess air vs. O2/CO2 analyzer, burner heat release rate & flue gas volume generator",
    "Kettle & thermosyphon reboiler design, shell-side condenser thermal rating, in-tube condensation heat transfer (Dukas-Muller), falling film evaporator rating",
    "Multi-layer pipe insulation thickness optimizer, bare metal surface heat loss (Radiation + Convection), personnel burn protection temperature calculator",
]
_DOMAIN_4_BULLETS = [
    "McCabe-Thiele binary stage counter, Fenske-Underwood-Gilliland (FUG) shortcut distillation design, minimum reflux ratio (Rmin) estimator, column hydraulic tray rating (Sieve, Valve, Bubble Cap), jet flooding & downcomer backup analyzer, packed column diameter & HETP solver, pressure drop across packing (GPDC chart / Stichlmair model), reactive distillation equilibrium module, batch distillation time-cut optimizer",
    "Kremser method for absorber/stripper theoretical stages, gas absorption column height (NOG, HOG), amine gas treating solvent circulation estimator, acid gas removal efficiency module, sour water stripper performance estimator",
    "Ternary liquid extraction stage calculator, mixer-settler design & dispersion band thickness, extraction column diameter & flood point solver, solvent-to-feed (S/F) ratio optimizer",
    "Fixed-bed adsorption breakthrough curve generator, bed length of unused bed (LUB) calculator, pressure drop in granular beds (Ergun equation), ion exchange vessel sizing & regeneration mass balance",
    "Rotary dryer mass & heat balance, spray dryer droplet evaporation time, psychrometric drying air requirement tool, crystallization yield & magma density solver, cooling crystallizer supersaturation profile generator",
    "Reverse Osmosis (RO) flux & salt rejection calculator, gas separation membrane permeate purity predictor, ultrafiltration/microfiltration cake resistance estimator",
]
_DOMAIN_5_BULLETS = [
    "Continuous Stirred Tank Reactor (CSTR) volume solver, Plug Flow Reactor (PFR) volume & conversion calculator, batch reactor cycle time & conversion solver, CSTRs-in-series cascade simulator",
    "Arrhenius equation parameter solver (Ea, A), differential & integral method kinetic order fitting, Langmuir-Hinshelwood rate expression calculator, power-law kinetic fitting tool",
    "Thiele modulus & internal effectiveness factor (eta), Mears criterion for external mass transfer resistance, Weisz-Prater criterion for internal diffusion resistance, packed bed catalytic reactor pressure drop (Ergun), catalyst deactivation kinetics solver (coking/poisoning)",
    "Reactor heat generation vs. removal curve overlay, adiabatic temperature rise (dTad) solver, runaway reaction threshold analysis, Semenov / Frank-Kamenetskii thermal explosion limit tool",
    "Monod cell growth kinetics calculator, oxygen transfer rate (OTR) & volumetric mass transfer coefficient (kLa) solver, bioreactor agitation power input calculator",
]
_DOMAIN_6_BULLETS = [
    "API 520 vapor/gas PSV orifice sizing, API 520 liquid PSV orifice sizing, API 520 steam PSV sizing, API 2000 low-pressure tank venting (Emergency/Normal), thermal expansion liquid relief valve sizing, two-phase flow PSV sizing (DIERS / Omega method), PSV backpressure correction factor (Kw, Kb) solver, inlet pipe pressure drop check (3% rule)",
    "Flare stack height & thermal radiation contours (API 521), flare tip noise level predictor, vessel blowdown rate & temperature drop calculator, flare knockout drum sizing (Vertical/Horizontal), flare header hydraulic network calculator",
    "Gaussian plume atmospheric dispersion solver, heavy gas dispersion model (Britter-McQuaid), vapor cloud explosion (VCE) overpressure estimator (TNT equivalent / TNO Multi-Energy), BLEVE thermal radiation dose calculator, pool fire heat flux & burning rate calculator",
    "Layers of Protection Analysis (LOPA) risk reduction calculator, Safety Integrity Level (SIL) target calculator, HAZOP action item tracking matrix, Quantitative Risk Assessment (QRA) Individual Risk (IR) metric generator",
]
_DOMAIN_8_BULLETS = [
    "Particle size distribution (Sauter mean diameter d32), Rosin-Rammler distribution curve fitter, Bond Work Index grinding power estimator, jaw crusher & ball mill throughput calculator",
    "Minimum fluidization velocity (umf) calculator, terminal settling velocity of particles (Stokes / Allen / Newton regimes), pneumatic conveying pressure drop & saltation velocity, cyclone separator collection efficiency (Lapple / Leith-Licht)",
    "Hydrocyclone performance curve estimator, continuous thickener area sizing (Coe-Clevenger method), rotary vacuum filter yield & cycle time solver, baghouse filter area & air-to-cloth ratio estimator, centrifuge G-force & cake dryness estimator",
    "Hopper angle & discharge rate solver (Jenike method), silo minimum arching & piping dimension calculator, bulk solid density & compressibility index estimator",
]
_DOMAIN_9_BULLETS = [
    "Steam boiler efficiency (Direct & Indirect methods), steam pressure reducing valve (PRV) desuperheater balance, steam trap capacity & flash steam recovery generator, condensate pipe diameter & two-phase return line solver, deaerator mass & energy balance",
    "Cooling tower evaporation, blowdown, and drift loss calculator, cycles of concentration (COC) optimizer, Langelier Saturation Index (LSI) & Ryznar Stability Index (RSI) water scaling calculator, cooling water dosing estimator",
    "Air compressor power & receiver tank sizing, compressed air piping network pressure drop, pressure swing adsorption (PSA) nitrogen generator rating, air dryer dew point & purge loss estimator",
    "Composite curves & Grand Composite Curve (GCC) generator, minimum hot/cold utility target calculator, heat exchanger network (HEN) pinch temperature finder, cogeneration (CHP) fuel utilization efficiency solver",
]
_DOMAIN_10_BULLETS = [
    "First-order plus dead time (FOPDT) system step response generator, second-order underdamped/overdamped dynamic solver, dead-time (transport delay) approximation tool (Pade approximation)",
    "Ziegler-Nichols open/closed loop tuning calculator, Cohen-Coon controller parameter generator, Internal Model Control (IMC) tuning rules solver, AMIGO PID parameter calculator",
    "Bode plot stability analyzer (Gain & Phase margin), Nyquist diagram generator, root locus trajectory plotter, control valve installed flow characteristic curve analyzer",
    "First-order exponential filter / moving average parameter, soft sensor linear regression / PLS estimator, multivariable loop interaction matrix (Relative Gain Array - RGA)",
]
_DOMAIN_11_BULLETS = [
    "Equipment bare module cost estimator (Guthrie method), capacity exponent scaling calculator, Chemical Engineering Plant Cost Index (CEPCI) escalation corrector, Lang factors plant cost estimator",
    "Net Present Value (NPV) & Internal Rate of Return (IRR) calculator, discounted payback period solver, levelized cost of production (LCOP/LCOE/LCOH) estimator, sensitivity / tornado plot generator for economic variables",
    "Single-variable non-linear optimizer (Golden section / Newton-Raphson), linear programming (LP) blend optimizer, Multi-Variable Mixed Integer Linear Programming (MILP) utility matcher",
]
# dom_12_environmental: only the Clean Energy & Green Technology bullet
# from the old "Sector-Specific" domain, plus the old Domain 11's
# carbon/sustainability bullet, are an unambiguous fit for "Environmental
# & Energy." The rest of old Domain 11 (refining, polymers, pharma) and
# ALL of old Domain 12 (Operations Diagnostics & Reliability) have no
# confirmed home in this 12-slot scheme — see README.
_DOMAIN_12_BULLETS = [
    "Process carbon footprint (tCO2e per ton of product) calculator, Scope 1 & Scope 2 greenhouse gas emissions tracker, Life Cycle Assessment (LCA) mass impact evaluator",
    "Water electrolyzer power requirement & hydrogen yield calculator, Carbon Capture Amine/Solvent mass balance, biomass gasification syngas composition predictor, fuel cell power & oxygen consumption solver",
]

_DOMAIN_BULLET_MAP = {
    1: _DOMAIN_1_BULLETS, 2: _DOMAIN_2_BULLETS, 3: _DOMAIN_3_BULLETS,
    4: _DOMAIN_4_BULLETS, 5: _DOMAIN_5_BULLETS, 6: _DOMAIN_6_BULLETS,
    7: [],  # dom_07_equipment_sizing - no confirmed source content, see README
    8: _DOMAIN_8_BULLETS, 9: _DOMAIN_9_BULLETS, 10: _DOMAIN_10_BULLETS,
    11: _DOMAIN_11_BULLETS, 12: _DOMAIN_12_BULLETS,
}

_DOMAIN_PREFIX_MAP = {
    1: "hy", 2: "tp", 3: "ht", 4: "mt", 5: "kr", 6: "ps",
    7: "eq", 8: "sh", 9: "ut", 10: "ic", 11: "ec", 12: "en",
}

# Tools with real compute() logic behind them, mapped by exact title
# match to their live ToolSpec.key (cross-domain, so this lookup is
# domain-agnostic).
_LIVE_TOOL_KEY_MAP = {
    "Liquid pipe sizing (Darcy-Weisbach)": "hy_001",
    "control valve sizing for liquids/gases/steam (ISA-75.01 standard)": "hy_002ab",
    "Net Positive Suction Head (NPSHa/NPSHr) margin estimator": "hy_003",
    "Water hammer / surge pressure wave analyzer": "hy_006",
    "orifice plate differential pressure calculator (ISO 5167)": "hy_007",
    "Fenske-Underwood-Gilliland (FUG) shortcut distillation design": "mt_011",
}


def _build_roadmap() -> list[RoadmapEntry]:
    entries = []
    counter = 1
    for domain_num in range(1, 13):
        label = DOMAIN_LABELS[domain_num]
        prefix = _DOMAIN_PREFIX_MAP[domain_num]
        bullets = _DOMAIN_BULLET_MAP[domain_num]
        for bullet in bullets:
            tools = [t.strip() for t in bullet.split(", ")]
            for tool_title in tools:
                live_key = _LIVE_TOOL_KEY_MAP.get(tool_title)
                key = live_key if live_key else f"{prefix}_planned_{counter:03d}"
                safe_title = tool_title.replace('"', "'")
                entries.append(RoadmapEntry(key, counter, safe_title, label))
                counter += 1
    return entries


ROADMAP: list[RoadmapEntry] = _build_roadmap()


def get_domain_order() -> list[str]:
    """Returns domain labels 1-12 in order (not roadmap-content order, so
    empty domains like dom_07 still appear in navigation)."""
    return [DOMAIN_LABELS[i] for i in range(1, 13)]
