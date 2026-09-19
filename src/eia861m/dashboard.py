from __future__ import annotations

import pandas as pd

from .eda import add_time_features, build_national_annual, build_sector_monthly, build_state_annual, build_state_sector_annual


FLAG_COLUMNS = ("flag_any_metric_zero", "flag_all_metrics_zero", "flag_negative_revenue")
REQUIRED_COLUMNS = (
    "period", "stateid", "stateDescription", "sectorid", "sectorName",
    "sales", "revenue", "customers", "price", *FLAG_COLUMNS,
)


def prepare_data(frame: pd.DataFrame) -> pd.DataFrame:
    missing = sorted(set(REQUIRED_COLUMNS) - set(frame.columns))
    if missing:
        raise ValueError(f"Flagged validation CSV is missing columns: {missing}")
    data = add_time_features(frame)
    for column in ("sales", "revenue", "customers"):
        data[column] = pd.to_numeric(data[column], errors="raise")
    for column in FLAG_COLUMNS:
        if data[column].dtype != bool:
            values = data[column].astype(str).str.lower()
            if not values.isin(("true", "false")).all():
                raise ValueError(f"Invalid boolean values in {column}")
            data[column] = values.eq("true")
    if data.duplicated(("period", "stateid", "sectorid")).any():
        raise ValueError("Duplicate period-state-sector keys in flagged validation CSV")
    return data


def annual_scope(data: pd.DataFrame, state: str | None = None, sector: str | None = None) -> pd.DataFrame:
    scoped = data
    if state is not None:
        scoped = scoped.loc[scoped["stateid"] == state]
    if sector is not None:
        scoped = scoped.loc[scoped["sectorid"] == sector]
    monthly = (
        scoped.groupby("period_month", as_index=False)
        .agg(sales=("sales", "sum"), revenue=("revenue", "sum"), customers=("customers", "sum"))
    )
    annual = build_national_annual(monthly)
    annual["implied_price_cents_kwh"] = annual["implied_price_cents_kwh"].where(annual["sales"] != 0)
    for column in ("sales", "revenue"):
        prior = annual[column].shift()
        annual[f"{column}_yoy"] = (annual[column] / prior - 1).where(prior.ne(0) & prior.notna())
    return annual


def sector_shares(data: pd.DataFrame, year: int) -> pd.DataFrame:
    selected = data.loc[data["year"] == year]
    result = (
        selected.groupby(["sectorid", "sectorName"], as_index=False)
        .agg(sales=("sales", "sum"), revenue=("revenue", "sum"))
    )
    for column in ("sales", "revenue"):
        total = selected[column].sum()
        result[f"{column}_share"] = result[column] / total if total != 0 else float("nan")
    return result.sort_values("sales", ascending=False)


def state_ranking(data: pd.DataFrame, year: int) -> pd.DataFrame:
    result = build_state_annual(data).loc[lambda frame: frame["year"] == year].copy()
    national_sales = result["sales"].sum()
    result["national_sales_share"] = result["sales"] / national_sales if national_sales != 0 else float("nan")
    return result.sort_values("sales", ascending=False)


def state_sector_table(data: pd.DataFrame, year: int) -> pd.DataFrame:
    result = build_state_sector_annual(data).loc[lambda frame: frame["year"] == year].copy()
    total = data.loc[data["year"] == year, "sales"].sum()
    result["national_sales_share"] = result["sales"] / total if total != 0 else float("nan")
    result["implied_price_cents_kwh"] = (100 * result["revenue"] / result["sales"]).where(result["sales"] != 0)
    return result


def monthly_scope(data: pd.DataFrame, state: str | None = None, sector: str | None = None) -> pd.DataFrame:
    scoped = data
    if state is not None:
        scoped = scoped.loc[scoped["stateid"] == state]
    if sector is not None:
        scoped = scoped.loc[scoped["sectorid"] == sector]
    return (
        scoped.groupby("period_month", as_index=False)
        .agg(sales=("sales", "sum"))
        .sort_values("period_month")
    )


def monthly_investigation(data: pd.DataFrame, period: str) -> pd.DataFrame:
    """Compare each state-sector with the same month in the previous year."""
    current_month = pd.Period(period, freq="M")
    prior_month = current_month - 12
    keys = ["stateid", "sectorid"]
    values = ["sales", "revenue", "customers", *FLAG_COLUMNS]
    current = data.loc[
        data["period"] == str(current_month),
        [*keys, "stateDescription", "sectorName", *values],
    ].copy()
    if current.empty:
        raise ValueError(f"No observations for {period}")

    prior = data.loc[data["period"] == str(prior_month), [*keys, *values]].rename(
        columns={column: f"{column}_prior" for column in values}
    )
    first_month = data["period_month"].min().to_period("M")
    if prior_month >= first_month and len(prior) != len(current):
        raise ValueError(f"State-sector coverage differs between {period} and {prior_month}")

    result = current.merge(prior, on=keys, how="left", validate="one_to_one", indicator=True)
    if not prior.empty and result["_merge"].ne("both").any():
        raise ValueError(f"State-sector keys differ between {period} and {prior_month}")
    result["has_prior"] = result["_merge"].eq("both")
    result = result.drop(columns="_merge")
    for column in FLAG_COLUMNS:
        result[f"{column}_prior"] = result[f"{column}_prior"].eq(True)

    result["implied_price_cents_kwh"] = (100 * result["revenue"] / result["sales"]).where(result["sales"] > 0)
    result["implied_price_cents_kwh_prior"] = (
        100 * result["revenue_prior"] / result["sales_prior"]
    ).where(result["sales_prior"] > 0)
    for column in ("sales", "revenue", "customers", "implied_price_cents_kwh"):
        prior_column = f"{column}_prior"
        result[f"{column}_change"] = result[column] - result[prior_column]
        result[f"{column}_change_pct"] = (
            100 * result[f"{column}_change"] / result[prior_column]
        ).where(result[prior_column] > 0)
    return result.sort_values(keys).reset_index(drop=True)


def seasonal_profile(data: pd.DataFrame) -> pd.DataFrame:
    monthly = build_sector_monthly(data.loc[data["sectorid"].isin(("RES", "COM", "IND"))]).copy()
    monthly["year"] = monthly["period_month"].dt.year
    monthly["month"] = monthly["period_month"].dt.month
    typical = monthly.groupby(["sectorid", "year"])["sales"].transform("mean")
    monthly["index"] = (monthly["sales"] / typical).where(typical != 0)
    return (
        monthly.groupby(["sectorid", "month"], as_index=False)
        .agg(index=("index", "mean"))
        .sort_values(["sectorid", "month"])
    )


def quality_counts(data: pd.DataFrame, year: int) -> pd.DataFrame:
    return (
        data.loc[data["year"] == year]
        .groupby("sectorid", as_index=False)
        .agg(
            observations=("period", "size"),
            any_zero=("flag_any_metric_zero", "sum"),
            all_zero=("flag_all_metrics_zero", "sum"),
            negative_revenue=("flag_negative_revenue", "sum"),
        )
        .sort_values("sectorid")
    )


def flagged_observations(data: pd.DataFrame, year: int, sector: str | None = None) -> pd.DataFrame:
    selected = data.loc[data["year"] == year]
    if sector is not None:
        selected = selected.loc[selected["sectorid"] == sector]
    flagged = selected.loc[selected[list(FLAG_COLUMNS)].any(axis=1)]
    columns = ["period", "stateid", "sectorid", "customers", "price", "revenue", "sales", *FLAG_COLUMNS]
    return flagged[columns].sort_values(["flag_negative_revenue", "period", "stateid"], ascending=[False, True, True])
