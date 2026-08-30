"""
domains/dom_08_solids_handling/particle_engine.py
====================================================
Domain 8: Particle Technology & Bulk Solid Handling. Pure Python
physics, zero Streamlit calls.

Live tools:
  sh_001  Terminal Settling Velocity (Stokes' Law)
  sh_002  Minimum Fluidization Velocity (Wen & Yu correlation)
"""

import math
from utils.tool_roadmap import ToolSpec, InputSpec
from utils.ui_components import check_positive, run_validators


# =======================================================================
# TOOL: TERMINAL SETTLING VELOCITY (STOKES' LAW)
# =======================================================================

def compute_stokes_settling(values: dict) -> dict:
    """
    Vt = g*d^2*(rho_p - rho_f) / (18*mu)   [SI units]
    Valid strictly for Re < 1 (Stokes/laminar regime) - flags when the
    computed Re falls outside this range rather than silently returning
    an invalid result.
    """
    g = 9.81
    d_m = values["particle_diameter_um"] * 1e-6
    rho_p = values["particle_density"]
    rho_f = values["fluid_density"]
    mu = values["fluid_viscosity_pas"]

    has_error, has_warning, errors, warnings = run_validators(
        check_positive(d_m, "Particle diameter"), check_positive(rho_p, "Particle density"),
        check_positive(rho_f, "Fluid density"), check_positive(mu, "Fluid viscosity"),
    )
    if has_error:
        raise ValueError("; ".join(errors))
    if rho_p <= rho_f:
        raise ValueError("Particle density must exceed fluid density for the particle to settle (otherwise it floats/is neutrally buoyant).")

    vt = g * d_m ** 2 * (rho_p - rho_f) / (18 * mu)
    re = rho_f * vt * d_m / mu

    regime_warning = None
    if re > 1.0:
        regime_warning = (
            f"Particle Reynolds number = {re:.2f} exceeds 1.0 - Stokes' law is not strictly valid here "
            "(true settling velocity will be lower than this Stokes estimate). Use the intermediate "
            "(Allen) or Newton's law regime correlation instead for Re > 1."
        )

    return {
        "Terminal Velocity (m/s)": round(vt, 6),
        "Terminal Velocity (mm/s)": round(vt * 1000, 3),
        "Particle Reynolds Number": round(re, 4),
        "_warnings": warnings + ([regime_warning] if regime_warning else []),
    }


TOOL_STOKES = ToolSpec(
    key="sh_001",
    title="Terminal Settling Velocity (Stokes' Law)",
    category="Particle Characterization & Sizing",
    description="Terminal settling velocity of a spherical particle in a fluid, with a Stokes-regime validity check.",
    inputs=[
        InputSpec("particle_diameter_um", "Particle Diameter", default=100.0, min_value=0.1, unit="(microns)"),
        InputSpec("particle_density", "Particle Density", default=2500.0, min_value=1.0, unit="(kg/m3)"),
        InputSpec("fluid_density", "Fluid Density", default=1000.0, min_value=0.01, unit="(kg/m3)"),
        InputSpec("fluid_viscosity_pas", "Fluid Viscosity", default=0.001, min_value=1e-6, unit="(Pa.s)"),
    ],
    compute=compute_stokes_settling,
    formula_md=r"$$V_t = \dfrac{g\,d^2(\rho_p-\rho_f)}{18\mu}, \quad \text{valid for } Re = \dfrac{\rho_f V_t d}{\mu} < 1$$",
    references=["Stokes, G.G. (1851), Trans. Cambridge Phil. Soc.", "Perry's Chemical Engineers' Handbook, Section 6 - Fluid and Particle Dynamics"],
    assumptions=[
        "Spherical particle assumed - irregular particle shapes require a shape/sphericity correction factor.",
        "Strictly valid only for particle Reynolds number < 1 (creeping flow) - the tool flags but does not block calculation outside this range.",
        "Dilute suspension assumed (no hindered settling from particle-particle interaction).",
    ],
)


