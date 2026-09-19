"""Run the portfolio's monthly investigation SQL against a validated CSV."""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from eia861m.dashboard import prepare_data  # noqa: E402


def default_data_path() -> Path:
    config = json.loads((PROJECT_ROOT / "configs" / "config.json").read_text(encoding="utf-8"))
    configured = os.environ.get("EIA861M_DATA_PATH")
    return Path(configured).expanduser() if configured else PROJECT_ROOT / config["paths"]["validation_flags"]


def investigate(data: pd.DataFrame, period: str) -> pd.DataFrame:
    selected = pd.Period(period, freq="M")
    prior = str(selected - 12)
    current_keys = set(map(tuple, data.loc[data["period"] == str(selected), ["stateid", "sectorid"]].to_numpy()))
    prior_keys = set(map(tuple, data.loc[data["period"] == prior, ["stateid", "sectorid"]].to_numpy()))
    if not current_keys:
        raise ValueError(f"No observations for {selected}")
    if current_keys != prior_keys:
        raise ValueError(f"Prior-year state-sector coverage differs for {selected} and {prior}")

    columns = [
        "period", "stateid", "stateDescription", "sectorid", "sectorName",
        "sales", "revenue", "customers", "flag_any_metric_zero", "flag_negative_revenue",
    ]
    with sqlite3.connect(":memory:") as connection:
        data[columns].to_sql("retail_sales", connection, index=False)
        query = (PROJECT_ROOT / "sql" / "monthly_investigation.sql").read_text(encoding="utf-8")
        return pd.read_sql_query(query, connection, params={"period": str(selected), "prior_period": prior})


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--period", default="2025-12", help="Reporting month in YYYY-MM format")
    parser.add_argument("--data-path", type=Path, default=default_data_path(), help="Validated flagged CSV")
    parser.add_argument("--top", type=int, default=3, help="Number of ranked rows to print")
    args = parser.parse_args()
    if args.top < 1:
        parser.error("--top must be positive")
    try:
        data = prepare_data(pd.read_csv(args.data_path))
        result = investigate(data, args.period)
    except (FileNotFoundError, OSError, ValueError, pd.errors.ParserError) as exc:
        parser.error(str(exc))
    display = [
        "investigation_rank", "stateid", "sectorid", "sales_change_million_kwh",
        "sales_change_pct", "revenue_change_pct", "customers_change_pct",
        "implied_price_change_cents_kwh", "flag_any_metric_zero", "flag_negative_revenue",
    ]
    print(result[display].head(args.top).to_string(index=False, float_format=lambda value: f"{value:,.2f}"))
    print(f"Compared {len(result)} state-sector observations for {args.period}.")


if __name__ == "__main__":
    main()
