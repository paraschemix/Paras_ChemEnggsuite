"""
domains/dom_05_reaction/kinetics_engine.py
=============================================
Domain 5: Chemical Reaction Engineering & Kinetics. Pure Python physics,
zero Streamlit calls.

Live tools:
  kr_001  Space Velocity (WHSV)
  kr_002  Conversion, Selectivity & Yield
  kr_003  Adiabatic Temperature Rise
"""

from utils.tool_roadmap import ToolSpec, InputSpec
from utils.ui_components import check_positive, run_validators
import math


# =======================================================================
# TOOL: WHSV
# =======================================================================

def compute_whsv(values: dict) -> dict:
    feed = values["feed_mass_flow_lb_hr"]
    cat = values["catalyst_mass_lb"]

    has_error, has_warning, errors, warnings = run_validators(
        check_positive(feed, "Feed mass flow"), check_positive(cat, "Catalyst mass"),
    )
    if has_error:
        raise ValueError("; ".join(errors))

    whsv = feed / cat
    return {"WHSV (1/hr)": round(whsv, 3), "_warnings": warnings}


TOOL_WHSV = ToolSpec(
    key="kr_001",
    title="Space Velocity Calculator (WHSV)",
    category="Ideal Reactor Sizing",
    description="Weight Hourly Space Velocity - a normalized measure of catalyst loading rate.",
    inputs=[
        InputSpec("feed_mass_flow_lb_hr", "Feed Mass Flow", default=10000.0, min_value=0.01, unit="(lb/hr)"),
        InputSpec("catalyst_mass_lb", "Catalyst Mass", default=2500.0, min_value=0.01, unit="(lb)"),
    ],
    compute=compute_whsv,
    formula_md=r"$$WHSV = \dfrac{\text{feed mass flow}}{\text{catalyst mass}} \quad [\text{hr}^{-1}]$$",
    references=["Perry's Chemical Engineers' Handbook, Section 19 - Reactors"],
    assumptions=["Used to track catalyst cycle length and compare runs at different feed rates - does not itself indicate conversion or selectivity."],
)


# =======================================================================
# TOOL: CONVERSION, SELECTIVITY & YIELD
# =======================================================================

def compute_conversion_selectivity(values: dict) -> dict:
    c_in = values["c_in"]
    c_out = values["c_out"]
    product_moles = values.get("product_moles")
    reactant_moles_converted = values.get("reactant_moles_converted")

    has_error, has_warning, errors, warnings = run_validators(check_positive(c_in, "Inlet concentration/flow"))
    if has_error:
        raise ValueError("; ".join(errors))

    conv = ((c_in - c_out) / c_in) * 100.0
    result = {"Conversion (%)": round(conv, 3)}

    if product_moles is not None and reactant_moles_converted is not None and reactant_moles_converted > 0:
        sel = (product_moles / reactant_moles_converted) * 100.0
        result["Selectivity (%)"] = round(sel, 3)
        result["Yield (%)"] = round((conv / 100) * sel, 3)

    result["_warnings"] = warnings
    return result


TOOL_CONVERSION = ToolSpec(
    key="kr_002",
    title="Conversion, Selectivity & Yield Calculator",
    category="Kinetic Parameter Regression",
    description="Reactant conversion, product selectivity, and overall yield from concentration/flow data.",
    inputs=[
        InputSpec("c_in", "Inlet Concentration/Flow (Cin)", default=100.0, min_value=0.001),
        InputSpec("c_out", "Outlet Concentration/Flow (Cout)", default=35.0, min_value=0.0),
        InputSpec("product_moles", "Product Moles (optional)", default=58.0, min_value=0.0),
        InputSpec("reactant_moles_converted", "Reactant Moles Converted (optional)", default=65.0, min_value=0.0),
    ],
    compute=compute_conversion_selectivity,
    formula_md=(
        r"$$\text{Conversion \%} = \dfrac{C_{in}-C_{out}}{C_{in}}\times 100$$"
        r"$$\text{Selectivity \%} = \dfrac{\text{moles desired product}}{\text{moles reactant converted}}\times 100, "
        r"\quad \text{Yield \%} = \text{Conversion \%}\times\text{Selectivity \%}/100$$"
    ),
    references=["Fogler, H.S., Elements of Chemical Reaction Engineering"],
    assumptions=["Selectivity/yield only computed if product moles and reactant moles converted are both provided."],
)


