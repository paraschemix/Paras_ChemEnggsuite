"""
domains/dom_12_environmental/tank_emissions_engine.py
=======================================================
Pattern A: pure Python, zero `st.*` calls. New in this release — closes
the tank emission-loss gap flagged in v9 planning (checalc taxonomy
cross-check; no prior tool in this suite covers VOC losses from
atmospheric storage tanks).

  en_003    Fixed-Roof Tank VOC Emissions — Standing + Working Loss (AP-42 Ch.7.1)

Scope note: this implements the WIDELY-PUBLISHED SIMPLIFIED method (the
same scope as most online AP-42 screening calculators and the checalc
reference tool that prompted this addition) — standing (breathing) loss
via Eq. 1-2/1-3/1-5 and working loss via the standard Vq*Kn*Kp*Wv*Kb
form. It does NOT implement: paint-condition/solar-absorptance lookup
tables, the full meteorological (degree-day) daily temperature range
correlations, floating-roof rim-seal losses, or flashing losses from
crude/condensate tanks. Those require chart/table lookups (AP-42
Figures 7.1-7 through 7.1-18) rather than a closed-form equation, same
design tradeoff already made for en_001/en_002's F and sigma_y/sigma_z
inputs in this domain.

Verification: KS, KE, and the combined LS form were cross-checked
directly against EPA's AP-42 Ch.7.1 source PDF (Eq. 1-2, 1-3, 1-5;
gaftp.epa.gov/ap42/ch07/s01/final/c07s01.pdf) during this session. The
worked numeric example below was NOT cross-checked against an official
EPA worked example (not accessible in this environment) - treat this
tool as screening-level per this suite's standing validation policy,
and cross-check against EPA's own TANKS software or a consultant's
calc before using results for permitting or fee-basis submissions.
"""

import math
from utils.tool_roadmap import ToolSpec, InputSpec
from utils.ui_components import check_positive, run_validators


R_GAS = 10.731  # psia.ft3 / (lb-mol.R)


def compute_tank_emissions(values: dict) -> dict:
    d = values["diameter"]              # tank diameter, ft
    h_vo = values["vapor_space_height"]  # vapor space outage, ft
    mv = values["mol_weight_vapor"]      # vapor molecular weight, lb/lb-mol
    p_va = values["vapor_pressure_avg"]  # vapor pressure at daily avg liquid surface temp, psia
    t_la = values["liquid_temp_avg"]     # daily average liquid surface temperature, deg R
    delta_tv = values["delta_tv"]        # daily vapor space temperature range, deg R
    delta_pv = values["delta_pv"]        # daily vapor pressure range, psi
    p_a = values["atm_pressure"]         # atmospheric pressure, psia
    breather_setting = values["breather_vent_setting"]  # +/- pressure/vacuum vent setting, psig (single value, symmetric)
    annual_throughput_bbl = values["annual_throughput_bbl"]  # net annual throughput, bbl/yr
    turnovers = values["turnovers_per_year"]
    kp = values["product_factor_kp"]     # 0.75 crude oil, 1.0 all other organic liquids

    has_error, has_warning, errors, warnings = run_validators(
        check_positive(d, "Tank diameter"), check_positive(h_vo, "Vapor space outage"),
        check_positive(mv, "Vapor molecular weight"), check_positive(p_va, "Vapor pressure"),
        check_positive(t_la, "Liquid surface temperature"), check_positive(p_a, "Atmospheric pressure"),
        check_positive(kp, "Product factor Kp"),
    )
    if has_error:
        raise ValueError("; ".join(errors))
    if p_va >= p_a:
        errors.append("Vapor pressure must be below atmospheric pressure for this method to apply (non-boiling stock).")
        raise ValueError("; ".join(errors))

    # --- Standing (breathing) loss: AP-42 Eq. 1-2 / 1-3 / 1-5 ---
    vv = (math.pi / 4.0) * d ** 2 * h_vo                       # vapor space volume, ft3
    wv = (mv * p_va) / (R_GAS * t_la)                          # vapor density, lb/ft3 (ideal gas)
    delta_pb = 2.0 * breather_setting                          # breather vent range = +setting to -setting
    ke = (delta_tv / t_la) + ((delta_pv - delta_pb) / (p_a - p_va))
    if ke <= 0:
        warnings.append(
            "Vapor space expansion factor Ke <= 0: standing (breathing) losses are not predicted to occur "
            "under these conditions (tight breather vent relative to daily T/P swing)."
        )
        ke_used = 0.0
    else:
        ke_used = ke
    ks = 1.0 / (1.0 + 0.053 * p_va * h_vo)                      # vented vapor saturation factor

    l_s = 365.0 * vv * wv * ke_used * ks                        # lb/yr

    # --- Working loss: standard simplified form ---
    v_q = annual_throughput_bbl * 5.614583                      # bbl/yr -> ft3/yr
    if turnovers <= 36.0:
        kn = 1.0
    else:
        kn = (180.0 + turnovers) / (6.0 * turnovers)
    kb = 1.0  # vented vapor saturation factor for working loss; 1.0 unless vapor recovery/high fill-rate correction applies
    l_w = v_q * kn * kp * wv * kb                                # lb/yr

    l_total = l_s + l_w

    if h_vo > 0 and p_va * h_vo > 10:
        warnings.append("Ks correlation (Eq. 1-5) is documented as reliable mainly for Pva*Hvo < ~1; check against Figure-based Ks if this stock is highly volatile.")

    return {
        "Vapor Space Volume, Vv (ft3)": round(vv, 1),
        "Vapor Density, Wv (lb/ft3)": round(wv, 5),
        "Vapor Space Expansion Factor, Ke": round(ke, 4),
        "Vented Vapor Saturation Factor, Ks": round(ks, 4),
        "Standing (Breathing) Loss (lb/yr)": round(l_s, 1),
        "Working Loss (lb/yr)": round(l_w, 1),
        "Total VOC Emissions (lb/yr)": round(l_total, 1),
        "Total VOC Emissions (ton/yr)": round(l_total / 2000.0, 3),
        "_warnings": warnings,
    }


