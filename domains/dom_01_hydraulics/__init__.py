"""domains/dom_01_hydraulics — Fluid Mechanics, Hydraulics & Piping Systems."""
from .fluid_dynamics_engine import REGISTRY as _BASE_REGISTRY
from .gas_pipeline_engine import REGISTRY_ADDITIONS as _GAS_PIPELINE_REGISTRY

# Merged rather than editing fluid_dynamics_engine.py directly, so the
# 9 previously hand-verified tools in that file stay untouched.
REGISTRY = {**_BASE_REGISTRY, **_GAS_PIPELINE_REGISTRY}

__all__ = ["REGISTRY"]
