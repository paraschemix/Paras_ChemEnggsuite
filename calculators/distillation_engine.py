"""
calculators/distillation_engine.py
=====================================
Houses calculation logic for the Mass Transfer & Aromatics Processing
domain (tools #11-20 in the roadmap).

Fully implemented:
  - Tool #11: Shortcut Distillation (Fenske-Underwood-Gilliland)
  - Tool #12: Tray Tower Hydraulics & Flooding (Fair's Method)
  - Tool #13: Packed Column Sizing & HETP
  - Tool #14: Two-Phase Vertical Flash Drum Sizing (GPSA / API 12J)
  - Tool #15: Horizontal Liquid-Liquid Decanter Sizing
  - Tool #16: Absorption & Stripping Factor (Kremser Equations)
  - Tool #17: Aromatics BTX Splitter / Fractionation Estimator
  - Tool #18: Liquid-Liquid Solvent Extraction (Stage Calculation)
  - Tool #19: Reflux Ratio vs. Utility Cost Optimization
  - Tool #20: Vapor Entrainment Velocity & Demister Sizing
"""

import math
from calculators.registry_base import ToolSpec, InputSpec
from utils.validators import check_positive, check_fraction_0_1, run_validators


# =======================================================================
# TOOL 11: SHORTCUT DISTILLATION (Fenske - Underwood - Gilliland)
# =======================================================================

def compute_shortcut_distillation(values: dict) -> dict:
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

    fenske_numerator = (xD_LK / xHK_D) * (xHK_B / xLK_B)
    if fenske_numerator <= 0:
        raise ValueError("Fenske separation factor is non-positive — check distillate/bottoms compositions.")
    n_min = math.log(fenske_numerator) / math.log(alpha) - 1

    r_min = (1 / (alpha - 1)) * ((xD_LK / xF_LK) - alpha * (xHK_D / xF_HK))

    if r_actual <= r_min:
        raise ValueError(
            f"Actual reflux ratio R ({r_actual}) must exceed the calculated Rmin ({r_min:.3f}) — "
            "operating below minimum reflux is thermodynamically infeasible."
        )

    x_gill = (r_actual - r_min) / (r_actual + 1)
    if x_gill <= 0:
        raise ValueError("Computed Gilliland X <= 0 — check R vs Rmin inputs.")
    y_gill = 1 - math.exp(((1 + 54.4 * x_gill) / (11 + 117.2 * x_gill)) * ((x_gill - 1) / math.sqrt(x_gill)))
    n_actual = (n_min + y_gill) / (1 - y_gill)

    reflux_ratio_multiple = r_actual / r_min

    extra_warnings = []
    if reflux_ratio_multiple < 1.1:
        extra_warnings.append(
            f"R/Rmin = {reflux_ratio_multiple:.2f} is very close to 1.0 (minimum reflux) — Gilliland correlation "
            "becomes unreliable near Rmin; typical economic design targets R/Rmin of 1.1-1.5."
        )
    if reflux_ratio_multiple > 2.0:
        extra_warnings.append(
            f"R/Rmin = {reflux_ratio_multiple:.2f} is well above typical economic optimum (~1.1-1.5) — "
            "this may indicate excessive utility cost."
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
    description="Combined FUG short-cut method: minimum stages, minimum reflux, and actual stages at chosen operating reflux.",
    inputs=[
        InputSpec("xD_LK", "x(LK) in Distillate", default=0.98, min_value=0.001, max_value=0.999, step=0.001),
        InputSpec("xHK_D", "x(HK) in Distillate", default=0.02, min_value=0.001, max_value=0.999, step=0.001),
        InputSpec("xLK_B", "x(LK) in Bottoms", default=0.02, min_value=0.001, max_value=0.999, step=0.001),
        InputSpec("xHK_B", "x(HK) in Bottoms", default=0.98, min_value=0.001, max_value=0.999, step=0.001),
        InputSpec("xF_LK", "x(LK) in Feed", default=0.50, min_value=0.001, max_value=0.999, step=0.001),
        InputSpec("xF_HK", "x(HK) in Feed", default=0.50, min_value=0.001, max_value=0.999, step=0.001),
        InputSpec("alpha", "Relative Volatility (alpha, LK/HK)", default=2.50, min_value=1.01, step=0.01),
        InputSpec("r_actual", "Chosen Actual Reflux Ratio (R)", default=1.70, min_value=0.01, step=0.01),
    ],
    compute=compute_shortcut_distillation,
    formula_md=(
        r"$$N_{min} = \frac{\ln\left[\left(\frac{x_{LK}}{x_{HK}}\right)_D \left(\frac{x_{HK}}{x_{LK}}\right)_B\right]}{\ln \alpha} - 1$$"
        "\n\n"
        r"$$R_{min} = \frac{1}{\alpha - 1}\left[\frac{x_{D,LK}}{x_{F,LK}} - \alpha \frac{x_{D,HK}}{x_{F,HK}}\right]$$"
    ),
    references=["Fenske (1932)", "Underwood (1948)", "Gilliland (1940)", "Perry's Handbook Section 13"],
    assumptions=["Constant relative volatility across column.", "Binary or pseudo-binary treatment."],
)


