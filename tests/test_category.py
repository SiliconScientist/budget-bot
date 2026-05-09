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
    UNCATEGORIZED_CATEGORY,
    UNCATEGORIZED_BUCKET,
    categorize_transaction,
    load_category_rules,
)
from bb.config import MonthlyBudgetConfig
from bb.transaction import Transaction, load_transactions


FIXTURES_DIR = Path(__file__).parent / "fixtures"
RULES_FIXTURE = FIXTURES_DIR / "categorization_rules.toml"
EXPECTED_CATEGORIES_FIXTURE = FIXTURES_DIR / "expected_categories.csv"
STATEMENT_FIXTURES = (
    ("debit_demo", "chase_debit.csv"),
    ("credit_demo", "chase_credit.csv"),
    ("venmo", "venmo.csv"),
)
DEFAULT_MONTHLY_BUDGET = MonthlyBudgetConfig()


@dataclass(frozen=True)
class ExpectedCategory:
    account: str
    posting_date: str
    description: str
    amount: Decimal
    expected_category: str
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
                expected_category=row["expected_category"],
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
        rules = load_category_rules(RULES_FIXTURE, DEFAULT_MONTHLY_BUDGET)

        self.assertEqual(len(rules), 10)
        self.assertIsInstance(rules[0], CategoryRule)
        self.assertEqual(rules[0].id, "paycheck_income")
        self.assertEqual(rules[0].category, "paycheck")
        self.assertEqual(rules[0].bucket, "income")
        self.assertEqual(rules[0].amounts, ())
        self.assertEqual(rules[0].description_contains, ("PAYROLL",))
        self.assertEqual(rules[0].accounts, ())
        self.assertTrue(rules[0].is_income)
        self.assertFalse(rules[0].credit_card_payment)

    def test_missing_rules_array_is_rejected(self) -> None:
        config_path = write_rules_file('default_category = "misc"\n')

        with self.assertRaisesRegex(
            CategoryRuleConfigError,
            r"top-level 'rules' array",
        ):
            load_category_rules(config_path, DEFAULT_MONTHLY_BUDGET)

    def test_empty_bucket_is_rejected(self) -> None:
        config_path = write_rules_file(
            (
                "[[rules]]\n"
                'id = "coffee"\n'
                'category = "coffee"\n'
                'bucket = ""\n'
            )
        )

        with self.assertRaisesRegex(
            CategoryRuleConfigError,
            r"rules\[1\]\.bucket must be a non-empty string",
        ):
            load_category_rules(config_path, DEFAULT_MONTHLY_BUDGET)

    def test_non_snake_case_category_is_rejected(self) -> None:
        config_path = write_rules_file(
            (
                "[[rules]]\n"
                'id = "coffee"\n'
                'category = "Dining / Coffee"\n'
            )
        )

        with self.assertRaisesRegex(
            CategoryRuleConfigError,
            r"rules\[1\]\.category must be snake_case",
        ):
            load_category_rules(config_path, DEFAULT_MONTHLY_BUDGET)

    def test_non_snake_case_bucket_is_rejected(self) -> None:
        config_path = write_rules_file(
            (
                "[[rules]]\n"
                'id = "coffee"\n'
                'category = "coffee"\n'
                'bucket = "Needs Bucket"\n'
            )
        )

        with self.assertRaisesRegex(
            CategoryRuleConfigError,
            r"rules\[1\]\.bucket must be snake_case",
        ):
            load_category_rules(config_path, DEFAULT_MONTHLY_BUDGET)

    def test_valid_budget_bucket_category_combination_is_accepted(self) -> None:
        config_path = write_rules_file(
            (
                "[[rules]]\n"
                'id = "rent"\n'
                'category = "rent"\n'
                'bucket = "needs"\n'
            )
        )

        rules = load_category_rules(config_path, DEFAULT_MONTHLY_BUDGET)

        self.assertEqual(len(rules), 1)
        self.assertEqual(rules[0].category, "rent")
        self.assertEqual(rules[0].bucket, "needs")

    def test_invalid_budget_bucket_category_combination_is_rejected(self) -> None:
        config_path = write_rules_file(
            (
                "[[rules]]\n"
                'id = "rent"\n'
                'category = "rent"\n'
                'bucket = "wants"\n'
            )
        )

        with self.assertRaisesRegex(
            CategoryRuleConfigError,
            r"rules\[1\] budget category 'rent' must use bucket 'needs'",
        ):
            load_category_rules(config_path, DEFAULT_MONTHLY_BUDGET)

    def test_unknown_category_for_budget_bucket_is_rejected(self) -> None:
        config_path = write_rules_file(
            (
                "[[rules]]\n"
                'id = "coffee"\n'
                'category = "coffee"\n'
                'bucket = "wants"\n'
            )
        )

        with self.assertRaisesRegex(
            CategoryRuleConfigError,
            r"rules\[1\] budget bucket 'wants' only allows categories:",
        ):
            load_category_rules(config_path, DEFAULT_MONTHLY_BUDGET)

    def test_invalid_rule_boolean_field_type_is_rejected(self) -> None:
        config_path = write_rules_file(
            (
                "[[rules]]\n"
                'id = "coffee"\n'
                'category = "coffee"\n'
                "credit_card_payment = 1\n"
            )
        )

        with self.assertRaisesRegex(
            CategoryRuleConfigError,
            r"rules\[1\]\.credit_card_payment must be a boolean",
        ):
            load_category_rules(config_path, DEFAULT_MONTHLY_BUDGET)

    def test_counts_toward_income_can_be_disabled_on_a_rule(self) -> None:
        config_path = write_rules_file(
            (
                "[[rules]]\n"
                'id = "example_savings"\n'
                'category = "savings"\n'
                'bucket = "savings"\n'
                "counts_toward_income = false\n"
            )
        )

        rules = load_category_rules(config_path, DEFAULT_MONTHLY_BUDGET)

        self.assertFalse(rules[0].counts_toward_income)

    def test_invalid_rule_amounts_field_type_is_rejected(self) -> None:
        config_path = write_rules_file(
            (
                "[[rules]]\n"
                'id = "rent"\n'
                'category = "rent"\n'
                'bucket = "needs"\n'
                'amounts = "-1000.00"\n'
            )
        )

        with self.assertRaisesRegex(
            CategoryRuleConfigError,
            r"rules\[1\]\.amounts must be an array of decimal strings",
        ):
            load_category_rules(config_path, DEFAULT_MONTHLY_BUDGET)

    def test_invalid_rule_amount_value_is_rejected(self) -> None:
        config_path = write_rules_file(
            (
                "[[rules]]\n"
                'id = "rent"\n'
                'category = "rent"\n'
                'bucket = "needs"\n'
                'amounts = ["banana"]\n'
            )
        )

        with self.assertRaisesRegex(
            CategoryRuleConfigError,
            r"rules\[1\]\.amounts must contain only decimal strings",
        ):
            load_category_rules(config_path, DEFAULT_MONTHLY_BUDGET)

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
            load_category_rules(config_path, DEFAULT_MONTHLY_BUDGET)

    def test_fixture_rules_assign_expected_categories_across_sources(self) -> None:
        rules = load_category_rules(RULES_FIXTURE, DEFAULT_MONTHLY_BUDGET)
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
        rules = load_category_rules(RULES_FIXTURE, DEFAULT_MONTHLY_BUDGET)
        transaction = load_fixture_transactions("chase_credit.csv", "credit_demo")[0]

        categorized_transaction = categorize_transaction(transaction, rules)

        self.assertIs(categorized_transaction.transaction, transaction)

    def test_categorized_result_carries_bucket_category_and_matched_rule_id(self) -> None:
        rules = load_category_rules(RULES_FIXTURE, DEFAULT_MONTHLY_BUDGET)
        transaction = next(
            tx
            for tx in load_fixture_transactions("chase_debit.csv", "debit_demo")
            if tx.description == "CARD PURCHASE COFFEE"
        )

        categorized_transaction = categorize_transaction(transaction, rules)

        self.assertEqual(categorized_transaction.bucket, "wants")
        self.assertEqual(categorized_transaction.category, "restaurants")
        self.assertEqual(categorized_transaction.matched_rule_id, "debit_coffee")
        self.assertIsNotNone(categorized_transaction.matched_rule)
        self.assertEqual(categorized_transaction.matched_rule.id, "debit_coffee")
        self.assertEqual(categorized_transaction.matched_rule.bucket, "wants")
        self.assertEqual(
            categorized_transaction.matched_on,
            ("account=debit_demo", "description_contains='COFFEE'"),
        )

    def test_categorized_result_exposes_matched_rule_metadata(self) -> None:
        rules = load_category_rules(RULES_FIXTURE, DEFAULT_MONTHLY_BUDGET)
        transaction = next(
            tx
            for tx in load_fixture_transactions("chase_credit.csv", "credit_demo")
            if tx.description == "DENTAL OFFICE VISIT"
        )

        categorized_transaction = categorize_transaction(transaction, rules)

        self.assertIsNotNone(categorized_transaction.matched_rule)
        self.assertEqual(categorized_transaction.matched_rule.id, "credit_health")
        self.assertEqual(categorized_transaction.bucket, "needs")
        self.assertEqual(categorized_transaction.category, "pharmacy_medical")
        self.assertEqual(
            categorized_transaction.matched_rule.details,
            ("Health & Wellness",),
        )
        self.assertEqual(
            categorized_transaction.matched_on,
            ("account=credit_demo", "details='Health & Wellness'"),
        )

    def test_overlapping_rules_use_first_match_for_debit_transactions(self) -> None:
        rules = load_category_rules(RULES_FIXTURE, DEFAULT_MONTHLY_BUDGET)
        coffee_transaction = next(
            tx
            for tx in load_fixture_transactions("chase_debit.csv", "debit_demo")
            if tx.description == "CARD PURCHASE COFFEE"
        )

        categorized_transaction = categorize_transaction(coffee_transaction, rules)

        self.assertEqual(categorized_transaction.bucket, "wants")
        self.assertEqual(categorized_transaction.category, "restaurants")
        self.assertEqual(categorized_transaction.matched_rule_id, "debit_coffee")

    def test_overlapping_rules_use_first_match_for_venmo_income(self) -> None:
        rules = load_category_rules(RULES_FIXTURE, DEFAULT_MONTHLY_BUDGET)
        reimbursement_transaction = next(
            tx
            for tx in load_fixture_transactions("venmo.csv", "venmo")
            if tx.description == "Dinner reimbursement"
        )

        categorized_transaction = categorize_transaction(reimbursement_transaction, rules)

        self.assertEqual(categorized_transaction.bucket, "income")
        self.assertEqual(categorized_transaction.category, "reimbursement")
        self.assertEqual(
            categorized_transaction.matched_rule_id,
            "venmo_reimbursement",
        )
        self.assertEqual(
            categorized_transaction.matched_on,
            ("venmo_reimbursement=true", "account=venmo"),
        )

    def test_unmatched_transactions_fall_back_to_uncategorized_bucket(self) -> None:
        transaction = Transaction(
            account="debit_demo",
            source_file=Path("data/raw/debit_demo/2026/march.csv"),
            posting_date="03/20/2026",
            description="UNKNOWN PURCHASE",
            amount=Decimal("-12.34"),
            source_metadata={
                "details": "DEBIT",
                "transaction_type": "DEBIT_CARD",
            },
        )

        categorized_transaction = categorize_transaction(transaction, [])

        self.assertEqual(categorized_transaction.bucket, UNCATEGORIZED_BUCKET)
        self.assertEqual(categorized_transaction.category, UNCATEGORIZED_CATEGORY)

    def test_credit_card_payment_rule_matches_explicit_flag(self) -> None:
        rules = load_category_rules(RULES_FIXTURE, DEFAULT_MONTHLY_BUDGET)
        payment_transaction = next(
            tx
            for tx in load_fixture_transactions("chase_credit.csv", "credit_demo")
            if tx.description == "AUTOMATIC PAYMENT - THANK"
        )

        categorized_transaction = categorize_transaction(payment_transaction, rules)

        self.assertEqual(
            categorized_transaction.category,
            "credit_card_payment",
        )
        self.assertEqual(categorized_transaction.matched_rule_id, "credit_card_payment")
        self.assertEqual(
            categorized_transaction.matched_on,
            ("credit_card_payment=true", "account=credit_demo"),
        )

    def test_amount_specific_rule_can_distinguish_shared_payee(self) -> None:
        config_path = write_rules_file(
            (
                "[[rules]]\n"
                'id = "zelle_example_rent"\n'
                'category = "rent"\n'
                'bucket = "needs"\n'
                'accounts = ["debit_demo"]\n'
                'amounts = ["-1000.00"]\n'
                'description_contains = ["Zelle payment to Example Recipient"]\n'
                "\n"
                "[[rules]]\n"
                'id = "zelle_example_utilities"\n'
                'category = "utilities"\n'
                'bucket = "needs"\n'
                'accounts = ["debit_demo"]\n'
                'description_contains = ["Zelle payment to Example Recipient"]\n'
            )
        )
        rules = load_category_rules(config_path, DEFAULT_MONTHLY_BUDGET)
        rent_transaction = Transaction(
            account="debit_demo",
            source_file=Path("data/raw/debit_demo/2026/april.csv"),
            posting_date="04/01/2026",
            description="Zelle payment to Example Recipient DEMO_REFERENCE",
            amount=Decimal("-1000.00"),
            source_metadata={"details": "DEBIT", "transaction_type": "ZELLE"},
        )
        utilities_transaction = Transaction(
            account="debit_demo",
            source_file=Path("data/raw/debit_demo/2026/april.csv"),
            posting_date="04/15/2026",
            description="Zelle payment to Example Recipient DEMO_REFERENCE",
            amount=Decimal("-75.00"),
            source_metadata={"details": "DEBIT", "transaction_type": "ZELLE"},
        )

        rent_result = categorize_transaction(rent_transaction, rules)
        utilities_result = categorize_transaction(utilities_transaction, rules)

        self.assertEqual(rent_result.category, "rent")
        self.assertEqual(rent_result.matched_rule_id, "zelle_example_rent")
        self.assertEqual(
            rent_result.matched_on,
            (
                "account=debit_demo",
                "amount=-1000.00",
                "description_contains='Zelle payment to Example Recipient'",
            ),
        )
        self.assertEqual(utilities_result.category, "utilities")
        self.assertEqual(
            utilities_result.matched_rule_id,
            "zelle_example_utilities",
        )

    def test_internal_transfer_rule_matches_explicit_flag(self) -> None:
        rules = load_category_rules(RULES_FIXTURE, DEFAULT_MONTHLY_BUDGET)
        transaction = Transaction(
            account="debit_demo",
            source_file=Path("data/raw/debit_demo/2026/april.csv"),
            posting_date="04/05/2026",
            description="ONLINE TRANSFER TO SAVINGS",
            amount=Decimal("-250.00"),
            source_metadata={
                "details": "TRANSFER",
                "transaction_type": "TRANSFER",
            },
        )

        categorized_transaction = categorize_transaction(transaction, rules)

        self.assertEqual(categorized_transaction.category, "internal_transfer")
        self.assertEqual(categorized_transaction.matched_rule_id, "internal_transfer")
        self.assertEqual(
            categorized_transaction.matched_on,
            ("internal_transfer=true",),
        )

    def test_unmatched_transactions_return_uncategorized_result(self) -> None:
        rules = load_category_rules(RULES_FIXTURE, DEFAULT_MONTHLY_BUDGET)
        merchant_transaction = next(
            tx
            for tx in load_fixture_transactions("venmo.csv", "venmo")
            if tx.description == "Merchant Transaction"
        )

        categorized_transaction = categorize_transaction(merchant_transaction, rules)

        self.assertIs(categorized_transaction.transaction, merchant_transaction)
        self.assertEqual(categorized_transaction.category, UNCATEGORIZED_CATEGORY)
        self.assertIsNone(categorized_transaction.matched_rule_id)
        self.assertIsNone(categorized_transaction.matched_rule)
        self.assertEqual(categorized_transaction.matched_on, ())


if __name__ == "__main__":
    unittest.main()
