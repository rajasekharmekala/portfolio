#!/usr/bin/env python3
"""Displacement memo (constitution section 7, work package W8).

Produces the one-page advisory memo comparing one current holding against one
candidate name on the same scorecard. Advisory only: it never generates
orders. The user makes the decision and records it in the decision log
(data/decisions/).

The memo's six required elements (plan section 7):
  1. the recommendation (DISPLACE, HOLD, or WATCH)
  2. the holding and candidate side by side on the same scorecard
  3. the expected return of each with its range
  4. the transaction costs
  5. the change in portfolio caps and theme exposure
  6. the single condition that would reverse the advice

Every number in the memo is computed from the stored input JSON, so the memo
is reproducible: `--verify` regenerates it and requires a byte-identical file.

Recommendation logic (deterministic, documented in
.agents/workflows/displacement.md):
  - The candidate must be gate-eligible (momentum_gate verdict
    IN_MOMENTUM or ENTERING_MOMENTUM) to be bought into.
  - DISPLACE: candidate gate-eligible AND (candidate base return - holding
    base return - cost drag) >= reversal threshold.
  - WATCH: candidate not yet gate-eligible, but its base return already
    exceeds the holding's by at least the reversal threshold.
  - HOLD: everything else (including a proposed size above the 15% hard cap).

Usage:
  python scripts/displacement.py --input data/displacement/ORCL_vs_ADBE_2026-10-08.json \
      --out docs/reports/displacement/ORCL_vs_ADBE_2026-10-08.md
  python scripts/displacement.py --input ... --out ... --verify
"""
from __future__ import annotations

import argparse
import json
import os
import sys

CONFIG_PATH = os.path.join(".agents", "config", "scoring.json")
GATE_ELIGIBLE = {"IN_MOMENTUM", "ENTERING_MOMENTUM"}
REQUIRED_NAME_KEYS = (
    "symbol", "name", "bucket", "theme", "price",
    "weight_pct", "gate_verdict", "support_distance_atr",
    "expected_return_pct_12m", "scorecard",
)
REQUIRED_TOP_KEYS = ("schema_version", "as_of", "market", "holding", "candidate", "costs")


def fail(msg: str) -> None:
    print(f"DISPLACEMENT ERROR: {msg}", file=sys.stderr)
    sys.exit(2)


