from __future__ import annotations

import csv
import shutil
import tempfile
import unittest
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from bb.categorization import categorize_transaction, load_category_rules
from bb.transactions import Transaction, load_transactions


FIXTURES_DIR = Path(__file__).parent / "fixtures"
RULES_FIXTURE = FIXTURES_DIR / "categorization_rules.toml"
EXPECTED_CATEGORIES_FIXTURE = FIXTURES_DIR / "expected_categories.csv"
STATEMENT_FIXTURES = (
    ("debit_demo", "chase_debit.csv"),
    ("credit_demo", "chase_credit.csv"),
    ("venmo", "venmo.csv"),
)


@dataclass(frozen=True)
class ExpectedCategory:
    account: str
    posting_date: str
    description: str
    amount: Decimal
    expected_category: str | None


def load_fixture_transactions(fixture_name: str, account_name: str) -> list[Transaction]:
    with tempfile.TemporaryDirectory() as tmpdir:
        account_dir = Path(tmpdir) / account_name
        account_dir.mkdir()
        shutil.copy(FIXTURES_DIR / fixture_name, account_dir / "statement.csv")
        return load_transactions(account_dir)


def load_all_statement_fixture_transactions() -> list[Transaction]:
    transactions: list[Transaction] = []
    for account_name, fixture_name in STATEMENT_FIXTURES:
        transactions.extend(load_fixture_transactions(fixture_name, account_name))
    return transactions


def load_expected_categories() -> list[ExpectedCategory]:
    with EXPECTED_CATEGORIES_FIXTURE.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return [
            ExpectedCategory(
                account=row["account"],
                posting_date=row["posting_date"],
                description=row["description"],
                amount=Decimal(row["amount"]),
                expected_category=row["expected_category"] or None,
            )
            for row in reader
        ]


def transaction_key(transaction: Transaction) -> tuple[str, str, str, Decimal]:
    return (
        transaction.account,
        transaction.posting_date,
        transaction.description,
        transaction.amount,
    )


class CategorizationFixtureTests(unittest.TestCase):
    def test_fixture_rules_assign_expected_categories_across_sources(self) -> None:
        rules = load_category_rules(RULES_FIXTURE)
        expected_categories = {
            (
                row.account,
                row.posting_date,
                row.description,
                row.amount,
            ): row.expected_category
            for row in load_expected_categories()
        }

        actual_categories = {
            transaction_key(transaction): categorize_transaction(transaction, rules)
            for transaction in load_all_statement_fixture_transactions()
        }

        self.assertEqual(actual_categories, expected_categories)

    def test_overlapping_rules_use_first_match_for_debit_transactions(self) -> None:
        rules = load_category_rules(RULES_FIXTURE)
        coffee_transaction = next(
            tx
            for tx in load_fixture_transactions("chase_debit.csv", "debit_demo")
            if tx.description == "CARD PURCHASE COFFEE"
        )

        self.assertEqual(categorize_transaction(coffee_transaction, rules), "dining:coffee")

    def test_overlapping_rules_use_first_match_for_venmo_income(self) -> None:
        rules = load_category_rules(RULES_FIXTURE)
        reimbursement_transaction = next(
            tx
            for tx in load_fixture_transactions("venmo.csv", "venmo")
            if tx.description == "Dinner reimbursement"
        )

        self.assertEqual(
            categorize_transaction(reimbursement_transaction, rules),
            "income:reimbursement",
        )

    def test_unmatched_transactions_return_none(self) -> None:
        rules = load_category_rules(RULES_FIXTURE)
        merchant_transaction = next(
            tx
            for tx in load_fixture_transactions("venmo.csv", "venmo")
            if tx.description == "Merchant Transaction"
        )

        self.assertIsNone(categorize_transaction(merchant_transaction, rules))


if __name__ == "__main__":
    unittest.main()