# =======================================================================
# TOOL 12: TRAY TOWER HYDRAULICS & FLOODING (Fair's Correlation)
# =======================================================================

def compute_tray_hydraulics(values: dict) -> dict:
    l_rate = values["l_rate"]  # kg/h
    v_rate = values["v_rate"]  # kg/h
    rho_l = values["rho_l"]    # kg/m3
    rho_v = values["rho_v"]    # kg/m3
    sigma = values["sigma"]    # mN/m (dyn/cm)
    tray_spacing = values["tray_spacing"] # mm
    target_flood = values["target_flood"] # %

    has_error, _, errors, _ = run_validators(
        check_positive(l_rate, "Liquid Flow Rate"),
        check_positive(v_rate, "Vapor Flow Rate"),
        check_positive(rho_l, "Liquid Density"),
        check_positive(rho_v, "Vapor Density"),
        check_positive(sigma, "Surface Tension"),
    )
    if has_error:
        raise ValueError("; ".join(errors))

    # Flow Parameter (FLV)
    flv = (l_rate / v_rate) * math.sqrt(rho_v / rho_l)

    # Base Capacity Factor C_sb at 20 dyn/cm (Fair's empiricism baseline)
    # Approx function for C_sb based on tray spacing and FLV
    c_base = 0.03 + 0.0004 * tray_spacing - 0.015 * math.log10(max(flv, 0.01))
    c_sb = max(0.01, c_base) * math.pow(sigma / 20.0, 0.2)

    # Flood Vapor Velocity (u_flood) [m/s]
    u_flood = c_sb * math.sqrt((rho_l - rho_v) / rho_v)
    
    # Target Operating Velocity [m/s]
    u_design = u_flood * (target_flood / 100.0)

    # Required Net Vapor Area (A_net) [m2]
    v_vol_flow = (v_rate / rho_v) / 3600.0  # m3/s
    a_net = v_vol_flow / u_design

    # Column Diameter assuming Active Area = 82% of total cross-section
    a_total = a_net / 0.82
    dia = math.sqrt(4 * a_total / math.pi)

    return {
        "Flow Parameter (FLV)": round(flv, 4),
        "Capacity Factor C_sb (m/s)": round(c_sb, 4),
        "Flooding Velocity u_flood (m/s)": round(u_flood, 2),
        "Design Velocity (m/s)": round(u_design, 2),
        "Net Active Area Required (m2)": round(a_net, 3),
        "Calculated Column Diameter (m)": round(dia, 2),
    }


