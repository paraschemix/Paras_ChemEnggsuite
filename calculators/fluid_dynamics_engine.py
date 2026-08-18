"""
calculators/fluid_dynamics_engine.py
======================================
Houses calculation logic for tools #1-10 (Fluid Dynamics domain).

This file follows the pure engine pattern: each tool is a pure `compute_*`
function (input dict -> result dict, no UI code) plus a ToolSpec entry in
REGISTRY describing its inputs and documentation. The page file
(pages/1_🌊_Fluid_Dynamics.py) iterates REGISTRY seamlessly.

Fully implemented:
  - Tool #1:  Single-Phase Pressure Drop (Darcy-Weisbach + Swamee-Jain)
  - Tool #2a: Control Valve Sizing — Liquid Cv (ISA-75.01)
  - Tool #2b: Control Valve Sizing — Gas/Vapor Cv (ISA-75.01)
  - Tool #3:  NPSH Available vs. Required Check
  - Tool #4:  Two-Phase Pressure Drop (Beggs & Brill / Lockhart-Martinelli)
  - Tool #5:  Pump Power, Sizing & Efficiency Calculation
  - Tool #6:  Water Hammer & Surge Pressure Peak Analysis (Joukowsky)
  - Tool #7:  Compressible Gas Flow & Line Sizing (Weymouth / Panhandle B)
  - Tool #8:  Equivalent Length & Fitting Losses (3K Method)
  - Tool #9:  Gravity Flow & Drain Line Sizing (Manning Equation)
  - Tool #10: Pitot Tube & Flow Meter Delta-P Velocity Sizing
"""

import math
from calculators.registry_base import ToolSpec, InputSpec
from utils.validators import (
    check_positive, check_pressure_drop, check_efficiency,
    check_specific_gravity, check_reynolds_regime, check_fraction_0_1, run_validators,
)


# =======================================================================
# TOOL 1: SINGLE-PHASE PRESSURE DROP (Darcy-Weisbach + Swamee-Jain)
# =======================================================================

def compute_pressure_drop(values: dict) -> dict:
    rho = values["rho"]          # kg/m3
    v = values["velocity"]       # m/s
    d = values["diameter"]       # m
    length = values["length"]    # m
    mu = values["viscosity"]     # Pa.s
    roughness = values["roughness"]  # m

    checks = run_validators(
        check_positive(rho, "Density"),
        check_positive(v, "Velocity"),
        check_positive(d, "Diameter"),
        check_positive(length, "Length"),
        check_positive(mu, "Viscosity"),
    )
    has_error, has_warning, errors, warnings = checks
    if has_error:
        raise ValueError("; ".join(errors))

    re = (rho * v * d) / mu
    regime = check_reynolds_regime(re)

    if re < 2300:
        f = 64.0 / re
    else:
        # Swamee-Jain explicit approximation to Colebrook-White
        rel_rough = roughness / d
        f = 0.25 / (math.log10((rel_rough / 3.7) + (5.74 / re ** 0.9))) ** 2

    dp_pa = f * (length / d) * (rho * v ** 2 / 2.0)

    return {
        "Reynolds Number": round(re, 1),
        "Flow Regime": regime,
        "Friction Factor (Darcy, Swamee-Jain)": round(f, 5),
        "Pressure Drop (Pa)": round(dp_pa, 1),
        "Pressure Drop (bar)": round(dp_pa / 1e5, 4),
        "Pressure Drop (psi)": round(dp_pa / 6894.757, 3),
        "_warnings": warnings,
    }


TOOL_PRESSURE_DROP = ToolSpec(
    key="fd_001",
    title="Single-Phase Pressure Drop (Darcy-Weisbach)",
    category="Piping Hydraulics",
    description="Pressure drop through a pipe segment using Darcy-Weisbach with the Swamee-Jain explicit friction factor.",
    inputs=[
        InputSpec("rho", "Fluid Density", default=1000.0, min_value=0.01, unit="(kg/m³)"),
        InputSpec("velocity", "Flow Velocity", default=2.0, min_value=0.001, unit="(m/s)"),
        InputSpec("diameter", "Pipe Internal Diameter", default=0.1, min_value=0.001, unit="(m)"),
        InputSpec("length", "Pipe Length", default=100.0, min_value=0.1, unit="(m)"),
        InputSpec("viscosity", "Dynamic Viscosity", default=0.001, min_value=1e-6, unit="(Pa·s)"),
        InputSpec("roughness", "Absolute Roughness", default=0.000045, min_value=0.0, unit="(m)"),
    ],
    compute=compute_pressure_drop,
    formula_md=(
        r"$$\Delta P = f \cdot \frac{L}{D} \cdot \frac{\rho v^2}{2}$$"
        "\n\nFriction factor via **Swamee-Jain** explicit approximation "
        r"(valid for turbulent flow, $4000 < Re < 10^8$, $10^{-6} < \varepsilon/D < 10^{-2}$):"
        "\n\n"
        r"$$f = \frac{0.25}{\left[\log_{10}\left(\frac{\varepsilon/D}{3.7} + \frac{5.74}{Re^{0.9}}\right)\right]^2}$$"
        "\n\nFor laminar flow (Re < 2300): $f = 64/Re$."
    ),
    references=[
        "Crane Technical Paper 410 — Flow of Fluids Through Valves, Fittings, and Pipe",
        "GPSA Engineering Data Book, Section 17 — Fluid Flow",
        "Swamee, P.K. & Jain, A.K. (1976), *Explicit equations for pipe-flow problems*, ASCE J. Hydraulics Div.",
    ],
    assumptions=[
        "Single-phase, incompressible, steady-state flow.",
        "Straight pipe run — fitting losses (K-factors, elbows, tees) are NOT included; add separately.",
        "Swamee-Jain is an explicit approximation to Colebrook-White — typically within ~1-2% for the stated validity range.",
    ],
)


# =======================================================================
# TOOL 2: CONTROL VALVE SIZING — Cv (Liquid & Gas), ISA-75.01
# =======================================================================

