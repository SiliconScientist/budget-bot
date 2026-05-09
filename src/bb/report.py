from __future__ import annotations

from decimal import Decimal

from bb.format import format_currency
from bb.category import CategorizedTransaction


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


def format_signed_currency(amount: Decimal) -> str:
    absolute_amount = abs(amount)
    if amount < 0:
        return f"-${absolute_amount:,.2f}"
    return f"${absolute_amount:,.2f}"


def format_category_label(category: str) -> str:
    return category.replace("_", " ").title()
