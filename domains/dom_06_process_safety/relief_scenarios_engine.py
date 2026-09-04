"""
domains/dom_06_process_safety/relief_scenarios_engine.py
==========================================================
Phase 6A of the psv_safety_package upgrade (v10 track).
Governing relief LOAD scenarios (W or Q) per API 521/2000 - feeds into
orifice_sizing_engine.py's area equations. Pure compute(), zero
Streamlit imports (Pattern A).

Live tools:
  ps_011  Fire Case - Wetted Vessel (API 521 heat input + latent-heat relief load)
  ps_012  Fire Case - Gas/Non-Wetted Vessel (API 521 bare-metal heat absorption)
  ps_013  Blocked Discharge Relief Load (rated pump/compressor flow passthrough)
  ps_014  Thermal Expansion of Trapped Liquid (blocked-in line/HX)
  ps_015  Heat Exchanger Tube Rupture Relief Load (two-ended shear area basis)
"""

import math
from utils.tool_roadmap import ToolSpec, InputSpec
from utils.ui_components import check_positive, run_validators


# =======================================================================
# TOOL: FIRE CASE - WETTED VESSEL (API 521)
# =======================================================================

def compute_fire_wetted(values: dict) -> dict:
    """Q = 21000*F*A_wetted^0.82 (Btu/hr, A in ft2) ; W = Q / latent_heat"""
    diameter_ft = values["diameter_ft"]
    wetted_height_ft = values["wetted_height_ft"]
    f_factor = values["f_factor"]
    latent_heat_btu_lb = values["latent_heat_btu_lb"]

    has_error, has_warning, errors, warnings = run_validators(
        check_positive(diameter_ft, "Vessel diameter"),
        check_positive(wetted_height_ft, "Wetted height"),
        check_positive(latent_heat_btu_lb, "Latent heat"),
    )
    if has_error:
        raise ValueError("; ".join(errors))
    if wetted_height_ft > 25.0:
        warnings.append(
            "Wetted height exceeds 25 ft (7.6 m) - API 521 caps the credited fire-exposure "
            "height at this value; using the full height overstates A_wetted."
        )
    wetted_height_ft = min(wetted_height_ft, 25.0)

    a_wetted_ft2 = math.pi * diameter_ft * wetted_height_ft
    q_btu_hr = 21000 * f_factor * a_wetted_ft2 ** 0.82
    w_lb_hr = q_btu_hr / latent_heat_btu_lb

    return {
        "Wetted Area (ft2)": round(a_wetted_ft2, 1),
        "Fire Heat Input Q (Btu/hr)": round(q_btu_hr, 0),
        "Required Relief Load W (lb/hr)": round(w_lb_hr, 1),
        "_warnings": warnings,
    }


TOOL_FIRE_WETTED = ToolSpec(
    key="ps_011",
    title="Fire Case - Wetted Vessel Relief Load (API 521)",
    category="Relief Load Scenarios",
    description="Fire-exposure heat input and vapor-generation relief load for a wetted vessel (vertical/horizontal).",
    inputs=[
        InputSpec("diameter_ft", "Vessel Diameter", default=8.0, min_value=0.5,
                   quantity_kind="length", canonical_unit="ft"),
        InputSpec("wetted_height_ft", "Wetted Height (liquid-contacted)", default=15.0, min_value=0.5, max_value=25.0,
                   quantity_kind="length", canonical_unit="ft",
                   help="Capped at 25 ft (7.6 m) per API 521 credited fire-exposure height."),
        InputSpec("f_factor", "Environmental Factor (F)", default=1.0, min_value=0.025, max_value=1.0, step=0.005,
                   help="1.0 for bare vessel, no drainage/fire-fighting credit; lower values require documented insulation/drainage credit per API 521 Table."),
        InputSpec("latent_heat_btu_lb", "Latent Heat of Vaporization", default=150.0, min_value=1.0, unit="(Btu/lb)"),
    ],
    compute=compute_fire_wetted,
    formula_md=r"$$Q = 21000\,F\,A_{wetted}^{0.82}, \quad W = \dfrac{Q}{\lambda}$$",
    references=["API Standard 521 - Pressure-relieving and Depressuring Systems"],
    assumptions=[
        "Uses the API 521 non-metric empirical constant (21000) with area in ft2 - a screening-level "
        "correlation, not a substitute for a full fire-radiation heat-transfer model.",
        "Assumes cylindrical shell wetted area only (pi*D*H) - excludes bottom-head contribution; "
        "add head area separately for a more exact vertical-vessel case.",
        "F=1.0 (no credit) is conservative default - any reduced F requires the specific insulation/"
        "drainage/fireproofing basis to be documented and defensible in a HAZOP/relief-system review.",
    ],
)


