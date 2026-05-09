from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout
from decimal import Decimal
from pathlib import Path

from bb.report import print_income_report
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


if __name__ == "__main__":
    unittest.main()