TOOL_TRAY_HYDRAULICS = ToolSpec(
    key="mt_012",
    title="Tray Tower Hydraulics & Flooding",
    category="Distillation & Separation",
    description="Sizing trayed columns based on Fair's entrainment flooding velocity correlation.",
    inputs=[
        InputSpec("l_rate", "Liquid Flow Rate (kg/h)", default=50000.0, min_value=1.0),
        InputSpec("v_rate", "Vapor Flow Rate (kg/h)", default=45000.0, min_value=1.0),
        InputSpec("rho_l", "Liquid Density (kg/m3)", default=750.0, min_value=10.0),
        InputSpec("rho_v", "Vapor Density (kg/m3)", default=3.2, min_value=0.01),
        InputSpec("sigma", "Surface Tension (mN/m)", default=18.0, min_value=1.0),
        InputSpec("tray_spacing", "Tray Spacing (mm)", default=600.0, min_value=300.0, max_value=900.0),
        InputSpec("target_flood", "Target % Flooding", default=80.0, min_value=50.0, max_value=90.0),
    ],
    compute=compute_tray_hydraulics,
    formula_md=r"$$F_{LV} = \frac{L}{V}\sqrt{\frac{\rho_v}{\rho_l}}, \quad u_{flood} = C_{sb} \left(\frac{\sigma}{20}\right)^{0.2} \sqrt{\frac{\rho_l - \rho_v}{\rho_v}}$$ ",
    references=["Fair, J.R. (1961), Petro/Chem Engineer", "Perry's Section 14"],
    assumptions=["Sieve or valve trays with standard geometry.", "Active area equals 82% of total column cross-section."],
)


# =======================================================================
# TOOL 13: PACKED COLUMN SIZING & HETP
# =======================================================================

def compute_packed_column(values: dict) -> dict:
    v_rate = values["v_rate"]      # kg/h
    rho_v = values["rho_v"]        # kg/m3
    f_factor = values["f_factor"]  # Pa^0.5
    hetp = values["hetp"]          # m
    n_stages = values["n_stages"]  # count

    has_error, _, errors, _ = run_validators(
        check_positive(v_rate, "Vapor Flow Rate"),
        check_positive(rho_v, "Vapor Density"),
        check_positive(f_factor, "Operating F-Factor"),
        check_positive(hetp, "HETP"),
    )
    if has_error:
        raise ValueError("; ".join(errors))

    v_vol = (v_rate / rho_v) / 3600.0  # m3/s
    u_v = f_factor / math.sqrt(rho_v)   # m/s
    area = v_vol / u_v
    dia = math.sqrt(4 * area / math.pi)
    bed_height = n_stages * hetp

    return {
        "Superficial Vapor Velocity (m/s)": round(u_v, 3),
        "Required Cross-Sectional Area (m2)": round(area, 3),
        "Calculated Diameter (m)": round(dia, 2),
        "Total Packed Bed Height (m)": round(bed_height, 2),
    }


TOOL_PACKED_BED_HETP = ToolSpec(
    key="mt_013",
    title="Packed Column Sizing & HETP",
    category="Distillation & Separation",
    description="Sizes structured/random packed columns using F-Factor velocity criteria and HETP stage conversions.",
    inputs=[
        InputSpec("v_rate", "Vapor Flow Rate (kg/h)", default=30000.0, min_value=1.0),
        InputSpec("rho_v", "Vapor Density (kg/m3)", default=2.5, min_value=0.01),
        InputSpec("f_factor", "Design F-Factor (Pa^0.5)", default=2.0, min_value=0.5, max_value=3.5),
        InputSpec("hetp", "HETP per Stage (m)", default=0.5, min_value=0.1, max_value=2.0),
        InputSpec("n_stages", "Theoretical Stages Required", default=25.0, min_value=1.0),
    ],
    compute=compute_packed_column,
    formula_md=r"$$u_v = \frac{F_{factor}}{\sqrt{\rho_v}}, \quad A = \frac{V_{vol}}{u_v}, \quad Height = N_{stages} \times HETP$$",
    references=["GPSA Engineering Data Book, Section 19"],
    assumptions=["Uniform vapor distribution across packing.", "No wall-channeling effects."],
)


