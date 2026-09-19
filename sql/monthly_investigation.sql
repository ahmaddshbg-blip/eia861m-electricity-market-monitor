-- Rank state-sector observations by absolute sales change from the same month
-- in the previous year. :period and :prior_period are bound by the runner.
WITH compared AS (
    SELECT
        current.period,
        current.stateid,
        current.stateDescription,
        current.sectorid,
        current.sectorName,
        current.sales AS sales_million_kwh,
        prior.sales AS sales_prior_million_kwh,
        current.sales - prior.sales AS sales_change_million_kwh,
        current.revenue AS revenue_million_usd,
        prior.revenue AS revenue_prior_million_usd,
        current.customers AS customers,
        prior.customers AS customers_prior,
        CASE WHEN current.sales > 0 THEN 100.0 * current.revenue / current.sales END
            AS implied_price_cents_kwh,
        CASE WHEN prior.sales > 0 THEN 100.0 * prior.revenue / prior.sales END
            AS implied_price_prior_cents_kwh,
        current.flag_any_metric_zero AS flag_any_metric_zero,
        prior.flag_any_metric_zero AS flag_any_metric_zero_prior,
        current.flag_negative_revenue AS flag_negative_revenue,
        prior.flag_negative_revenue AS flag_negative_revenue_prior
    FROM retail_sales AS current
    JOIN retail_sales AS prior
      ON prior.stateid = current.stateid
     AND prior.sectorid = current.sectorid
     AND prior.period = :prior_period
    WHERE current.period = :period
)
SELECT
    ROW_NUMBER() OVER (
        ORDER BY ABS(sales_change_million_kwh) DESC, stateid, sectorid
    ) AS investigation_rank,
    period,
    stateid,
    stateDescription,
    sectorid,
    sectorName,
    sales_million_kwh,
    sales_prior_million_kwh,
    sales_change_million_kwh,
    CASE WHEN sales_prior_million_kwh > 0
         THEN 100.0 * sales_change_million_kwh / sales_prior_million_kwh END
        AS sales_change_pct,
    revenue_million_usd,
    revenue_prior_million_usd,
    CASE WHEN revenue_prior_million_usd > 0
         THEN 100.0 * (revenue_million_usd - revenue_prior_million_usd) / revenue_prior_million_usd END
        AS revenue_change_pct,
    customers,
    customers_prior,
    CASE WHEN customers_prior > 0
         THEN 100.0 * (customers - customers_prior) / customers_prior END
        AS customers_change_pct,
    implied_price_cents_kwh,
    implied_price_prior_cents_kwh,
    implied_price_cents_kwh - implied_price_prior_cents_kwh
        AS implied_price_change_cents_kwh,
    flag_any_metric_zero,
    flag_any_metric_zero_prior,
    flag_negative_revenue,
    flag_negative_revenue_prior
FROM compared
ORDER BY investigation_rank;
