"""
domains/dom_10_instrumentation_control/control_engine.py
===========================================================
Domain 10: Process Dynamics, Instrumentation & Control. Pure Python
physics, zero Streamlit calls.

Live tools:
  ic_001  First-Order Plus Dead Time (FOPDT) Step Response
  ic_002  Ziegler-Nichols PID Tuning (Closed-Loop / Ultimate Gain Method)
"""

import math
from utils.tool_roadmap import ToolSpec, InputSpec
from utils.ui_components import check_positive, run_validators


# =======================================================================
# TOOL: FIRST-ORDER STEP RESPONSE
# =======================================================================

def compute_first_order_response(values: dict) -> dict:
    """y(t) = K*deltaU*(1 - exp(-(t-theta)/tau)) for t >= theta, else 0 (dead time)."""
    k_gain = values["k_gain"]
    delta_u = values["delta_u"]
    tau = values["tau"]
    dead_time = values["dead_time"]
    t = values["time"]

    has_error, has_warning, errors, warnings = run_validators(check_positive(tau, "Time constant (tau)"))
    if has_error:
        raise ValueError("; ".join(errors))
    if dead_time < 0 or t < 0:
        raise ValueError("Dead time and evaluation time must be non-negative.")

    if t < dead_time:
        y = 0.0
        pct_complete = 0.0
    else:
        y = k_gain * delta_u * (1 - math.exp(-(t - dead_time) / tau))
        y_final = k_gain * delta_u
        pct_complete = (y / y_final * 100.0) if y_final != 0 else 0.0

    return {
        "Response at t (process units)": round(y, 4),
        "Final Steady-State Value": round(k_gain * delta_u, 4),
        "Percent of Final Value Reached (%)": round(pct_complete, 2),
        "_warnings": warnings,
    }


TOOL_FOPDT = ToolSpec(
    key="ic_001",
    title="First-Order Plus Dead Time (FOPDT) Step Response",
    category="Dynamic System Response",
    description="Process response at a given time to a step input change, for a first-order-plus-dead-time model.",
    inputs=[
        InputSpec("k_gain", "Process Gain (K)", default=2.0, help="Change in output per unit change in input, at steady state."),
        InputSpec("delta_u", "Step Input Change", default=5.0),
        InputSpec("tau", "Time Constant (tau)", default=10.0, min_value=0.001, unit="(time units)"),
        InputSpec("dead_time", "Dead Time (theta)", default=0.0, min_value=0.0, unit="(time units)"),
        InputSpec("time", "Evaluation Time (t)", default=10.0, min_value=0.0, unit="(time units)"),
    ],
    compute=compute_first_order_response,
    formula_md=r"$$y(t) = K\Delta u\left(1-e^{-(t-\theta)/\tau}\right), \quad t \geq \theta$$",
    references=["Seborg, Edgar, Mellichamp & Doyle, Process Dynamics and Control", "Smith & Corripio, Principles and Practice of Automatic Process Control"],
    assumptions=[
        "Linear first-order-plus-dead-time (FOPDT) model - many real processes are only approximately first-order; higher-order dynamics will deviate from this response shape.",
        "Step input assumed to occur at t=0.",
    ],
)


# =======================================================================
# TOOL: ZIEGLER-NICHOLS PID TUNING (CLOSED-LOOP / ULTIMATE GAIN METHOD)
# =======================================================================

def compute_zn_pid_tuning(values: dict) -> dict:
    ku = values["ku"]
    pu = values["pu"]
    controller_type = values["controller_type"]

    has_error, has_warning, errors, warnings = run_validators(
        check_positive(ku, "Ultimate gain (Ku)"), check_positive(pu, "Ultimate period (Pu)"),
    )
    if has_error:
        raise ValueError("; ".join(errors))

    if controller_type == "P":
        kc = 0.5 * ku
        return {"Kc (Controller Gain)": round(kc, 4), "_warnings": warnings}
    elif controller_type == "PI":
        kc = 0.45 * ku
        ti = pu / 1.2
        return {"Kc (Controller Gain)": round(kc, 4), "Ti (Integral Time)": round(ti, 4), "_warnings": warnings}
    else:  # PID
        kc = 0.6 * ku
        ti = pu / 2.0
        td = pu / 8.0
        return {
            "Kc (Controller Gain)": round(kc, 4),
            "Ti (Integral Time)": round(ti, 4),
            "Td (Derivative Time)": round(td, 4),
            "_warnings": warnings,
        }


