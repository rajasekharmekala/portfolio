#!/usr/bin/env python3
"""
Momentum gate (constitution §9): Test A (in momentum now) and Test B (entering
momentum), computed from the frozen facts ledger (scripts/market_facts.py output)
against the thresholds in .agents/config/scoring.json (single source of truth;
the config marks the thresholds needs_calibration until reviewed).

Usage:
  python3 scripts/momentum_gate.py cache/facts_US_2026-09-28.json
  python3 scripts/momentum_gate.py cache/facts_IN_2026-10-08.json --write
  python3 scripts/momentum_gate.py cache/facts_US_2026-09-28.json --out momentum_gate_US.json

Per name the gate emits:
  - test_a: pass/fail with every measured value (structure, SMA200 slope, 63d RS, extension)
  - test_b: pass/fail with every measured value (SMA50 slope, 28d RS, base pivot, volume dryup/expand)
  - verdict: IN_MOMENTUM | ENTERING_MOMENTUM | NO_MOMENTUM
A name that fails both tests is not allocated, however good its business.
--write merges each result into the ledger at instruments.<SYM>.momentum_gate so the
gate output lives in the ledger for every name.
"""
import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCORING_FILE = os.path.join(ROOT, ".agents", "config", "scoring.json")


def load_config(path=SCORING_FILE):
    with open(path, encoding="utf-8") as f:
        return json.load(f)["momentum_gate"]


def _cond(ok, measured, reason=None):
    d = {"pass": bool(ok), "measured": measured}
    if reason:
        d["reason"] = reason
    return d


def _missing(m, *keys):
    return [k for k in keys if m.get(k) is None]


def _support_distance_atr(m):
    """ATR multiple above the nearest verified support anchor (SMA50 or 63d base low)."""
    close, atr = m.get("close"), m.get("atr14")
    anchors = [a for a in (m.get("sma50"), m.get("base_low_63d")) if a is not None]
    if close is None or not atr or not anchors:
        return None
    return round((close - min(anchors)) / atr, 2)


def test_a(m, cfg):
    """Test A — in momentum now: stage-2 structure, SMA200 not falling, RS leading, not extended."""
    t = cfg["test_a_in_momentum_now"]
    conds = {}
    close, s50, s200 = m.get("close"), m.get("sma50"), m.get("sma200")
    s50_21, s200_63, rs = m.get("sma50_21d_ago"), m.get("sma200_63d_ago"), m.get("rs_63d_pct")

    miss = _missing(m, "close", "sma50", "sma200", "sma50_21d_ago")
    if miss:
        conds["A1_structure"] = _cond(False, None, "missing_fields:" + ",".join(miss))
    else:
        ok = close > s50 > s200 and s50 > s50_21
        conds["A1_structure"] = _cond(ok, {"close": close, "sma50": s50, "sma200": s200,
                                           "sma50_%dd_ago" % t["sma50_rising_window_days"]: s50_21})

    miss = _missing(m, "sma200", "sma200_63d_ago")
    if miss:
        conds["A2_sma200_not_falling"] = _cond(False, None, "missing_fields:" + ",".join(miss))
    else:
        conds["A2_sma200_not_falling"] = _cond(s200 >= s200_63, {"sma200": s200,
                                                                 "sma200_%dd_ago" % t["sma200_not_falling_window_days"]: s200_63})

    if rs is None:
        conds["A3_rs_leading_63d"] = _cond(False, None, "missing_fields:rs_63d_pct")
    else:
        conds["A3_rs_leading_63d"] = _cond(rs >= t["rs_min_excess_vs_benchmark_pct"],
                                           {"rs_63d_excess_pct": rs, "required_min_pct": t["rs_min_excess_vs_benchmark_pct"]})

    sd = _support_distance_atr(m)
    if sd is None:
        miss = _missing(m, "close", "atr14")
        if not (m.get("sma50") is not None or m.get("base_low_63d") is not None):
            miss = miss + ["sma50|base_low_63d"]
        conds["A4_not_extended"] = _cond(False, None, "missing_fields:" + ",".join(miss))
    else:
        conds["A4_not_extended"] = _cond(sd <= t["support_distance_atr_max"],
                                         {"support_distance_atr": sd, "max_atr": t["support_distance_atr_max"]})

    return {"pass": all(c["pass"] for c in conds.values()), "conditions": conds}


