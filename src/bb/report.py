from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal

from bb.category import (
    UNCATEGORIZED_CATEGORY,
    UNCATEGORIZED_BUCKET,
    CategorizedTransaction,
)
from bb.config import MonthlyBudgetConfig
from bb.format import format_currency


def format_reporting_month(year: int, month: str | int) -> str:
    if isinstance(month, int):
        return f"{year}-{month:02d}"

    normalized = month.strip()
    if normalized.isdigit():
        return f"{year}-{int(normalized):02d}"

    month_number = {
        "january": 1,
        "february": 2,
        "march": 3,
        "april": 4,
        "may": 5,
        "june": 6,
        "july": 7,
        "august": 8,
        "september": 9,
        "october": 10,
        "november": 11,
        "december": 12,
    }[normalized.lower()]
    return f"{year}-{month_number:02d}"


def print_categorization_report(
    categorized_transactions: list[CategorizedTransaction],
) -> None:
    print("Categorization report")
    for categorized_transaction in categorized_transactions:
        transaction = categorized_transaction.transaction
        matched_rule_id = categorized_transaction.matched_rule_id or "-"
        category_label = format_category_label(categorized_transaction.category)
        print(
            f"{transaction.posting_date}  "
            f"{format_signed_currency(transaction.amount):>10}  "
            f"{transaction.account:<10}  {category_label:<30}"
            f"{matched_rule_id:<13}  {transaction.description}"
        )


def compute_total_monthly_income(
    categorized_transactions: list[CategorizedTransaction],
) -> Decimal:
    return sum(
        (
            categorized_transaction.transaction.amount
            for categorized_transaction in categorized_transactions
            if categorized_transaction.transaction.is_income
        ),
        start=Decimal("0"),
    )


def compute_total_spend_by_budget_bucket(
    categorized_transactions: list[CategorizedTransaction],
) -> dict[str, Decimal]:
    spend_by_bucket: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    for categorized_transaction in categorized_transactions:
        amount = categorized_transaction.transaction.amount
        if amount >= 0 or categorized_transaction.bucket == UNCATEGORIZED_BUCKET:
            continue
        spend_by_bucket[categorized_transaction.bucket] += abs(amount)
    return dict(spend_by_bucket)


def compute_total_spend_by_category_within_bucket(
    categorized_transactions: list[CategorizedTransaction],
) -> dict[str, dict[str, Decimal]]:
    spend_by_bucket: dict[str, dict[str, Decimal]] = defaultdict(
        lambda: defaultdict(lambda: Decimal("0"))
    )
    for categorized_transaction in categorized_transactions:
        amount = categorized_transaction.transaction.amount
        if amount >= 0 or categorized_transaction.bucket == UNCATEGORIZED_BUCKET:
            continue
        spend_by_bucket[categorized_transaction.bucket][
            categorized_transaction.category
        ] += abs(amount)
    return {
        bucket: dict(spend_by_category)
        for bucket, spend_by_category in spend_by_bucket.items()
    }


def compute_total_uncategorized_spend(
    categorized_transactions: list[CategorizedTransaction],
) -> Decimal:
    return sum(
        (
            abs(categorized_transaction.transaction.amount)
            for categorized_transaction in categorized_transactions
            if categorized_transaction.transaction.amount < 0
            and categorized_transaction.bucket == UNCATEGORIZED_BUCKET
        ),
        start=Decimal("0"),
    )


@dataclass(frozen=True)
class BudgetBucketPercentageComparison:
    bucket: str
    target_fraction: Decimal
    actual_fraction: Decimal | None
    difference_fraction: Decimal | None
    actual_spend: Decimal
    monthly_income: Decimal
    has_income: bool


def compute_budget_bucket_percentage_comparison(
    bucket: str,
    target_fraction: float,
    actual_spend: Decimal,
    monthly_income: Decimal,
) -> BudgetBucketPercentageComparison:
    target_fraction_decimal = Decimal(str(target_fraction))
    if monthly_income == 0:
        return BudgetBucketPercentageComparison(
            bucket=bucket,
            target_fraction=target_fraction_decimal,
            actual_fraction=None,
            difference_fraction=None,
            actual_spend=actual_spend,
            monthly_income=monthly_income,
            has_income=False,
        )

    actual_fraction = actual_spend / monthly_income
    return BudgetBucketPercentageComparison(
        bucket=bucket,
        target_fraction=target_fraction_decimal,
        actual_fraction=actual_fraction,
        difference_fraction=actual_fraction - target_fraction_decimal,
        actual_spend=actual_spend,
        monthly_income=monthly_income,
        has_income=True,
    )


