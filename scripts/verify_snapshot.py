"""Verify the versioned historical snapshot against its SHA-256 manifest."""

from __future__ import annotations

import hashlib
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MANIFEST = PROJECT_ROOT / "artifacts" / "metadata" / "snapshot_checksums.sha256"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    failures = []
    entries = []
    for line in MANIFEST.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        expected, relative_path = line.split(maxsplit=1)
        path = PROJECT_ROOT / relative_path
        if not path.is_file():
            failures.append(f"missing: {relative_path}")
            continue
        observed = sha256(path)
        if observed != expected.lower():
            failures.append(f"checksum mismatch: {relative_path}")
        entries.append(relative_path)

    if failures:
        raise RuntimeError("Snapshot verification failed: " + "; ".join(failures))
    print(f"Verified {len(entries)} snapshot files against {MANIFEST.relative_to(PROJECT_ROOT)}.")


if __name__ == "__main__":
    main()
