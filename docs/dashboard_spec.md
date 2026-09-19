# Market Monitoring Dashboard Specification

## Status And Purpose

- Project: Electricity Retail Sales Decision Intelligence
- Status: Monthly investigation implemented and technically checked on 2026-09-18; user visual review and public deployment pending
- Design date: 2026-09-17
- Evidence base: `docs/eda_findings.md` and the flagged EIA-861M dataset for 2016-01 through 2025-12

The working user is an energy market analyst or planning analyst comparing published U.S. electricity retail sales by year, sector, and state. This is a portfolio scenario, not a claim that a particular company requested or used the dashboard.

The dashboard should help the user identify changes and segments worth further investigation. It must not recommend utility tariffs, investments, policy actions, or company-specific operational decisions from these public data alone.

## Approved Business Problem (2026-09-18)

| Element | Project 01 definition |
|---|---|
| Context | A hypothetical U.S. energy-market analyst monitors published EIA-861M retail electricity sales by state and end-use sector. No company commissioned or used this project. |
| Problem | There are 204 state-sector observations per month. Differences in scale, seasonality, and data quality make it difficult to decide where to investigate first from raw tables alone. |
| Objective | Prioritize state-sector observations for monthly market investigation when sales, nominal revenue, customer counts, or implied average price change conspicuously. |
| Decision | Select a short list of state-sector observations for deeper analyst review after each published month. This is an attention-allocation decision, not a tariff, investment, or policy recommendation. |
| Success criterion | For a selected published month, the analyst can compare each state-sector with the same month one year earlier, see absolute and percentage changes with units, inspect quality flags and historical context, and export the selected rows. No automated anomaly label or claimed business impact is required. |
| Scope | The current fixed snapshot covers 2016-01 through 2025-12. RES, COM, and IND are the primary comparison sectors; TRA remains visible with quality cautions. A monthly refresh workflow is future work; forecasting is out of scope for Project 01. |

The selected-month investigation table implements the comparison and analyst shortlisting workflow and has passed user visual review. The December 2025 example is documented in `reports/market_investigation_2025_12.md`. A clean-environment publication test remains pending. Rankings must not silently become anomaly or causal claims. Forecasting is excluded from Project 01 and remains a core competency of Portfolio Project 02.

The table compares each observation with the same calendar month one year earlier to avoid treating ordinary seasonality as an unexplained change. It shows both absolute and percentage differences; percentage change is unavailable when the prior value is zero or negative, and 2016 has no prior-year comparison in this snapshot. Small positive baselines can still produce unstable percentages. Implied price is calculated from revenue and sales at the same state-sector-month grain and is unavailable when sales are zero. Current and prior quality flags remain visible in the quality note. No automatic combined priority score is assigned.

## Questions And Decisions

| User question | Evidence shown | Supported next action |
|---|---|---|
| How did the national market change? | Annual sales, nominal revenue, implied price, and year-over-year changes | Flag a year or metric for closer descriptive review |
| Which sectors contribute most? | Sales and revenue share in the same selected year | Choose sectors for comparison without confusing volume and revenue |
| Which states and state-sector segments stand out? | State sales share ranking and sortable state-sector table | Prioritize segments for deeper analysis |
| Which state-sector observations changed most in a selected month? | Same-month-prior-year absolute and percentage changes, quality flags, and historical context (planned) | Choose a short list for investigation, not an automatic business action |
| Is there a recurring monthly pattern? | Monthly sales series and within-year seasonal index for RES, COM, and IND | Plan monitoring around recurring peaks while keeping forecasting unproven |
| When should an observation be treated cautiously? | Counts and details of published zero values and negative revenue flags | Read the quality note before interpreting a segment |

## MVP Views

| View | Primary contents | User control |
|---|---|---|
| Monthly investigation | Selected-month state-sector comparisons with same-month-prior-year changes, quality notes, historical series, and analyst-selected CSV shortlist | Year and month selectors; state, sector, metric, and ordering controls |
| National overview | Selected-year KPI strip; 2016-2025 annual sales, revenue, and implied price trends; selected-year sector shares | Year selector, default 2025 |
| Segment explorer | Selected-year state sales ranking; sortable state-sector table; monthly sales trend for the selected state-sector; seasonal profile for RES, COM, and IND | State and sector selectors within this view |
| Data quality and method | Flag counts by sector for the selected year; flagged observation table; concise source, units, and interpretation notes | Year and optional sector selector |

