"""
domains/dom_07_equipment_sizing/tray_vessel_engine.py
========================================================
Domain 7: Equipment Sizing. Pure Python physics, zero Streamlit calls.

Live tools:
  eq_001  Sieve Tray Hydraulics (dry/wet pressure drop, flood check, weep flag)
  eq_002  Liquid Surge Drum Sizing (Horizontal & Vertical)

Both tools compose well-established closed-form equations (orifice
equation, Francis weir formula, Souders-Brown, circular-segment
geometry). Where a rigorous design would require reading an empirical
correlation off a chart or table (e.g. the Fair flooding-capacity chart,
or the Eduljee weep-point correlation's tabulated K2 factor), this
engine takes that value as a direct, clearly-documented user input
rather than hard-coding a remembered constant that could be subtly
wrong - see each tool's assumptions for specifics.
"""

import math
from utils.tool_roadmap import ToolSpec, InputSpec
from utils.ui_components import check_positive, run_validators


# =======================================================================
# TOOL: SIEVE TRAY HYDRAULICS
# =======================================================================

def compute_sieve_tray_hydraulics(values: dict) -> dict:
    hole_velocity_ft_s = values["hole_velocity_ft_s"]
    orifice_coeff = values["orifice_coeff"]
    rho_vapor = values["rho_vapor"]
    rho_liquid = values["rho_liquid"]
    liquid_flow_gpm = values["liquid_flow_gpm"]
    weir_length_in = values["weir_length_in"]
    weir_height_in = values["weir_height_in"]
    aeration_factor = values["aeration_factor"]
    net_vapor_velocity_ft_s = values["net_vapor_velocity_ft_s"]
    flood_velocity_constant_csb = values["flood_velocity_constant_csb"]
    surface_tension_dyne_cm = values["surface_tension_dyne_cm"]

    has_error, has_warning, errors, warnings = run_validators(
        check_positive(orifice_coeff, "Orifice coefficient"),
        check_positive(rho_vapor, "Vapor density"), check_positive(rho_liquid, "Liquid density"),
        check_positive(liquid_flow_gpm, "Liquid flow"), check_positive(weir_length_in, "Weir length"),
        check_positive(flood_velocity_constant_csb, "Flood velocity constant"),
        check_positive(surface_tension_dyne_cm, "Surface tension"),
    )
    if has_error:
        raise ValueError("; ".join(errors))
    if hole_velocity_ft_s < 0 or net_vapor_velocity_ft_s < 0 or weir_height_in < 0:
        raise ValueError("Velocities and weir height cannot be negative.")
    if rho_vapor >= rho_liquid:
        raise ValueError("Vapor density must be less than liquid density.")

    # Dry tray pressure drop (orifice equation), inches of liquid
    hd = (0.186 / orifice_coeff ** 2) * hole_velocity_ft_s ** 2 * (rho_vapor / rho_liquid)

    # Weir crest height (Francis weir formula), inches of liquid
    how = 0.48 * (liquid_flow_gpm / weir_length_in) ** (2.0 / 3.0)

    # Clear liquid height on the tray, with an aeration/froth correction
    hl = aeration_factor * (weir_height_in + how)

    # Total wet tray pressure drop
    ht_in_liquid = hd + hl
    ht_psi = ht_in_liquid * (rho_liquid / 62.4) * (1.0 / 27.68)  # in. liquid -> psi via SG

    # Flooding check (Souders-Brown, surface-tension corrected)
    u_flood = flood_velocity_constant_csb * (surface_tension_dyne_cm / 20.0) ** 0.2 * math.sqrt(
        (rho_liquid - rho_vapor) / rho_vapor
    )
    pct_flood = (net_vapor_velocity_ft_s / u_flood * 100.0) if u_flood > 0 else float("inf")

    extra_warnings = []
    if pct_flood > 85:
        extra_warnings.append(
            f"Net vapor velocity is {pct_flood:.0f}% of the calculated flood velocity - typical design "
            "practice targets 70-85% of flood at design rates; re-check tray spacing or active area."
        )
    if hole_velocity_ft_s < 20.0:
        extra_warnings.append(
            "Hole velocity is below ~20 ft/s, a common rule-of-thumb minimum for weep-free operation on "
            "many hydrocarbon systems - this is a screening heuristic, not a validated correlation. For a "
            "rigorous weep-point check, use the Eduljee correlation or the manufacturer's tray rating software."
        )

    return {
        "Dry Tray Pressure Drop, hd (in. liquid)": round(hd, 3),
        "Weir Crest Height, how (in. liquid)": round(how, 3),
        "Clear Liquid Height, hl (in. liquid)": round(hl, 3),
        "Total Wet Tray Pressure Drop (in. liquid)": round(ht_in_liquid, 3),
        "Total Wet Tray Pressure Drop (psi)": round(ht_psi, 4),
        "Flood Velocity, Uf (ft/s)": round(u_flood, 3),
        "Percent of Flood (%)": round(pct_flood, 1),
        "_warnings": warnings + extra_warnings,
    }


