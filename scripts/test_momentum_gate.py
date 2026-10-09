#!/usr/bin/env python3
"""
Unit tests for the momentum gate (scripts/momentum_gate.py) and the market_facts
metrics it consumes. Run:  .venv/bin/python -m unittest scripts.test_momentum_gate -v
(or: cd scripts && ../.venv/bin/python -m unittest test_momentum_gate -v)

Coverage:
  - one deterministic case per Test A condition (structure, SMA200 slope, RS, extension)
  - one deterministic case per Test B condition (SMA50 slope, RS turn, base pivot, dryup, expansion)
  - boundary cases (exactly at the threshold passes)
  - missing-field handling (no crash; condition fails with reason)
  - known synthetic price series: steady uptrend (extended -> A4 fails),
    downtrend (NO_MOMENTUM), decline-then-flat-base (ENTERING_MOMENTUM)
  - ledger merge: --write path puts momentum_gate into instruments.<SYM>
"""
import copy
import json
import math
import os
import sys
import tempfile
import unittest

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import market_facts as mf
import momentum_gate as mg

CFG = mg.load_config()


def base_a_pass():
    """All Test A conditions satisfied (and Test B too)."""
    return {
        "kind": "stock",
        "close": 103.0, "sma50": 102.0, "sma200": 95.0,
        "sma50_21d_ago": 101.0, "sma200_63d_ago": 94.0,
        "atr14": 3.0, "base_low_63d": 101.0,
        "rs_63d_pct": 5.0, "rs_28d_pct": 2.0,
        "vol_dryup_ratio_63d": 0.6, "vol_mult_20d": 1.3,
    }


def base_b_pass():
    """Test A fails on structure (SMA200 still above), Test B all satisfied."""
    return {
        "kind": "stock",
        "close": 102.0, "sma50": 101.0, "sma200": 105.0,
        "sma50_21d_ago": 101.3, "sma200_63d_ago": 104.5,
        "atr14": 3.0, "base_low_63d": 100.0,
        "rs_63d_pct": -1.0, "rs_28d_pct": 1.0,
        "vol_dryup_ratio_63d": 0.8, "vol_mult_20d": 1.2,
    }


def make_df(closes, volumes=None):
    idx = pd.date_range("2025-01-01", periods=len(closes), freq="D")
    c = pd.Series([float(x) for x in closes], index=idx)
    vol = [int(v) for v in volumes] if volumes is not None else [1_000_000] * len(closes)
    return pd.DataFrame({
        "Open": c.shift(1).fillna(c.iloc[0]),
        "High": c * 1.002,
        "Low": c.shift(1).fillna(c.iloc[0]) * 0.998,
        "Close": c,
        "Volume": vol,
    })


class TestTestA(unittest.TestCase):
    def test_all_pass(self):
        a = mg.test_a(base_a_pass(), CFG)
        self.assertTrue(a["pass"])
        for k, c in a["conditions"].items():
            self.assertTrue(c["pass"], k)

    def test_a1_structure_fails(self):
        m = base_a_pass()
        m["close"] = 94.0  # below SMA200
        a = mg.test_a(m, CFG)
        self.assertFalse(a["pass"])
        self.assertFalse(a["conditions"]["A1_structure"]["pass"])
        self.assertTrue(a["conditions"]["A2_sma200_not_falling"]["pass"])
        self.assertTrue(a["conditions"]["A3_rs_leading_63d"]["pass"])

    def test_a1_sma50_falling(self):
        m = base_a_pass()
        m["sma50_21d_ago"] = 102.5  # SMA50 lower 21d ago -> not rising
        a = mg.test_a(m, CFG)
        self.assertFalse(a["conditions"]["A1_structure"]["pass"])

    def test_a2_sma200_falling(self):
        m = base_a_pass()
        m["sma200_63d_ago"] = 95.5  # SMA200 lower 63d ago
        a = mg.test_a(m, CFG)
        self.assertFalse(a["conditions"]["A2_sma200_not_falling"]["pass"])
        self.assertTrue(a["conditions"]["A1_structure"]["pass"])

    def test_a3_rs_lagging(self):
        m = base_a_pass()
        m["rs_63d_pct"] = -0.5
        a = mg.test_a(m, CFG)
        self.assertFalse(a["conditions"]["A3_rs_leading_63d"]["pass"])

    def test_a4_extended(self):
        m = base_a_pass()
        m["close"] = 110.0  # (110-101)/3 = 3.0 ATR above support
        a = mg.test_a(m, CFG)
        self.assertFalse(a["conditions"]["A4_not_extended"]["pass"])
        self.assertEqual(a["conditions"]["A4_not_extended"]["measured"]["support_distance_atr"], 3.0)

    def test_a4_boundary_exactly_max(self):
        m = base_a_pass()
        m["close"] = 101.0 + 1.2 * 3.0  # exactly 1.2 ATR above anchor
        a = mg.test_a(m, CFG)
        self.assertTrue(a["conditions"]["A4_not_extended"]["pass"])

    def test_a_missing_rs_field(self):
        m = base_a_pass()
        del m["rs_63d_pct"]
        a = mg.test_a(m, CFG)
        c = a["conditions"]["A3_rs_leading_63d"]
        self.assertFalse(c["pass"])
        self.assertIn("missing_fields", c["reason"])


