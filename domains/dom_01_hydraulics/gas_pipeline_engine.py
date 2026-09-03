"""
domains/dom_01_hydraulics/gas_pipeline_engine.py
==================================================
Pattern A: pure Python, zero `st.*` calls. New in this release — closes a
confirmed gap in dom_01_hydraulics (previously no compressible gas
transmission correlation; the 9 live hy_* tools cover liquid dP, control
valves, NPSH, water hammer, orifice metering, pump/compressor BHP, and
erosional/minimum line-size checks only).

  hy_010    Gas Pipeline Capacity — Weymouth / Panhandle A / Panhandle B

Verification: hand-checked against the standard textbook case set
(D=12.09 in, L=100 mi, P1=1400 psia, P2=800 psia, G=0.6, Tf=520 R,
Z=0.85, E=1.0 — the reference case used throughout E. Shashi Menon,
"Gas Pipeline Hydraulics", CRC Press, Ch. 2). Computed results:
Weymouth 83.4 MMscfd, Panhandle A 110.2 MMscfd, Panhandle B 111.4
MMscfd — correctly reproduces the well-documented ordering (Weymouth
most conservative; Panhandle A/B predict materially higher capacity
for the same line, per GPSA Engineering Data Book and Menon Ch. 2).
Exact published numeric values were not independently re-confirmed
against the book text itself (not accessible in this environment) —
treat as screening-level until cross-checked against a second source
or vendor software for any capital-commitment use, per this suite's
standing validation policy.
"""

import math
from utils.tool_roadmap import ToolSpec, InputSpec
from utils.ui_components import check_positive, check_pressure_drop, run_validators


def compute_gas_pipeline_sizing(values: dict) -> dict:
    p1 = values["p1"]          # upstream pressure, psia
    p2 = values["p2"]          # downstream pressure, psia
    d = values["diameter"]     # pipe internal diameter, inches
    length = values["length"]  # pipe length, miles
    g = values["sg"]           # gas specific gravity (air = 1.0)
    tf = values["temperature"] # average flowing temperature, deg R
    z = values["z"]            # average gas compressibility factor
    eff = values["efficiency"] # pipeline efficiency factor, 0-1
    tb = values["tb"]          # base temperature, deg R
    pb = values["pb"]          # base pressure, psia

    has_error, has_warning, errors, warnings = run_validators(
        check_positive(d, "Diameter"), check_positive(length, "Length"),
        check_positive(g, "Specific gravity"), check_positive(tf, "Flowing temperature"),
        check_positive(z, "Compressibility factor Z"), check_positive(eff, "Efficiency"),
        check_pressure_drop(p1, p2, "pressure"),
    )
    if has_error:
        raise ValueError("; ".join(errors))
    if eff > 1.0:
        warnings.append("Efficiency factor > 1.0 is non-physical for E; typical range is 0.85-1.00.")

    dp2 = p1 ** 2 - p2 ** 2
    tb_pb = tb / pb

    # Weymouth (GPSA Engineering Data Book; Menon Eq. 2.30) — D^2.667 term
    # sits OUTSIDE the sqrt; a common transcription error puts it inside,
    # which silently understates Q by roughly an order of magnitude.
    q_weymouth = 433.5 * eff * tb_pb * math.sqrt(dp2 / (g * tf * length * z)) * d ** 2.667

    # Panhandle A (GPSA)
    q_panhandle_a = (
        435.87 * eff * tb_pb ** 1.0788
        * (dp2 / (g ** 0.8539 * tf * length * z)) ** 0.5394
        * d ** 2.6182
    )

    # Panhandle B (GPSA)
    q_panhandle_b = (
        737.0 * eff * tb_pb ** 1.02
        * (dp2 / (g ** 0.961 * tf * length * z)) ** 0.51
        * d ** 2.53
    )

    # Bare (uninsulated-line) gas velocity check at the downstream (lower-
    # pressure, higher-velocity) end, using the most conservative flow
    # (Weymouth) so the erosional check is on the safe side.
    area_ft2 = math.pi / 4.0 * (d / 12.0) ** 2
    q_ft3_s_at_p2 = (q_weymouth / 86400.0) * (pb / p2) * (tf / tb) * z  # scfd -> actual ft3/s at P2,Tf,Z
    velocity_fps = q_ft3_s_at_p2 / area_ft2 if area_ft2 > 0 else 0.0

    if velocity_fps > 60.0:
        warnings.append(
            f"Gas velocity at Weymouth-predicted flow ({velocity_fps:.1f} ft/s at P2) exceeds the "
            "common 50-60 ft/s erosional guideline — recheck against API RP 14E if this line carries entrained liquids/solids."
        )

    return {
        "Weymouth — Flow Capacity (MMscfd)": round(q_weymouth / 1e6, 2),
        "Panhandle A — Flow Capacity (MMscfd)": round(q_panhandle_a / 1e6, 2),
        "Panhandle B — Flow Capacity (MMscfd)": round(q_panhandle_b / 1e6, 2),
        "Spread (Panhandle A vs Weymouth, %)": round(
            (q_panhandle_a - q_weymouth) / q_weymouth * 100.0, 1
        ) if q_weymouth > 0 else None,
        "Gas Velocity at P2, Weymouth basis (ft/s)": round(velocity_fps, 1),
        "_warnings": warnings,
    }


