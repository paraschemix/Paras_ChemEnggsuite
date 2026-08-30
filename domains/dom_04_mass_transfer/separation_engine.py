"""
domains/dom_04_mass_transfer/separation_engine.py
====================================================
Domain 4: Mass Transfer & Separation Operations. Pure Python physics,
zero Streamlit calls.

Live tool:
  mt_011  Shortcut Distillation (Fenske-Underwood-Gilliland)
"""

import math
from utils.tool_roadmap import ToolSpec, InputSpec
from utils.ui_components import check_fraction_0_1, run_validators


def compute_shortcut_distillation(values: dict) -> dict:
    """
    Combined FUG short-cut method:
      1. Fenske    -> Nmin (minimum theoretical stages, total reflux)
      2. Underwood -> Rmin (minimum reflux ratio, constant relative
         volatility, binary/pseudo-binary light-key/heavy-key system)
      3. Gilliland -> N actual (theoretical stages at chosen actual R)
    """
    xD_LK = values["xD_LK"]
    xHK_D = values["xHK_D"]
    xLK_B = values["xLK_B"]
    xHK_B = values["xHK_B"]
    xF_LK = values["xF_LK"]
    xF_HK = values["xF_HK"]
    alpha = values["alpha"]
    r_actual = values["r_actual"]

    has_error, has_warning, errors, warnings = run_validators(
        check_fraction_0_1(xD_LK, "x(LK) in Distillate"), check_fraction_0_1(xHK_D, "x(HK) in Distillate"),
        check_fraction_0_1(xLK_B, "x(LK) in Bottoms"), check_fraction_0_1(xHK_B, "x(HK) in Bottoms"),
        check_fraction_0_1(xF_LK, "x(LK) in Feed"), check_fraction_0_1(xF_HK, "x(HK) in Feed"),
    )
    if has_error:
        raise ValueError("; ".join(errors))
    if alpha <= 1:
        raise ValueError("Relative volatility (alpha) must be greater than 1 for a separable system.")

    fenske_numerator = (xD_LK / xHK_D) * (xHK_B / xLK_B)
    if fenske_numerator <= 0:
        raise ValueError("Fenske separation factor is non-positive - check distillate/bottoms compositions.")
    n_min = math.log(fenske_numerator) / math.log(alpha) - 1

    r_min = (1 / (alpha - 1)) * ((xD_LK / xF_LK) - alpha * (xHK_D / xF_HK))

    if r_actual <= r_min:
        raise ValueError(
            f"Actual reflux ratio R ({r_actual}) must exceed the calculated Rmin ({r_min:.3f})."
        )

    x_gill = (r_actual - r_min) / (r_actual + 1)
    if x_gill <= 0:
        raise ValueError("Computed Gilliland X <= 0 - check R vs Rmin inputs.")
    y_gill = 1 - math.exp(((1 + 54.4 * x_gill) / (11 + 117.2 * x_gill)) * ((x_gill - 1) / math.sqrt(x_gill)))
    n_actual = (n_min + y_gill) / (1 - y_gill)

    reflux_ratio_multiple = r_actual / r_min

    extra_warnings = []
    if reflux_ratio_multiple < 1.1:
        extra_warnings.append(
            f"R/Rmin = {reflux_ratio_multiple:.2f} is very close to 1.0 (minimum reflux) - "
            "Gilliland correlation becomes unreliable near Rmin; typical economic design targets 1.1-1.5."
        )
    if reflux_ratio_multiple > 2.0:
        extra_warnings.append(
            f"R/Rmin = {reflux_ratio_multiple:.2f} is well above the typical economic optimum (~1.1-1.5)."
        )

    return {
        "Nmin (Fenske, total reflux)": round(n_min, 2),
        "Rmin (Underwood)": round(r_min, 3),
        "R/Rmin Ratio": round(reflux_ratio_multiple, 2),
        "N Actual (Gilliland)": round(n_actual, 2),
        "Gilliland X": round(x_gill, 4),
        "Gilliland Y": round(y_gill, 4),
        "_warnings": warnings + extra_warnings,
    }


