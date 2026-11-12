"""Unit tests for portfolio performance, XIRR, and P&L timeline calculations."""
import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_performance import (
    classify_cash_row,
    compute_xirr,
    compute_window_metrics,
    price_on_or_before,
    replay_through_dates,
)


class PerformanceMathTests(unittest.TestCase):
    def test_xirr_one_year_exact_10pct(self):
        cfs = [(date(2025, 1, 1), -1000.0), (date(2026, 1, 1), 1100.0)]
        r = compute_xirr(cfs)
        self.assertIsNotNone(r)
        self.assertAlmostEqual(r, 0.10, places=4)

    def test_xirr_multiple_cashflows(self):
        cfs = [
            (date(2025, 1, 1), -1000.0),
            (date(2025, 7, 2), -1000.0),
            (date(2026, 1, 1), 2300.0),
        ]
        r = compute_xirr(cfs)
        self.assertIsNotNone(r)
        self.assertGreater(r, 0.15)
        self.assertLess(r, 0.25)

    def test_xirr_negative_return(self):
        cfs = [(date(2025, 1, 1), -1000.0), (date(2026, 1, 1), 800.0)]
        r = compute_xirr(cfs)
        self.assertIsNotNone(r)
        self.assertAlmostEqual(r, -0.20, places=4)

    def test_xirr_requires_both_signs_and_span(self):
        self.assertIsNone(compute_xirr([(date(2025, 1, 1), -100.0), (date(2026, 1, 1), -50.0)]))
        self.assertIsNone(compute_xirr([(date(2025, 1, 1), -100.0), (date(2025, 1, 1), 110.0)]))

    def test_price_on_or_before_binary_search(self):
        pmap = {"2026-01-02": 100.0, "2026-01-05": 105.0, "2026-01-09": 110.0}
        sdates = sorted(pmap.keys())
        self.assertIsNone(price_on_or_before(sdates, pmap, "2026-01-01"))
        self.assertEqual(price_on_or_before(sdates, pmap, "2026-01-02"), 100.0)
        self.assertEqual(price_on_or_before(sdates, pmap, "2026-01-04"), 100.0)
        self.assertEqual(price_on_or_before(sdates, pmap, "2026-01-05"), 105.0)
        self.assertEqual(price_on_or_before(sdates, pmap, "2026-01-12"), 110.0)

    def test_replay_and_window_pnl_identity(self):
        rows = [
            {"_line": 1, "_date": date(2025, 1, 2), "date": "2025-01-02", "type": "cash", "account": "Charles Schwab", "note": "Journal", "amount": 2000.0},
            {"_line": 2, "_date": date(2025, 1, 5), "date": "2025-01-05", "type": "buy", "account": "Charles Schwab", "symbol": "TEST", "quantity": 10.0, "amount": 1000.0},
            {"_line": 3, "_date": date(2025, 7, 1), "date": "2025-07-01", "type": "sell", "account": "Charles Schwab", "symbol": "TEST", "quantity": 4.0, "amount": 600.0},
            {"_line": 4, "_date": date(2025, 8, 1), "date": "2025-08-01", "type": "cash", "account": "Charles Schwab", "note": "Cash Dividend", "amount": 20.0},
            {"_line": 5, "_date": date(2025, 9, 1), "date": "2025-09-01", "type": "fee", "account": "Charles Schwab", "amount": 5.0},
        ]
        pmap = {
            "2025-01-05": 100.0,
            "2025-06-30": 140.0,
            "2025-12-31": 160.0,
        }
        price_lookup = {"TEST": (sorted(pmap.keys()), pmap)}
        snaps = replay_through_dates(rows, [date(2025, 6, 30), date(2025, 12, 31)], price_lookup)
        end = snaps[-1]

        # Open shares: 6 @ cost 100 = 600; MV @ 160 = 960 -> unrealized = 360
        # Realized on 4 shares sold @ 150 vs 100 cost = +200
        # Cash: 2000 - 1000 + 600 + 20 - 5 = 1615
        self.assertAlmostEqual(end["costBasis"], 600.0)
        self.assertAlmostEqual(end["equityMv"], 960.0)
        self.assertAlmostEqual(end["unrealizedPnl"], 360.0)
        self.assertAlmostEqual(end["realizedPnl"], 200.0)
        self.assertAlmostEqual(end["cash"], 1615.0)
        # Identity: (equityMv + cash) - capitalPutIn == netAccountPnl
        self.assertAlmostEqual(end["accountValue"] - end["capitalPutIn"], end["netAccountPnl"])
        self.assertAlmostEqual(end["netAccountPnl"], 200.0 + 360.0 + 20.0 - 5.0)

        # Window from 2025-06-30 (10 shares @ 140 = 1400 carrying value):
        # Sold 4 @ 150 = 600 -> window realized = 600 - 4*140 = 40
        # Remaining 6 @ 160 = 960 vs 6*140 = 840 -> window unrealized = 120
        # Total window equity P&L = 160
        win = compute_window_metrics(
            rows, date(2025, 6, 30), date(2025, 12, 31), price_lookup, end,
            is_all=False, has_dated_deposits=True, options_mv=0.0, has_options=False,
        )
        self.assertAlmostEqual(win["realizedPnl"], 40.0)
        self.assertAlmostEqual(win["unrealizedPnl"], 120.0)
        self.assertAlmostEqual(win["equityPnl"], 160.0)
        self.assertIsNone(win["equityXirr"])
        self.assertIsNone(win["accountXirr"])
        self.assertFalse(win["xirrEligible"])

        # Modified Dietz: sale of 4 shares at day 1 of 184 carries weight 183/184
        capital = 1400.0 - (183.0 / 184.0) * 600.0
        self.assertAlmostEqual(win["returnPct"], 160.0 / capital, places=6)

    def test_one_year_window_reports_xirr(self):
        rows = [
            {"_line": 1, "_date": date(2025, 1, 2), "date": "2025-01-02", "type": "buy", "account": "Schwab", "symbol": "TEST", "quantity": 10.0, "amount": 1000.0},
        ]
        pmap = {"2025-01-02": 100.0, "2026-01-02": 110.0}
        price_lookup = {"TEST": (sorted(pmap.keys()), pmap)}
        end = replay_through_dates(rows, [date(2026, 1, 2)], price_lookup)[-1]
        win = compute_window_metrics(
            rows, date(2025, 1, 2), date(2026, 1, 2), price_lookup, end,
            is_all=False, has_dated_deposits=False, options_mv=0.0, has_options=False,
        )
        self.assertTrue(win["xirrEligible"])
        self.assertAlmostEqual(win["equityXirr"], 0.10, places=3)

    def test_robinhood_opening_balance_is_not_a_contribution(self):
        row = {"note": "implied opening balance (margin debit); pre-2025 activity not in export"}
        self.assertEqual(classify_cash_row("Robinhood", row), "opening_state")


if __name__ == "__main__":
    unittest.main()

