from __future__ import annotations

import csv
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Mapping


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


def load_transactions(account_dir: Path) -> list[Transaction]:
    transactions: list[Transaction] = []

    for csv_file in sorted(account_dir.glob("*.csv")):
        with csv_file.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                transactions.append(
                    Transaction(
                        account=account_dir.name,
                        source_file=csv_file,
                        posting_date=row["Posting Date"],
                        description=row["Description"],
                        amount=Decimal(row["Amount"]),
                        source_metadata={
                            "details": row["Details"],
                            "transaction_type": row["Type"],
                        },
                    )
                )

    return transactions


def load_income_transactions(raw_data_dir: Path, account_name: str) -> list[Transaction]:
    account_dir = raw_data_dir / account_name
    return [tx for tx in load_transactions(account_dir) if tx.is_income]
