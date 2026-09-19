import sys
import unittest
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from eia861m.dashboard import monthly_investigation, prepare_data  # noqa: E402
from run_sql_investigation import investigate  # noqa: E402


class SqlInvestigationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rows = []
        for period, values in (
            ("2024-12", (("AA", "RES", 100, 20, 1000), ("BB", "COM", 0, 0, 0))),
            ("2025-12", (("AA", "RES", 75, 18, 1010), ("BB", "COM", 5, 1, 1))),
        ):
            for state, sector, sales, revenue, customers in values:
                rows.append({
                    "period": period,
                    "stateid": state,
                    "stateDescription": state,
                    "sectorid": sector,
                    "sectorName": sector,
                    "sales": sales,
                    "revenue": revenue,
                    "customers": customers,
                    "price": 0,
                    "flag_any_metric_zero": sales == 0,
                    "flag_all_metrics_zero": sales == 0,
                    "flag_negative_revenue": False,
                })
        cls.data = prepare_data(pd.DataFrame(rows))

    def test_sql_matches_dashboard_comparisons(self):
        sql = investigate(self.data, "2025-12")
        python = monthly_investigation(self.data, "2025-12")
        self.assertEqual(sql[["stateid", "sectorid"]].values.tolist(), [["AA", "RES"], ["BB", "COM"]])
        for row in sql.itertuples():
            match = python.loc[(python.stateid == row.stateid) & (python.sectorid == row.sectorid)].iloc[0]
            self.assertAlmostEqual(row.sales_change_million_kwh, match.sales_change)
            for sql_value, python_value in (
                (row.revenue_change_pct, match.revenue_change_pct),
                (row.customers_change_pct, match.customers_change_pct),
                (row.implied_price_change_cents_kwh, match.implied_price_cents_kwh_change),
            ):
                if pd.isna(python_value):
                    self.assertTrue(pd.isna(sql_value))
                else:
                    self.assertAlmostEqual(sql_value, python_value)
        self.assertTrue(pd.isna(sql.iloc[1]["sales_change_pct"]))
        self.assertEqual(sql.iloc[1]["flag_any_metric_zero_prior"], 1)

    def test_missing_prior_coverage_is_rejected(self):
        incomplete = self.data.loc[~((self.data.period == "2024-12") & (self.data.stateid == "BB"))]
        with self.assertRaisesRegex(ValueError, "coverage differs"):
            investigate(incomplete, "2025-12")


if __name__ == "__main__":
    unittest.main()
