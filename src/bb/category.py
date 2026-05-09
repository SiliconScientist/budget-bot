from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11 fallback
    import tomli as tomllib

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


class CategoryRuleConfigError(ValueError):
    pass


def load_category_rules(config_path: Path) -> list[CategoryRule]:
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

        rule = parse_category_rule(rule_data, index)
        if rule.id in seen_rule_ids:
            raise CategoryRuleConfigError(f"rules[{index}].id duplicates {rule.id!r}")
        seen_rule_ids.add(rule.id)
        rules.append(rule)

    return rules


def parse_category_rule(
    rule_data: Mapping[str, Any],
    index: int,
) -> CategoryRule:
    return CategoryRule(
        id=require_non_empty_string(rule_data, "id", index),
        category=require_non_empty_string(rule_data, "category", index),
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


def categorize_transaction(
    transaction: Transaction,
    rules: Sequence[CategoryRule],
) -> CategorizedTransaction:
    raise NotImplementedError("Transaction categorization is not implemented yet")
