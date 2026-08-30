"""
domains/dom_03_heat_transfer/hx_engine.py
============================================
Domain 3: Heat Transfer & Thermal Equipment. Pure Python physics, zero
Streamlit calls.

Live tools:
  ht_001  LMTD (Counter-Current)
  ht_002  Heat Exchanger Duty & Required Area
"""

import math
from utils.tool_roadmap import ToolSpec, InputSpec
from utils.ui_components import check_positive, run_validators


# =======================================================================
# TOOL: LMTD (COUNTER-CURRENT)
# =======================================================================

def compute_lmtd(values: dict) -> dict:
    th_in = values["th_in"]
    th_out = values["th_out"]
    tc_in = values["tc_in"]
    tc_out = values["tc_out"]

    dt1 = th_in - tc_out
    dt2 = th_out - tc_in
    if dt1 <= 0 or dt2 <= 0:
        raise ValueError(
            "Invalid temperatures - a temperature cross has occurred (dT1 or dT2 <= 0). "
            "Check that hot-side temps exceed cold-side temps throughout."
        )

    if abs(dt1 - dt2) < 1e-6:
        lmtd = dt1
    else:
        lmtd = (dt1 - dt2) / math.log(dt1 / dt2)

    return {
        "dT1 (degF)": round(dt1, 2),
        "dT2 (degF)": round(dt2, 2),
        "LMTD (degF)": round(lmtd, 3),
        "_warnings": [],
    }


TOOL_LMTD = ToolSpec(
    key="ht_001",
    title="Log Mean Temperature Difference (LMTD)",
    category="Shell & Tube Heat Exchangers",
    description="Counter-current LMTD from the four terminal temperatures.",
    inputs=[
        InputSpec("th_in", "Hot Fluid Inlet Temperature", default=250.0, unit="(degF)"),
        InputSpec("th_out", "Hot Fluid Outlet Temperature", default=150.0, unit="(degF)"),
        InputSpec("tc_in", "Cold Fluid Inlet Temperature", default=100.0, unit="(degF)"),
        InputSpec("tc_out", "Cold Fluid Outlet Temperature", default=180.0, unit="(degF)"),
    ],
    compute=compute_lmtd,
    formula_md=(
        r"$$LMTD = \dfrac{\Delta T_1 - \Delta T_2}{\ln(\Delta T_1/\Delta T_2)}, \quad "
        r"\Delta T_1 = T_{h,in}-T_{c,out}, \ \Delta T_2 = T_{h,out}-T_{c,in}$$"
    ),
    references=["Perry's Chemical Engineers' Handbook, Section 11 - Heat Transfer Equipment", "Kern, D.Q., Process Heat Transfer"],
    assumptions=[
        "Counter-current flow arrangement assumed - for 1-shell-pass/multiple-tube-pass or crossflow exchangers, apply an Ft correction factor to this LMTD.",
        "Constant fluid properties and overall heat transfer coefficient U across the exchanger.",
    ],
)


# =======================================================================
# TOOL: HEAT EXCHANGER DUTY & REQUIRED AREA
# =======================================================================

def compute_hx_duty_area(values: dict) -> dict:
    mass_flow = values["mass_flow_lb_hr"]
    cp = values["cp_btu_lb_f"]
    t_in = values["t_in_f"]
    t_out = values["t_out_f"]
    u = values["u_btu_hr_ft2_f"]
    lmtd = values["lmtd_f"]

    has_error, has_warning, errors, warnings = run_validators(
        check_positive(mass_flow, "Mass flow"), check_positive(cp, "Cp"),
        check_positive(u, "U"), check_positive(lmtd, "LMTD"),
    )
    if has_error:
        raise ValueError("; ".join(errors))

    q_btu_hr = mass_flow * cp * (t_out - t_in)
    q_kw = abs(q_btu_hr) * 0.000293071
    area_ft2 = abs(q_btu_hr) / (u * lmtd)
    area_m2 = area_ft2 * 0.092903

    return {
        "Duty (Btu/hr)": round(q_btu_hr, 1),
        "Duty (kW)": round(q_kw, 3),
        "Required Area (ft2)": round(area_ft2, 2),
        "Required Area (m2)": round(area_m2, 3),
        "_warnings": warnings,
    }


