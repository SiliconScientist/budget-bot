from __future__ import annotations

from decimal import Decimal

from bb.format import format_currency
from bb.transactions import Transaction


def print_income_report(account_name: str, income_transactions: list[Transaction]) -> None:
    total_income = sum((tx.amount for tx in income_transactions), start=Decimal("0"))

    print(f"Income for {account_name}: {format_currency(total_income)}")
    for tx in income_transactions:
        print(
            f"{tx.posting_date}  {format_currency(tx.amount):>10}  "
            f"{tx.transaction_type:<12}  {tx.description}"
        )