TOOL_SHORTCUT_DISTILLATION = ToolSpec(
    key="mt_011",
    title="Shortcut Distillation (Fenske-Underwood-Gilliland)",
    category="Distillation & Fractionation",
    description="Combined FUG short-cut method: minimum stages, minimum reflux, and actual stages at your chosen operating reflux.",
    inputs=[
        InputSpec("xD_LK", "x(LK) in Distillate", default=0.98, min_value=0.001, max_value=0.999, step=0.001),
        InputSpec("xHK_D", "x(HK) in Distillate", default=0.02, min_value=0.001, max_value=0.999, step=0.001),
        InputSpec("xLK_B", "x(LK) in Bottoms", default=0.02, min_value=0.001, max_value=0.999, step=0.001),
        InputSpec("xHK_B", "x(HK) in Bottoms", default=0.98, min_value=0.001, max_value=0.999, step=0.001),
        InputSpec("xF_LK", "x(LK) in Feed", default=0.50, min_value=0.001, max_value=0.999, step=0.001),
        InputSpec("xF_HK", "x(HK) in Feed", default=0.50, min_value=0.001, max_value=0.999, step=0.001),
        InputSpec("alpha", "Relative Volatility (avg, LK/HK)", default=2.50, min_value=1.01, step=0.01),
        InputSpec("r_actual", "Chosen Actual Reflux Ratio (R)", default=1.70, min_value=0.01, step=0.01),
    ],
    compute=compute_shortcut_distillation,
    formula_md=(
        r"**Fenske:** $N_{min}=\dfrac{\ln[(x_{LK}/x_{HK})_D(x_{HK}/x_{LK})_B]}{\ln\alpha}-1$"
        "\n\n**Underwood:** $R_{min}=\\dfrac{1}{\\alpha-1}\\left[\\dfrac{x_{D,LK}}{x_{F,LK}}-\\alpha\\dfrac{x_{D,HK}}{x_{F,HK}}\\right]$"
        "\n\n**Gilliland:** $X=\\dfrac{R-R_{min}}{R+1}$, $Y=1-\\exp\\left[\\dfrac{1+54.4X}{11+117.2X}\\cdot\\dfrac{X-1}{\\sqrt{X}}\\right]$, $N=\\dfrac{N_{min}+Y}{1-Y}$"
    ),
    references=[
        "Fenske, M.R. (1932), Ind. Eng. Chem.", "Underwood, A.J.V. (1948), Chem. Eng. Prog.",
        "Gilliland, E.R. (1940), Ind. Eng. Chem.", "Perry's Chemical Engineers' Handbook, Section 13",
    ],
    assumptions=[
        "Constant relative volatility across the column.",
        "Binary/pseudo-binary (light-key/heavy-key) treatment - true multicomponent needs rigorous simulation.",
        "Gilliland correlation gives no feed-stage location - pair with Kirkbride for that.",
        "Total condenser and partial reboiler assumed.",
    ],
)


# =======================================================================
# TOOL: KREMSER METHOD (ABSORPTION/STRIPPING THEORETICAL STAGES)
# =======================================================================

def compute_kremser_absorption(values: dict) -> dict:
    """
    Kremser equation for theoretical stages in a countercurrent
    absorption column with a linear equilibrium relationship (y = m*x).

    N = ln[ ((y1 - m*x0)/(y2 - m*x0))*(1 - 1/A) + 1/A ] / ln(A)
    A = L/(m*V)  (absorption factor)
    """
    l_liquid = values["l_liquid"]
    v_gas = values["v_gas"]
    m_slope = values["m_slope"]
    y1 = values["y1"]
    y2 = values["y2"]
    x0 = values["x0"]

    if l_liquid <= 0 or v_gas <= 0 or m_slope <= 0:
        raise ValueError("Liquid flow, gas flow, and equilibrium slope must all be positive.")
    if y2 >= y1:
        raise ValueError("Exit gas composition (y2) must be less than inlet gas composition (y1) for absorption to occur.")

    a_factor = l_liquid / (m_slope * v_gas)
    if abs(a_factor - 1.0) < 1e-9:
        raise ValueError("Absorption factor A is too close to 1.0 - the Kremser equation is singular here; adjust L, V, or m slightly.")

    denom_y1 = y1 - m_slope * x0
    denom_y2 = y2 - m_slope * x0
    if denom_y2 <= 0 or denom_y1 <= 0:
        raise ValueError("y - m*x0 must be positive at both ends - check that absorption is thermodynamically feasible with these compositions.")

    ratio = denom_y1 / denom_y2
    n_stages = math.log(ratio * (1 - 1 / a_factor) + 1 / a_factor) / math.log(a_factor)

    warning = None
    if a_factor < 1.0:
        warning = (
            f"Absorption factor A = {a_factor:.3f} is below 1.0 - absorption becomes progressively "
            "less efficient per stage; consider increasing liquid rate L or reducing gas rate V."
        )

    return {
        "Absorption Factor (A)": round(a_factor, 4),
        "Theoretical Stages (N)": round(n_stages, 2),
        "_warnings": [warning] if warning else [],
    }


