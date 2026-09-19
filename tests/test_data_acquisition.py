from contextlib import redirect_stdout
from io import StringIO
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import sys

import pandas as pd
import requests


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from eia861m.data_acquisition import fetch_window  # noqa: E402
import download_data  # noqa: E402


class AcquisitionSafetyTests(unittest.TestCase):
    @patch("requests.get")
    def test_http_error_does_not_expose_api_key(self, get):
        secret = "test-secret-do-not-print"
        get.return_value.raise_for_status.side_effect = requests.HTTPError(
            f"403 Client Error for url: https://api.eia.gov/data/?api_key={secret}"
        )
        with self.assertRaisesRegex(RuntimeError, "EIA API request failed") as caught:
            fetch_window("https://api.eia.gov/data/", secret, "monthly", ["RES"], ["CA"], "2025-01", "2025-12", 5000)
        self.assertNotIn(secret, str(caught.exception))

    def test_existing_raw_snapshot_requires_explicit_replacement(self):
        config = {"paths": {"raw_data": "data/raw.csv", "acquisition_metadata": "artifacts/metadata.json"}}
        with TemporaryDirectory() as directory:
            raw = Path(directory) / "data" / "raw.csv"
            raw.parent.mkdir(parents=True)
            raw.write_text("existing snapshot", encoding="utf-8")
            with (
                patch.object(download_data, "load_config", return_value=config),
                patch.object(download_data, "project_path", side_effect=lambda path: Path(directory) / path),
                patch("sys.argv", ["download_data.py"]),
                patch.object(download_data, "fetch_dataset") as fetch,
            ):
                with self.assertRaisesRegex(FileExistsError, "already exists"):
                    download_data.main()
                fetch.assert_not_called()
            self.assertEqual(raw.read_text(encoding="utf-8"), "existing snapshot")

            with (
                patch.object(download_data, "load_config", return_value=config),
                patch.object(download_data, "project_path", side_effect=lambda path: Path(directory) / path),
                patch("sys.argv", ["download_data.py", "--replace-existing"]),
                patch.object(download_data, "load_env_file"),
                patch.object(download_data.os, "getenv", return_value="private-key"),
                patch.object(download_data, "fetch_dataset", return_value=(pd.DataFrame({"period": ["2025-12"]}), {"rows_fetched": 1})),
            ):
                with redirect_stdout(StringIO()):
                    download_data.main()
            self.assertIn("2025-12", raw.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
