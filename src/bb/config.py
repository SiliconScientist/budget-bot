from pathlib import Path
from dataclasses import dataclass
from typing import Optional

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11 fallback
    import tomli as tomllib


@dataclass(frozen=True)
class Config:
    seed: Optional[int] = None
    message: str = "Hello from budget-bot!"
    raw_data_dir: Path = Path("data/raw")
    income_account: str = "debit_demo"


ROOT_DIR = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT_DIR / "config.toml"


def get_config() -> Config:
    with CONFIG_PATH.open("rb") as f:
        cfg_data = tomllib.load(f)
    if "raw_data_dir" not in cfg_data:
        cfg_data["raw_data_dir"] = ROOT_DIR / "data/raw"
    else:
        cfg_data["raw_data_dir"] = Path(cfg_data["raw_data_dir"])
        if not cfg_data["raw_data_dir"].is_absolute():
            cfg_data["raw_data_dir"] = ROOT_DIR / cfg_data["raw_data_dir"]
    return Config(**cfg_data)
