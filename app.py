from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pandas as pd
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from eia861m.dashboard import (  # noqa: E402
    annual_scope,
    flagged_observations,
    monthly_investigation,
    monthly_scope,
    prepare_data,
    quality_counts,
    seasonal_profile,
    sector_shares,
    state_ranking,
    state_sector_table,
)


st.set_page_config(page_title="Electricity Retail Sales | Market Monitor", layout="wide")


def data_path() -> Path:
    config = json.loads((PROJECT_ROOT / "configs" / "config.json").read_text(encoding="utf-8"))
    configured = os.environ.get("EIA861M_DATA_PATH")
    return Path(configured).expanduser() if configured else PROJECT_ROOT / config["paths"]["validation_flags"]


@st.cache_data(show_spinner="Loading validated data")
def load_data(path: str, modified_ns: int) -> pd.DataFrame:
    return prepare_data(pd.read_csv(path))


def format_growth(value: float) -> str | None:
    return f"{value:+.1%} YoY" if pd.notna(value) else None


def show_kpis(row: pd.Series) -> None:
    cols = st.columns(4)
    cols[0].metric("Sales | TWh", f"{row['sales'] / 1000:,.2f}", format_growth(row["sales_yoy"]))
    cols[1].metric("Revenue | USD bn, nominal", f"{row['revenue'] / 1000:,.2f}", format_growth(row["revenue_yoy"]))
    price = row["implied_price_cents_kwh"]
    cols[2].metric("Implied price | cents/kWh", f"{price:,.2f}" if pd.notna(price) else "N/A")
    cols[3].metric("Avg monthly customers | million", f"{row['avg_monthly_customers'] / 1e6:,.2f}")


def methodology() -> None:
    with st.expander("Source, units & methodology", expanded=False):
        st.markdown(
            "EIA-861M monthly retail sales, 2016-01 to 2025-12. Sales and revenue are summed "
            "across months; customers are averaged after summing each month's observations. "
            "Implied price = 100 × revenue / sales, never the mean of reported prices. "
            "Revenue and price are nominal, without inflation adjustment. Shares refer to the "
            "published national total, not a company's market share. Zeros and negative values "
            "are retained and flagged. These patterns are descriptive, not causal or predictive."
        )


def investigation_quality(row: pd.Series) -> str:
    notes = []
    for suffix, period_label in (("", "current"), ("_prior", "prior")):
        if suffix and not row["has_prior"]:
            continue
        if row[f"flag_all_metrics_zero{suffix}"]:
            notes.append(f"{period_label}: all zero")
        elif row[f"flag_any_metric_zero{suffix}"]:
            notes.append(f"{period_label}: zero metric")
        if row[f"flag_negative_revenue{suffix}"]:
            notes.append(f"{period_label}: negative revenue")
    return "; ".join(notes) if notes else "None"


st.title("Electricity retail sales")
st.caption("U.S. market monitor · EIA-861M · published state-sector observations")

path = data_path()
if not path.is_file():
    st.error(f"Validated CSV not found: {path}")
    st.info("Run acquisition and validation, or set EIA861M_DATA_PATH to the flagged interim CSV.")
    st.stop()

try:
    data = load_data(str(path), path.stat().st_mtime_ns)
except (ValueError, OSError, pd.errors.ParserError) as exc:
    st.error(f"Could not load validated CSV: {exc}")
    st.stop()

years = sorted(data["year"].unique().tolist())
year = st.selectbox("Reporting year", years, index=len(years) - 1)
methodology()

investigation, overview, explorer, quality = st.tabs(
    ("Monthly investigation", "National overview", "Segment explorer", "Data quality & method")
)

