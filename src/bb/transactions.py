from __future__ import annotations

import csv
from dataclasses import dataclass
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


CsvRow = dict[str, str]
StatementParser = Callable[[str, Path, Iterable[CsvRow]], list[Transaction]]


class UnsupportedStatementFormat(ValueError):
    pass


CHASE_DEBIT_COLUMNS = (
    "Details",
    "Posting Date",
    "Description",
    "Amount",
    "Type",
    "Balance",
    "Check or Slip #",
)


def is_chase_debit_statement(fieldnames: list[str] | None) -> bool:
    return fieldnames == list(CHASE_DEBIT_COLUMNS)


def parse_chase_debit_rows(
    account_name: str,
    source_file: Path,
    rows: Iterable[CsvRow],
) -> list[Transaction]:
    return [
        Transaction(
            account=account_name,
            source_file=source_file,
            posting_date=row["Posting Date"],
            description=row["Description"],
            amount=Decimal(row["Amount"]),
            source_metadata={
                "details": row["Details"],
                "transaction_type": row["Type"],
            },
        )
        for row in rows
    ]


def get_statement_parser(fieldnames: list[str] | None) -> StatementParser:
    if is_chase_debit_statement(fieldnames):
        return parse_chase_debit_rows

    raise UnsupportedStatementFormat(f"Unsupported statement columns: {fieldnames}")


def read_statement_rows(csv_file: Path) -> tuple[list[str] | None, list[CsvRow]]:
    with csv_file.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        return reader.fieldnames, list(reader)


def load_transactions(account_dir: Path) -> list[Transaction]:
    transactions: list[Transaction] = []

    for csv_file in sorted(account_dir.glob("*.csv")):
        fieldnames, rows = read_statement_rows(csv_file)
        parser = get_statement_parser(fieldnames)
        transactions.extend(parser(account_dir.name, csv_file, rows))

    return transactions


def load_income_transactions(raw_data_dir: Path, account_name: str) -> list[Transaction]:
    account_dir = raw_data_dir / account_name
    return [tx for tx in load_transactions(account_dir) if tx.is_income]
