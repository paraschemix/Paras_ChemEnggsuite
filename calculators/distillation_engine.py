"""
calculators/distillation_engine.py
=====================================
Houses calculation logic for the Mass Transfer & Aromatics Processing
domain (tools #11-20 in the roadmap). Fully implemented: Tool #11,
Shortcut Distillation (Fenske-Underwood-Gilliland) — combines all three
correlations into a single design tool, since in practice an engineer
runs them together as one FUG short-cut sequence, not as three separate
lookups.

Remaining tools in this domain (#12-20: tray hydraulics, packed bed
HETP, flash drum sizing, decanter sizing, absorption/stripping factor,
BTX fractionation, solvent extraction, reflux optimization, entrainment
velocity) follow the identical ToolSpec/REGISTRY pattern — see
calculators/fluid_dynamics_engine.py for the reference implementation.
"""

import math
from calculators.registry_base import ToolSpec, InputSpec
from utils.validators import check_positive, check_fraction_0_1, run_validators


# =======================================================================
# TOOL 11: SHORTCUT DISTILLATION (Fenske - Underwood - Gilliland)
# =======================================================================

def compute_shortcut_distillation(values: dict) -> dict:
    """
    Combined FUG short-cut method:
      1. Fenske  -> Nmin (minimum theoretical stages, total reflux)
      2. Underwood -> Rmin (minimum reflux ratio, constant relative
         volatility, binary/pseudo-binary light-key/heavy-key system)
      3. Gilliland -> N actual (theoretical stages at the chosen actual
         reflux ratio R)

    Internal units: mole fractions (dimensionless), dimensionless
    relative volatility and reflux ratios — no SI/Imperial distinction
    applies to this tool (all inputs are already dimensionless).
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
        check_fraction_0_1(xD_LK, "x(LK) in Distillate"),
        check_fraction_0_1(xHK_D, "x(HK) in Distillate"),
        check_fraction_0_1(xLK_B, "x(LK) in Bottoms"),
        check_fraction_0_1(xHK_B, "x(HK) in Bottoms"),
        check_fraction_0_1(xF_LK, "x(LK) in Feed"),
        check_fraction_0_1(xF_HK, "x(HK) in Feed"),
    )
    if has_error:
        raise ValueError("; ".join(errors))
    if alpha <= 1:
        raise ValueError("Relative volatility (alpha) must be greater than 1 for a separable system.")

    # --- Step 1: Fenske equation (Nmin at total reflux) ---
    fenske_numerator = (xD_LK / xHK_D) * (xHK_B / xLK_B)
    if fenske_numerator <= 0:
        raise ValueError("Fenske separation factor is non-positive — check distillate/bottoms compositions.")
    n_min = math.log(fenske_numerator) / math.log(alpha) - 1

    # --- Step 2: Underwood equation (Rmin, constant alpha, binary/pseudo-binary) ---
    r_min = (1 / (alpha - 1)) * ((xD_LK / xF_LK) - alpha * (xHK_D / xF_HK))

    if r_actual <= r_min:
        raise ValueError(
            f"Actual reflux ratio R ({r_actual}) must exceed the calculated Rmin ({r_min:.3f}) — "
            "operating below minimum reflux is thermodynamically infeasible."
        )

    # --- Step 3: Gilliland correlation (actual N at chosen R) ---
    x_gill = (r_actual - r_min) / (r_actual + 1)
    if x_gill <= 0:
        raise ValueError("Computed Gilliland X <= 0 — check R vs Rmin inputs.")
    y_gill = 1 - math.exp(((1 + 54.4 * x_gill) / (11 + 117.2 * x_gill)) * ((x_gill - 1) / math.sqrt(x_gill)))
    n_actual = (n_min + y_gill) / (1 - y_gill)

    reflux_ratio_multiple = r_actual / r_min

    extra_warnings = []
    if reflux_ratio_multiple < 1.1:
        extra_warnings.append(
            f"R/Rmin = {reflux_ratio_multiple:.2f} is very close to 1.0 (minimum reflux) — the Gilliland "
            "correlation becomes unreliable near Rmin; typical economic design targets R/Rmin of 1.1-1.5."
        )
    if reflux_ratio_multiple > 2.0:
        extra_warnings.append(
            f"R/Rmin = {reflux_ratio_multiple:.2f} is well above the typical economic optimum (~1.1-1.5) — "
            "this may indicate excessive utility cost; consider re-optimizing R."
        )

    return {
        "Nmin (Fenske, total reflux)": round(n_min, 2),
        "Rmin (Underwood)": round(r_min, 3),
        "R/Rmin Ratio": round(reflux_ratio_multiple, 2),
        "N Actual (Gilliland, theoretical stages)": round(n_actual, 2),
        "Gilliland X": round(x_gill, 4),
        "Gilliland Y": round(y_gill, 4),
        "_warnings": warnings + extra_warnings,
    }


TOOL_SHORTCUT_DISTILLATION = ToolSpec(
    key="mt_011",
    title="Shortcut Distillation (Fenske-Underwood-Gilliland)",
    category="Distillation & Separation",
    description="Combined FUG short-cut method: minimum stages, minimum reflux, and actual stages at your chosen operating reflux.",
    inputs=[
        InputSpec("xD_LK", "x(LK) in Distillate", default=0.98, min_value=0.001, max_value=0.999, step=0.001),
        InputSpec("xHK_D", "x(HK) in Distillate", default=0.02, min_value=0.001, max_value=0.999, step=0.001),
        InputSpec("xLK_B", "x(LK) in Bottoms", default=0.02, min_value=0.001, max_value=0.999, step=0.001),
        InputSpec("xHK_B", "x(HK) in Bottoms", default=0.98, min_value=0.001, max_value=0.999, step=0.001),
        InputSpec("xF_LK", "x(LK) in Feed", default=0.50, min_value=0.001, max_value=0.999, step=0.001),
        InputSpec("xF_HK", "x(HK) in Feed", default=0.50, min_value=0.001, max_value=0.999, step=0.001),
        InputSpec("alpha", "Relative Volatility (alpha, LK/HK, average)", default=2.50, min_value=1.01, step=0.01,
                   help="Average relative volatility between light key and heavy key across the column, at total reflux conditions."),
        InputSpec("r_actual", "Chosen Actual Reflux Ratio (R)", default=1.70, min_value=0.01, step=0.01,
                   help="Must exceed the calculated Rmin — typical economic design is 1.1-1.5x Rmin."),
    ],
    compute=compute_shortcut_distillation,
    formula_md=(
        r"**Fenske (Nmin, total reflux):**"
        "\n\n"
        r"$$N_{min} = \frac{\ln\left[\left(\frac{x_{LK}}{x_{HK}}\right)_D \left(\frac{x_{HK}}{x_{LK}}\right)_B\right]}{\ln \alpha} - 1$$"
        "\n\n**Underwood (Rmin, constant alpha, binary/pseudo-binary):**"
        "\n\n"
        r"$$R_{min} = \frac{1}{\alpha - 1}\left[\frac{x_{D,LK}}{x_{F,LK}} - \alpha \frac{x_{D,HK}}{x_{F,HK}}\right]$$"
        "\n\n**Gilliland (1940) correlation for actual stages at chosen R:**"
        "\n\n"
        r"$$X = \frac{R - R_{min}}{R+1}, \quad Y = 1 - \exp\left[\frac{1+54.4X}{11+117.2X}\cdot\frac{X-1}{\sqrt{X}}\right], \quad N = \frac{N_{min}+Y}{1-Y}$$"
    ),
    references=[
        "Fenske, M.R. (1932), Ind. Eng. Chem.",
        "Underwood, A.J.V. (1948), Chem. Eng. Prog.",
        "Gilliland, E.R. (1940), Ind. Eng. Chem. — empirical N vs R correlation",
        "Perry's Chemical Engineers' Handbook, Section 13 — Distillation",
        "GPSA Engineering Data Book, Section 19 — Hydrocarbon Fractionation",
    ],
    assumptions=[
        "Constant relative volatility (alpha) across the column — valid for close-boiling, ideal or near-ideal systems.",
        "Binary or pseudo-binary (light-key/heavy-key) treatment — true multicomponent systems need rigorous tray-by-tray simulation for final design.",
        "Underwood's simplified binary form is used (not the full multicomponent theta-root method) — adequate for early-stage screening, not detailed design.",
        "Gilliland correlation does not give feed-stage location — pair with a Kirkbride estimate for that.",
        "Total condenser and partial reboiler assumed (standard Fenske derivation basis).",
    ],
)


REGISTRY: dict[str, ToolSpec] = {
    TOOL_SHORTCUT_DISTILLATION.key: TOOL_SHORTCUT_DISTILLATION,
    # Remaining domain tools (#12-20) follow the identical pattern:
    # TOOL_TRAY_HYDRAULICS.key: TOOL_TRAY_HYDRAULICS,           # mt_012
    # TOOL_PACKED_BED_HETP.key: TOOL_PACKED_BED_HETP,           # mt_013
    # TOOL_FLASH_DRUM.key: TOOL_FLASH_DRUM,                     # mt_014
    # TOOL_DECANTER.key: TOOL_DECANTER,                         # mt_015
    # TOOL_ABSORPTION_STRIPPING.key: TOOL_ABSORPTION_STRIPPING, # mt_016
    # TOOL_BTX_FRACTIONATION.key: TOOL_BTX_FRACTIONATION,       # mt_017
    # TOOL_SOLVENT_EXTRACTION.key: TOOL_SOLVENT_EXTRACTION,     # mt_018
    # TOOL_REFLUX_OPTIMIZATION.key: TOOL_REFLUX_OPTIMIZATION,   # mt_019
    # TOOL_ENTRAINMENT_VELOCITY.key: TOOL_ENTRAINMENT_VELOCITY, # mt_020
}
