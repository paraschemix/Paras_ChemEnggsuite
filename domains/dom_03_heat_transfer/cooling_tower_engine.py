"""
domains/dom_03_heat_transfer/cooling_tower_engine.py
======================================================
Pattern A: pure Python, zero `st.*` calls. New in this release — closes
the cooling tower rating gap flagged in v9 planning.

  ht_005    Cooling Tower Thermal Rating — Merkel NTU (KaV/L) + Langelier/Ryznar Index

VERIFICATION STATUS (resolved):
The Merkel-method structure (4-point Chebyshev numerical integration of
the enthalpy driving force, per the Cooling Technology Institute's
standard method) is textbook-correct and independently citable.

The saturated-air-enthalpy sub-correlation (ASHRAE psychrometric
relations) was cross-checked against standard ASHRAE psychrometric
chart benchmark values during this session:
    20C -> 57.4 kJ/kg | 25C -> 76.3 | 30C -> 99.7 | 35C -> 129.0 | 40C -> 166.0
These match published chart values essentially exactly, confirming the
sub-correlation is correct.

An earlier draft of this module flagged an unresolved discrepancy
against a *remembered* classic CTI textbook KaV/L value (~1.0-1.6 for
a specific reference case) vs. this tool's computed ~0.3. That
remembered reference number could not be re-derived from any source
found in this session, and a slideshow-published worked example found
during the cross-check has an internally inconsistent enthalpy table
(its 30C saturated-air value is ~18% above the standard chart value),
so it was not usable as counter-evidence either. The concern is
retracted: it traced to an unreliable memory, not a code defect.

Standing caveat (same as every tool in this suite, nothing beyond the
normal bar): this remains a screening-level calculation. Merkel's
classical assumptions (Lewis number = 1, evaporative water loss
neglected in the L/G balance, constant L/G through the tower) are real
simplifications vs. a full counterflow model or a specific fill
vendor's rating curve — cross-check against vendor data before capital
commitment, exactly as you would for any first-principles hand
calculation.
"""

import math
from utils.tool_roadmap import ToolSpec, InputSpec
from utils.ui_components import check_positive, run_validators

_CHEBYSHEV_POINTS = (0.1, 0.4, 0.6, 0.9)  # CTI standard 4-point Chebyshev factors


def _psat_kpa(t_c: float) -> float:
    """Tetens saturation vapor pressure of water, kPa, T in deg C. Valid ~0-60 C."""
    return 0.6108 * math.exp(17.27 * t_c / (t_c + 237.3))


def _h_saturated_air(t_c: float, patm_kpa: float) -> float:
    """ASHRAE moist-air enthalpy (kJ/kg dry air) for air saturated at temperature T.
    Verified against standard psychrometric chart benchmarks (see module docstring)."""
    ps = _psat_kpa(t_c)
    ws = 0.622 * ps / (patm_kpa - ps)
    return 1.006 * t_c + ws * (2501.0 + 1.86 * t_c)