# =======================================================================
# TOOL: ADIABATIC TEMPERATURE RISE
# =======================================================================

def compute_adiabatic_temp_rise(values: dict) -> dict:
    heat_of_reaction = values["heat_of_reaction_btu_lb"]
    conversion_fraction = values["conversion_fraction"]
    cp = values["cp_btu_lb_f"]

    has_error, has_warning, errors, warnings = run_validators(check_positive(cp, "Cp"))
    if has_error:
        raise ValueError("; ".join(errors))
    if not (0 <= conversion_fraction <= 1):
        raise ValueError("Conversion fraction must be between 0 and 1.")

    dt = (conversion_fraction * abs(heat_of_reaction)) / cp
    return {"Adiabatic Temperature Rise (degF)": round(dt, 2), "_warnings": warnings}


TOOL_ADIABATIC_RISE = ToolSpec(
    key="kr_003",
    title="Adiabatic Temperature Rise",
    category="Non-Isothermal Dynamics & Safety",
    description="Adiabatic temperature change if all reaction heat stays in the process stream.",
    inputs=[
        InputSpec("heat_of_reaction_btu_lb", "Heat of Reaction (magnitude)", default=850.0, unit="(Btu/lb)",
                   help="Enter as a positive magnitude - apply as a rise for exothermic reactions, a drop for endothermic."),
        InputSpec("conversion_fraction", "Conversion Fraction", default=0.65, min_value=0.0, max_value=1.0, step=0.01),
        InputSpec("cp_btu_lb_f", "Cp", default=0.55, min_value=0.01, unit="(Btu/lb-degF)"),
    ],
    compute=compute_adiabatic_temp_rise,
    formula_md=r"$$\Delta T_{ad} = \dfrac{X\cdot|\Delta H_{rxn}|}{C_p}$$",
    references=["Fogler, H.S., Elements of Chemical Reaction Engineering, Ch. 8"],
    assumptions=[
        "Single-pass estimate - does not account for reverse reactions, multiple reaction paths, or non-adiabatic heat losses.",
        "Used for reactor thermal design and quench-gas requirement estimates.",
    ],
)


# =======================================================================
# TOOL: CSTR vs. PFR VOLUME COMPARISON (n-th ORDER, ISOTHERMAL, CONSTANT DENSITY)
# =======================================================================

def compute_cstr_vs_pfr(values: dict) -> dict:
    """
    Constant-density, isothermal, n-th order reaction: -r_A = k*C_A^n.

    tau_PFR  = (C_A0^(1-n)/k) * [1-(1-X)^(1-n)]/(1-n)   for n != 1
    tau_PFR  = (1/k) * (-ln(1-X))                          for n == 1
    tau_CSTR = (C_A0^(1-n)/k) * X/(1-X)^n

    V = tau * v0 (volumetric flow rate)
    """
    k_rate = values["k_rate"]
    reaction_order_n = values["reaction_order_n"]
    c_a0 = values["c_a0"]
    conversion_x = values["conversion_x"]
    volumetric_flow = values["volumetric_flow"]

    has_error, has_warning, errors, warnings = run_validators(
        check_positive(k_rate, "Rate constant"), check_positive(c_a0, "Inlet concentration"),
        check_positive(volumetric_flow, "Volumetric flow rate"),
    )
    if has_error:
        raise ValueError("; ".join(errors))
    if not (0 < conversion_x < 1):
        raise ValueError("Conversion (X) must be strictly between 0 and 1.")

    if abs(reaction_order_n - 1.0) < 1e-9:
        tau_pfr = (1.0 / k_rate) * (-math.log(1 - conversion_x))
    else:
        tau_pfr = (c_a0 ** (1 - reaction_order_n) / k_rate) * (
            (1 - (1 - conversion_x) ** (1 - reaction_order_n)) / (1 - reaction_order_n)
        )

    tau_cstr = (c_a0 ** (1 - reaction_order_n) / k_rate) * (conversion_x / (1 - conversion_x) ** reaction_order_n)

    v_pfr = tau_pfr * volumetric_flow
    v_cstr = tau_cstr * volumetric_flow
    ratio = v_cstr / v_pfr if v_pfr > 0 else float("inf")

    extra_warning = None
    if conversion_x > 0.95:
        extra_warning = (
            f"Conversion of {conversion_x*100:.1f}% is very high - both tau_PFR and (especially) tau_CSTR "
            "become very sensitive to X near complete conversion; small input changes will swing the result significantly."
        )

    return {
        "PFR Space Time, tau (time units)": round(tau_pfr, 4),
        "CSTR Space Time, tau (time units)": round(tau_cstr, 4),
        "PFR Volume": round(v_pfr, 3),
        "CSTR Volume": round(v_cstr, 3),
        "CSTR/PFR Volume Ratio": round(ratio, 3),
        "_warnings": warnings + ([extra_warning] if extra_warning else []),
    }