def load_input(path: str) -> dict:
    try:
        data = json.load(open(path, encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        fail(f"cannot read input {path}: {e}")
    for key in REQUIRED_TOP_KEYS:
        if key not in data:
            fail(f"input missing top-level key '{key}'")
    for side in ("holding", "candidate"):
        for key in REQUIRED_NAME_KEYS:
            if key not in data[side]:
                fail(f"input {side} missing key '{key}'")
        for key in ("low", "base", "high"):
            if key not in data[side]["expected_return_pct_12m"]:
                fail(f"input {side}.expected_return_pct_12m missing '{key}'")
        for key in ("quality", "valuation", "momentum"):
            if key not in data[side]["scorecard"]:
                fail(f"input {side}.scorecard missing '{key}'")
    return data


def load_limits(market: str) -> dict:
    try:
        cfg = json.load(open(CONFIG_PATH, encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        fail(f"cannot read {CONFIG_PATH}: {e}")
    hard_cap = cfg["position_sizing"]["hard_cap_pct"]
    band = cfg["buckets"]["TACTICAL_MOMENTUM"][market]
    return {"hard_cap_pct": hard_cap, "tactical_band_pct": list(band)}


def pct(x: float, digits: int = 2) -> str:
    return f"{x:+.{digits}f}%"


def usd(x: float) -> str:
    return f"${x:,.2f}"


def compute(inp: dict, limits: dict) -> dict:
    hold, cand = inp["holding"], inp["candidate"]
    costs = inp["costs"]
    notional = float(costs["notional_usd"])
    rt_bps = (float(costs["sell_bps"]) + float(costs["buy_bps"])
              + 2.0 * float(costs["slippage_bps"]))
    cost_usd = notional * rt_bps / 10_000.0
    cost_drag_pp = rt_bps / 100.0  # bps of notional == percentage points

    hold_base = float(hold["expected_return_pct_12m"]["base"])
    cand_base = float(cand["expected_return_pct_12m"]["base"])
    proposed = float(cand.get("proposed_weight_pct", 0.0))
    threshold = float(inp.get("params", {}).get("reversal_threshold_pp", 5.0))
    hard_cap = limits["hard_cap_pct"]

    eligible = cand["gate_verdict"] in GATE_ELIGIBLE
    cap_ok = proposed <= hard_cap
    edge_pp = cand_base - hold_base
    net_edge_pp = edge_pp - cost_drag_pp

    if not cap_ok:
        rec, rec_code = "HOLD", "cap_violation"
        rationale = (
            f"The proposed {pct(proposed, 1)} size for {cand['symbol']} is above "
            f"the {hard_cap:.0f}% single-name hard cap, so no displacement is "
            f"proposed at that size. Resize the proposal and re-run."
        )
        reverse = (
            f"Re-run this memo once the proposed {cand['symbol']} size is at or "
            f"below the {hard_cap:.0f}% hard cap and {cand['symbol']}'s gate "
            f"verdict is IN_MOMENTUM or ENTERING_MOMENTUM."
        )
    elif eligible and net_edge_pp >= threshold:
        rec, rec_code = "DISPLACE", "eligible_edge"
        new_w = min(proposed, hard_cap)
        rationale = (
            f"{cand['symbol']} is gate-eligible ({cand['gate_verdict']}) and its "
            f"base return of {pct(cand_base, 1)} exceeds {hold['symbol']}'s "
            f"{pct(hold_base, 1)} by {pct(edge_pp, 1)}; after the {pct(cost_drag_pp, 2)} "
            f"cost drag the net edge is {pct(net_edge_pp, 1)}, above the "
            f"{threshold:.1f}pp reversal threshold."
        )
        reverse = (
            f"Re-run this memo if {hold['symbol']} closes below its stop, or if "
            f"{cand['symbol']}'s 12-month base expected return falls to within "
            f"{threshold:.1f}pp of {hold['symbol']}'s."
        )
        post = {hold["symbol"]: 0.0, cand["symbol"]: new_w}
        theme_delta = {hold["theme"]: -float(hold["weight_pct"]),
                       cand["theme"]: new_w}
    elif (not eligible) and edge_pp >= threshold:
        rec, rec_code = "WATCH", "strong_candidate_gate_pending"
        rationale = (
            f"{cand['symbol']}'s base return of {pct(cand_base, 1)} already "
            f"exceeds {hold['symbol']}'s {pct(hold_base, 1)} by "
            f"{pct(edge_pp, 1)} (above the {threshold:.1f}pp threshold), but its "
            f"momentum gate is {cand['gate_verdict']}, so the system does not "
            f"allocate to it yet. No displacement now; the candidate is "
            f"watched for gate eligibility."
        )
        reverse = (
            f"Re-run this memo the day {cand['symbol']}'s gate verdict becomes "
            f"IN_MOMENTUM or ENTERING_MOMENTUM; if its base return is then still "
            f"at least {threshold:.1f}pp above {hold['symbol']}'s, the advice "
            f"moves from WATCH to DISPLACE."
        )
        post = {hold["symbol"]: float(hold["weight_pct"]), cand["symbol"]: 0.0}
        theme_delta = {}
    else:
        rec, rec_code = "HOLD", "no_edge"
        rationale = (
            f"{cand['symbol']}'s base return of {pct(cand_base, 1)} is "
            f"{abs(edge_pp):.1f}pp below {hold['symbol']}'s {pct(hold_base, 1)} "
            f"(net of the {pct(cost_drag_pp, 2)} cost drag the edge is "
            f"{pct(net_edge_pp, 1)}), and its momentum gate is "
            f"{cand['gate_verdict']}. There is no edge in selling "
            f"{hold['symbol']} to buy {cand['symbol']}."
        )
        reverse = (
            f"Re-run this memo when {cand['symbol']}'s momentum gate verdict "
            f"becomes IN_MOMENTUM or ENTERING_MOMENTUM and its 12-month base "
            f"expected return is at least {threshold:.1f}pp above "
            f"{hold['symbol']}'s current base of {pct(hold_base, 1)}."
        )
        post = {hold["symbol"]: float(hold["weight_pct"]), cand["symbol"]: 0.0}
        theme_delta = {}

    return {
        "rec": rec, "rec_code": rec_code, "rationale": rationale,
        "reverse": reverse, "rt_bps": rt_bps, "cost_usd": cost_usd,
        "cost_drag_pp": cost_drag_pp, "edge_pp": edge_pp,
        "net_edge_pp": net_edge_pp, "eligible": eligible, "cap_ok": cap_ok,
        "proposed": proposed, "post": post, "theme_delta": theme_delta,
        "hold_base": hold_base, "cand_base": cand_base,
        "threshold": threshold, "hard_cap": hard_cap,
        "tactical_band": limits["tactical_band_pct"],
    }


def render(inp: dict, r: dict) -> str:
    hold, cand = inp["holding"], inp["candidate"]
    costs = inp["costs"]
    as_of, market = inp["as_of"], inp["market"]

    def row(label, h, c):
        return f"| {label} | {h} | {c} |\n"

    h_ret = hold["expected_return_pct_12m"]
    c_ret = cand["expected_return_pct_12m"]
    h_sc = hold["scorecard"]
    c_sc = cand["scorecard"]

    scorecard = (
        "| | " + hold["symbol"] + " (holding) | " + cand["symbol"] + " (candidate) |\n"
        "|---|---|---|\n"
        + row("Name", hold["name"], cand["name"])
        + row("Price (" + as_of + ")", f"${hold['price']:,.2f}", f"${cand['price']:,.2f}")
        + row("Bucket", hold["bucket"], cand["bucket"])
        + row("Theme", hold["theme"], cand["theme"])
        + row("Weight in market portfolio",
              f"{float(hold['weight_pct']):.2f}%",
              f"0% (proposed {r['proposed']:.1f}%)")
        + row("Momentum gate (frozen snapshot)", hold["gate_verdict"], cand["gate_verdict"])
        + row("Distance to support",
              f"{float(hold['support_distance_atr']):.2f} ATR",
              f"{float(cand['support_distance_atr']):.2f} ATR")
        + row("Scorecard (quality / valuation / momentum)",
              f"{h_sc['quality']} / {h_sc['valuation']} / {h_sc['momentum']}",
              f"{c_sc['quality']} / {c_sc['valuation']} / {c_sc['momentum']}")
        + row("Expected 12-mo return (low / base / high)",
              f"{pct(float(h_ret['low']))} / {pct(float(h_ret['base']))} / {pct(float(h_ret['high']))}",
              f"{pct(float(c_ret['low']))} / {pct(float(c_ret['base']))} / {pct(float(c_ret['high']))}")
    )

    if r["rec"] == "DISPLACE":
        cap_theme = (
            f"- {r['hard_cap']:.0f}% single-name hard cap: proposed {cand['symbol']} size "
            f"{pct(r['proposed'], 1)} - compliant (cap {r['hard_cap']:.0f}%).\n"
            f"- Tactical band {r['tactical_band'][0]}-{r['tactical_band'][1]}%: "
            f"recomputed after the trade; the {cand['symbol']} addition of "
            f"{pct(r['proposed'], 1)} must keep the bucket inside the band.\n"
            f"- Theme exposure: "
            + "; ".join(f"{k} {v:+.2f}pp" for k, v in r["theme_delta"].items())
            + f".\n"
            f"- Post-trade weights: {hold['symbol']} {r['post'][hold['symbol']]:.2f}%, "
            f"{cand['symbol']} {r['post'][cand['symbol']]:.2f}%."
        )
    else:
        band = r["tactical_band"]
        cap_theme = (
            f"- {r['hard_cap']:.0f}% single-name hard cap: no trade, so no cap is touched "
            f"(proposed {cand['symbol']} size {pct(r['proposed'], 1)} is "
            f"{'within' if r['cap_ok'] else 'ABOVE'} the {r['hard_cap']:.0f}% cap).\n"
            f"- Tactical band {band[0]}-{band[1]}%: unchanged (no trade).\n"
            f"- Theme exposure: unchanged (no trade)."
        )

    note_hold = hold.get("source_note", "")
    note_cand = cand.get("source_note", "")

    md = f"""# Displacement memo - {hold['symbol']} vs {cand['symbol']}

**As of:** {as_of}  |  **Market:** {market}  |  **Advisory only - no orders are generated.**

## Recommendation: **{r['rec']}**

{r['rationale']}

## Side by side on the same scorecard

{scorecard}
## Expected return of each, with its range

- **{hold['symbol']} (holding):** base {pct(r['hold_base'])} over 12 months
  (range {pct(float(h_ret['low']))} to {pct(float(h_ret['high']))}).
  Source: {note_hold}
- **{cand['symbol']} (candidate):** base {pct(r['cand_base'])} over 12 months
  (range {pct(float(c_ret['low']))} to {pct(float(c_ret['high']))}).
  Source: {note_cand}

## Transaction costs

Round trip of {r['rt_bps']:.0f} bps (sell {float(costs['sell_bps']):.0f} + buy
{float(costs['buy_bps']):.0f} + slippage {float(costs['slippage_bps']):.0f} on each leg) on
the {usd(float(costs['notional_usd']))} notional = **{usd(r['cost_usd'])}**, a
{pct(r['cost_drag_pp'])} drag. Tax note: {costs.get('tax_note', 'n/a')}

## Portfolio caps and theme exposure

{cap_theme}

## The single condition that would reverse this advice

{r['reverse']}

---
Stored inputs: `{inp.get('input_file', 'data/displacement/')}`. Numbers above are
computed from those inputs by `scripts/displacement.py`; re-run with `--verify`
to reproduce. You make the decision and record it in the decision log
(`data/decisions/`).
"""
    return md


def main() -> None:
    ap = argparse.ArgumentParser(description="One-page displacement memo (advisory).")
    ap.add_argument("--input", required=True, help="stored input JSON")
    ap.add_argument("--out", required=True, help="memo output path (markdown)")
    ap.add_argument("--verify", action="store_true",
                    help="regenerate and require byte-identical output")
    args = ap.parse_args()

    inp = load_input(args.input)
    inp["input_file"] = os.path.abspath(args.input)
    limits = load_limits(inp["market"])
    r = compute(inp, limits)
    text = render(inp, r)

    if args.verify:
        try:
            existing = open(args.out, encoding="utf-8").read()
        except OSError as e:
            fail(f"--verify cannot read existing memo {args.out}: {e}")
        if existing != text:
            print(f"VERIFY FAIL: {args.out} does not match the memo regenerated "
                  f"from the stored inputs.", file=sys.stderr)
            sys.exit(1)
        print(f"VERIFY PASS: {args.out} reproduced byte-identical from the stored inputs.")
        return

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"memo written: {args.out} (recommendation: {r['rec']})")


if __name__ == "__main__":
    main()
