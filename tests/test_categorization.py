from __future__ import annotations

import csv
import shutil
import tempfile
import unittest
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from bb.category import (
    CategoryRule,
    CategoryRuleConfigError,
    CategorizedTransaction,
    categorize_transaction,
    load_category_rules,
)
from bb.transaction import Transaction, load_transactions


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
    expected_rule_id: str | None


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
                expected_rule_id=row["expected_rule_id"] or None,
            )
            for row in reader
        ]


def write_rules_file(contents: str) -> Path:
    tmpdir = tempfile.mkdtemp()
    config_path = Path(tmpdir) / "category.toml"
    config_path.write_text(contents, encoding="utf-8")
    return config_path


def transaction_key(transaction: Transaction) -> tuple[str, str, str, Decimal]:
    return (
        transaction.account,
        transaction.posting_date,
        transaction.description,
        transaction.amount,
    )


def categorized_transaction_key(
    categorized_transaction: CategorizedTransaction,
) -> tuple[str, str, str, Decimal]:
    return transaction_key(categorized_transaction.transaction)


class CategorizationFixtureTests(unittest.TestCase):
    def test_load_category_rules_returns_typed_rule_models(self) -> None:
        rules = load_category_rules(RULES_FIXTURE)

        self.assertEqual(len(rules), 9)
        self.assertIsInstance(rules[0], CategoryRule)
        self.assertEqual(rules[0].id, "paycheck_income")
        self.assertEqual(rules[0].category, "income:paycheck")
        self.assertEqual(rules[0].description_contains, ("PAYROLL",))
        self.assertEqual(rules[0].accounts, ())
        self.assertTrue(rules[0].is_income)

    def test_missing_rules_array_is_rejected(self) -> None:
        config_path = write_rules_file('default_category = "misc"\n')

        with self.assertRaisesRegex(
            CategoryRuleConfigError,
            r"top-level 'rules' array",
        ):
            load_category_rules(config_path)

    def test_invalid_rule_field_type_is_rejected(self) -> None:
        config_path = write_rules_file(
            (
                "[[rules]]\n"
                'id = "coffee"\n'
                'category = "dining:coffee"\n'
                'description_contains = "COFFEE"\n'
            )
        )

        with self.assertRaisesRegex(
            CategoryRuleConfigError,
            r"rules\[1\]\.description_contains must be an array of strings",
        ):
            load_category_rules(config_path)

    def test_duplicate_rule_ids_are_rejected(self) -> None:
        config_path = write_rules_file(
            (
                "[[rules]]\n"
                'id = "duplicate"\n'
                'category = "first"\n'
                "\n"
                "[[rules]]\n"
                'id = "duplicate"\n'
                'category = "second"\n'
            )
        )

        with self.assertRaisesRegex(
            CategoryRuleConfigError,
            r"rules\[2\]\.id duplicates 'duplicate'",
        ):
            load_category_rules(config_path)

    def test_fixture_rules_assign_expected_categories_across_sources(self) -> None:
        rules = load_category_rules(RULES_FIXTURE)
        expected_categories = {
            (
                row.account,
                row.posting_date,
                row.description,
                row.amount,
            ): (row.expected_category, row.expected_rule_id)
            for row in load_expected_categories()
        }

        actual_categories = {
            categorized_transaction_key(categorized_transaction): (
                categorized_transaction.category,
                categorized_transaction.matched_rule_id,
            )
            for categorized_transaction in (
                categorize_transaction(transaction, rules)
                for transaction in load_all_statement_fixture_transactions()
            )
        }

        self.assertEqual(actual_categories, expected_categories)

    def test_categorized_result_carries_original_transaction(self) -> None:
        rules = load_category_rules(RULES_FIXTURE)
        transaction = load_fixture_transactions("chase_credit.csv", "credit_demo")[0]

        categorized_transaction = categorize_transaction(transaction, rules)

        self.assertIs(categorized_transaction.transaction, transaction)

    def test_categorized_result_carries_category_and_matched_rule_id(self) -> None:
        rules = load_category_rules(RULES_FIXTURE)
        transaction = next(
            tx
            for tx in load_fixture_transactions("chase_debit.csv", "debit_demo")
            if tx.description == "CARD PURCHASE COFFEE"
        )

        categorized_transaction = categorize_transaction(transaction, rules)

        self.assertEqual(categorized_transaction.category, "dining:coffee")
        self.assertEqual(categorized_transaction.matched_rule_id, "debit_coffee")

    def test_overlapping_rules_use_first_match_for_debit_transactions(self) -> None:
        rules = load_category_rules(RULES_FIXTURE)
        coffee_transaction = next(
            tx
            for tx in load_fixture_transactions("chase_debit.csv", "debit_demo")
            if tx.description == "CARD PURCHASE COFFEE"
        )

        categorized_transaction = categorize_transaction(coffee_transaction, rules)

        self.assertEqual(categorized_transaction.category, "dining:coffee")
        self.assertEqual(categorized_transaction.matched_rule_id, "debit_coffee")

    def test_overlapping_rules_use_first_match_for_venmo_income(self) -> None:
        rules = load_category_rules(RULES_FIXTURE)
        reimbursement_transaction = next(
            tx
            for tx in load_fixture_transactions("venmo.csv", "venmo")
            if tx.description == "Dinner reimbursement"
        )

        categorized_transaction = categorize_transaction(reimbursement_transaction, rules)

        self.assertEqual(categorized_transaction.category, "income:reimbursement")
        self.assertEqual(
            categorized_transaction.matched_rule_id,
            "venmo_reimbursement",
        )

    def test_unmatched_transactions_return_empty_category_result(self) -> None:
        rules = load_category_rules(RULES_FIXTURE)
        merchant_transaction = next(
            tx
            for tx in load_fixture_transactions("venmo.csv", "venmo")
            if tx.description == "Merchant Transaction"
        )

        categorized_transaction = categorize_transaction(merchant_transaction, rules)

        self.assertIs(categorized_transaction.transaction, merchant_transaction)
        self.assertIsNone(categorized_transaction.category)
        self.assertIsNone(categorized_transaction.matched_rule_id)


if __name__ == "__main__":
    unittest.main()
