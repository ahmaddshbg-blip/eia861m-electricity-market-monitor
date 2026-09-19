# EDA Design

## Status

Analytical design document for the exploratory data analysis stage of Project 01.

- Project: Project 01 - EIA-861M Electricity Retail Sales Analytics
- Last updated: 2026-09-17
- Current stage: Descriptive EDA reviewed; monthly investigation MVP technically checked; user visual review pending
- Prior gate: Acquisition and structural validation passed

## Project Framing

Working title:

```text
Electricity Retail Sales Decision Intelligence
```

Analytical framing:

```text
Analyzing state-sector electricity demand, revenue, customer base, and price patterns to support market monitoring and planning.
```

This project is a Business Analytics and Decision Intelligence project. Early EDA planning considered a light predictive extension, but the current Project 01 scope excludes forecasting. The candidate-series discussion below records the earlier exploratory option; it is not a current implementation plan. Forecasting is reserved for Portfolio Project 02.

## EDA Objective

The EDA stage should answer:

> What are the major state, sector, temporal, price, revenue, customer, and sales patterns in EIA-861M electricity retail sales data, and which patterns are decision-relevant enough to support monitoring, segmentation, or light forecasting?

The EDA should produce a defensible analytical foundation for:

- KPI design;
- sector and state comparison;
- market monitoring;
- anomaly awareness;
- business interpretation;
- later dashboard design;
- possible lightweight forecasting.

The EDA should not become a gallery of unrelated charts.

## Primary Analytical Questions

### 1. Market Size And Trend

How did electricity retail sales, revenue, customer count, and average retail price change from 2016 to 2025?

Useful views:

- national monthly trend;
- national annual trend;
- sector-level monthly and annual trend;
- state-level contribution.

Decision relevance:

- identify broad growth, decline, or stability;
- understand market scale;
- support high-level monitoring.

### 2. Sector Structure

How do `RES`, `COM`, `IND`, and `TRA` differ in sales, revenue, customer count, and price?

Useful views:

- sector share of total sales;
- sector share of revenue;
- price distribution by sector;
- customer base by sector;
- sector growth and volatility.

Decision relevance:

- identify dominant segments;
- distinguish high-volume and high-price segments;
- avoid treating all sectors as analytically equivalent.

### 3. State Contribution And Concentration

Which states contribute the most to electricity sales and revenue, and how concentrated is the market?

Useful views:

- top states by sales;
- top states by revenue;
- state share of national totals;
- cumulative contribution by rank;
- annual state contribution changes.

Decision relevance:

- identify high-impact geographies;
- support prioritization and monitoring;
- avoid overgeneralizing national trends.

### 4. State-Sector Patterns

Which state-sector combinations stand out by volume, revenue, customer base, price, growth, or volatility?

Useful views:

- state-sector annual summaries;
- top state-sector combinations by sales and revenue;
- sector mix by state;
- price variation by state-sector;
- volatility by state-sector.

Decision relevance:

- identify segments that may deserve separate treatment;
- prepare candidates for dashboard segmentation;
- identify possible candidates for light forecasting.

### 5. Seasonality And Volatility

Do sales, revenue, or price show recurring seasonal patterns?

Useful views:

- month-of-year profile by sector;
- seasonal index by sector;
- monthly volatility by sector;
- state-sector volatility ranking.

Decision relevance:

- distinguish structural trend from seasonality;
- decide whether forecasting is justified;
- identify segments where naive baselines may already be strong.

### 6. Price, Sales, And Revenue Relationship

How do sales, price, and revenue relate across sectors and states?

Useful views:

- revenue versus sales by sector;
- average retail price distribution;
- revenue per customer;
- sales per customer;
- approximate revenue consistency check context.

Decision relevance:

- understand whether revenue differences are driven mainly by volume, price, or customer base;
- avoid interpreting average price as a tariff;
- avoid causal claims about price response.

### 7. Data Quality Awareness In Analysis

