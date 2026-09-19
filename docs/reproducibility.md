# Reproducibility Guide

## What Is Reproduced

Project 01 has two distinct reproduction paths:

1. **Historical snapshot:** Use the versioned raw CSV and acquisition metadata from the 2026-09-16 Colab/Drive run, then regenerate validation outputs and analysis. These files are included in the repository with SHA-256 checksums. This is the default path and can match the December 2025 brief without an API key.
2. **Fresh EIA fetch:** Use a private EIA API key to download the configured 2016-01 to 2025-12 scope, validate it, and run the analysis. EIA can revise published values, so a fresh fetch is not guaranteed to reproduce the historical shortlist or exact figures. Record the new acquisition timestamp and compare outputs before making claims.

Passing unit tests or running SQL against an existing interim CSV does not prove a fresh-source rebuild. The versioned historical snapshot establishes the reviewed result; it does not freeze EIA's current API response.

## Environment And Inputs

- Local tests were run with Python 3.12.14. The Colab test suite also passed, but its package versions were not recorded.
- `requirements.txt` pins the direct dependency versions used for the local verification. Transitive packages and operating-system details can still vary.
- `EIA_API_KEY` is required only for a fresh download. Store it in Colab Secrets or a private local environment, never in code, output, or a shared Drive file.
- `EIA861M_DATA_PATH` is optional for the dashboard and SQL runner when the flagged CSV is outside the configured `data/interim/` path.
- Run commands from the project root. Scripts resolve configuration and output paths relative to that root.

## Rebuild From The Versioned Snapshot

Start from a new clone and run:

```text
python -m pip install -r requirements.txt
python scripts/verify_snapshot.py
python scripts/validate_data.py
python -m unittest discover -s tests -v
python scripts/run_sql_investigation.py --period 2025-12
python -m streamlit run app.py
```

The validation script regenerates the flagged CSV and summary from the raw CSV. Notebook 02 can then regenerate EDA views and figures from the flagged CSV; it does not fetch data.

## Fetch Fresh EIA Data

Use a separate clone or working copy so the historical snapshot remains intact. Set `EIA_API_KEY` in a private environment or Colab Secrets, then run `python scripts/download_data.py --replace-existing` followed by `python scripts/validate_data.py`. The explicit replacement flag is required because the repository includes a raw snapshot. Record the new acquisition timestamp and do not represent revised values as the 2026-09-16 snapshot.

The current configuration expects 24,480 rows, 120 months, 51 jurisdictions, and four sectors. A structural failure stops validation. In the reviewed historical snapshot, the December 2025 SQL query compares 204 state-sector observations and ranks CA-RES, TX-RES, and OH-COM first. A fresh EIA fetch may have different values or rankings after revisions.

## Verification Status

| Check | Status |
|---|---|
| SQL shortlist matches the reviewed December 2025 brief | Passed locally and in the author's Colab/Drive run |
| Unit tests | 12 passed locally, in the author's Colab/Drive run, and in GitHub Actions without warnings |
| Fresh installation and EIA download in an empty project copy | Not yet tested |
| Historical snapshot available to an external reviewer | Included with attribution and SHA-256 manifest; local clean-clone verification passed |
| Fresh dependency installation | Passed in GitHub Actions on Ubuntu with Python 3.12 at commit `a97e4df` |
| Public deployment | Not done; local Streamlit dashboard only |

The historical-snapshot path is reproducible from the public repository: the local clean clone and GitHub Actions both passed. A fresh API download remains a separate, revision-sensitive path and has not been tested in GitHub Actions because it requires a private key. The project's decision support is descriptive; forecasting and Power BI are outside the current implementation.
