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

CHASE_CREDIT_COLUMNS = (
    "Transaction Date",
    "Post Date",
    "Description",
    "Category",
    "Type",
    "Amount",
    "Memo",
)

VENMO_COLUMNS = (
    "",
    "ID",
    "Datetime",
    "Type",
    "Status",
    "Note",
    "From",
    "To",
    "Amount (total)",
    "Amount (tip)",
    "Amount (tax)",
    "Amount (fee)",
    "Tax Rate",
    "Tax Exempt",
    "Funding Source",
    "Destination",
    "Beginning Balance",
    "Ending Balance",
    "Statement Period Venmo Fees",
    "Terminal Location",
    "Year to Date Venmo Fees",
    "Disclaimer",
)

VENMO_COMPLETED_STATUS = "Complete"


def is_chase_debit_statement(fieldnames: list[str] | None) -> bool:
    return fieldnames == list(CHASE_DEBIT_COLUMNS)


def is_chase_credit_statement(fieldnames: list[str] | None) -> bool:
    return fieldnames == list(CHASE_CREDIT_COLUMNS)


def is_venmo_statement(fieldnames: list[str] | None) -> bool:
    return fieldnames == list(VENMO_COLUMNS)


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


def parse_chase_credit_rows(
    account_name: str,
    source_file: Path,
    rows: Iterable[CsvRow],
) -> list[Transaction]:
    return [
        Transaction(
            account=account_name,
            source_file=source_file,
            posting_date=row["Post Date"],
            description=row["Description"],
            amount=Decimal(row["Amount"]),
            source_metadata={
                "details": row["Category"],
                "transaction_date": row["Transaction Date"],
                "transaction_type": row["Type"],
                "memo": row["Memo"],
            },
        )
        for row in rows
    ]


def parse_venmo_amount(raw_amount: str) -> Decimal:
    normalized = raw_amount.replace("$", "").replace(",", "").replace(" ", "")
    return Decimal(normalized)


def parse_venmo_rows(
    account_name: str,
    source_file: Path,
    rows: Iterable[CsvRow],
) -> list[Transaction]:
    transactions: list[Transaction] = []

    for row in rows:
        if not row["ID"] or row["Status"] != VENMO_COMPLETED_STATUS:
            continue

        note = row["Note"] or row["Type"]
        transactions.append(
            Transaction(
                account=account_name,
                source_file=source_file,
                posting_date=row["Datetime"].split("T", 1)[0],
                description=note,
                amount=parse_venmo_amount(row["Amount (total)"]),
                source_metadata={
                    "details": row["Status"],
                    "transaction_type": row["Type"],
                    "venmo_id": row["ID"],
                    "from": row["From"],
                    "to": row["To"],
                    "funding_source": row["Funding Source"],
                    "destination": row["Destination"],
                },
            )
        )

    return transactions


def get_statement_parser(fieldnames: list[str] | None) -> StatementParser:
    if is_chase_debit_statement(fieldnames):
        return parse_chase_debit_rows
    if is_chase_credit_statement(fieldnames):
        return parse_chase_credit_rows
    if is_venmo_statement(fieldnames):
        return parse_venmo_rows

    raise UnsupportedStatementFormat(f"Unsupported statement columns: {fieldnames}")


def is_supported_statement_header(row: list[str]) -> bool:
    return row in (
        list(CHASE_DEBIT_COLUMNS),
        list(CHASE_CREDIT_COLUMNS),
        list(VENMO_COLUMNS),
    )


def read_statement_rows(csv_file: Path) -> tuple[list[str] | None, list[CsvRow]]:
    with csv_file.open(newline="", encoding="utf-8-sig") as handle:
        lines = handle.readlines()

    header_row_index = 0
    for index, row in enumerate(csv.reader(lines)):
        if is_supported_statement_header(row):
            header_row_index = index
            break

    reader = csv.DictReader(lines[header_row_index:])
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
