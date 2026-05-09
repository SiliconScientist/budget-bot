from __future__ import annotations

import unittest

from bb.config import MonthlyBudgetConfig


class MonthlyBudgetConfigTests(unittest.TestCase):
    def test_month_name_is_valid(self) -> None:
        cfg = MonthlyBudgetConfig(year=2026, month="February")
        self.assertEqual(cfg.year, 2026)
        self.assertEqual(cfg.month, "February")

    def test_numeric_string_month_is_valid(self) -> None:
        cfg = MonthlyBudgetConfig(year=2026, month="2")
        self.assertEqual(cfg.month, "2")

    def test_integer_month_is_valid(self) -> None:
        cfg = MonthlyBudgetConfig(year=2026, month=2)
        self.assertEqual(cfg.month, 2)

    def test_invalid_month_name_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            r"monthly_budget\.month must be a month name or number 1-12",
        ):
            MonthlyBudgetConfig(year=2026, month="banana")

    def test_invalid_month_number_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            r"monthly_budget\.month must be between 1 and 12",
        ):
            MonthlyBudgetConfig(year=2026, month=13)

    def test_invalid_year_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            r"monthly_budget\.year must be a positive integer",
        ):
            MonthlyBudgetConfig(year=0, month="february")


if __name__ == "__main__":
    unittest.main()
