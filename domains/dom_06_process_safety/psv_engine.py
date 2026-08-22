"""
domains/dom_06_process_safety/psv_engine.py
==============================================
Domain 6: Process Safety, Relief & Loss Prevention. Pure Python physics,
zero Streamlit calls.

This domain had ZERO live tools until this release, despite being
flagged as the highest-priority gap in every prior review of this
suite — pressure relief is safety-critical and was completely
unaddressed.

Live tools:
  ps_001  PSV Gas/Vapor Sizing (API 520 Part I)
  ps_002  PSV Liquid Thermal Relief Sizing (API 520)
"""

import math
from utils.tool_roadmap import ToolSpec, InputSpec
from utils.ui_components import check_positive, run_validators


# =======================================================================
# TOOL: PSV GAS/VAPOR SIZING (API 520 Part I)
# =======================================================================

def compute_psv_gas_vapor(values: dict) -> dict:
    """
    A = W / (C*Kd*P1*Kb*Kc) * sqrt(T*Z/M)   [A in in^2]
    C = 520*sqrt(k*(2/(k+1))^((k+1)/(k-1)))
    """
    w_lb_hr = values["w_lb_hr"]
    set_pressure_psig = values["set_pressure_psig"]
    overpressure_fraction = values["overpressure_fraction"]
    back_pressure_psig = values["back_pressure_psig"]
    t_r = values["t_r"]
    z = values["z"]
    k = values["k"]
    m_molecular_weight = values["m_molecular_weight"]
    kd = values["kd"]
    kb = values["kb"]
    kc = values["kc"]

    has_error, has_warning, errors, warnings = run_validators(
        check_positive(w_lb_hr, "Relieving rate"),
        check_positive(set_pressure_psig, "Set pressure"),
        check_positive(t_r, "Relieving temperature"),
        check_positive(m_molecular_weight, "Molecular weight"),
    )
    if has_error:
        raise ValueError("; ".join(errors))
    if k <= 1.0:
        raise ValueError("Ratio of specific heats (k) must be greater than 1.0.")

    p1_psia = set_pressure_psig * (1 + overpressure_fraction) + 14.7
    c = 520 * math.sqrt(k * (2 / (k + 1)) ** ((k + 1) / (k - 1)))
    a_in2 = w_lb_hr / (c * kd * p1_psia * kb * kc) * math.sqrt((t_r * z) / m_molecular_weight)

    extra_warnings = []
    if back_pressure_psig > 0.1 * p1_psia and kb == 1.0:
        extra_warnings.append(
            "Back pressure exceeds ~10% of relieving pressure but Kb=1.0 (conventional valve "
            "assumption) was used - for a conventional (non-balanced) PRV this is invalid; use a "
            "balanced-bellows or pilot-operated valve and the correct Kb curve."
        )

    return {
        "Relieving Pressure P1 (psia)": round(p1_psia, 2),
        "Coefficient C": round(c, 2),
        "Required Orifice Area (in2)": round(a_in2, 4),
        "_warnings": warnings + extra_warnings,
    }


TOOL_PSV_GAS = ToolSpec(
    key="ps_001",
    title="PSV Gas/Vapor Sizing (API 520)",
    category="Pressure Relief Valve (PSV) Sizing",
    description="Required orifice area for a gas/vapor relief scenario per API 520 Part I.",
    inputs=[
        InputSpec("w_lb_hr", "Relieving Rate (W)", default=50000.0, min_value=1.0, unit="(lb/hr)"),
        InputSpec("set_pressure_psig", "Set Pressure", default=250.0, min_value=1.0, unit="(psig)"),
        InputSpec("overpressure_fraction", "Overpressure Fraction", default=0.10, min_value=0.0, max_value=0.30, step=0.01),
        InputSpec("back_pressure_psig", "Back Pressure", default=0.0, min_value=0.0, unit="(psig)"),
        InputSpec("t_r", "Relieving Temperature (T)", default=660.0, min_value=1.0, unit="(degR)"),
        InputSpec("z", "Compressibility Factor (Z)", default=1.0, min_value=0.1, max_value=2.0, step=0.01),
        InputSpec("k", "Ratio of Specific Heats (k)", default=1.3, min_value=1.01, max_value=1.7, step=0.01),
        InputSpec("m_molecular_weight", "Molecular Weight (M)", default=44.0, min_value=1.0),
        InputSpec("kd", "Discharge Coefficient (Kd)", default=0.975, min_value=0.5, max_value=1.0, step=0.001,
                   help="0.975 is the typical certified value for a conventional/balanced-bellows valve."),
        InputSpec("kb", "Backpressure Correction (Kb)", default=1.0, min_value=0.3, max_value=1.0, step=0.01,
                   help="1.0 for a conventional valve with back pressure <10% of set pressure. Use the manufacturer's Kb curve otherwise."),
        InputSpec("kc", "Combination Correction (Kc)", default=1.0, min_value=0.9, max_value=1.0, step=0.01,
                   help="1.0 if no rupture disk installed upstream; 0.9 if a rupture disk is installed (unless the valve is specifically tested with the disk)."),
    ],
    compute=compute_psv_gas_vapor,
    formula_md=(
        r"$$A = \dfrac{W}{C\,K_d\,P_1\,K_b\,K_c}\sqrt{\dfrac{TZ}{M}}, \quad "
        r"C = 520\sqrt{k\left(\dfrac{2}{k+1}\right)^{\frac{k+1}{k-1}}}$$"
    ),
    references=[
        "API Standard 520 Part I - Sizing, Selection, and Installation of Pressure-relieving Devices",
        "API Standard 526 - Flanged Steel Pressure-relief Valves",
    ],
    assumptions=[
        "Gives required orifice area for ONE relief scenario only - a full relief system design "
        "requires evaluating all governing cases (fire, blocked outlet, tube rupture, control valve "
        "failure, etc.) and sizing for the worst case.",
        "Kd=0.975 is a typical certified discharge coefficient - use the actual certified value for "
        "the specific valve model where available.",
        "Does not select the actual standard API orifice letter (D through T) - round up to the next "
        "standard size after sizing.",
    ],
)


