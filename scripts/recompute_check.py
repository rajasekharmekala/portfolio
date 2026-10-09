#!/usr/bin/env python3
"""
W2 — Recompute checker for shortlist records.

Recomputes stored values from the raw price fields of the same row and
reports every mismatch beyond tolerance:

  1. asymmetry_ratio  = (target_base - cmp) / (cmp - stop_loss)
     (the formula used in SYSTEM_IMPROVEMENT_PLAN.md section 1:
      CRWD stores 3.6 but recomputes to 0.36; ORCL stores 3.2 but
      recomputes to 1.11)
  2. price-field consistency: stop_loss < cmp < target_base
     (and target_bull >= target_base when both exist)
  3. entry-zone sanity: entry_zone_low <= entry_zone_high, and the zone
     sits below the current price for rows that are not rejected

Usage:
    .venv/bin/python scripts/recompute_check.py
    .venv/bin/python scripts/recompute_check.py --tolerance 0.10 --market US

Exit code 1 if any mismatch is found, 0 otherwise.
"""

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MARKETS = ("US", "IN")


def recomputed_asymmetry(cmp_, stop, target):
    if None in (cmp_, stop, target):
        return None
    if cmp_ <= stop or target <= cmp_:
        return None
    return (target - cmp_) / (cmp_ - stop)


def check_row(row, tol):
    """Returns list of (kind, message) findings for one row."""
    out = []
    sym = row.get("symbol", "?")
    cmp_ = row.get("cmp")
    stop = row.get("stop_loss")
    target = row.get("target_base")
    bull = row.get("target_bull")
    el, eh = row.get("entry_zone_low"), row.get("entry_zone_high")
    stored = row.get("asymmetry_ratio")
    rejected = row.get("action_verdict") == "REJECTED" or row.get("strategy_bucket") == "REJECTED"

    # 1. asymmetry recomputation
    calc = recomputed_asymmetry(cmp_, stop, target)
    if calc is not None:
        if stored is None:
            out.append(("asym_missing", f"{sym}: asymmetry not stored but recomputes to {calc:.2f}"))
        elif abs(calc - stored) > tol * max(abs(calc), 1.0):
            out.append(("asym_mismatch", f"{sym}: stored {stored:.2f} vs recomputed {calc:.2f}"))
    else:
        if stored is not None:
            out.append(("asym_uncomputable", f"{sym}: stored {stored:.2f} but stop/target do not bracket cmp"))
        if stop is not None and cmp_ is not None and stop >= cmp_:
            out.append(("price_order", f"{sym}: stop_loss {stop} >= cmp {cmp_}"))
        if target is not None and cmp_ is not None and target <= cmp_:
            out.append(("price_order", f"{sym}: target_base {target} <= cmp {cmp_}"))

    # 2. bull target
    if bull is not None and target is not None and bull < target:
        out.append(("price_order", f"{sym}: target_bull {bull} < target_base {target}"))

    # 3. entry zone sanity
    if el is not None and eh is not None:
        if el > eh:
            out.append(("entry_zone", f"{sym}: entry_zone_low {el} > entry_zone_high {eh}"))
        if not rejected and cmp_ is not None and el < cmp_ * 0.99 and eh > cmp_ * 1.01:
            pass  # zone straddling price is possible pre-gap; not an error
        if not rejected and cmp_ is not None and el > cmp_ and eh > cmp_:
            out.append(("entry_zone", f"{sym}: entry zone {el}-{eh} fully above cmp {cmp_}"))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--tolerance", type=float, default=0.05,
                    help="relative tolerance for asymmetry mismatches (default 0.05)")
    ap.add_argument("--market", choices=list(MARKETS) + ["ALL"], default="ALL")
    args = ap.parse_args()

    markets = [args.market] if args.market != "ALL" else list(MARKETS)
    total = 0
    asym_mismatches = 0

    for market in markets:
        data = json.loads((REPO / "data" / "shortlist" / f"{market}.json").read_text(encoding="utf-8"))
        print(f"== {market} ==")
        market_findings = 0
        for sheet, rows in data["sheets"].items():
            if sheet == "Swap_Decision_Matrix":
                continue
            for row in rows:
                findings = check_row(row, args.tolerance)
                for kind, msg in findings:
                    if kind == "asym_mismatch":
                        asym_mismatches += 1
                    print(f"  [{kind}] {sheet}: {msg}")
                market_findings += len(findings)
                total += len(findings)
        print(f"  {market}: {market_findings} findings")

    print(f"\ntotal findings: {total} (asymmetry mismatches: {asym_mismatches})")
    sys.exit(1 if total else 0)


if __name__ == "__main__":
    main()
