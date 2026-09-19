from __future__ import annotations

from typing import Any

import pandas as pd


REQUIRED_COLUMNS = [
    "period",
    "stateid",
    "stateDescription",
    "sectorid",
    "sectorName",
    "customers",
    "price",
    "revenue",
    "sales",
    "customers-units",
    "price-units",
    "revenue-units",
    "sales-units",
]

NUMERIC_COLUMNS = ["customers", "price", "revenue", "sales"]
KEY_COLUMNS = ["period", "stateid", "sectorid"]


def coerce_numeric_columns(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Return a copy with project numeric columns converted to numeric values."""
    df = dataframe.copy()
    for column in NUMERIC_COLUMNS:
        df[column] = pd.to_numeric(df[column], errors="raise")
    return df


def validate_required_columns(dataframe: pd.DataFrame) -> None:
    """Raise an error if required API columns are missing."""
    missing_columns = [column for column in REQUIRED_COLUMNS if column not in dataframe.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")


def add_quality_flags(
    dataframe: pd.DataFrame,
    revenue_abs_tolerance_million_usd: float,
) -> pd.DataFrame:
    """Add conservative quality flags without deleting or imputing observations."""
    validate_required_columns(dataframe)
    df = coerce_numeric_columns(dataframe)

    df["period_month"] = pd.to_datetime(df["period"], format="%Y-%m")
    df["expected_revenue"] = df["sales"] * df["price"] / 100
    df["revenue_diff"] = df["revenue"] - df["expected_revenue"]
    df["revenue_abs_diff"] = df["revenue_diff"].abs()

    denominator = df["revenue"].abs()
    df["revenue_relative_diff"] = df["revenue_abs_diff"].where(denominator == 0, df["revenue_abs_diff"] / denominator)

    df["flag_all_metrics_zero"] = (df[NUMERIC_COLUMNS] == 0).all(axis=1)
    df["flag_any_metric_zero"] = (df[NUMERIC_COLUMNS] == 0).any(axis=1)
    df["flag_negative_revenue"] = df["revenue"] < 0
    df["flag_transportation_sector"] = df["sectorid"] == "TRA"
    df["flag_revenue_consistency_check"] = (
        df["revenue_abs_diff"] > revenue_abs_tolerance_million_usd
    )

    return df


def build_validation_summary(dataframe: pd.DataFrame, config: dict[str, Any]) -> dict[str, Any]:
    """Build a compact validation summary for documentation and review."""
    validate_required_columns(dataframe)
    df = coerce_numeric_columns(dataframe)
    validation_config = config["validation"]

    duplicate_key_count = int(df.duplicated(subset=KEY_COLUMNS).sum())
    missing_counts = {column: int(value) for column, value in df.isna().sum().items()}
    zero_counts = {column: int((df[column] == 0).sum()) for column in NUMERIC_COLUMNS}
    negative_counts = {column: int((df[column] < 0).sum()) for column in NUMERIC_COLUMNS}

    rows_per_state = df.groupby("stateid").size()
    rows_per_sector = df.groupby("sectorid").size()
    rows_per_period = df.groupby("period").size()

    summary = {
        "row_count": int(len(df)),
        "column_count": int(len(df.columns)),
        "unique_months": int(df["period"].nunique()),
        "unique_states": int(df["stateid"].nunique()),
        "unique_sectors": int(df["sectorid"].nunique()),
        "duplicate_key_count": duplicate_key_count,
        "missing_counts": missing_counts,
        "zero_counts": zero_counts,
        "negative_counts": negative_counts,
        "rows_per_state_distribution": {
            str(index): int(value) for index, value in rows_per_state.value_counts().sort_index().items()
        },
        "rows_per_sector": {str(index): int(value) for index, value in rows_per_sector.sort_index().items()},
        "rows_per_period_distribution": {
            str(index): int(value) for index, value in rows_per_period.value_counts().sort_index().items()
        },
        "expected": {
            "rows": int(validation_config["expected_rows"]),
            "months": int(validation_config["expected_months"]),
            "states": int(validation_config["expected_states"]),
            "sectors": int(validation_config["expected_sectors"]),
        },
    }

    _assert_expected_coverage(summary)
    return summary


def _assert_expected_coverage(summary: dict[str, Any]) -> None:
    expected = summary["expected"]
    failures = []

    if summary["row_count"] != expected["rows"]:
        failures.append(f"row_count={summary['row_count']} expected={expected['rows']}")
    if summary["unique_months"] != expected["months"]:
        failures.append(f"unique_months={summary['unique_months']} expected={expected['months']}")
    if summary["unique_states"] != expected["states"]:
        failures.append(f"unique_states={summary['unique_states']} expected={expected['states']}")
    if summary["unique_sectors"] != expected["sectors"]:
        failures.append(f"unique_sectors={summary['unique_sectors']} expected={expected['sectors']}")
    if summary["duplicate_key_count"] != 0:
        failures.append(f"duplicate_key_count={summary['duplicate_key_count']} expected=0")

    if failures:
        raise ValueError("Validation failed: " + "; ".join(failures))