# =======================================================================
# TOOL 14: TWO-PHASE VERTICAL FLASH DRUM SIZING
# =======================================================================

def compute_flash_drum(values: dict) -> dict:
    v_flow = values["v_flow"]  # kg/h
    l_flow = values["l_flow"]  # kg/h
    rho_v = values["rho_v"]    # kg/m3
    rho_l = values["rho_l"]    # kg/m3
    k_v = values["k_v"]        # m/s (Souders-Brown factor)
    surge_time = values["surge_time"] # min

    v_vol = (v_flow / rho_v) / 3600.0  # m3/s
    u_max = k_v * math.sqrt((rho_l - rho_v) / rho_v)
    a_min = v_vol / u_max
    d_min = math.sqrt(4 * a_min / math.pi)

    # Liquid surge volume
    l_vol_min = (l_flow / rho_l) * (surge_time / 60.0)  # m3
    h_liquid = l_vol_min / a_min
    
    # Total Height = Liquid Level + Disengagement Height (min 1.0 m or 2xD)
    h_disengage = max(1.0, 2.0 * d_min)
    h_total = h_liquid + h_disengage
    ld_ratio = h_total / d_min

    return {
        "Max Permissible Vapor Velocity (m/s)": round(u_max, 3),
        "Minimum Drum Diameter (m)": round(d_min, 2),
        "Liquid Surge Volume (m3)": round(l_vol_min, 2),
        "Liquid Height (m)": round(h_liquid, 2),
        "Total Drum Height (m)": round(h_total, 2),
        "L/D Ratio": round(ld_ratio, 2),
    }


TOOL_FLASH_DRUM = ToolSpec(
    key="mt_014",
    title="Vertical Flash Drum Sizing",
    category="Distillation & Separation",
    description="Sizes two-phase gas-liquid separator vessel diameter and height using Sounders-Brown vapor velocity constraints.",
    inputs=[
        InputSpec("v_flow", "Vapor Mass Flow (kg/h)", default=20000.0, min_value=1.0),
        InputSpec("l_flow", "Liquid Mass Flow (kg/h)", default=80000.0, min_value=1.0),
        InputSpec("rho_v", "Vapor Density (kg/m3)", default=12.0, min_value=0.01),
        InputSpec("rho_l", "Liquid Density (kg/m3)", default=650.0, min_value=10.0),
        InputSpec("k_v", "Souders-Brown K-Factor (m/s)", default=0.075, min_value=0.01, max_value=0.2),
        InputSpec("surge_time", "Liquid Retention Time (min)", default=10.0, min_value=1.0),
    ],
    compute=compute_flash_drum,
    formula_md=r"$$u_{max} = K \sqrt{\frac{\rho_l - \rho_v}{\rho_v}}, \quad A_{min} = \frac{Q_v}{u_{max}}$$ ",
    references=["GPSA Data Book Section 7", "API 12J"],
    assumptions=["Vertical orientation.", "Standard wire mesh mist eliminator assumed if K = 0.075-0.10."],
)


# =======================================================================
# TOOL 15: HORIZONTAL LIQUID-LIQUID DECANTER SIZING
# =======================================================================

