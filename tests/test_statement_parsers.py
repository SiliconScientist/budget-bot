from __future__ import annotations

import shutil
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from bb.transactions import load_transactions


FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture_transactions(fixture_name: str, account_name: str) -> list:
    with tempfile.TemporaryDirectory() as tmpdir:
        account_dir = Path(tmpdir) / account_name
        account_dir.mkdir()
        shutil.copy(FIXTURES_DIR / fixture_name, account_dir / "statement.csv")
        return load_transactions(account_dir)


class StatementParserTests(unittest.TestCase):
    def test_chase_debit_fixture_matches_current_normalized_shape(self) -> None:
        transactions = load_fixture_transactions("chase_debit.csv", "debit_demo")

        self.assertEqual(len(transactions), 2)

        income_tx = transactions[0]
        self.assertEqual(income_tx.account, "debit_demo")
        self.assertEqual(income_tx.posting_date, "03/21/2026")
        self.assertEqual(income_tx.description, "ACME PAYROLL")
        self.assertEqual(income_tx.amount, Decimal("1500.00"))
        self.assertEqual(
            income_tx.source_metadata,
            {"details": "CREDIT", "transaction_type": "ACH_CREDIT"},
        )

        debit_tx = transactions[1]
        self.assertEqual(debit_tx.account, "debit_demo")
        self.assertEqual(debit_tx.posting_date, "03/20/2026")
        self.assertEqual(debit_tx.description, "CARD PURCHASE COFFEE")
        self.assertEqual(debit_tx.amount, Decimal("-15.00"))
        self.assertEqual(
            debit_tx.source_metadata,
            {"details": "DEBIT", "transaction_type": "DEBIT_CARD"},
        )

    @unittest.expectedFailure
    def test_chase_credit_fixture_documents_expected_normalized_fields(self) -> None:
        transactions = load_fixture_transactions("chase_credit.csv", "credit_demo")

        self.assertEqual(len(transactions), 2)

        first_tx = transactions[0]
        self.assertEqual(first_tx.account, "credit_demo")
        self.assertEqual(first_tx.posting_date, "03/23/2026")
        self.assertEqual(first_tx.description, "DENTAL OFFICE VISIT")
        self.assertEqual(first_tx.amount, Decimal("-90.00"))
        self.assertEqual(
            first_tx.source_metadata,
            {"details": "Health & Wellness", "transaction_type": "Sale"},
        )

    @unittest.expectedFailure
    def test_venmo_fixture_documents_expected_normalized_fields(self) -> None:
        transactions = load_fixture_transactions("venmo.csv", "venmo")

        self.assertEqual(len(transactions), 1)

        tx = transactions[0]
        self.assertEqual(tx.account, "venmo")
        self.assertEqual(tx.posting_date, "2026-03-10")
        self.assertEqual(tx.description, "Coaching session")
        self.assertEqual(tx.amount, Decimal("-20.00"))
        self.assertEqual(
            tx.source_metadata,
            {"details": "Complete", "transaction_type": "Charge"},
        )


if __name__ == "__main__":
    unittest.main()