TOOL_TANK_EMISSIONS = ToolSpec(
    key="en_003",
    title="Fixed-Roof Tank VOC Emissions (AP-42 Ch.7.1 Standing + Working Loss)",
    category="Air Emissions & Permitting",
    description=(
        "Annual standing (breathing) and working VOC loss estimate for a vertical, "
        "cylindrical, fixed-roof atmospheric storage tank."
    ),
    inputs=[
        InputSpec("diameter", "Tank Diameter", default=30.0, min_value=0.1, unit="(ft)"),
        InputSpec("vapor_space_height", "Vapor Space Outage, Hvo", default=6.0, min_value=0.01, unit="(ft)",
                   help="Height from liquid surface to roof (or to the mid-height of a cone/dome roof)."),
        InputSpec("mol_weight_vapor", "Vapor Molecular Weight, Mv", default=68.0, min_value=1.0, unit="(lb/lb-mol)",
                   help="e.g. ~68 for typical gasoline/naphtha vapor; use stock-specific value from lab data if available."),
        InputSpec("vapor_pressure_avg", "True Vapor Pressure at Avg. Liquid Temp, Pva", default=5.0, min_value=0.001, max_value=14.0, unit="(psia)"),
        InputSpec("liquid_temp_avg", "Avg. Daily Liquid Surface Temperature, Tla", default=520.0, min_value=1.0, unit="(deg R)"),
        InputSpec("delta_tv", "Daily Vapor Space Temperature Range, dTv", default=20.0, min_value=0.0, unit="(deg R)",
                   help="Typically ~1.2x the daily ambient temperature range for an uninsulated, non-white tank; use Figure 7.1-17 method for rigor."),
        InputSpec("delta_pv", "Daily Vapor Pressure Range, dPv", default=0.5, min_value=0.0, unit="(psi)"),
        InputSpec("atm_pressure", "Atmospheric Pressure, Pa", default=14.7, min_value=1.0, unit="(psia)"),
        InputSpec("breather_vent_setting", "Breather Vent Setting (+/-)", default=0.03, min_value=0.0, unit="(psig)",
                   help="Typical conservation vent setting is +/-0.03 psig if not otherwise specified."),
        InputSpec("annual_throughput_bbl", "Annual Net Throughput", default=100000.0, min_value=0.0, unit="(bbl/yr)"),
        InputSpec("turnovers_per_year", "Annual Turnovers", default=12.0, min_value=0.1),
        InputSpec("product_factor_kp", "Working Loss Product Factor, Kp", default=1.0, min_value=0.1, max_value=1.0,
                   help="0.75 for crude oils; 1.0 for all other organic liquids per AP-42."),
    ],
    compute=compute_tank_emissions,
    formula_md=(
        r"$$L_S = 365\,V_V\,W_V\,K_E\,K_S,\quad V_V=\frac{\pi}{4}D^2 H_{VO},\quad W_V=\frac{M_V P_{VA}}{R\,T_{LA}}$$"
        r"$$K_E=\frac{\Delta T_V}{T_{LA}}+\frac{\Delta P_V-\Delta P_B}{P_A-P_{VA}},\qquad K_S=\frac{1}{1+0.053\,P_{VA}\,H_{VO}}$$"
        r"$$L_W = V_Q\,K_N\,K_P\,W_V\,K_B$$"
    ),
    references=[
        "US EPA AP-42, Chapter 7.1 - Organic Liquid Storage Tanks (Eq. 1-2, 1-3, 1-5; gaftp.epa.gov/ap42/ch07/s01/final/c07s01.pdf).",
    ],
    assumptions=[
        "Vertical, cylindrical, fixed-roof tank at approximately atmospheric pressure; substantially liquid- and vapor-tight.",
        "Simplified/screening-level method: does not use AP-42's paint-condition/solar-absorptance lookup tables or the full "
        "meteorological daily-temperature-range correlation for dTv/dTa - both are taken as direct inputs here.",
        "Not valid for boiling stocks, unstable hydrocarbons, tanks with gas injection, or floating-roof rim-seal losses.",
        "Ks correlation (Eq. 1-5 form) is most reliable for Pva*Hvo well under ~10; flagged automatically if exceeded.",
        "Cross-check against EPA's TANKS program or a second method before using for permitting, fee-basis, or compliance submissions.",
    ],
)


REGISTRY_ADDITIONS: dict[str, ToolSpec] = {
    TOOL_TANK_EMISSIONS.key: TOOL_TANK_EMISSIONS,
}
