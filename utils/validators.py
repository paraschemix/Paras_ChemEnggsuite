"""
utils/validators.py
=====================
Physical-limit input validation shared across all calculation modules.
Every calculator should route its inputs through these functions before
running the underlying engineering math, so that obviously unphysical
inputs (negative absolute pressure, sub-absolute-zero temperature, etc.)
are caught with a clear UI warning instead of producing silently wrong
(or NaN/complex) results.

Each validator returns a tuple: (is_valid: bool, message: str | None)
`message` is None when valid, or a human-readable warning/error string
when invalid. Callers decide whether to treat a failed check as a hard
stop (st.error, block calculation) or soft warning (st.warning, allow
calculation to proceed) - see `severity` below.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ValidationResult:
    is_valid: bool
    severity: str  # "error" | "warning"
    message: Optional[str] = None


def check_absolute_temperature_R(t_rankine: float) -> ValidationResult:
    if t_rankine <= 0:
        return ValidationResult(False, "error", "Temperature must be above absolute zero (0 °R).")
    if t_rankine < 300:
        return ValidationResult(True, "warning", f"T = {t_rankine:.1f} °R is unusually low for typical process conditions — confirm units (°R vs °F).")
    return ValidationResult(True, "warning", None)


def check_absolute_temperature_K(t_kelvin: float) -> ValidationResult:
    if t_kelvin <= 0:
        return ValidationResult(False, "error", "Temperature must be above absolute zero (0 K).")
    if t_kelvin < 150:
        return ValidationResult(True, "warning", f"T = {t_kelvin:.1f} K is unusually low for typical process conditions — confirm units.")
    return ValidationResult(True, "warning", None)


def check_absolute_pressure_psia(p_psia: float) -> ValidationResult:
    if p_psia <= 0:
        return ValidationResult(False, "error", "Absolute pressure must be greater than 0 psia — check for a psig/psia mix-up.")
    return ValidationResult(True, "warning", None)


def check_pressure_drop(p1: float, p2: float, label: str = "pressure") -> ValidationResult:
    if p2 >= p1:
        return ValidationResult(False, "error", f"Downstream {label} ({p2}) must be less than upstream {label} ({p1}) for flow to occur in this direction.")
    return ValidationResult(True, "warning", None)


def check_positive(value: float, name: str) -> ValidationResult:
    if value <= 0:
        return ValidationResult(False, "error", f"{name} must be greater than zero (got {value}).")
    return ValidationResult(True, "warning", None)


def check_non_negative(value: float, name: str) -> ValidationResult:
    if value < 0:
        return ValidationResult(False, "error", f"{name} cannot be negative (got {value}).")
    return ValidationResult(True, "warning", None)


def check_fraction_0_1(value: float, name: str) -> ValidationResult:
    if not (0 <= value <= 1):
        return ValidationResult(False, "error", f"{name} must be between 0 and 1 (got {value}).")
    return ValidationResult(True, "warning", None)


def check_efficiency(value: float, name: str = "Efficiency") -> ValidationResult:
    if not (0 < value <= 1):
        return ValidationResult(False, "error", f"{name} must be between 0 (exclusive) and 1 (inclusive) — enter as a fraction, not a percentage.")
    if value < 0.2:
        return ValidationResult(True, "warning", f"{name} = {value:.2f} is unusually low — confirm this is a fraction (e.g. 0.75), not a percentage (e.g. 75).")
    return ValidationResult(True, "warning", None)


def check_velocity_sanity(v: float, unit: str = "ft/s", max_reasonable: float = 400.0) -> ValidationResult:
    if v < 0:
        return ValidationResult(False, "error", f"Velocity cannot be negative (got {v} {unit}).")
    if v > max_reasonable:
        return ValidationResult(True, "warning", f"Velocity of {v} {unit} is unusually high for typical process piping — verify inputs (flow rate / diameter units).")
    return ValidationResult(True, "warning", None)


def check_reynolds_regime(re: float) -> str:
    """Returns a human label for flow regime, no validation failure possible."""
    if re < 2300:
        return "Laminar"
    elif re < 4000:
        return "Transitional"
    return "Turbulent"


def check_specific_gravity(sg: float) -> ValidationResult:
    if sg <= 0:
        return ValidationResult(False, "error", f"Specific gravity must be positive (got {sg}).")
    if sg > 3.0:
        return ValidationResult(True, "warning", f"SG = {sg} is unusually high for typical process fluids — confirm this isn't a density value entered by mistake.")
    return ValidationResult(True, "warning", None)


def run_validators(*results: ValidationResult):
    """
    Aggregates multiple ValidationResult objects. Returns (has_error, has_warning,
    error_messages, warning_messages) so a calling page can decide whether to
    block the calculation (any error) while still surfacing all warnings.
    """
    errors = [r.message for r in results if not r.is_valid and r.message]
    warnings = [r.message for r in results if r.is_valid and r.severity == "warning" and r.message]
    has_error = len(errors) > 0
    has_warning = len(warnings) > 0
    return has_error, has_warning, errors, warnings
