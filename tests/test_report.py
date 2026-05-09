from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout
from decimal import Decimal
from pathlib import Path

from bb.category import CategorizedTransaction, CategoryRule, UNCATEGORIZED_CATEGORY
from bb.report import print_categorization_report, print_income_report
from bb.transaction import Transaction


class ReportTests(unittest.TestCase):
    def test_income_report_header_shows_active_month_filter(self) -> None:
        income_transactions = [
            Transaction(
                account="debit_demo",
                source_file=Path("data/raw/debit_demo/2026/february.csv"),
                posting_date="02/07/2026",
                description="ACME PAYROLL",
                amount=Decimal("500.00"),
                source_metadata={"details": "CREDIT", "transaction_type": "ACH_CREDIT"},
            )
        ]

        output = io.StringIO()
        with redirect_stdout(output):
            print_income_report(2026, "february", income_transactions)

        lines = output.getvalue().splitlines()
        self.assertEqual(lines[0], "Income for 2026-02: $500.00")

    def test_categorization_report_prints_category_and_rule_id(self) -> None:
        categorized_transactions = [
            CategorizedTransaction(
                transaction=Transaction(
                    account="debit_demo",
                    source_file=Path("data/raw/debit_demo/2026/march.csv"),
                    posting_date="03/20/2026",
                    description="CARD PURCHASE COFFEE",
                    amount=Decimal("-15.00"),
                    source_metadata={
                        "details": "DEBIT",
                        "transaction_type": "DEBIT_CARD",
                    },
                ),
                category="dining:coffee",
                matched_rule_id="debit_coffee",
                matched_rule=CategoryRule(
                    id="debit_coffee",
                    category="dining:coffee",
                    accounts=("debit_demo",),
                    description_contains=("COFFEE",),
                ),
                matched_on=("account=debit_demo", "description_contains='COFFEE'"),
            ),
            CategorizedTransaction(
                transaction=Transaction(
                    account="venmo",
                    source_file=Path("data/raw/venmo/2026/march.csv"),
                    posting_date="2026-03-11",
                    description="Merchant Transaction",
                    amount=Decimal("-35.00"),
                    source_metadata={
                        "details": "Complete",
                        "transaction_type": "Merchant Transaction",
                    },
                ),
                category=UNCATEGORIZED_CATEGORY,
                matched_rule_id=None,
                matched_rule=None,
                matched_on=(),
            ),
        ]

        output = io.StringIO()
        with redirect_stdout(output):
            print_categorization_report(categorized_transactions)

        lines = output.getvalue().splitlines()
        self.assertEqual(lines[0], "Categorization report")
        self.assertEqual(
            lines[1],
            "03/20/2026     -$15.00  debit_demo   dining:coffee                 debit_coffee   CARD PURCHASE COFFEE",
        )
        self.assertEqual(
            lines[2],
            "2026-03-11     -$35.00  venmo       uncategorized                 -              Merchant Transaction",
        )


if __name__ == "__main__":
    unittest.main()
