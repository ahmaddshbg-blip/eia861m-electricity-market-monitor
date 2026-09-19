import sys
import unittest
import warnings
from pathlib import Path

import pandas as pd


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from eia861m.dashboard import (  # noqa: E402
    annual_scope,
    flagged_observations,
    monthly_investigation,
    prepare_data,
    quality_counts,
    sector_shares,
    state_ranking,
    state_sector_table,
)


class DashboardAggregationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rows = []
        for year in (2021, 2022):
            for month in range(1, 13):
                for state, sector, sales, revenue, customers in (
                    ("AA", "RES", 10.0, 2.0, 100 + month),
                    ("BB", "RES", 20.0, 2.0, 200 + month),
                    ("AA", "TRA", 0.0, -0.00001 if year == 2022 and month == 2 else 0.0, 0),
                ):
                    rows.append({
                        "period": f"{year}-{month:02d}", "stateid": state,
                        "stateDescription": state, "sectorid": sector,
                        "sectorName": sector, "sales": sales * (2 if year == 2022 else 1),
                        "revenue": revenue * (2 if year == 2022 else 1),
                        "customers": customers, "price": 0.0,
                        "flag_any_metric_zero": sector == "TRA",
                        "flag_all_metrics_zero": sector == "TRA" and not (year == 2022 and month == 2),
                        "flag_negative_revenue": sector == "TRA" and year == 2022 and month == 2,
                    })
        cls.data = prepare_data(pd.DataFrame(rows))

    def test_annual_customer_average_and_ratio(self):
        annual = annual_scope(self.data, sector="RES")
        first = annual.loc[annual["year"] == 2021].iloc[0]
        self.assertEqual(first["sales"], 360)
        self.assertEqual(first["avg_monthly_customers"], 313)
        self.assertAlmostEqual(first["implied_price_cents_kwh"], 100 * 48 / 360)
        self.assertTrue(pd.isna(first["sales_yoy"]))
        self.assertAlmostEqual(annual.iloc[1]["sales_yoy"], 1.0)

    def test_shares_keep_national_denominator(self):
        shares = sector_shares(self.data, 2021)
        self.assertAlmostEqual(shares.loc[shares["sectorid"] == "RES", "sales_share"].iloc[0], 1.0)
        state = state_ranking(self.data, 2021)
        self.assertAlmostEqual(state.loc[state["stateid"] == "AA", "national_sales_share"].iloc[0], 1 / 3)
        segments = state_sector_table(self.data, 2021)
        aa_res = segments.loc[(segments["stateid"] == "AA") & (segments["sectorid"] == "RES")].iloc[0]
        self.assertAlmostEqual(aa_res["national_sales_share"], 1 / 3)

    def test_tra_flags_and_negative_record_are_retained(self):
        counts = quality_counts(self.data, 2022)
        tra = counts.loc[counts["sectorid"] == "TRA"].iloc[0]
        self.assertEqual(tra["any_zero"], 12)
        self.assertEqual(tra["negative_revenue"], 1)
        flagged = flagged_observations(self.data, 2022, "TRA")
        self.assertEqual(len(flagged), 12)
        self.assertEqual(flagged.iloc[0]["period"], "2022-02")
        self.assertEqual(flagged.iloc[0]["revenue"], -0.00002)

    def test_invalid_flag_rejected(self):
        broken = self.data.copy()
        broken["flag_negative_revenue"] = "unknown"
        with self.assertRaises(ValueError):
            prepare_data(broken)

    def test_monthly_investigation_uses_same_month_previous_year(self):
        compared = monthly_investigation(self.data, "2022-02")
        self.assertEqual(len(compared), 3)
        aa_res = compared.loc[(compared["stateid"] == "AA") & (compared["sectorid"] == "RES")].iloc[0]
        self.assertEqual(aa_res["sales"], 20)
        self.assertEqual(aa_res["sales_prior"], 10)
        self.assertEqual(aa_res["sales_change"], 10)
        self.assertEqual(aa_res["sales_change_pct"], 100)
        self.assertEqual(aa_res["customers_change"], 0)
        self.assertEqual(aa_res["implied_price_cents_kwh"], 20)
        self.assertEqual(aa_res["implied_price_cents_kwh_change"], 0)

    def test_monthly_investigation_keeps_zero_and_negative_quality_context(self):
        compared = monthly_investigation(self.data, "2022-02")
        aa_tra = compared.loc[compared["sectorid"] == "TRA"].iloc[0]
        self.assertTrue(aa_tra["flag_negative_revenue"])
        self.assertTrue(aa_tra["flag_any_metric_zero_prior"])
        self.assertTrue(pd.isna(aa_tra["sales_change_pct"]))
        self.assertTrue(pd.isna(aa_tra["revenue_change_pct"]))
        self.assertTrue(pd.isna(aa_tra["implied_price_cents_kwh"]))

    def test_monthly_investigation_has_no_yoy_for_first_year(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", FutureWarning)
            compared = monthly_investigation(self.data, "2021-02")
        self.assertFalse(any(issubclass(warning.category, FutureWarning) for warning in caught))
        self.assertFalse(compared["has_prior"].any())
        self.assertTrue(compared["sales_change"].isna().all())
        self.assertTrue(compared["sales_change_pct"].isna().all())
        self.assertFalse(compared["flag_any_metric_zero_prior"].any())

    def test_monthly_investigation_rejects_missing_prior_coverage(self):
        incomplete = self.data.loc[
            ~((self.data["period"] == "2021-02") & (self.data["stateid"] == "BB"))
        ]
        with self.assertRaisesRegex(ValueError, "coverage differs"):
            monthly_investigation(incomplete, "2022-02")


if __name__ == "__main__":
    unittest.main()
