from __future__ import annotations

import csv
from decimal import Decimal
from pathlib import Path
from typing import Iterable

from bb.transaction import CsvRow, StatementParser, Transaction


class UnsupportedStatementSource(ValueError):
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

CHASE_CREDIT_PAYMENT_TYPE = "Payment"

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
            amount=normalize_chase_credit_amount(row["Type"], row["Amount"]),
            source_metadata={
                "details": row["Category"],
                "transaction_date": row["Transaction Date"],
                "transaction_type": row["Type"],
                "memo": row["Memo"],
            },
        )
        for row in rows
    ]


def normalize_chase_credit_amount(transaction_type: str, raw_amount: str) -> Decimal:
    amount = Decimal(raw_amount)
    if transaction_type == CHASE_CREDIT_PAYMENT_TYPE:
        return -abs(amount)
    return amount


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


def get_statement_parser(account_name: str) -> StatementParser:
    if account_name.startswith("debit"):
        return parse_chase_debit_rows
    if account_name.startswith("credit"):
        return parse_chase_credit_rows
    if account_name == "venmo":
        return parse_venmo_rows

    raise UnsupportedStatementSource(f"Unsupported statement source: {account_name}")


def get_expected_columns(account_name: str) -> list[str]:
    if account_name.startswith("debit"):
        return list(CHASE_DEBIT_COLUMNS)
    if account_name.startswith("credit"):
        return list(CHASE_CREDIT_COLUMNS)
    if account_name == "venmo":
        return list(VENMO_COLUMNS)

    raise UnsupportedStatementSource(f"Unsupported statement source: {account_name}")


def read_statement_rows(
    csv_file: Path,
    expected_columns: list[str],
) -> tuple[list[str] | None, list[CsvRow]]:
    with csv_file.open(newline="", encoding="utf-8-sig") as handle:
        lines = handle.readlines()

    header_row_index = 0
    for index, row in enumerate(csv.reader(lines)):
        if row == expected_columns:
            header_row_index = index
            break

    reader = csv.DictReader(lines[header_row_index:])
    return reader.fieldnames, list(reader)


def validate_statement_columns(
    account_name: str,
    fieldnames: list[str] | None,
) -> None:
    expected_columns = get_expected_columns(account_name)
    if fieldnames != expected_columns:
        raise UnsupportedStatementSource(
            f"{account_name} expected columns {expected_columns}, got {fieldnames}"
        )
