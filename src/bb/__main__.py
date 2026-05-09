from __future__ import annotations

from decimal import Decimal

from bb.category import categorize_transactions, load_category_rules
from bb.config import get_category_config_path, get_config
from bb.format import format_currency
from bb.report import format_reporting_month, print_categorization_report
from bb.transaction import filter_transactions_by_month, load_all_transactions


def main() -> None:
    cfg = get_config()
    all_transactions = load_all_transactions(cfg.raw_data_path)
    monthly_transactions = filter_transactions_by_month(
        all_transactions,
        cfg.monthly_budget.year,
        cfg.monthly_budget.month,
    )
    income_transactions = [tx for tx in monthly_transactions if tx.is_income]
    total_income = sum((tx.amount for tx in income_transactions), start=Decimal("0"))
    reporting_period = format_reporting_month(
        cfg.monthly_budget.year,
        cfg.monthly_budget.month,
    )

    print(f"Income for {reporting_period}: {format_currency(total_income)}")
    for tx in income_transactions:
        print(
            f"{tx.posting_date}  {format_currency(tx.amount):>10}  "
            f"{tx.account:<10}  {tx.description}"
        )
    print()
    category_rules = load_category_rules(
        get_category_config_path(),
        cfg.monthly_budget,
    )
    print_categorization_report(
        categorize_transactions(all_transactions, category_rules)
    )


if __name__ == "__main__":
    main()
