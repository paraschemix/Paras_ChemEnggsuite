"""
domains/dom_06_process_safety/orifice_sizing_engine.py
==========================================================
Phase 6B of the psv_safety_package upgrade (v10 track).
Two-phase relief sizing (Omega/HEM method, Leung 1986 simplified
correlation) and automated API 526 standard orifice-letter mapping.
Pure compute(), zero Streamlit imports (Pattern A).

Live tools:
  ps_016  Two-Phase Relief Sizing - Omega Method (Leung, HEM)
  ps_017  API 526 Standard Orifice Letter Selector
"""

import math
from utils.tool_roadmap import ToolSpec, InputSpec
from utils.ui_components import check_positive, run_validators


# =======================================================================
# TOOL: TWO-PHASE RELIEF SIZING - OMEGA METHOD (LEUNG, HEM)
# =======================================================================

def compute_two_phase_omega(values: dict) -> dict:
    """
    Leung's Omega-method critical mass flux for homogeneous equilibrium
    flashing/non-flashing two-phase flow through a PRV nozzle.
    G_crit = eta_crit * sqrt(P1*rho1) / omega   (simplified explicit form,
    eta_crit solved via the standard low-omega / high-omega bounding fits).
    """
    w_lb_hr = values["w_lb_hr"]
    p1_psia = values["p1_psia"]
    rho1_lb_ft3 = values["rho1_lb_ft3"]
    omega = values["omega"]
    kd = values["kd"]
    kb = values["kb"]
    kc = values["kc"]

    has_error, has_warning, errors, warnings = run_validators(
        check_positive(w_lb_hr, "Relief mass flow"),
        check_positive(p1_psia, "Relieving pressure P1"),
        check_positive(rho1_lb_ft3, "Stagnation mixture density"),
        check_positive(omega, "Omega parameter"),
    )
    if has_error:
        raise ValueError("; ".join(errors))

    # Critical pressure ratio eta_c - Leung's explicit approximation,
    # valid across the practical omega range (0.1 - 20+).
    if omega < 1.5:
        eta_c = 1 / (1 + math.sqrt(omega)) if omega > 0 else 1.0
        # correction per Leung (1986) low-omega asymptote
        eta_c = 1 - 0.6 * math.sqrt(omega) if omega <= 1.0 else eta_c
        eta_c = max(min(eta_c, 0.999), 0.1)
    else:
        eta_c = 1 / omega
        eta_c = max(min(eta_c, 0.999), 0.05)

    if eta_c <= 0 or eta_c >= 1:
        eta_c = 0.55  # fallback mid-range value; flagged via warning
        warnings.append(
            "Critical pressure ratio fell outside (0,1) - a fallback eta_c=0.55 was used. "
            "Verify the Omega parameter input; results should be cross-checked against a "
            "rigorous HEM solver for final design."
        )

    p1_psf = p1_psia * 144.0
    g_crit = eta_c * math.sqrt(p1_psf * rho1_lb_ft3 * 32.174) / math.sqrt(omega)  # lb/(s-ft2), approx form
    g_crit_hr = g_crit * 3600.0  # lb/(hr-ft2)

    a_required_in2 = w_lb_hr / (kd * kb * kc * g_crit_hr) * 144.0

    return {
        "Critical Pressure Ratio (eta_c)": round(eta_c, 4),
        "Critical Mass Flux G (lb/hr-ft2)": round(g_crit_hr, 1),
        "Required Orifice Area (in2)": round(a_required_in2, 4),
        "_warnings": warnings,
    }


TOOL_TWO_PHASE_OMEGA = ToolSpec(
    key="ps_016",
    title="Two-Phase Relief Sizing - Omega Method (Leung/HEM)",
    category="Valve & Orifice Sizing",
    description="Homogeneous Equilibrium Model relief-orifice sizing for flashing or non-flashing two-phase (vapor-liquid) discharge using Leung's Omega correlation.",
    inputs=[
        InputSpec("w_lb_hr", "Required Relief Mass Flow (W)", default=20000.0, min_value=1.0,
                   quantity_kind="flow_mass", canonical_unit="lb/hr"),
        InputSpec("p1_psia", "Relieving Pressure P1 (upstream stagnation)", default=150.0, min_value=1.0,
                   quantity_kind="pressure", canonical_unit="psia"),
        InputSpec("rho1_lb_ft3", "Stagnation Mixture Density", default=30.0, min_value=0.01, unit="(lb/ft3)",
                   help="Homogeneous two-phase mixture density at P1, T1 (mass-weighted)."),
        InputSpec("omega", "Omega Parameter", default=2.0, min_value=0.01, max_value=50.0, step=0.1,
                   help="omega = (Cp1*T1*P1*Vfg^2)/(vfg^2*hfg^2)-type flashing parameter, OR "
                        "for non-flashing homogeneous gas-liquid mixtures: omega = (x*vg/vfg) + "
                        "(rho1*vfg*Cp1*T1/vg... ) - compute externally per Leung (1986)/API 520 Part I Annex C "
                        "and enter the resulting dimensionless value here."),
        InputSpec("kd", "Discharge Coefficient (Kd)", default=0.85, min_value=0.1, max_value=1.0, step=0.01),
        InputSpec("kb", "Backpressure Correction (Kb)", default=1.0, min_value=0.1, max_value=1.0, step=0.01),
        InputSpec("kc", "Combination Factor (Kc)", default=1.0, min_value=0.1, max_value=1.0, step=0.01,
                   help="1.0 for PSV alone; 0.9 for PSV in series with an uncertified rupture disc."),
    ],
    compute=compute_two_phase_omega,
    formula_md=(
        r"$$G_{crit} = \dfrac{\eta_c}{\sqrt{\omega}}\sqrt{P_1\,\rho_1\,g_c}, \quad "
        r"A = \dfrac{W}{K_d K_b K_c\,G_{crit}}$$"
    ),
    references=[
        "Leung, J.C. (1986) 'A Generalized Correlation for One-Component Homogeneous Equilibrium "
        "Flashing Choked Flow', AIChE Journal",
        "API 520 Part I, Annex C - Sizing for Two-Phase Flow",
    ],
    assumptions=[
        "The Omega parameter is a REQUIRED user-supplied input, not derived internally - it must be "
        "computed from fluid property data (Cp, hfg, vfg, quality x) per API 520 Annex C or Leung's "
        "original paper before using this tool. Entering an incorrect omega silently produces a "
        "wrong-but-plausible-looking area.",
        "eta_c (critical pressure ratio) is estimated via Leung's simplified explicit bounding fits, "
        "not the exact implicit solution - adequate for screening/first-pass sizing; a rigorous design "
        "should verify eta_c via iterative solution of Leung's full critical-flow equation.",
        "Assumes homogeneous equilibrium (no slip, instant phase equilibrium) - valid for most PRV "
        "nozzle lengths per HEM applicability guidance, not for very short nozzles or highly "
        "non-equilibrium (subcooled non-flashing) discharges.",
    ],
)


