from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def project_path(relative_path: str) -> Path:
    """Return an absolute path inside the project root."""
    return PROJECT_ROOT / relative_path