def compute_valve_cv_liquid(values: dict) -> dict:
    q = values["flow"]       # USGPM
    p1 = values["p1"]        # psia
    p2 = values["p2"]        # psia
    sg = values["sg"]
    pv = values["pv"]        # psia
    pc = values["pc"]        # psia
    fl = values["fl"]

    has_error, has_warning, errors, warnings = run_validators(
        check_positive(q, "Flow rate"),
        check_pressure_drop(p1, p2, "pressure"),
        check_specific_gravity(sg),
        check_positive(fl, "FL"),
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

    result = {
        "Required Cv": round(cv, 3),
        "Actual ΔP (psi)": round(dp, 2),
        "Choked ΔP Threshold (psi)": round(dp_choked, 2),
        "Choked Flow?": "Yes" if is_choked else "No",
        "_warnings": warnings + (
            ["CHOKED/CAVITATING FLOW — sizing uses ΔP_choked; verify valve trim (anti-cavitation may be required)."]
            if is_choked else []
        ),
    }
    return result


def compute_valve_cv_gas(values: dict) -> dict:
    w = values["mass_flow"]   # lb/hr
    p1 = values["p1"]         # psia
    p2 = values["p2"]         # psia
    t1 = values["t1"]         # deg R
    sg_gas = values["sg_gas"]
    z = values["z"]
    xt = values["xt"]
    k = values["k"]

    has_error, has_warning, errors, warnings = run_validators(
        check_positive(w, "Mass flow"),
        check_pressure_drop(p1, p2, "pressure"),
        check_positive(t1, "Temperature"),
        check_positive(sg_gas, "Gas specific gravity"),
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
            ["CHOKED FLOW — mass flow is independent of further downstream pressure reduction."]
            if is_choked else []
        ),
    }


TOOL_VALVE_LIQUID = ToolSpec(
    key="fd_002a",
    title="Control Valve Sizing — Liquid Cv (ISA-75.01)",
    category="Control Valves",
    description="Required Cv for liquid service with choked-flow / cavitation check.",
    inputs=[
        InputSpec("flow", "Flow Rate", default=150.0, min_value=0.01, unit="(USGPM)"),
        InputSpec("p1", "Upstream Pressure P1", default=150.0, min_value=0.01, unit="(psia)"),
        InputSpec("p2", "Downstream Pressure P2", default=100.0, min_value=0.01, unit="(psia)"),
        InputSpec("sg", "Specific Gravity", default=1.0, min_value=0.01, step=0.01),
        InputSpec("pv", "Vapor Pressure Pv", default=0.5, min_value=0.0, unit="(psia)"),
        InputSpec("pc", "Critical Pressure Pc", default=3208.0, min_value=0.01, unit="(psia)"),
        InputSpec("fl", "FL — Recovery Factor", default=0.9, min_value=0.01, max_value=1.0, step=0.01),
    ],
    compute=compute_valve_cv_liquid,
    formula_md=(
        r"$$C_v = Q\sqrt{\frac{SG}{\Delta P_{eff}}}$$"
        "\n\nChoked-flow check via the liquid critical pressure ratio factor:"
        r"$$F_F = 0.96 - 0.28\sqrt{P_v/P_c}$$"
        r"Flow chokes when $\Delta P \geq F_L^2(P_1 - F_F P_v)$; if choked, $\Delta P_{eff}$ is capped there."
    ),
    references=[
        "ISA-75.01.01 / IEC 60534-2-1 — Control valve sizing equations",
        "Fisher Control Valve Handbook, 5th Ed.",
    ],
    assumptions=[
        "FL is valve/trim-specific; the default (0.9) is a typical globe-valve value only — use manufacturer data for final sizing.",
        "Single-phase liquid at the valve inlet (no flashing feed).",
    ],
)

TOOL_VALVE_GAS = ToolSpec(
    key="fd_002b",
    title="Control Valve Sizing — Gas/Vapor Cv (ISA-75.01)",
    category="Control Valves",
    description="Required Cv for compressible (gas/vapor) service with choked-flow check.",
    inputs=[
        InputSpec("mass_flow", "Mass Flow Rate", default=5000.0, min_value=0.01, unit="(lb/hr)"),
        InputSpec("p1", "Upstream Pressure P1", default=150.0, min_value=0.01, unit="(psia)"),
        InputSpec("p2", "Downstream Pressure P2", default=100.0, min_value=0.01, unit="(psia)"),
        InputSpec("t1", "Upstream Temperature T1", default=560.0, min_value=1.0, unit="(°R)"),
        InputSpec("sg_gas", "Gas Specific Gravity (vs air)", default=1.0, min_value=0.01, step=0.01),
        InputSpec("z", "Compressibility Factor Z", default=1.0, min_value=0.1, max_value=2.0, step=0.01),
        InputSpec("xt", "XT — Terminal Pressure Drop Ratio", default=0.7, min_value=0.1, max_value=1.0, step=0.01),
        InputSpec("k", "k — Ratio of Specific Heats (Cp/Cv)", default=1.4, min_value=1.0, max_value=1.7, step=0.01),
    ],
    compute=compute_valve_cv_gas,
    formula_md=(
        r"$$C_v = \frac{W}{63.3\, Y \sqrt{x_{eff}\, P_1 \cdot P_1/(SG \cdot T_1 \cdot Z)}}$$"
        r"where $x = \Delta P/P_1$; choking occurs when $x \geq F_k X_T$ ($F_k = k/1.4$); "
        r"expansion factor $Y = 1 - x/(3 F_k X_T)$, bounded to $[0.667, 1.0]$."
    ),
    references=[
        "ISA-75.01.01 / IEC 60534-2-1 — Control valve sizing equations",
        "GPSA Engineering Data Book, Section 3 — Valve sizing",
    ],
    assumptions=[
        "XT is valve/trim-specific — default is a typical globe-valve value only.",
        "Ideal gas compressibility correction (Z) — real-gas deviations at high pressure should use a rigorous EOS if available.",
    ],
)