TOOL_ZN_PID = ToolSpec(
    key="ic_002",
    title="Ziegler-Nichols PID Tuning (Ultimate Gain Method)",
    category="PID Controller Tuning",
    description="Controller tuning parameters from the ultimate gain (Ku) and ultimate period (Pu) found via closed-loop testing.",
    inputs=[
        InputSpec("ku", "Ultimate Gain (Ku)", default=4.0, min_value=0.01,
                   help="Controller gain at which the closed loop sustains constant-amplitude oscillation (found experimentally or from a stability analysis)."),
        InputSpec("pu", "Ultimate Period (Pu)", default=10.0, min_value=0.01, unit="(time units)",
                   help="Period of the sustained oscillation at Ku."),
        InputSpec("controller_type", "Controller Type", default=0.0, input_type="select", options=["PID", "PI", "P"]),
    ],
    compute=compute_zn_pid_tuning,
    formula_md=(
        r"**P:** $K_c=0.5K_u$ &nbsp; **PI:** $K_c=0.45K_u,\ T_i=P_u/1.2$ &nbsp; "
        r"**PID:** $K_c=0.6K_u,\ T_i=P_u/2,\ T_d=P_u/8$"
    ),
    references=["Ziegler, J.G. & Nichols, N.B. (1942), Trans. ASME", "Seborg, Edgar, Mellichamp & Doyle, Process Dynamics and Control"],
    assumptions=[
        "Classic Ziegler-Nichols closed-loop tuning tends to give an aggressive, underdamped response (~25% overshoot on a setpoint change) - many practitioners detune (e.g. reduce Kc by 30-50%) for a more conservative response in production.",
        "Finding Ku and Pu experimentally (relay/ultimate-gain testing) introduces process upsets - use with caution on sensitive processes.",
    ],
)


# =======================================================================
# TOOL: FREQUENCY RESPONSE (BODE POINT) FOR FOPDT
# =======================================================================

def compute_bode_point(values: dict) -> dict:
    """
    Gp(s) = K*exp(-theta*s) / (tau*s + 1)
    At s=jw:
      |G(jw)| = K / sqrt(1 + (w*tau)^2)
      angle(G(jw)) = -atan(w*tau) - w*theta   [radians; dead time adds pure phase lag]
    """
    k_gain = values["k_gain"]
    tau = values["tau"]
    dead_time = values["dead_time"]
    frequency_rad = values["frequency_rad"]

    has_error, has_warning, errors, warnings = run_validators(check_positive(tau, "Time constant"))
    if has_error:
        raise ValueError("; ".join(errors))
    if frequency_rad < 0 or dead_time < 0:
        raise ValueError("Frequency and dead time cannot be negative.")

    magnitude = abs(k_gain) / math.sqrt(1 + (frequency_rad * tau) ** 2)
    phase_rad = -math.atan(frequency_rad * tau) - frequency_rad * dead_time
    phase_deg = math.degrees(phase_rad)
    magnitude_db = 20 * math.log10(magnitude) if magnitude > 0 else float("-inf")

    warning = None
    if phase_deg <= -180:
        warning = (
            f"Phase angle ({phase_deg:.1f} deg) has reached or passed -180 degrees at this frequency - "
            "this is at or beyond the classical closed-loop phase-crossover point; check closed-loop stability "
            "margins carefully if this frequency is near the expected controller crossover."
        )

    return {
        "Magnitude |G(jw)|": round(magnitude, 4),
        "Magnitude (dB)": round(magnitude_db, 2),
        "Phase Angle (degrees)": round(phase_deg, 2),
        "_warnings": [warning] if warning else [],
    }


TOOL_BODE_POINT = ToolSpec(
    key="ic_003",
    title="Frequency Response (Bode Point) for FOPDT",
    category="Control Loop Analysis",
    description="Magnitude and phase angle of a first-order-plus-dead-time process at a single frequency.",
    inputs=[
        InputSpec("k_gain", "Process Gain (K)", default=2.0),
        InputSpec("tau", "Time Constant (tau)", default=10.0, min_value=0.001, unit="(time units)"),
        InputSpec("dead_time", "Dead Time (theta)", default=2.0, min_value=0.0, unit="(time units)"),
        InputSpec("frequency_rad", "Frequency (omega)", default=0.05, min_value=0.0, unit="(rad/time unit)"),
    ],
    compute=compute_bode_point,
    formula_md=(
        r"$$|G(j\omega)| = \dfrac{K}{\sqrt{1+(\omega\tau)^2}}, \quad "
        r"\angle G(j\omega) = -\arctan(\omega\tau) - \omega\theta \ \text{(dead-time phase lag)}$$"
    ),
    references=["Seborg, Edgar, Mellichamp & Doyle, Process Dynamics and Control", "Ogata, K., Modern Control Engineering"],
    assumptions=[
        "Single-frequency evaluation, not a full swept Bode plot - evaluate at several frequencies externally to trace out the full curve, or to find the phase/gain crossover frequencies.",
        "FOPDT model assumed - higher-order or nonlinear process dynamics will show different frequency response behavior.",
    ],
)


REGISTRY: dict[str, ToolSpec] = {
    TOOL_FOPDT.key: TOOL_FOPDT,
    TOOL_ZN_PID.key: TOOL_ZN_PID,
    TOOL_BODE_POINT.key: TOOL_BODE_POINT,
}
