"""
domains/dom_11_economics/economics_engine.py
===============================================
Domain 11: Process Economics, Costing & Optimization. Pure Python
math, zero Streamlit calls.

Live tools:
  ec_001  CEPCI Cost Escalation
  ec_002  Capacity Exponent Scaling
  ec_003  Net Present Value (NPV)
"""

from utils.tool_roadmap import ToolSpec, InputSpec
from utils.ui_components import check_positive, run_validators


# =======================================================================
# TOOL: CEPCI COST ESCALATION
# =======================================================================

def compute_cepci_escalation(values: dict) -> dict:
    cost_old = values["cost_old"]
    cepci_old = values["cepci_old"]
    cepci_new = values["cepci_new"]

    has_error, has_warning, errors, warnings = run_validators(
        check_positive(cost_old, "Original cost"), check_positive(cepci_old, "Original CEPCI"),
        check_positive(cepci_new, "New CEPCI"),
    )
    if has_error:
        raise ValueError("; ".join(errors))

    cost_new = cost_old * (cepci_new / cepci_old)
    escalation_pct = (cost_new / cost_old - 1) * 100

    return {
        "Escalated Cost": round(cost_new, 2),
        "Escalation (%)": round(escalation_pct, 2),
        "_warnings": warnings,
    }


TOOL_CEPCI = ToolSpec(
    key="ec_001",
    title="CEPCI Cost Escalation",
    category="Capital Cost Estimation (CAPEX)",
    description="Escalates a historical equipment/plant cost to current dollars using the Chemical Engineering Plant Cost Index.",
    inputs=[
        InputSpec("cost_old", "Original Cost", default=100000.0, min_value=0.01),
        InputSpec("cepci_old", "CEPCI at Original Cost Date", default=550.0, min_value=1.0,
                   help="Look up the published CEPCI value for the year/month of the original cost estimate."),
        InputSpec("cepci_new", "CEPCI at Target (Current) Date", default=800.0, min_value=1.0),
    ],
    compute=compute_cepci_escalation,
    formula_md=r"$$C_{new} = C_{old} \times \dfrac{CEPCI_{new}}{CEPCI_{old}}$$",
    references=["Chemical Engineering magazine - Plant Cost Index (published monthly)", "Peters, Timmerhaus & West, Plant Design and Economics for Chemical Engineers"],
    assumptions=[
        "Assumes cost escalation tracks the overall CEPCI - actual equipment-specific escalation can differ, especially over long time spans or during material-specific price shocks.",
        "Does not account for location factors, currency effects, or scale changes - use the Capacity Exponent tool separately for scale changes.",
    ],
)


# =======================================================================
# TOOL: CAPACITY EXPONENT SCALING
# =======================================================================

def compute_capacity_scaling(values: dict) -> dict:
    cost_b = values["cost_b"]
    size_b = values["size_b"]
    size_a = values["size_a"]
    n_exponent = values["n_exponent"]

    has_error, has_warning, errors, warnings = run_validators(
        check_positive(cost_b, "Known cost"), check_positive(size_b, "Known size"), check_positive(size_a, "Target size"),
    )
    if has_error:
        raise ValueError("; ".join(errors))

    cost_a = cost_b * (size_a / size_b) ** n_exponent
    scale_ratio = size_a / size_b

    extra_warning = None
    if scale_ratio > 10 or scale_ratio < 0.1:
        extra_warning = (
            f"Scale ratio ({scale_ratio:.2f}x) is well outside the typical 0.1x-10x range where a "
            "single capacity exponent is reliable - large extrapolations can introduce significant error."
        )

    return {
        "Scale Ratio": round(scale_ratio, 3),
        "Estimated Cost at Target Size": round(cost_a, 2),
        "_warnings": [extra_warning] if extra_warning else [],
    }


