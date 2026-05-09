from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Mapping, Sequence

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11 fallback
    import tomli as tomllib

from bb.config import MonthlyBudgetConfig
from bb.transaction import Transaction


UNCATEGORIZED_CATEGORY = "uncategorized"
UNCATEGORIZED_BUCKET = "uncategorized"
SNAKE_CASE_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")


@dataclass(frozen=True)
class CategoryRule:
    id: str
    category: str
    bucket: str | None = None
    counts_toward_income: bool = True
    amounts: tuple[Decimal, ...] = ()
    accounts: tuple[str, ...] = ()
    description_contains: tuple[str, ...] = ()
    details: tuple[str, ...] = ()
    transaction_types: tuple[str, ...] = ()
    is_income: bool | None = None
    credit_card_payment: bool = False
    venmo_reimbursement: bool = False
    internal_transfer: bool = False


@dataclass(frozen=True)
class CategorizedTransaction:
    transaction: Transaction
    category: str
    bucket: str
    matched_rule_id: str | None
    matched_rule: CategoryRule | None
    matched_on: tuple[str, ...]
    counts_toward_income: bool = True


class CategoryRuleConfigError(ValueError):
    pass


def load_category_rules(
    config_path: Path,
    monthly_budget: MonthlyBudgetConfig,
) -> list[CategoryRule]:
    with config_path.open("rb") as handle:
        config_data = tomllib.load(handle)

    rules_data = config_data.get("rules")
    if not isinstance(rules_data, list):
        raise CategoryRuleConfigError(
            "category rules file must contain a top-level 'rules' array"
        )

    rules: list[CategoryRule] = []
    seen_rule_ids: set[str] = set()
    for index, rule_data in enumerate(rules_data, start=1):
        if not isinstance(rule_data, dict):
            raise CategoryRuleConfigError(
                f"rules[{index}] must be a table of rule fields"
            )

        rule = parse_category_rule(rule_data, index, monthly_budget)
        if rule.id in seen_rule_ids:
            raise CategoryRuleConfigError(f"rules[{index}].id duplicates {rule.id!r}")
        seen_rule_ids.add(rule.id)
        rules.append(rule)

    return rules


def parse_category_rule(
    rule_data: Mapping[str, Any],
    index: int,
    monthly_budget: MonthlyBudgetConfig,
) -> CategoryRule:
    category = require_snake_case_identifier(rule_data, "category", index)
    bucket = require_optional_snake_case_identifier(rule_data, "bucket", index)
    try:
        validate_budget_bucket_category(monthly_budget, bucket, category)
    except ValueError as exc:
        raise CategoryRuleConfigError(f"rules[{index}] {exc}") from exc

    return CategoryRule(
        id=require_non_empty_string(rule_data, "id", index),
        category=category,
        bucket=bucket,
        counts_toward_income=require_bool_with_default(
            rule_data,
            "counts_toward_income",
            index,
            default=True,
        ),
        amounts=require_decimal_list(rule_data, "amounts", index),
        accounts=require_string_list(rule_data, "accounts", index),
        description_contains=require_string_list(
            rule_data,
            "description_contains",
            index,
        ),
        details=require_string_list(rule_data, "details", index),
        transaction_types=require_string_list(
            rule_data,
            "transaction_types",
            index,
        ),
        is_income=require_optional_bool(rule_data, "is_income", index),
        credit_card_payment=require_bool(rule_data, "credit_card_payment", index),
        venmo_reimbursement=require_bool(rule_data, "venmo_reimbursement", index),
        internal_transfer=require_bool(rule_data, "internal_transfer", index),
    )


