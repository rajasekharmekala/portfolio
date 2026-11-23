import unittest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import stock_snapshot
from stock_snapshot import collect_symbols_from_records, evaluate_stage2_and_entry_posture, match_stage2_symbol
from stage2_scanner import (
    build_tradingview_stage2,
    clear_india_slicers,
    extract_in,
    extract_scrollable_sectors,
    split_stage2_rows,
)


class Stage2MembershipTest(unittest.TestCase):
    def test_scanner_excludes_exits_from_current_universe(self):
        active = {"TradingView Code": "NEW", "Stage2 Status": "New Addition"}
        removed = {"TradingView Code": "OLD", "Stage2 Status": " Removed "}
        self.assertEqual(split_stage2_rows([active, removed]), ([active], [removed]))

    def test_slicer_reset_rejects_unverified_selection(self):
        with patch("stage2_scanner.run_js", side_effect=['[]']), patch("stage2_scanner.time.sleep"):
            with self.assertRaises(RuntimeError):
                clear_india_slicers("private-tab")

    def test_scanner_requires_cap_filter_to_be_visible(self):
        with patch("stage2_scanner.apply_market_cap_filter", return_value={"ok": True}), \
             patch("stage2_scanner.run_js", return_value="500"):
            with self.assertRaisesRegex(RuntimeError, "not verified"):
                extract_in("private-tab", 1000)

    def test_sector_chart_reports_incomplete_on_stall(self):
        page = [{"sector": "A", "pct_in_stage2": 50}]
        state = '{"found":true,"top":true,"bottom":false}'
        states = [state, state] + [item for _ in range(4) for item in ("", state)] + ["", state]
        with patch("stage2_scanner.run_js", side_effect=states), patch("stage2_scanner.time.sleep"), \
             patch("stage2_scanner.extract_bar_chart_sectors", return_value=page):
            rows, complete = extract_scrollable_sectors("private-tab", "heading", "pct_in_stage2")
        self.assertEqual(rows, page)
        self.assertFalse(complete)

    def test_sector_chart_collects_pages_until_bottom(self):
        states = ['{"found":true,"top":true,"bottom":false}',
                  '{"found":true,"top":true,"bottom":false}', '',
                  '{"found":true,"top":false,"bottom":true}']
        pages = [[{"sector": "A", "pct_in_stage2": 100}],
                 [{"sector": "B", "pct_in_stage2": 10}]]
        with patch("stage2_scanner.run_js", side_effect=states), patch("stage2_scanner.time.sleep"), \
             patch("stage2_scanner.extract_bar_chart_sectors", side_effect=pages):
            rows, complete = extract_scrollable_sectors("private-tab", "heading", "pct_in_stage2")
        self.assertEqual([r["sector"] for r in rows], ["A", "B"])
        self.assertTrue(complete)

    def test_removed_stock_is_not_current_even_if_in_top_list(self):
        removed = {"TradingView Code": "OLD", "Stage2 Status": "Removed"}
        data = {"stage2_universe": [removed], "top_25_stage2": [removed]}
        self.assertFalse(match_stage2_symbol("OLD", "IN", {}, data)["in_thewrap_stage2"])

    def test_surveillance_field_is_not_stage_status(self):
        current = {"TradingView Code": "NEW", "Stage2 Status": "New Addition", "ASM ESM GSM": "LTASM - I"}
        result = match_stage2_symbol("NEW", "IN", {}, {"stage2_universe": [current]})
        self.assertTrue(result["in_thewrap_stage2"])
        self.assertEqual(result["asm_status"], "LTASM - I")
        current["ASM ESM GSM"] = ""
        self.assertIsNone(match_stage2_symbol("NEW", "IN", {}, {"stage2_universe": [current]})["asm_status"])

    def test_entry_thresholds_and_missing_valuation(self):
        tv = {"close": 110.1, "sma50": 100, "sma30_weekly": 100,
              "ema10_weekly": 100, "rsi_14_daily": 60, "pe_ttm": 20,
              "revenue_yoy_growth_ttm_pct": 20}
        s2 = {"in_thewrap_stage2": True}
        self.assertEqual(evaluate_stage2_and_entry_posture(tv, s2, {}, "IN")["technical_timing_gate"], "CAP_WAIT_FOR_SUPPORT")
        tv.update(close=110.001)
        self.assertEqual(evaluate_stage2_and_entry_posture(tv, s2, {}, "IN")["technical_timing_gate"], "CAP_WAIT_FOR_SUPPORT")
        tv.update(close=112.1, ema10_weekly=110)
        self.assertEqual(evaluate_stage2_and_entry_posture(tv, s2, {}, "IN")["technical_timing_gate"], "CAP_WAIT_FOR_SUPPORT")
        tv.update(close=100, rsi_14_daily=73.1)
        self.assertEqual(evaluate_stage2_and_entry_posture(tv, s2, {}, "IN")["technical_timing_gate"], "CAP_WAIT_FOR_SUPPORT")
        tv.update(rsi_14_daily=60, pe_ttm=None)
        self.assertEqual(evaluate_stage2_and_entry_posture(tv, s2, {}, "IN")["technical_timing_gate"], "CAP_WAIT_FOR_SUPPORT")

    def test_exact_thresholds_and_zero_growth_are_not_missing(self):
        tv = {"close": 110, "sma50": 100, "sma30_weekly": 100,
              "ema10_weekly": 100, "rsi_14_daily": 73, "pe_ttm": 20,
              "revenue_yoy_growth_ttm_pct": 0}
        result = evaluate_stage2_and_entry_posture(tv, {"in_thewrap_stage2": True}, {}, "IN")
        self.assertEqual(result["technical_timing_gate"], "CLEAR_FOR_CONSIDERATION")

    def test_snapshot_collection_reads_active_shortlist_records(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "data/shortlist/US.json"
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps({"active": [{"symbol": "AAA"}, {"symbol": "BBB"}]}))
            with patch.object(stock_snapshot, "ROOT", root):
                self.assertEqual(collect_symbols_from_records("US", True, False), ["AAA", "BBB"])

    def test_tradingview_stage2_in_compatible_with_stock_snapshot(self):
        rows = [
            {"name": "AAA", "description": "AAA Ltd", "exchange": "NSE", "sector": "Tech", "industry": "IT",
             "close": 103.0, "SMA30|1W": 100.0, "SMA50": 102.0, "SMA200": 95.0,
             "volume": 200000, "average_volume_30d_calc": 100000, "Perf.W": 3.0, "Perf.3M": 25.0, "Perf.6M": 40.0, "Perf.Y": 60.0, "market_cap_basic": 2e10},
            {"name": "BBB", "description": "BBB Ltd", "exchange": "NSE", "sector": "Tech", "industry": "IT",
             "close": 120.0, "SMA30|1W": 100.0, "SMA50": 110.0, "SMA200": 90.0,
             "volume": 100000, "average_volume_30d_calc": 100000, "Perf.W": 1.0, "Perf.3M": 15.0, "Perf.6M": 20.0, "Perf.Y": 30.0, "market_cap_basic": 3e10},
            {"name": "CCC", "description": "CCC Ltd", "exchange": "NSE", "sector": "Tech", "industry": "IT",
             "close": 80.0, "SMA30|1W": 100.0, "SMA50": 85.0, "SMA200": 95.0,
             "volume": 50000, "average_volume_30d_calc": 100000, "Perf.W": -4.0, "Perf.3M": -15.0, "Perf.6M": -20.0, "Perf.Y": -10.0, "market_cap_basic": 2e10},
        ]
        payload = build_tradingview_stage2("IN", 1000.0, rows)
        self.assertEqual(payload["source"], "tradingview_scanner")
        self.assertEqual(payload["stage2_universe_count"], 2)
        self.assertTrue(payload["stage2_universe_complete"])
        self.assertEqual(payload["strongest_sectors"][0]["sector"], "IT")
        self.assertAlmostEqual(payload["strongest_sectors"][0]["pct_in_stage2"], 66.7, places=1)
        m_aaa = match_stage2_symbol("AAA", "IN", {}, payload)
        self.assertTrue(m_aaa["in_thewrap_stage2"])
        self.assertTrue(m_aaa["is_new_addition_this_week"])
        self.assertEqual(m_aaa["sector_rank"], 1)
        m_ccc = match_stage2_symbol("CCC", "IN", {}, payload)
        self.assertFalse(m_ccc["in_thewrap_stage2"])

    def test_tradingview_stage2_us_breadth_and_breakout(self):
        rows = [
            {"name": "NVDA", "description": "NVIDIA", "exchange": "NASDAQ", "sector": "Tech", "industry": "Semis",
             "close": 149.0, "change": 2.5, "SMA30|1W": 120.0, "SMA50": 135.0, "SMA200": 110.0, "EMA50": 136.0, "EMA200": 112.0,
             "price_52_week_high": 150.0, "volume": 2000000, "average_volume_30d_calc": 1000000,
             "Perf.1M": 10.0, "Perf.3M": 30.0, "Perf.6M": 50.0, "Perf.Y": 90.0, "market_cap_basic": 3e12},
            {"name": "AMD", "description": "AMD", "exchange": "NASDAQ", "sector": "Tech", "industry": "Semis",
             "close": 160.0, "change": 1.0, "SMA30|1W": 150.0, "SMA50": 155.0, "SMA200": 145.0, "EMA50": 154.0, "EMA200": 146.0,
             "price_52_week_high": 200.0, "volume": 1000000, "average_volume_30d_calc": 1000000,
             "Perf.1M": 5.0, "Perf.3M": 12.0, "Perf.6M": 20.0, "Perf.Y": 25.0, "market_cap_basic": 2.5e11},
            {"name": "INTC", "description": "Intel", "exchange": "NASDAQ", "sector": "Tech", "industry": "Semis",
             "close": 20.0, "change": -1.0, "SMA30|1W": 30.0, "SMA50": 25.0, "SMA200": 32.0, "EMA50": 25.0, "EMA200": 32.0,
             "price_52_week_high": 50.0, "volume": 500000, "average_volume_30d_calc": 1000000,
             "Perf.1M": -5.0, "Perf.3M": -10.0, "Perf.6M": -30.0, "Perf.Y": -40.0, "market_cap_basic": 1e11},
        ]
        payload = build_tradingview_stage2("US", 1.0, rows, spy_3m=5.0)
        self.assertEqual(payload["strongest_sectors"][0]["sector"], "Semis")
        self.assertAlmostEqual(payload["strongest_sectors"][0]["pct_outperforming_sp500"], 66.7, places=1)
        m_nvda = match_stage2_symbol("NVDA", "US", {"industry": "Semis"}, payload)
        self.assertEqual(m_nvda["breakout_type"], "52W High Breakout")
        self.assertEqual(m_nvda["volume_signal"], "Volume Spike")


if __name__ == "__main__":
    unittest.main()
