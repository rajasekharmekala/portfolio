#!/usr/bin/env python3
"""W10 - Decision log and outcome tracking.

Records each decision (thesis, expected return, invalidation, date) in
data/decisions/decisions.json and compares results with the benchmark at
3, 6 and 12 months using only the stored prices.

Commands
--------
--init                Create an empty decision ledger if missing.
--add <file.json>     Validate and append one decision record.
--refresh <id>        Fetch missing stored price bars (symbol + benchmark)
                      from yfinance into the record. The only command that
                      touches the network.
--report [id]         Compute the 3/6/12-month outcome rows for one
                      decision (or all) strictly from stored prices.

A decision record:
{
  "id": "YYYY-MM-DD_SYMBOL_SLUG",
  "date": "YYYY-MM-DD",                 # decision date
  "market": "US" | "IN",
  "symbol": "ADBE",
  "benchmark": "SPY",
  "action": "WAIT_FOR_SUPPORT",
  "price_at_decision": 241.05,
  "benchmark_price_at_decision": 638.5,
  "thesis": "...",
  "expected_return_pct_12m": {"low": -19.1, "base": 11.98, "high": 36.94},
  "invalidation": "close below 210.88 ...",
  "invalidation_price": 210.88,          # optional numeric level
  "status": "open",
  "prices": {"ADBE": {"YYYY-MM-DD": px}, "SPY": {"YYYY-MM-DD": px}}
}
"""

from __future__ import annotations

import argparse
import calendar
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LEDGER = ROOT / "data" / "decisions" / "decisions.json"
HORIZONS_MONTHS = (3, 6, 12)

REQUIRED_KEYS = ("id", "date", "market", "symbol", "benchmark", "action",
                 "thesis", "invalidation")