TOOL_GAS_PIPELINE = ToolSpec(
    key="hy_010",
    title="Gas Pipeline Sizing — Weymouth / Panhandle A / Panhandle B",
    category="Piping Systems & Flow Measurement",
    description=(
        "Steady-state, isothermal compressible gas flow capacity for a transmission/gathering "
        "pipeline segment, computed by all three classical correlations side-by-side for comparison."
    ),
    inputs=[
        InputSpec("p1", "Upstream Pressure", default=1400.0, min_value=0.1, unit="(psia)"),
        InputSpec("p2", "Downstream Pressure", default=800.0, min_value=0.1, unit="(psia)"),
        InputSpec("diameter", "Pipe Internal Diameter", default=12.09, min_value=0.1, unit="(in)"),
        InputSpec("length", "Pipe Length", default=100.0, min_value=0.01, unit="(miles)"),
        InputSpec("sg", "Gas Specific Gravity (air = 1.0)", default=0.6, min_value=0.01, max_value=2.0),
        InputSpec("temperature", "Average Flowing Temperature", default=520.0, min_value=1.0, unit="(deg R)"),
        InputSpec("z", "Average Compressibility Factor, Z", default=0.85, min_value=0.01, max_value=1.5),
        InputSpec("efficiency", "Pipeline Efficiency Factor, E", default=1.0, min_value=0.1, max_value=1.0,
                   help="Typical 0.85-1.00; use GPSA/Menon default of 0.92 for older/unpigged lines."),
        InputSpec("tb", "Base Temperature", default=520.0, min_value=1.0, unit="(deg R)",
                   help="Standard-conditions reference temperature; 520 R = 60 deg F is the common US convention."),
        InputSpec("pb", "Base Pressure", default=14.73, min_value=0.1, unit="(psia)"),
    ],
    compute=compute_gas_pipeline_sizing,
    formula_md=(
        r"$$Q_{Weymouth} = 433.5\,E\,\frac{T_b}{P_b}\sqrt{\frac{P_1^2-P_2^2}{G\,T_f\,L\,Z}}\,D^{2.667}$$"
        r"$$Q_{PanhandleA} = 435.87\,E\left(\frac{T_b}{P_b}\right)^{1.0788}\left(\frac{P_1^2-P_2^2}{G^{0.8539}T_f L Z}\right)^{0.5394} D^{2.6182}$$"
        r"$$Q_{PanhandleB} = 737\,E\left(\frac{T_b}{P_b}\right)^{1.02}\left(\frac{P_1^2-P_2^2}{G^{0.961}T_f L Z}\right)^{0.51} D^{2.53}$$"
        "\n\nUS customary field units: Q in scfd, P in psia, D in inches, L in miles, T in deg R."
    ),
    references=[
        "GPSA Engineering Data Book, 13th Ed., Section 17 - Fluid Flow (Weymouth, Panhandle A, Panhandle B).",
        "E. Shashi Menon, Gas Pipeline Hydraulics, CRC Press, 2005, Ch. 2 (Eq. 2.30 Weymouth; Panhandle A/B forms).",
    ],
    assumptions=[
        "Steady-state, isothermal, single-phase (dry gas) flow — no elevation change term included.",
        "Fully turbulent flow assumed (all three correlations were developed for this regime; not valid at low Reynolds number).",
        "Weymouth is empirically known to be conservative (can understate capacity 8-12% vs. transmission-line field data); "
        "Panhandle A is best suited to large-diameter (>=10 in), long-distance lines; Panhandle B to high Reynolds-number "
        "(5-11 million) transmission lines. Use the AGA fully-turbulent or general flow equation with a numerically-solved "
        "friction factor for higher-rigor work — not yet implemented in this suite.",
        "Screening-level — cross-check against a second correlation or vendor simulation before capital-commitment sizing.",
    ],
)


REGISTRY_ADDITIONS: dict[str, ToolSpec] = {
    TOOL_GAS_PIPELINE.key: TOOL_GAS_PIPELINE,
}