How do zero values, `TRA` patterns, and the negative revenue anomaly affect interpretation?

Useful views:

- counts of quality flags by sector;
- `TRA` zero patterns over time and state;
- explicit display of the negative revenue anomaly;
- sensitivity notes for metrics affected by zero values.

Decision relevance:

- prevent misleading business interpretation;
- keep data-quality findings separate from business conclusions;
- preserve methodological defensibility.

## KPI Candidates

Only use KPIs that are directly supported by the EIA-861M data.

| KPI | Formula / Source | Primary use | Caution |
|---|---|---|---|
| Total sales | Sum of `sales` | Demand/volume scale | Sales are electricity retail sales to ultimate customers |
| Total revenue | Sum of `revenue` | Revenue scale | Public EIA revenue, not company revenue |
| Monthly customer count | Sum of `customers` across states and sectors within a month | Monthly customer base scale | Counts are not necessarily unique people across sectors |
| Average monthly customers in a year | Mean of the 12 monthly aggregate customer counts | Annual customer base indicator | Never sum monthly counts and label the result annual unique customers |
| Aggregate average retail price | `100 * sum(revenue) / sum(sales)` in cents/kWh | Price monitoring | Undefined for zero sales; not a tariff or a simple mean of state prices |
| Sales per customer | `sales / customers` | Intensity indicator | Undefined or misleading when customers are zero |
| Revenue per customer | `revenue / customers` | Customer-level revenue indicator | Undefined or misleading when customers are zero |
| Revenue per sales | `revenue / sales` | Implied average revenue per kWh | Handle zero sales carefully |
| Sector share of sales | Sector sales / total sales | Sector structure | Scope depends on aggregation level |
| State contribution | State sales or revenue / national total | Geographic concentration | Not causal |
| YoY growth | Current period vs same period prior year | Growth monitoring | Requires temporal alignment |
| Month-over-month change | Current month vs previous month | Short-term monitoring | Can be noisy |
| Volatility | Standard deviation or coefficient of variation | Stability/risk monitoring | Avoid overinterpreting small denominators |
| Seasonal profile | Average by calendar month | Seasonality | Descriptive, not causal |

The first executed EDA notebook exposed an aggregation error: summing 2025 monthly customer counts produced 1,974,119,645 customer-months, while the average monthly count was 164,509,970.42. Annual and multi-year summaries now use `avg_monthly_customers` and retain sales and revenue as sums. These counts should not be described as unique individuals or unique accounts across the year.

## Preferred Aggregation Levels

EDA should move from broad to granular:

1. National x month
2. National x sector x month
3. National x year
4. National x sector x year
5. State x year
6. State x sector x year
7. State x sector x month for selected deep dives

Do not start with highly granular state-sector-month charts for all combinations; that creates visual noise before analytical direction is clear.

## Source Dataset For EDA

Use the flagged interim dataset as the EDA input:

```text
data/interim/eia861m_retail_sales_2016_2025_with_quality_flags.csv
```

This dataset preserves published values and adds explicit quality flags.

Raw data should remain unchanged:

```text
data/raw/eia861m_retail_sales_2016_2025.csv
```

## Required EDA Outputs

The EDA stage should produce:

- a clean EDA notebook: `notebooks/02_exploratory_data_analysis.ipynb`;
- reusable aggregation functions if logic becomes repeated;
- selected figures saved to `reports/figures/`;
- a concise EDA findings document or section later used in the README;
- documented decisions about which KPIs are retained for dashboarding;
- documented candidates for light forecasting.

Four selected figures were generated from the EDA notebook and reviewed:

| Figure | Question answered | Interpretation boundary |
|---|---|---|
| `01_national_annual_trends.png` | How did annual sales, revenue, and implied aggregate price move from 2016 to 2025? | Separate vertical scales; revenue and price are not inflation-adjusted; price is a ratio, not a tariff or causal driver |
| `02_sector_mix_latest_year.png` | What shares of national sales and revenue came from each sector in 2025? | Uses 2025 only; do not mix with the pooled 2016-2025 sector summary |
| `03_top_state_sales_share_latest_year.png` | Which states had the largest shares of national sales in 2025? | Descriptive contribution, not a causal or investment ranking |
| `04_sector_monthly_sales_index.png` | Do RES, COM, and IND show recurring within-year sales patterns? | Each year is normalized separately; TRA is excluded because of zero-heavy observations |

## Suggested EDA Notebook Structure

```text
1. Purpose and scope
2. Load flagged interim data
3. Validate expected input shape and flags
4. Build reusable time and aggregation fields
5. National trend overview
6. Sector trend overview
7. State contribution analysis
8. State-sector segmentation
9. Seasonality and volatility
10. Price, sales, revenue relationship
11. Data-quality interpretation guardrails
12. Candidate KPIs for dashboard
13. Candidate segments for light forecasting
14. EDA conclusions and limitations
```

## Business Analytics Scope

The Business Analytics component should focus on:

- monitoring market scale;
- identifying dominant sectors and states;
- comparing segment trends;
- identifying high-volatility or high-growth segments;
- creating defensible KPI candidates;
- supporting dashboard design.

It should not claim:

- internal utility operational performance;
- company-specific business impact;
- causal effect of price on demand;
- policy impact;
- total transportation activity;
- forecast value before a baseline is tested.

## Light Predictive Scope

Prediction is optional and should be introduced only after EDA identifies a justified target.

Candidate target:

```text
monthly sales
```

Candidate levels:

- national x sector monthly sales;
- selected high-volume state-sector monthly sales;
- selected stable state-sector monthly sales.

Candidate baselines:

- naive forecast;
- seasonal naive forecast;
- historical monthly average.

Candidate forecast horizon:

```text
3 to 6 months
```

Minimum rule:

No ML model should be introduced before a meaningful baseline is built and evaluated.

## Forecasting Readiness Criteria

A segment becomes a reasonable forecasting candidate only if:

- it has complete monthly history;
- its target is not dominated by structural zeros;
- the target has meaningful scale;
- the pattern is interpretable enough for a business user;
- a baseline can be defined clearly;
- the evaluation split can be chronological;
- the forecasting use case can be explained.

Segments with heavy `TRA` zero patterns should not be used for forecasting without separate justification.

## Interpretation Boundaries

All EDA conclusions must respect these boundaries:

- The data is public EIA data, not internal company data.
- EIA-861M is not raw transaction-level utility data.
- The dataset has no observation-level reported/imputed/estimated flag.
- Published zero values are retained and not automatically treated as missing.
- `TRA` is an EIA electricity end-use sector classification, not all transportation activity.
- Average retail price is not automatically a tariff.
- Prediction is not explanation.
- Correlation is not causation.
- Feature importance, if later used, is not causal evidence.

## EDA Gate Checklist

The descriptive EDA stage is ready for dashboard design after:

- [x] EDA notebook loads the flagged interim dataset, not raw data directly.
- [x] Key KPI definitions are documented.
- [x] Aggregation levels are explicit.
- [x] National, sector, state, and state-sector patterns are summarized.
- [x] Quality flags are included in interpretation.
- [x] `TRA` limitations are explicitly handled.
- [x] At least one concise findings summary exists in `docs/eda_findings.md`.
- [x] Candidate dashboard KPIs are selected in `docs/eda_findings.md`.
- [x] Candidate monthly sales series for later baseline experiments are identified; forecast value is still untested.
- [x] Limitations are documented.

## Immediate Next Step

Use the reviewed selected-month workflow and the December 2025 example in `reports/market_investigation_2025_12.md` to assess the decision-support narrative. Address reproducible data packaging and the remaining Project 01 BI/SQL evidence before publication. Forecasting is out of scope for Project 01 and is the core focus of Portfolio Project 02.