def compute_decanter(values: dict) -> dict:
    q_heavy = values["q_heavy"] / 3600.0  # m3/s
    q_light = values["q_light"] / 3600.0  # m3/s
    rho_heavy = values["rho_heavy"]      # kg/m3
    rho_light = values["rho_light"]      # kg/m3
    mu_continuous = values["mu_cont"]    # cP (mPa.s)
    d_drop = values["d_drop"] * 1e-6     # m

    d_rho = rho_heavy - rho_light
    if d_rho <= 0:
        raise ValueError("Heavy phase density must exceed light phase density.")

    # Stokes' Law settling velocity (m/s)
    mu_kg = mu_continuous * 1e-3  # Pa.s
    v_settle = (9.81 * (d_drop**2) * d_rho) / (18.0 * mu_kg)

    # Total liquid area based on horizontal settling
    q_total = q_heavy + q_light
    a_interface = q_total / v_settle  # L x D required area
    
    # Vessel diameter assuming L/D = 4
    dia = math.sqrt(a_interface / 4.0)
    length = 4.0 * dia
    retention_time = (math.pi * (dia**2) / 4.0 * length) / q_total / 60.0  # minutes

    return {
        "Droplet Settling Velocity (mm/s)": round(v_settle * 1000.0, 3),
        "Interfacial Area Required (m2)": round(a_interface, 2),
        "Calculated Diameter (m)": round(dia, 2),
        "Calculated Length (m)": round(length, 2),
        "Total Retention Time (min)": round(retention_time, 1),
    }


TOOL_DECANTER = ToolSpec(
    key="mt_015",
    title="Horizontal Liquid-Liquid Decanter",
    category="Distillation & Separation",
    description="Sizes liquid-liquid separator vessels using Stokes' Law droplet settling velocities.",
    inputs=[
        InputSpec("q_heavy", "Heavy Phase Volumetric Flow (m3/h)", default=15.0, min_value=0.1),
        InputSpec("q_light", "Light Phase Volumetric Flow (m3/h)", default=45.0, min_value=0.1),
        InputSpec("rho_heavy", "Heavy Phase Density (kg/m3)", default=1000.0, min_value=500.0),
        InputSpec("rho_light", "Light Phase Density (kg/m3)", default=860.0, min_value=400.0),
        InputSpec("mu_cont", "Continuous Phase Viscosity (cP)", default=0.6, min_value=0.01),
        InputSpec("d_drop", "Target Droplet Diameter (microns)", default=150.0, min_value=10.0),
    ],
    compute=compute_decanter,
    formula_md=r"$$u_s = \frac{g d_p^2 (\rho_H - \rho_L)}{18 \mu_c}$$",
    references=["Perry's Chemical Engineers' Handbook, Section 15"],
    assumptions=["Spherical droplet behavior (Stokes' regime).", "L/D ratio equal to 4.0."],
)


# =======================================================================
# TOOL 16: ABSORPTION & STRIPPING FACTOR (Kremser Equations)
# =======================================================================

def compute_kremser(values: dict) -> dict:
    l_molar = values["l_molar"]  # kmol/h
    v_molar = values["v_molar"]  # kmol/h
    m_slope = values["m_slope"]  # equilibrium line slope y = mx
    y_in = values["y_in"]
    y_out = values["y_out"]
    x_in = values["x_in"]

    # Absorption Factor A = L / (m * V)
    a_factor = l_molar / (m_slope * v_molar)
    if abs(a_factor - 1.0) < 1e-4:
        a_factor = 1.0001  # Prevent divide by zero

    fraction_absorbed = (y_in - y_out) / (y_in - m_slope * x_in)
    if fraction_absorbed >= 1.0:
        raise ValueError("Target outlet fraction implies >100% absorption — check equilibrium slope.")

    # Kremser equation for theoretical stages N
    num = math.log(((y_in - m_slope * x_in) / (y_out - m_slope * x_in)) * (1.0 - 1.0 / a_factor) + 1.0 / a_factor)
    den = math.log(a_factor)
    n_stages = num / den

    return {
        "Absorption Factor (A)": round(a_factor, 3),
        "Fraction Absorbed": round(fraction_absorbed, 4),
        "Theoretical Stages Required (N)": round(n_stages, 2),
    }