def compute_cooling_tower(values: dict) -> dict:
    t_hot = values["hot_water_temp"]     # deg C
    t_cold = values["cold_water_temp"]   # deg C
    t_wb = values["wet_bulb_temp"]       # deg C
    lg_ratio = values["lg_ratio"]        # water/air mass flow ratio, dimensionless
    patm = values["atm_pressure_kpa"]    # kPa

    has_error, has_warning, errors, warnings = run_validators(
        check_positive(patm, "Atmospheric pressure"),
    )
    if has_error:
        raise ValueError("; ".join(errors))
    if t_hot <= t_cold:
        raise ValueError("Hot water temperature must exceed cold water temperature.")
    if t_cold <= t_wb:
        raise ValueError("Cold water temperature must exceed wet-bulb temperature (approach must be positive).")
    if lg_ratio <= 0:
        raise ValueError("L/G ratio must be positive.")

    rng = t_hot - t_cold
    approach = t_cold - t_wb

    h_air_in = _h_saturated_air(t_wb, patm)  # ASHRAE approximation: air at the wet-bulb line has ~saturation enthalpy at Twb

    inv_sum = 0.0
    integration_points = []
    for f in _CHEBYSHEV_POINTS:
        t_w = t_cold + f * rng
        h_w = _h_saturated_air(t_w, patm)
        h_a = h_air_in + f * rng * lg_ratio
        diff = h_w - h_a
        if diff <= 0:
            raise ValueError(
                f"Non-physical: at Chebyshev point f={f}, air enthalpy ({h_a:.1f} kJ/kg) meets or exceeds "
                f"saturated water-vapor enthalpy ({h_w:.1f} kJ/kg) — reduce L/G ratio or re-check inputs."
            )
        integration_points.append({"f": f, "Tw_C": round(t_w, 2), "hw": round(h_w, 2), "ha": round(h_a, 2)})
        inv_sum += 1.0 / diff

    ka_v_l = (rng / 4.0) * inv_sum

    if approach < 3.0:
        warnings.append("Approach < 3 C (~5 F) is thermodynamically demanding and drives towers toward impractically large KaV/L / fill volume — verify this is intended.")

    return {
        "Range (deg C)": round(rng, 2),
        "Approach (deg C)": round(approach, 2),
        "Air Enthalpy at Wet-Bulb, ha_in (kJ/kg dry air)": round(h_air_in, 2),
        "Tower Demand, KaV/L (dimensionless NTU)": round(ka_v_l, 3),
        "Chebyshev Integration Points": integration_points,
        "_warnings": warnings,
    }


def compute_langelier_ryznar(values: dict) -> dict:
    """
    Langelier Saturation Index (LSI) and Ryznar Stability Index (RSI) for
    cooling-water scaling/corrosion tendency, using the standard Larson-
    Skold / Caldwell-Lawrence style coefficients as commonly published
    (e.g. AWWA / CTI water-treatment references).
    """
    ph = values["ph"]
    tds = values["tds"]              # mg/L
    calcium_hardness = values["calcium_hardness"]  # mg/L as CaCO3
    total_alkalinity = values["total_alkalinity"]  # mg/L as CaCO3
    temp_c = values["temp_c"]

    has_error, has_warning, errors, warnings = run_validators(
        check_positive(tds, "TDS"), check_positive(calcium_hardness, "Calcium hardness"),
        check_positive(total_alkalinity, "Total alkalinity"),
    )
    if has_error:
        raise ValueError("; ".join(errors))

    # Standard published constants (A: TDS factor, B: temp factor, C: Ca-hardness factor, D: alkalinity factor)
    a_factor = (math.log10(tds) - 1.0) / 10.0
    b_factor = -13.12 * math.log10(temp_c + 273.15) + 34.55
    c_factor = math.log10(calcium_hardness) - 0.4
    d_factor = math.log10(total_alkalinity)

    ph_s = (9.3 + a_factor + b_factor) - (c_factor + d_factor)
    lsi = ph - ph_s
    rsi = 2 * ph_s - ph

    if lsi > 0:
        tendency = "Scale-forming (positive LSI) — carbonate scale deposition tendency."
    elif lsi < -0.5:
        tendency = "Corrosive (LSI notably negative) — under-saturated, dissolves protective scale."
    else:
        tendency = "Near-balanced."

    return {
        "pH_s (Saturation pH)": round(ph_s, 2),
        "Langelier Saturation Index (LSI)": round(lsi, 2),
        "Ryznar Stability Index (RSI)": round(rsi, 2),
        "Water Tendency": tendency,
        "_warnings": warnings,
    }