# =======================================================================
# TOOL: FIRE CASE - GAS/NON-WETTED VESSEL (API 521)
# =======================================================================

def compute_fire_gas_nonwetted(values: dict) -> dict:
    """Q = 43.2*F*A_bare^0.82 (Btu/hr); vapor mass relief via ideal-gas thermal expansion."""
    a_bare_ft2 = values["a_bare_ft2"]
    f_factor = values["f_factor"]
    cp_btu_lb_r = values["cp_btu_lb_r"]
    delta_t_r = values["delta_t_r"]

    has_error, has_warning, errors, warnings = run_validators(
        check_positive(a_bare_ft2, "Bare metal area"),
        check_positive(cp_btu_lb_r, "Vapor Cp"),
        check_positive(delta_t_r, "Temperature rise"),
    )
    if has_error:
        raise ValueError("; ".join(errors))

    q_btu_hr = 43.2 * f_factor * a_bare_ft2 ** 0.82
    w_lb_hr = q_btu_hr / (cp_btu_lb_r * delta_t_r)

    return {
        "Fire Heat Input Q (Btu/hr)": round(q_btu_hr, 0),
        "Required Relief Load W (lb/hr)": round(w_lb_hr, 1),
        "_warnings": warnings,
    }


TOOL_FIRE_GAS_NONWETTED = ToolSpec(
    key="ps_012",
    title="Fire Case - Gas/Non-Wetted Vessel Relief Load (API 521)",
    category="Relief Load Scenarios",
    description="Fire-exposure heat absorption into vapor-only (non-wetted) equipment and resulting thermal-expansion relief load.",
    inputs=[
        InputSpec("a_bare_ft2", "Exposed Bare-Metal Area", default=300.0, min_value=1.0,
                   quantity_kind="area", canonical_unit="ft2"),
        InputSpec("f_factor", "Environmental Factor (F)", default=1.0, min_value=0.025, max_value=1.0, step=0.005),
        InputSpec("cp_btu_lb_r", "Vapor Specific Heat (Cp)", default=0.5, min_value=0.05, unit="(Btu/lb-degR)"),
        InputSpec("delta_t_r", "Allowable Temperature Rise", default=100.0, min_value=1.0, unit="(degR)",
                   help="Temperature rise assumed over the relief event duration - a simplifying screening assumption."),
    ],
    compute=compute_fire_gas_nonwetted,
    formula_md=r"$$Q = 43.2\,F\,A_{bare}^{0.82}, \quad W \approx \dfrac{Q}{C_p\,\Delta T}$$",
    references=["API Standard 521 - Pressure-relieving and Depressuring Systems"],
    assumptions=[
        "The W = Q/(Cp*dT) mass-relief estimate is a simplified thermal-expansion screening method, "
        "not the full API 521 gas-expansion derivation (which also tracks P,V,T relief-valve blowdown "
        "dynamics) - use for first-pass sizing only.",
        "43.2 constant (vs. 21000 for wetted case) reflects the much lower heat-transfer coefficient "
        "into a gas-filled vessel wall under fire exposure.",
    ],
)


# =======================================================================
# TOOL: BLOCKED DISCHARGE RELIEF LOAD
# =======================================================================

def compute_blocked_discharge(values: dict) -> dict:
    rated_flow = values["rated_flow"]
    safety_margin_pct = values["safety_margin_pct"]

    has_error, has_warning, errors, warnings = run_validators(
        check_positive(rated_flow, "Rated flow"),
    )
    if has_error:
        raise ValueError("; ".join(errors))

    w_relief = rated_flow * (1 + safety_margin_pct / 100.0)
    return {
        "Governing Relief Load": round(w_relief, 2),
        "_warnings": warnings,
    }