TOOL_ABSORPTION_STRIPPING = ToolSpec(
    key="mt_016",
    title="Absorption & Stripping Factor (Kremser)",
    category="Distillation & Separation",
    description="Calculates required theoretical absorption stages using Kremser analytical solutions.",
    inputs=[
        InputSpec("l_molar", "Liquid Solvent Flow (kmol/h)", default=500.0, min_value=1.0),
        InputSpec("v_molar", "Gas Feed Flow (kmol/h)", default=350.0, min_value=1.0),
        InputSpec("m_slope", "Equilibrium Line Slope (m)", default=0.85, min_value=0.01),
        InputSpec("y_in", "Inlet Gas Mole Fraction", default=0.05, min_value=0.0001, max_value=0.99),
        InputSpec("y_out", "Target Outlet Gas Mole Fraction", default=0.002, min_value=0.00001, max_value=0.99),
        InputSpec("x_in", "Inlet Solvent Solute Mole Fraction", default=0.0, min_value=0.0, max_value=0.1),
    ],
    compute=compute_kremser,
    formula_md=r"$$A = \frac{L}{m V}, \quad N = \frac{\ln\left[\frac{y_{in}-mx_{in}}{y_{out}-mx_{in}}\left(1-\frac{1}{A}\right)+\frac{1}{A}\right]}{\ln A}$$",
    references=["Kremser, A. (1930), Natl. Pet. News", "Treybal, Mass Transfer Operations"],
    assumptions=["Dilute solute concentrations.", "Straight operating and equilibrium lines."],
)


# =======================================================================
# TOOL 17: AROMATICS BTX FRACTIONATION ESTIMATOR
# =======================================================================

def compute_btx_splitter(values: dict) -> dict:
    benzene_feed = values["b_feed"]   # kg/h
    toluene_feed = values["t_feed"]   # kg/h
    xylene_feed = values["x_feed"]    # kg/h
    b_rec = values["b_rec"] / 100.0   # Recovery of Benzene in overhead
    t_rec = values["t_rec"] / 100.0   # Recovery of Toluene in bottoms

    b_dist = benzene_feed * b_rec
    b_bot = benzene_feed * (1.0 - b_rec)

    t_bot = toluene_feed * t_rec
    t_dist = toluene_feed * (1.0 - t_rec)

    # All Xylenes go to bottoms in standard Benzene/Toluene splitter
    x_bot = xylene_feed
    x_dist = 0.0

    d_total = b_dist + t_dist + x_dist
    b_total = b_bot + t_bot + x_bot

    return {
        "Distillate Benzene (kg/h)": round(b_dist, 1),
        "Distillate Toluene (kg/h)": round(t_dist, 1),
        "Distillate Purity (wt% Benzene)": round((b_dist / d_total) * 100.0, 2),
        "Bottoms Toluene + Xylene (kg/h)": round(t_bot + x_bot, 1),
        "Bottoms Benzene Slip (kg/h)": round(b_bot, 1),
    }


TOOL_BTX_FRACTIONATION = ToolSpec(
    key="mt_017",
    title="Aromatics BTX Splitter Estimator",
    category="Distillation & Separation",
    description="Shortcut material balance estimator for Benzene-Toluene-Xylene (BTX) fractionators.",
    inputs=[
        InputSpec("b_feed", "Feed Benzene (kg/h)", default=12000.0, min_value=0.0),
        InputSpec("t_feed", "Feed Toluene (kg/h)", default=18000.0, min_value=0.0),
        InputSpec("x_feed", "Feed Xylenes (kg/h)", default=10000.0, min_value=0.0),
        InputSpec("b_rec", "% Benzene Recovery in Distillate", default=99.5, min_value=80.0, max_value=99.99),
        InputSpec("t_rec", "% Toluene Recovery in Bottoms", default=99.0, min_value=80.0, max_value=99.99),
    ],
    compute=compute_btx_splitter,
    formula_md=r"$$D_B = F_B \times Rec_B, \quad B_T = F_T \times Rec_T$$",
    references=["Handbook of Aromatics Manufacturing"],
    assumptions=["Sharp split modeling.", "Xylenes act entirely as heavy key non-volatiles."],
)


# =======================================================================
# TOOL 18: LIQUID-LIQUID SOLVENT EXTRACTION
# =======================================================================