# =======================================================================
# TOOL 3: NPSH AVAILABLE vs. REQUIRED CHECK
# =======================================================================

def compute_npsh_check(values: dict) -> dict:
    npsha = values["npsha"]
    npshr = values["npshr"]
    margin_target = values["margin_target"]

    has_error, has_warning, errors, warnings = run_validators(
        check_positive(npsha, "NPSH available"),
        check_positive(npshr, "NPSH required"),
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
        "Status": "Adequate" if is_adequate else "INSUFFICIENT — cavitation risk",
        "_warnings": warnings + (
            [f"NPSH margin of {margin:.2f} ft is below the {margin_target:.1f} ft target — "
             "risk of cavitation, vibration, and impeller damage. Consider raising suction "
             "level, reducing suction-side losses, or selecting a lower-NPSHr pump."]
            if not is_adequate else []
        ),
    }


TOOL_NPSH = ToolSpec(
    key="fd_003",
    title="NPSH Available vs. Required Check",
    category="Rotating Equipment",
    description="Compares NPSH available to NPSH required with a configurable minimum design margin.",
    inputs=[
        InputSpec("npsha", "NPSH Available (NPSHa)", default=20.0, min_value=0.01, unit="(ft)"),
        InputSpec("npshr", "NPSH Required (NPSHr)", default=12.0, min_value=0.01, unit="(ft)"),
        InputSpec("margin_target", "Target Minimum Margin", default=3.0, min_value=0.0, unit="(ft)",
                   help="Hydraulic Institute typically recommends 3-5 ft (higher for high suction-energy pumps)."),
    ],
    compute=compute_npsh_check,
    formula_md=r"$$\text{NPSH margin} = \text{NPSH}_a - \text{NPSH}_r$$",
    references=[
        "Hydraulic Institute Standards (ANSI/HI 9.6.1) — NPSH margin guidance",
        "API 610 — Centrifugal Pumps for Petroleum, Petrochemical and Natural Gas Industries",
    ],
    assumptions=[
        "NPSHa must be independently calculated from the actual suction system (elevation, friction losses, vapor pressure) — this tool only compares the two values.",
        "Higher margins are recommended for high suction-energy pumps per HI 9.6.1 — 3 ft is a generic default, not a universal minimum.",
    ],
)


# =======================================================================
# TOOL 4: TWO-PHASE PRESSURE DROP (Lockhart-Martinelli)
# =======================================================================

def compute_twophase_pressure_drop(values: dict) -> dict:
    w_l = values["w_l"]          # Liquid mass flow kg/h
    w_v = values["w_v"]          # Vapor mass flow kg/h
    rho_l = values["rho_l"]      # Liquid density kg/m3
    rho_v = values["rho_v"]      # Vapor density kg/m3
    mu_l = values["mu_l"]        # Liquid viscosity Pa.s
    mu_v = values["mu_v"]        # Vapor viscosity Pa.s
    d = values["diameter"]       # Pipe ID m
    length = values["length"]    # Pipe length m
    roughness = values["roughness"] # Roughness m

    has_error, _, errors, warnings = run_validators(
        check_positive(w_l, "Liquid Mass Flow"),
        check_positive(w_v, "Vapor Mass Flow"),
        check_positive(rho_l, "Liquid Density"),
        check_positive(rho_v, "Vapor Density"),
        check_positive(mu_l, "Liquid Viscosity"),
        check_positive(mu_v, "Vapor Viscosity"),
        check_positive(d, "Diameter"),
        check_positive(length, "Length"),
    )
    if has_error:
        raise ValueError("; ".join(errors))

    area = (math.pi / 4.0) * (d ** 2)
    
    # Superficial velocities (m/s)
    v_sl = (w_l / 3600.0) / (rho_l * area)
    v_sg = (w_v / 3600.0) / (rho_v * area)

    # Reynolds numbers for liquid and gas phases acting alone
    re_l = (rho_l * v_sl * d) / mu_l
    re_v = (rho_v * v_sg * d) / mu_v

    # Single-phase friction factors
    f_l = 64.0 / re_l if re_l < 2300 else 0.25 / (math.log10((roughness / d / 3.7) + (5.74 / re_l ** 0.9))) ** 2
    f_v = 64.0 / re_v if re_v < 2300 else 0.25 / (math.log10((roughness / d / 3.7) + (5.74 / re_v ** 0.9))) ** 2

    # Single-phase pressure drops (Pa)
    dp_l = f_l * (length / d) * (rho_l * v_sl ** 2 / 2.0)
    dp_v = f_v * (length / d) * (rho_v * v_sg ** 2 / 2.0)

    # Lockhart-Martinelli parameter X
    x_lm = math.sqrt(dp_l / dp_v) if dp_v > 0 else 1.0

    # Chisholm C-parameter determination based on flow regime combinations
    l_turb = re_l >= 2300
    v_turb = re_v >= 2300
    if l_turb and v_turb:
        c_param = 20.0
    elif not l_turb and v_turb:
        c_param = 12.0
    elif l_turb and not v_turb:
        c_param = 10.0
    else:
        c_param = 5.0

    # Two-phase liquid multiplier phi_l^2
    phi_l_sq = 1.0 + (c_param / x_lm) + (1.0 / (x_lm ** 2))
    dp_tp_pa = dp_l * phi_l_sq

    return {
        "Superficial Liquid Velocity (m/s)": round(v_sl, 2),
        "Superficial Gas Velocity (m/s)": round(v_sg, 2),
        "Lockhart-Martinelli Parameter (X)": round(x_lm, 3),
        "Two-Phase Multiplier (Phi_L^2)": round(phi_l_sq, 2),
        "Two-Phase Pressure Drop (kPa)": round(dp_tp_pa / 1000.0, 2),
        "Two-Phase Pressure Drop (psi)": round(dp_tp_pa / 6894.757, 2),
        "_warnings": warnings,
    }


