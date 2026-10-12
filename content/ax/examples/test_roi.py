"""Tests verify arithmetic, not business outcomes or AI answer quality."""

import json
from pathlib import Path
import unittest

from roi_calculator import calculate


class CalculatorTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(Path(__file__).with_name("baseline-assumptions.json").read_text())

    def test_baseline_and_no_positive_cash_payback(self):
        result = calculate(self.data)
        self.assertEqual(result["effective_cases"], 1440)
        self.assertEqual(result["hours_change"], 96)
        self.assertEqual(result["potential_capacity_value"], 2400000)
        self.assertEqual(result["monthly_economic_burden"], 1900000)
        self.assertEqual(result["monthly_economic_difference"], 500000)
        self.assertEqual(result["monthly_cash_change"], -300000)
        self.assertIsNone(result["simple_payback_months"])

    def test_slower_work_keeps_negative_change(self):
        self.data["after_minutes"] = 12
        result = calculate(self.data)
        self.assertEqual(result["hours_change"], -48)
        self.assertLess(result["monthly_cash_change"], -900000)

    def test_missing_cash_assumption_defaults_to_zero(self):
        del self.data["cash_realization_rate"]
        self.assertEqual(calculate(self.data)["monthly_cash_change"], -900000)

    def test_positive_cash_payback(self):
        self.data["cash_realization_rate"] = 1
        self.assertEqual(calculate(self.data)["simple_payback_months"], 4)

    def test_rates_and_invalid_numbers(self):
        for key, value in (
            ("adoption_rate", 1.1), ("eligible_rate", -0.1),
            ("cash_realization_rate", 2), ("allocation_months", 0),
            ("setup_cash", -1), ("hourly_value", float("inf")),
            ("before_minutes", float("nan")), ("monthly_volume", True),
            ("recurring_cash", "900000"),
        ):
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                calculate({**self.data, key: value})

    def test_missing_and_unknown_fields(self):
        data = dict(self.data)
        del data["before_minutes"]
        with self.assertRaises(ValueError):
            calculate(data)
        with self.assertRaises(ValueError):
            calculate({**self.data, "secret": "not-needed"})

    def test_zero_volume_still_has_cost(self):
        self.data["monthly_volume"] = 0
        result = calculate(self.data)
        self.assertEqual(result["hours_change"], 0)
        self.assertEqual(result["monthly_economic_difference"], -1900000)


if __name__ == "__main__":
    unittest.main()