def compute_liquid_extraction(values: dict) -> dict:
    f_flow = values["f_flow"]  # Feed kg/h
    s_flow = values["s_flow"]  # Solvent kg/h
    k_dist = values["k_dist"]  # Distribution coefficient K = Y/X
    x_in = values["x_in"]      # Solute in feed

    # Extraction Factor E = K * (S / F)
    e_factor = k_dist * (s_flow / f_flow)
    if abs(e_factor - 1.0) < 1e-4:
        e_factor = 1.0001

    n_stages = values["n_stages"]
    
    # Fraction remaining in raffinate for N counter-current stages
    x_out_fraction = (e_factor - 1.0) / (math.pow(e_factor, n_stages + 1) - 1.0)
    x_out = x_in * x_out_fraction
    recovery = (1.0 - x_out_fraction) * 100.0

    return {
        "Extraction Factor (E)": round(e_factor, 3),
        "Raffinate Solute Conc (wt%)": round(x_out * 100.0, 3),
        "Solute Extraction Recovery (%)": round(recovery, 2),
    }


TOOL_SOLVENT_EXTRACTION = ToolSpec(
    key="mt_018",
    title="Liquid-Liquid Extraction Stages",
    category="Distillation & Separation",
    description="Multistage counter-current solvent extraction recovery estimator.",
    inputs=[
        InputSpec("f_flow", "Feed Flow Rate (kg/h)", default=10000.0, min_value=1.0),
        InputSpec("s_flow", "Solvent Flow Rate (kg/h)", default=5000.0, min_value=1.0),
        InputSpec("k_dist", "Distribution Coefficient (K = Y/X)", default=2.5, min_value=0.1),
        InputSpec("x_in", "Feed Solute Mass Fraction", default=0.15, min_value=0.001, max_value=0.8),
        InputSpec("n_stages", "Number of Equilibrium Stages", default=4.0, min_value=1.0, max_value=20.0),
    ],
    compute=compute_liquid_extraction,
    formula_md=r"$$E = K \frac{S}{F}, \quad \frac{X_N}{X_0} = \frac{E - 1}{E^{N+1} - 1}$$",
    references=["Perry's Chemical Engineers' Handbook, Section 15"],
    assumptions=["Immiscible carrier and solvent phases.", "Constant distribution coefficient K."],
)


# =======================================================================
# TOOL 19: REFLUX RATIO VS. UTILITY COST OPTIMIZATION
# =======================================================================

def compute_reflux_optimization(values: dict) -> dict:
    r_min = values["r_min"]
    r_actual = values["r_actual"]
    latent_heat = values["latent_heat"] # kJ/kg
    d_flow = values["d_flow"]           # kg/h
    steam_cost = values["steam_cost"]   # $/ton

    v_flow = d_flow * (r_actual + 1.0)
    reboiler_duty_kw = (v_flow * latent_heat) / 3600.0 / 1000.0  # MW
    annual_steam_ton = (v_flow * 8760.0) / 1000.0
    annual_cost = annual_steam_ton * steam_cost

    return {
        "Vapor Boilup Rate (kg/h)": round(v_flow, 1),
        "Reboiler Duty (MW)": round(reboiler_duty_kw, 2),
        "Annual Steam Consumption (Tons/yr)": round(annual_steam_ton, 0),
        "Estimated Annual Utility Cost ($/yr)": round(annual_cost, 0),
    }


