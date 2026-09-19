# Electricity Retail Sales Decision Intelligence

[![tests](https://github.com/ahmaddshbg-blip/eia861m-electricity-market-monitor/actions/workflows/tests.yml/badge.svg)](https://github.com/ahmaddshbg-blip/eia861m-electricity-market-monitor/actions/workflows/tests.yml)

Portfolio project using published EIA-861M monthly state-sector retail electricity sales for 2016-2025. The dashboard supports descriptive market monitoring. It does not forecast demand or establish causal explanations.

## Business problem

The approved Project 01 objective is to help a hypothetical energy-market analyst decide which state-sector observations deserve deeper investigation each month because sales, nominal revenue, customer counts, or implied average price changed conspicuously. The supported decision is where to focus analyst attention, not a company-specific tariff, investment, or policy action. See the [dashboard specification](docs/dashboard_spec.md) for the decision, scope, and success criterion.

The local dashboard now opens on a selected-month investigation table. An analyst can compare a state-sector with the same month one year earlier, sort by a chosen change metric, inspect its history, and export selected rows for follow-up. This is an analyst-controlled shortlist, not an anomaly score or a validated business outcome. See the [December 2025 investigation brief](reports/market_investigation_2025_12.md) for one reproducible decision example. Forecasting is out of scope for Project 01 and is the core focus of Portfolio Project 02.

## Decision output

![Monthly investigation dashboard showing December 2025 state-sector priorities](reports/figures/02_dashboard_monthly_investigation.png)

The reviewed December 2025 workflow compares all 204 state-sector observations with the same month one year earlier. Ranking by absolute sales change directs analyst attention to CA residential, TX residential, and OH commercial. It does not classify these rows as anomalies or explain why they changed.

## Key results

- Published 2025 retail sales totaled 4,058.01 TWh, nominal revenue totaled USD 553.28 billion, and implied average price was 13.63 nominal cents/kWh.
- From 2016 to 2025, published sales increased 7.9%, while nominal revenue increased 43.1% and implied average price increased 32.7%. No inflation adjustment or causal interpretation is applied.
- In December 2025, national sales were 2.9% above December 2024 and nominal revenue was 10.2% higher.
- CA residential recorded the largest absolute decline in the monthly shortlist; TX residential and OH commercial recorded the largest increases. OH commercial also exceeded its prior observed December YoY range, making it a strong follow-up candidate rather than a confirmed anomaly.

![National annual sales, nominal revenue, and implied average price trends](reports/figures/01_national_annual_trends.png)

## Reproduce the data

The repository includes the reviewed raw and flagged snapshots that support the December 2025 brief. Install the pinned direct dependencies and verify the files:

```powershell
python -m pip install -r requirements.txt
python scripts/verify_snapshot.py
python scripts/validate_data.py
python -m unittest discover -s tests -v
```

Validation rebuilds the flagged CSV and summary from the versioned raw snapshot. No API key is needed for this path. See the [reproducibility guide](docs/reproducibility.md) for the full execution order and the separate fresh-fetch path. [Data attribution](DATA_ATTRIBUTION.md) documents EIA provenance and reuse; [Colab workflow](docs/colab_workflow.md) covers the author's private Drive workflow. Never put a real key in a notebook cell, repository, or shared file.

## Run the dashboard

From this project directory, run `python -m streamlit run app.py`. No API key is needed to view the dashboard. It reads the flagged interim CSV at the configured path. To use an existing CSV elsewhere without copying it, set `EIA861M_DATA_PATH` to its absolute path before starting the app. In PowerShell:

```powershell
$env:EIA861M_DATA_PATH = 'D:\path\to\eia861m_retail_sales_2016_2025_with_quality_flags.csv'
python -m streamlit run app.py
```

Streamlit prints a local URL (normally `http://localhost:8501`). This is not a public deployment.

The global year selector starts at the latest year in the CSV. The Monthly investigation view defaults to its latest month. National totals do not change when state or sector filters are used in Segment explorer. The annual state-sector table's CSV download contains its displayed filter scope and explicit sort order; the monthly export contains analyst-selected rows.

## Reproduce the SQL shortlist

The [monthly investigation SQL](sql/monthly_investigation.sql) independently ranks state-sector observations by absolute sales change against the same month a year earlier. It uses SQLite via Python's standard library and the same validated CSV as the dashboard. From the project directory, run:

```powershell
python scripts/run_sql_investigation.py --period 2025-12
```

The default top three should match the [December 2025 investigation brief](reports/market_investigation_2025_12.md). Use `--data-path` or set `EIA861M_DATA_PATH` only when testing another flagged CSV. This SQL is a reproducible analysis artifact, not a database-backed dashboard or a deployed BI product.

## Analytical boundaries

Sales and revenue are annual sums; the customer indicator is the average of monthly customer counts. Implied price is `100 * sum(revenue) / sum(sales)` in nominal cents/kWh, not a tariff or a mean of reported prices. Zeros and the small negative revenue observation are retained and flagged. See `docs/data_provenance.md`, `docs/data_quality.md`, and `docs/eda_findings.md` for source, quality, and interpretation details.

This local MVP uses a fixed 2016-2025 snapshot, not an automated monthly refresh. The dashboard is not publicly deployed. The monthly view has passed code and data checks and user visual review. Forecasting and Power BI are not implemented in Project 01 and must not be inferred from the Streamlit dashboard.

## License

Project code and documentation are released under the [MIT License](LICENSE). The source data are attributed separately in [DATA_ATTRIBUTION.md](DATA_ATTRIBUTION.md).
