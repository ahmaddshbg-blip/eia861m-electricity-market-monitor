import argparse
import json
import os
import sys


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

from eia861m.config import load_config  # noqa: E402
from eia861m.data_acquisition import fetch_dataset  # noqa: E402
from eia861m.env import load_env_file  # noqa: E402
from eia861m.paths import project_path  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Download the configured EIA-861M raw dataset")
    parser.add_argument(
        "--replace-existing", action="store_true", help="Explicitly replace an existing raw snapshot"
    )
    args = parser.parse_args()

    config = load_config()
    raw_path = project_path(config["paths"]["raw_data"])
    metadata_path = project_path(config["paths"]["acquisition_metadata"])
    if raw_path.exists() and not args.replace_existing:
        raise FileExistsError(
            f"Raw snapshot already exists: {raw_path}. Use a clean project copy, "
            "or pass --replace-existing only if you intend to overwrite this snapshot."
        )

    load_env_file(project_path(".env"))
    api_key = os.getenv("EIA_API_KEY")
    if not api_key:
        raise ValueError("EIA_API_KEY is required. See .env.example.")

    dataframe, metadata = fetch_dataset(config=config, api_key=api_key)

    raw_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)

    with raw_path.open("w", encoding="utf-8", newline="") as file:
        dataframe.to_csv(file, index=False, lineterminator="\n")
    metadata_path.write_bytes(json.dumps(metadata, indent=2).encode("utf-8"))

    print(f"Saved raw data: {raw_path}")
    print(f"Saved acquisition metadata: {metadata_path}")
    print(f"Rows fetched: {len(dataframe)}")


if __name__ == "__main__":
    main()