TOOL_KREMSER = ToolSpec(
    key="mt_012",
    title="Kremser Method (Absorption Theoretical Stages)",
    category="Absorption & Stripping",
    description="Theoretical stages for a countercurrent gas absorption column with linear equilibrium (y=mx).",
    inputs=[
        InputSpec("l_liquid", "Liquid Flow Rate (L)", default=100.0, min_value=0.01),
        InputSpec("v_gas", "Gas Flow Rate (V)", default=100.0, min_value=0.01),
        InputSpec("m_slope", "Equilibrium Line Slope (m)", default=0.5, min_value=0.001),
        InputSpec("y1", "Inlet Gas Mole Fraction (y1, rich)", default=0.02, min_value=0.0, max_value=0.999, step=0.001),
        InputSpec("y2", "Exit Gas Mole Fraction (y2, lean)", default=0.001, min_value=0.0, max_value=0.999, step=0.0001),
        InputSpec("x0", "Inlet Liquid Mole Fraction (x0)", default=0.0, min_value=0.0, max_value=0.999, step=0.001,
                   help="Solute concentration in the lean liquid entering at the top - typically 0 for fresh solvent."),
    ],
    compute=compute_kremser_absorption,
    formula_md=(
        r"$$N = \dfrac{\ln\left[\left(\dfrac{y_1-mx_0}{y_2-mx_0}\right)\left(1-\dfrac{1}{A}\right)+\dfrac{1}{A}\right]}{\ln A}, "
        r"\quad A = \dfrac{L}{mV}$$"
    ),
    references=["Kremser, A. (1930), National Petroleum News", "Perry's Chemical Engineers' Handbook, Section 14 - Gas Absorption"],
    assumptions=[
        "Linear equilibrium relationship (y=mx) assumed constant across the column - valid for dilute systems only.",
        "Isothermal, isobaric operation assumed.",
        "For stripping (rather than absorption), the analogous stripping-factor form of the Kremser equation should be used instead.",
    ],
)


# =======================================================================
# TOOL: FLASH DRUM SIZING (SOUDERS-BROWN)
# =======================================================================

def compute_flash_drum_sizing(values: dict) -> dict:
    k_factor = values["k_factor"]
    rho_liquid = values["rho_liquid"]
    rho_vapor = values["rho_vapor"]
    vapor_flow_ft3_s = values["vapor_flow_ft3_s"]

    if k_factor <= 0 or rho_liquid <= 0 or rho_vapor <= 0 or vapor_flow_ft3_s <= 0:
        raise ValueError("All inputs must be positive.")
    if rho_vapor >= rho_liquid:
        raise ValueError("Vapor density must be less than liquid density.")

    v_max_ft_s = k_factor * math.sqrt((rho_liquid - rho_vapor) / rho_vapor)
    area_ft2 = vapor_flow_ft3_s / v_max_ft_s
    diameter_ft = math.sqrt(4 * area_ft2 / math.pi)

    return {
        "Max Allowable Vapor Velocity (ft/s)": round(v_max_ft_s, 3),
        "Required Cross-Sectional Area (ft2)": round(area_ft2, 3),
        "Minimum Vessel Diameter (ft)": round(diameter_ft, 3),
        "Minimum Vessel Diameter (in)": round(diameter_ft * 12, 1),
        "_warnings": [],
    }


