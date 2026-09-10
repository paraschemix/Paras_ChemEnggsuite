"""
utils/unit_converter.py
=========================
Universal SI (Metric) <-> US Customary unit conversion engine, built on
`pint` (a mature, independently-tested unit library) rather than
hand-rolled conversion factors.

ARCHITECTURE NOTE (why this is safe to add without breaking the 40
existing verified tools): every domain engine's compute() function
keeps working in whatever "canonical" unit it was already verified
against (e.g. hy_001 takes SI values, hy_004 takes USGPM/ft). This
module converts between a user's CHOSEN DISPLAY unit and that tool's
existing canonical unit at the UI boundary only - it never changes what
a compute() function receives or how it does math. This means:
  - Zero risk of regressing any of the 40 already-verified calculations.
  - Retrofitting is additive and incremental: an InputSpec that doesn't
    opt in (no quantity_kind set) renders exactly as before.

QUANTITY_KINDS maps a short string key (used by InputSpec.quantity_kind)
to the list of user-selectable units and pint-compatible unit strings.
Add new quantity kinds here as more tools are retrofitted - no other
file needs to change to support a new kind, other than referencing it
from an InputSpec.
"""

import pint

_ureg = pint.UnitRegistry()
_ureg.default_format = "~P"

# ---------------------------------------------------------------------
# Custom unit definitions (v9 pitfalls fixed here, not with raw pint
# defaults - see file docstring / project memory for context):
#   - pint's built-in "mil" is an ANGULAR unit (1/6400 revolution,
#     dimensionless), not thousandths-of-an-inch. Defining a distinct
#     name avoids silently colliding with that built-in.
#   - pint's built-in "barrel" is US liquid barrel (119.24 L), not the
#     oilfield barrel (158.987 L) process engineers mean by "bbl".
#   - "1e6*Btu/hour" is not a valid pint unit expression on its own
#     (arithmetic-prefixed strings like this raise/misparse) - it needs
#     a proper named unit definition instead.
# ---------------------------------------------------------------------
_ureg.define("mil_thou = 0.001 * inch = mil_th")
_ureg.define("oil_bbl = 158.987 * liter = obbl")
_ureg.define("mmbtu_per_hour = 1e6 * Btu / hour = MMBtuh")

