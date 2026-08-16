"""
calculators/fluid_dynamics_engine.py
======================================
Houses calculation logic for tools #1-75 (Fluid Dynamics domain).

This file demonstrates the full pattern: each tool is a pure `compute_*`
function (input dict -> result dict, no Streamlit/UI code) plus a
ToolSpec entry in REGISTRY describing its inputs and documentation. The
page file (pages/1_🌊_Fluid_Dynamics.py) never needs to change when a
new tool is added here — it just iterates REGISTRY.

Only 3 tools are fully implemented below (as required for the initial
deliverable); the REGISTRY dict is exactly where tools #4 through #75
would be added, following the identical pattern.
"""

import math
from calculators.registry_base import ToolSpec, InputSpec
from utils.validators import (
    check_positive, check_pressure_drop, check_efficiency,
    check_specific_gravity, check_reynolds_regime, run_validators,
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
# TOOL 6: WATER HAMMER & SURGE PRESSURE PEAK ANALYSIS (Joukowsky)
# =======================================================================

# Modulus of elasticity (E) by pipe material, Pa. Used to compute the
# pressure-wave speed via the Korteweg formula (accounts for pipe wall
# elasticity reducing the effective wave speed vs. rigid-pipe acoustic
# velocity).
PIPE_MATERIAL_E_PA = {
    "Steel": 200e9,
    "Ductile Iron": 166e9,
    "Copper": 117e9,
    "PVC": 3.0e9,
    "HDPE": 0.9e9,
}


def compute_water_hammer(values: dict) -> dict:
    """
    Joukowsky surge pressure with the Korteweg wave-speed correction for
    pipe wall elasticity, plus a rapid-vs-slow valve closure check
    (Allievi criterion: instantaneous-closure formula only applies when
    actual closure time <= critical/reflection time 2L/a).

    Internal units: SI (Pa, m, m/s, kg/m3) — results converted to psi/
    bar for display, matching the rest of the suite's convention.
    """
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

    # Korteweg wave speed (m/s) — c1 (pipe restraint factor) taken as 1.0
    # (typical assumption for a pipe anchored throughout its length).
    a = math.sqrt(
        (bulk_modulus / rho) / (1 + (bulk_modulus * d_m) / (e_pipe * e_wall_m))
    )

    # Critical (pipe reflection) time — the threshold between "rapid"
    # (instantaneous-equivalent) and "slow" valve closure, per the
    # Allievi/Joukowsky criterion.
    t_critical = (2 * pipe_length_m) / a
    is_rapid_closure = closure_time_s <= t_critical

    # Joukowsky surge pressure (full, instantaneous-closure case)
    dp_joukowsky_pa = rho * a * velocity_change

    if is_rapid_closure:
        dp_surge_pa = dp_joukowsky_pa
    else:
        # Standard engineering approximation for slow closure: surge
        # pressure scales down roughly linearly with (t_critical / t_closure).
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
        InputSpec("pipe_material", "Pipe Material", default=0.0, input_type="select",
                   options=list(PIPE_MATERIAL_E_PA.keys())),
        InputSpec("diameter_mm", "Pipe Internal Diameter", default=150.0, min_value=1.0, unit="(mm)"),
        InputSpec("wall_thickness_mm", "Pipe Wall Thickness", default=6.0, min_value=0.5, unit="(mm)"),
        InputSpec("velocity_change", "Velocity Change (arrested flow)", default=2.0, min_value=0.01, unit="(m/s)"),
        InputSpec("pipe_length", "Pipe Length (source to valve)", default=500.0, min_value=1.0, unit="(m)"),
        InputSpec("closure_time", "Valve Closure Time", default=0.3, min_value=0.001, unit="(s)",
                   help="Time for the valve to fully close. Compare against the calculated critical (reflection) time to see whether this counts as 'rapid' closure."),
        InputSpec("static_pressure", "Static Operating Pressure", default=500.0, min_value=0.0, unit="(kPa)"),
    ],
    compute=compute_water_hammer,
    formula_md=(
        r"**Korteweg wave speed** (accounts for pipe wall elasticity):"
        "\n\n"
        r"$$a = \sqrt{\dfrac{K/\rho}{1 + \dfrac{K \cdot D}{E \cdot e}}}$$"
        "\n\n**Critical (reflection) time:**"
        "\n\n"
        r"$$t_c = \dfrac{2L}{a}$$"
        "\n\n**Joukowsky surge pressure** (rapid closure, $t_{close} \\leq t_c$):"
        "\n\n"
        r"$$\Delta P = \rho \cdot a \cdot \Delta v$$"
        "\n\nFor slow closure ($t_{close} > t_c$), surge pressure is approximated as "
        r"$\Delta P \times (t_c/t_{close})$ — a standard linear-attenuation engineering approximation."
    ),
    references=[
        "Wylie, E.B. & Streeter, V.L., *Fluid Transients in Systems*",
        "AWWA Manual M11 — Steel Pipe: A Guide for Design and Installation",
        "Parmakian, J., *Waterhammer Analysis*",
    ],
    assumptions=[
        "Pipe restraint factor c1 = 1.0 (fully anchored/restrained pipe) — unrestrained or partially restrained pipe reduces effective wave speed further.",
        "Slow-closure surge attenuation uses the common linear (t_c/t_close) approximation, not a full method-of-characteristics transient solution — for critical/high-consequence lines, run a full transient (surge) analysis.",
        "Single, uniform pipe segment (no branches, no elevation profile, no air valves/surge vessels modeled).",
        "Instantaneous full velocity arrest assumed for Delta-v — partial closures need the actual achieved velocity change.",
    ],
)


# =======================================================================
# REGISTRY — tools #1-75 for the Fluid Dynamics domain.
# Only a subset are populated below; the rest follow the identical
# pattern: define compute_xxx(values) -> dict, then a ToolSpec, then add
# it here.
# =======================================================================

REGISTRY: dict[str, ToolSpec] = {
    TOOL_PRESSURE_DROP.key: TOOL_PRESSURE_DROP,
    TOOL_VALVE_LIQUID.key: TOOL_VALVE_LIQUID,
    TOOL_VALVE_GAS.key: TOOL_VALVE_GAS,
    TOOL_NPSH.key: TOOL_NPSH,
    TOOL_WATER_HAMMER.key: TOOL_WATER_HAMMER,
    # TOOL_4.key: TOOL_4,   # <-- e.g. "Two-Phase Pressure Drop (Lockhart-Martinelli)"
    # TOOL_5.key: TOOL_5,   # <-- e.g. "Compressor Polytropic/Isentropic Head"
    # ... up to fd_075
}