TOOL_BLOCKED_DISCHARGE = ToolSpec(
    key="ps_013",
    title="Blocked Discharge Relief Load",
    category="Relief Load Scenarios",
    description="Governing relief load for a blocked-outlet scenario: full rated upstream pump/compressor/PD-pump output at max operating head.",
    inputs=[
        InputSpec("rated_flow", "Upstream Rated Flow at Max Head/Speed", default=10000.0, min_value=0.1,
                   quantity_kind="flow_mass", canonical_unit="lb/hr"),
        InputSpec("safety_margin_pct", "Additional Safety Margin", default=0.0, min_value=0.0, max_value=25.0, step=1.0, unit="(%)",
                   help="Optional margin above nameplate rating; 0% uses the rated capacity as-is per API 521 base case."),
    ],
    compute=compute_blocked_discharge,
    formula_md=r"$$W_{relief} = W_{rated}\,(1 + \text{margin})$$",
    references=["API Standard 521 - Pressure-relieving and Depressuring Systems"],
    assumptions=[
        "Assumes the source (pump/compressor) curve is flat enough near shutoff/blocked conditions "
        "that rated flow at max head is a valid governing load - for centrifugal machines, verify "
        "against the actual head-flow curve at the relief valve set pressure, not just nameplate flow.",
        "For PD pumps/compressors, full rated displacement flow is inherently the correct blocked-in "
        "relief load (curve-shape caveat does not apply).",
    ],
)


# =======================================================================
# TOOL: THERMAL EXPANSION OF TRAPPED LIQUID
# =======================================================================

def compute_thermal_expansion(values: dict) -> dict:
    """Q_vol = alpha * H_heat / (rho * Cp)  [volumetric relief rate]"""
    alpha_per_f = values["alpha_per_f"]
    heat_input_btu_hr = values["heat_input_btu_hr"]
    rho_lb_ft3 = values["rho_lb_ft3"]
    cp_btu_lb_f = values["cp_btu_lb_f"]

    has_error, has_warning, errors, warnings = run_validators(
        check_positive(heat_input_btu_hr, "Heat input"),
        check_positive(rho_lb_ft3, "Liquid density"),
        check_positive(cp_btu_lb_f, "Liquid Cp"),
    )
    if has_error:
        raise ValueError("; ".join(errors))

    q_vol_ft3_hr = (alpha_per_f * heat_input_btu_hr) / (rho_lb_ft3 * cp_btu_lb_f)
    q_gpm = q_vol_ft3_hr * 7.4805 / 60.0

    return {
        "Volumetric Relief Rate (ft3/hr)": round(q_vol_ft3_hr, 4),
        "Volumetric Relief Rate (USGPM)": round(q_gpm, 5),
        "_warnings": warnings,
    }


TOOL_THERMAL_EXPANSION = ToolSpec(
    key="ps_014",
    title="Thermal Expansion of Trapped Liquid",
    category="Relief Load Scenarios",
    description="Relief flow (Q) from solar/process heat input to a blocked-in liquid-full line, exchanger, or vessel.",
    inputs=[
        InputSpec("alpha_per_f", "Coefficient of Cubical Expansion (alpha)", default=0.0004, min_value=0.00001, max_value=0.01, step=0.00001, unit="(1/degF)",
                   help="Typical hydrocarbon liquids ~0.0003-0.0009 /degF; water ~0.0001-0.0002 /degF at ambient."),
        InputSpec("heat_input_btu_hr", "Heat Input Rate", default=2000.0, min_value=1.0, unit="(Btu/hr)",
                   help="Solar gain (~150-260 Btu/hr-ft2 typical) or adjacent process heat source, whichever governs."),
        InputSpec("rho_lb_ft3", "Liquid Density", default=50.0, min_value=1.0, unit="(lb/ft3)"),
        InputSpec("cp_btu_lb_f", "Liquid Specific Heat (Cp)", default=0.5, min_value=0.05, unit="(Btu/lb-degF)"),
    ],
    compute=compute_thermal_expansion,
    formula_md=r"$$Q_{vol} = \dfrac{\alpha\,H_{heat}}{\rho\,C_p}$$",
    references=["API Standard 521 - Pressure-relieving and Depressuring Systems (thermal relief section)"],
    assumptions=[
        "Resulting Q is normally very small (mL/min to few GPM range) - feeds directly into the "
        "ps_002 liquid thermal-relief orifice-sizing tool as the required flow Q.",
        "Solar heat-input default is illustrative only - use the actual insolation/process exposure "
        "basis for the specific line/equipment segment being evaluated.",
    ],
)


