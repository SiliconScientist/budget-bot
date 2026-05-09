from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from bb.transaction import Transaction


@dataclass(frozen=True)
class CategoryRule:
    id: str
    category: str
    accounts: tuple[str, ...] = ()
    description_contains: tuple[str, ...] = ()
    details: tuple[str, ...] = ()
    transaction_types: tuple[str, ...] = ()
    is_income: bool | None = None


@dataclass(frozen=True)
class CategorizedTransaction:
    transaction: Transaction
    category: str | None
    matched_rule_id: str | None


def load_category_rules(config_path: Path) -> list[CategoryRule]:
    raise NotImplementedError("Category rule loading is not implemented yet")


def categorize_transaction(
    transaction: Transaction,
    rules: Sequence[CategoryRule],
) -> CategorizedTransaction:
    raise NotImplementedError("Transaction categorization is not implemented yet")
