"""
domains/dom_01_hydraulics/fluid_dynamics_engine.py
=====================================================
Pattern A: pure Python physics, zero `st.*` calls. Every function here
takes a plain dict and returns a plain dict — testable headlessly,
reusable by the report/email export, and safe to call from CI without a
Streamlit runtime.

6 live tools, all previously verified (see this project's history):
  hy_001    Single-Phase Pressure Drop (Darcy-Weisbach + Swamee-Jain)
  hy_002ab  Control Valve Sizing, Liquid & Gas (ISA-75.01)
  hy_003    NPSH Available vs. Required
  hy_006    Water Hammer & Surge Pressure (Joukowsky + Korteweg)
  hy_007    Orifice Plate Flowmeter (ISO 5167)
"""

import math
from utils.tool_roadmap import ToolSpec, InputSpec
from utils.ui_components import (
    check_positive, check_pressure_drop, check_specific_gravity,
    check_reynolds_regime, run_validators,
)


# =======================================================================
# TOOL: SINGLE-PHASE PRESSURE DROP (Darcy-Weisbach + Swamee-Jain)
# =======================================================================

def compute_pressure_drop(values: dict) -> dict:
    rho = values["rho"]
    v = values["velocity"]
    d = values["diameter"]
    length = values["length"]
    mu = values["viscosity"]
    roughness = values["roughness"]

    has_error, has_warning, errors, warnings = run_validators(
        check_positive(rho, "Density"), check_positive(v, "Velocity"),
        check_positive(d, "Diameter"), check_positive(length, "Length"),
        check_positive(mu, "Viscosity"),
    )
    if has_error:
        raise ValueError("; ".join(errors))

    re = (rho * v * d) / mu
    regime = check_reynolds_regime(re)

    if re < 2300:
        f = 64.0 / re
    else:
        rel_rough = roughness / d
        f = 0.25 / (math.log10((rel_rough / 3.7) + (5.74 / re ** 0.9))) ** 2

    dp_pa = f * (length / d) * (rho * v ** 2 / 2.0)

    return {
        "Reynolds Number": round(re, 1),
        "Flow Regime": regime,
        "Friction Factor (Swamee-Jain)": round(f, 5),
        "Pressure Drop (Pa)": round(dp_pa, 1),
        "Pressure Drop (bar)": round(dp_pa / 1e5, 4),
        "Pressure Drop (psi)": round(dp_pa / 6894.757, 3),
        "_warnings": warnings,
    }


TOOL_PRESSURE_DROP = ToolSpec(
    key="hy_001",
    title="Single-Phase Pressure Drop (Darcy-Weisbach)",
    category="Piping Systems & Flow Measurement",
    description="Pressure drop through a pipe segment using Darcy-Weisbach with the Swamee-Jain explicit friction factor.",
    inputs=[
        InputSpec("rho", "Fluid Density", default=1000.0, min_value=0.01, unit="(kg/m3)"),
        InputSpec("velocity", "Flow Velocity", default=2.0, min_value=0.001, unit="(m/s)"),
        InputSpec("diameter", "Pipe Internal Diameter", default=0.1, min_value=0.001, unit="(m)"),
        InputSpec("length", "Pipe Length", default=100.0, min_value=0.1, unit="(m)"),
        InputSpec("viscosity", "Dynamic Viscosity", default=0.001, min_value=1e-6, unit="(Pa.s)"),
        InputSpec("roughness", "Absolute Roughness", default=0.000045, min_value=0.0, unit="(m)"),
    ],
    compute=compute_pressure_drop,
    formula_md=(
        r"$$\Delta P = f \cdot \frac{L}{D} \cdot \frac{\rho v^2}{2}$$"
        "\n\nFriction factor via Swamee-Jain explicit approximation "
        r"(turbulent, $4000<Re<10^8$); $f=64/Re$ for laminar flow."
    ),
    references=[
        "Crane Technical Paper 410 - Flow of Fluids Through Valves, Fittings, and Pipe",
        "GPSA Engineering Data Book, Section 17 - Fluid Flow",
    ],
    assumptions=[
        "Single-phase, incompressible, steady-state flow.",
        "Straight pipe run - fitting losses (K-factors) not included; add separately.",
    ],
)