TOOL_HX_DUTY_AREA = ToolSpec(
    key="ht_002",
    title="Heat Exchanger Duty & Required Area",
    category="Shell & Tube Heat Exchangers",
    description="Thermal duty from stream conditions, then required heat transfer area given U and LMTD.",
    inputs=[
        InputSpec("mass_flow_lb_hr", "Mass Flow Rate", default=10000.0, min_value=0.01, unit="(lb/hr)"),
        InputSpec("cp_btu_lb_f", "Specific Heat (Cp)", default=0.5, min_value=0.01, unit="(Btu/lb-degF)"),
        InputSpec("t_in_f", "Stream Inlet Temperature", default=100.0, unit="(degF)"),
        InputSpec("t_out_f", "Stream Outlet Temperature", default=180.0, unit="(degF)"),
        InputSpec("u_btu_hr_ft2_f", "Overall Heat Transfer Coefficient (U)", default=100.0, min_value=0.01, unit="(Btu/hr-ft2-degF)"),
        InputSpec("lmtd_f", "LMTD", default=59.44, min_value=0.01, unit="(degF)",
                   help="Use the LMTD tool above to calculate this from your four terminal temperatures, then enter it here to chain the calculations."),
    ],
    compute=compute_hx_duty_area,
    formula_md=r"$$Q = \dot{m}\,C_p\,(T_{out}-T_{in}), \quad A = \dfrac{Q}{U \cdot LMTD}$$",
    references=["Perry's Chemical Engineers' Handbook, Section 11", "TEMA Standards"],
    assumptions=[
        "Screening-level sizing only - true design must account for fouling factors, the Ft correction factor for non-1-shell-pass exchangers, and detailed TEMA rating.",
        "U must be estimated or taken from vendor/literature data for the specific service - this tool does not calculate U from first principles.",
    ],
)


# =======================================================================
# TOOL: CYLINDRICAL PIPE INSULATION HEAT LOSS
# =======================================================================

def compute_insulation_heat_loss(values: dict) -> dict:
    """
    Steady-state radial conduction through a single insulation layer
    plus outside convection, per unit pipe length:
      Q/L = (T_pipe - T_amb) / [ln(r2/r1)/(2*pi*k_ins) + 1/(2*pi*r2*h_conv)]
    """
    pipe_od_in = values["pipe_od_in"]
    insulation_thickness_in = values["insulation_thickness_in"]
    k_insulation = values["k_insulation"]
    h_conv = values["h_conv"]
    t_pipe_f = values["t_pipe_f"]
    t_ambient_f = values["t_ambient_f"]

    has_error, has_warning, errors, warnings = run_validators(
        check_positive(pipe_od_in, "Pipe OD"), check_positive(insulation_thickness_in, "Insulation thickness"),
        check_positive(k_insulation, "Insulation conductivity"), check_positive(h_conv, "Convection coefficient"),
    )
    if has_error:
        raise ValueError("; ".join(errors))
    if t_pipe_f <= t_ambient_f:
        raise ValueError("Pipe temperature must exceed ambient temperature for heat loss to occur outward.")

    r1_ft = (pipe_od_in / 2.0) / 12.0
    r2_ft = r1_ft + (insulation_thickness_in / 12.0)
    delta_t = t_pipe_f - t_ambient_f

    r_cond = math.log(r2_ft / r1_ft) / (2 * math.pi * k_insulation)
    r_conv = 1.0 / (2 * math.pi * r2_ft * h_conv)
    r_total = r_cond + r_conv

    q_per_ft = delta_t / r_total
    t_surface_f = t_ambient_f + q_per_ft * r_conv

    warning = None
    if t_surface_f > 140:
        warning = (
            f"Calculated outer surface temperature ({t_surface_f:.0f} degF) exceeds ~140 degF - this may "
            "present a personnel burn hazard; consider thicker insulation or a personnel protection guard."
        )

    return {
        "Conduction Resistance (hr-ft-degF/Btu)": round(r_cond, 4),
        "Convection Resistance (hr-ft-degF/Btu)": round(r_conv, 4),
        "Heat Loss per Unit Length (Btu/hr-ft)": round(q_per_ft, 2),
        "Outer Surface Temperature (degF)": round(t_surface_f, 1),
        "_warnings": warnings + ([warning] if warning else []),
    }


