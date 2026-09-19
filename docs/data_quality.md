# Data Quality

## Status

Data-quality assessment for Project 01. This document records validation results, anomalies, and cleaning decisions for the EIA-861M electricity retail sales dataset.

- Project: Project 01 - EIA-861M Electricity Retail Sales Analytics
- Last updated: 2026-09-16
- Current stage: Acquisition and structural validation gate passed

Project 01 is currently scoped to Business Analytics and Decision Intelligence without forecasting. The data-quality layer supports reliable KPI design and market investigation without silently carrying data defects forward. Early predictive ideas are reserved for Portfolio Project 02.

## Validation Gate Result

The Colab/Drive workflow completed successfully on 2026-09-16 and generated:

```text
data/raw/eia861m_retail_sales_2016_2025.csv
data/interim/eia861m_retail_sales_2016_2025_with_quality_flags.csv
artifacts/metrics/data_validation_summary.json
```

The notebook completed with:

```text
Acquisition and validation notebook completed successfully.
```

Gate decision:

```text
Pass for downstream EDA preparation.
```

This does not yet approve final business interpretation, KPI design, dashboarding, or modeling. It only confirms that the acquisition and validation layer is reproducible and structurally sound.

## Validation Scope

The initial notebook inspected the EIA-861M monthly retail sales data with the following scope:

- Period: 2016-01 through 2025-12
- Geography: 51 U.S. jurisdictions or states
- Sectors: `COM`, `IND`, `RES`, `TRA`
- Metrics: `customers`, `price`, `revenue`, `sales`
- Unit of observation: `state x month x sector`
- Expected key: `period + stateid + sectorid`

## Structural Validation Results

| Check | Result | Status |
|---|---:|---|
| Total rows | 24,480 | Pass |
| Total columns | 13 | Pass |
| Unique months | 120 | Pass |
| Jurisdictions/states | 51 | Pass |
| Sectors | 4 | Pass |
| Rows per state | 480 | Pass |
| Rows per sector | 6,120 | Pass |
| Rows per month | 204 | Pass |
| Duplicate keys on `period + stateid + sectorid` | 0 | Pass |
| Missing values in inspected dataset | 0 | Pass |

Expected row count:

```text
120 months x 51 states x 4 sectors = 24,480 rows
```

The observed row count matches the expected row count.

## Schema Observed

The API response produced the following columns:

```text
period
stateid
stateDescription
sectorid
sectorName
customers
price
revenue
sales
customers-units
price-units
revenue-units
sales-units
```

Initial API values arrived as strings for numeric columns and were converted to numeric types in the notebook:

| Column | Initial notebook dtype after conversion |
|---|---|
| `customers` | integer |
| `price` | float |
| `revenue` | float |
| `sales` | float |

The `period` column should later be converted explicitly to a monthly date representation, such as a month-start datetime or monthly period type.

## Missing Values

Initial missing-value check:

```text
0 missing values across all inspected columns
```

This result only means the public API response had no null values in the inspected dataframe. It does not prove that every underlying value was directly observed by EIA.

## Zero Values

Initial zero-value counts:

| Column | Zero count |
|---|---:|
| `customers` | 2,642 |
| `price` | 2,646 |
| `revenue` | 2,645 |
| `sales` | 2,642 |

Zero values are concentrated in the transportation sector:

| Sector | `customers` zero | `price` zero | `revenue` zero | `sales` zero |
|---|---:|---:|---:|---:|
| `COM` | 0 | 0 | 0 | 0 |
| `IND` | 0 | 0 | 0 | 0 |
| `RES` | 0 | 0 | 0 | 0 |
| `TRA` | 2,642 | 2,646 | 2,645 | 2,642 |

## Zero-Value Decision

Zero values are retained as published numeric values.

Do not automatically:

- Replace zero with missing values.
- Treat zero as non-response.
- Treat zero as imputed.
- Drop zero observations.
- Build business conclusions from `TRA` zero values before documenting the sector definition and limitations.

Reason:

The public EIA-861M API does not expose observation-level flags that distinguish reported, imputed, estimated, or adjusted values.

## Negative Revenue Anomaly

Initial validation found one negative revenue observation:

| Period | State | Sector | Customers | Price | Revenue | Sales |
|---|---|---|---:|---:|---:|---:|
| 2022-02 | DC | `TRA` | 3 | 0.0 | -0.00001 | 19.90724 |

The revenue value is in million dollars. A value of -0.00001 million USD equals -10 USD.

Decision:

- Retain the observation for now.
- Flag it as an anomaly.
- Do not assert a cause without EIA evidence.
- Do not remove it solely because the value is negative.

## Revenue Consistency Check

The notebook calculated an approximate expected revenue:

```text
expected_revenue = sales * price / 100
```

This is a useful reasonableness check because:

- `sales` is measured in million kilowatt-hours.
- `price` is measured in cents per kilowatt-hour.
- Dividing by 100 converts cents to dollars.
- The resulting value is in million dollars.

However, this should not be treated as a strict identity. The published `price` field is an average retail price and may be rounded. Small differences between reported revenue and calculated expected revenue are expected.

Initial observed difference range:

| Field | Value |
|---|---:|
| Minimum `revenue - expected_revenue` | -0.786646252 |
| Maximum `revenue - expected_revenue` | 0.769073362 |

The largest positive difference observed in the notebook was:

| Period | State | Sector | Revenue | Sales | Price | Difference |
|---|---|---|---:|---:|---:|---:|
| 2022-07 | TX | `RES` | 2844.55318 | 20742.40778 | 13.71 | 0.769073362 |

Next step:

Define an explicit tolerance policy using both absolute and relative differences before flagging records as materially inconsistent.

## Proposed Quality Flags

The processed or interim dataset should include explicit quality flags rather than silently altering observations:

| Flag | Meaning |
|---|---|
| `flag_all_metrics_zero` | `customers`, `price`, `revenue`, and `sales` are all zero |
| `flag_any_metric_zero` | At least one of the main numeric metrics is zero |
| `flag_negative_revenue` | `revenue` is less than zero |
| `flag_revenue_consistency_check` | Revenue differs from `sales * price / 100` beyond a documented tolerance |
| `flag_transportation_sector` | Observation belongs to the `TRA` sector |

These flags should support investigation and documentation. They should not automatically imply deletion.

Actual quality flag counts from the 2026-09-16 validation run:

| Flag | Count |
|---|---:|
| `flag_all_metrics_zero` | 2,642 |
| `flag_any_metric_zero` | 2,646 |
| `flag_negative_revenue` | 1 |
| `flag_transportation_sector` | 6,120 |
| `flag_revenue_consistency_check` | 0 |

## Current Cleaning Decisions

| Issue | Decision | Rationale |
|---|---|---|
| Published zero values | Retain | The API does not expose observation-level provenance flags |
| `TRA` zero concentration | Retain and investigate | Sector-specific pattern may reflect classification, reporting, estimation, or structural zeros |
| Missing values | No imputation required at this stage | No null values observed in the inspected dataframe |
| Negative revenue | Retain and flag | Magnitude is tiny and cause is unknown |
| Revenue formula differences | Retain; no rows exceeded current tolerance | Average price may be rounded |

## Risks If Mishandled

- Treating all zeros as missing would create undocumented data manipulation.
- Dropping `TRA` zero observations could bias transportation-sector analysis.
- Treating `TRA` as all transportation activity would be a business interpretation error.
- Treating EIA-861M as raw census data would misrepresent the data-generating process.
- Treating `revenue = sales * price / 100` as an exact identity could falsely label rounded values as errors.

## Required Next Checks

Before business EDA, KPI design, dashboarding, or modeling:

1. Use `data/interim/eia861m_retail_sales_2016_2025_with_quality_flags.csv` as the source of truth for EDA preparation.
2. Keep quality flags in downstream analysis; do not silently drop flagged observations.
3. Add tests for deterministic validation logic.
4. Keep exploratory analysis separate from final quality decisions.
5. Re-run validation if the API query, validation logic, tolerance settings, or raw data snapshot changes.

## Review Position

Current data quality is sufficient to begin EDA preparation using the flagged interim dataset.

The next professional milestone is EDA design: define the analytical questions, KPI candidates, aggregation levels, and decision-support angle before building charts or models.
