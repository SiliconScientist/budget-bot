from pathlib import Path
from typing import Optional

import tomllib

from pydantic import BaseModel


class Config(BaseModel):
    seed: Optional[int] = None
    message: str = "Hello from budget-bot!"


def get_config():
    with open("config.toml", "rb") as f:
        cfg_data = tomllib.load(f)
        cfg = Config(**cfg_data)
    return cfg
