from __future__ import annotations

from bb.category import categorize_transactions, load_category_rules
from bb.config import get_category_config_path, get_config
from bb.report import print_categorization_report, print_monthly_budget_summary
from bb.transaction import filter_transactions_by_month, load_all_transactions


def main() -> None:
    cfg = get_config()
    all_transactions = load_all_transactions(cfg.raw_data_path)
    monthly_transactions = filter_transactions_by_month(
        all_transactions,
        cfg.monthly_budget.year,
        cfg.monthly_budget.month,
    )
    category_rules = load_category_rules(
        get_category_config_path(),
        cfg.monthly_budget,
    )
    categorized_monthly_transactions = categorize_transactions(
        monthly_transactions,
        category_rules,
    )

    print_monthly_budget_summary(
        categorized_monthly_transactions,
        cfg.monthly_budget,
    )
    # print_categorization_report(categorized_monthly_transactions)


if __name__ == "__main__":
    main()