# =======================================================================
# TOOL: API 526 STANDARD ORIFICE LETTER SELECTOR
# =======================================================================

API_526_ORIFICES = [
    ("D", 0.110), ("E", 0.196), ("F", 0.307), ("G", 0.503),
    ("H", 0.785), ("J", 1.287), ("K", 1.838), ("L", 2.853),
    ("M", 3.600), ("N", 4.340), ("P", 6.380), ("Q", 11.050),
    ("R", 16.000), ("T", 26.000),
]


def compute_api526_selector(values: dict) -> dict:
    a_calc_in2 = values["a_calc_in2"]

    has_error, has_warning, errors, warnings = run_validators(
        check_positive(a_calc_in2, "Calculated required area"),
    )
    if has_error:
        raise ValueError("; ".join(errors))

    selected = None
    for letter, area in API_526_ORIFICES:
        if area >= a_calc_in2:
            selected = (letter, area)
            break

    if selected is None:
        warnings.append(
            f"Calculated area {a_calc_in2:.3f} in2 exceeds the largest standard API 526 orifice "
            f"(T = 26.000 in2) - a multiple-valve installation or custom/oversized nozzle design "
            f"is required; consult the vendor."
        )
        return {
            "Calculated Required Area (in2)": round(a_calc_in2, 4),
            "Selected API 526 Orifice": "NONE - EXCEEDS T ORIFICE",
            "Selected Orifice Area (in2)": None,
            "Oversizing Margin (%)": None,
            "_warnings": warnings,
        }

    letter, area = selected
    margin_pct = (area - a_calc_in2) / a_calc_in2 * 100.0

    if margin_pct > 100:
        warnings.append(
            f"Selected orifice '{letter}' is more than 2x the calculated area (margin "
            f"{margin_pct:.0f}%) - check for a calculation error, or confirm intentional "
            f"oversizing (e.g. standardization across similar services)."
        )

    return {
        "Calculated Required Area (in2)": round(a_calc_in2, 4),
        "Selected API 526 Orifice": letter,
        "Selected Orifice Area (in2)": area,
        "Oversizing Margin (%)": round(margin_pct, 1),
        "_warnings": warnings,
    }


TOOL_API526_SELECTOR = ToolSpec(
    key="ps_017",
    title="API 526 Standard Orifice Letter Selector",
    category="Valve & Orifice Sizing",
    description="Maps a calculated required relief area to the next-largest standard API 526 orifice designation (D through T).",
    inputs=[
        InputSpec("a_calc_in2", "Calculated Required Area", default=1.0, min_value=0.001,
                   unit="(in2)", help="Output area from any liquid/gas/steam/two-phase orifice sizing calculation."),
    ],
    compute=compute_api526_selector,
    formula_md=r"$$\text{Select smallest } A_{std} \ge A_{calc} \text{ from API 526 Table}$$",
    references=["API Standard 526 - Flanged Steel Pressure-relief Valves (standard orifice areas)"],
    assumptions=[
        "Pure lookup/mapping tool - does not itself validate the upstream area calculation; "
        "garbage-in/garbage-out on A_calc.",
        "Standard letters D-T cover the vast majority of single-valve applications; areas above "
        "T (26.0 in2) require multiple valves in parallel or a non-standard nozzle - not automated here.",
    ],
)


REGISTRY: dict[str, ToolSpec] = {
    TOOL_TWO_PHASE_OMEGA.key: TOOL_TWO_PHASE_OMEGA,
    TOOL_API526_SELECTOR.key: TOOL_API526_SELECTOR,
}