TOOL_TRAY_HYDRAULICS = ToolSpec(
    key="eq_001",
    title="Sieve Tray Hydraulics",
    category="Distillation Tray Hydraulics",
    description="Dry/wet tray pressure drop, flooding check, and a weep-risk screening flag for a sieve tray.",
    inputs=[
        InputSpec("hole_velocity_ft_s", "Vapor Velocity Through Holes", default=30.0, min_value=0.0, unit="(ft/s)"),
        InputSpec("orifice_coeff", "Orifice Coefficient (Co)", default=0.75, min_value=0.5, max_value=0.9, step=0.01,
                   help="Typical range 0.65-0.85, depending on hole diameter to deck thickness ratio."),
        InputSpec("rho_vapor", "Vapor Density", default=0.5, min_value=0.001, unit="(lb/ft3)"),
        InputSpec("rho_liquid", "Liquid Density", default=45.0, min_value=0.1, unit="(lb/ft3)"),
        InputSpec("liquid_flow_gpm", "Liquid Flow Rate", default=200.0, min_value=0.01, unit="(USGPM)"),
        InputSpec("weir_length_in", "Weir Length", default=24.0, min_value=1.0, unit="(in)"),
        InputSpec("weir_height_in", "Weir Height", default=2.0, min_value=0.0, unit="(in)"),
        InputSpec("aeration_factor", "Aeration/Froth Factor (beta)", default=0.5, min_value=0.3, max_value=0.7, step=0.01,
                   help="Typical range 0.4-0.7; accounts for the frothy, aerated nature of the liquid on an operating tray vs. clear liquid."),
        InputSpec("net_vapor_velocity_ft_s", "Actual Vapor Velocity (net/active area basis)", default=2.8, min_value=0.0, unit="(ft/s)",
                   help="Superficial vapor velocity based on net (or active) tray area - NOT the hole velocity above, which is a different area basis."),
        InputSpec("flood_velocity_constant_csb", "Souders-Brown Flood Constant (Csb)", default=0.35, min_value=0.05, max_value=0.6, step=0.01,
                   help="Function of tray spacing; ~0.35 ft/s is a commonly cited value for 24 in. tray spacing. Read the specific value from a Fair flooding-capacity chart for your actual tray spacing and flow parameter for a rigorous check."),
        InputSpec("surface_tension_dyne_cm", "Liquid Surface Tension", default=20.0, min_value=1.0, unit="(dyne/cm)"),
    ],
    compute=compute_sieve_tray_hydraulics,
    formula_md=(
        r"**Dry pressure drop:** $h_d = \dfrac{0.186}{C_o^2}u_h^2\dfrac{\rho_V}{\rho_L}$ (inches liquid)"
        "\n\n**Weir crest (Francis formula):** $h_{ow}=0.48\\left(\\dfrac{q}{L_w}\\right)^{2/3}$"
        "\n\n**Total tray dP:** $h_t = h_d + \\beta(h_w+h_{ow})$"
        "\n\n**Flood velocity (Souders-Brown):** $U_f = C_{sb}\\left(\\dfrac{\\sigma}{20}\\right)^{0.2}\\sqrt{\\dfrac{\\rho_L-\\rho_V}{\\rho_V}}$"
    ),
    references=[
        "Fair, J.R. (1961), Petro/Chem Engineer - sieve tray design correlations",
        "Treybal, R.E., Mass-Transfer Operations",
        "GPSA Engineering Data Book, Section 19 - Hydrocarbon Fractionation",
    ],
    assumptions=[
        "Csb (flood constant) and the weep-velocity threshold are exposed as direct inputs/heuristics rather than computed from the full Fair flooding chart or Eduljee weep-point correlation - both require reading an empirical curve/table that is easy to misremember as a fixed formula; supply your own value from the relevant chart for a rigorous check.",
        "Aeration factor (beta) is a simplification of the actual froth/aeration behavior, which is itself system- and rate-dependent.",
        "Assumes a conventional sieve tray (not valve or bubble-cap) with no significant liquid gradient across the tray.",
    ],
)


# =======================================================================
# TOOL: LIQUID SURGE DRUM SIZING (HORIZONTAL & VERTICAL)
# =======================================================================