def fail(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def load_ledger() -> dict:
    if not LEDGER.exists():
        return {"schema_version": 1, "decisions": []}
    data = json.loads(LEDGER.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1 or "decisions" not in data:
        fail(f"ledger {LEDGER} is not schema_version 1")
    return data


def save_ledger(data: dict) -> None:
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    LEDGER.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                      encoding="utf-8")


def validate_record(rec: dict) -> None:
    for key in REQUIRED_KEYS:
        if not rec.get(key):
            fail(f"decision missing non-empty key {key!r}")
    try:
        datetime.strptime(rec["date"], "%Y-%m-%d")
    except ValueError:
        fail(f"date must be YYYY-MM-DD, got {rec['date']!r}")
    exp = rec.get("expected_return_pct_12m") or {}
    for key in ("low", "base", "high"):
        if not isinstance(exp.get(key), (int, float)):
            fail(f"expected_return_pct_12m.{key} must be a number")
    if not isinstance(rec.get("prices"), dict) or not rec["prices"]:
        fail("prices must be an object {SYMBOL: {date: px}}")
    for series_name, series in rec["prices"].items():
        if not isinstance(series, dict):
            fail(f"prices[{series_name}] must be an object")
        for d in series:
            datetime.strptime(d, "%Y-%m-%d")


def cmd_add(path: str) -> None:
    rec = json.loads(Path(path).read_text(encoding="utf-8"))
    validate_record(rec)
    data = load_ledger()
    if any(d["id"] == rec["id"] for d in data["decisions"]):
        fail(f"duplicate decision id {rec['id']!r}")
    data["decisions"].append(rec)
    save_ledger(data)
    print(f"added decision {rec['id']} ({len(data['decisions'])} total)")


def add_months(d: date, months: int) -> date:
    month_index = d.month - 1 + months
    year = d.year + month_index // 12
    month = month_index % 12 + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def parse_iso(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()


def first_bar_on_or_after(series: dict, target: date):
    """First (date, price) stored on/after target, or None."""
    for d in sorted(series):
        dd = parse_iso(d)
        if dd >= target:
            return d, series[d]
    return None


def bars_on_or_before(series: dict, upto: date):
    return {d: p for d, p in series.items() if parse_iso(d) <= upto}


def outcome_row(dec: dict, months: int):
    """One 3/6/12-month row, computed only from stored prices."""
    sym_series = dec["prices"].get(dec["symbol"], {})
    bench_series = dec["prices"].get(dec.get("benchmark", ""), {})
    if not sym_series:
        return {"horizon_months": months, "status": "NOT_REFRESHED"}
    dec_date = parse_iso(dec["date"])
    target = add_months(dec_date, months)

    out = {"horizon_months": months, "target_date": target.isoformat()}

    sym_bar = first_bar_on_or_after(sym_series, target)
    if not sym_bar:
        out["status"] = "NOT_REACHED"
        latest = max(sym_series)
        out["note"] = (f"no stored bar on/after {target}; "
                       f"latest stored bar {latest}")
        return out

    bar_date, px = sym_bar
    bench_bar = first_bar_on_or_after(bench_series, target)
    bench_px0 = dec.get("benchmark_price_at_decision")
    px0 = dec.get("price_at_decision", sym_series[sorted(sym_series)[0]])

    out["asof_date"] = bar_date
    out["symbol_close"] = px
    out["symbol_return_pct"] = round((px / px0 - 1.0) * 100.0, 2)
    if bench_bar and bench_px0:
        out["benchmark_close"] = bench_bar[1]
        out["benchmark_return_pct"] = round(
            (bench_bar[1] / bench_px0 - 1.0) * 100.0, 2)
        out["excess_pct"] = round(out["symbol_return_pct"]
                                  - out["benchmark_return_pct"], 2)
    if months == 12:
        base = dec["expected_return_pct_12m"]["base"]
        out["expected_base_pct"] = base
        out["vs_expected_pp"] = round(out["symbol_return_pct"] - base, 2)

    # invalidation check over stored bars up to the asof date
    lvl = dec.get("invalidation_price")
    if isinstance(lvl, (int, float)):
        prior = bars_on_or_before(sym_series, parse_iso(bar_date))
        hits = [d for d, p in prior.items() if p < lvl]
        out["invalidation"] = (f"HIT {min(hits)} (close below {lvl})"
                               if hits else "not hit")
    return out


def cmd_report(dec_id: str | None) -> None:
    data = load_ledger()
    decisions = data["decisions"]
    if dec_id:
        decisions = [d for d in decisions if d["id"] == dec_id]
        if not decisions:
            fail(f"no decision with id {dec_id!r}")
    if not decisions:
        fail("ledger has no decisions")

    for dec in decisions:
        print(f"## {dec['id']}  ({dec['date']}, {dec['market']}, "
              f"{dec['symbol']} vs {dec['benchmark']}, {dec['action']})")
        if not dec["prices"].get(dec["symbol"]):
            print("NOT_REFRESHED: no stored prices; run "
                  f"`outcomes.py --refresh {dec['id']}` first.\n")
            continue
        print(f"thesis: {dec['thesis']}")
        exp = dec["expected_return_pct_12m"]
        print(f"expected 12m: low {exp['low']}% / base {exp['base']}% / "
              f"high {exp['high']}%   invalidation: {dec['invalidation']}")
        print()
        print("| horizon | asof | symbol close | symbol ret % | "
              "bench close | bench ret % | excess pp | invalidation |")
        print("|---|---|---|---|---|---|---|---|")
        for months in HORIZONS_MONTHS:
            row = outcome_row(dec, months)
            if row.get("status") in ("NOT_REACHED", "NOT_REFRESHED"):
                print(f"| {months}m | - | - | - | - | - | - | "
                      f"{row.get('status', 'NOT_REACHED').lower().replace('_', ' ')} "
                      f"({row.get('note', 'run --refresh first')}) |")
                continue
            inv = row.get("invalidation", "-")
            print(f"| {months}m | {row['asof_date']} | {row['symbol_close']}"
                  f" | {row['symbol_return_pct']:+.2f} "
                  f"| {row.get('benchmark_close', '-')} "
                  f"| {row.get('benchmark_return_pct', '-')} "
                  f"| {row.get('excess_pct', '-')} | {inv} |")
            if months == 12 and "vs_expected_pp" in row:
                print(f"  12m vs expected base: {row['vs_expected_pp']:+.2f} pp")
        print()

    json_out = []
    for dec in decisions:
        json_out.append({
            "id": dec["id"],
            "date": dec["date"],
            "symbol": dec["symbol"],
            "benchmark": dec["benchmark"],
            "rows": [outcome_row(dec, m) for m in HORIZONS_MONTHS],
        })
    print("JSON:")
    print(json.dumps(json_out, indent=2))


def cmd_refresh(dec_id: str) -> None:
    try:
        import yfinance as yf
    except ImportError:
        fail("yfinance is not installed in this environment")
    data = load_ledger()
    dec = next((d for d in data["decisions"] if d["id"] == dec_id), None)
    if not dec:
        fail(f"no decision with id {dec_id!r}")
    dec_date = parse_iso(dec["date"])
    start = (dec_date - timedelta(days=7)).isoformat()
    end = date.today().isoformat()
    symbols = {dec["symbol"], dec["benchmark"]}
    for sym in sorted(symbols):
        hist = yf.Ticker(sym).history(start=start, end=end, interval="1d",
                                      auto_adjust=False)
        if hist is None or len(hist) == 0 or "Close" not in hist.columns:
            fail(f"no price data returned for {sym}")
        close = hist["Close"]
        series = dec["prices"].setdefault(sym, {})
        added = 0
        for idx, px in close.items():
            d = idx.date().isoformat() if hasattr(idx, "date") else str(idx)[:10]
            if d not in series:
                series[d] = round(float(px), 2)
                added += 1
        dec["prices"][sym] = dict(sorted(series.items()))
        print(f"{sym}: stored {len(dec['prices'][sym])} bars "
              f"({added} new)")
    # fill decision-date prices if the caller left them out: the bar on the
    # decision date, else the closest stored bar before it
    for field, sym in (("price_at_decision", dec["symbol"]),
                       ("benchmark_price_at_decision", dec["benchmark"])):
        if dec.get(field) is None:
            series = dec["prices"][sym]
            prior = [d for d in series if d <= dec["date"]]
            if not prior:
                fail(f"no stored {sym} bar on/before {dec['date']}")
            dec[field] = series[max(prior)]
    save_ledger(data)
    print(f"refreshed {dec_id}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--init", action="store_true",
                    help="create an empty ledger if missing")
    ap.add_argument("--add", metavar="FILE",
                    help="validate and append one decision record")
    ap.add_argument("--refresh", metavar="ID",
                    help="fetch missing stored bars via yfinance")
    ap.add_argument("--report", nargs="?", const="__ALL__", default=None,
                    metavar="ID", help="compute 3/6/12-month rows")
    args = ap.parse_args()

    if args.init:
        if not LEDGER.exists():
            save_ledger({"schema_version": 1, "decisions": []})
            print(f"created {LEDGER}")
        else:
            print(f"ledger already exists: {LEDGER}")
        return
    if args.add:
        cmd_add(args.add)
        return
    if args.refresh:
        cmd_refresh(args.refresh)
        return
    if args.report:
        cmd_report(None if args.report == "__ALL__" else args.report)
        return
    ap.print_help()


if __name__ == "__main__":
    main()
