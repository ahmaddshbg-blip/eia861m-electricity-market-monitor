# Data Provenance

## Status

Data provenance record for Project 01. This document should be updated whenever the data acquisition process, API query, dataset coverage, or cleaning decisions change.

- Project: Project 01 - EIA-861M Electricity Retail Sales Analytics
- Document owner: Project author
- Last updated: 2026-09-16
- Initial Colab API acquisition date: 2026-09-07
- Reproducible Colab/Drive acquisition run date: 2026-09-16

## Dataset Identity

This project uses public electricity retail sales data from the U.S. Energy Information Administration (EIA), specifically the EIA-861M monthly electricity retail sales data exposed through the EIA Open Data API.

The dataset represents electricity sales to ultimate customers by state, month, and end-use sector. It is used as a public-data demonstration of a realistic analytical workflow, not as evidence of access to internal utility or company systems.

Project 01 is scoped to Business Analytics and Decision Intelligence. Early planning considered a light predictive extension, but the current scope decision excludes forecasting; it belongs to Portfolio Project 02. This provenance record describes the data used for descriptive market investigation, not a predictive model.

## Source

Primary source:

- EIA Open Data API, Electricity Retail Sales: https://www.eia.gov/opendata/browser/electricity/retail-sales

Supporting source pages:

- EIA Form EIA-861M Detailed Data: https://www.eia.gov/electricity/data/eia861m/
- EIA Electricity Data: https://www.eia.gov/electricity/data.php
- EIA Electric Power Annual and technical notes: https://www.eia.gov/electricity/annual/

## API Endpoint

The acquisition notebook uses the following endpoint:

```text
https://api.eia.gov/v2/electricity/retail-sales/data/
```

The initial query requested:

- Frequency: monthly
- Metrics: `customers`, `price`, `revenue`, `sales`
- Sectors: `COM`, `IND`, `RES`, `TRA`
- Geography: 51 U.S. jurisdictions or states, including the District of Columbia
- Period: 2016-01 through 2025-12

The initial notebook split the request into two-year windows:

```text
2016-01 to 2017-12
2018-01 to 2019-12
2020-01 to 2021-12
2022-01 to 2023-12
2024-01 to 2025-12
```

This chunking produced 4,896 rows per two-year window and 24,480 rows in total.

## Unit Of Analysis

The unit of observation is:

```text
state x month x end-use sector
```

The expected primary key is:

```text
period + stateid + sectorid
```

Initial validation found no duplicate keys for this combination.

## Coverage

Initial inspected coverage:

| Dimension | Coverage |
|---|---:|
| Period | 2016-01 to 2025-12 |
| Unique months | 120 |
| Jurisdictions/states | 51 |
| Sectors | 4 |
| Observations | 24,480 |

Sector coverage:

| Sector ID | Sector name |
|---|---|
| `COM` | Commercial |
| `IND` | Industrial |
| `RES` | Residential |
| `TRA` | Transportation |

Each state has 480 observations:

```text
120 months x 4 sectors
```

Each sector has 6,120 observations:

```text
120 months x 51 states
```

Each month has 204 observations:

```text
51 states x 4 sectors
```

## Variables And Units

| Variable | Unit | Description |
|---|---|---|
| `customers` | Number of customers | Count of ultimate customers for the state-month-sector observation |
| `price` | Cents per kilowatt-hour | Average retail price |
| `revenue` | Million dollars | Revenue from sales to ultimate customers |
| `sales` | Million kilowatt-hours | Electricity sales to ultimate customers |

Important interpretation rule:

`price` is an average retail price in cents per kilowatt-hour. It should not be automatically interpreted as a utility tariff, contract rate, or customer-specific rate.

## Data-Generating Process Notes

The public EIA-861M data should not be treated as raw census data for every utility. Based on EIA technical documentation summarized in the project anchor:

- EIA-861M is a monthly collection based on a sample of large utilities and a census of energy service providers.
- EIA uses model-based methods to estimate monthly sales, revenues, and customer counts by sector and state where necessary.
- EIA performs follow-up for non-response and reports very high response quality.
- EIA methodology may use borrowing of strength for small domains.
- Monthly values may involve state-level reconciliation or adjustment.
- Monthly EIA-861M values may be benchmarked against final annual EIA-861 values.

These points matter because the dataset is a public analytical product created through reporting, estimation, reconciliation, and benchmarking. It should not be interpreted as direct observation of every underlying utility transaction.

## Known Provenance Limitation

The public EIA-861M API does not expose an observation-level indicator distinguishing reported, imputed, estimated, or adjusted values.

Therefore:

- A value of zero cannot automatically be classified as missing.
- A value of zero cannot automatically be classified as non-response.
- A value of zero cannot automatically be classified as directly reported or imputed.
- Observation-level provenance cannot be inferred solely from the public dataframe.

Documentation statement to preserve:

> The public EIA-861M API does not expose an observation-level indicator distinguishing reported, imputed, or estimated values. Therefore, zero values were retained as published values and were not treated as missing solely based on their magnitude.

## Special Interpretation Note For `TRA`

The `TRA` sector represents the EIA end-use transportation electricity sector classification. It must not be interpreted as all transportation activity in a state.

In particular:

- `TRA` zero values do not prove that there was no transportation activity.
- `TRA` zero values do not prove that there was no transportation-related energy use.
- `TRA` should be interpreted only within the EIA electricity retail sales sector definition.

## Initial Data Handling Decisions

The initial data-quality policy is conservative:

- Retain published zero values.
- Retain small published values.
- Retain observations that pass structural validation.
- Do not replace zero values with missing values solely based on magnitude.
- Do not drop zero observations solely because they are surprising.
- Do not create our own imputed values during initial acquisition.
- Do not label observations as imputed unless EIA provides evidence for that classification.
- Retain the tiny negative revenue observation for now and document it as an anomaly.

## Reproducibility Notes

The current workflow supports both script-based and Colab/Drive execution. In Colab, the project folder is mounted from Google Drive and the notebook imports reusable logic from `src/eia861m/`.

Current public data policy:

- Version the reviewed 2026-09-16 raw and flagged snapshots so an external reviewer can reproduce the documented brief without an API key.
- Publish acquisition metadata, validation summary, and SHA-256 checksums with the data.
- Attribute EIA and distinguish project-derived quality flags from EIA-provided fields.
- Preserve a separate fresh-fetch path because EIA may revise published values.
- Refuse accidental raw-snapshot replacement unless the user passes `--replace-existing` explicitly.

The repository supports:

- `EIA_API_KEY` loaded from an environment variable
- `.env.example` documenting required environment variables
- A reusable acquisition function or script
- API pagination or explicit checks against the API `total` field
- Saved metadata about acquisition date, endpoint, query parameters, and row counts

Generated checkpoint files from the 2026-09-16 Colab/Drive run:

```text
data/raw/eia861m_retail_sales_2016_2025.csv
artifacts/metadata/eia861m_acquisition_metadata.json
data/interim/eia861m_retail_sales_2016_2025_with_quality_flags.csv
artifacts/metrics/data_validation_summary.json
```

## Open Items

- Verify the first public clone in a clean environment.
- Record the resulting GitHub Actions run and any environment-specific differences.