TOOL_FLASH_DRUM = ToolSpec(
    key="mt_013",
    title="Flash Drum / V-L Separator Sizing (Souders-Brown)",
    category="Absorption & Stripping",
    description="Minimum vertical separator diameter to prevent liquid entrainment, via the Souders-Brown vapor velocity limit.",
    inputs=[
        InputSpec("k_factor", "Souders-Brown K Factor", default=0.15, min_value=0.01, max_value=0.5, step=0.01, unit="(ft/s)",
                   help="Typical: 0.10-0.15 without a mist eliminator, up to 0.30-0.35 with a well-designed mesh pad demister."),
        InputSpec("rho_liquid", "Liquid Density", default=45.0, min_value=0.1, unit="(lb/ft3)"),
        InputSpec("rho_vapor", "Vapor Density", default=0.5, min_value=0.001, unit="(lb/ft3)"),
        InputSpec("vapor_flow_ft3_s", "Actual Vapor Volumetric Flow", default=5.0, min_value=0.001, unit="(ft3/s)"),
    ],
    compute=compute_flash_drum_sizing,
    formula_md=(
        r"$$V_{max} = K\sqrt{\dfrac{\rho_L-\rho_V}{\rho_V}}, \quad D = \sqrt{\dfrac{4}{\pi}\cdot\dfrac{Q_V}{V_{max}}}$$"
    ),
    references=["Souders, M. & Brown, G.G. (1934), Ind. Eng. Chem.", "GPSA Engineering Data Book, Section 7 - Separators"],
    assumptions=[
        "Sizes for vapor-liquid disengagement only - does not size the liquid holdup volume/residence time, which typically governs overall vessel height.",
        "K factor is a strong function of internals (demister type) and system properties (foaming tendency, surface tension) - vendor/literature K values for the specific service should be used for final design.",
    ],
)


# =======================================================================
# TOOL: McCABE-THIELE BINARY DISTILLATION STAGE STEPPING
# =======================================================================

def compute_mccabe_thiele(values: dict) -> dict:
    """
    Algebraic equivalent of the graphical McCabe-Thiele method for a
    binary system with constant relative volatility. Steps between the
    equilibrium curve (y = alpha*x/(1+(alpha-1)*x)) and the operating
    lines (rectifying, then stripping after crossing the q-line
    intersection), starting from the total-condenser point (xD, xD) and
    counting stages until x drops to or below xB.

    Cross-checked during development against this suite's own FUG tool
    (Fenske/Underwood/Gilliland) at identical inputs - this exact
    stage-by-stage method gave ~17 stages vs. Gilliland's empirical
    curve-fit estimate of ~15.5 stages for the same separation, which is
    the right ballpark agreement between an exact method and its
    empirical approximation.
    """
    alpha = values["alpha"]
    xd = values["xd"]
    xb = values["xb"]
    xf = values["xf"]
    q = values["q"]
    r_actual = values["r_actual"]

    if alpha <= 1:
        raise ValueError("Relative volatility (alpha) must be greater than 1.")
    for name, v in [("xD", xd), ("xB", xb), ("xF", xf)]:
        if not (0 < v < 1):
            raise ValueError(f"{name} must be strictly between 0 and 1.")
    if xb >= xf or xf >= xd:
        raise ValueError("Compositions must satisfy xB < xF < xD.")
    if r_actual <= 0:
        raise ValueError("Reflux ratio must be positive.")
    if abs(q - 1.0) < 1e-9:
        x_intersect = xf
        m_rect = r_actual / (r_actual + 1)
        b_rect = xd / (r_actual + 1)
        y_intersect = m_rect * x_intersect + b_rect
    else:
        # Rectifying line: y = (R/(R+1))x + xD/(R+1)
        # q-line:          y = (q/(q-1))x - xF/(q-1)
        m_rect = r_actual / (r_actual + 1)
        b_rect = xd / (r_actual + 1)
        m_q = q / (q - 1)
        b_q = -xf / (q - 1)
        if abs(m_rect - m_q) < 1e-12:
            raise ValueError("Rectifying line and q-line are parallel for these inputs - cannot find their intersection; adjust q or R.")
        x_intersect = (b_q - b_rect) / (m_rect - m_q)
        y_intersect = m_rect * x_intersect + b_rect

    # Stripping line passes through (xB, xB) and the intersection point.
    if abs(x_intersect - xb) < 1e-12:
        raise ValueError("Stripping line is vertical for these inputs - check q, R, and composition inputs.")
    m_strip = (y_intersect - xb) / (x_intersect - xb)
    b_strip = xb - m_strip * xb

    def equilibrium_x_from_y(y_val: float) -> float:
        denom = alpha - (alpha - 1) * y_val
        if denom <= 0:
            raise ValueError("Equilibrium curve inversion failed (non-physical y value reached) - check inputs.")
        return y_val / denom

    x_current = xd
    y_current = xd  # start on the y=x line at the total condenser
    stage_count = 0
    max_stages = 200
    crossed_feed_at_stage = None

    while x_current > xb and stage_count < max_stages:
        x_current = equilibrium_x_from_y(y_current)
        stage_count += 1
        if x_current <= xb:
            break
        if x_current > x_intersect:
            y_current = m_rect * x_current + b_rect
        else:
            if crossed_feed_at_stage is None:
                crossed_feed_at_stage = stage_count
            y_current = m_strip * x_current + b_strip

    if stage_count >= max_stages:
        raise ValueError(
            "Stage count exceeded 200 without reaching xB - the specified reflux ratio may be too close to "
            "Rmin (or below it) for this separation; increase R or verify inputs."
        )

    return {
        "Theoretical Stages (McCabe-Thiele)": stage_count,
        "Feed Stage (approx.)": crossed_feed_at_stage if crossed_feed_at_stage else "Feed stage at or above top stage",
        "Operating Line Intersection (x)": round(x_intersect, 4),
        "Operating Line Intersection (y)": round(y_intersect, 4),
        "_warnings": [],
    }


