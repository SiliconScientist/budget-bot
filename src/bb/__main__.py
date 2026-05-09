from __future__ import annotations

from bb.config import get_config
from bb.report import print_income_report
from bb.transactions import load_income_transactions


def main() -> None:
    cfg = get_config()
    income_transactions = load_income_transactions(cfg.raw_data_path)
    print_income_report(income_transactions)


if __name__ == "__main__":
    main()
