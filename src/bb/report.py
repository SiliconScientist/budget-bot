from __future__ import annotations

from decimal import Decimal

from bb.format import format_currency
from bb.category import CategorizedTransaction
from bb.transaction import Transaction


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


def print_income_report(
    reporting_year: int,
    reporting_month: str | int,
    income_transactions: list[Transaction],
) -> None:
    total_income = sum((tx.amount for tx in income_transactions), start=Decimal("0"))
    reporting_period = format_reporting_month(reporting_year, reporting_month)

    print(f"Income for {reporting_period}: {format_currency(total_income)}")
    for tx in income_transactions:
        print(
            f"{tx.posting_date}  {format_currency(tx.amount):>10}  "
            f"{tx.account:<10}  {tx.description}"
        )


def print_categorization_report(
    categorized_transactions: list[CategorizedTransaction],
) -> None:
    print("Categorization report")
    for categorized_transaction in categorized_transactions:
        transaction = categorized_transaction.transaction
        matched_rule_id = categorized_transaction.matched_rule_id or "-"
        print(
            f"{transaction.posting_date}  "
            f"{format_signed_currency(transaction.amount):>10}  "
            f"{transaction.account:<10}  {categorized_transaction.category:<30}"
            f"{matched_rule_id:<13}  {transaction.description}"
        )


def format_signed_currency(amount: Decimal) -> str:
    absolute_amount = abs(amount)
    if amount < 0:
        return f"-${absolute_amount:,.2f}"
    return f"${absolute_amount:,.2f}"
