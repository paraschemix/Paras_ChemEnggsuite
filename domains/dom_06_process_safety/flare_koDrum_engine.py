"""
domains/dom_06_process_safety/flare_koDrum_engine.py
==========================================================
Phase 6C of the psv_safety_package upgrade (v10 track).
Flare header hydraulic check (Mach/backpressure) and KO drum sizing
(Souders-Brown with fixed API-typical K). Pure compute(), zero
Streamlit imports (Pattern A).

Live tools:
  ps_018  Flare Header Backpressure & Mach Number Check
  ps_019  Flare KO Drum Sizing (Souders-Brown, API-typical K)
"""

import math
from utils.tool_roadmap import ToolSpec, InputSpec
from utils.ui_components import check_positive, run_validators


# =======================================================================
# TOOL: FLARE HEADER BACKPRESSURE & MACH CHECK
# =======================================================================

def compute_flare_header_mach(values: dict) -> dict:
    w_lb_hr = values["w_lb_hr"]
    mw = values["mw"]
    t_r = values["t_r"]
    z = values["z"]
    p_line_psia = values["p_line_psia"]
    id_in = values["id_in"]
    is_header = values["segment_type"] == "header"

    has_error, has_warning, errors, warnings = run_validators(
        check_positive(w_lb_hr, "Mass flow"),
        check_positive(mw, "Molecular weight"),
        check_positive(t_r, "Temperature"),
        check_positive(p_line_psia, "Line pressure"),
        check_positive(id_in, "Pipe ID"),
    )
    if has_error:
        raise ValueError("; ".join(errors))

    r_specific = 1545.0 / mw  # ft-lbf/lbmol-R -> ft-lbf/lb-R
    rho_lb_ft3 = (p_line_psia * 144.0) / (r_specific * t_r * z)

    area_ft2 = math.pi / 4 * (id_in / 12.0) ** 2
    q_ft3_s = (w_lb_hr / 3600.0) / rho_lb_ft3
    v_ft_s = q_ft3_s / area_ft2

    k_ratio = 1.3  # typical light-HC/flare-gas isentropic exponent, fixed screening value
    g_c = 32.174
    c_sonic_ft_s = math.sqrt(k_ratio * g_c * r_specific * t_r)
    mach = v_ft_s / c_sonic_ft_s

    mach_limit = 0.7 if is_header else 0.5
    if mach > mach_limit:
        warnings.append(
            f"Mach {mach:.2f} exceeds the recommended limit of {mach_limit} for "
            f"{'flare headers' if is_header else 'long tailpipe/sub-header runs'} - "
            f"noise, vibration, and non-recoverable backpressure become significant; "
            f"increase line size."
        )

    return {
        "Gas Density at Line Conditions (lb/ft3)": round(rho_lb_ft3, 4),
        "Velocity (ft/s)": round(v_ft_s, 1),
        "Sonic Velocity (ft/s)": round(c_sonic_ft_s, 1),
        "Mach Number": round(mach, 3),
        "Mach Limit Applied": mach_limit,
        "Within Limit?": "YES" if mach <= mach_limit else "NO - RESIZE LINE",
        "_warnings": warnings,
    }