# =======================================================================
# TOOL: CONTROL VALVE SIZING - Cv (Liquid & Gas), ISA-75.01
# =======================================================================

def compute_valve_cv_liquid(values: dict) -> dict:
    q = values["flow"]
    p1 = values["p1"]
    p2 = values["p2"]
    sg = values["sg"]
    pv = values["pv"]
    pc = values["pc"]
    fl = values["fl"]

    has_error, has_warning, errors, warnings = run_validators(
        check_positive(q, "Flow rate"), check_pressure_drop(p1, p2, "pressure"),
        check_specific_gravity(sg), check_positive(fl, "FL"),
    )
    if has_error:
        raise ValueError("; ".join(errors))

    dp = p1 - p2
    ff = 0.96 - 0.28 * math.sqrt(pv / pc) if pc > 0 else 0.96
    dp_choked = (fl ** 2) * (p1 - ff * pv)
    is_choked = dp >= dp_choked
    dp_eff = dp_choked if is_choked else dp
    if dp_eff <= 0:
        dp_eff = dp

    cv = q * math.sqrt(sg / dp_eff)

    return {
        "Required Cv": round(cv, 3),
        "Actual dP (psi)": round(dp, 2),
        "Choked dP Threshold (psi)": round(dp_choked, 2),
        "Choked Flow?": "Yes" if is_choked else "No",
        "_warnings": warnings + (
            ["CHOKED/CAVITATING FLOW - sizing uses dP_choked; verify valve trim."] if is_choked else []
        ),
    }


def compute_valve_cv_gas(values: dict) -> dict:
    w = values["mass_flow"]
    p1 = values["p1"]
    p2 = values["p2"]
    t1 = values["t1"]
    sg_gas = values["sg_gas"]
    z = values["z"]
    xt = values["xt"]
    k = values["k"]

    has_error, has_warning, errors, warnings = run_validators(
        check_positive(w, "Mass flow"), check_pressure_drop(p1, p2, "pressure"),
        check_positive(t1, "Temperature"), check_positive(sg_gas, "Gas specific gravity"),
    )
    if has_error:
        raise ValueError("; ".join(errors))

    dp = p1 - p2
    x = dp / p1
    fk = k / 1.4
    x_choked = fk * xt
    is_choked = x >= x_choked
    x_eff = x_choked if is_choked else x

    y = 1 - (x_eff / (3 * fk * xt))
    y = max(0.667, min(1.0, y))

    denom = 63.3 * y * math.sqrt(x_eff * p1 * (p1 / (sg_gas * t1 * z)))
    cv = w / denom if denom > 0 else 0.0

    return {
        "Required Cv": round(cv, 3),
        "Pressure Drop Ratio (x)": round(x, 4),
        "Choked x Threshold": round(x_choked, 4),
        "Choked Flow?": "Yes" if is_choked else "No",
        "Expansion Factor (Y)": round(y, 4),
        "_warnings": warnings + (
            ["CHOKED FLOW - mass flow independent of further downstream pressure reduction."] if is_choked else []
        ),
    }


TOOL_VALVE_LIQUID = ToolSpec(
    key="hy_002a",
    title="Control Valve Sizing - Liquid Cv (ISA-75.01)",
    category="Piping Systems & Flow Measurement",
    description="Required Cv for liquid service with choked-flow / cavitation check.",
    inputs=[
        InputSpec("flow", "Flow Rate", default=150.0, min_value=0.01, unit="(USGPM)"),
        InputSpec("p1", "Upstream Pressure P1", default=150.0, min_value=0.01, unit="(psia)"),
        InputSpec("p2", "Downstream Pressure P2", default=100.0, min_value=0.01, unit="(psia)"),
        InputSpec("sg", "Specific Gravity", default=1.0, min_value=0.01, step=0.01),
        InputSpec("pv", "Vapor Pressure Pv", default=0.5, min_value=0.0, unit="(psia)"),
        InputSpec("pc", "Critical Pressure Pc", default=3208.0, min_value=0.01, unit="(psia)"),
        InputSpec("fl", "FL - Recovery Factor", default=0.9, min_value=0.01, max_value=1.0, step=0.01),
    ],
    compute=compute_valve_cv_liquid,
    formula_md=r"$$C_v = Q\sqrt{SG/\Delta P_{eff}}$$ Choked when $\Delta P \geq F_L^2(P_1-F_F P_v)$, $F_F=0.96-0.28\sqrt{P_v/P_c}$.",
    references=["ISA-75.01.01 / IEC 60534-2-1", "Fisher Control Valve Handbook, 5th Ed."],
    assumptions=["FL is valve-specific; default is a typical globe-valve value only.", "Single-phase liquid at valve inlet."],
)

