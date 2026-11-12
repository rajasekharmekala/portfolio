import unittest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import stock_snapshot
from stock_snapshot import collect_symbols_from_records, evaluate_stage2_and_entry_posture, match_stage2_symbol
from stage2_scanner import clear_india_slicers, extract_in, extract_scrollable_sectors, split_stage2_rows


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
                self.assertEqual(collect_symbols_from_records("US", False, True, False), ["AAA", "BBB"])


if __name__ == "__main__":
    unittest.main()
