from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout
from decimal import Decimal
from pathlib import Path

from bb.category import CategorizedTransaction, CategoryRule, UNCATEGORIZED_CATEGORY
from bb.format import format_currency
from bb.report import (
    compute_total_monthly_income,
    compute_total_spend_by_budget_bucket,
    compute_total_spend_by_category_within_bucket,
    compute_total_uncategorized_spend,
    format_category_label,
    format_reporting_month,
    print_categorization_report,
)
from bb.transaction import Transaction


class ReportTests(unittest.TestCase):
    def test_compute_total_monthly_income_sums_income_transactions(self) -> None:
        categorized_transactions = [
            CategorizedTransaction(
                transaction=Transaction(
                    account="debit_demo",
                    source_file=Path("data/raw/debit_demo/2026/march.csv"),
                    posting_date="03/01/2026",
                    description="PAYROLL",
                    amount=Decimal("1200.00"),
                    source_metadata={"details": "CREDIT", "transaction_type": "ACH"},
                ),
                bucket="income",
                category="paycheck",
                matched_rule_id="paycheck_income",
                matched_rule=None,
                matched_on=(),
            ),
            CategorizedTransaction(
                transaction=Transaction(
                    account="venmo",
                    source_file=Path("data/raw/venmo/2026/march.csv"),
                    posting_date="2026-03-02",
                    description="Reimbursement",
                    amount=Decimal("12.34"),
                    source_metadata={
                        "details": "Complete",
                        "transaction_type": "Payment",
                    },
                ),
                bucket="income",
                category="reimbursement",
                matched_rule_id="venmo_reimbursement",
                matched_rule=None,
                matched_on=(),
            ),
            CategorizedTransaction(
                transaction=Transaction(
                    account="debit_demo",
                    source_file=Path("data/raw/debit_demo/2026/march.csv"),
                    posting_date="03/03/2026",
                    description="Groceries",
                    amount=Decimal("-45.67"),
                    source_metadata={
                        "details": "DEBIT",
                        "transaction_type": "DEBIT_CARD",
                    },
                ),
                bucket="needs",
                category="groceries",
                matched_rule_id="groceries",
                matched_rule=None,
                matched_on=(),
            ),
        ]

        self.assertEqual(
            compute_total_monthly_income(categorized_transactions),
            Decimal("1212.34"),
        )

    def test_compute_total_spend_by_budget_bucket_groups_negative_amounts(self) -> None:
        categorized_transactions = [
            CategorizedTransaction(
                transaction=Transaction(
                    account="debit_demo",
                    source_file=Path("data/raw/debit_demo/2026/march.csv"),
                    posting_date="03/03/2026",
                    description="Groceries",
                    amount=Decimal("-45.67"),
                    source_metadata={},
                ),
                bucket="needs",
                category="groceries",
                matched_rule_id="groceries",
                matched_rule=None,
                matched_on=(),
            ),
            CategorizedTransaction(
                transaction=Transaction(
                    account="credit_demo",
                    source_file=Path("data/raw/credit_demo/2026/march.csv"),
                    posting_date="03/04/2026",
                    description="Doctor",
                    amount=Decimal("-20.00"),
                    source_metadata={},
                ),
                bucket="needs",
                category="pharmacy_medical",
                matched_rule_id="health",
                matched_rule=None,
                matched_on=(),
            ),
            CategorizedTransaction(
                transaction=Transaction(
                    account="credit_demo",
                    source_file=Path("data/raw/credit_demo/2026/march.csv"),
                    posting_date="03/05/2026",
                    description="Movie",
                    amount=Decimal("-15.00"),
                    source_metadata={},
                ),
                bucket="wants",
                category="movies",
                matched_rule_id="movies",
                matched_rule=None,
                matched_on=(),
            ),
            CategorizedTransaction(
                transaction=Transaction(
                    account="venmo",
                    source_file=Path("data/raw/venmo/2026/march.csv"),
                    posting_date="2026-03-06",
                    description="Unknown",
                    amount=Decimal("-8.00"),
                    source_metadata={},
                ),
                bucket="uncategorized",
                category=UNCATEGORIZED_CATEGORY,
                matched_rule_id=None,
                matched_rule=None,
                matched_on=(),
            ),
        ]

        self.assertEqual(
            compute_total_spend_by_budget_bucket(categorized_transactions),
            {
                "needs": Decimal("65.67"),
                "wants": Decimal("15.00"),
            },
        )

    def test_compute_total_spend_by_category_within_bucket_groups_nested_totals(
        self,
    ) -> None:
        categorized_transactions = [
            CategorizedTransaction(
                transaction=Transaction(
                    account="debit_demo",
                    source_file=Path("data/raw/debit_demo/2026/march.csv"),
                    posting_date="03/03/2026",
                    description="Groceries",
                    amount=Decimal("-45.67"),
                    source_metadata={},
                ),
                bucket="needs",
                category="groceries",
                matched_rule_id="groceries_a",
                matched_rule=None,
                matched_on=(),
            ),
            CategorizedTransaction(
                transaction=Transaction(
                    account="debit_demo",
                    source_file=Path("data/raw/debit_demo/2026/march.csv"),
                    posting_date="03/07/2026",
                    description="More Groceries",
                    amount=Decimal("-10.00"),
                    source_metadata={},
                ),
                bucket="needs",
                category="groceries",
                matched_rule_id="groceries_b",
                matched_rule=None,
                matched_on=(),
            ),
            CategorizedTransaction(
                transaction=Transaction(
                    account="credit_demo",
                    source_file=Path("data/raw/credit_demo/2026/march.csv"),
                    posting_date="03/04/2026",
                    description="Doctor",
                    amount=Decimal("-20.00"),
                    source_metadata={},
                ),
                bucket="needs",
                category="pharmacy_medical",
                matched_rule_id="health",
                matched_rule=None,
                matched_on=(),
            ),
            CategorizedTransaction(
                transaction=Transaction(
                    account="credit_demo",
                    source_file=Path("data/raw/credit_demo/2026/march.csv"),
                    posting_date="03/05/2026",
                    description="Movie",
                    amount=Decimal("-15.00"),
                    source_metadata={},
                ),
                bucket="wants",
                category="movies",
                matched_rule_id="movies",
                matched_rule=None,
                matched_on=(),
            ),
        ]

        self.assertEqual(
            compute_total_spend_by_category_within_bucket(categorized_transactions),
            {
                "needs": {
                    "groceries": Decimal("55.67"),
                    "pharmacy_medical": Decimal("20.00"),
                },
                "wants": {
                    "movies": Decimal("15.00"),
                },
            },
        )

    def test_compute_total_uncategorized_spend_sums_only_uncategorized_expenses(
        self,
    ) -> None:
        categorized_transactions = [
            CategorizedTransaction(
                transaction=Transaction(
                    account="venmo",
                    source_file=Path("data/raw/venmo/2026/march.csv"),
                    posting_date="2026-03-06",
                    description="Unknown",
                    amount=Decimal("-8.00"),
                    source_metadata={},
                ),
                bucket="uncategorized",
                category=UNCATEGORIZED_CATEGORY,
                matched_rule_id=None,
                matched_rule=None,
                matched_on=(),
            ),
            CategorizedTransaction(
                transaction=Transaction(
                    account="venmo",
                    source_file=Path("data/raw/venmo/2026/march.csv"),
                    posting_date="2026-03-07",
                    description="Paycheck",
                    amount=Decimal("10.00"),
                    source_metadata={},
                ),
                bucket="uncategorized",
                category=UNCATEGORIZED_CATEGORY,
                matched_rule_id=None,
                matched_rule=None,
                matched_on=(),
            ),
            CategorizedTransaction(
                transaction=Transaction(
                    account="debit_demo",
                    source_file=Path("data/raw/debit_demo/2026/march.csv"),
                    posting_date="03/03/2026",
                    description="Groceries",
                    amount=Decimal("-45.67"),
                    source_metadata={},
                ),
                bucket="needs",
                category="groceries",
                matched_rule_id="groceries",
                matched_rule=None,
                matched_on=(),
            ),
        ]

        self.assertEqual(
            compute_total_uncategorized_spend(categorized_transactions),
            Decimal("8.00"),
        )

    def test_format_reporting_month_shows_active_month_filter(self) -> None:
        self.assertEqual(format_reporting_month(2026, "february"), "2026-02")

    def test_income_summary_header_can_be_built_from_generic_helpers(self) -> None:
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

        total_income = sum((tx.amount for tx in income_transactions), start=Decimal("0"))
        header = (
            f"Income for {format_reporting_month(2026, 'february')}: "
            f"{format_currency(total_income)}"
        )

        self.assertEqual(header, "Income for 2026-02: $500.00")

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
                bucket="wants",
                category="coffee",
                matched_rule_id="debit_coffee",
                matched_rule=CategoryRule(
                    id="debit_coffee",
                    category="coffee",
                    bucket="wants",
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
                bucket="uncategorized",
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
            "03/20/2026     -$15.00  debit_demo   Coffee                        debit_coffee   CARD PURCHASE COFFEE",
        )
        self.assertEqual(
            lines[2],
            "2026-03-11     -$35.00  venmo       Uncategorized                 -              Merchant Transaction",
        )

    def test_format_category_label_uses_title_case_display_text(self) -> None:
        self.assertEqual(format_category_label("tuition_education"), "Tuition Education")


if __name__ == "__main__":
    unittest.main()