TOOL_VALVE_GAS = ToolSpec(
    key="hy_002b",
    title="Control Valve Sizing - Gas/Vapor Cv (ISA-75.01)",
    category="Piping Systems & Flow Measurement",
    description="Required Cv for compressible service with choked-flow check.",
    inputs=[
        InputSpec("mass_flow", "Mass Flow Rate", default=5000.0, min_value=0.01, unit="(lb/hr)"),
        InputSpec("p1", "Upstream Pressure P1", default=150.0, min_value=0.01, unit="(psia)"),
        InputSpec("p2", "Downstream Pressure P2", default=100.0, min_value=0.01, unit="(psia)"),
        InputSpec("t1", "Upstream Temperature T1", default=560.0, min_value=1.0, unit="(degR)"),
        InputSpec("sg_gas", "Gas Specific Gravity (vs air)", default=1.0, min_value=0.01, step=0.01),
        InputSpec("z", "Compressibility Factor Z", default=1.0, min_value=0.1, max_value=2.0, step=0.01),
        InputSpec("xt", "XT - Terminal Pressure Drop Ratio", default=0.7, min_value=0.1, max_value=1.0, step=0.01),
        InputSpec("k", "k - Ratio of Specific Heats", default=1.4, min_value=1.0, max_value=1.7, step=0.01),
    ],
    compute=compute_valve_cv_gas,
    formula_md=r"$$C_v = \frac{W}{63.3\,Y\sqrt{x_{eff}\,P_1\cdot P_1/(SG\,T_1\,Z)}}$$ Choking at $x\geq F_kX_T$.",
    references=["ISA-75.01.01 / IEC 60534-2-1", "GPSA Engineering Data Book, Section 3"],
    assumptions=["XT is valve-specific; default is a typical globe-valve value only.", "Ideal gas compressibility correction."],
)


# =======================================================================
# TOOL: NPSH AVAILABLE vs. REQUIRED CHECK
# =======================================================================

def compute_npsh_check(values: dict) -> dict:
    npsha = values["npsha"]
    npshr = values["npshr"]
    margin_target = values["margin_target"]

    has_error, has_warning, errors, warnings = run_validators(
        check_positive(npsha, "NPSH available"), check_positive(npshr, "NPSH required"),
        check_positive(margin_target, "Target margin"),
    )
    if has_error:
        raise ValueError("; ".join(errors))

    margin = npsha - npshr
    is_adequate = margin >= margin_target
    ratio = npsha / npshr if npshr > 0 else float("inf")

    return {
        "NPSH Margin (ft)": round(margin, 2),
        "NPSHa / NPSHr Ratio": round(ratio, 2),
        "Status": "Adequate" if is_adequate else "INSUFFICIENT - cavitation risk",
        "_warnings": warnings + (
            [f"NPSH margin of {margin:.2f} ft is below the {margin_target:.1f} ft target - cavitation risk."]
            if not is_adequate else []
        ),
    }


TOOL_NPSH = ToolSpec(
    key="hy_003",
    title="NPSH Available vs. Required Check",
    category="Piping Systems & Flow Measurement",
    description="Compares NPSH available to NPSH required with a configurable minimum design margin.",
    inputs=[
        InputSpec("npsha", "NPSH Available (NPSHa)", default=20.0, min_value=0.01, unit="(ft)"),
        InputSpec("npshr", "NPSH Required (NPSHr)", default=12.0, min_value=0.01, unit="(ft)"),
        InputSpec("margin_target", "Target Minimum Margin", default=3.0, min_value=0.0, unit="(ft)",
                   help="Hydraulic Institute typically recommends 3-5 ft."),
    ],
    compute=compute_npsh_check,
    formula_md=r"$$\text{NPSH margin} = \text{NPSH}_a - \text{NPSH}_r$$",
    references=["Hydraulic Institute Standards (ANSI/HI 9.6.1)", "API 610"],
    assumptions=["NPSHa must be independently calculated from the actual suction system."],
)