TOOL_REFLUX_OPTIMIZATION = ToolSpec(
    key="mt_019",
    title="Reflux Ratio vs. Utility Cost",
    category="Distillation & Separation",
    description="Evaluates reboiler energy demand and operating utility cost impact across varying reflux ratios.",
    inputs=[
        InputSpec("r_min", "Minimum Reflux Ratio Rmin", default=1.2, min_value=0.1),
        InputSpec("r_actual", "Operating Reflux Ratio R", default=1.5, min_value=0.1),
        InputSpec("latent_heat", "Latent Heat of Vaporization (kJ/kg)", default=350.0, min_value=50.0),
        InputSpec("d_flow", "Distillate Product Rate (kg/h)", default=15000.0, min_value=1.0),
        InputSpec("steam_cost", "Steam Cost ($/ton)", default=25.0, min_value=1.0),
    ],
    compute=compute_reflux_optimization,
    formula_md=r"$$V = D(R+1), \quad Q_{reb} = V \cdot \Delta H_{vap}$$",
    references=["Turton et al., Analysis, Synthesis, and Design of Chemical Processes"],
    assumptions=["Reboiler duty equals condenser duty.", "8760 operating hours per year."],
)


# =======================================================================
# TOOL 20: VAPOR ENTRAINMENT VELOCITY & DEMISTER SIZING
# =======================================================================

def compute_entrainment_velocity(values: dict) -> dict:
    v_flow = values["v_flow"]  # m3/h
    rho_v = values["rho_v"]    # kg/m3
    rho_l = values["rho_l"]    # kg/m3
    k_demister = values["k_demister"] # m/s

    v_m3s = v_flow / 3600.0
    u_max = k_demister * math.sqrt((rho_l - rho_v) / rho_v)
    area_req = v_m3s / u_max
    dia_req = math.sqrt(4.0 * area_req / math.pi)

    return {
        "Max Permissible Velocity (m/s)": round(u_max, 3),
        "Demister Pad Area Required (m2)": round(area_req, 2),
        "Minimum Demister Diameter (m)": round(dia_req, 2),
    }


TOOL_ENTRAINMENT_VELOCITY = ToolSpec(
    key="mt_020",
    title="Vapor Entrainment & Demister Sizing",
    category="Distillation & Separation",
    description="Sizes wire mesh demister pads to eliminate liquid mist carryover in vapor streams.",
    inputs=[
        InputSpec("v_flow", "Vapor Volumetric Flow (m3/h)", default=12000.0, min_value=1.0),
        InputSpec("rho_v", "Vapor Density (kg/m3)", default=4.5, min_value=0.01),
        InputSpec("rho_l", "Liquid Density (kg/m3)", default=800.0, min_value=10.0),
        InputSpec("k_demister", "Demister K-Factor (m/s)", default=0.107, min_value=0.01, max_value=0.2),
    ],
    compute=compute_entrainment_velocity,
    formula_md=r"$$u_{max} = K_{demister} \sqrt{\frac{\rho_l - \rho_v}{\rho_v}}$$ ",
    references=["GPSA Engineering Data Book Section 7"],
    assumptions=["Standard 100-150 mm thick mesh demister pad.", "Uniform flow distribution."],
)


# =======================================================================
# DOMAIN REGISTRY
# =======================================================================

REGISTRY: dict[str, ToolSpec] = {
    TOOL_SHORTCUT_DISTILLATION.key: TOOL_SHORTCUT_DISTILLATION, # mt_011
    TOOL_TRAY_HYDRAULICS.key: TOOL_TRAY_HYDRAULICS,             # mt_012
    TOOL_PACKED_BED_HETP.key: TOOL_PACKED_BED_HETP,             # mt_013
    TOOL_FLASH_DRUM.key: TOOL_FLASH_DRUM,                       # mt_014
    TOOL_DECANTER.key: TOOL_DECANTER,                           # mt_015
    TOOL_ABSORPTION_STRIPPING.key: TOOL_ABSORPTION_STRIPPING,   # mt_016
    TOOL_BTX_FRACTIONATION.key: TOOL_BTX_FRACTIONATION,         # mt_017
    TOOL_SOLVENT_EXTRACTION.key: TOOL_SOLVENT_EXTRACTION,       # mt_018
    TOOL_REFLUX_OPTIMIZATION.key: TOOL_REFLUX_OPTIMIZATION,     # mt_019
    TOOL_ENTRAINMENT_VELOCITY.key: TOOL_ENTRAINMENT_VELOCITY,   # mt_020
}
