from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pandas as pd


DATA_FIELDS = ["customers", "price", "revenue", "sales"]


def build_request_params(
    api_key: str,
    frequency: str,
    sectors: list[str],
    states: list[str],
    start: str,
    end: str,
    length: int,
    offset: int = 0,
) -> dict[str, Any]:
    """Build EIA API request parameters for one paginated request."""
    params: dict[str, Any] = {
        "api_key": api_key,
        "frequency": frequency,
        "facets[sectorid][]": sectors,
        "facets[stateid][]": states,
        "sort[0][column]": "period",
        "sort[0][direction]": "asc",
        "start": start,
        "end": end,
        "length": length,
        "offset": offset,
    }

    for index, field in enumerate(DATA_FIELDS):
        params[f"data[{index}]"] = field

    return params


def fetch_window(
    endpoint: str,
    api_key: str,
    frequency: str,
    sectors: list[str],
    states: list[str],
    start: str,
    end: str,
    length: int,
    timeout: int = 30,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Fetch one date window from the EIA API using pagination."""
    import requests

    rows: list[dict[str, Any]] = []
    offset = 0
    total: int | None = None

    while True:
        params = build_request_params(
            api_key=api_key,
            frequency=frequency,
            sectors=sectors,
            states=states,
            start=start,
            end=end,
            length=length,
            offset=offset,
        )

        try:
            response = requests.get(endpoint, params=params, timeout=timeout)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise RuntimeError(
                f"EIA API request failed for {start} to {end}, offset {offset} "
                f"({type(exc).__name__}). Check the key, network, and API status."
            ) from None
        payload = response.json()
        response_body = payload.get("response", {})
        page_rows = response_body.get("data", [])

        if total is None:
            total_value = response_body.get("total")
            total = int(total_value) if total_value is not None else None

        rows.extend(page_rows)

        if not page_rows:
            break
        if total is not None and len(rows) >= total:
            break
        if len(page_rows) < length:
            break

        offset += length

    metadata = {
        "start": start,
        "end": end,
        "rows_fetched": len(rows),
        "api_total": total,
    }

    if total is not None and len(rows) != total:
        raise ValueError(
            f"Incomplete API fetch for {start} to {end}: "
            f"fetched {len(rows)} rows but API reported {total}."
        )

    return rows, metadata


def fetch_dataset(config: dict[str, Any], api_key: str) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Fetch the configured EIA-861M dataset and return data plus metadata."""
    api_config = config["api"]
    dataset_config = config["dataset"]
    all_rows: list[dict[str, Any]] = []
    window_metadata: list[dict[str, Any]] = []

    for start, end in dataset_config["request_windows"]:
        rows, metadata = fetch_window(
            endpoint=api_config["endpoint"],
            api_key=api_key,
            frequency=api_config["frequency"],
            sectors=dataset_config["sectors"],
            states=dataset_config["states"],
            start=start,
            end=end,
            length=int(api_config["length"]),
        )
        all_rows.extend(rows)
        window_metadata.append(metadata)

    dataframe = pd.DataFrame(all_rows)
    metadata = {
        "endpoint": api_config["endpoint"],
        "frequency": api_config["frequency"],
        "data_fields": DATA_FIELDS,
        "sectors": dataset_config["sectors"],
        "states": dataset_config["states"],
        "start_period": dataset_config["start_period"],
        "end_period": dataset_config["end_period"],
        "request_windows": window_metadata,
        "rows_fetched": len(dataframe),
        "acquired_at_utc": datetime.now(timezone.utc).isoformat(),
    }

    return dataframe, metadata