class TestTestB(unittest.TestCase):
    def test_all_pass(self):
        b = mg.test_b(base_b_pass(), CFG)
        self.assertTrue(b["pass"])
        for k, c in b["conditions"].items():
            self.assertTrue(c["pass"], k)

    def test_b1_sma50_declining_too_fast(self):
        m = base_b_pass()
        m["sma50_21d_ago"] = 102.0  # (101/102-1)*100 = -0.98% < -0.5%
        b = mg.test_b(m, CFG)
        self.assertFalse(b["conditions"]["B1_sma50_holding"]["pass"])

    def test_b1_boundary_exactly_max_decline(self):
        m = base_b_pass()
        m["sma50_21d_ago"] = 101.0 / 0.995  # exactly -0.5%
        b = mg.test_b(m, CFG)
        self.assertTrue(b["conditions"]["B1_sma50_holding"]["pass"])

    def test_b2_rs_not_rising(self):
        m = base_b_pass()
        m["rs_28d_pct"] = 0.0
        b = mg.test_b(m, CFG)
        self.assertFalse(b["conditions"]["B2_rs_turning_28d"]["pass"])

    def test_b3_too_far_from_base(self):
        m = base_b_pass()
        m["close"] = 105.0  # (105-100)/3 = 1.67 ATR above base low
        b = mg.test_b(m, CFG)
        self.assertFalse(b["conditions"]["B3_at_base_pivot"]["pass"])

    def test_b4_no_volume_dryup(self):
        m = base_b_pass()
        m["vol_dryup_ratio_63d"] = 0.95
        b = mg.test_b(m, CFG)
        self.assertFalse(b["conditions"]["B4_volume_dryup"]["pass"])

    def test_b5_no_volume_expansion(self):
        m = base_b_pass()
        m["vol_mult_20d"] = 0.95
        b = mg.test_b(m, CFG)
        self.assertFalse(b["conditions"]["B5_volume_expansion"]["pass"])


class TestVerdict(unittest.TestCase):
    def test_in_momentum(self):
        g = mg.gate(base_a_pass(), CFG)
        self.assertEqual(g["verdict"], "IN_MOMENTUM")
        self.assertTrue(g["test_a"]["pass"])

    def test_entering_momentum_with_conditional_note(self):
        g = mg.gate(base_b_pass(), CFG)
        self.assertEqual(g["verdict"], "ENTERING_MOMENTUM")
        self.assertFalse(g["test_a"]["pass"])
        self.assertTrue(g["test_b"]["pass"])
        self.assertIn("breakout", g["note"])

    def test_no_momentum_fails_both(self):
        m = {"kind": "stock", "close": 90.0, "sma50": 95.0, "sma200": 100.0,
             "sma50_21d_ago": 97.0, "sma200_63d_ago": 101.0,
             "atr14": 2.0, "base_low_63d": 80.0,
             "rs_63d_pct": -5.0, "rs_28d_pct": -2.0,
             "vol_dryup_ratio_63d": 1.1, "vol_mult_20d": 0.8}
        g = mg.gate(m, CFG)
        self.assertEqual(g["verdict"], "NO_MOMENTUM")
        self.assertFalse(g["test_a"]["pass"])
        self.assertFalse(g["test_b"]["pass"])
        self.assertIn("not allocated", g["note"])

    def test_needs_calibration_flag_propagates(self):
        self.assertTrue(mg.gate(base_a_pass(), CFG)["config_needs_calibration"])


