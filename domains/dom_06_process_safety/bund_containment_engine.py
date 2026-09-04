"""
domains/dom_06_process_safety/bund_containment_engine.py
==========================================================
Phase 6D of the psv_safety_package upgrade (v10 track).
Secondary containment / bund sizing per API 650 practice & NFPA 30.
Pure compute(), zero Streamlit imports (Pattern A).

Live tools:
  ps_010  Tank Bund / Dike Capacity Sizing (NFPA 30 / 110% Rule)
"""

import math
from utils.tool_roadmap import ToolSpec, InputSpec
from utils.ui_components import check_positive, run_validators


def compute_bund_capacity(values: dict) -> dict:
    v_largest_m3 = values["v_largest_m3"]
    v_others_m3 = values["v_others_m3"]
    rainfall_mm = values["rainfall_mm"]
    bund_area_m2 = values["bund_area_m2"]
    wall_height_m = values["wall_height_m"]

    has_error, has_warning, errors, warnings = run_validators(
        check_positive(v_largest_m3, "Largest tank volume"),
        check_positive(bund_area_m2, "Bund footprint area"),
        check_positive(wall_height_m, "Wall height"),
    )
    if has_error:
        raise ValueError("; ".join(errors))

    v_rain_m3 = (rainfall_mm / 1000.0) * bund_area_m2
    v_required_110 = 1.10 * v_largest_m3
    v_required_100_plus = v_largest_m3 + v_others_m3
    v_required = max(v_required_110, v_required_100_plus) + v_rain_m3

    v_bund_geom = bund_area_m2 * wall_height_m

    extra_warnings = []
    if wall_height_m > 1.8:
        extra_warnings.append(
            "Wall height exceeds 1.8 m - operator access/firefighting-visibility guidance "
            "typically caps freestanding bund walls at this height; consider a stepped or "
            "larger-footprint design instead."
        )
    if v_bund_geom < v_required:
        extra_warnings.append(
            f"Bund geometric capacity ({v_bund_geom:.1f} m3) is LESS than required capacity "
            f"({v_required:.1f} m3) - increase footprint area or wall height."
        )

    return {
        "Rainfall Allowance (m3)": round(v_rain_m3, 2),
        "Required Capacity - 110% Rule (m3)": round(v_required_110 + v_rain_m3, 2),
        "Required Capacity - 100% + Others Rule (m3)": round(v_required_100_plus + v_rain_m3, 2),
        "Governing Required Capacity (m3)": round(v_required, 2),
        "Bund Geometric Capacity Provided (m3)": round(v_bund_geom, 2),
        "Adequate?": "YES" if v_bund_geom >= v_required else "NO - INCREASE SIZE",
        "_warnings": warnings + extra_warnings,
    }


TOOL_BUND_CAPACITY = ToolSpec(
    key="ps_010",
    title="Tank Bund / Dike Capacity Sizing (NFPA 30)",
    category="Secondary Containment",
    description="Governing bund/dike net capacity: 110% of largest tank vs. 100%+displaced volumes, plus rainfall allowance.",
    inputs=[
        InputSpec("v_largest_m3", "Largest Tank Volume", default=5000.0, min_value=1.0,
                   quantity_kind="volume", canonical_unit="m3"),
        InputSpec("v_others_m3", "Sum of Other Tanks' Displaced Volume", default=0.0, min_value=0.0,
                   quantity_kind="volume", canonical_unit="m3",
                   help="Displacement volume of all other tank shells within the bund below wall height."),
        InputSpec("rainfall_mm", "24-hr Storm Rainfall Depth", default=100.0, min_value=0.0,
                   quantity_kind="length", canonical_unit="mm"),
        InputSpec("bund_area_m2", "Bund Footprint Area", default=3500.0, min_value=1.0,
                   quantity_kind="area", canonical_unit="m2"),
        InputSpec("wall_height_m", "Bund Wall Height", default=1.5, min_value=0.3, max_value=3.0, step=0.1,
                   quantity_kind="length", canonical_unit="m",
                   help="Practical max ~1.8 m for firefighter access/visibility."),
    ],
    compute=compute_bund_capacity,
    formula_md=(
        r"$$V_{bund} \ge \max\big(1.10\,V_{largest},\; V_{largest}+V_{others}\big) + V_{rain}, "
        r"\quad V_{rain} = \dfrac{d_{rain}}{1000}\cdot A_{bund}$$"
    ),
    references=[
        "NFPA 30 - Flammable and Combustible Liquids Code (secondary containment sizing)",
        "API 650 - Welded Tanks for Oil Storage (bund/dike practice reference)",
    ],
    assumptions=[
        "Screening-level net-capacity check only - does not verify wall structural stress, "
        "liner permeability, or drainage valve arrangement.",
        "Rainfall allowance uses a single-storm depth input; local code may require a specific "
        "return-period design storm - confirm the governing regulatory value for the site.",
        "Displaced volume of other tanks assumed pre-computed by the user (shell volume below "
        "wall height) - not derived from tank geometry here.",
    ],
)


REGISTRY: dict[str, ToolSpec] = {
    TOOL_BUND_CAPACITY.key: TOOL_BUND_CAPACITY,
}