def validate_budget_bucket_category(
    monthly_budget: MonthlyBudgetConfig,
    bucket: str | None,
    category: str,
) -> None:
    bucket_to_categories = monthly_budget.bucket_to_categories
    expected_bucket = next(
        (
            bucket_name
            for bucket_name, categories in bucket_to_categories.items()
            if category in categories
        ),
        None,
    )
    if expected_bucket is None:
        if bucket in bucket_to_categories:
            allowed_categories = ", ".join(sorted(bucket_to_categories[bucket]))
            raise ValueError(
                f"budget bucket {bucket!r} only allows categories: {allowed_categories}; "
                f"got {category!r}"
            )
        return

    if bucket != expected_bucket:
        raise ValueError(
            f"budget category {category!r} must use bucket {expected_bucket!r}, "
            f"got {bucket!r}"
        )


def require_non_empty_string(
    rule_data: Mapping[str, Any],
    field_name: str,
    index: int,
) -> str:
    value = rule_data.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise CategoryRuleConfigError(
            f"rules[{index}].{field_name} must be a non-empty string"
        )
    return value


def require_optional_non_empty_string(
    rule_data: Mapping[str, Any],
    field_name: str,
    index: int,
) -> str | None:
    value = rule_data.get(field_name)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise CategoryRuleConfigError(
            f"rules[{index}].{field_name} must be a non-empty string"
        )
    return value


def require_snake_case_identifier(
    rule_data: Mapping[str, Any],
    field_name: str,
    index: int,
) -> str:
    value = require_non_empty_string(rule_data, field_name, index)
    if not SNAKE_CASE_PATTERN.fullmatch(value):
        raise CategoryRuleConfigError(
            f"rules[{index}].{field_name} must be snake_case, got {value!r}"
        )
    return value


def require_optional_snake_case_identifier(
    rule_data: Mapping[str, Any],
    field_name: str,
    index: int,
) -> str | None:
    value = require_optional_non_empty_string(rule_data, field_name, index)
    if value is None:
        return None
    if not SNAKE_CASE_PATTERN.fullmatch(value):
        raise CategoryRuleConfigError(
            f"rules[{index}].{field_name} must be snake_case, got {value!r}"
        )
    return value


def require_string_list(
    rule_data: Mapping[str, Any],
    field_name: str,
    index: int,
) -> tuple[str, ...]:
    value = rule_data.get(field_name)
    if value is None:
        return ()
    if not isinstance(value, list):
        raise CategoryRuleConfigError(
            f"rules[{index}].{field_name} must be an array of strings"
        )
    if not all(isinstance(item, str) and item.strip() for item in value):
        raise CategoryRuleConfigError(
            f"rules[{index}].{field_name} must be an array of non-empty strings"
        )
    return tuple(value)


def require_decimal_list(
    rule_data: Mapping[str, Any],
    field_name: str,
    index: int,
) -> tuple[Decimal, ...]:
    value = rule_data.get(field_name)
    if value is None:
        return ()
    if not isinstance(value, list):
        raise CategoryRuleConfigError(
            f"rules[{index}].{field_name} must be an array of decimal strings"
        )

    decimals: list[Decimal] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise CategoryRuleConfigError(
                f"rules[{index}].{field_name} must be an array of non-empty decimal strings"
            )
        try:
            decimals.append(Decimal(item))
        except InvalidOperation as exc:
            raise CategoryRuleConfigError(
                f"rules[{index}].{field_name} must contain only decimal strings"
            ) from exc
    return tuple(decimals)


def require_optional_bool(
    rule_data: Mapping[str, Any],
    field_name: str,
    index: int,
) -> bool | None:
    value = rule_data.get(field_name)
    if value is None:
        return None
    if not isinstance(value, bool):
        raise CategoryRuleConfigError(f"rules[{index}].{field_name} must be a boolean")
    return value


def require_bool(
    rule_data: Mapping[str, Any],
    field_name: str,
    index: int,
) -> bool:
    return require_bool_with_default(rule_data, field_name, index, default=False)


def require_bool_with_default(
    rule_data: Mapping[str, Any],
    field_name: str,
    index: int,
    *,
    default: bool,
) -> bool:
    value = rule_data.get(field_name, default)
    if not isinstance(value, bool):
        raise CategoryRuleConfigError(f"rules[{index}].{field_name} must be a boolean")
    return value