TOOL_TWOPHASE_PRESSURE_DROP = ToolSpec(
    key="fd_004",
    title="Two-Phase Pressure Drop (Lockhart-Martinelli)",
    category="Piping Hydraulics",
    description="Calculates horizontal two-phase gas-liquid frictional pressure drop using Chisholm's Lockhart-Martinelli correlation.",
    inputs=[
        InputSpec("w_l", "Liquid Mass Flow", default=50000.0, min_value=0.1, unit="(kg/h)"),
        InputSpec("w_v", "Vapor Mass Flow", default=2500.0, min_value=0.1, unit="(kg/h)"),
        InputSpec("rho_l", "Liquid Density", default=800.0, min_value=1.0, unit="(kg/m3)"),
        InputSpec("rho_v", "Vapor Density", default=15.0, min_value=0.01, unit="(kg/m3)"),
        InputSpec("mu_l", "Liquid Viscosity", default=0.001, min_value=1e-6, unit="(Pa·s)"),
        InputSpec("mu_v", "Vapor Viscosity", default=0.000015, min_value=1e-7, unit="(Pa·s)"),
        InputSpec("diameter", "Pipe Internal Diameter", default=0.154, min_value=0.001, unit="(m)"),
        InputSpec("length", "Pipe Length", default=200.0, min_value=0.1, unit="(m)"),
        InputSpec("roughness", "Pipe Roughness", default=0.000045, min_value=0.0, unit="(m)"),
    ],
    compute=compute_twophase_pressure_drop,
    formula_md=(
        r"$$X^2 = \frac{(\Delta P/\Delta L)_L}{(\Delta P/\Delta L)_G}, \quad \Phi_L^2 = 1 + \frac{C}{X} + \frac{1}{X^2}$$"
        "\n\n"
        r"$$\Delta P_{TP} = \Phi_L^2 \cdot \Delta P_L$$"
    ),
    references=[
        "Lockhart, R.W. and Martinelli, R.C. (1949), Chem. Eng. Prog.",
        "Chisholm, D. (1967), Int. J. Heat Mass Transfer",
    ],
    assumptions=[
        "Horizontal pipe orientation (no elevation head changes).",
        "Steady-state non-boiling and non-condensing adiabatic flow.",
    ],
)


# =======================================================================
# TOOL 5: PUMP POWER & EFFICIENCY CALCULATION
# =======================================================================

def compute_pump_power(values: dict) -> dict:
    q_m3h = values["flow_m3h"]     # m3/h
    head_m = values["head_m"]      # meters
    rho = values["rho"]            # kg/m3
    eta_pump = values["eta_pump"]  # %
    eta_motor = values["eta_motor"]# %

    has_error, _, errors, warnings = run_validators(
        check_positive(q_m3h, "Flow Rate"),
        check_positive(head_m, "Total Dynamic Head"),
        check_positive(rho, "Fluid Density"),
        check_efficiency(eta_pump, "Pump Efficiency"),
        check_efficiency(eta_motor, "Motor Efficiency"),
    )
    if has_error:
        raise ValueError("; ".join(errors))

    q_m3s = q_m3h / 3600.0
    mass_flow = q_m3s * rho  # kg/s

    # Hydraulic power (W)
    p_hydraulic = mass_flow * 9.81 * head_m  # Watts
    
    # Brake Horsepower / Shaft Power (kW)
    p_shaft_kw = (p_hydraulic / (eta_pump / 100.0)) / 1000.0
    
    # Electrical Power (kW)
    p_elec_kw = (p_shaft_kw / (eta_motor / 100.0))
    p_elec_hp = p_elec_kw * 1.34102

    return {
        "Hydraulic Power (kW)": round(p_hydraulic / 1000.0, 2),
        "Shaft Power / Brake kW (kW)": round(p_shaft_kw, 2),
        "Electrical Power (kW)": round(p_elec_kw, 2),
        "Electrical Power (hp)": round(p_elec_hp, 2),
        "Overall Wire-to-Water Efficiency (%)": round((eta_pump / 100.0) * (eta_motor / 100.0) * 100.0, 1),
        "_warnings": warnings,
    }


TOOL_PUMP_POWER = ToolSpec(
    key="fd_005",
    title="Pump Power, Sizing & Efficiency Calculation",
    category="Rotating Equipment",
    description="Calculates hydraulic power, shaft power (BHP), and electrical motor consumption given dynamic head and efficiency.",
    inputs=[
        InputSpec("flow_m3h", "Volumetric Flow Rate", default=120.0, min_value=0.1, unit="(m3/h)"),
        InputSpec("head_m", "Total Dynamic Head (TDH)", default=45.0, min_value=0.1, unit="(m)"),
        InputSpec("rho", "Fluid Density", default=1000.0, min_value=1.0, unit="(kg/m3)"),
        InputSpec("eta_pump", "Pump Hydraulic Efficiency", default=75.0, min_value=1.0, max_value=100.0, unit="(%)"),
        InputSpec("eta_motor", "Electrical Motor Efficiency", default=92.0, min_value=1.0, max_value=100.0, unit="(%)"),
    ],
    compute=compute_pump_power,
    formula_md=(
        r"$$P_{hyd} = \rho \cdot g \cdot Q \cdot H$$"
        "\n\n"
        r"$$P_{shaft} = \frac{P_{hyd}}{\eta_{pump}}, \quad P_{elec} = \frac{P_{shaft}}{\eta_{motor}}$$"
    ),
    references=[
        "Perry's Chemical Engineers' Handbook, Section 10",
        "Igor J. Karassik, Pump Handbook, 4th Edition",
    ],
    assumptions=[
        "Incompressible, steady-state fluid delivery.",
        "Total Dynamic Head (TDH) includes static elevation lift and suction/discharge friction losses.",
    ],
)


# =======================================================================
# TOOL 6: WATER HAMMER & SURGE PRESSURE PEAK ANALYSIS (Joukowsky)
# =======================================================================

PIPE_MATERIAL_E_PA = {
    "Steel": 200e9,
    "Ductile Iron": 166e9,
    "Copper": 117e9,
    "PVC": 3.0e9,
    "HDPE": 0.9e9,
}