def compute_budget_target_vs_actual_percentages(
    categorized_transactions: list[CategorizedTransaction],
    monthly_budget: MonthlyBudgetConfig,
) -> dict[str, BudgetBucketPercentageComparison]:
    monthly_income = compute_total_monthly_income(categorized_transactions)
    spend_by_bucket = compute_total_spend_by_budget_bucket(categorized_transactions)
    bucket_targets = {
        "needs": monthly_budget.needs.frac,
        "wants": monthly_budget.wants.frac,
        "savings": monthly_budget.savings.frac,
    }
    return {
        bucket: compute_budget_bucket_percentage_comparison(
            bucket=bucket,
            target_fraction=target_fraction,
            actual_spend=spend_by_bucket.get(bucket, Decimal("0")),
            monthly_income=monthly_income,
        )
        for bucket, target_fraction in bucket_targets.items()
    }


def format_monthly_budget_summary(
    categorized_transactions: list[CategorizedTransaction],
    monthly_budget: MonthlyBudgetConfig,
    *,
    include_uncategorized_transactions: bool = False,
) -> str:
    reporting_month = format_reporting_month(monthly_budget.year, monthly_budget.month)
    total_income = compute_total_monthly_income(categorized_transactions)
    comparisons = compute_budget_target_vs_actual_percentages(
        categorized_transactions,
        monthly_budget,
    )
    spend_by_category = compute_total_spend_by_category_within_bucket(
        categorized_transactions
    )
    uncategorized_spend = compute_total_uncategorized_spend(categorized_transactions)

    lines = [
        f"Monthly budget summary for {reporting_month}",
        f"Income: {format_currency(total_income)}",
    ]
    for bucket in ("needs", "wants", "savings"):
        comparison = comparisons[bucket]
        target_text = format_percentage(comparison.target_fraction)
        actual_text = (
            format_percentage(comparison.actual_fraction)
            if comparison.actual_fraction is not None
            else "n/a"
        )
        lines.append(
            f"{format_category_label(bucket)}: "
            f"target {target_text}  actual {actual_text}  "
            f"total {format_currency(comparison.actual_spend)}"
        )
        for category, total in sorted(spend_by_category.get(bucket, {}).items()):
            lines.append(
                f"  - {format_category_label(category)}: {format_currency(total)}"
            )

    if include_uncategorized_transactions:
        lines.append(
            f"Uncategorized spend: {format_currency(uncategorized_spend)}"
        )
        for categorized_transaction in categorized_transactions:
            amount = categorized_transaction.transaction.amount
            if (
                categorized_transaction.bucket == UNCATEGORIZED_BUCKET
                and categorized_transaction.category == UNCATEGORIZED_CATEGORY
                and amount < 0
            ):
                transaction = categorized_transaction.transaction
                lines.append(
                    f"  - {transaction.posting_date}  "
                    f"{format_signed_currency(amount)}  {transaction.description}"
                )
    elif uncategorized_spend > 0:
        lines.append(f"Uncategorized spend: {format_currency(uncategorized_spend)}")

    return "\n".join(lines)


def print_monthly_budget_summary(
    categorized_transactions: list[CategorizedTransaction],
    monthly_budget: MonthlyBudgetConfig,
    *,
    include_uncategorized_transactions: bool = False,
) -> None:
    print(
        format_monthly_budget_summary(
            categorized_transactions,
            monthly_budget,
            include_uncategorized_transactions=include_uncategorized_transactions,
        )
    )


def format_signed_currency(amount: Decimal) -> str:
    absolute_amount = abs(amount)
    if amount < 0:
        return f"-${absolute_amount:,.2f}"
    return f"${absolute_amount:,.2f}"


def format_category_label(category: str) -> str:
    return category.replace("_", " ").title()


def format_percentage(fraction: Decimal) -> str:
    return f"{(fraction * Decimal('100')):.1f}%"