TOOL_CAPACITY_SCALING = ToolSpec(
    key="ec_002",
    title="Capacity Exponent Scaling",
    category="Capital Cost Estimation (CAPEX)",
    description="Scales a known equipment/plant cost to a different capacity using the six-tenths (or custom) rule.",
    inputs=[
        InputSpec("cost_b", "Known Cost (at Size B)", default=1000000.0, min_value=0.01),
        InputSpec("size_b", "Known Size (B)", default=1000.0, min_value=0.001),
        InputSpec("size_a", "Target Size (A)", default=2000.0, min_value=0.001),
        InputSpec("n_exponent", "Capacity Exponent (n)", default=0.6, min_value=0.1, max_value=1.2, step=0.01,
                   help="0.6 is the classic 'six-tenths rule' default for many process equipment types; use equipment-specific published exponents where available."),
    ],
    compute=compute_capacity_scaling,
    formula_md=r"$$C_A = C_B\left(\dfrac{S_A}{S_B}\right)^n$$",
    references=["Peters, Timmerhaus & West, Plant Design and Economics for Chemical Engineers", "Williams, R. (1947), Chem. Eng. - origin of the six-tenths rule"],
    assumptions=[
        "Single capacity exponent assumed constant across the scale range - reliable roughly within 0.1x-10x of the known size; large extrapolations are flagged but not blocked.",
        "Does not include time-based cost escalation - combine with the CEPCI tool if the known cost is also from a different time period.",
    ],
)


# =======================================================================
# TOOL: NET PRESENT VALUE (NPV)
# =======================================================================

def compute_npv(values: dict) -> dict:
    cash_flows_str = values["cash_flows"]
    discount_rate = values["discount_rate"]

    try:
        cash_flows = [float(x.strip()) for x in cash_flows_str.split(",") if x.strip()]
    except ValueError:
        raise ValueError("Cash flows must be a comma-separated list of numbers (e.g. -1000, 300, 300, 300).")

    if len(cash_flows) < 2:
        raise ValueError("Provide at least two cash flows (e.g. an initial investment and at least one return period).")
    if discount_rate <= -1:
        raise ValueError("Discount rate must be greater than -100%.")

    npv = sum(cf / (1 + discount_rate) ** t for t, cf in enumerate(cash_flows))

    warning = None
    if cash_flows[0] > 0:
        warning = "The first cash flow (period 0) is positive - typically period 0 represents the initial investment and is negative. Confirm this is intentional."

    return {
        "Number of Periods": len(cash_flows) - 1,
        "Net Present Value (NPV)": round(npv, 2),
        "Decision": "NPV positive - project adds value at this discount rate" if npv > 0 else "NPV negative - project destroys value at this discount rate",
        "_warnings": [warning] if warning else [],
    }


TOOL_NPV = ToolSpec(
    key="ec_003",
    title="Net Present Value (NPV) Calculator",
    category="Operating Cost & Profitability (OPEX)",
    description="Discounts a series of cash flows to present value at a given discount rate.",
    inputs=[
        InputSpec("cash_flows", "Cash Flows (comma-separated, period 0 first)", default=0.0, input_type="text",
                   default_text="-1000, 300, 300, 300, 300, 300",
                   help="Enter as text: period-0 cash flow first (typically the negative initial investment), then one value per subsequent period."),
        InputSpec("discount_rate", "Discount Rate (r)", default=0.10, min_value=-0.99, max_value=2.0, step=0.01,
                   help="Enter as a fraction, e.g. 0.10 for 10%."),
    ],
    compute=compute_npv,
    formula_md=r"$$NPV = \sum_{t=0}^{n} \dfrac{CF_t}{(1+r)^t}$$",
    references=["Peters, Timmerhaus & West, Plant Design and Economics for Chemical Engineers, Ch. 9", "Brealey, Myers & Allen, Principles of Corporate Finance"],
    assumptions=[
        "Discrete, end-of-period cash flows assumed (standard NPV convention) - period 0 is typically the initial investment.",
        "A single, constant discount rate is applied across all periods - does not account for a term structure of rates.",
        "This tool calculates NPV only, not IRR - IRR requires iterative root-finding and is a natural next addition.",
    ],
)


REGISTRY: dict[str, ToolSpec] = {
    TOOL_CEPCI.key: TOOL_CEPCI,
    TOOL_CAPACITY_SCALING.key: TOOL_CAPACITY_SCALING,
    TOOL_NPV.key: TOOL_NPV,
}
