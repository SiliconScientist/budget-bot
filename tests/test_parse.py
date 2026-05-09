from __future__ import annotations

import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from bb.parse import (
    UnsupportedStatementSource,
    get_statement_parser,
    parse_chase_credit_rows,
    parse_chase_debit_rows,
    parse_venmo_rows,
)


class ParseTests(unittest.TestCase):
    def test_chase_debit_selects_chase_debit_parser(self) -> None:
        self.assertIs(get_statement_parser("debit_demo"), parse_chase_debit_rows)

    def test_chase_debit_rows_match_normalized_shape(self) -> None:
        transactions = parse_chase_debit_rows(
            "debit_demo",
            Path("statement.csv"),
            [
                {
                    "Details": "CREDIT",
                    "Posting Date": "03/21/2026",
                    "Description": "ACME PAYROLL",
                    "Amount": "1500.00",
                    "Type": "ACH_CREDIT",
                },
                {
                    "Details": "DEBIT",
                    "Posting Date": "03/20/2026",
                    "Description": "CARD PURCHASE COFFEE",
                    "Amount": "-15.00",
                    "Type": "DEBIT_CARD",
                },
            ],
        )

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
        self.assertEqual(income_tx.posting_year, 2026)
        self.assertEqual(income_tx.posting_month, 3)

        debit_tx = transactions[1]
        self.assertEqual(debit_tx.account, "debit_demo")
        self.assertEqual(debit_tx.posting_date, "03/20/2026")
        self.assertEqual(debit_tx.description, "CARD PURCHASE COFFEE")
        self.assertEqual(debit_tx.amount, Decimal("-15.00"))
        self.assertEqual(
            debit_tx.source_metadata,
            {"details": "DEBIT", "transaction_type": "DEBIT_CARD"},
        )

    def test_chase_credit_selects_chase_credit_parser(self) -> None:
        self.assertIs(get_statement_parser("credit_demo"), parse_chase_credit_rows)

    def test_chase_credit_rows_match_normalized_shape(self) -> None:
        transactions = parse_chase_credit_rows(
            "credit_demo",
            Path("statement.csv"),
            [
                {
                    "Transaction Date": "03/22/2026",
                    "Post Date": "03/23/2026",
                    "Description": "DENTAL OFFICE VISIT",
                    "Category": "Health & Wellness",
                    "Type": "Sale",
                    "Amount": "-90.00",
                    "Memo": "",
                },
                {
                    "Transaction Date": "03/28/2026",
                    "Post Date": "03/29/2026",
                    "Description": "GROCERY STORE",
                    "Category": "Groceries",
                    "Type": "Sale",
                    "Amount": "-22.50",
                    "Memo": "",
                },
                {
                    "Transaction Date": "03/04/2026",
                    "Post Date": "03/04/2026",
                    "Description": "AUTOMATIC PAYMENT - THANK",
                    "Category": "",
                    "Type": "Payment",
                    "Amount": "750.00",
                    "Memo": "",
                },
            ],
        )

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

    def test_venmo_selects_venmo_parser(self) -> None:
        self.assertIs(get_statement_parser("venmo"), parse_venmo_rows)

    def test_venmo_rows_match_normalized_shape(self) -> None:
        transactions = parse_venmo_rows(
            "venmo",
            Path("statement.csv"),
            [
                {
                    "ID": "1234567890123456789",
                    "Datetime": "2026-03-10T09:00:00",
                    "Type": "Charge",
                    "Status": "Complete",
                    "Note": "Coaching session",
                    "From": "Person Example",
                    "To": "Sample User",
                    "Amount (total)": "-20.00",
                    "Funding Source": "Venmo balance",
                    "Destination": "",
                },
                {
                    "ID": "2234567890123456789",
                    "Datetime": "2026-03-11T09:00:00",
                    "Type": "Payment",
                    "Status": "Complete",
                    "Note": "Dinner reimbursement",
                    "From": "Person Example",
                    "To": "Sample User",
                    "Amount (total)": "12.34",
                    "Funding Source": "Venmo balance",
                    "Destination": "",
                },
                {
                    "ID": "4234567890123456789",
                    "Datetime": "2026-03-11T09:00:00",
                    "Type": "Merchant Transaction",
                    "Status": "Complete",
                    "Note": "",
                    "From": "Sample User",
                    "To": "Fundraiser Example",
                    "Amount (total)": "-35.00",
                    "Funding Source": "Venmo balance",
                    "Destination": "",
                },
            ],
        )

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

    def test_unknown_account_source_is_rejected(self) -> None:
        with self.assertRaises(UnsupportedStatementSource):
            get_statement_parser("savings1234")

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