TOOL_INSULATION = ToolSpec(
    key="ht_004",
    title="Cylindrical Pipe Insulation Heat Loss",
    category="Insulation & Heat Loss",
    description="Steady-state heat loss per unit length and outer surface temperature for an insulated pipe.",
    inputs=[
        InputSpec("pipe_od_in", "Pipe Outside Diameter", default=6.0, min_value=0.1, unit="(in)"),
        InputSpec("insulation_thickness_in", "Insulation Thickness", default=2.0, min_value=0.1, unit="(in)"),
        InputSpec("k_insulation", "Insulation Thermal Conductivity (k)", default=0.03, min_value=0.001, unit="(Btu/hr-ft-degF)",
                   help="Typical mineral wool/calcium silicate: 0.02-0.04 Btu/hr-ft-degF at moderate temperatures."),
        InputSpec("h_conv", "Outside Convection Coefficient (h)", default=2.0, min_value=0.1, unit="(Btu/hr-ft2-degF)",
                   help="Typical still-air natural convection: 1.5-3 Btu/hr-ft2-degF; higher in wind."),
        InputSpec("t_pipe_f", "Pipe (Process) Temperature", default=300.0, unit="(degF)"),
        InputSpec("t_ambient_f", "Ambient Temperature", default=70.0, unit="(degF)"),
    ],
    compute=compute_insulation_heat_loss,
    formula_md=(
        r"$$\dfrac{Q}{L} = \dfrac{T_{pipe}-T_{amb}}{\dfrac{\ln(r_2/r_1)}{2\pi k_{ins}}+\dfrac{1}{2\pi r_2 h}}$$"
    ),
    references=["Incropera & DeWitt, Fundamentals of Heat and Mass Transfer", "Perry's Chemical Engineers' Handbook, Section 11"],
    assumptions=[
        "Single insulation layer, steady-state, 1-D radial conduction - does not account for jacketing, weather barriers, or thermal bridging at supports.",
        "Outside convection coefficient (h) is a direct input - for a more rigorous value, compute h from a natural/forced convection correlation for the specific pipe size, orientation, and wind condition.",
        "Radiation heat loss from the outer surface is not included separately - h can be adjusted upward to approximate a combined convection+radiation coefficient if needed.",
    ],
)


# =======================================================================
# TOOL: AIR-COOLED HEAT EXCHANGER (FIN-FAN) AIR-SIDE SIZING
# =======================================================================

