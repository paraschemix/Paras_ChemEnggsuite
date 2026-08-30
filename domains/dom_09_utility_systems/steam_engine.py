"""
domains/dom_09_utility_systems/steam_engine.py
=================================================
Domain 9: Plant Utilities, Energy & Power Generation. Pure Python
physics, zero Streamlit calls.

Live tools:
  ut_001  Saturated Steam Properties Lookup
  ut_002  Flash Steam Percentage
"""

from utils.tool_roadmap import ToolSpec, InputSpec
from utils.ui_components import check_positive, run_validators

# P(psia), Tsat(F), hf, hfg, hg (Btu/lb), vg (ft3/lb) - standard
# saturated steam table, imperial units.
_STEAM_TABLE = [
    (1.0, 101.74, 69.74, 1036.0, 1105.8, 333.6),
    (5.0, 162.24, 130.13, 1000.9, 1131.1, 73.53),
    (14.7, 212.00, 180.17, 970.3, 1150.5, 26.80),
    (20.0, 227.96, 196.27, 960.1, 1156.3, 20.09),
    (50.0, 281.03, 250.24, 924.0, 1174.1, 8.514),
    (100.0, 327.82, 298.61, 888.6, 1187.2, 4.434),
    (150.0, 358.48, 330.65, 863.1, 1193.7, 3.016),
    (200.0, 381.80, 355.5, 843.0, 1198.4, 2.288),
    (300.0, 417.35, 394.0, 809.4, 1203.4, 1.5442),
    (400.0, 444.62, 424.2, 780.4, 1204.6, 1.1620),
    (500.0, 467.14, 449.6, 754.7, 1204.3, 0.9283),
    (600.0, 486.25, 471.8, 731.1, 1202.9, 0.7702),
    (800.0, 518.30, 509.8, 687.7, 1197.5, 0.5691),
    (1000.0, 544.75, 542.6, 646.5, 1189.1, 0.4459),
]


def _interp_steam(p_psia: float) -> dict:
    t = _STEAM_TABLE
    if p_psia <= t[0][0]:
        _, tsat, hf, hfg, hg, vg = t[0]
        return {"t_sat": tsat, "hf": hf, "hfg": hfg, "hg": hg, "vg": vg}
    if p_psia >= t[-1][0]:
        _, tsat, hf, hfg, hg, vg = t[-1]
        return {"t_sat": tsat, "hf": hf, "hfg": hfg, "hg": hg, "vg": vg}
    for i in range(len(t) - 1):
        p0, t0, hf0, hfg0, hg0, vg0 = t[i]
        p1, t1, hf1, hfg1, hg1, vg1 = t[i + 1]
        if p0 <= p_psia <= p1:
            frac = (p_psia - p0) / (p1 - p0)
            lerp = lambda a, b: a + frac * (b - a)
            return {
                "t_sat": lerp(t0, t1), "hf": lerp(hf0, hf1), "hfg": lerp(hfg0, hfg1),
                "hg": lerp(hg0, hg1), "vg": lerp(vg0, vg1),
            }
    _, tsat, hf, hfg, hg, vg = t[-1]
    return {"t_sat": tsat, "hf": hf, "hfg": hfg, "hg": hg, "vg": vg}


# =======================================================================
# TOOL: SATURATED STEAM PROPERTIES LOOKUP
# =======================================================================

def compute_steam_properties(values: dict) -> dict:
    p_psia = values["p_psia"]
    if p_psia <= 0:
        raise ValueError("Pressure must be positive.")

    props = _interp_steam(p_psia)
    return {
        "Saturation Temperature (degF)": round(props["t_sat"], 2),
        "hf - Liquid Enthalpy (Btu/lb)": round(props["hf"], 2),
        "hfg - Latent Heat (Btu/lb)": round(props["hfg"], 2),
        "hg - Vapor Enthalpy (Btu/lb)": round(props["hg"], 2),
        "vg - Specific Volume (ft3/lb)": round(props["vg"], 4),
        "_warnings": [],
    }


TOOL_STEAM_PROPERTIES = ToolSpec(
    key="ut_001",
    title="Saturated Steam Properties Lookup",
    category="Steam & Condensate Networks",
    description="Saturation temperature, enthalpies, and specific volume at a given pressure.",
    inputs=[
        InputSpec("p_psia", "Pressure", default=150.0, min_value=0.1, unit="(psia)"),
    ],
    compute=compute_steam_properties,
    formula_md="Linearly interpolated from a standard saturated steam table (imperial units).",
    references=["ASME Steam Tables (IAPWS-IF97 basis)"],
    assumptions=[
        "Linear interpolation between table points - for precision work beyond screening/estimation, use full IAPWS-IF97 steam tables.",
    ],
)


# =======================================================================
# TOOL: FLASH STEAM PERCENTAGE
# =======================================================================

def compute_flash_steam(values: dict) -> dict:
    p1_psia = values["p1_psia"]
    p2_psia = values["p2_psia"]

    if p2_psia >= p1_psia:
        raise ValueError("Downstream (flash) pressure must be lower than upstream pressure.")

    props1 = _interp_steam(p1_psia)
    props2 = _interp_steam(p2_psia)
    flash_pct = ((props1["hf"] - props2["hf"]) / props2["hfg"]) * 100.0

    return {
        "hf Upstream (Btu/lb)": round(props1["hf"], 2),
        "hf Downstream (Btu/lb)": round(props2["hf"], 2),
        "hfg Downstream (Btu/lb)": round(props2["hfg"], 2),
        "Flash Steam (%)": round(flash_pct, 2),
        "_warnings": [],
    }