The national overview remains national when a state or sector is selected in the segment explorer. The selected year is shared across views. Historical trend and seasonal charts must label their full 2016-2025 window even when the selected year is highlighted.

The first screen opens on monthly investigation because it serves the approved decision. National overview remains available as a separate view. The annual state-sector table supports sorting and CSV export of its filtered rows; the monthly table exports analyst-selected rows. Method notes remain accessible from every view without dominating the main workflow.

## KPI Contract

| KPI | Calculation | Display and boundary |
|---|---|---|
| Annual sales | Sum of `sales` over all 12 months and the selected geography/sector | Show TWh (`million kWh / 1000`); source is retail electricity sales |
| Annual nominal revenue | Sum of `revenue` over all 12 months and the selected geography/sector | Show billion USD (`million USD / 1000`); no inflation adjustment |
| Implied average price | `100 * sum(revenue) / sum(sales)` for the same scope | Nominal cents/kWh; undefined when sales is zero; not a tariff |
| Average monthly customers | Mean of the 12 monthly customer counts after summing across the selected state-sector observations within each month | Show as a monthly average; never sum month counts and call them annual unique customers |
| Annual sales/revenue growth | Current full-year total divided by the prior full-year total for the same scope, minus one | Not available for 2016 or when the prior denominator is zero |
| Sector share | Selected-sector annual sales or revenue divided by the corresponding national annual total for the same year | Denominator stays national and unfiltered by the sector selector |
| State share | Selected-state annual sales divided by national annual sales for the same year | Denominator stays national and unfiltered by the state selector |
| Seasonal sales index | Monthly sector sales divided by that sector-year's average monthly sales, then averaged over years | An index of 1.0 is that year's average month; RES, COM, and IND only in the MVP |

If the user selects one state-sector, monthly customer counts are shown at that grain and annual customer indicators remain averages of monthly counts. A mean of published state prices must not replace the revenue-to-sales calculation.

## Quality And Interpretation Rules

- Preserve every published row, including zeros and the one small negative revenue value. Flags provide context; they are not automatic deletion rules.
- Show a visible caution when TRA is selected: 2,646 of the full dataset's TRA observations had at least one zero metric. A selected-year count must be calculated for that year, not copied from the full-period total.
- Show the DC-TRA 2022-02 negative-revenue record in the flagged-observation table when that year and sector are in scope.
- Label revenue and implied price as nominal and unadjusted for inflation. Sector and state contributions are shares of the published EIA totals, not company market shares.
- Provide a methodology link to `docs/data_provenance.md`, `docs/data_quality.md`, and `docs/eda_findings.md` in the portfolio version.

## Data And Reproducibility

The local MVP reads the flagged interim CSV using the configured project path. The dashboard must use the same aggregation rules as `src/eia861m/eda.py` and must not call the EIA API or require an API key during normal viewing.

The current `.gitignore` excludes `data/interim/`, so a shared or deployed dashboard will need a reproducible data build step or a small versioned, derived data artifact before publication. That packaging decision belongs to implementation; a working local notebook alone does not make the dashboard reproducible for another user.

The local Streamlit implementation is `app.py` with aggregation helpers in `src/eia861m/dashboard.py`. It reads the configured flagged CSV, or an existing file selected through `EIA861M_DATA_PATH`. The synthetic aggregation tests pass, the 2025 acceptance values match the reviewed CSV, and the 2022 TRA quality view retains the DC negative-revenue observation. Browser-level visual QA and public deployment are not yet complete.

## Acceptance Checks

- With year 2025 and national scope, display about 4,058.01 TWh sales, 553.28 billion USD nominal revenue, 13.63 nominal cents/kWh implied price, and 164.51 million average monthly customers.
- For 2025, RES shows about 37.3% of sales and 47.4% of revenue; Texas shows about 12.8% of national sales.
- Selecting a state or sector does not silently change the denominator of a national share.
- Year changes update annual KPIs, sector shares, state ranking, and quality counts consistently. Historical panels retain clearly labeled full-period context.
- TRA zero flags and the negative revenue record remain visible in the relevant quality view.
- No annual customer total is formed by summing monthly customer counts; no national price is formed by averaging state prices.
- Forecasts, model accuracy, and causal explanations are absent from Project 01 by scope decision. Predictive evaluation belongs to Portfolio Project 02.
- For 2025-12, the monthly investigation table contains 204 unique state-sector rows and 204 prior-year comparisons. For 2016-01, prior-year changes are unavailable rather than zero.
- Filtering the monthly table to TRA in 2022-02 retains the DC observation and its negative-revenue quality context.
