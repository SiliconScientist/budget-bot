from dataclasses import dataclass, field
from pathlib import Path
from math import isclose
import re
from typing import Union

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11 fallback
    import tomli as tomllib


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
SNAKE_CASE_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")


def validate_month_value(month: Union[str, int]) -> None:
    if isinstance(month, int):
        if 1 <= month <= 12:
            return
        raise ValueError(
            f"monthly_budget.month must be between 1 and 12, got {month}"
        )

    normalized = month.strip().lower()
    if normalized.isdigit():
        month_number = int(normalized)
        if 1 <= month_number <= 12:
            return
        raise ValueError(
            f"monthly_budget.month must be between 1 and 12, got {month}"
        )

    if normalized in MONTH_NAME_TO_NUMBER:
        return

    raise ValueError(
        "monthly_budget.month must be a month name or number 1-12, "
        f"got {month!r}"
    )


def validate_fraction_value(name: str, value: float) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"monthly_budget.{name} must be a number, got {value!r}")
    if not 0 <= value <= 1:
        raise ValueError(
            f"monthly_budget.{name} must be between 0 and 1, got {value!r}"
        )


def validate_taxonomy_categories(
    bucket_name: str,
    categories: tuple[str, ...],
) -> None:
    if not isinstance(categories, tuple):
        raise ValueError(
            f"monthly_budget.{bucket_name}.categories must be an array of snake_case strings"
        )
    if not categories:
        raise ValueError(f"monthly_budget.{bucket_name}.categories must not be empty")
    for category in categories:
        if not isinstance(category, str) or not SNAKE_CASE_PATTERN.fullmatch(category):
            raise ValueError(
                f"monthly_budget.{bucket_name}.categories must contain only snake_case strings"
            )
    if len(categories) != len(set(categories)):
        raise ValueError(
            f"monthly_budget.{bucket_name}.categories must not contain duplicate categories"
        )


@dataclass(frozen=True)
class BudgetBucketConfig:
    frac: float
    categories: tuple[str, ...]

    def __post_init__(self) -> None:
        # Validation is handled from MonthlyBudgetConfig so error messages carry bucket names.
        pass


@dataclass(frozen=True)
class MonthlyBudgetConfig:
    year: int = 2026
    month: Union[str, int] = "february"
    needs: BudgetBucketConfig = field(
        default_factory=lambda: BudgetBucketConfig(
            frac=0.5,
            categories=(
                "rent",
                "groceries",
                "utilities",
                "transport",
                "insurance",
                "tuition_education",
                "pharmacy_medical",
                "errands",
            ),
        )
    )
    wants: BudgetBucketConfig = field(
        default_factory=lambda: BudgetBucketConfig(
            frac=0.3,
            categories=(
                "meal_prep",
                "books",
                "movies",
                "hobbies",
                "restaurants",
                "digital_services",
                "personal_care",
                "social",
                "travel",
            ),
        )
    )
    savings: BudgetBucketConfig = field(
        default_factory=lambda: BudgetBucketConfig(
            frac=0.2,
            categories=("savings",),
        )
    )

    def __post_init__(self) -> None:
        if not isinstance(self.year, int) or self.year < 1:
            raise ValueError(
                f"monthly_budget.year must be a positive integer, got {self.year!r}"
            )
        validate_month_value(self.month)
        validate_fraction_value("needs.frac", self.needs.frac)
        validate_fraction_value("wants.frac", self.wants.frac)
        validate_fraction_value("savings.frac", self.savings.frac)
        validate_taxonomy_categories("needs", self.needs.categories)
        validate_taxonomy_categories("wants", self.wants.categories)
        validate_taxonomy_categories("savings", self.savings.categories)
        all_categories = (
            self.needs.categories + self.wants.categories + self.savings.categories
        )
        if len(all_categories) != len(set(all_categories)):
            raise ValueError(
                "monthly_budget categories must be unique across needs, wants, "
                "and savings"
            )
        total = self.needs.frac + self.wants.frac + self.savings.frac
        if not isclose(total, 1.0, rel_tol=0.0, abs_tol=1e-9):
            raise ValueError(
                "monthly_budget.needs.frac, monthly_budget.wants.frac, and "
                f"monthly_budget.savings.frac must sum to 1, got {total!r}"
            )

    @property
    def bucket_to_categories(self) -> dict[str, frozenset[str]]:
        return {
            "needs": frozenset(self.needs.categories),
            "wants": frozenset(self.wants.categories),
            "savings": frozenset(self.savings.categories),
        }


@dataclass(frozen=True)
class Config:
    raw_data_path: Path = Path("data/raw")
    export_path: Path = Path("exports")
    monthly_budget: MonthlyBudgetConfig = MonthlyBudgetConfig()


ROOT_DIR = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT_DIR / "config.toml"
CATEGORY_CONFIG_PATH = ROOT_DIR / "category.toml"
CATEGORY_EXAMPLE_CONFIG_PATH = ROOT_DIR / "category.example.toml"


def get_category_config_path() -> Path:
    if CATEGORY_CONFIG_PATH.exists():
        return CATEGORY_CONFIG_PATH
    if CATEGORY_EXAMPLE_CONFIG_PATH.exists():
        return CATEGORY_EXAMPLE_CONFIG_PATH
    raise FileNotFoundError(
        "Expected category.toml or category.example.toml at the repo root"
    )


def get_config() -> Config:
    with CONFIG_PATH.open("rb") as f:
        cfg_data = tomllib.load(f)
    if "raw_data_path" not in cfg_data:
        cfg_data["raw_data_path"] = ROOT_DIR / "data" / "raw"
    else:
        cfg_data["raw_data_path"] = Path(cfg_data["raw_data_path"])
        if not cfg_data["raw_data_path"].is_absolute():
            cfg_data["raw_data_path"] = ROOT_DIR / cfg_data["raw_data_path"]
    default_monthly_budget = MonthlyBudgetConfig()
    monthly_budget_data = dict(cfg_data.get("monthly_budget", {}))
    export_data = dict(monthly_budget_data.pop("export", {}))
    export_dir = monthly_budget_data.pop("export_dir", None)
    if "export_path" in cfg_data:
        export_path = Path(cfg_data["export_path"])
    elif "path" in export_data:
        export_path = Path(export_data["path"])
    elif export_dir is not None:
        export_path = Path(export_dir)
    else:
        export_path = ROOT_DIR / "exports"
    if not export_path.is_absolute():
        export_path = ROOT_DIR / export_path
    cfg_data["export_path"] = export_path
    default_buckets = {
        "needs": default_monthly_budget.needs,
        "wants": default_monthly_budget.wants,
        "savings": default_monthly_budget.savings,
    }
    for bucket_name in ("needs", "wants", "savings"):
        bucket_data = dict(monthly_budget_data.get(bucket_name, {}))
        default_bucket = default_buckets[bucket_name]
        if "frac" not in bucket_data:
            bucket_data["frac"] = default_bucket.frac
        if "categories" not in bucket_data:
            bucket_data["categories"] = default_bucket.categories
        else:
            bucket_data["categories"] = tuple(bucket_data["categories"])
        monthly_budget_data[bucket_name] = BudgetBucketConfig(**bucket_data)
    cfg_data["monthly_budget"] = MonthlyBudgetConfig(**monthly_budget_data)
    return Config(**cfg_data)
