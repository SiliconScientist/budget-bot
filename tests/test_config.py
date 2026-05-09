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

    def test_budget_allocation_fractions_are_valid(self) -> None:
        cfg = MonthlyBudgetConfig(
            year=2026,
            month="February",
            needs_frac=0.5,
            wants_frac=0.3,
            savings_frac=0.2,
        )
        self.assertEqual(cfg.needs_frac, 0.5)
        self.assertEqual(cfg.wants_frac, 0.3)
        self.assertEqual(cfg.savings_frac, 0.2)

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

    def test_invalid_budget_allocation_fraction_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            r"monthly_budget\.needs_frac must be between 0 and 1",
        ):
            MonthlyBudgetConfig(
                year=2026,
                month="february",
                needs_frac=1.1,
                wants_frac=0.0,
                savings_frac=0.0,
            )

    def test_budget_allocation_fractions_must_sum_to_one(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            r"monthly_budget\.needs_frac, monthly_budget\.wants_frac, "
            r"and monthly_budget\.savings_frac must sum to 1",
        ):
            MonthlyBudgetConfig(
                year=2026,
                month="february",
                needs_frac=0.5,
                wants_frac=0.3,
                savings_frac=0.1,
            )


if __name__ == "__main__":
    unittest.main()
