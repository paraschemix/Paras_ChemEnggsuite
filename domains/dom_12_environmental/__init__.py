"""domains/dom_12_environmental — Environmental & Energy.
LIVE this release: Flare Stack Thermal Radiation (API 521), Gaussian Plume Dispersion,
Fixed-Roof Tank VOC Emissions (AP-42 Ch.7.1 standing + working loss).
This domain previously had a partial content mapping (Clean Energy/
sustainability bullets only); populated per the v7 sprint spec (Flare
Radiation and Chimney/Vent Dispersion), extended this release with tank emissions."""
from .dispersion_engine import REGISTRY as _BASE_REGISTRY
from .tank_emissions_engine import REGISTRY_ADDITIONS as _TANK_REGISTRY

# Merged rather than editing dispersion_engine.py directly, so the 2
# previously hand-verified tools in that file stay untouched.
REGISTRY = {**_BASE_REGISTRY, **_TANK_REGISTRY}

__all__ = ["REGISTRY"]
