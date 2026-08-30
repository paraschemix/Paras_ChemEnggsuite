"""domains/dom_12_environmental — Environmental & Energy.
LIVE this release: Flare Stack Thermal Radiation (API 521), Gaussian Plume Dispersion.
This domain previously had a partial content mapping (Clean Energy/
sustainability bullets only); populated per the v7 sprint spec (Flare
Radiation and Chimney/Vent Dispersion)."""
from .dispersion_engine import REGISTRY

__all__ = ["REGISTRY"]
