from __future__ import annotations

import shutil
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from bb.config import MonthlyBudgetConfig
from bb.transactions import load_income_transactions


FIXTURES_DIR = Path(__file__).parent / "fixtures"


def create_statement(
    raw_data_dir: Path,
    account_name: str,
    year: str,
    month_filename: str,
    fixture_name: str,
) -> None:
    month_dir = raw_data_dir / account_name / year
    month_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(FIXTURES_DIR / fixture_name, month_dir / month_filename)


def load_configured_monthly_income_transactions(
    raw_data_dir: Path,
    monthly_budget: MonthlyBudgetConfig,
) -> list:
    return load_income_transactions(raw_data_dir, monthly_budget)


class MonthlyIncomeTests(unittest.TestCase):
    def test_monthly_budget_month_matches_one_month(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            raw_data_dir = Path(tmpdir) / "raw"
            create_statement(
                raw_data_dir,
                "debit_demo",
                "2026",
                "february.csv",
                "chase_debit_february.csv",
            )
            create_statement(
                raw_data_dir,
                "debit_demo",
                "2026",
                "march.csv",
                "chase_debit.csv",
            )
            monthly_budget = MonthlyBudgetConfig(year=2026, month="february")

            income_transactions = load_configured_monthly_income_transactions(
                raw_data_dir,
                monthly_budget,
            )

        self.assertEqual(len(income_transactions), 1)
        self.assertEqual(income_transactions[0].posting_date, "02/07/2026")
        self.assertEqual(income_transactions[0].amount, Decimal("500.00"))

    def test_monthly_budget_month_excludes_other_months(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            raw_data_dir = Path(tmpdir) / "raw"
            create_statement(
                raw_data_dir,
                "debit_demo",
                "2026",
                "february.csv",
                "chase_debit_february.csv",
            )
            create_statement(
                raw_data_dir,
                "debit_demo",
                "2026",
                "march.csv",
                "chase_debit.csv",
            )
            monthly_budget = MonthlyBudgetConfig(year=2026, month="february")

            income_transactions = load_configured_monthly_income_transactions(
                raw_data_dir,
                monthly_budget,
            )

        self.assertTrue(
            all(tx.posting_date.startswith("02/") for tx in income_transactions)
        )
        self.assertTrue(
            all(tx.description != "EXAMPLE EMPLOYER PAYROLL"
                for tx in income_transactions)
        )

    def test_monthly_budget_month_handles_mixed_source_income(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            raw_data_dir = Path(tmpdir) / "raw"
            create_statement(
                raw_data_dir,
                "debit_demo",
                "2026",
                "march.csv",
                "chase_debit.csv",
            )
            create_statement(
                raw_data_dir,
                "venmo",
                "2026",
                "march.csv",
                "venmo.csv",
            )
            monthly_budget = MonthlyBudgetConfig(year=2026, month="march")

            income_transactions = load_configured_monthly_income_transactions(
                raw_data_dir,
                monthly_budget,
            )

        self.assertEqual(
            {tx.account for tx in income_transactions},
            {"debit_demo", "venmo"},
        )
        self.assertEqual(
            sum((tx.amount for tx in income_transactions), start=Decimal("0")),
            Decimal("1512.34"),
        )

    def test_monthly_budget_month_handles_no_match(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            raw_data_dir = Path(tmpdir) / "raw"
            create_statement(
                raw_data_dir,
                "debit_demo",
                "2026",
                "march.csv",
                "chase_debit.csv",
            )
            create_statement(
                raw_data_dir,
                "venmo",
                "2026",
                "march.csv",
                "venmo.csv",
            )
            monthly_budget = MonthlyBudgetConfig(year=2026, month="january")

            income_transactions = load_configured_monthly_income_transactions(
                raw_data_dir,
                monthly_budget,
            )

        self.assertEqual(income_transactions, [])

    def test_monthly_budget_month_accepts_integer_month(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            raw_data_dir = Path(tmpdir) / "raw"
            create_statement(
                raw_data_dir,
                "debit_demo",
                "2026",
                "february.csv",
                "chase_debit_february.csv",
            )
            create_statement(
                raw_data_dir,
                "debit_demo",
                "2026",
                "march.csv",
                "chase_debit.csv",
            )
            monthly_budget = MonthlyBudgetConfig(year=2026, month=2)

            income_transactions = load_configured_monthly_income_transactions(
                raw_data_dir,
                monthly_budget,
            )

        self.assertEqual(len(income_transactions), 1)
        self.assertEqual(income_transactions[0].posting_date, "02/07/2026")

    def test_monthly_budget_month_accepts_numeric_string_month(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            raw_data_dir = Path(tmpdir) / "raw"
            create_statement(
                raw_data_dir,
                "debit_demo",
                "2026",
                "february.csv",
                "chase_debit_february.csv",
            )
            create_statement(
                raw_data_dir,
                "debit_demo",
                "2026",
                "march.csv",
                "chase_debit.csv",
            )
            monthly_budget = MonthlyBudgetConfig(year=2026, month="2")

            income_transactions = load_configured_monthly_income_transactions(
                raw_data_dir,
                monthly_budget,
            )

        self.assertEqual(len(income_transactions), 1)
        self.assertEqual(income_transactions[0].posting_date, "02/07/2026")


if __name__ == "__main__":
    unittest.main()
