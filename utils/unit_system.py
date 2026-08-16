"""
utils/unit_system.py
======================
Persistent, global SI <-> Imperial toggle backed by st.session_state.
Every tool page reads `get_unit_system()` and adjusts input labels,
default values, and units shown to the user accordingly. The underlying
`compute_*` functions always work in one fixed internal system (documented
per-function) — conversion happens only at the UI boundary, so calculation
logic never has to branch on unit system internally.

Usage in a page:
    from utils.unit_system import get_unit_system, render_unit_toggle, UNITS

    render_unit_toggle()  # renders the sidebar radio, once, at the top
    us = get_unit_system()  # "SI" or "Imperial"
    label = UNITS[us]["pressure"]  # e.g. "kPa" or "psi"
"""

import streamlit as st

SI = "SI"
IMPERIAL = "Imperial"

# Display units per system, per physical quantity. Extend as new tools
# need new quantity types — this is the single source of truth so a
# quantity's displayed unit never drifts between tools.
UNITS = {
    SI: {
        "pressure": "kPa",
        "pressure_abs": "kPa(a)",
        "temperature": "°C",
        "temperature_abs": "K",
        "flow_mass": "kg/hr",
        "flow_vol_liquid": "m³/hr",
        "flow_vol_gas": "Nm³/hr",
        "diameter": "mm",
        "length": "m",
        "density": "kg/m³",
        "viscosity": "cP",
        "velocity": "m/s",
        "power": "kW",
        "head": "m",
        "roughness": "mm",
    },
    IMPERIAL: {
        "pressure": "psi",
        "pressure_abs": "psia",
        "temperature": "°F",
        "temperature_abs": "°R",
        "flow_mass": "lb/hr",
        "flow_vol_liquid": "GPM",
        "flow_vol_gas": "SCFH",
        "diameter": "in (NPS)",
        "length": "ft",
        "density": "lb/ft³",
        "viscosity": "cP",
        "velocity": "ft/s",
        "power": "hp",
        "head": "ft",
        "roughness": "in",
    },
}

# Standard NPS (Nominal Pipe Size) schedule-40 internal diameters, inches.
# Used to populate pipe-size dropdowns under Imperial so users pick a real
# NPS designation instead of typing an arbitrary diameter.
NPS_SCHEDULE_40_ID_IN = {
    '1/2"': 0.622, '3/4"': 0.824, '1"': 1.049, '1.5"': 1.610,
    '2"': 2.067, '3"': 3.068, '4"': 4.026, '6"': 6.065,
    '8"': 7.981, '10"': 10.020, '12"': 11.938, '16"': 15.000,
}

# Equivalent metric DN pipe sizes (mm, approximate nominal bore).
DN_METRIC_ID_MM = {
    "DN15": 15.8, "DN20": 21.0, "DN25": 26.6, "DN40": 40.9,
    "DN50": 52.5, "DN80": 78.0, "DN100": 102.3, "DN150": 154.1,
    "DN200": 202.7, "DN250": 254.5, "DN300": 303.2, "DN400": 381.0,
}


def get_unit_system() -> str:
    """Returns the current global unit system, defaulting to SI on first load."""
    if "unit_system" not in st.session_state:
        st.session_state["unit_system"] = SI
    return st.session_state["unit_system"]


def render_unit_toggle() -> None:
    """
    Renders the persistent unit-system radio at the top of the sidebar.
    Call this once per page render (it's idempotent — session_state
    carries the choice across pages and reruns).
    """
    st.sidebar.markdown("### 🌐 Unit System")
    current = get_unit_system()
    choice = st.sidebar.radio(
        "Unit System", options=[SI, IMPERIAL], index=[SI, IMPERIAL].index(current),
        horizontal=True, label_visibility="collapsed", key="unit_system_radio",
    )
    st.session_state["unit_system"] = choice


# ---------------------------------------------------------------------
# Conversion helpers (SI <-> Imperial) for the quantities in UNITS above.
# Internal calculation functions should pick ONE fixed system (documented
# in their docstring) and the page layer converts at the boundary using
# these, rather than every compute_xxx() needing unit-system branches.
# ---------------------------------------------------------------------

def kpa_to_psi(kpa: float) -> float:
    return kpa * 0.145038

def psi_to_kpa(psi: float) -> float:
    return psi / 0.145038

def c_to_f(c: float) -> float:
    return c * 9 / 5 + 32

def f_to_c(f: float) -> float:
    return (f - 32) * 5 / 9

def kg_hr_to_lb_hr(kg_hr: float) -> float:
    return kg_hr * 2.20462

def lb_hr_to_kg_hr(lb_hr: float) -> float:
    return lb_hr / 2.20462

def m3hr_to_gpm(m3hr: float) -> float:
    return m3hr * 4.40287

def gpm_to_m3hr(gpm: float) -> float:
    return gpm / 4.40287

def mm_to_in(mm: float) -> float:
    return mm / 25.4

def in_to_mm(inch: float) -> float:
    return inch * 25.4

def m_to_ft(m: float) -> float:
    return m / 0.3048

def ft_to_m(ft: float) -> float:
    return ft * 0.3048

def kgm3_to_lbft3(kgm3: float) -> float:
    return kgm3 * 0.0624280

def lbft3_to_kgm3(lbft3: float) -> float:
    return lbft3 / 0.0624280