TOOL_FLASH_STEAM = ToolSpec(
    key="ut_002",
    title="Flash Steam Percentage",
    category="Steam & Condensate Networks",
    description="Percentage of condensate that flashes to steam when throttled from a higher to a lower pressure.",
    inputs=[
        InputSpec("p1_psia", "Upstream Pressure", default=150.0, min_value=0.2, unit="(psia)"),
        InputSpec("p2_psia", "Flash (Downstream) Pressure", default=15.0, min_value=0.1, unit="(psia)"),
    ],
    compute=compute_flash_steam,
    formula_md=r"$$\%\text{Flash} = \dfrac{h_{f1}-h_{f2}}{h_{fg2}}\times 100$$",
    references=["Spirax Sarco Steam Engineering Tutorials", "ASME Steam Tables"],
    assumptions=["Single-stage throttling (isenthalpic) assumed - no heat loss to surroundings during the pressure drop."],
)


# =======================================================================
# TOOL: COOLING TOWER EVAPORATION, BLOWDOWN & MAKEUP
# =======================================================================

def compute_cooling_tower_balance(values: dict) -> dict:
    """
    E = 0.00085 * range(degF) * L(gpm)   [Cooling Technology Institute
        rule-of-thumb approximation, ~1% evaporation loss per 10 degF range]
    B = E / (COC - 1)     [from M = E + B, COC = M/B]
    M = E + B + D
    """
    circ_flow_gpm = values["circ_flow_gpm"]
    range_f = values["range_f"]
    cycles_of_concentration = values["cycles_of_concentration"]
    drift_loss_gpm = values.get("drift_loss_gpm", 0.0)

    has_error, has_warning, errors, warnings = run_validators(
        check_positive(circ_flow_gpm, "Circulating flow"), check_positive(range_f, "Cooling range"),
    )
    if has_error:
        raise ValueError("; ".join(errors))
    if cycles_of_concentration <= 1:
        raise ValueError("Cycles of concentration (COC) must be greater than 1.")

    evaporation_gpm = 0.00085 * range_f * circ_flow_gpm
    blowdown_gpm = evaporation_gpm / (cycles_of_concentration - 1)
    makeup_gpm = evaporation_gpm + blowdown_gpm + drift_loss_gpm

    return {
        "Evaporation Loss (gpm)": round(evaporation_gpm, 2),
        "Blowdown Required (gpm)": round(blowdown_gpm, 2),
        "Total Makeup Water Required (gpm)": round(makeup_gpm, 2),
        "Evaporation (% of Circulating Flow)": round(evaporation_gpm / circ_flow_gpm * 100, 3),
        "_warnings": warnings,
    }


TOOL_COOLING_TOWER = ToolSpec(
    key="ut_003",
    title="Cooling Tower Evaporation, Blowdown & Makeup",
    category="Cooling Water Systems",
    description="Water balance for a cooling tower: evaporation loss, required blowdown, and total makeup water.",
    inputs=[
        InputSpec("circ_flow_gpm", "Circulating Water Flow (L)", default=10000.0, min_value=1.0, unit="(USGPM)"),
        InputSpec("range_f", "Cooling Range (ΔT)", default=20.0, min_value=0.1, unit="(degF)",
                   help="Temperature drop across the tower: hot water return temp minus cold water supply temp."),
        InputSpec("cycles_of_concentration", "Target Cycles of Concentration (COC)", default=5.0, min_value=1.01, step=0.1,
                   help="Ratio of dissolved solids in blowdown to makeup water - higher COC means less blowdown/makeup but more scaling risk; typical range 3-8."),
        InputSpec("drift_loss_gpm", "Drift Loss (optional)", default=2.0, min_value=0.0, unit="(USGPM)",
                   help="Typically 0.001-0.02% of circulating flow for a modern drift eliminator; often small enough to neglect."),
    ],
    compute=compute_cooling_tower_balance,
    formula_md=(
        r"$$E = 0.00085 \times \Delta T \times L, \quad B = \dfrac{E}{COC-1}, \quad M = E+B+D$$"
    ),
    references=["Cooling Technology Institute (CTI) - cooling tower fundamentals", "Perry's Chemical Engineers' Handbook, Section 12 - Psychrometry, Evaporative Cooling"],
    assumptions=[
        "Evaporation estimate uses the common industry rule-of-thumb (~1% evaporation per 10 degF range) rather than a full psychrometric heat/mass balance - adequate for screening, but a detailed psychrometric calculation is more accurate for final design, especially at unusual ambient wet-bulb conditions.",
        "Drift loss is a small, typically-neglected term unless a specific drift eliminator performance value is known.",
    ],
)


REGISTRY: dict[str, ToolSpec] = {
    TOOL_STEAM_PROPERTIES.key: TOOL_STEAM_PROPERTIES,
    TOOL_FLASH_STEAM.key: TOOL_FLASH_STEAM,
    TOOL_COOLING_TOWER.key: TOOL_COOLING_TOWER,
}
