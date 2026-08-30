"""
domains/dom_12_environmental/dispersion_engine.py
====================================================
Domain 12: Environmental & Energy. Pure Python physics, zero Streamlit
calls.

Live tools:
  en_001  Flare Stack Thermal Radiation (API 521 point-source model)
  en_002  Chimney/Vent Gas Dispersion (Gaussian plume model)

Both tools implement the exact, universally-cited governing equation
(inverse-square point-source radiation; the Gaussian plume equation).
The empirical sub-correlations that would normally FEED these equations
- API 521's fraction-radiated (F) correlations, and the Pasquill-Gifford
dispersion-coefficient curves for sigma_y/sigma_z as a function of
downwind distance and atmospheric stability class - are exposed as
direct user inputs with typical ranges cited, rather than computed
internally, since both require reading a specific empirical chart/table
rather than applying a single remembered formula.
"""

import math
from utils.tool_roadmap import ToolSpec, InputSpec
from utils.ui_components import check_positive, run_validators


# =======================================================================
# TOOL: FLARE STACK THERMAL RADIATION (API 521 POINT-SOURCE MODEL)
# =======================================================================

def compute_flare_radiation(values: dict) -> dict:
    """
    K = (tau * F * Q) / (4*pi*R^2)
    Also solves inversely for the distance at which a target radiation
    level is reached (e.g. a personnel exposure limit).
    """
    heat_release_btu_hr = values["heat_release_btu_hr"]
    fraction_radiated_f = values["fraction_radiated_f"]
    transmissivity_tau = values["transmissivity_tau"]
    distance_ft = values["distance_ft"]
    target_radiation_limit = values.get("target_radiation_limit")

    has_error, has_warning, errors, warnings = run_validators(
        check_positive(heat_release_btu_hr, "Heat release rate"),
        check_positive(fraction_radiated_f, "Fraction radiated (F)"),
        check_positive(transmissivity_tau, "Atmospheric transmissivity"),
        check_positive(distance_ft, "Distance"),
    )
    if has_error:
        raise ValueError("; ".join(errors))
    if fraction_radiated_f > 1.0 or transmissivity_tau > 1.0:
        raise ValueError("Fraction radiated (F) and transmissivity (tau) must each be between 0 and 1.")

    k_radiation = (transmissivity_tau * fraction_radiated_f * heat_release_btu_hr) / (4 * math.pi * distance_ft ** 2)
    k_radiation_kw_m2 = k_radiation * 0.0031546

    result = {
        "Radiation Intensity at Distance (Btu/hr-ft2)": round(k_radiation, 2),
        "Radiation Intensity at Distance (kW/m2)": round(k_radiation_kw_m2, 4),
    }

    if target_radiation_limit and target_radiation_limit > 0:
        required_distance_ft = math.sqrt(
            (transmissivity_tau * fraction_radiated_f * heat_release_btu_hr) / (4 * math.pi * target_radiation_limit)
        )
        result["Required Distance for Target Limit (ft)"] = round(required_distance_ft, 1)

    result["_warnings"] = warnings
    return result


TOOL_FLARE_RADIATION = ToolSpec(
    key="en_001",
    title="Flare Stack Thermal Radiation (API 521)",
    category="Flare Systems & Depressurization",
    description="Point-source thermal radiation intensity at a given distance from a flare, per the API 521 model.",
    inputs=[
        InputSpec("heat_release_btu_hr", "Total Heat Release Rate (Q)", default=50000000.0, min_value=1.0, unit="(Btu/hr)"),
        InputSpec("fraction_radiated_f", "Fraction of Heat Radiated (F)", default=0.20, min_value=0.01, max_value=1.0, step=0.01,
                   help="Typically 0.15-0.35 for flares depending on fuel composition and flame characteristics - read from an API 521 F-factor correlation/chart for the specific fuel for a rigorous value."),
        InputSpec("transmissivity_tau", "Atmospheric Transmissivity (tau)", default=0.80, min_value=0.1, max_value=1.0, step=0.01,
                   help="Typically 0.7-0.85 for a clear day; lower for humid/hazy conditions."),
        InputSpec("distance_ft", "Distance from Flame Center (R)", default=200.0, min_value=1.0, unit="(ft)"),
        InputSpec("target_radiation_limit", "Target Radiation Limit (optional)", default=500.0, min_value=0.0, unit="(Btu/hr-ft2)",
                   help="If provided, also calculates the distance at which this level is reached (e.g. 500 Btu/hr-ft2 is a common short-exposure personnel limit per API 521)."),
    ],
    compute=compute_flare_radiation,
    formula_md=(
        r"$$K = \dfrac{\tau \cdot F \cdot Q}{4\pi R^2}$$"
        r"\n\nInverse (required distance for a target K): $R = \sqrt{\dfrac{\tau F Q}{4\pi K_{target}}}$"
    ),
    references=[
        "API Standard 521 - Pressure-relieving and Depressuring Systems, Section on Flare Radiation",
        "Brzustowski, T.A. & Sommer, E.C., API Proceedings - flare radiation modeling",
    ],
    assumptions=[
        "Point-source model - treats the entire flame as radiating from a single point, adequate for screening but less accurate very close to large flames (where a multi-point or solid-flame model would be more accurate).",
        "F (fraction radiated) and tau (transmissivity) are taken as direct inputs rather than computed from sub-correlations - use published API 521 correlations or a flare radiation study for the specific fuel/conditions for a rigorous value.",
        "Does not account for wind-induced flame tilt, which shifts the effective flame center and increases radiation on the downwind side.",
    ],
)


