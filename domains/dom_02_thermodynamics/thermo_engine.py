"""
domains/dom_02_thermodynamics/thermo_engine.py
=================================================
Domain 2: Thermodynamics, VLE & Transport Properties. Pure Python
physics, zero Streamlit calls.

Live tools:
  tp_001  Real Gas Compressibility Factor (Papay correlation)
  tp_002  Vapor Pressure & Dew Point (Antoine equation)
"""

import math
from utils.tool_roadmap import ToolSpec, InputSpec
from utils.ui_components import check_positive, run_validators


# =======================================================================
# TOOL: REAL GAS Z-FACTOR (PAPAY CORRELATION)
# =======================================================================

def compute_papay_z_factor(values: dict) -> dict:
    p_psia = values["p_psia"]
    t_r = values["t_r"]
    pc_psia = values["pc_psia"]
    tc_r = values["tc_r"]

    has_error, has_warning, errors, warnings = run_validators(
        check_positive(p_psia, "Pressure"), check_positive(t_r, "Temperature"),
        check_positive(pc_psia, "Critical pressure"), check_positive(tc_r, "Critical temperature"),
    )
    if has_error:
        raise ValueError("; ".join(errors))

    pr = p_psia / pc_psia
    tr = t_r / tc_r
    z = 1 - 3.52 * pr * math.exp(-2.26 * tr) + 0.274 * pr ** 2 * math.exp(-1.878 * tr)

    range_warning = None
    if pr > 15 or tr < 1.0 or tr > 3.0:
        range_warning = (
            f"Pr={pr:.2f}, Tr={tr:.2f} are outside the typical validated range for the Papay "
            "correlation (roughly Pr<15, 1<Tr<3) - treat result as a rough estimate only."
        )

    return {
        "Reduced Pressure (Pr)": round(pr, 4),
        "Reduced Temperature (Tr)": round(tr, 4),
        "Z Factor": round(z, 4),
        "_warnings": warnings + ([range_warning] if range_warning else []),
    }


TOOL_Z_FACTOR = ToolSpec(
    key="tp_001",
    title="Real Gas Compressibility Factor (Papay)",
    category="Equations of State (EOS)",
    description="Explicit Papay correlation Z-factor estimate for real gas behavior.",
    inputs=[
        InputSpec("p_psia", "Pressure (P)", default=2000.0, min_value=1.0, unit="(psia)"),
        InputSpec("t_r", "Temperature (T)", default=600.0, min_value=1.0, unit="(degR)"),
        InputSpec("pc_psia", "Critical Pressure (Pc)", default=667.0, min_value=1.0, unit="(psia)",
                   help="Typical for pipeline-quality (methane-dominant) natural gas."),
        InputSpec("tc_r", "Critical Temperature (Tc)", default=343.0, min_value=1.0, unit="(degR)"),
    ],
    compute=compute_papay_z_factor,
    formula_md=r"$$Z = 1 - 3.52 P_r e^{-2.26 T_r} + 0.274 P_r^2 e^{-1.878 T_r}, \quad P_r=P/P_c,\ T_r=T/T_c$$",
    references=["Papay, J. (1968), OGIL MUSZ. TUD. KUTATO INTEZETENEK KOZLEMENYEI"],
    assumptions=[
        "Explicit correlation - reasonably accurate for sweet natural gas over moderate Pr/Tr ranges.",
        "Less accurate than Standing-Katz charts or a full EOS (Peng-Robinson, SRK) for sour gas or high-pressure conditions.",
        "Default critical properties are typical for pipeline-quality natural gas - use actual mixture criticals for other gases.",
    ],
)


# =======================================================================
# TOOL: VAPOR PRESSURE & DEW POINT (ANTOINE EQUATION)
# =======================================================================