# =======================================================================
# TOOL: PSV LIQUID THERMAL RELIEF SIZING (API 520)
# =======================================================================

def compute_psv_liquid_thermal(values: dict) -> dict:
    """A = Q / (38 * Kd * Kw * Kc * sqrt(dP))   [A in in^2, Q in US gpm, dP in psi]"""
    q_gpm = values["q_gpm"]
    set_pressure_psig = values["set_pressure_psig"]
    overpressure_fraction = values["overpressure_fraction"]
    back_pressure_psig = values["back_pressure_psig"]
    kd = values["kd"]
    kw = values["kw"]
    kc = values["kc"]

    has_error, has_warning, errors, warnings = run_validators(
        check_positive(q_gpm, "Relieving flow"),
        check_positive(set_pressure_psig, "Set pressure"),
    )
    if has_error:
        raise ValueError("; ".join(errors))

    p1 = set_pressure_psig * (1 + overpressure_fraction)
    dp = p1 - back_pressure_psig
    if dp <= 0:
        raise ValueError("Relieving pressure must exceed back pressure.")

    a_in2 = q_gpm / (38 * kd * kw * kc * math.sqrt(dp))

    return {
        "Relieving Pressure (psig)": round(p1, 2),
        "Delta P (psi)": round(dp, 2),
        "Required Orifice Area (in2)": round(a_in2, 4),
        "_warnings": warnings,
    }


TOOL_PSV_LIQUID = ToolSpec(
    key="ps_002",
    title="PSV Liquid Thermal Relief Sizing (API 520)",
    category="Pressure Relief Valve (PSV) Sizing",
    description="Required orifice area for thermal expansion of a blocked-in liquid line/vessel per API 520.",
    inputs=[
        InputSpec("q_gpm", "Relieving Flow (Q)", default=5.0, min_value=0.01, unit="(USGPM)",
                   help="For thermal relief this is typically a small flow - see API 521 for the thermal expansion rate calculation."),
        InputSpec("set_pressure_psig", "Set Pressure", default=150.0, min_value=1.0, unit="(psig)"),
        InputSpec("overpressure_fraction", "Overpressure Fraction", default=0.10, min_value=0.0, max_value=0.30, step=0.01),
        InputSpec("back_pressure_psig", "Back Pressure", default=0.0, min_value=0.0, unit="(psig)"),
        InputSpec("kd", "Discharge Coefficient (Kd)", default=0.65, min_value=0.5, max_value=0.8, step=0.01,
                   help="0.65 is a typical certified discharge coefficient for liquid service."),
        InputSpec("kw", "Backpressure Correction (Kw)", default=1.0, min_value=0.3, max_value=1.0, step=0.01),
        InputSpec("kc", "Combination Correction (Kc)", default=1.0, min_value=0.9, max_value=1.0, step=0.01),
    ],
    compute=compute_psv_liquid_thermal,
    formula_md=r"$$A = \dfrac{Q}{38\,K_d\,K_w\,K_c\sqrt{\Delta P}}$$",
    references=["API Standard 520 Part I", "API Standard 521 - Pressure-relieving and Depressuring Systems"],
    assumptions=[
        "Relieving flow Q for thermal relief must be calculated separately (API 521 gives a thermal "
        "expansion rate method) - this tool only sizes the orifice given Q, it does not compute Q.",
        "Kd=0.65 is a typical certified value for liquid service - use the actual certified value where available.",
    ],
)


REGISTRY: dict[str, ToolSpec] = {
    TOOL_PSV_GAS.key: TOOL_PSV_GAS,
    TOOL_PSV_LIQUID.key: TOOL_PSV_LIQUID,
}
