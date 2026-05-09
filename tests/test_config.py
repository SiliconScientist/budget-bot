from __future__ import annotations

import unittest

from bb.config import BudgetBucketConfig, MonthlyBudgetConfig


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
            needs=BudgetBucketConfig(frac=0.5, categories=("rent",)),
            wants=BudgetBucketConfig(frac=0.3, categories=("movies",)),
            savings=BudgetBucketConfig(frac=0.2, categories=("savings",)),
        )
        self.assertEqual(cfg.needs.frac, 0.5)
        self.assertEqual(cfg.wants.frac, 0.3)
        self.assertEqual(cfg.savings.frac, 0.2)

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
            r"monthly_budget\.needs\.frac must be between 0 and 1",
        ):
            MonthlyBudgetConfig(
                year=2026,
                month="february",
                needs=BudgetBucketConfig(frac=1.1, categories=("rent",)),
                wants=BudgetBucketConfig(frac=0.0, categories=("movies",)),
                savings=BudgetBucketConfig(frac=0.0, categories=("savings",)),
            )

    def test_budget_allocation_fractions_must_sum_to_one(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            r"monthly_budget\.needs\.frac, monthly_budget\.wants\.frac, "
            r"and monthly_budget\.savings\.frac must sum to 1",
        ):
            MonthlyBudgetConfig(
                year=2026,
                month="february",
                needs=BudgetBucketConfig(frac=0.5, categories=("rent",)),
                wants=BudgetBucketConfig(frac=0.3, categories=("movies",)),
                savings=BudgetBucketConfig(frac=0.1, categories=("savings",)),
            )

    def test_budget_categories_are_valid(self) -> None:
        cfg = MonthlyBudgetConfig(
            needs=BudgetBucketConfig(frac=0.5, categories=("housing", "groceries")),
            wants=BudgetBucketConfig(frac=0.3, categories=("travel",)),
            savings=BudgetBucketConfig(frac=0.2, categories=("emergency_fund",)),
        )
        self.assertEqual(cfg.needs.categories, ("housing", "groceries"))
        self.assertEqual(cfg.wants.categories, ("travel",))
        self.assertEqual(cfg.savings.categories, ("emergency_fund",))

    def test_budget_categories_reject_non_snake_case_category(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            r"monthly_budget\.needs\.categories must contain only snake_case strings",
        ):
            MonthlyBudgetConfig(
                needs=BudgetBucketConfig(frac=0.5, categories=("Rent",)),
                wants=BudgetBucketConfig(frac=0.3, categories=("travel",)),
                savings=BudgetBucketConfig(frac=0.2, categories=("emergency_fund",)),
            )

    def test_budget_categories_reject_duplicate_cross_bucket_category(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            r"monthly_budget categories must be unique across needs, wants, and savings",
        ):
            MonthlyBudgetConfig(
                needs=BudgetBucketConfig(frac=0.5, categories=("rent",)),
                wants=BudgetBucketConfig(frac=0.3, categories=("rent",)),
                savings=BudgetBucketConfig(frac=0.2, categories=("emergency_fund",)),
            )


if __name__ == "__main__":
    unittest.main()
