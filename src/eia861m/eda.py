from __future__ import annotations

import pandas as pd


def add_time_features(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Add reusable monthly and annual time fields for EDA."""
    df = dataframe.copy()
    df["period_month"] = pd.to_datetime(df["period"], format="%Y-%m")
    df["year"] = df["period_month"].dt.year
    df["month"] = df["period_month"].dt.month
    df["month_name"] = df["period_month"].dt.month_name()
    return df


def add_safe_ratio_features(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Add ratio metrics while avoiding division by zero."""
    df = dataframe.copy()
    df["sales_per_customer"] = df["sales"].where(df["customers"] != 0) / df["customers"].where(
        df["customers"] != 0
    )
    df["revenue_per_customer"] = df["revenue"].where(df["customers"] != 0) / df["customers"].where(
        df["customers"] != 0
    )
    df["revenue_per_sales"] = df["revenue"].where(df["sales"] != 0) / df["sales"].where(
        df["sales"] != 0
    )
    return df


def build_national_monthly(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Aggregate core numeric metrics at the national-month level."""
    return (
        dataframe.groupby("period_month", as_index=False)
        .agg(
            sales=("sales", "sum"),
            revenue=("revenue", "sum"),
            customers=("customers", "sum"),
        )
        .sort_values("period_month")
    )


def build_sector_monthly(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Aggregate core numeric metrics at the sector-month level."""
    return (
        dataframe.groupby(["period_month", "sectorid", "sectorName"], as_index=False)
        .agg(
            sales=("sales", "sum"),
            revenue=("revenue", "sum"),
            customers=("customers", "sum"),
        )
        .sort_values(["sectorid", "period_month"])
    )


def build_national_annual(national_monthly: pd.DataFrame) -> pd.DataFrame:
    """Sum annual flows and average the monthly customer counts."""
    monthly = national_monthly.assign(year=national_monthly["period_month"].dt.year)
    annual = (
        monthly.groupby("year", as_index=False)
        .agg(
            sales=("sales", "sum"),
            revenue=("revenue", "sum"),
            avg_monthly_customers=("customers", "mean"),
        )
        .sort_values("year")
    )
    annual["implied_price_cents_kwh"] = 100 * annual["revenue"] / annual["sales"]
    return annual


def build_state_annual(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Sum state-year flows and average monthly customer counts."""
    state_monthly = dataframe.groupby(
        ["year", "period_month", "stateid", "stateDescription"], as_index=False
    ).agg(
        sales=("sales", "sum"),
        revenue=("revenue", "sum"),
        customers=("customers", "sum"),
    )
    return (
        state_monthly.groupby(["year", "stateid", "stateDescription"], as_index=False)
        .agg(
            sales=("sales", "sum"),
            revenue=("revenue", "sum"),
            avg_monthly_customers=("customers", "mean"),
        )
        .sort_values(["year", "sales"], ascending=[True, False])
    )


def build_state_sector_annual(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Sum state-sector-year flows and average monthly customer counts."""
    return (
        dataframe.groupby(["year", "stateid", "stateDescription", "sectorid", "sectorName"], as_index=False)
        .agg(
            sales=("sales", "sum"),
            revenue=("revenue", "sum"),
            avg_monthly_customers=("customers", "mean"),
            zero_flag_count=("flag_any_metric_zero", "sum"),
            negative_revenue_count=("flag_negative_revenue", "sum"),
        )
        .sort_values(["year", "sales"], ascending=[True, False])
    )
