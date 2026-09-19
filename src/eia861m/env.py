import os
from pathlib import Path


def load_env_file(path: Path) -> None:
    """Load simple KEY=VALUE pairs from a local .env file if it exists."""
    if not path.exists():
        return

    with path.open("r", encoding="utf-8") as file:
        for line in file:
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
