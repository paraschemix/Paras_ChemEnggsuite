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


REGISTRY: dict[str, ToolSpec] = {
    TOOL_SHORTCUT_DISTILLATION.key: TOOL_SHORTCUT_DISTILLATION,
}
