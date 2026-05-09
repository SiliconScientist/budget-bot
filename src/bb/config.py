from pathlib import Path
from dataclasses import dataclass
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


@dataclass(frozen=True)
class MonthlyBudgetConfig:
    year: int = 2026
    month: Union[str, int] = "february"

    def __post_init__(self) -> None:
        if not isinstance(self.year, int) or self.year < 1:
            raise ValueError(
                f"monthly_budget.year must be a positive integer, got {self.year!r}"
            )
        validate_month_value(self.month)


@dataclass(frozen=True)
class Config:
    raw_data_path: Path = Path("data/raw")
    monthly_budget: MonthlyBudgetConfig = MonthlyBudgetConfig()


ROOT_DIR = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT_DIR / "config.toml"


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