TOOL_MCCABE_THIELE = ToolSpec(
    key="mt_014",
    title="McCabe-Thiele Binary Distillation Stage Stepping",
    category="Distillation & Fractionation",
    description="Algebraic stage-by-stage stage count for binary distillation with constant relative volatility.",
    inputs=[
        InputSpec("alpha", "Relative Volatility (alpha)", default=2.5, min_value=1.01, step=0.01),
        InputSpec("xd", "Distillate Composition (xD)", default=0.98, min_value=0.001, max_value=0.999, step=0.001),
        InputSpec("xb", "Bottoms Composition (xB)", default=0.02, min_value=0.001, max_value=0.999, step=0.001),
        InputSpec("xf", "Feed Composition (xF)", default=0.50, min_value=0.001, max_value=0.999, step=0.001),
        InputSpec("q", "Feed Thermal Condition (q)", default=1.0, step=0.01,
                   help="q=1: saturated liquid feed. q=0: saturated vapor feed. 0<q<1: partially vaporized. q>1: subcooled liquid."),
        InputSpec("r_actual", "Actual Reflux Ratio (R)", default=1.70, min_value=0.01, step=0.01,
                   help="Must exceed Rmin (see the Shortcut Distillation FUG tool above to check Rmin for the same inputs)."),
    ],
    compute=compute_mccabe_thiele,
    formula_md=(
        r"**Equilibrium curve:** $y=\dfrac{\alpha x}{1+(\alpha-1)x}$"
        "\n\n**Rectifying line:** $y=\\dfrac{R}{R+1}x+\\dfrac{x_D}{R+1}$"
        "\n\n**q-line:** $y=\\dfrac{q}{q-1}x-\\dfrac{x_F}{q-1}$ (vertical at $x=x_F$ when q=1)"
        "\n\nStages counted by stepping horizontally to the equilibrium curve, then vertically to whichever "
        "operating line governs, starting from $(x_D,x_D)$ down to $x_B$."
    ),
    references=[
        "McCabe, W.L. & Thiele, E.W. (1925), Ind. Eng. Chem.",
        "Perry's Chemical Engineers' Handbook, Section 13 - Distillation",
    ],
    assumptions=[
        "Constant relative volatility and constant molal overflow (CMO) assumed - the same assumptions underlying the equilibrium curve and straight operating lines.",
        "Total condenser and partial reboiler assumed (matches this suite's FUG tool for direct comparison).",
        "Stage count is capped at 200 as a safety limit for reflux ratios too close to Rmin, where the true stage count approaches infinity.",
        "Feed stage location is reported as the stage where stepping crosses from the rectifying to the stripping operating line - the true optimal feed stage can differ slightly in practice.",
    ],
)


REGISTRY: dict[str, ToolSpec] = {
    TOOL_SHORTCUT_DISTILLATION.key: TOOL_SHORTCUT_DISTILLATION,
    TOOL_KREMSER.key: TOOL_KREMSER,
    TOOL_FLASH_DRUM.key: TOOL_FLASH_DRUM,
    TOOL_MCCABE_THIELE.key: TOOL_MCCABE_THIELE,
}