# =======================================================================
# TOOL: WATER HAMMER & SURGE PRESSURE PEAK ANALYSIS (Joukowsky)
# =======================================================================

PIPE_MATERIAL_E_PA = {
    "Steel": 200e9, "Ductile Iron": 166e9, "Copper": 117e9, "PVC": 3.0e9, "HDPE": 0.9e9,
}


def compute_water_hammer(values: dict) -> dict:
    rho = values["fluid_density"]
    bulk_modulus = values["bulk_modulus"] * 1e9
    material = values["pipe_material"]
    diameter_mm = values["diameter_mm"]
    wall_thickness_mm = values["wall_thickness_mm"]
    velocity_change = values["velocity_change"]
    pipe_length_m = values["pipe_length"]
    closure_time_s = values["closure_time"]
    static_pressure_kpa = values["static_pressure"]

    has_error, has_warning, errors, warnings = run_validators(
        check_positive(rho, "Fluid density"), check_positive(bulk_modulus, "Bulk modulus"),
        check_positive(diameter_mm, "Pipe diameter"), check_positive(wall_thickness_mm, "Wall thickness"),
        check_positive(pipe_length_m, "Pipe length"), check_positive(closure_time_s, "Closure time"),
    )
    if has_error:
        raise ValueError("; ".join(errors))
    if velocity_change <= 0:
        raise ValueError("Velocity change must be greater than zero.")

    e_pipe = PIPE_MATERIAL_E_PA.get(material)
    if e_pipe is None:
        raise ValueError(f"Unknown pipe material: {material}")

    d_m = diameter_mm / 1000.0
    e_wall_m = wall_thickness_mm / 1000.0

    a = math.sqrt((bulk_modulus / rho) / (1 + (bulk_modulus * d_m) / (e_pipe * e_wall_m)))
    t_critical = (2 * pipe_length_m) / a
    is_rapid_closure = closure_time_s <= t_critical

    dp_joukowsky_pa = rho * a * velocity_change
    dp_surge_pa = dp_joukowsky_pa if is_rapid_closure else dp_joukowsky_pa * (t_critical / closure_time_s)

    dp_surge_kpa = dp_surge_pa / 1000.0
    dp_surge_psi = dp_surge_pa / 6894.757
    peak_pressure_kpa = static_pressure_kpa + dp_surge_kpa

    extra_warnings = []
    if is_rapid_closure:
        extra_warnings.append(
            f"Closure time ({closure_time_s:.3f}s) is at/below critical reflection time "
            f"({t_critical:.3f}s) - RAPID closure. Full Joukowsky surge pressure applies."
        )

    return {
        "Pressure Wave Speed a (m/s)": round(a, 1),
        "Critical Reflection Time (s)": round(t_critical, 3),
        "Closure Type": "RAPID (full Joukowsky)" if is_rapid_closure else "Slow (attenuated surge)",
        "Surge Pressure Rise (kPa)": round(dp_surge_kpa, 1),
        "Surge Pressure Rise (psi)": round(dp_surge_psi, 1),
        "Peak Pressure (kPa)": round(peak_pressure_kpa, 1),
        "_warnings": warnings + extra_warnings,
    }