def test_b(m, cfg):
    """Test B — entering momentum: flat-or-up SMA50, RS turning, at the base, volume dryup then expansion."""
    t = cfg["test_b_entering_momentum"]
    conds = {}
    s50, s50_21 = m.get("sma50"), m.get("sma50_21d_ago")

    if s50 is None or s50_21 is None:
        conds["B1_sma50_holding"] = _cond(False, None, "missing_fields:sma50,sma50_21d_ago")
    else:
        chg = round((s50 / s50_21 - 1) * 100, 2)
        conds["B1_sma50_holding"] = _cond(chg >= -t["sma50_max_decline_pct"],
                                          {"sma50_%dd_chg_pct" % t["sma50_window_days"]: chg,
                                           "max_decline_pct": t["sma50_max_decline_pct"]})

    rs28 = m.get("rs_28d_pct")
    if rs28 is None:
        conds["B2_rs_turning_28d"] = _cond(False, None, "missing_fields:rs_28d_pct")
    else:
        conds["B2_rs_turning_28d"] = _cond(rs28 > 0, {"rs_28d_excess_pct": rs28,
                                                       "required": "rising (> 0)"})

    close, base, atr = m.get("close"), m.get("base_low_63d"), m.get("atr14")
    if close is None or base is None or not atr:
        conds["B3_at_base_pivot"] = _cond(False, None, "missing_fields:close,base_low_63d,atr14")
    else:
        d = round((close - base) / atr, 2)
        conds["B3_at_base_pivot"] = _cond(d <= t["pivot_atr_max"],
                                          {"base_pivot_atr": d, "max_atr": t["pivot_atr_max"]})

    dry = m.get("vol_dryup_ratio_63d")
    if dry is None:
        conds["B4_volume_dryup"] = _cond(False, None, "missing_fields:vol_dryup_ratio_63d")
    else:
        conds["B4_volume_dryup"] = _cond(dry <= t["volume_dryup_ratio_max"],
                                         {"vol_dryup_ratio_63d": dry, "max_ratio": t["volume_dryup_ratio_max"]})

    ve = m.get("vol_mult_20d")
    if ve is None:
        conds["B5_volume_expansion"] = _cond(False, None, "missing_fields:vol_mult_20d")
    else:
        conds["B5_volume_expansion"] = _cond(ve >= t["volume_expand_ratio_min"],
                                             {"vol_mult_20d": ve, "min_ratio": t["volume_expand_ratio_min"]})

    return {"pass": all(c["pass"] for c in conds.values()), "conditions": conds,
            "conditional_entry": t.get("conditional_entry")}


def gate(m, cfg):
    a, b = test_a(m, cfg), test_b(m, cfg)
    if a["pass"]:
        verdict, note = "IN_MOMENTUM", None
    elif b["pass"]:
        verdict, note = "ENTERING_MOMENTUM", b["conditional_entry"]
    else:
        verdict, note = "NO_MOMENTUM", "fails both tests — not allocated, however good its business"
    return {"verdict": verdict, "test_a": a, "test_b": b, "note": note,
            "config_needs_calibration": bool(cfg.get("needs_calibration", False))}


def run_ledger(facts, cfg):
    """Gate every stock instrument in the ledger. Returns {symbol: result} and skips names with errors."""
    out, skipped = {}, []
    for sym, m in facts.get("instruments", {}).items():
        if m.get("kind") != "stock":
            continue
        if m.get("error") or m.get("close") is None:
            skipped.append(sym)
            continue
        out[sym] = gate(m, cfg)
    return out, skipped


def print_table(results):
    order = {"IN_MOMENTUM": 0, "ENTERING_MOMENTUM": 1, "NO_MOMENTUM": 2}
    print("%-16s %-18s %-4s %-4s %-4s %-4s %-4s %-4s %-4s %-4s %-4s" %
          ("symbol", "verdict", "A1", "A2", "A3", "A4", "B1", "B2", "B3", "B4", "B5"))
    for sym in sorted(results, key=lambda s: (order[results[s]["verdict"]], s)):
        r = results[sym]
        ca = {k: ("✓" if c["pass"] else "✗") for k, c in r["test_a"]["conditions"].items()}
        cb = {k: ("✓" if c["pass"] else "✗") for k, c in r["test_b"]["conditions"].items()}
        print("%-16s %-18s %s %s %s %s %s %s %s %s %s" %
              (sym, r["verdict"],
               ca.get("A1_structure", "–"), ca.get("A2_sma200_not_falling", "–"),
               ca.get("A3_rs_leading_63d", "–"), ca.get("A4_not_extended", "–"),
               cb.get("B1_sma50_holding", "–"), cb.get("B2_rs_turning_28d", "–"),
               cb.get("B3_at_base_pivot", "–"), cb.get("B4_volume_dryup", "–"),
               cb.get("B5_volume_expansion", "–")))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("ledger", help="facts ledger JSON from scripts/market_facts.py")
    ap.add_argument("--out", help="write the full gate report to this path")
    ap.add_argument("--write", action="store_true", help="merge results into the ledger file (instruments.<SYM>.momentum_gate)")
    ap.add_argument("--config", default=SCORING_FILE)
    args = ap.parse_args()

    cfg = load_config(args.config)
    facts = json.load(open(args.ledger, encoding="utf-8"))
    results, skipped = run_ledger(facts, cfg)

    print_table(results)
    if skipped:
        print("skipped (no data): %s" % ", ".join(skipped))
    counts = {}
    for r in results.values():
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
    print("summary: %d names — %s%s" % (len(results),
                                        ", ".join("%s %d" % (k, counts[k]) for k in
                                                  ("IN_MOMENTUM", "ENTERING_MOMENTUM", "NO_MOMENTUM") if k in counts),
                                        "  [thresholds need calibration]" if cfg.get("needs_calibration") else ""))

    if args.out:
        json.dump({"market": facts.get("market"), "asof": facts.get("asof"),
                   "config": cfg, "results": results, "skipped": skipped},
                  open(args.out, "w", encoding="utf-8"), indent=2)
        print("wrote %s" % args.out)

    if args.write:
        for sym, r in results.items():
            facts["instruments"][sym]["momentum_gate"] = r
        json.dump(facts, open(args.ledger, "w", encoding="utf-8"), indent=2)
        print("merged momentum_gate into %s for %d names" % (args.ledger, len(results)))


if __name__ == "__main__":
    main()