def compute_water_hammer(values: dict) -> dict:
    rho = values["fluid_density"]              # kg/m3
    bulk_modulus = values["bulk_modulus"] * 1e9  # input in GPa -> Pa
    material = values["pipe_material"]
    diameter_mm = values["diameter_mm"]
    wall_thickness_mm = values["wall_thickness_mm"]
    velocity_change = values["velocity_change"]  # m/s
    pipe_length_m = values["pipe_length"]         # m
    closure_time_s = values["closure_time"]       # s
    static_pressure_kpa = values["static_pressure"]  # kPa

    has_error, has_warning, errors, warnings = run_validators(
        check_positive(rho, "Fluid density"),
        check_positive(bulk_modulus, "Bulk modulus"),
        check_positive(diameter_mm, "Pipe diameter"),
        check_positive(wall_thickness_mm, "Wall thickness"),
        check_positive(pipe_length_m, "Pipe length"),
        check_positive(closure_time_s, "Closure time"),
    )
    if has_error:
        raise ValueError("; ".join(errors))
    if velocity_change <= 0:
        raise ValueError("Velocity change must be greater than zero (the flow velocity being arrested).")

    e_pipe = PIPE_MATERIAL_E_PA.get(material)
    if e_pipe is None:
        raise ValueError(f"Unknown pipe material: {material}")

    d_m = diameter_mm / 1000.0
    e_wall_m = wall_thickness_mm / 1000.0

    a = math.sqrt(
        (bulk_modulus / rho) / (1 + (bulk_modulus * d_m) / (e_pipe * e_wall_m))
    )

    t_critical = (2 * pipe_length_m) / a
    is_rapid_closure = closure_time_s <= t_critical

    dp_joukowsky_pa = rho * a * velocity_change

    if is_rapid_closure:
        dp_surge_pa = dp_joukowsky_pa
    else:
        dp_surge_pa = dp_joukowsky_pa * (t_critical / closure_time_s)

    dp_surge_kpa = dp_surge_pa / 1000.0
    dp_surge_psi = dp_surge_pa / 6894.757
    peak_pressure_kpa = static_pressure_kpa + dp_surge_kpa

    extra_warnings = []
    if is_rapid_closure:
        extra_warnings.append(
            f"Closure time ({closure_time_s:.3f}s) is at or below the critical reflection time "
            f"({t_critical:.3f}s) - this is a RAPID closure. Full Joukowsky surge pressure applies; "
            "consider a slower valve/actuator or a surge relief device if this pressure is unacceptable."
        )

    return {
        "Pressure Wave Speed 'a' (m/s)": round(a, 1),
        "Critical (Reflection) Time (s)": round(t_critical, 3),
        "Closure Type": "RAPID (full Joukowsky)" if is_rapid_closure else "Slow (attenuated surge)",
        "Surge Pressure Rise (kPa)": round(dp_surge_kpa, 1),
        "Surge Pressure Rise (psi)": round(dp_surge_psi, 1),
        "Peak Pressure (Static + Surge, kPa)": round(peak_pressure_kpa, 1),
        "_warnings": warnings + extra_warnings,
    }


TOOL_WATER_HAMMER = ToolSpec(
    key="fd_006",
    title="Water Hammer & Surge Pressure Peak Analysis",
    category="Piping Hydraulics",
    description="Joukowsky surge pressure with Korteweg wave-speed correction and rapid/slow valve-closure check.",
    inputs=[
        InputSpec("fluid_density", "Fluid Density", default=998.0, min_value=1.0, unit="(kg/m3)"),
        InputSpec("bulk_modulus", "Fluid Bulk Modulus", default=2.15, min_value=0.01, unit="(GPa)",
                   help="Water at ambient conditions: ~2.15 GPa."),
        InputSpec("pipe_material", "Pipe Material", default="Steel", input_type="select",
                   options=list(PIPE_MATERIAL_E_PA.keys())),
        InputSpec("diameter_mm", "Pipe Internal Diameter", default=150.0, min_value=1.0, unit="(mm)"),
        InputSpec("wall_thickness_mm", "Pipe Wall Thickness", default=6.0, min_value=0.5, unit="(mm)"),
        InputSpec("velocity_change", "Velocity Change (arrested flow)", default=2.0, min_value=0.01, unit="(m/s)"),
        InputSpec("pipe_length", "Pipe Length (source to valve)", default=500.0, min_value=1.0, unit="(m)"),
        InputSpec("closure_time", "Valve Closure Time", default=0.3, min_value=0.001, unit="(s)",
                   help="Time for the valve to fully close. Compare against critical time."),
        InputSpec("static_pressure", "Static Operating Pressure", default=500.0, min_value=0.0, unit="(kPa)"),
    ],
    compute=compute_water_hammer,
    formula_md=(
        r"$$a = \sqrt{\dfrac{K/\rho}{1 + \dfrac{K \cdot D}{E \cdot e}}}, \quad t_c = \dfrac{2L}{a}, \quad \Delta P = \rho \cdot a \cdot \Delta v$$"
    ),
    references=[
        "Wylie, E.B. & Streeter, V.L., Fluid Transients in Systems",
        "AWWA Manual M11 — Steel Pipe Design",
    ],
    assumptions=[
        "Pipe restraint factor c1 = 1.0 (anchored pipe).",
        "Linear velocity attenuation during valve stroke.",
    ],
)


# =======================================================================
# TOOL 7: COMPRESSIBLE GAS FLOW & LINE SIZING (Weymouth)
# =======================================================================