ANTOINE_TABLE = {
    "Water": (8.07131, 1730.63, 233.426, "1-100 degC"),
    "Methane": (6.61184, 389.93, 266.00, "-181 to -160 degC"),
    "Ethane": (6.80266, 656.40, 256.00, "-138 to -75 degC"),
    "Propane": (6.82973, 813.20, 248.00, "-108 to -25 degC"),
    "n-Butane": (6.83029, 945.90, 240.00, "-77 to 19 degC"),
    "n-Pentane": (6.85296, 1064.63, 232.00, "-50 to 58 degC"),
}


def compute_vapor_pressure_dewpoint(values: dict) -> dict:
    component = values["component"]
    mode = values["mode"]  # "Vapor Pressure at T" or "Dew Point at P"
    t_degc = values.get("t_degc")
    partial_pressure_mmhg = values.get("partial_pressure_mmhg")

    coef = ANTOINE_TABLE.get(component)
    if coef is None:
        raise ValueError(f"Unknown component: {component}")
    a, b, c, valid_range = coef

    if mode == "Vapor Pressure at T":
        if t_degc is None:
            raise ValueError("Temperature is required for vapor pressure mode.")
        log_p = a - b / (c + t_degc)
        p_mmhg = 10 ** log_p
        return {
            "Vapor Pressure (mmHg)": round(p_mmhg, 3),
            "Vapor Pressure (kPa)": round(p_mmhg * 0.133322, 4),
            "Valid Range": valid_range,
            "_warnings": [],
        }
    else:
        if partial_pressure_mmhg is None or partial_pressure_mmhg <= 0:
            raise ValueError("Partial pressure must be positive for dew point mode.")
        log_p = math.log10(partial_pressure_mmhg)
        t_dew_c = b / (a - log_p) - c
        return {
            "Dew Point (degC)": round(t_dew_c, 2),
            "Dew Point (degF)": round(t_dew_c * 9 / 5 + 32, 2),
            "Valid Range": valid_range,
            "_warnings": [
                "Antoine correlation is a single-component approximation. For multi-component "
                "hydrocarbon dew point (e.g. natural gas), a full K-value flash is required for "
                "accurate results - use this as a quick screening estimate only."
            ],
        }


TOOL_VAPOR_PRESSURE = ToolSpec(
    key="tp_002",
    title="Vapor Pressure & Dew Point (Antoine Equation)",
    category="Liquid Activity Coefficients & Non-Ideal VLE",
    description="Single-component vapor pressure at a given temperature, or dew point at a given partial pressure.",
    inputs=[
        InputSpec("component", "Component", default=0.0, input_type="select", options=list(ANTOINE_TABLE.keys())),
        InputSpec("mode", "Mode", default=0.0, input_type="select",
                   options=["Vapor Pressure at T", "Dew Point at P"]),
        InputSpec("t_degc", "Temperature", default=25.0, unit="(degC)",
                   help="Used only in 'Vapor Pressure at T' mode."),
        InputSpec("partial_pressure_mmhg", "Partial Pressure", default=23.76, min_value=0.001, unit="(mmHg)",
                   help="Used only in 'Dew Point at P' mode."),
    ],
    compute=compute_vapor_pressure_dewpoint,
    formula_md=(
        r"$$\log_{10}(P_{mmHg}) = A - \dfrac{B}{C+T[^\circ C]}$$ "
        r"Inverted for dew point: $T_{dew} = \dfrac{B}{A-\log_{10}P} - C$"
    ),
    references=["Antoine, C. (1888), Comptes Rendus", "NIST Chemistry WebBook (Antoine parameter tables)"],
    assumptions=[
        "Single-component approximation. Multi-component hydrocarbon dew point (natural gas) requires a full K-value flash for accurate results.",
        "Antoine coefficients are valid only within each component's stated temperature range - extrapolation outside that range is unreliable.",
    ],
)


REGISTRY: dict[str, ToolSpec] = {
    TOOL_Z_FACTOR.key: TOOL_Z_FACTOR,
    TOOL_VAPOR_PRESSURE.key: TOOL_VAPOR_PRESSURE,
}