with investigation:
    st.caption("Published monthly snapshot | state-sector review, not an automated anomaly score")
    periods = sorted(data.loc[data["year"] == year, "period"].unique().tolist())
    months_col, sector_col, state_col = st.columns([2, 1, 1])
    with months_col:
        period = st.selectbox("Reporting month", periods, index=len(periods) - 1)
    with sector_col:
        investigation_sector = st.selectbox("Sector filter", ["All sectors", *sorted(data["sectorid"].unique())])
    with state_col:
        investigation_state = st.selectbox("State filter", ["All states", *sorted(data["stateid"].unique())])

    monthly = monthly_investigation(data, period)
    total_sales = monthly["sales"].sum()
    total_revenue = monthly["revenue"].sum()
    previous_sales = monthly["sales_prior"].sum(min_count=1)
    previous_revenue = monthly["revenue_prior"].sum(min_count=1)
    total_price = 100 * total_revenue / total_sales if total_sales > 0 else float("nan")
    summary = st.columns(3)
    summary[0].metric(
        "National monthly sales | TWh", f"{total_sales / 1000:,.2f}",
        format_growth(total_sales / previous_sales - 1) if previous_sales > 0 else None,
    )
    summary[1].metric(
        "National monthly revenue | USD bn, nominal", f"{total_revenue / 1000:,.2f}",
        format_growth(total_revenue / previous_revenue - 1) if previous_revenue > 0 else None,
    )
    summary[2].metric(
        "Implied price | nominal cents/kWh", f"{total_price:,.2f}" if pd.notna(total_price) else "N/A",
    )
    if year == years[0]:
        st.info("No prior-year month exists in this snapshot for 2016; YoY comparisons are unavailable.")
    if investigation_sector == "TRA":
        st.warning("Transportation has many zero-valued observations. Review the quality notes before interpreting changes.")

    filtered = monthly
    if investigation_sector != "All sectors":
        filtered = filtered.loc[filtered["sectorid"] == investigation_sector]
    if investigation_state != "All states":
        filtered = filtered.loc[filtered["stateid"] == investigation_state]
    metric_label = st.segmented_control(
        "Compare", ("Sales", "Revenue", "Customers", "Implied price"), default="Sales"
    )
    metric = {
        "Sales": "sales", "Revenue": "revenue", "Customers": "customers",
        "Implied price": "implied_price_cents_kwh",
    }[metric_label]
    unit = {
        "Sales": "million kWh", "Revenue": "million USD, nominal", "Customers": "monthly count",
        "Implied price": "nominal cents/kWh",
    }[metric_label]
    order = st.selectbox(
        "Order by", ("Largest absolute change", "Largest increase", "Largest decrease", "Largest percentage change")
    )
    change = f"{metric}_change"
    change_pct = f"{metric}_change_pct"
    if order == "Largest absolute change":
        sort_values = filtered[change].abs()
        ascending = False
    elif order == "Largest increase":
        sort_values = filtered[change]
        ascending = False
    elif order == "Largest decrease":
        sort_values = filtered[change]
        ascending = True
    else:
        sort_values = filtered[change_pct].abs()
        ascending = False
    filtered = (
        filtered.assign(_sort=sort_values)
        .sort_values("_sort", ascending=ascending, na_position="last")
        .drop(columns="_sort")
    )
    table = filtered[["stateid", "sectorid", metric, f"{metric}_prior", change, change_pct]].rename(columns={
        "stateid": "State", "sectorid": "Sector", metric: f"Current ({unit})",
        f"{metric}_prior": f"Prior year ({unit})", change: f"Change ({unit})",
        change_pct: "YoY change (%)",
    })
    table["Quality note"] = filtered.apply(investigation_quality, axis=1)
    table = table.reset_index(drop=True)
    selection = st.dataframe(
        table, hide_index=True, width="stretch", height=460,
        on_select="rerun", selection_mode="multi-row",
        key=f"monthly_rows_{period}_{metric}_{investigation_sector}_{investigation_state}_{order}",
        column_config={"YoY change (%)": st.column_config.NumberColumn(format="%.1f%%")},
    )
    chosen = table.iloc[selection.selection.rows]
    st.caption(
        f"{len(table)} state-sector rows shown; {len(chosen)} selected for follow-up. "
        "YoY compares the same calendar month; percentages are unavailable when the prior value is zero or negative. "
        "Small positive baselines can produce unstable percentages."
    )
    st.download_button(
        "Download selected rows (CSV)", chosen.to_csv(index=False).encode("utf-8"),
        file_name=f"eia861m_investigation_{period}.csv", mime="text/csv", disabled=chosen.empty,
    )

    if not filtered.empty:
        focus_options = [f"{state} / {sector}" for state, sector in zip(filtered["stateid"], filtered["sectorid"])]
        focus = st.selectbox("Inspect historical series", focus_options)
        focus_state, focus_sector = focus.split(" / ")
        history = (
            data.loc[(data["stateid"] == focus_state) & (data["sectorid"] == focus_sector)]
            .sort_values("period_month")
            .copy()
        )
        if metric == "implied_price_cents_kwh":
            history[metric] = (100 * history["revenue"] / history["sales"]).where(history["sales"] > 0)
        st.line_chart(history.set_index("period_month")[metric], x_label="Month", y_label=unit)
        st.caption("Full available history; a prominent YoY change is a reason to investigate, not evidence of its cause.")

with overview:
    national = annual_scope(data)
    selected = national.loc[national["year"] == year].iloc[0]
    show_kpis(selected)
    st.subheader("National trends | full 2016–2025 history")
    a, b, c = st.columns(3)
    with a:
        st.caption("Annual sales · TWh")
        st.line_chart(national.set_index("year")["sales"] / 1000, x_label="Year", y_label="TWh")
    with b:
        st.caption("Annual revenue · USD bn, nominal")
        st.line_chart(national.set_index("year")["revenue"] / 1000, x_label="Year", y_label="USD bn")
    with c:
        st.caption("Implied average price · nominal cents/kWh")
        st.line_chart(national.set_index("year")["implied_price_cents_kwh"], x_label="Year", y_label="cents/kWh")
    st.subheader(f"Sector contribution | {year}")
    shares = sector_shares(data, year)
    left, right = st.columns([2, 3])
    with left:
        st.bar_chart(
            shares.set_index("sectorid")[["sales_share", "revenue_share"]] * 100,
            x_label="Sector", y_label="National share (%)",
        )
    with right:
        displayed = shares[["sectorid", "sales_share", "revenue_share"]].copy()
        displayed[["sales_share", "revenue_share"]] *= 100
        displayed.columns = ["Sector", "Sales share", "Revenue share"]
        st.dataframe(displayed, hide_index=True, width="stretch", column_config={
            "Sales share": st.column_config.NumberColumn(format="%.1f%%"),
            "Revenue share": st.column_config.NumberColumn(format="%.1f%%"),
        })
        st.caption("Shares use the national total in the selected year as denominator.")

