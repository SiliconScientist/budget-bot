from __future__ import annotations

import shutil
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from bb.transactions import (
    UnsupportedStatementSource,
    get_statement_parser,
    load_transactions,
    parse_chase_credit_rows,
    parse_chase_debit_rows,
    parse_venmo_rows,
)


FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture_transactions(fixture_name: str, account_name: str) -> list:
    with tempfile.TemporaryDirectory() as tmpdir:
        account_dir = Path(tmpdir) / account_name
        account_dir.mkdir()
        shutil.copy(FIXTURES_DIR / fixture_name, account_dir / "statement.csv")
        return load_transactions(account_dir)


class StatementParserTests(unittest.TestCase):
    def test_chase_debit_fixture_selects_chase_debit_parser(self) -> None:
        self.assertIs(get_statement_parser("debit_demo"), parse_chase_debit_rows)

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
        self.assertEqual(income_tx.posting_year, 2026)
        self.assertEqual(income_tx.posting_month, 3)

    def test_chase_credit_fixture_selects_chase_credit_parser(self) -> None:
        self.assertIs(get_statement_parser("credit_demo"), parse_chase_credit_rows)

    def test_chase_credit_fixture_documents_expected_normalized_fields(self) -> None:
        transactions = load_fixture_transactions("chase_credit.csv", "credit_demo")

        self.assertEqual(len(transactions), 3)

        first_tx = transactions[0]
        self.assertEqual(first_tx.account, "credit_demo")
        self.assertEqual(first_tx.posting_date, "03/23/2026")
        self.assertEqual(first_tx.description, "DENTAL OFFICE VISIT")
        self.assertEqual(first_tx.amount, Decimal("-90.00"))
        self.assertEqual(
            first_tx.source_metadata,
            {
                "details": "Health & Wellness",
                "transaction_date": "03/22/2026",
                "transaction_type": "Sale",
                "memo": "",
            },
        )

        payment_tx = transactions[2]
        self.assertEqual(payment_tx.account, "credit_demo")
        self.assertEqual(payment_tx.posting_date, "03/04/2026")
        self.assertEqual(payment_tx.description, "AUTOMATIC PAYMENT - THANK")
        self.assertEqual(payment_tx.amount, Decimal("-750.00"))
        self.assertFalse(payment_tx.is_income)
        self.assertEqual(
            payment_tx.source_metadata,
            {
                "details": "",
                "transaction_date": "03/04/2026",
                "transaction_type": "Payment",
                "memo": "",
            },
        )

    def test_venmo_fixture_selects_venmo_parser(self) -> None:
        self.assertIs(get_statement_parser("venmo"), parse_venmo_rows)

    def test_venmo_fixture_documents_expected_normalized_fields(self) -> None:
        transactions = load_fixture_transactions("venmo.csv", "venmo")

        self.assertEqual(len(transactions), 3)

        outgoing_tx = transactions[0]
        self.assertEqual(outgoing_tx.account, "venmo")
        self.assertEqual(outgoing_tx.posting_date, "2026-03-10")
        self.assertEqual(outgoing_tx.description, "Coaching session")
        self.assertEqual(outgoing_tx.amount, Decimal("-20.00"))
        self.assertEqual(
            outgoing_tx.source_metadata,
            {
                "details": "Complete",
                "transaction_type": "Charge",
                "venmo_id": "1234567890123456789",
                "from": "Person Example",
                "to": "Sample User",
                "funding_source": "Venmo balance",
                "destination": "",
            },
        )

        incoming_tx = transactions[1]
        self.assertEqual(incoming_tx.account, "venmo")
        self.assertEqual(incoming_tx.posting_date, "2026-03-11")
        self.assertEqual(incoming_tx.description, "Dinner reimbursement")
        self.assertEqual(incoming_tx.amount, Decimal("12.34"))
        self.assertTrue(incoming_tx.is_income)
        self.assertEqual(incoming_tx.posting_year, 2026)
        self.assertEqual(incoming_tx.posting_month, 3)

        merchant_tx = transactions[2]
        self.assertEqual(merchant_tx.account, "venmo")
        self.assertEqual(merchant_tx.posting_date, "2026-03-11")
        self.assertEqual(merchant_tx.description, "Merchant Transaction")
        self.assertEqual(merchant_tx.amount, Decimal("-35.00"))
        self.assertEqual(
            merchant_tx.source_metadata,
            {
                "details": "Complete",
                "transaction_type": "Merchant Transaction",
                "venmo_id": "4234567890123456789",
                "from": "Sample User",
                "to": "Fundraiser Example",
                "funding_source": "Venmo balance",
                "destination": "",
            },
        )

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

    def test_unknown_account_source_is_rejected(self) -> None:
        with self.assertRaises(UnsupportedStatementSource):
            get_statement_parser("savings1234")

    def test_mismatched_directory_and_fixture_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            account_dir = Path(tmpdir) / "venmo"
            account_dir.mkdir()
            shutil.copy(FIXTURES_DIR / "chase_debit.csv", account_dir / "statement.csv")

            with self.assertRaises(UnsupportedStatementSource):
                load_transactions(account_dir)

    def test_unsupported_posting_date_format_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tx = parse_chase_debit_rows(
                "debit_demo",
                Path(tmpdir) / "statement.csv",
                [
                    {
                        "Details": "CREDIT",
                        "Posting Date": "2026/03/27",
                        "Description": "ACME PAYROLL",
                        "Amount": "1500.00",
                        "Type": "ACH_CREDIT",
                    }
                ],
            )[0]

        with self.assertRaises(ValueError):
            _ = tx.posting_date_value


if __name__ == "__main__":
    unittest.main()