def compute_surge_drum_sizing(values: dict) -> dict:
    orientation = values["orientation"]
    liquid_flow_gpm = values["liquid_flow_gpm"]
    residence_time_min = values["residence_time_min"]
    diameter_ft = values["diameter_ft"]
    vapor_space_ft = values.get("vapor_space_ft", 0.0)

    has_error, has_warning, errors, warnings = run_validators(
        check_positive(liquid_flow_gpm, "Liquid flow"), check_positive(residence_time_min, "Residence time"),
        check_positive(diameter_ft, "Diameter"),
    )
    if has_error:
        raise ValueError("; ".join(errors))

    liquid_volume_gal = liquid_flow_gpm * residence_time_min
    liquid_volume_ft3 = liquid_volume_gal * 0.133681
    radius_ft = diameter_ft / 2.0

    if orientation == "Vertical":
        liquid_height_ft = liquid_volume_ft3 / (math.pi * radius_ft ** 2)
        total_height_ft = liquid_height_ft + vapor_space_ft
        l_d_ratio = total_height_ft / diameter_ft if diameter_ft > 0 else float("inf")

        extra_warning = None
        if vapor_space_ft > 0 and vapor_space_ft < 0.5 * diameter_ft:
            extra_warning = (
                "Vapor disengagement space is less than 0.5x the vessel diameter - many company standards "
                "specify a minimum vapor space of the greater of ~0.5x diameter or 24-36 inches; verify "
                "against your project's vessel sizing standard."
            )

        return {
            "Liquid Holdup Volume (ft3)": round(liquid_volume_ft3, 2),
            "Liquid Holdup Volume (gal)": round(liquid_volume_gal, 1),
            "Required Liquid Height (ft)": round(liquid_height_ft, 2),
            "Total Vessel Height incl. Vapor Space (ft)": round(total_height_ft, 2),
            "Height-to-Diameter Ratio (L/D)": round(l_d_ratio, 2),
            "_warnings": warnings + ([extra_warning] if extra_warning else []),
        }
    else:  # Horizontal, 50% liquid level design basis
        area_half_circle_ft2 = (math.pi * radius_ft ** 2) / 2.0
        length_ft = liquid_volume_ft3 / area_half_circle_ft2 if area_half_circle_ft2 > 0 else float("inf")
        l_d_ratio = length_ft / diameter_ft if diameter_ft > 0 else float("inf")

        extra_warning = None
        if l_d_ratio < 2.5 or l_d_ratio > 5.0:
            extra_warning = (
                f"L/D ratio of {l_d_ratio:.1f} is outside the typical 2.5-5.0 range for horizontal separators - "
                "consider adjusting the diameter to bring the vessel proportions into a more standard range."
            )

        return {
            "Liquid Holdup Volume (ft3)": round(liquid_volume_ft3, 2),
            "Liquid Holdup Volume (gal)": round(liquid_volume_gal, 1),
            "Required Tangent-to-Tangent Length (ft)": round(length_ft, 2),
            "Length-to-Diameter Ratio (L/D)": round(l_d_ratio, 2),
            "_warnings": warnings + ([extra_warning] if extra_warning else []),
        }


TOOL_SURGE_DRUM = ToolSpec(
    key="eq_002",
    title="Liquid Surge Drum Sizing (Horizontal & Vertical)",
    category="Vessel Sizing",
    description="Sizes a liquid surge/knockout drum for a target residence time, given a chosen vessel diameter.",
    inputs=[
        InputSpec("orientation", "Vessel Orientation", default=0.0, input_type="select", options=["Vertical", "Horizontal"]),
        InputSpec("liquid_flow_gpm", "Liquid Flow Rate", default=200.0, min_value=0.01, unit="(USGPM)"),
        InputSpec("residence_time_min", "Target Residence Time", default=5.0, min_value=0.01, unit="(min)",
                   help="Typical surge drums: 5-10 min; reflux drums/feed surge: often 3-5 min. Confirm against your project's design basis."),
        InputSpec("diameter_ft", "Vessel Diameter", default=4.0, min_value=0.5, unit="(ft)"),
        InputSpec("vapor_space_ft", "Vapor Disengagement Space (Vertical only)", default=2.0, min_value=0.0, unit="(ft)",
                   help="Only used for vertical orientation - added above the liquid height for vapor-liquid disengagement."),
    ],
    compute=compute_surge_drum_sizing,
    formula_md=(
        r"**Vertical:** $H_{liquid} = \dfrac{V_{liquid}}{\pi R^2}$"
        "\n\n**Horizontal (50% level basis):** $L = \\dfrac{V_{liquid}}{\\pi R^2/2}$"
        "\n\nBoth from $V_{liquid} = Q_{liquid}\\times t_{residence}$"
    ),
    references=["GPSA Engineering Data Book, Section 7 - Separators", "Arnold, K. & Stewart, M., Surface Production Operations, Vol. 1"],
    assumptions=[
        "Horizontal sizing assumes a standard 50% liquid level design basis (the circular-segment area at any other fill fraction has no closed-form solution for length and requires iterative solving) - for a different target level, iterate the diameter/length externally.",
        "Does not size for vapor-liquid disengagement (Souders-Brown) requirements on the vapor side - check separately, especially for two-phase separators.",
        "Does not include nozzle, mounting, or skirt/support allowances - tangent-to-tangent dimensions only.",
    ],
)


REGISTRY: dict[str, ToolSpec] = {
    TOOL_TRAY_HYDRAULICS.key: TOOL_TRAY_HYDRAULICS,
    TOOL_SURGE_DRUM.key: TOOL_SURGE_DRUM,
}
