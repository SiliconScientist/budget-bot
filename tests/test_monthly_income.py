from __future__ import annotations

import shutil
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from bb.config import MonthlyBudgetConfig
import bb.transactions as transactions_module
from bb.transactions import load_all_transactions


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
    transactions = load_all_transactions(raw_data_dir)
    filter_transactions_by_month = getattr(
        transactions_module,
        "filter_transactions_by_month",
    )
    monthly_transactions = filter_transactions_by_month(
        transactions,
        monthly_budget.year,
        monthly_budget.month,
    )
    return [tx for tx in monthly_transactions if tx.is_income]


class MonthlyIncomeTests(unittest.TestCase):
    @unittest.expectedFailure
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

    @unittest.expectedFailure
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

    @unittest.expectedFailure
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

    @unittest.expectedFailure
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


if __name__ == "__main__":
    unittest.main()
