from __future__ import annotations

import shutil
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from bb.config import MonthlyBudgetConfig
from bb.parse import UnsupportedStatementSource
from bb.transaction import (
    filter_transactions_by_month,
    load_all_transactions,
    load_transactions,
)


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
    monthly_transactions = filter_transactions_by_month(
        transactions,
        monthly_budget.year,
        monthly_budget.month,
    )
    return [tx for tx in monthly_transactions if tx.is_income]


class TransactionTests(unittest.TestCase):
    def test_chase_debit_and_credit_fixtures_can_coexist(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            raw_data_dir = Path(tmpdir)
            debit_dir = raw_data_dir / "debit_demo"
            credit_dir = raw_data_dir / "credit_demo"
            debit_dir.mkdir()
            credit_dir.mkdir()

            shutil.copy(FIXTURES_DIR / "chase_debit.csv", debit_dir / "statement.csv")
            shutil.copy(FIXTURES_DIR / "chase_credit.csv", credit_dir / "statement.csv")

            debit_transactions = load_transactions(debit_dir)
            credit_transactions = load_transactions(credit_dir)

        self.assertEqual(len(debit_transactions), 2)
        self.assertEqual(len(credit_transactions), 3)
        self.assertEqual(debit_transactions[0].account, "debit_demo")
        self.assertEqual(credit_transactions[0].account, "credit_demo")

    def test_nested_statement_files_are_loaded(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            account_dir = Path(tmpdir) / "debit_demo"
            year_dir = account_dir / "2026"
            year_dir.mkdir(parents=True)
            shutil.copy(FIXTURES_DIR / "chase_debit.csv", year_dir / "march.csv")

            transactions = load_transactions(account_dir)

        self.assertEqual(len(transactions), 2)
        self.assertEqual(transactions[0].source_file.name, "march.csv")

    def test_mismatched_directory_and_fixture_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            account_dir = Path(tmpdir) / "venmo"
            account_dir.mkdir()
            shutil.copy(FIXTURES_DIR / "chase_debit.csv", account_dir / "statement.csv")

            with self.assertRaises(UnsupportedStatementSource):
                load_transactions(account_dir)

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
            all(
                tx.description
                != "EXAMPLE EMPLOYER PAYROLL"
                for tx in income_transactions
            )
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
