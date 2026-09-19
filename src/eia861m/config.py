import json
from pathlib import Path
from typing import Any

from eia861m.paths import PROJECT_ROOT


DEFAULT_CONFIG_PATH = PROJECT_ROOT / "configs" / "config.json"


def load_config(path: Path = DEFAULT_CONFIG_PATH) -> dict[str, Any]:
    """Load the project YAML configuration."""
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    config = json.loads(path.read_text(encoding="utf-8"))

    if not isinstance(config, dict):
        raise ValueError(f"Config file must contain a mapping: {path}")

    return config