TOOL_WATER_HAMMER = ToolSpec(
    key="hy_006",
    title="Water Hammer & Surge Pressure Peak Analysis",
    category="Piping Systems & Flow Measurement",
    description="Joukowsky surge pressure with Korteweg wave-speed correction and rapid/slow valve-closure check.",
    inputs=[
        InputSpec("fluid_density", "Fluid Density", default=998.0, min_value=1.0, unit="(kg/m3)"),
        InputSpec("bulk_modulus", "Fluid Bulk Modulus", default=2.15, min_value=0.01, unit="(GPa)",
                   help="Water at ambient conditions: ~2.15 GPa."),
        InputSpec("pipe_material", "Pipe Material", default=0.0, input_type="select",
                   options=list(PIPE_MATERIAL_E_PA.keys())),
        InputSpec("diameter_mm", "Pipe Internal Diameter", default=150.0, min_value=1.0, unit="(mm)"),
        InputSpec("wall_thickness_mm", "Pipe Wall Thickness", default=6.0, min_value=0.5, unit="(mm)"),
        InputSpec("velocity_change", "Velocity Change (arrested flow)", default=2.0, min_value=0.01, unit="(m/s)"),
        InputSpec("pipe_length", "Pipe Length (source to valve)", default=500.0, min_value=1.0, unit="(m)"),
        InputSpec("closure_time", "Valve Closure Time", default=0.3, min_value=0.001, unit="(s)"),
        InputSpec("static_pressure", "Static Operating Pressure", default=500.0, min_value=0.0, unit="(kPa)"),
    ],
    compute=compute_water_hammer,
    formula_md=(
        r"$$a=\sqrt{\dfrac{K/\rho}{1+\dfrac{KD}{Ee}}}, \quad t_c=\dfrac{2L}{a}, \quad \Delta P = \rho a \Delta v \text{ (rapid closure)}$$"
    ),
    references=["Wylie & Streeter, Fluid Transients in Systems", "AWWA Manual M11"],
    assumptions=["Pipe restraint factor c1=1.0 (fully anchored).", "Slow-closure uses linear (tc/tclose) attenuation approximation."],
)


# =======================================================================
# TOOL: ORIFICE PLATE FLOWMETER (ISO 5167)
# =======================================================================

def compute_orifice_plate(values: dict) -> dict:
    d_pipe_mm = values["pipe_id_mm"]
    d_orifice_mm = values["orifice_bore_mm"]
    dp_kpa = values["diff_pressure_kpa"]
    rho = values["fluid_density"]
    c = values["discharge_coeff"]
    epsilon = values.get("expansibility", 1.0)

    if d_pipe_mm <= 0 or d_orifice_mm <= 0:
        raise ValueError("Diameters must be positive.")
    if d_orifice_mm >= d_pipe_mm:
        raise ValueError("Orifice bore must be smaller than the pipe ID.")
    if rho <= 0:
        raise ValueError("Fluid density must be positive.")
    if dp_kpa <= 0:
        raise ValueError("Differential pressure must be positive.")

    d_pipe_m = d_pipe_mm / 1000.0
    d_orifice_m = d_orifice_mm / 1000.0
    beta = d_orifice_m / d_pipe_m
    dp_pa = dp_kpa * 1000.0
    area_m2 = (math.pi / 4.0) * d_orifice_m ** 2

    qm_kg_s = (c / math.sqrt(1 - beta ** 4)) * epsilon * area_m2 * math.sqrt(2 * dp_pa * rho)
    q_vol_m3_s = qm_kg_s / rho
    q_vol_m3_hr = q_vol_m3_s * 3600.0

    beta_warning = None
    if not (0.1 <= beta <= 0.75):
        beta_warning = (
            f"Beta ratio {beta:.3f} is outside ISO 5167's typical validated range "
            f"(0.1-0.75) - discharge coefficient accuracy not guaranteed outside this range."
        )

    return {
        "Beta Ratio": round(beta, 4),
        "Mass Flow (kg/s)": round(qm_kg_s, 4),
        "Volumetric Flow (m3/hr)": round(q_vol_m3_hr, 3),
        "Volumetric Flow (m3/s)": round(q_vol_m3_s, 5),
        "_warnings": [w for w in [beta_warning] if w],
    }


