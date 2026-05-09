from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Callable, Iterable, Mapping

@dataclass(frozen=True)
class Transaction:
    """Normalized transaction shape shared by all importers.

    Every importer must provide the universal fields below. Any source-specific
    data belongs in ``source_metadata``.
    """

    account: str
    source_file: Path
    posting_date: str
    description: str
    amount: Decimal
    source_metadata: Mapping[str, str]

    @property
    def is_income(self) -> bool:
        return self.amount > 0

    @property
    def posting_date_value(self) -> date:
        for fmt in ("%m/%d/%Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(self.posting_date, fmt).date()
            except ValueError:
                pass
        raise ValueError(f"Unsupported posting date format: {self.posting_date}")

    @property
    def posting_year(self) -> int:
        return self.posting_date_value.year

    @property
    def posting_month(self) -> int:
        return self.posting_date_value.month


CsvRow = dict[str, str]
StatementParser = Callable[[str, Path, Iterable[CsvRow]], list[Transaction]]

from bb.parse import (
    get_expected_columns,
    get_statement_parser,
    read_statement_rows,
    validate_statement_columns,
)


MONTH_NAME_TO_NUMBER = {
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
}


def load_transactions(account_dir: Path) -> list[Transaction]:
    transactions: list[Transaction] = []
    parser = get_statement_parser(account_dir.name)
    expected_columns = get_expected_columns(account_dir.name)
    for csv_file in sorted(account_dir.rglob("*.csv")):
        fieldnames, rows = read_statement_rows(csv_file, expected_columns)
        validate_statement_columns(account_dir.name, fieldnames)
        transactions.extend(parser(account_dir.name, csv_file, rows))
    return transactions


def load_all_transactions(raw_data_dir: Path) -> list[Transaction]:
    transactions: list[Transaction] = []

    for account_dir in sorted(path for path in raw_data_dir.iterdir() if path.is_dir()):
        transactions.extend(load_transactions(account_dir))

    return transactions


def parse_month_name(month_name: str | int) -> int:
    if isinstance(month_name, int):
        if 1 <= month_name <= 12:
            return month_name
        raise ValueError(f"Unsupported month number: {month_name}")

    normalized = month_name.strip().lower()
    if normalized.isdigit():
        month_number = int(normalized)
        if 1 <= month_number <= 12:
            return month_number
        raise ValueError(f"Unsupported month number: {month_name}")

    try:
        return MONTH_NAME_TO_NUMBER[normalized]
    except KeyError as exc:
        raise ValueError(f"Unsupported month name: {month_name}") from exc


def filter_transactions_by_month(
    transactions: Iterable[Transaction],
    year: int,
    month_name: str | int,
) -> list[Transaction]:
    month = parse_month_name(month_name)
    return [
        tx
        for tx in transactions
        if tx.posting_year == year and tx.posting_month == month
    ]