class TestKnownPriceSeries(unittest.TestCase):
    def test_steady_uptrend_is_extended(self):
        """A clean, uninterrupted markup passes structure but is too far from support: A4 fails."""
        closes = [100 * 1.004 ** i for i in range(300)]
        m = mf.metrics(make_df(closes))
        m["rs_63d_pct"], m["rs_28d_pct"] = 5.0, 2.0
        self.assertEqual(m["stage"], 2)
        self.assertEqual(m["sma50_trend"], "RISING")
        a = mg.test_a(m, CFG)
        self.assertTrue(a["conditions"]["A1_structure"]["pass"])
        self.assertTrue(a["conditions"]["A2_sma200_not_falling"]["pass"])
        self.assertFalse(a["conditions"]["A4_not_extended"]["pass"],
                         "steady markup must be flagged as extended")
        self.assertEqual(mg.gate(m, CFG)["verdict"], "NO_MOMENTUM")

    def test_downtrend_fails_both(self):
        closes = [100 * 0.996 ** i for i in range(300)]
        m = mf.metrics(make_df(closes))
        m["rs_63d_pct"], m["rs_28d_pct"] = -5.0, -2.0
        self.assertEqual(m["stage"], 4)
        g = mg.gate(m, CFG)
        self.assertEqual(g["verdict"], "NO_MOMENTUM")
        self.assertFalse(g["test_a"]["conditions"]["A1_structure"]["pass"])
        self.assertFalse(g["test_b"]["conditions"]["B1_sma50_holding"]["pass"])

    def test_decline_then_flat_base_is_entering(self):
        """Decline for 200 bars, then a 100-bar flat base with drying volume and a final
        expansion bar: Test B passes, Test A fails (SMA200 still above) -> ENTERING_MOMENTUM."""
        decline = [100 * 0.996 ** i for i in range(200)]
        level = decline[-1]
        base = [level] * 100
        closes = decline + base
        base_vols = [int(2_000_000 * (0.4 + 0.005 * i)) for i in range(99)] + [2_000_000]
        volumes = [2_000_000] * 200 + base_vols
        m = mf.metrics(make_df(closes, volumes))
        m["rs_63d_pct"], m["rs_28d_pct"] = -1.0, 0.5
        g = mg.gate(m, CFG)
        self.assertFalse(g["test_a"]["pass"], "recovery below SMA200 cannot be in-momentum")
        self.assertTrue(g["test_b"]["pass"], g["test_b"])
        self.assertEqual(g["verdict"], "ENTERING_MOMENTUM")


class TestLedgerMerge(unittest.TestCase):
    def test_run_ledger_and_write(self):
        facts = {
            "market": "US", "asof": "2026-10-08",
            "instruments": {
                "SPY": {"kind": "etf", "close": 600.0},
                "AAA": base_a_pass(),
                "BBB": base_b_pass(),
                "ERR": {"kind": "stock", "error": "only 12 bars"},
            },
        }
        results, skipped = mg.run_ledger(facts, CFG)
        self.assertEqual(sorted(results), ["AAA", "BBB"])
        self.assertEqual(skipped, ["ERR"])
        self.assertEqual(results["AAA"]["verdict"], "IN_MOMENTUM")
        self.assertEqual(results["BBB"]["verdict"], "ENTERING_MOMENTUM")

        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "facts.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(facts, f)
            # emulate --write
            for sym, r in results.items():
                facts["instruments"][sym]["momentum_gate"] = r
            with open(path, "w", encoding="utf-8") as f:
                json.dump(facts, f)
            with open(path, encoding="utf-8") as f:
                back = json.load(f)
            self.assertIn("momentum_gate", back["instruments"]["AAA"])
            self.assertNotIn("momentum_gate", back["instruments"]["ERR"])
            self.assertEqual(back["instruments"]["AAA"]["momentum_gate"]["verdict"], "IN_MOMENTUM")


if __name__ == "__main__":
    unittest.main()