def compute_weymouth_gas_flow(values: dict) -> dict:
    p1 = values["p1"]          # kPa abs
    p2 = values["p2"]          # kPa abs
    d_mm = values["d_mm"]      # mm
    length_km = values["length_km"] # km
    sg_gas = values["sg_gas"]  # vs Air
    temp_k = values["temp_k"]  # Kelvin
    z = values["z"]            # Compressibility

    has_error, _, errors, warnings = run_validators(
        check_pressure_drop(p1, p2, "Gas Line Pressure"),
        check_positive(d_mm, "Diameter"),
        check_positive(length_km, "Length"),
        check_positive(sg_gas, "Gas SG"),
        check_positive(temp_k, "Temperature"),
    )
    if has_error:
        raise ValueError("; ".join(errors))

    # Convert units to customary Weymouth equation constants:
    # P in psia, D in inches, L in miles, T in deg R
    p1_psi = p1 / 6.89476
    p2_psi = p2 / 6.89476
    d_in = d_mm / 25.4
    l_mi = length_km * 0.621371
    t_r = temp_k * 1.8

    # Weymouth volumetric capacity Q in SCFD
    term = (p1_psi**2 - p2_psi**2) / (sg_gas * t_r * l_mi * z)
    if term <= 0:
        raise ValueError("Non-positive pressure term in Weymouth formula.")

    q_scfd = 433.5 * ((520.0 / 520.0) ** 1.0) * (d_in ** (16.0 / 3.0)) * math.sqrt(term)
    q_m3d = q_scfd * 0.0283168  # Standard m3/day

    # Average pressure and superficial velocity at midpoint
    p_avg_psi = (2.0 / 3.0) * (p1_psi + (p2_psi ** 2) / (p1_psi + p2_psi))
    p_avg_kpa = p_avg_psi * 6.89476
    
    # Velocity at line outlet (highest velocity point)
    area_m2 = (math.pi / 4.0) * ((d_mm / 1000.0) ** 2)
    q_actual_m3s = (q_m3d / 86400.0) * (101.325 / p2) * (temp_k / 288.15) * z
    v_outlet = q_actual_m3s / area_m2

    extra_warnings = []
    if v_outlet > 20.0:
        extra_warnings.append(
            f"Outlet velocity ({v_outlet:.1f} m/s) exceeds recommended noise/erosion limit (~15-20 m/s)."
        )

    return {
        "Gas Flow Capacity (MSCFD)": round(q_scfd / 1000.0, 1),
        "Gas Flow Capacity (Sm3/day)": round(q_m3d, 1),
        "Average Line Pressure (kPa abs)": round(p_avg_kpa, 1),
        "Outlet Line Velocity (m/s)": round(v_outlet, 2),
        "_warnings": warnings + extra_warnings,
    }


TOOL_WEYMOUTH_GAS = ToolSpec(
    key="fd_007",
    title="Compressible Gas Flow & Line Sizing (Weymouth)",
    category="Piping Hydraulics",
    description="Sizes high-pressure gas transmission pipelines using the Weymouth compressible flow equation.",
    inputs=[
        InputSpec("p1", "Inlet Pressure P1", default=5000.0, min_value=10.0, unit="(kPa abs)"),
        InputSpec("p2", "Outlet Pressure P2", default=3500.0, min_value=5.0, unit="(kPa abs)"),
        InputSpec("d_mm", "Pipe Internal Diameter", default=200.0, min_value=10.0, unit="(mm)"),
        InputSpec("length_km", "Pipeline Length", default=10.0, min_value=0.01, unit="(km)"),
        InputSpec("sg_gas", "Gas Specific Gravity (Air=1.0)", default=0.65, min_value=0.1, step=0.01),
        InputSpec("temp_k", "Gas Flow Temperature", default=300.0, min_value=200.0, unit="(K)"),
        InputSpec("z", "Gas Compressibility Z", default=0.90, min_value=0.2, max_value=1.5, step=0.01),
    ],
    compute=compute_weymouth_gas_flow,
    formula_md=(
        r"$$Q = 433.5 \left(\frac{T_b}{P_b}\right) D^{16/3} \left[\frac{P_1^2 - P_2^2}{\gamma_g \cdot T \cdot L \cdot Z}\right]^{0.5}$$"
    ),
    references=[
        "GPSA Engineering Data Book, Section 17",
        "Crane Technical Paper No. 410",
    ],
    assumptions=[
        "Isothermal, steady-state compressible gas flow.",
        "Fully turbulent flow regime (Weymouth friction factor assumption).",
    ],
)


# =======================================================================
# TOOL 8: EQUIVALENT LENGTH & FITTING LOSSES (3K Method)
# =======================================================================

FITTING_3K_PARAMS = {
    "90 deg Standard Elbow": {"k1": 800.0, "ki": 0.14, "kd": 4.0},
    "90 deg Long Radius Elbow": {"k1": 800.0, "ki": 0.09, "kd": 4.0},
    "45 deg Standard Elbow": {"k1": 500.0, "ki": 0.04, "kd": 4.0},
    "Tee (Through Run)": {"k1": 150.0, "ki": 0.05, "kd": 4.0},
    "Tee (Through Branch)": {"k1": 1000.0, "ki": 0.34, "kd": 4.0},
    "Globe Valve (Full Open)": {"k1": 1500.0, "ki": 1.70, "kd": 3.6},
    "Gate Valve (Full Open)": {"k1": 300.0, "ki": 0.03, "kd": 3.9},
    "Check Valve (Swing)": {"k1": 1500.0, "ki": 0.40, "kd": 3.5},
}


def compute_3k_fitting_loss(values: dict) -> dict:
    fitting_type = values["fitting_type"]
    count = values["count"]
    d_mm = values["d_mm"]          # mm
    rho = values["rho"]            # kg/m3
    v = values["velocity"]         # m/s
    mu = values["viscosity"]       # Pa.s

    has_error, _, errors, warnings = run_validators(
        check_positive(count, "Fitting Count"),
        check_positive(d_mm, "Diameter"),
        check_positive(rho, "Density"),
        check_positive(v, "Velocity"),
        check_positive(mu, "Viscosity"),
    )
    if has_error:
        raise ValueError("; ".join(errors))

    params = FITTING_3K_PARAMS.get(fitting_type)
    if not params:
        raise ValueError(f"Unknown fitting type selected: {fitting_type}")

    d_in = d_mm / 25.4
    d_m = d_mm / 1000.0
    re = (rho * v * d_m) / mu

    # Darby 3K correlation formula for fitting K-factor
    k_single = (params["k1"] / re) + params["ki"] * (1.0 + params["kd"] / (d_in ** 0.3))
    k_total = k_single * count

    # Pressure drop = K * (rho * v^2 / 2)
    dp_pa = k_total * (rho * (v ** 2) / 2.0)
    
    # Equivalent length L_eq = K * D / f (assuming generic f = 0.018)
    l_eq = (k_total * d_m) / 0.018

    return {
        "Single Fitting K-Factor": round(k_single, 3),
        "Total Fitting K-Factor": round(k_total, 3),
        "Pressure Drop (kPa)": round(dp_pa / 1000.0, 2),
        "Pressure Drop (psi)": round(dp_pa / 6894.757, 2),
        "Equivalent Pipe Length (m)": round(l_eq, 2),
        "_warnings": warnings,
    }