# ---------------------------------------------------------------------
# Quantity kind registry: kind_key -> { "options": [(label, pint_unit), ...] }
# `pint_unit` strings must be valid pint unit expressions.
# ---------------------------------------------------------------------
QUANTITY_KINDS = {
    "pressure": {
        # NOTE: psi and psia are mapped to the same underlying unit here.
        # This converter performs unit-of-measure conversion only (e.g.
        # psi <-> kPa <-> bar) - it does NOT perform gauge<->absolute
        # conversion, which requires knowing local atmospheric pressure.
        # If you need psig -> psia, add local atmospheric pressure (~14.7
        # psi at sea level) to the gauge value separately before/after
        # using this converter.
        "options": [
            ("psi", "psi"), ("psia", "psi"), ("kPa", "kPa"), ("bar", "bar"),
            ("atm", "atm"), ("kg/cm2", "kgf/cm**2"), ("mmHg", "mmHg"),
        ],
    },
    "temperature": {
        "options": [
            ("degF", "degF"), ("degC", "degC"), ("K", "kelvin"), ("degR", "degR"),
        ],
    },
    "length": {
        "options": [
            ("ft", "ft"), ("m", "meter"), ("in", "inch"), ("mm", "mm"), ("cm", "cm"),
        ],
    },
    "density": {
        "options": [
            ("lb/ft3", "lb/ft**3"), ("kg/m3", "kg/m**3"), ("g/cm3", "g/cm**3"),
        ],
    },
    "velocity": {
        "options": [
            ("ft/s", "ft/s"), ("m/s", "m/s"), ("ft/min", "ft/min"),
        ],
    },
    "viscosity_dynamic": {
        "options": [
            ("cP", "centipoise"), ("Pa.s", "pascal*second"), ("lb/ft-hr", "lb/(ft*hour)"),
        ],
    },
    "flow_volumetric": {
        "options": [
            ("USGPM", "gallon/minute"), ("m3/hr", "meter**3/hour"),
            ("L/min", "liter/minute"), ("ft3/s", "ft**3/second"),
        ],
    },
    "flow_mass": {
        "options": [
            ("lb/hr", "lb/hour"), ("kg/hr", "kg/hour"), ("lb/min", "lb/minute"),
        ],
    },
    "power_heat_duty": {
        "options": [
            ("Btu/hr", "Btu/hour"), ("kW", "kilowatt"), ("hp", "horsepower"),
            ("MMBtu/hr", "mmbtu_per_hour"),  # fixed: was invalid "1e6*Btu/hour" string
        ],
    },
    # -------------------------------------------------------------
    # v10 additions below
    # -------------------------------------------------------------
    "area": {
        "options": [
            ("m2", "meter**2"), ("ft2", "ft**2"), ("in2", "inch**2"), ("cm2", "cm**2"),
        ],
    },
    "volume": {
        "options": [
            ("m3", "meter**3"), ("ft3", "ft**3"), ("L", "liter"), ("USgal", "gallon"),
            ("oil_bbl", "oil_bbl"),
        ],
    },
    # Heat transfer datasheet quantities
    "heat_transfer_coeff": {
        "options": [
            ("W/m2-K", "watt/(meter**2*kelvin)"), ("Btu/hr-ft2-degF", "Btu/(hour*ft**2*degF)"),
        ],
    },
    "fouling_resistance": {
        "options": [
            ("m2-K/W", "meter**2*kelvin/watt"), ("hr-ft2-degF/Btu", "hour*ft**2*degF/Btu"),
        ],
    },
    "thermal_conductivity": {
        "options": [
            ("W/m-K", "watt/(meter*kelvin)"), ("Btu/hr-ft-degF", "Btu/(hour*ft*degF)"),
        ],
    },
    "heat_flux": {
        "options": [
            ("W/m2", "watt/meter**2"), ("Btu/hr-ft2", "Btu/(hour*ft**2)"),
        ],
    },
    # Thermodynamic properties
    "specific_heat": {
        "options": [
            ("kJ/kg-K", "kilojoule/(kg*kelvin)"), ("Btu/lb-degF", "Btu/(lb*degF)"),
        ],
    },
    "enthalpy_specific": {
        "options": [
            ("kJ/kg", "kilojoule/kg"), ("Btu/lb", "Btu/lb"), ("kcal/kg", "kilocalorie/kg"),
        ],
    },
    "molar_flow": {
        "options": [
            ("kmol/hr", "kmol/hour"), ("lbmol/hr", "lbmol/hour"), ("mol/s", "mol/second"),
        ],
    },
    # Fluid properties
    "viscosity_kinematic": {
        "options": [
            ("cSt", "mm**2/second"), ("m2/s", "meter**2/second"), ("ft2/s", "ft**2/second"),
        ],
    },
    "surface_tension": {
        "options": [
            ("N/m", "newton/meter"), ("dyn/cm", "dyne/cm"), ("lbf/ft", "lbf/ft"),
        ],
    },
    # Electrical
    "electrical_power": {
        "options": [
            ("kW", "kilowatt"), ("hp", "horsepower"), ("MW", "megawatt"),
        ],
    },
    "voltage": {
        "options": [
            ("V", "volt"), ("kV", "kilovolt"),
        ],
    },
    # Corrosion rate
    "corrosion_rate": {
        "options": [
            ("mm/yr", "mm/year"), ("mpy", "mil_thou/year"),  # mpy = mils per year, thousandths-of-inch (NOT angular mil)
        ],
    },
    # Piping pressure gradient
    "pressure_gradient": {
        "options": [
            ("kPa/m", "kPa/meter"), ("psi/ft", "psi/ft"), ("bar/100m", "bar/(100*meter)"),
        ],
    },
    # Oilfield barrels (flow and volume)
    "flow_oilfield": {
        "options": [
            ("bbl/day", "oil_bbl/day"), ("bbl/hr", "oil_bbl/hour"), ("m3/hr", "meter**3/hour"),
        ],
    },
    # Gas reference-condition volumetric flow functions:
    #   Normal   = 0 degC,  1 atm   (Nm3/hr)
    #   Standard-ISO = 15 degC, 1 atm  (Sm3/hr, ISO 13443)
    #   Standard-US  = 60 degF, 14.696 psia (SCFM/SCFH)
    # These are reference-condition-tagged volumetric flows, not a pure
    # unit conversion (they depend on the reference T/P convention used),
    # so they are exposed as dedicated helper functions below rather than
    # folded into QUANTITY_KINDS' simple linear-factor table.
}