def compute_air_cooled_sizing(values: dict) -> dict:
    duty_btu_hr = values["duty_btu_hr"]
    cp_air = values["cp_air"]
    t_air_in_f = values["t_air_in_f"]
    t_air_out_f = values["t_air_out_f"]
    rho_air = values["rho_air"]
    face_velocity_ft_min = values["face_velocity_ft_min"]

    has_error, has_warning, errors, warnings = run_validators(
        check_positive(duty_btu_hr, "Duty"), check_positive(cp_air, "Air Cp"),
        check_positive(rho_air, "Air density"), check_positive(face_velocity_ft_min, "Face velocity"),
    )
    if has_error:
        raise ValueError("; ".join(errors))
    if t_air_out_f <= t_air_in_f:
        raise ValueError("Air outlet temperature must exceed air inlet temperature (air is being heated by the process stream).")

    delta_t_air = t_air_out_f - t_air_in_f
    m_air_lb_hr = duty_btu_hr / (cp_air * delta_t_air)
    vol_flow_ft3_hr = m_air_lb_hr / rho_air
    vol_flow_acfm = vol_flow_ft3_hr / 60.0
    face_area_ft2 = vol_flow_acfm / face_velocity_ft_min

    extra_warning = None
    if face_velocity_ft_min < 300 or face_velocity_ft_min > 700:
        extra_warning = (
            f"Face velocity of {face_velocity_ft_min:.0f} ft/min is outside the typical 300-700 ft/min "
            "range for induced/forced-draft air coolers - verify this is intentional for the specific fan/bay design."
        )

    return {
        "Air Mass Flow Rate (lb/hr)": round(m_air_lb_hr, 1),
        "Air Volumetric Flow (ACFM)": round(vol_flow_acfm, 1),
        "Required Face Area (ft2)": round(face_area_ft2, 2),
        "_warnings": warnings + ([extra_warning] if extra_warning else []),
    }


TOOL_AIR_COOLED = ToolSpec(
    key="ht_003",
    title="Air-Cooled Heat Exchanger (Fin-Fan) Air-Side Sizing",
    category="Air-Cooled Heat Exchangers",
    description="Air-side mass/volumetric flow and required face area for a fin-fan cooler, from process duty and air temperature rise.",
    inputs=[
        InputSpec("duty_btu_hr", "Process Duty (Q)", default=2000000.0, min_value=1.0, unit="(Btu/hr)"),
        InputSpec("cp_air", "Air Specific Heat (Cp)", default=0.24, min_value=0.01, unit="(Btu/lb-degF)"),
        InputSpec("t_air_in_f", "Air Inlet (Ambient) Temperature", default=90.0, unit="(degF)"),
        InputSpec("t_air_out_f", "Air Outlet Temperature", default=140.0, unit="(degF)"),
        InputSpec("rho_air", "Air Density (at average conditions)", default=0.0709, min_value=0.001, unit="(lb/ft3)",
                   help="Roughly 0.075 lb/ft3 at 70 degF, decreasing with temperature - use a value near the average air temperature through the bundle."),
        InputSpec("face_velocity_ft_min", "Design Face Velocity", default=500.0, min_value=1.0, unit="(ft/min)",
                   help="Typical induced/forced-draft air coolers: 300-700 ft/min face velocity."),
    ],
    compute=compute_air_cooled_sizing,
    formula_md=(
        r"$$\dot m_{air} = \dfrac{Q}{C_{p,air}\Delta T_{air}}, \quad A_{face} = \dfrac{\dot m_{air}/\rho_{air}}{V_{face}}$$"
    ),
    references=["GPSA Engineering Data Book, Section 9 - Air-Cooled Heat Exchangers", "API 661 - Air-Cooled Heat Exchangers for General Refinery Service"],
    assumptions=[
        "Air-side sizing only - does not size the finned-tube bundle (tube rows, fin density, tube-side pressure drop) or select the fan/motor.",
        "Air density is a direct input rather than computed from ideal gas law at actual site elevation/temperature - use a value appropriate to the average bundle air temperature and site elevation.",
        "Screening-level only - final air cooler selection should go through a vendor's rating program (API 661 compliant).",
    ],
)


REGISTRY: dict[str, ToolSpec] = {
    TOOL_LMTD.key: TOOL_LMTD,
    TOOL_HX_DUTY_AREA.key: TOOL_HX_DUTY_AREA,
    TOOL_INSULATION.key: TOOL_INSULATION,
    TOOL_AIR_COOLED.key: TOOL_AIR_COOLED,
}