TOOL_ORIFICE_PLATE = ToolSpec(
    key="hy_007",
    title="Orifice Plate Flowmeter (ISO 5167)",
    category="Piping Systems & Flow Measurement",
    description="Volumetric/mass flow rate from differential pressure across a concentric orifice plate.",
    inputs=[
        InputSpec("pipe_id_mm", "Pipe Internal Diameter", default=100.0, min_value=1.0, unit="(mm)"),
        InputSpec("orifice_bore_mm", "Orifice Bore Diameter", default=60.0, min_value=0.5, unit="(mm)"),
        InputSpec("diff_pressure_kpa", "Differential Pressure", default=50.0, min_value=0.001, unit="(kPa)"),
        InputSpec("fluid_density", "Fluid Density", default=998.0, min_value=0.01, unit="(kg/m3)"),
        InputSpec("discharge_coeff", "Discharge Coefficient (C)", default=0.60, min_value=0.4, max_value=0.75, step=0.01,
                   help="Typical corner-tap value ~0.60-0.62. Take from ISO 5167 tables or calibration certificate."),
        InputSpec("expansibility", "Expansibility Factor (epsilon)", default=1.0, min_value=0.8, max_value=1.0, step=0.01,
                   help="Use 1.0 for liquids. Gas/vapor service requires a separately-computed epsilon per ISO 5167 Annex A."),
    ],
    compute=compute_orifice_plate,
    formula_md=r"$$q_m=\dfrac{C}{\sqrt{1-\beta^4}}\varepsilon\dfrac{\pi}{4}d^2\sqrt{2\Delta P\rho_1}, \quad \beta=d/D$$",
    references=["ISO 5167-1:2022 & ISO 5167-2:2022", "Reader-Harris, M.J. (2015), Orifice Plates and Venturi Tubes"],
    assumptions=[
        "Discharge coefficient C is a direct input (from ISO 5167 tables/calibration), not computed via the full Reader-Harris/Gallagher correlation.",
        "Expansibility epsilon=1.0 default valid for incompressible liquids only.",
        "Beta ratio should fall within 0.1-0.75 for standard's validated accuracy; tool warns but does not block outside this range.",
        "Assumes fully-developed flow with adequate straight-pipe run per ISO 5167 Table 3 - not checked by this tool.",
    ],
)


# =======================================================================
# TOOL: PUMP BRAKE HORSEPOWER
# =======================================================================

def compute_pump_bhp(values: dict) -> dict:
    flow_gpm = values["flow_gpm"]
    head_ft = values["head_ft"]
    sg = values["sg"]
    efficiency_fraction = values["efficiency_fraction"]

    has_error, has_warning, errors, warnings = run_validators(
        check_positive(flow_gpm, "Flow"), check_positive(head_ft, "Head"), check_specific_gravity(sg),
    )
    if has_error:
        raise ValueError("; ".join(errors))
    if not (0 < efficiency_fraction <= 1):
        raise ValueError("Efficiency must be between 0 (exclusive) and 1 (inclusive) - enter as a fraction, not a percentage.")

    hydraulic_hp = (flow_gpm * head_ft * sg) / 3960
    bhp = hydraulic_hp / efficiency_fraction

    return {
        "Hydraulic HP": round(hydraulic_hp, 3),
        "Brake Horsepower (BHP)": round(bhp, 3),
        "_warnings": warnings,
    }


TOOL_PUMP_BHP = ToolSpec(
    key="hy_004",
    title="Pump Total Dynamic Head & Brake Horsepower",
    category="Pumps & Fluid Drivers",
    description="Hydraulic and brake horsepower for a centrifugal pump given flow, head, and efficiency.",
    inputs=[
        InputSpec("flow_gpm", "Flow Rate", default=500.0, min_value=0.01, unit="(USGPM)"),
        InputSpec("head_ft", "Total Dynamic Head", default=150.0, min_value=0.01, unit="(ft)"),
        InputSpec("sg", "Specific Gravity", default=1.0, min_value=0.01, step=0.01),
        InputSpec("efficiency_fraction", "Pump Efficiency", default=0.75, min_value=0.01, max_value=1.0, step=0.01,
                   help="Enter as a fraction (e.g. 0.75), not a percentage."),
    ],
    compute=compute_pump_bhp,
    formula_md=r"$$BHP = \dfrac{Q[\text{gpm}]\cdot H[\text{ft}]\cdot SG}{3960\cdot\eta}$$",
    references=["Hydraulic Institute Standards (ANSI/HI 1.3)", "Perry's Chemical Engineers' Handbook, Section 10"],
    assumptions=["Screening-level - actual pump selection requires vendor performance curves at the specific operating point."],
)


# =======================================================================
# TOOL: COMPRESSOR POLYTROPIC HEAD & DISCHARGE TEMPERATURE
# =======================================================================