# Gas reference conditions: (temperature_K, pressure_Pa)
GAS_REFERENCE_CONDITIONS = {
    "normal": {"label": "Normal (0°C, 1 atm)", "T_K": 273.15, "P_Pa": 101325.0},
    "standard_iso": {"label": "Standard-ISO (15°C, 1 atm)", "T_K": 288.15, "P_Pa": 101325.0},
    "standard_us": {"label": "Standard-US (60°F, 14.696 psia)", "T_K": 288.7056, "P_Pa": 101325.0},
}


def convert_gas_reference_flow(value: float, from_ref: str, to_ref: str) -> float:
    """Converts a volumetric gas flow reported at one reference condition
    (Nm3/hr, Sm3/hr-ISO, SCFM, etc.) to the equivalent flow at another
    reference condition, via the ideal gas law (same mass/mole flow):
        V2 = V1 * (P1/P2) * (T2/T1)
    Note this converts between reference CONVENTIONS only, at matching
    volumetric units (e.g. both in m3/hr, or both in ft3, on either
    side) - it does not itself change m3 to ft3; combine with the
    `volume`/`flow_volumetric` kinds above for that.
    """
    if from_ref == to_ref:
        return value
    ref1 = GAS_REFERENCE_CONDITIONS[from_ref]
    ref2 = GAS_REFERENCE_CONDITIONS[to_ref]
    return value * (ref1["P_Pa"] / ref2["P_Pa"]) * (ref2["T_K"] / ref1["T_K"])


def get_unit_options(quantity_kind: str) -> list[str]:
    """Returns the list of user-facing unit labels for a quantity kind."""
    kind = QUANTITY_KINDS.get(quantity_kind)
    if not kind:
        raise ValueError(f"Unknown quantity kind: {quantity_kind}")
    return [label for label, _ in kind["options"]]


def _pint_unit_for_label(quantity_kind: str, label: str) -> str:
    kind = QUANTITY_KINDS.get(quantity_kind)
    if not kind:
        raise ValueError(f"Unknown quantity kind: {quantity_kind}")
    for opt_label, pint_unit in kind["options"]:
        if opt_label == label:
            return pint_unit
    raise ValueError(f"Unknown unit label '{label}' for quantity kind '{quantity_kind}'")


def convert(value: float, quantity_kind: str, from_label: str, to_label: str) -> float:
    """
    Converts `value` from `from_label` to `to_label` within the given
    quantity_kind. Temperature conversions correctly handle the
    non-multiplicative (offset) nature of degF/degC/degR via pint's
    Quantity system rather than naive scaling.
    """
    if from_label == to_label:
        return value
    from_unit = _pint_unit_for_label(quantity_kind, from_label)
    to_unit = _pint_unit_for_label(quantity_kind, to_label)
    qty = _ureg.Quantity(value, from_unit)
    return qty.to(to_unit).magnitude


def convert_to_canonical(value: float, quantity_kind: str, display_label: str, canonical_label: str) -> float:
    """Convenience wrapper: converts a user-entered display value into
    the tool's canonical unit, ready to hand to a compute() function."""
    return convert(value, quantity_kind, display_label, canonical_label)