TOOL_FLARE_HEADER_MACH = ToolSpec(
    key="ps_018",
    title="Flare Header Backpressure & Mach Number Check",
    category="Flare System",
    description="Screening compressible-flow velocity/Mach check for flare headers and tailpipes against API 521 guidance limits.",
    inputs=[
        InputSpec("w_lb_hr", "Relief Gas Mass Flow (W)", default=50000.0, min_value=1.0,
                   quantity_kind="flow_mass", canonical_unit="lb/hr"),
        InputSpec("mw", "Gas Molecular Weight", default=44.0, min_value=2.0, unit="(lb/lbmol)"),
        InputSpec("t_r", "Flowing Temperature", default=600.0, min_value=1.0, unit="(degR)"),
        InputSpec("z", "Compressibility Factor (Z)", default=0.95, min_value=0.3, max_value=1.2, step=0.01),
        InputSpec("p_line_psia", "Line Pressure", default=20.0, min_value=0.5,
                   quantity_kind="pressure", canonical_unit="psia"),
        InputSpec("id_in", "Pipe Inside Diameter", default=12.0, min_value=1.0,
                   quantity_kind="length", canonical_unit="in"),
        InputSpec("segment_type", "Segment Type", default=0, input_type="select",
                   options=["header", "tailpipe"],
                   help="'header' = main flare header (Mach limit 0.7); 'tailpipe' = long sub-header/tailpipe run (Mach limit 0.5)."),
    ],
    compute=compute_flare_header_mach,
    formula_md=(
        r"$$\rho = \dfrac{P}{R_{specific}\,T\,Z}, \quad v=\dfrac{Q}{A}, \quad "
        r"c=\sqrt{k\,g_c\,R_{specific}\,T}, \quad Ma=\dfrac{v}{c}$$"
    ),
    references=["API Standard 521 - Pressure-relieving and Depressuring Systems (flare header velocity guidance)"],
    assumptions=[
        "Uses a fixed isentropic exponent k=1.3 as a representative flare-gas screening value - "
        "actual mixture k varies with composition; refine with real gas properties for final design.",
        "Single-point (single flow-rate, single-location) check - does not integrate the full "
        "network pressure-drop profile back to each PSV outlet; use dedicated flare-network "
        "hydraulics software for a complete backpressure study across all contributing sources.",
        "Constant Z, T, MW assumed along the segment - acceptable for a short segment screening "
        "check, not for long headers with significant property change along the run.",
    ],
)


# =======================================================================
# TOOL: FLARE KO DRUM SIZING (SOUDERS-BROWN, API-TYPICAL K)
# =======================================================================

def compute_ko_drum_sizing(values: dict) -> dict:
    w_vapor_lb_hr = values["w_vapor_lb_hr"]
    rho_vapor_lb_ft3 = values["rho_vapor_lb_ft3"]
    rho_liquid_lb_ft3 = values["rho_liquid_lb_ft3"]
    k_sb = values["k_sb"]
    liquid_holdup_min = values["liquid_holdup_min"]
    liquid_inflow_gpm = values["liquid_inflow_gpm"]
    orientation = values["orientation"]

    has_error, has_warning, errors, warnings = run_validators(
        check_positive(w_vapor_lb_hr, "Vapor mass flow"),
        check_positive(rho_vapor_lb_ft3, "Vapor density"),
        check_positive(rho_liquid_lb_ft3, "Liquid density"),
        check_positive(liquid_inflow_gpm, "Liquid inflow rate"),
    )
    if has_error:
        raise ValueError("; ".join(errors))
    if liquid_holdup_min < 20:
        warnings.append(
            "Liquid holdup time below 20 minutes - API 521 typically expects a 20-30 minute "
            "minimum emergency liquid retention capacity in a flare KO drum."
        )

    u_terminal_ft_s = k_sb * math.sqrt((rho_liquid_lb_ft3 - rho_vapor_lb_ft3) / rho_vapor_lb_ft3)
    q_vapor_ft3_s = (w_vapor_lb_hr / 3600.0) / rho_vapor_lb_ft3
    a_vapor_ft2 = q_vapor_ft3_s / u_terminal_ft_s

    if orientation == "vertical":
        diameter_ft = math.sqrt(4 * a_vapor_ft2 / math.pi)
        vessel_note = f"Minimum vessel ID for vapor disengagement: {diameter_ft:.2f} ft"
    else:
        # horizontal: assume vapor space is upper ~50% of a drum sized on L/D~4 heuristic,
        # solved from required vapor-flow area at superficial velocity u_terminal
        diameter_ft = math.sqrt(4 * (a_vapor_ft2 / 0.5) / math.pi)
        vessel_note = f"Minimum shell ID (vapor space ~50% of cross-section): {diameter_ft:.2f} ft"

    liquid_volume_ft3 = (liquid_inflow_gpm * liquid_holdup_min) / 7.4805
    liquid_volume_gal = liquid_inflow_gpm * liquid_holdup_min

    return {
        "Souders-Brown Terminal Velocity (ft/s)": round(u_terminal_ft_s, 3),
        "Required Vapor Disengagement Area (ft2)": round(a_vapor_ft2, 2),
        "Vessel Sizing Note": vessel_note,
        "Minimum Diameter (ft)": round(diameter_ft, 2),
        "Required Liquid Holdup Volume (ft3)": round(liquid_volume_ft3, 1),
        "Required Liquid Holdup Volume (gal)": round(liquid_volume_gal, 0),
        "_warnings": warnings,
    }