def compute_compressor_polytropic(values: dict) -> dict:
    p1_psia = values["p1_psia"]
    p2_psia = values["p2_psia"]
    t1_r = values["t1_r"]
    n_polytropic = values["n_polytropic"]
    z_avg = values["z_avg"]
    mw = values["mw"]
    efficiency_fraction = values.get("efficiency_fraction")

    has_error, has_warning, errors, warnings = run_validators(
        check_positive(p1_psia, "Suction pressure"), check_positive(t1_r, "Suction temperature"),
        check_positive(mw, "Molecular weight"),
    )
    if has_error:
        raise ValueError("; ".join(errors))
    if p2_psia <= p1_psia:
        raise ValueError("Discharge pressure must exceed suction pressure.")
    if n_polytropic <= 1:
        raise ValueError("Polytropic exponent n must be greater than 1.")

    ratio = p2_psia / p1_psia
    t2_r = t1_r * ratio ** ((n_polytropic - 1) / n_polytropic)

    r_universal = 1545.35  # ft-lbf/(lbmol-degR)
    hp_ft = (n_polytropic / (n_polytropic - 1)) * (z_avg * r_universal * t1_r / mw) * (ratio ** ((n_polytropic - 1) / n_polytropic) - 1)

    result = {
        "Pressure Ratio": round(ratio, 4),
        "Discharge Temperature (degR)": round(t2_r, 2),
        "Discharge Temperature (degF)": round(t2_r - 459.67, 2),
        "Polytropic Head (ft-lbf/lbm)": round(hp_ft, 1),
    }

    if efficiency_fraction:
        if not (0 < efficiency_fraction <= 1):
            raise ValueError("Efficiency must be between 0 (exclusive) and 1 (inclusive).")
        gas_hp_per_lb_min = hp_ft / (33000 * efficiency_fraction)
        result["Gas HP per lb/min"] = round(gas_hp_per_lb_min, 5)

    result["_warnings"] = warnings
    return result


TOOL_COMPRESSOR = ToolSpec(
    key="hy_005",
    title="Compressor Polytropic Head & Power",
    category="Compressors & Blowers",
    description="Polytropic head, discharge temperature, and gas horsepower for a centrifugal compressor stage.",
    inputs=[
        InputSpec("p1_psia", "Suction Pressure (P1)", default=150.0, min_value=0.01, unit="(psia)"),
        InputSpec("p2_psia", "Discharge Pressure (P2)", default=450.0, min_value=0.01, unit="(psia)"),
        InputSpec("t1_r", "Suction Temperature (T1)", default=560.0, min_value=1.0, unit="(degR)"),
        InputSpec("n_polytropic", "Polytropic Exponent (n)", default=1.35, min_value=1.01, max_value=2.0, step=0.01),
        InputSpec("z_avg", "Average Compressibility (Z)", default=0.95, min_value=0.1, max_value=2.0, step=0.01),
        InputSpec("mw", "Molecular Weight", default=18.0, min_value=1.0),
        InputSpec("efficiency_fraction", "Polytropic Efficiency (optional)", default=0.78, min_value=0.0, max_value=1.0, step=0.01,
                   help="Leave at 0 to skip gas horsepower calculation."),
    ],
    compute=compute_compressor_polytropic,
    formula_md=(
        r"$$T_2 = T_1(P_2/P_1)^{(n-1)/n}$$"
        r"$$H_p = \dfrac{n}{n-1}\cdot\dfrac{ZRT_1}{MW}\left[(P_2/P_1)^{(n-1)/n}-1\right], \quad R=1545.35\ \text{ft-lbf/(lbmol-}^\circ\text{R)}$$"
    ),
    references=["GPSA Engineering Data Book, Section 13 - Compressors", "API 617"],
    assumptions=[
        "Screening-level - actual compressor selection requires vendor performance curves and a full multi-stage thermodynamic analysis.",
        "Gas horsepower result is per lb/min of mass flow - multiply by actual mass flow rate for total gas horsepower.",
    ],
)


REGISTRY: dict[str, ToolSpec] = {
    TOOL_PRESSURE_DROP.key: TOOL_PRESSURE_DROP,
    TOOL_VALVE_LIQUID.key: TOOL_VALVE_LIQUID,
    TOOL_VALVE_GAS.key: TOOL_VALVE_GAS,
    TOOL_NPSH.key: TOOL_NPSH,
    TOOL_WATER_HAMMER.key: TOOL_WATER_HAMMER,
    TOOL_ORIFICE_PLATE.key: TOOL_ORIFICE_PLATE,
    TOOL_PUMP_BHP.key: TOOL_PUMP_BHP,
    TOOL_COMPRESSOR.key: TOOL_COMPRESSOR,
}