def categorize_transaction(
    transaction: Transaction,
    rules: Sequence[CategoryRule],
) -> CategorizedTransaction:
    for rule in rules:
        if rule_matches_transaction(rule, transaction):
            return CategorizedTransaction(
                transaction=transaction,
                category=rule.category,
                bucket=rule.bucket or UNCATEGORIZED_BUCKET,
                counts_toward_income=rule.counts_toward_income,
                matched_rule_id=rule.id,
                matched_rule=rule,
                matched_on=get_match_reasons(rule, transaction),
            )

    return CategorizedTransaction(
        transaction=transaction,
        category=UNCATEGORIZED_CATEGORY,
        bucket=UNCATEGORIZED_BUCKET,
        counts_toward_income=True,
        matched_rule_id=None,
        matched_rule=None,
        matched_on=(),
    )


def categorize_transactions(
    transactions: Sequence[Transaction],
    rules: Sequence[CategoryRule],
) -> list[CategorizedTransaction]:
    return [categorize_transaction(transaction, rules) for transaction in transactions]


def rule_matches_transaction(
    rule: CategoryRule,
    transaction: Transaction,
) -> bool:
    if rule.credit_card_payment and not is_credit_card_payment(transaction):
        return False

    if rule.venmo_reimbursement and not is_venmo_reimbursement(transaction):
        return False

    if rule.internal_transfer and not is_internal_transfer(transaction):
        return False

    if rule.accounts and transaction.account not in rule.accounts:
        return False

    if rule.amounts and transaction.amount not in rule.amounts:
        return False

    if (
        rule.description_contains
        and not any(
            substring in transaction.description
            for substring in rule.description_contains
        )
    ):
        return False

    if (
        rule.details
        and transaction.source_metadata.get("details") not in rule.details
    ):
        return False

    if (
        rule.transaction_types
        and transaction.source_metadata.get("transaction_type")
        not in rule.transaction_types
    ):
        return False

    if rule.is_income is not None and transaction.is_income != rule.is_income:
        return False

    return True


def get_match_reasons(
    rule: CategoryRule,
    transaction: Transaction,
) -> tuple[str, ...]:
    reasons: list[str] = []

    if rule.credit_card_payment:
        reasons.append("credit_card_payment=true")

    if rule.venmo_reimbursement:
        reasons.append("venmo_reimbursement=true")

    if rule.internal_transfer:
        reasons.append("internal_transfer=true")

    if rule.accounts:
        reasons.append(f"account={transaction.account}")

    if rule.amounts and transaction.amount in rule.amounts:
        reasons.append(f"amount={transaction.amount}")

    for substring in rule.description_contains:
        if substring in transaction.description:
            reasons.append(f"description_contains={substring!r}")

    details = transaction.source_metadata.get("details")
    if rule.details and details in rule.details:
        reasons.append(f"details={details!r}")

    transaction_type = transaction.source_metadata.get("transaction_type")
    if rule.transaction_types and transaction_type in rule.transaction_types:
        reasons.append(f"transaction_type={transaction_type!r}")

    if rule.is_income is not None:
        reasons.append(f"is_income={transaction.is_income}")

    return tuple(reasons)


def is_credit_card_payment(transaction: Transaction) -> bool:
    return (
        transaction.account.startswith("credit")
        and transaction.source_metadata.get("transaction_type") == "Payment"
    )


def is_venmo_reimbursement(transaction: Transaction) -> bool:
    return (
        transaction.account == "venmo"
        and transaction.is_income
        and transaction.source_metadata.get("transaction_type") == "Payment"
    )


def is_internal_transfer(transaction: Transaction) -> bool:
    description = transaction.description.upper()
    return (
        "TRANSFER" in description
        or transaction.source_metadata.get("transaction_type") == "TRANSFER"
        or transaction.source_metadata.get("details") == "TRANSFER"
    )
