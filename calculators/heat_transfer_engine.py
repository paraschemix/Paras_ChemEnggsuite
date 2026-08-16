"""
calculators/heat_transfer_engine.py
======================================
Houses calculation logic for tools #151-225 (Heat Transfer domain):
LMTD/NTU-effectiveness heat exchanger rating, fouling factor tracking,
fired heater efficiency, steam/condensate balancing, etc.

Not yet populated — follows the identical pattern as
fluid_dynamics_engine.py.
"""

from calculators.registry_base import ToolSpec  # noqa: F401

REGISTRY: dict = {}