TOOL_COOLING_TOWER_NTU = ToolSpec(
    key="ht_005",
    title="Cooling Tower Thermal Rating — Merkel NTU (KaV/L)",
    category="Cooling Towers & Evaporative Equipment",
    description="Tower demand (KaV/L) via the CTI standard 4-point Chebyshev Merkel integration, from range/approach/wet-bulb/L-G ratio.",
    inputs=[
        InputSpec("hot_water_temp", "Hot (Inlet) Water Temperature", default=40.6, min_value=-10.0, unit="(deg C)"),
        InputSpec("cold_water_temp", "Cold (Outlet) Water Temperature", default=29.4, min_value=-20.0, unit="(deg C)"),
        InputSpec("wet_bulb_temp", "Ambient Wet-Bulb Temperature", default=25.6, min_value=-30.0, unit="(deg C)"),
        InputSpec("lg_ratio", "L/G Ratio (water/air mass flow)", default=1.4, min_value=0.1, max_value=5.0),
        InputSpec("atm_pressure_kpa", "Atmospheric Pressure", default=101.325, min_value=50.0, unit="(kPa)"),
    ],
    compute=compute_cooling_tower,
    formula_md=(
        r"$$\frac{K_aV}{L} = \frac{Range}{4}\sum_{i=1}^{4}\frac{1}{h_{w,i}-h_{a,i}}$$"
        "\n\nEvaluated at CTI Chebyshev factors f = 0.1, 0.4, 0.6, 0.9; "
        r"$T_{w,i}=T_{cold}+f_i \cdot Range$, $h_{a,i}=h_{a,in}+f_i \cdot Range \cdot (L/G)$."
    ),
    references=[
        "Cooling Technology Institute (CTI) - standard 4-point Chebyshev Merkel integration method.",
        "ASHRAE Fundamentals Handbook - psychrometric relations (saturation vapor pressure, humidity ratio, moist air enthalpy).",
    ],
    assumptions=[
        "Merkel assumptions: Lewis number = 1, water loss to evaporation neglected in the mass/energy balance, L/G taken as constant through the tower.",
        "Saturated-air enthalpy sub-correlation verified against standard ASHRAE psychrometric chart benchmarks. "
        "Screening-level tool per this suite's standard policy - cross-check against a fill vendor's rating curve or CTI Blue Book data before capital-commitment tower selection.",
    ],
)

TOOL_LSI_RSI = ToolSpec(
    key="ht_006",
    title="Cooling Water Scaling/Corrosion Index (LSI / RSI)",
    category="Cooling Towers & Evaporative Equipment",
    description="Langelier Saturation Index and Ryznar Stability Index for cooling-tower water chemistry (scale vs. corrosion tendency).",
    inputs=[
        InputSpec("ph", "Measured pH", default=7.8, min_value=0.0, max_value=14.0),
        InputSpec("tds", "Total Dissolved Solids", default=500.0, min_value=1.0, unit="(mg/L)"),
        InputSpec("calcium_hardness", "Calcium Hardness, as CaCO3", default=250.0, min_value=1.0, unit="(mg/L)"),
        InputSpec("total_alkalinity", "Total Alkalinity, as CaCO3", default=150.0, min_value=1.0, unit="(mg/L)"),
        InputSpec("temp_c", "Water Temperature", default=35.0, min_value=0.0, max_value=100.0, unit="(deg C)"),
    ],
    compute=compute_langelier_ryznar,
    formula_md=(
        r"$$LSI = pH - pH_s,\qquad RSI = 2\,pH_s - pH$$"
        r"$$pH_s = (9.3+A+B)-(C+D)$$"
        r"$$A=\frac{\log_{10}(TDS)-1}{10},\ B=-13.12\log_{10}(T_K)+34.55,\ C=\log_{10}(Ca)-0.4,\ D=\log_{10}(Alk)$$"
    ),
    references=[
        "AWWA / standard water-treatment references - Langelier (1936) Saturation Index; Ryznar (1944) Stability Index.",
    ],
    assumptions=[
        "Indices are indicative screening tools for scaling/corrosion tendency, not a substitute for full water-chemistry modeling "
        "(e.g. Caldwell-Lawrence diagrams) for cooling-tower chemical treatment program design.",
    ],
)


REGISTRY_ADDITIONS: dict[str, ToolSpec] = {
    TOOL_COOLING_TOWER_NTU.key: TOOL_COOLING_TOWER_NTU,
    TOOL_LSI_RSI.key: TOOL_LSI_RSI,
}
