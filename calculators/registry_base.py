"""
calculators/registry_base.py
==============================
Defines the Dynamic Dictionary-Registry pattern that lets the suite scale
to 500+ tools without 500+ hardcoded UI blocks.

Each calculation engine (fluid_dynamics_engine.py, distillation_engine.py,
...) builds a `REGISTRY: dict[str, ToolSpec]` mapping a unique tool key
to a ToolSpec describing:
  - its inputs (as declarative InputSpec objects, so a page can render
    st.number_input/st.selectbox for each one generically)
  - a `compute` function taking a dict of {input_name: value} and
    returning a dict of {result_label: value}
  - its formula/reference/assumption metadata for the standardized
    "📚 Engineering Basis & Limitations" expander
  - an optional `validate` function returning a list of ValidationResult

A page (e.g. pages/1_🌊_Fluid_Dynamics.py) then becomes a thin, generic
loader: it lists REGISTRY.keys() in a selectbox, renders inputs from
tool.inputs, calls tool.compute(values), and renders tool.formula_md /
tool.references / tool.assumptions via the shared styling helper. Adding
tool #501 never touches the page file — only the relevant engine module.
"""

from dataclasses import dataclass, field
from typing import Callable, Optional, Any


@dataclass
class InputSpec:
    name: str                      # dict key passed into compute()
    label: str                     # UI label
    default: float                 # default value shown in the widget
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    step: Optional[float] = None
    unit: str = ""                 # appended to label for display, e.g. "(psia)"
    help: str = ""                 # tooltip
    input_type: str = "number"     # "number" | "select"
    options: Optional[list] = None  # required if input_type == "select"

    def display_label(self) -> str:
        return f"{self.label} {self.unit}".strip() if self.unit else self.label


@dataclass
class ToolSpec:
    key: str                                   # unique registry key, e.g. "fd_001"
    title: str                                  # display name in search/selectbox
    category: str                               # sub-grouping within the domain page
    description: str                            # one-line summary shown under the title
    inputs: list[InputSpec]
    compute: Callable[[dict[str, Any]], dict[str, Any]]
    formula_md: str
    references: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    validate: Optional[Callable[[dict[str, Any]], list]] = None
    # validate(values) -> list[ValidationResult]; None means no extra checks
    # beyond whatever `compute` itself raises.