TOOL_3K_FITTINGS = ToolSpec(
    key="fd_008",
    title="Fitting Loss & Equivalent Length (Darby 3K)",
    category="Piping Hydraulics",
    description="Accurate fitting pressure drop and resistance factors using Darby's 3K method accounting for pipe diameter and Reynolds number.",
    inputs=[
        InputSpec("fitting_type", "Fitting Selection", default="90 deg Standard Elbow", input_type="select",
                   options=list(FITTING_3K_PARAMS.keys())),
        InputSpec("count", "Quantity of Fittings", default=4.0, min_value=1.0, step=1.0),
        InputSpec("d_mm", "Internal Diameter", default=100.0, min_value=1.0, unit="(mm)"),
        InputSpec("rho", "Fluid Density", default=1000.0, min_value=1.0, unit="(kg/m3)"),
        InputSpec("velocity", "Flow Velocity", default=2.5, min_value=0.01, unit="(m/s)"),
        InputSpec("viscosity", "Dynamic Viscosity", default=0.001, min_value=1e-6, unit="(Pa·s)"),
    ],
    compute=compute_3k_fitting_loss,
    formula_md=(
        r"$$K = \frac{K_1}{Re} + K_i \left(1 + \frac{K_d}{D_{in}^{0.3}}\right), \quad \Delta P = K_{total} \frac{\rho v^2}{2}$$"
    ),
    references=[
        "Darby, R. (2001), Chemical Engineering Fluid Mechanics",
        "Perry's Chemical Engineers' Handbook, Section 6",
    ],
    assumptions=[
        "Fully developed flow entering the fitting.",
        "Fits standard industrial commercial steel or smooth internal pipe geometries.",
    ],
)


# =======================================================================
# TOOL 9: GRAVITY FLOW & DRAIN LINE SIZING (Manning Equation)
# =======================================================================

def compute_manning_gravity_flow(values: dict) -> dict:
    d_mm = values["d_mm"]          # Pipe internal diameter mm
    slope = values["slope"]        # m/m
    n_manning = values["n_manning"]# Manning roughness
    fill_ratio = values["fill_ratio"] / 100.0 # percentage -> ratio

    has_error, _, errors, warnings = run_validators(
        check_positive(d_mm, "Diameter"),
        check_positive(slope, "Slope"),
        check_positive(n_manning, "Manning 'n'"),
        check_fraction_0_1(fill_ratio, "Pipe Fill Ratio"),
    )
    if has_error:
        raise ValueError("; ".join(errors))

    d_m = d_mm / 1000.0
    r_m = d_m / 2.0  # Pipe radius

    # Full pipe hydraulic parameters
    a_full = (math.pi / 4.0) * (d_m ** 2)
    p_full = math.pi * d_m

    # Partially filled pipe geometry (depth y = fill_ratio * D)
    theta = 2.0 * math.acos(1.0 - 2.0 * fill_ratio)  # central angle in radians
    a_partial = (r_m ** 2) * (theta - math.sin(theta)) / 2.0
    p_partial = r_m * theta
    rh_partial = a_partial / p_partial if p_partial > 0 else 0.0

    # Manning equation: Velocity v = (1 / n) * Rh^(2/3) * S^(1/2)
    v_partial = (1.0 / n_manning) * (rh_partial ** (2/3)) * math.sqrt(slope)
    q_m3s = a_partial * v_partial
    q_m3h = q_m3s * 3600.0

    extra_warnings = []
    if v_partial < 0.6:
        extra_warnings.append(
            f"Low flow velocity ({v_partial:.2f} m/s) — self-cleaning threshold (~0.6 m/s) not met; potential for solids deposition."
        )
    if v_partial > 3.0:
        extra_warnings.append(
            f"High flow velocity ({v_partial:.2f} m/s) — check for drain line invert scouring/erosion risk."
        )

    return {
        "Flow Velocity (m/s)": round(v_partial, 2),
        "Volumetric Capacity (m3/h)": round(q_m3h, 1),
        "Volumetric Capacity (USGPM)": round(q_m3h * 4.40287, 1),
        "Hydraulic Radius (m)": round(rh_partial, 4),
        "Self-Cleaning Velocity Met?": "Yes" if v_partial >= 0.6 else "No (Solids Risk)",
        "_warnings": warnings + extra_warnings,
    }


TOOL_MANNING_DRAIN = ToolSpec(
    key="fd_009",
    title="Gravity Flow & Drain Line Sizing (Manning)",
    category="Piping Hydraulics",
    description="Sizes partially-filled gravity drain lines, sewers, and plant run-off piping using the Manning equation.",
    inputs=[
        InputSpec("d_mm", "Pipe Internal Diameter", default=200.0, min_value=10.0, unit="(mm)"),
        InputSpec("slope", "Line Slope (m/m or ft/ft)", default=0.01, min_value=0.0001, max_value=0.2, step=0.001),
        InputSpec("n_manning", "Manning Roughness Coefficient n", default=0.012, min_value=0.005, max_value=0.03, step=0.001,
                   help="Smooth plastic/steel = 0.010-0.012, Concrete/Cast Iron = 0.013-0.015"),
        InputSpec("fill_ratio", "Pipe Fill Depth (% of D)", default=75.0, min_value=10.0, max_value=99.0, unit="(%)"),
    ],
    compute=compute_manning_gravity_flow,
    formula_md=(
        r"$$V = \frac{1}{n} R_h^{2/3} S^{1/2}, \quad Q = A \cdot V$$"
    ),
    references=[
        "Chow, V.T., Open-Channel Hydraulics",
        "ASCE Manuals and Reports on Engineering Practice No. 60",
    ],
    assumptions=[
        "Uniform, steady open-channel flow in circular conduit.",
        "Newtonian liquid behaving primarily as water.",
    ],
)