# =======================================================================
# TOOL: CHIMNEY/VENT GAS DISPERSION (GAUSSIAN PLUME MODEL)
# =======================================================================

def compute_gaussian_plume(values: dict) -> dict:
    """
    Ground-level, centerline concentration from a continuous elevated
    point source (Gaussian plume model):
      C = Q / (pi * u * sigma_y * sigma_z) * exp(-H^2 / (2*sigma_z^2))
    """
    emission_rate_g_s = values["emission_rate_g_s"]
    wind_speed_m_s = values["wind_speed_m_s"]
    sigma_y_m = values["sigma_y_m"]
    sigma_z_m = values["sigma_z_m"]
    effective_height_m = values["effective_height_m"]

    has_error, has_warning, errors, warnings = run_validators(
        check_positive(emission_rate_g_s, "Emission rate"), check_positive(wind_speed_m_s, "Wind speed"),
        check_positive(sigma_y_m, "Sigma-y"), check_positive(sigma_z_m, "Sigma-z"),
    )
    if has_error:
        raise ValueError("; ".join(errors))
    if effective_height_m < 0:
        raise ValueError("Effective stack height cannot be negative.")

    concentration_g_m3 = (
        emission_rate_g_s / (math.pi * wind_speed_m_s * sigma_y_m * sigma_z_m)
        * math.exp(-(effective_height_m ** 2) / (2 * sigma_z_m ** 2))
    )
    concentration_mg_m3 = concentration_g_m3 * 1000.0
    concentration_ug_m3 = concentration_g_m3 * 1e6

    warning = None
    if wind_speed_m_s < 1.0:
        warning = (
            "Wind speed below 1 m/s - the standard Gaussian plume model becomes unreliable under near-calm "
            "conditions (plume meandering and building/terrain effects dominate); treat this result as a "
            "rough estimate only."
        )

    return {
        "Ground-Level Concentration (g/m3)": round(concentration_g_m3, 8),
        "Ground-Level Concentration (mg/m3)": round(concentration_mg_m3, 5),
        "Ground-Level Concentration (ug/m3)": round(concentration_ug_m3, 2),
        "_warnings": [warning] if warning else [],
    }


TOOL_GAUSSIAN_PLUME = ToolSpec(
    key="en_002",
    title="Chimney/Vent Gas Dispersion (Gaussian Plume)",
    category="Consequence & Dispersion Modeling",
    description="Ground-level, downwind centerline concentration from a continuous elevated point source.",
    inputs=[
        InputSpec("emission_rate_g_s", "Emission Rate (Q)", default=10.0, min_value=0.001, unit="(g/s)"),
        InputSpec("wind_speed_m_s", "Wind Speed (u)", default=3.0, min_value=0.01, unit="(m/s)"),
        InputSpec("sigma_y_m", "Horizontal Dispersion Coefficient (sigma-y)", default=50.0, min_value=0.1, unit="(m)",
                   help="Read from a Pasquill-Gifford chart/correlation for the downwind distance and atmospheric stability class of interest."),
        InputSpec("sigma_z_m", "Vertical Dispersion Coefficient (sigma-z)", default=30.0, min_value=0.1, unit="(m)",
                   help="Read from a Pasquill-Gifford chart/correlation for the same downwind distance and stability class as sigma-y."),
        InputSpec("effective_height_m", "Effective Stack Height (H)", default=20.0, min_value=0.0, unit="(m)",
                   help="Physical stack height plus plume rise due to exit velocity and buoyancy."),
    ],
    compute=compute_gaussian_plume,
    formula_md=(
        r"$$C(x,0,0,H) = \dfrac{Q}{\pi u \sigma_y \sigma_z}\exp\left(-\dfrac{H^2}{2\sigma_z^2}\right)$$"
    ),
    references=[
        "Turner, D.B., Workbook of Atmospheric Dispersion Estimates, US EPA",
        "Pasquill, F. (1961), Meteorological Magazine - atmospheric stability classification",
    ],
    assumptions=[
        "sigma_y and sigma_z are taken as direct inputs rather than computed from a Pasquill-Gifford stability-class correlation - supply values read from the appropriate chart/table for the downwind distance and stability class of interest.",
        "Evaluates concentration at a single downwind distance (implicit in the sigma_y/sigma_z pair chosen) at ground level, on the plume centerline - off-centerline or elevated-receptor concentrations require the full 3D form of the equation.",
        "Assumes flat terrain, no chemical reaction/deposition of the pollutant, and steady-state emission and meteorology.",
        "Not valid for near-calm wind conditions (typically < 1 m/s) - flagged but not blocked.",
    ],
)


REGISTRY: dict[str, ToolSpec] = {
    TOOL_FLARE_RADIATION.key: TOOL_FLARE_RADIATION,
    TOOL_GAUSSIAN_PLUME.key: TOOL_GAUSSIAN_PLUME,
}