# =======================================================================
# TOOL: MINIMUM FLUIDIZATION VELOCITY (WEN & YU CORRELATION)
# =======================================================================

def compute_minimum_fluidization_velocity(values: dict) -> dict:
    """
    Wen & Yu (1966) correlation:
      Ar = d_p^3 * rho_f * (rho_p - rho_f) * g / mu^2
      Re_mf = sqrt(33.7^2 + 0.0408*Ar) - 33.7
      u_mf = Re_mf * mu / (rho_f * d_p)
    """
    g = 9.81
    d_p_m = values["particle_diameter_um"] * 1e-6
    rho_p = values["particle_density"]
    rho_f = values["fluid_density"]
    mu = values["fluid_viscosity_pas"]

    has_error, has_warning, errors, warnings = run_validators(
        check_positive(d_p_m, "Particle diameter"), check_positive(rho_p, "Particle density"),
        check_positive(rho_f, "Fluid density"), check_positive(mu, "Fluid viscosity"),
    )
    if has_error:
        raise ValueError("; ".join(errors))
    if rho_p <= rho_f:
        raise ValueError("Particle density must exceed fluid density.")

    ar = d_p_m ** 3 * rho_f * (rho_p - rho_f) * g / mu ** 2
    re_mf = math.sqrt(33.7 ** 2 + 0.0408 * ar) - 33.7
    u_mf = re_mf * mu / (rho_f * d_p_m)

    return {
        "Archimedes Number (Ar)": round(ar, 2),
        "Reynolds Number at Min. Fluidization": round(re_mf, 4),
        "Minimum Fluidization Velocity (m/s)": round(u_mf, 5),
        "Minimum Fluidization Velocity (cm/s)": round(u_mf * 100, 3),
        "_warnings": warnings,
    }


TOOL_MIN_FLUIDIZATION = ToolSpec(
    key="sh_002",
    title="Minimum Fluidization Velocity (Wen & Yu)",
    category="Fluidization & Conveying",
    description="Superficial gas velocity at which a packed bed of particles begins to fluidize.",
    inputs=[
        InputSpec("particle_diameter_um", "Particle Diameter", default=200.0, min_value=1.0, unit="(microns)"),
        InputSpec("particle_density", "Particle Density", default=2500.0, min_value=1.0, unit="(kg/m3)"),
        InputSpec("fluid_density", "Fluid (Gas) Density", default=1.2, min_value=0.001, unit="(kg/m3)",
                   help="Air at ambient conditions: ~1.2 kg/m3."),
        InputSpec("fluid_viscosity_pas", "Fluid (Gas) Viscosity", default=1.8e-5, min_value=1e-7, unit="(Pa.s)",
                   help="Air at ambient conditions: ~1.8e-5 Pa.s."),
    ],
    compute=compute_minimum_fluidization_velocity,
    formula_md=(
        r"$$Ar = \dfrac{d_p^3\rho_f(\rho_p-\rho_f)g}{\mu^2}, \quad "
        r"Re_{mf} = \sqrt{33.7^2+0.0408\,Ar}-33.7, \quad u_{mf} = \dfrac{Re_{mf}\,\mu}{\rho_f d_p}$$"
    ),
    references=["Wen, C.Y. & Yu, Y.H. (1966), AIChE Journal", "Kunii, D. & Levenspiel, O., Fluidization Engineering"],
    assumptions=[
        "Wen & Yu correlation is a widely-used general-purpose fit - for a specific particle system, an experimentally measured umf is more reliable.",
        "Assumes spherical particles and a narrow size distribution - broad particle size distributions fluidize over a range rather than at a single sharp velocity.",
    ],
)


REGISTRY: dict[str, ToolSpec] = {
    TOOL_STOKES.key: TOOL_STOKES,
    TOOL_MIN_FLUIDIZATION.key: TOOL_MIN_FLUIDIZATION,
}
