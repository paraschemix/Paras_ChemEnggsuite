"""
calculators package
=====================
Backend calculation logic for the PetroProcess Suite, organized into one
engine module per domain (fluid_dynamics_engine.py, distillation_engine.py,
etc.), each housing ~75 calculation tools as the suite scales to 500+.

Each engine module exposes a `REGISTRY` dictionary mapping a unique tool
key to a ToolSpec (see calculators/registry_base.py) — this is the core
pattern that lets pages/*.py stay tiny "dynamic loaders" instead of
500+ hardcoded if/else blocks.
"""
