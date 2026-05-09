from pathlib import Path
from dataclasses import dataclass

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11 fallback
    import tomli as tomllib


@dataclass(frozen=True)
class MonthlyBudgetConfig:
    year: int = 2026
    month: str = "february"


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
