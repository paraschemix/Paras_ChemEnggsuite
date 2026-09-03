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
            ("Btu/hr", "Btu/hour"), ("kW", "kilowatt"), ("hp", "horsepower"), ("MMBtu/hr", "1e6*Btu/hour"),
        ],
    },
}


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
