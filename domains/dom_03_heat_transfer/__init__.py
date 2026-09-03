"""domains/dom_03_heat_transfer — Heat Transfer & Thermal Equipment.
LIVE this release: LMTD, Heat Exchanger Duty & Required Area, Insulation,
Air-Cooled Exchanger, Cooling Tower Merkel NTU, Cooling Water LSI/RSI."""
from .hx_engine import REGISTRY as _BASE_REGISTRY
from .cooling_tower_engine import REGISTRY_ADDITIONS as _COOLING_TOWER_REGISTRY

# Merged rather than editing hx_engine.py directly, so the 4 previously
# hand-verified tools in that file stay untouched.
REGISTRY = {**_BASE_REGISTRY, **_COOLING_TOWER_REGISTRY}

__all__ = ["REGISTRY"]
