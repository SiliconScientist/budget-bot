from __future__ import annotations

from pathlib import Path

from bb.category import categorize_transactions, load_category_rules
from bb.config import get_config
from bb.report import print_categorization_report, print_income_report
from bb.transaction import load_all_transactions, load_income_transactions


CATEGORY_CONFIG_PATH = Path(__file__).resolve().parents[2] / "category.toml"


def main() -> None:
    cfg = get_config()
    income_transactions = load_income_transactions(
        cfg.raw_data_path,
        cfg.monthly_budget,
    )
    print_income_report(
        cfg.monthly_budget.year,
        cfg.monthly_budget.month,
        income_transactions,
    )
    print()
    all_transactions = load_all_transactions(cfg.raw_data_path)
    category_rules = load_category_rules(CATEGORY_CONFIG_PATH)
    print_categorization_report(categorize_transactions(all_transactions, category_rules))


if __name__ == "__main__":
    main()
