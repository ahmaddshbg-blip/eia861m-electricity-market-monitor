import json
import os
import sys

import pandas as pd


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

from eia861m.config import load_config  # noqa: E402
from eia861m.paths import project_path  # noqa: E402
from eia861m.validation import add_quality_flags, build_validation_summary  # noqa: E402


def main() -> None:
    config = load_config()
    raw_path = project_path(config["paths"]["raw_data"])
    flagged_path = project_path(config["paths"]["validation_flags"])
    summary_path = project_path(config["paths"]["validation_summary"])

    if not raw_path.exists():
        raise FileNotFoundError(
            f"Raw data not found: {raw_path}. Run scripts/download_data.py first."
        )

    dataframe = pd.read_csv(raw_path)
    summary = build_validation_summary(dataframe, config=config)
    flagged = add_quality_flags(
        dataframe,
        revenue_abs_tolerance_million_usd=float(
            config["validation"]["revenue_abs_tolerance_million_usd"]
        ),
    )

    flagged_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    with flagged_path.open("w", encoding="utf-8", newline="") as file:
        flagged.to_csv(file, index=False, lineterminator="\n")
    summary_path.write_bytes(json.dumps(summary, indent=2).encode("utf-8"))

    print(f"Saved flagged data: {flagged_path}")
    print(f"Saved validation summary: {summary_path}")
    print(f"Rows validated: {summary['row_count']}")


if __name__ == "__main__":
    main()
