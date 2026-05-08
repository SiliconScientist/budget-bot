from __future__ import annotations

from bb.config import get_config
from bb.report import print_income_report


def main() -> None:
    cfg = get_config()
    print_income_report(cfg)


if __name__ == "__main__":
    main()