TOOL_KO_DRUM_SIZING = ToolSpec(
    key="ps_019",
    title="Flare KO Drum Sizing (Souders-Brown)",
    category="Flare System",
    description="Vapor-liquid disengagement sizing (Souders-Brown terminal velocity) plus minimum emergency liquid holdup for a flare knock-out drum.",
    inputs=[
        InputSpec("w_vapor_lb_hr", "Vapor Mass Flow to Flare", default=50000.0, min_value=1.0,
                   quantity_kind="flow_mass", canonical_unit="lb/hr"),
        InputSpec("rho_vapor_lb_ft3", "Vapor Density", default=0.3, min_value=0.001, unit="(lb/ft3)"),
        InputSpec("rho_liquid_lb_ft3", "Entrained Liquid Density", default=45.0, min_value=1.0, unit="(lb/ft3)"),
        InputSpec("k_sb", "Souders-Brown K Factor", default=0.15, min_value=0.05, max_value=0.35, step=0.01,
                   help="API-typical fixed value for a horizontal/vertical KO drum without a mist eliminator; "
                        "~0.15 ft/s targets ~300-600 micron droplet removal per API 521 guidance."),
        InputSpec("liquid_holdup_min", "Required Liquid Holdup Time", default=20.0, min_value=1.0, unit="(min)",
                   help="API 521 typical range 20-30 minutes for emergency liquid retention."),
        InputSpec("liquid_inflow_gpm", "Liquid Inflow Rate (governing case)", default=50.0, min_value=0.1, unit="(USGPM)"),
        InputSpec("orientation", "Drum Orientation", default=0, input_type="select",
                   options=["horizontal", "vertical"]),
    ],
    compute=compute_ko_drum_sizing,
    formula_md=(
        r"$$U_v = K\sqrt{\dfrac{\rho_l-\rho_g}{\rho_g}}, \quad A_{vapor}=\dfrac{Q_g}{U_v}$$"
    ),
    references=[
        "API Standard 521 - Pressure-relieving and Depressuring Systems (KO drum sizing)",
        "Souders, M. & Brown, G.G. (1934) - vapor-liquid disengagement velocity correlation",
    ],
    assumptions=[
        "Uses a FIXED, API-typical Souders-Brown K value (no droplet-size/drag-coefficient "
        "iteration) - a deliberate screening-level simplification; droplet cut sizes below "
        "~300 microns require a mist eliminator and a different K basis, not covered here.",
        "Horizontal-drum vapor area assumes a simple 50% cross-section vapor-space heuristic, "
        "not a rigorous liquid-level/chord-area solve - refine with actual operating liquid "
        "level for final vessel data sheet dimensions.",
        "Liquid holdup volume is a simple inflow-rate x time calculation - does not include "
        "nozzle/inlet momentum, high-liquid-level trip elevation, or L/D ratio optimization.",
    ],
)


REGISTRY: dict[str, ToolSpec] = {
    TOOL_FLARE_HEADER_MACH.key: TOOL_FLARE_HEADER_MACH,
    TOOL_KO_DRUM_SIZING.key: TOOL_KO_DRUM_SIZING,
}
