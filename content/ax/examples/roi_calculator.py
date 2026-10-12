"""Planning arithmetic only. Standard library; no network or AI API calls."""

import argparse
import json
import math
from pathlib import Path


def calculate(data):
    """Unknown cash realization is 0. Negative time changes remain negative."""
    required = (
        "monthly_volume", "eligible_rate", "adoption_rate", "before_minutes",
        "after_minutes", "hourly_value", "setup_cash", "allocation_months",
        "recurring_cash", "internal_operation_value",
    )
    optional = {"cash_realization_rate"}
    if not isinstance(data, dict) or set(data) - set(required) - optional:
        raise ValueError("Expected only the documented assumption fields")
    values = {}
    for key in (*required, "cash_realization_rate"):
        raw = data.get(key, 0) if key == "cash_realization_rate" else data.get(key)
        if isinstance(raw, bool) or not isinstance(raw, (int, float)):
            raise ValueError(f"{key}: finite number required")
        value = float(raw)
        if not math.isfinite(value) or value < 0:
            raise ValueError(f"{key}: nonnegative finite number required")
        if key.endswith("_rate") and value > 1:
            raise ValueError(f"{key}: use a ratio from 0 to 1")
        values[key] = value
    if values["allocation_months"] <= 0:
        raise ValueError("allocation_months must be positive")
    effective = values["monthly_volume"] * values["eligible_rate"] * values["adoption_rate"]
    hours = effective * (values["before_minutes"] - values["after_minutes"]) / 60
    potential = hours * values["hourly_value"]
    burden = (values["setup_cash"] / values["allocation_months"]
              + values["recurring_cash"] + values["internal_operation_value"])
    cash = potential * values["cash_realization_rate"] - values["recurring_cash"]
    result = {
        "effective_cases": effective,
        "hours_change": hours,
        "potential_capacity_value": potential,
        "monthly_economic_burden": burden,
        "monthly_economic_difference": potential - burden,
        "monthly_cash_change": cash,
        "simple_payback_months": values["setup_cash"] / cash if cash > 0 else None,
    }
    if any(value is not None and not math.isfinite(value) for value in result.values()):
        raise ValueError("Result exceeds finite arithmetic range")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("assumptions", type=Path)
    args = parser.parse_args()
    try:
        result = calculate(json.loads(args.assumptions.read_text(encoding="utf-8-sig")))
    except (OSError, ValueError, OverflowError) as exc:
        parser.exit(2, f"Invalid assumptions: {exc}\n")
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