with explorer:
    states = sorted(data["stateid"].unique().tolist())
    sectors = sorted(data["sectorid"].unique().tolist())
    filter_a, filter_b = st.columns(2)
    with filter_a:
        state_choice = st.selectbox("State", ["All states", *states])
    with filter_b:
        sector_choice = st.selectbox("Sector", ["All sectors", *sectors])
    state = None if state_choice == "All states" else state_choice
    sector = None if sector_choice == "All sectors" else sector_choice
    if sector == "TRA":
        st.warning("Transportation has many published zero observations. Review Data quality before interpreting price or customer patterns.")
    scoped_annual = annual_scope(data, state, sector)
    scoped_row = scoped_annual.loc[scoped_annual["year"] == year].iloc[0]
    st.caption(f"Selected scope: {state_choice} · {sector_choice} · {year}")
    show_kpis(scoped_row)

    left, right = st.columns([2, 3])
    with left:
        st.subheader(f"State sales share | {year}")
        ranking = state_ranking(data, year).head(12)
        st.bar_chart(ranking.set_index("stateid")["national_sales_share"] * 100, x_label="State", y_label="National sales share (%)")
        st.caption("Top 12 states; national denominator does not change with filters.")
    with right:
        st.subheader("Monthly sales | full 2016–2025 history")
        monthly = monthly_scope(data, state, sector)
        st.line_chart(monthly.set_index("period_month")["sales"] / 1000, x_label="Month", y_label="TWh")
        st.caption("The year selector changes annual KPIs; this trend retains the full period.")

    st.subheader("State-sector comparison")
    segments = state_sector_table(data, year)
    if state is not None:
        segments = segments.loc[segments["stateid"] == state]
    if sector is not None:
        segments = segments.loc[segments["sectorid"] == sector]
    sort_col, order_col = st.columns([2, 1])
    with sort_col:
        sort_label = st.selectbox("Sort by", ["Sales", "Revenue", "National sales share", "Implied price", "Avg monthly customers"])
    with order_col:
        descending = st.toggle("Descending", value=True)
    sort_map = {
        "Sales": "sales", "Revenue": "revenue", "National sales share": "national_sales_share",
        "Implied price": "implied_price_cents_kwh", "Avg monthly customers": "avg_monthly_customers",
    }
    segments = segments.sort_values(sort_map[sort_label], ascending=not descending)
    table = segments[[
        "stateid", "sectorid", "sales", "revenue", "national_sales_share",
        "implied_price_cents_kwh", "avg_monthly_customers", "zero_flag_count", "negative_revenue_count",
    ]].rename(columns={
        "stateid": "State", "sectorid": "Sector", "sales": "Sales (million kWh)",
        "revenue": "Revenue (million USD)", "national_sales_share": "National sales share",
        "implied_price_cents_kwh": "Implied price (cents/kWh)",
        "avg_monthly_customers": "Avg monthly customers", "zero_flag_count": "Zero flags",
        "negative_revenue_count": "Negative revenue flags",
    })
    st.dataframe(table, hide_index=True, width="stretch", height=350)
    st.download_button("Download displayed rows (CSV)", table.to_csv(index=False).encode("utf-8"),
                       file_name=f"eia861m_segments_{year}.csv", mime="text/csv")
    st.caption("Download includes the selected scope and explicit sort order. Shares retain the national denominator.")

    st.subheader("Seasonal sales index | RES, COM, IND · 2016–2025")
    profile = seasonal_profile(data).pivot(index="month", columns="sectorid", values="index")
    st.line_chart(profile, x_label="Month", y_label="Index (sector-year mean = 1)")
    st.caption("Each sector-month is divided by that sector-year's average month, then averaged across years. TRA is excluded because of zero-heavy observations.")

with quality:
    st.subheader(f"Published observation flags | {year}")
    counts = quality_counts(data, year)
    st.dataframe(counts.rename(columns={
        "sectorid": "Sector", "observations": "Observations", "any_zero": "Any metric zero",
        "all_zero": "All metrics zero", "negative_revenue": "Negative revenue",
    }), hide_index=True, width="stretch")
    quality_sector = st.selectbox("Flagged rows: sector", ["All sectors", *sectors], key="quality_sector")
    flagged = flagged_observations(data, year, None if quality_sector == "All sectors" else quality_sector)
    st.caption(f"{len(flagged):,} flagged observations in this selection. Published values are retained.")
    st.dataframe(flagged, hide_index=True, width="stretch", height=390)
    st.subheader("Method documentation")
    for name in ("data_provenance.md", "data_quality.md", "eda_findings.md"):
        document = PROJECT_ROOT / "docs" / name
        with st.expander(name):
            st.markdown(document.read_text(encoding="utf-8"))
