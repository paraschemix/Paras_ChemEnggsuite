"""
calculators/tool_roadmap.py
==============================
Static master list of all 51 tools from the "Paras Chemical Engineering
Calc Suite" roadmap, organized by domain. This powers:
  - the categorized sidebar navigation (grouped by domain),
  - the global search bar (search should surface planned tools too, not
    just live ones, so users/stakeholders can see the full roadmap),
  - the "Live" / "Coming Soon" status badges on the landing page.

Each entry's `key` matches the ToolSpec.key used in the relevant engine's
REGISTRY *if and only if* that tool has been implemented — this file is
cross-referenced against the live registries at import time in app.py to
determine live/planned status, so this list itself never needs a manual
"is it done yet" flag that could drift out of sync with the actual code.
"""

from dataclasses import dataclass


@dataclass
class RoadmapEntry:
    key: str            # matches a ToolSpec.key once implemented, else a stable placeholder id
    number: int          # position in the original 50+ roadmap
    title: str
    domain: str           # domain label, matches DOMAIN_REGISTRIES keys in app.py


ROADMAP: list[RoadmapEntry] = [
    # --- Domain A: Fluid Dynamics & Hydraulics (10) ---
    RoadmapEntry("fd_001", 1, "Single-Phase Pipe Pressure Drop (Darcy-Weisbach)", "🌊 Fluid Dynamics & Hydraulics"),
    RoadmapEntry("fd_planned_02", 2, "Two-Phase Pressure Drop (Lockhart-Martinelli)", "🌊 Fluid Dynamics & Hydraulics"),
    RoadmapEntry("fd_003", 3, "Pump NPSH (Available vs Required) & System Curve", "🌊 Fluid Dynamics & Hydraulics"),
    RoadmapEntry("fd_002ab", 4, "Control Valve Sizing (ISA-75, Liquid/Gas & Cavitation)", "🌊 Fluid Dynamics & Hydraulics"),
    RoadmapEntry("fd_planned_05", 5, "Compressor Polytropic & Isentropic Head / Power", "🌊 Fluid Dynamics & Hydraulics"),
    RoadmapEntry("fd_006", 6, "Water Hammer & Surge Pressure Peak Analysis", "🌊 Fluid Dynamics & Hydraulics"),
    RoadmapEntry("fd_planned_07", 7, "Orifice Plate & Flowmeter Sizing (ISO 5167)", "🌊 Fluid Dynamics & Hydraulics"),
    RoadmapEntry("fd_planned_08", 8, "Settling Velocity & Drag Coefficient (Stokes/Newton)", "🌊 Fluid Dynamics & Hydraulics"),
    RoadmapEntry("fd_planned_09", 9, "Eductor / Jet Pump Sizing", "🌊 Fluid Dynamics & Hydraulics"),
    RoadmapEntry("fd_planned_10", 10, "Pipe Wall Thickness Calculation (ASME B31.3)", "🌊 Fluid Dynamics & Hydraulics"),

    # --- Domain B: Mass Transfer & Aromatics Processing (10) ---
    RoadmapEntry("mt_011", 11, "Shortcut Distillation (Fenske-Underwood-Gilliland)", "⚗️ Mass Transfer & Aromatics"),
    RoadmapEntry("mt_planned_12", 12, "Distillation Tray Hydraulics (Weeping, Flooding, Entrainment)", "⚗️ Mass Transfer & Aromatics"),
    RoadmapEntry("mt_planned_13", 13, "Packed Bed HETP & Pressure Drop", "⚗️ Mass Transfer & Aromatics"),
    RoadmapEntry("mt_planned_14", 14, "Flash Drum / V-L Separator Sizing (Souders-Brown)", "⚗️ Mass Transfer & Aromatics"),
    RoadmapEntry("mt_planned_15", 15, "Liquid-Liquid Decanter Sizing", "⚗️ Mass Transfer & Aromatics"),
    RoadmapEntry("mt_planned_16", 16, "Gas Absorption / Stripping Factor Calculation", "⚗️ Mass Transfer & Aromatics"),
    RoadmapEntry("mt_planned_17", 17, "Benzene/Toluene/Xylene (BTX) Fractionation Estimator", "⚗️ Mass Transfer & Aromatics"),
    RoadmapEntry("mt_planned_18", 18, "Solvent Extraction Stage Calculator", "⚗️ Mass Transfer & Aromatics"),
    RoadmapEntry("mt_planned_19", 19, "Reflux Ratio Optimization vs Utility Cost", "⚗️ Mass Transfer & Aromatics"),
    RoadmapEntry("mt_planned_20", 20, "Minimum Vapor Velocity for Entrainment Prevention", "⚗️ Mass Transfer & Aromatics"),

    # --- Domain C: Heat Transfer (8) ---
    RoadmapEntry("ht_planned_21", 21, "Shell-and-Tube LMTD Correction Factor (Ft)", "🔥 Heat Transfer"),
    RoadmapEntry("ht_planned_22", 22, "Shell-and-Tube Overall Heat Transfer Coefficient (U) Estimator", "🔥 Heat Transfer"),
    RoadmapEntry("ht_planned_23", 23, "Air-Cooled Heat Exchanger (Fin-Fan) Sizing", "🔥 Heat Transfer"),
    RoadmapEntry("ht_planned_24", 24, "Insulation Thickness & Heat Loss Optimizer", "🔥 Heat Transfer"),
    RoadmapEntry("ht_planned_25", 25, "Heat Tracing Steam/Electrical Requirements", "🔥 Heat Transfer"),
    RoadmapEntry("ht_planned_26", 26, "Fouling Factor Impact Calculator", "🔥 Heat Transfer"),
    RoadmapEntry("ht_planned_27", 27, "Steam Desuperheater / Attemperator Sizing", "🔥 Heat Transfer"),
    RoadmapEntry("ht_planned_28", 28, "Cooling Tower Makeup & Blowdown Rate", "🔥 Heat Transfer"),

    # --- Domain D: Kinetics, Reactors & Catalysis (7) ---
    RoadmapEntry("kr_planned_29", 29, "Power Law Kinetic Parameter Regression (Arrhenius)", "⚛️ Kinetics, Reactors & Catalysis"),
    RoadmapEntry("kr_planned_30", 30, "Catalyst Deactivation Modeling (Time-on-stream vs Activity)", "⚛️ Kinetics, Reactors & Catalysis"),
    RoadmapEntry("kr_planned_31", 31, "Continuous Stirred-Tank Reactor (CSTR) Sizing", "⚛️ Kinetics, Reactors & Catalysis"),
    RoadmapEntry("kr_planned_32", 32, "Plug Flow Reactor (PFR) Sizing", "⚛️ Kinetics, Reactors & Catalysis"),
    RoadmapEntry("kr_planned_33", 33, "Space Velocity Calculator (WHSV & LHSV)", "⚛️ Kinetics, Reactors & Catalysis"),
    RoadmapEntry("kr_planned_34", 34, "Residence Time Distribution (RTD) Variance", "⚛️ Kinetics, Reactors & Catalysis"),
    RoadmapEntry("kr_planned_35", 35, "Adiabatic Temperature Rise in Reactors", "⚛️ Kinetics, Reactors & Catalysis"),

    # --- Domain E: Utilities, Environmental & Water Treatment (7) ---
    RoadmapEntry("uw_planned_36", 36, "Total Organic Carbon (TOC) Analytics", "💧 Utilities & Water Treatment"),
    RoadmapEntry("uw_planned_37", 37, "TOC to BOD/COD Correlation & Conversion", "💧 Utilities & Water Treatment"),
    RoadmapEntry("uw_planned_38", 38, "Instrument Air Consumption Estimator", "💧 Utilities & Water Treatment"),
    RoadmapEntry("uw_planned_39", 39, "Flare Header Backpressure & Mach Number", "💧 Utilities & Water Treatment"),
    RoadmapEntry("uw_planned_40", 40, "Boiler Feed Water (BFW) Preheating Economics", "💧 Utilities & Water Treatment"),
    RoadmapEntry("uw_planned_41", 41, "Condensate Recovery Flash Steam Rate", "💧 Utilities & Water Treatment"),
    RoadmapEntry("uw_planned_42", 42, "Demineralized Water Ion Exchange Capacity", "💧 Utilities & Water Treatment"),

    # --- Domain F: Thermodynamics & Physical Properties (9) ---
    RoadmapEntry("tp_planned_43", 43, "Equations of State (PR/SRK) Z-Factor Calculator", "🧪 Thermodynamics & Physical Properties"),
    RoadmapEntry("tp_planned_44", 44, "Vapor Pressure Calculator (Antoine Equation)", "🧪 Thermodynamics & Physical Properties"),
    RoadmapEntry("tp_planned_45", 45, "Bubble Point & Dew Point Iteration", "🧪 Thermodynamics & Physical Properties"),
    RoadmapEntry("tp_planned_46", 46, "API Gravity & Specific Gravity Conversions", "🧪 Thermodynamics & Physical Properties"),
    RoadmapEntry("tp_planned_47", 47, "Viscosity Blending Index", "🧪 Thermodynamics & Physical Properties"),
    RoadmapEntry("tp_planned_48", 48, "Lower/Upper Flammability Limits (LFL/UFL) of Mixtures", "🧪 Thermodynamics & Physical Properties"),
    RoadmapEntry("tp_planned_49", 49, "API 520 PRV Sizing (Subcritical/Critical Gas & Liquid)", "🧪 Thermodynamics & Physical Properties"),
    RoadmapEntry("tp_planned_50", 50, "Thermal Expansion of Liquids in Blocked Pipes (API 521)", "🧪 Thermodynamics & Physical Properties"),
    RoadmapEntry("tp_planned_51", 51, "Specific Heat Capacity Polynomial Interpolator", "🧪 Thermodynamics & Physical Properties"),
]


def get_domain_order() -> list[str]:
    """Returns domain labels in roadmap order (dict preserves insertion order in Py3.7+)."""
    seen = []
    for entry in ROADMAP:
        if entry.domain not in seen:
            seen.append(entry.domain)
    return seen