TOOL_CSTR_VS_PFR = ToolSpec(
    key="kr_004",
    title="CSTR vs. PFR Volume Comparison (n-th Order)",
    category="Ideal Reactor Sizing",
    description="Compares required CSTR and PFR volumes for the same conversion, isothermal n-th order reaction, constant density.",
    inputs=[
        InputSpec("k_rate", "Rate Constant (k)", default=0.1, min_value=1e-6,
                   help="Units depend on reaction order n: for n=1, 1/time; for n=2, volume/(mol*time); etc."),
        InputSpec("reaction_order_n", "Reaction Order (n)", default=1.0, min_value=0.0, max_value=3.0, step=0.1),
        InputSpec("c_a0", "Inlet Concentration (C_A0)", default=2.0, min_value=1e-6, unit="(mol/vol)"),
        InputSpec("conversion_x", "Target Conversion (X)", default=0.90, min_value=0.001, max_value=0.999, step=0.001),
        InputSpec("volumetric_flow", "Volumetric Flow Rate (v0)", default=100.0, min_value=1e-6, unit="(vol/time)"),
    ],
    compute=compute_cstr_vs_pfr,
    formula_md=(
        r"$$\tau_{PFR} = \dfrac{C_{A0}^{1-n}}{k}\cdot\dfrac{1-(1-X)^{1-n}}{1-n} \quad (n\neq 1), "
        r"\quad \tau_{PFR}=\dfrac{-\ln(1-X)}{k}\ (n=1)$$"
        r"$$\tau_{CSTR} = \dfrac{C_{A0}^{1-n}}{k}\cdot\dfrac{X}{(1-X)^n}, \quad V=\tau \cdot v_0$$"
    ),
    references=["Fogler, H.S., Elements of Chemical Reaction Engineering, Ch. 2-4", "Levenspiel, O., Chemical Reaction Engineering"],
    assumptions=[
        "Isothermal, constant-density (liquid-phase or constant-volume gas-phase) system - not valid for reactions with significant volume change or non-isothermal operation.",
        "Single, irreversible n-th order reaction - does not account for reversible reactions, multiple reactions, or catalyst deactivation.",
        "For positive-order reactions (n>0), CSTR volume will always exceed PFR volume for the same conversion - this is the classic result from the Levenspiel-plot comparison of reactor performance.",
    ],
)


REGISTRY: dict[str, ToolSpec] = {
    TOOL_WHSV.key: TOOL_WHSV,
    TOOL_CONVERSION.key: TOOL_CONVERSION,
    TOOL_ADIABATIC_RISE.key: TOOL_ADIABATIC_RISE,
    TOOL_CSTR_VS_PFR.key: TOOL_CSTR_VS_PFR,
}
