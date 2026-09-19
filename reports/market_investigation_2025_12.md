# Monthly Market Investigation Brief: December 2025

- Status: Retrospective portfolio case study, reviewed 2026-09-18
- Source: Flagged EIA-861M state-sector monthly CSV for 2016-01 through 2025-12
- Decision supported: Which state-sector observations should a market analyst investigate first?
- Scope: Published U.S. retail electricity sales; no company-specific decision or measured business impact

## Selection Rule

Compare December 2025 with December 2024 at the same state-sector grain. Rank all 204 state-sector observations by the absolute change in `sales` (million kWh) and shortlist the first three. This rule favors material volume changes over large percentages from tiny baselines. Revenue, customer counts, implied average price, prior December changes, and quality flags provide context; they do not form a hidden composite score. The shortlist is an allocation of analyst attention, not an anomaly classification.

The comparison is descriptive. Using the same calendar month reduces simple seasonal mismatch but does not control for weather, economic activity, reporting revisions, or other drivers. No forecast is used in Project 01.

## Market Context

| National monthly measure | Dec 2024 | Dec 2025 | Change |
|---|---:|---:|---:|
| Retail sales (TWh) | 328.19 | 337.72 | +2.90% |
| Nominal revenue (billion USD) | 42.08 | 46.38 | +10.22% |
| Implied average price (nominal cents/kWh) | 12.82 | 13.73 | +0.91 cents/kWh |

Implied price is `100 * sum(revenue) / sum(sales)` at the stated scope, not a tariff or a mean of state prices.

## Investigation Shortlist

| Rank | State-sector | Sales change (million kWh) | Sales YoY | Revenue YoY | Customers YoY | Implied price change (cents/kWh) |
|---:|---|---:|---:|---:|---:|---:|
| 1 | California residential (CA-RES) | -1,152.16 | -16.31% | -5.13% | +1.94% | +4.09 |
| 2 | Texas residential (TX-RES) | +1,095.78 | +9.90% | +13.61% | +1.80% | +0.52 |
| 3 | Ohio commercial (OH-COM) | +1,031.41 | +24.49% | +43.63% | -0.47% | +1.63 |

None of these three observations, nor their December 2024 comparators, carry an `any metric zero` or `negative revenue` flag. That does not prove every underlying value was directly observed or free from reporting revisions.

### 1. CA-RES: Largest Absolute Decline

Published sales fell from 7,063.34 to 5,911.18 million kWh. This -16.31% December YoY change is lower than the prior December YoY range of -14.39% to +10.83% observed for CA-RES in 2017-2024. Nominal revenue fell only 5.13%, while the implied price rose from 30.62 to 34.71 cents/kWh and the monthly customer count rose 1.94%. The revenue-volume difference is arithmetic context, not evidence of why either quantity changed. Investigate whether the decline persists in adjacent months and seek external weather, reporting, and rate-context evidence before explaining it.

### 2. TX-RES: Largest Absolute Increase

Published sales rose from 11,067.52 to 12,163.29 million kWh. Its +9.90% December YoY change is material in volume, but lies within the prior December YoY range of -13.16% to +23.42% for 2017-2024. Nominal revenue rose 13.61%; implied price increased by 0.52 cents/kWh and the monthly customer count rose 1.80%. Investigate the volume shift because of scale, without calling its percentage historically unprecedented.

### 3. OH-COM: Largest Relative Shift Among the Three

Published sales rose from 4,211.86 to 5,243.27 million kWh. Its +24.49% December YoY increase exceeds the prior December YoY range of -3.20% to +9.36% for OH-COM in 2017-2024. Nominal revenue rose 43.63%, implied price increased by 1.63 cents/kWh, and the monthly customer count was 0.47% lower. This makes OH-COM the strongest candidate for checking whether the change reflects a persistent pattern, an unusual month, or reporting/context changes. The nine December YoY comparisons are a small descriptive sample, not a statistical anomaly test.

## Analyst Decision And Limits

The proposed next action is to review CA-RES, TX-RES, and OH-COM in that order of absolute sales change, while giving OH-COM particular attention for its larger relative shift against its own December history. For each, check adjacent months, EIA revisions and definitions, and relevant external context before attributing causes. No tariff, investment, procurement, or company policy action follows from this brief alone.

This is a retrospective demonstration using a fixed data snapshot, not a live monthly monitoring service. It establishes that the dashboard can produce a traceable shortlist, not that a real organization saved time or improved a decision. No forecasting is performed; the forecasting portfolio project is separate.

## Reproduction

Use the configured flagged interim CSV and open `app.py`. In **Monthly investigation**, set reporting year to 2025 and month to `2025-12`; keep all states and sectors; choose **Sales** and **Largest absolute change**. The first three rows reproduce the shortlist. Use the metric selector and historical series to inspect the supporting context. The aggregation and same-month-prior-year calculations are implemented in `src/eia861m/dashboard.py` and covered by `tests/test_dashboard.py`.