# =======================================================================
# TOOL: HEAT EXCHANGER TUBE RUPTURE RELIEF LOAD
# =======================================================================

def compute_tube_rupture(values: dict) -> dict:
    """Liquid choked flow through two-ended tube shear area (screening, single-phase)."""
    tube_id_in = values["tube_id_in"]
    delta_p_psi = values["delta_p_psi"]
    rho_lb_ft3 = values["rho_lb_ft3"]
    cd = values["cd"]

    has_error, has_warning, errors, warnings = run_validators(
        check_positive(tube_id_in, "Tube ID"),
        check_positive(delta_p_psi, "HP-LP differential pressure"),
        check_positive(rho_lb_ft3, "Fluid density"),
    )
    if has_error:
        raise ValueError("; ".join(errors))

    a_tube_ft2 = math.pi / 4 * (tube_id_in / 12.0) ** 2
    a_shear_ft2 = 2 * a_tube_ft2  # two-ended shear

    rho_lb_ft3_local = rho_lb_ft3
    g_c = 32.174
    dp_lbf_ft2 = delta_p_psi * 144.0
    v_ft_s = cd * math.sqrt(2 * g_c * dp_lbf_ft2 / rho_lb_ft3_local)
    w_lb_hr = a_shear_ft2 * v_ft_s * rho_lb_ft3_local * 3600.0

    return {
        "Single Tube Bore Area (in2)": round(a_tube_ft2 * 144, 4),
        "Two-Ended Shear Area (in2)": round(a_shear_ft2 * 144, 4),
        "Discharge Velocity (ft/s)": round(v_ft_s, 2),
        "Relief Load W (lb/hr)": round(w_lb_hr, 1),
        "_warnings": warnings,
    }


TOOL_TUBE_RUPTURE = ToolSpec(
    key="ps_015",
    title="Heat Exchanger Tube Rupture Relief Load",
    category="Relief Load Scenarios",
    description="Screening single-phase liquid relief load from a full-bore two-ended tube rupture (HP tube-side to LP shell-side).",
    inputs=[
        InputSpec("tube_id_in", "Tube Inside Diameter", default=0.75, min_value=0.1,
                   quantity_kind="length", canonical_unit="in"),
        InputSpec("delta_p_psi", "HP-to-LP Differential Pressure", default=500.0, min_value=1.0,
                   quantity_kind="pressure", canonical_unit="psi"),
        InputSpec("rho_lb_ft3", "Fluid Density (HP side)", default=50.0, min_value=1.0, unit="(lb/ft3)"),
        InputSpec("cd", "Discharge Coefficient", default=0.61, min_value=0.4, max_value=1.0, step=0.01,
                   help="0.61 is a typical sharp-edged-orifice screening value for a sheared tube break."),
    ],
    compute=compute_tube_rupture,
    formula_md=(
        r"$$A_{shear} = 2\cdot\dfrac{\pi}{4}D_{tube}^2, \quad "
        r"v = C_d\sqrt{\dfrac{2\,g_c\,\Delta P}{\rho}}, \quad W = A_{shear}\,v\,\rho$$"
    ),
    references=["API Standard 521 - Pressure-relieving and Depressuring Systems (tube rupture section)"],
    assumptions=[
        "Single-phase liquid screening model only - if HP fluid flashes across the break (vapor-"
        "liquid HP source), use a two-phase HEM calculation (see ps_016) instead; this tool will "
        "UNDER-estimate relief load for a flashing fluid.",
        "Assumes a clean full-bore two-ended shear (worst credible case per API 521) - a partial "
        "crack/pinhole leak produces a smaller, non-governing load.",
        "Does not check whether the LP shell-side design pressure/existing relief device already "
        "covers this load - that comparison must be done separately.",
    ],
)


REGISTRY: dict[str, ToolSpec] = {
    TOOL_FIRE_WETTED.key: TOOL_FIRE_WETTED,
    TOOL_FIRE_GAS_NONWETTED.key: TOOL_FIRE_GAS_NONWETTED,
    TOOL_BLOCKED_DISCHARGE.key: TOOL_BLOCKED_DISCHARGE,
    TOOL_THERMAL_EXPANSION.key: TOOL_THERMAL_EXPANSION,
    TOOL_TUBE_RUPTURE.key: TOOL_TUBE_RUPTURE,
}
