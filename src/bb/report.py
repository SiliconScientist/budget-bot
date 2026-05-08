from __future__ import annotations

from decimal import Decimal

from bb.config import Config
from bb.format import format_currency
from bb.transactions import load_income_transactions


def print_income_report(cfg: Config) -> None:
    income_transactions = load_income_transactions(
        cfg.raw_data_dir,
        cfg.income_account,
    )
    total_income = sum((tx.amount for tx in income_transactions), start=Decimal("0"))

    print(f"Income for {cfg.income_account}: {format_currency(total_income)}")
    for tx in income_transactions:
        print(
            f"{tx.posting_date}  {format_currency(tx.amount):>10}  "
            f"{tx.transaction_type:<12}  {tx.description}"
        )