# =======================================================================
# TOOL 10: PITOT TUBE & FLOW METER VELOCITY SIZING
# =======================================================================

def compute_dp_flowmeter(values: dict) -> dict:
    dp_mbar = values["dp_mbar"]    # Differential pressure mbar
    rho = values["rho"]            # Fluid density kg/m3
    cd = values["cd"]              # Discharge coefficient Cd
    pipe_d_mm = values["pipe_d_mm"]# Pipe ID mm
    throat_d_mm = values["throat_d_mm"] # Orifice/throat diameter mm

    has_error, _, errors, warnings = run_validators(
        check_positive(dp_mbar, "Differential Pressure"),
        check_positive(rho, "Fluid Density"),
        check_positive(cd, "Discharge Coefficient"),
        check_positive(pipe_d_mm, "Pipe Diameter"),
        check_positive(throat_d_mm, "Throat/Orifice Diameter"),
    )
    if has_error:
        raise ValueError("; ".join(errors))

    if throat_d_mm >= pipe_d_mm:
        raise ValueError("Throat/Orifice diameter must be strictly smaller than pipe diameter.")

    dp_pa = dp_mbar * 100.0  # mbar -> Pa
    beta = throat_d_mm / pipe_d_mm
    
    # Velocity approach factor (E)
    e_factor = 1.0 / math.sqrt(1.0 - (beta ** 4))

    # Flow velocity through throat (m/s)
    v_throat = cd * e_factor * math.sqrt(2.0 * dp_pa / rho)
    
    # Flow velocity in main line (m/s)
    v_line = v_throat * (beta ** 2)

    # Volumetric flow rate
    area_pipe = (math.pi / 4.0) * ((pipe_d_mm / 1000.0) ** 2)
    q_m3s = area_pipe * v_line
    q_m3h = q_m3s * 3600.0

    return {
        "Beta Ratio (d/D)": round(beta, 3),
        "Velocity Approach Factor (E)": round(e_factor, 3),
        "Line Flow Velocity (m/s)": round(v_line, 2),
        "Throat/Orifice Velocity (m/s)": round(v_throat, 2),
        "Volumetric Flow Rate (m3/h)": round(q_m3h, 1),
        "Volumetric Flow Rate (USGPM)": round(q_m3h * 4.40287, 1),
        "_warnings": warnings,
    }


TOOL_DP_FLOWMETER = ToolSpec(
    key="fd_010",
    title="Pitot Tube & Flow Meter Delta-P Velocity Sizing",
    category="Instrumentation & Measurement",
    description="Calculates fluid velocity and volumetric flow rate from differential pressure measurement devices (Pitot tubes, Orifice plates, Venturis).",
    inputs=[
        InputSpec("dp_mbar", "Differential Pressure (ΔP)", default=250.0, min_value=0.1, unit="(mbar)"),
        InputSpec("rho", "Fluid Density", default=1000.0, min_value=0.1, unit="(kg/m3)"),
        InputSpec("cd", "Discharge Coefficient (Cd)", default=0.61, min_value=0.1, max_value=1.0, step=0.01,
                   help="Orifice plate ~ 0.60-0.62, Venturi ~ 0.98, Pitot ~ 0.99"),
        InputSpec("pipe_d_mm", "Pipe Internal Diameter D", default=150.0, min_value=10.0, unit="(mm)"),
        InputSpec("throat_d_mm", "Throat / Orifice Diameter d", default=90.0, min_value=5.0, unit="(mm)"),
    ],
    compute=compute_dp_flowmeter,
    formula_md=(
        r"$$\beta = \frac{d}{D}, \quad E = \frac{1}{\sqrt{1-\beta^4}}, \quad v_{throat} = C_d E \sqrt{\frac{2 \Delta P}{\rho}}$$"
    ),
    references=[
        "ISO 5167-1 — Measurement of fluid flow by means of pressure differential devices",
        "Miller, R.W., Flow Measurement Engineering Handbook",
    ],
    assumptions=[
        "Incompressible, steady-state single-phase liquid or low-DP gas flow.",
        "Fully developed turbulent velocity profile upstream of elements.",
    ],
)


# =======================================================================
# DOMAIN REGISTRY
# =======================================================================

REGISTRY: dict[str, ToolSpec] = {
    TOOL_PRESSURE_DROP.key: TOOL_PRESSURE_DROP,               # fd_001
    TOOL_VALVE_LIQUID.key: TOOL_VALVE_LIQUID,                 # fd_002a
    TOOL_VALVE_GAS.key: TOOL_VALVE_GAS,                       # fd_002b
    TOOL_NPSH.key: TOOL_NPSH,                                 # fd_003
    TOOL_TWOPHASE_PRESSURE_DROP.key: TOOL_TWOPHASE_PRESSURE_DROP, # fd_004
    TOOL_PUMP_POWER.key: TOOL_PUMP_POWER,                     # fd_005
    TOOL_WATER_HAMMER.key: TOOL_WATER_HAMMER,                 # fd_006
    TOOL_WEYMOUTH_GAS.key: TOOL_WEYMOUTH_GAS,                 # fd_007
    TOOL_3K_FITTINGS.key: TOOL_3K_FITTINGS,                   # fd_008
    TOOL_MANNING_DRAIN.key: TOOL_MANNING_DRAIN,               # fd_009
    TOOL_DP_FLOWMETER.key: TOOL_DP_FLOWMETER,                 # fd_010
}
