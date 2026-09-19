# Data Dictionary

## Status

Draft data dictionary for the EIA-861M electricity retail sales dataset used in Project 01.

- Project: Project 01 - EIA-861M Electricity Retail Sales Analytics
- Last updated: 2026-09-16
- Unit of observation: `state x month x end-use sector`
- Expected key: `period + stateid + sectorid`

This dictionary supports Project 01's Business Analytics and Decision Intelligence scope. Forecasting is out of scope for this project and belongs to Portfolio Project 02. The variable definitions below should be used consistently across notebooks, scripts, and the dashboard.

## Table Overview

The initial API response contains 13 columns:

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

## Column Definitions

| Column | Expected type | Unit | Description | Notes |
|---|---|---|---|---|
| `period` | string or monthly date | Month | Reporting period in `YYYY-MM` format | Convert to a formal monthly date type before time-series analysis |
| `stateid` | string | Not applicable | State or jurisdiction abbreviation | Includes the District of Columbia |
| `stateDescription` | string | Not applicable | Full state or jurisdiction name | Used for readability and reporting |
| `sectorid` | string | Not applicable | End-use sector code | Expected values: `COM`, `IND`, `RES`, `TRA` |
| `sectorName` | string | Not applicable | End-use sector name | Human-readable label for `sectorid` |
| `customers` | integer | Number of customers | Count of ultimate customers for the observation | Zero values are retained as published values |
| `price` | float | Cents per kilowatt-hour | Average retail price | Do not interpret automatically as a tariff or customer-specific rate |
| `revenue` | float | Million dollars | Revenue from sales to ultimate customers | One tiny negative value was observed and retained as an anomaly |
| `sales` | float | Million kilowatt-hours | Electricity sold to ultimate customers | Zero values are retained as published values |
| `customers-units` | string | Text metadata | Unit label for `customers` | Expected value: `number of customers` |
| `price-units` | string | Text metadata | Unit label for `price` | Expected value: `cents per kilowatt-hour` |
| `revenue-units` | string | Text metadata | Unit label for `revenue` | Expected value: `million dollars` |
| `sales-units` | string | Text metadata | Unit label for `sales` | Expected value: `million kilowatt hours` |

## Sector Codes

| Sector ID | Sector name | Interpretation note |
|---|---|---|
| `COM` | Commercial | Electricity retail sales to commercial ultimate customers |
| `IND` | Industrial | Electricity retail sales to industrial ultimate customers |
| `RES` | Residential | Electricity retail sales to residential ultimate customers |
| `TRA` | Transportation | EIA transportation end-use electricity sector; not equivalent to all transportation activity |

## Key And Granularity

The expected unique key is:

```text
period + stateid + sectorid
```

Initial duplicate-key check found:

```text
0 duplicate keys
```

This means each state-sector-month combination appears once in the inspected dataset.

## Numeric Variable Interpretation

### `customers`

Represents the number of ultimate customers associated with the state-month-sector observation.

Important cautions:

- A zero value is retained as a published value.
- A zero value is not automatically missing.
- A zero value is not automatically non-response.
- A zero value is not automatically proof that the real-world activity does not exist.

### `price`

Represents average retail price in cents per kilowatt-hour.

Important cautions:

- This is an average price, not necessarily a tariff.
- It should not be interpreted as a customer-specific rate.
- It may be rounded, so revenue reconstructed from `sales * price / 100` may differ from the reported `revenue`.

### `revenue`

Represents revenue in million dollars.

Important cautions:

- Revenue is reported in millions of dollars, so very small values may appear near zero.
- One value of `-0.00001` million dollars was observed for `2022-02`, `DC`, `TRA`.
- That negative value is retained and flagged rather than deleted.

### `sales`

Represents electricity sales in million kilowatt-hours.

Important cautions:

- This is electricity sold to ultimate customers.
- It is not total energy use across all possible transportation, industrial, commercial, or residential activity.

## Unit Consistency

The following relationship is useful for approximate validation:

```text
revenue ~= sales * price / 100
```

This is approximate, not exact.

Reason:

- `sales` is in million kilowatt-hours.
- `price` is in cents per kilowatt-hour.
- `revenue` is in million dollars.
- Published average price may be rounded.

Do not flag a row as erroneous solely because this approximate equation does not match exactly.

## Recommended Derived Validation Fields

These fields should be generated in an interim or processed validation layer, not manually edited into raw data:

| Field | Type | Description |
|---|---|---|
| `period_month` | datetime or period | Parsed monthly period from `period` |
| `expected_revenue` | float | Approximate revenue calculated as `sales * price / 100` |
| `revenue_diff` | float | Reported revenue minus approximate expected revenue |
| `revenue_abs_diff` | float | Absolute value of `revenue_diff` |
| `revenue_relative_diff` | float | Relative difference where denominator is meaningful |
| `flag_all_metrics_zero` | boolean | True when all four main numeric metrics are zero |
| `flag_any_metric_zero` | boolean | True when any main numeric metric is zero |
| `flag_negative_revenue` | boolean | True when `revenue < 0` |
| `flag_transportation_sector` | boolean | True when `sectorid == "TRA"` |

## Interpretation Boundaries

This dataset supports analysis of public EIA electricity retail sales patterns by state, month, and sector.

It does not directly provide:

- Utility-level operational details.
- Customer-level records.
- Direct causal mechanisms.
- Observation-level reported/imputed/estimated flags.
- Complete transportation activity measures.
- Internal company operational data.

Any project conclusion must stay within these boundaries.
