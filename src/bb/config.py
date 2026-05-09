from pathlib import Path
from dataclasses import dataclass
from math import isclose
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


@dataclass(frozen=True)
class MonthlyBudgetConfig:
    year: int = 2026
    month: Union[str, int] = "february"
    needs_frac: float = 0.5
    wants_frac: float = 0.3
    savings_frac: float = 0.2

    def __post_init__(self) -> None:
        if not isinstance(self.year, int) or self.year < 1:
            raise ValueError(
                f"monthly_budget.year must be a positive integer, got {self.year!r}"
            )
        validate_month_value(self.month)
        validate_fraction_value("needs_frac", self.needs_frac)
        validate_fraction_value("wants_frac", self.wants_frac)
        validate_fraction_value("savings_frac", self.savings_frac)
        total = self.needs_frac + self.wants_frac + self.savings_frac
        if not isclose(total, 1.0, rel_tol=0.0, abs_tol=1e-9):
            raise ValueError(
                "monthly_budget.needs_frac, monthly_budget.wants_frac, and "
                f"monthly_budget.savings_frac must sum to 1, got {total!r}"
            )


@dataclass(frozen=True)
class Config:
    raw_data_path: Path = Path("data/raw")
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
    cfg_data["monthly_budget"] = MonthlyBudgetConfig(
        **cfg_data.get("monthly_budget", {})
    )
    return Config(**cfg_data)
