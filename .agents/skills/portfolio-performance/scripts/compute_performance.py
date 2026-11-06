#!/usr/bin/env python3
"""Replay stock transactions and compare broker P&L with an SPY reference."""
from __future__ import annotations

import argparse
import json
import math
import re
import calendar
import sys
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path


def load_jsonl(path: Path):
    rows = []
    with path.open() as f:
        for line_no, line in enumerate(f, 1):
            if line.strip():
                try:
                    row = json.loads(line)
                    row["_line"] = line_no
                    row["_date"] = date.fromisoformat(row["date"])
                    rows.append(row)
                except Exception as e:
                    raise ValueError(f"{path}:{line_no}: {e}") from e
    return sorted(rows, key=lambda r: (r["_date"], r["_line"]))


def historical_prices(symbols, market, starts, as_of, overrides):
    """Download closes from Yahoo; return exact-or-prior close per requested date."""
    needed = sorted(set(starts + [as_of]))
    out, warnings = {}, []
    try:
        import yfinance as yf
    except ImportError:
        return {}, ["yfinance is unavailable; historical marks were not fetched"]
    for symbol in symbols:
        requests = {}
        for d in needed:
            key = d.isoformat()
            if key in overrides.get(symbol, {}):
                requests[d] = float(overrides[symbol][key])
        if len(requests) == len(needed):
            out[symbol] = requests
            continue
        candidates = [symbol + ".NS", symbol + ".BO"] if market == "IN" else [symbol]
        hist = None
        for ticker in candidates:
            try:
                h = yf.Ticker(ticker).history(start=(min(needed)-timedelta(days=10)).isoformat(),
                                               end=(max(needed)+timedelta(days=2)).isoformat(),
                                               auto_adjust=False)
                if h is not None and not h.empty:
                    col = "Close"
                    hist = [(ts.date(), float(v)) for ts, v in h[col].dropna().items()]
                    break
            except Exception:
                pass
        if not hist:
            warnings.append(f"No Yahoo history found for {symbol}")
            if requests:
                out[symbol] = requests
            continue
        marks = {}
        for d in needed:
            if d in requests:
                marks[d] = requests[d]
                continue
            prior = [(dt, v) for dt, v in hist if dt <= d]
            if prior:
                marks[d] = prior[-1][1]
            else:
                warnings.append(f"No historical close on or before {d} for {symbol}")
        out[symbol] = marks
    return out, warnings


def replay(rows, positions_mv, marks, start=None):
    """Average-cost replay. With start, carry start shares at their start mark."""
    q, basis = defaultdict(float), defaultdict(float)
    realized = 0.0
    income = 0.0
    fees = 0.0
    warnings = []
    start_date = start
    for row in rows:
        d, typ = row["_date"], str(row.get("type", "")).lower()
        sym = row.get("symbol")
        if start_date and d < start_date:
            # Replay the account immediately before the start date, then reset basis
            # to the start valuation when crossing into the requested window.
            if sym and typ == "buy":
                q[sym] += float(row.get("quantity") or 0)
                basis[sym] += float(row.get("amount") or 0)
            elif sym and typ == "sell":
                qty, amt = float(row.get("quantity") or 0), float(row.get("amount") or 0)
                avg = basis[sym] / q[sym] if q[sym] else 0.0
                used = min(qty, q[sym])
                basis[sym] -= avg * used
                q[sym] -= used
            elif sym and typ == "split":
                split_move(row, q, basis)
            continue
        if start_date and d >= start_date and not getattr(replay, "_reset_done", False):
            for s in list(q):
                price = marks.get(s)
                if price is not None:
                    basis[s] = q[s] * price
                else:
                    warnings.append(f"{s}: start mark unavailable; original cost basis retained")
            replay._reset_done = True
        if sym and typ == "buy":
            q[sym] += float(row.get("quantity") or 0)
            basis[sym] += float(row.get("amount") or 0)
        elif sym and typ == "sell":
            qty, amt = float(row.get("quantity") or 0), float(row.get("amount") or 0)
            avg = basis[sym] / q[sym] if q[sym] else 0.0
            used = min(qty, q[sym])
            realized += amt - avg * used
            basis[sym] -= avg * used
            q[sym] -= used
            if qty > used + 1e-7:
                warnings.append(f"{sym}: sale exceeds replayed quantity by {qty-used:g}")
        elif sym and typ == "split":
            split_move(row, q, basis)
        elif typ == "fee":
            fees += abs(float(row.get("amount") or 0))
        elif typ == "cash":
            note = (row.get("note") or "").lower()
            if "net of" not in note and any(k in note for k in ("dividend", "interest", "stock lending", "stock lend")):
                income += float(row.get("amount") or 0)

    # If the requested start is after all recorded activity, still mark replayed shares.
    if start_date and not getattr(replay, "_reset_done", False):
        for s in list(q):
            if s in marks:
                basis[s] = q[s] * marks[s]
        replay._reset_done = True
    replay._reset_done = False
    current_mv = sum(float(v) for v in positions_mv.values())
    current_cost = sum(basis.values())
    return {"realized": realized, "unrealized": current_mv-current_cost,
            "income": income, "fees": fees, "net_pnl": realized+(current_mv-current_cost)+income-fees,
            "current_market_value": current_mv, "recorded_cost_basis": current_cost,
            "open_quantities": dict(q), "warnings": warnings}


def held_symbols_at(rows, when):
    q = defaultdict(float)
    for row in rows:
        if row["_date"] >= when:
            break
        sym, typ = row.get("symbol"), str(row.get("type", "")).lower()
        if not sym:
            continue
        if typ == "buy":
            q[sym] += float(row.get("quantity") or 0)
        elif typ == "sell":
            q[sym] -= float(row.get("quantity") or 0)
        elif typ == "split":
            split_move(row, q, defaultdict(float))
    return {s for s, qty in q.items() if qty > 1e-8}


def split_move(row, quantities, basis):
    """Apply a split row encoded as bonus shares, optionally renaming a ticker."""
    new_symbol = row.get("symbol")
    note = row.get("note") or ""
    match = re.search(r"([A-Z0-9.-]+) became ([A-Z0-9.-]+)", note)
    if match:
        old_symbol, new_symbol = match.groups()
        quantities[new_symbol] += quantities.pop(old_symbol, 0.0)
        basis[new_symbol] += basis.pop(old_symbol, 0.0)
    if row.get("factor") is not None:
        factor = float(row["factor"])
        old_qty = quantities[new_symbol]
        quantities[new_symbol] *= factor
        basis[new_symbol] *= factor if row.get("basis_adjusted", False) else 1.0
    else:
        # Repository split rows store the number of bonus shares in quantity.
        quantities[new_symbol] += float(row.get("quantity") or 0)


def spy_return(start, end):
    try:
        import yfinance as yf
        h = yf.Ticker("SPY").history(start=(start-timedelta(days=10)).isoformat(),
                                     end=(end+timedelta(days=2)).isoformat(), auto_adjust=False)
        if h is None or h.empty:
            return None, "SPY history unavailable"
        col = "Adj Close" if "Adj Close" in h.columns else "Close"
        vals = [(ts.date(), float(v)) for ts, v in h[col].dropna().items()]
        a = [v for d, v in vals if d <= start]
        b = [v for d, v in vals if d <= end]
        if not a or not b:
            return None, "SPY adjusted closes unavailable for requested dates"
        return b[-1]/a[-1]-1, None
    except Exception as e:
        return None, f"SPY history fetch failed: {e}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path.cwd())
    ap.add_argument("--snapshot", required=True, type=Path)
    args = ap.parse_args()
    snapshot = json.loads(args.snapshot.read_text())
    as_of = date.fromisoformat(snapshot["as_of"])
    results = {"as_of": as_of.isoformat(), "benchmark": {}, "accounts": {}}
    six_month = as_of.year, as_of.month-6
    y, m = six_month
    if m <= 0:
        y, m = y-1, m+12
    default_starts = {"1y": as_of.replace(year=as_of.year-1),
                      "6m": date(y, m, min(as_of.day, calendar.monthrange(y, m)[1]))}
    period_start_cfg = snapshot.get("period_starts", {})
    starts_by_label = {k: date.fromisoformat(period_start_cfg.get(k, v.isoformat())) for k, v in default_starts.items()}
    for period, start in starts_by_label.items():
        ret, err = spy_return(start, as_of)
        results["benchmark"][period] = {"start": start.isoformat(), "return": ret,
                                         "label": "SPY adjusted close proxy", "warning": err}
    for name, account in snapshot["accounts"].items():
        log = Path(account["transaction_log"])
        if not log.is_absolute():
            log = args.root / log
        rows = load_jsonl(log)
        positions = {k: float(v) for k, v in account.get("positions_mv", {}).items()}
        starts = [starts_by_label["1y"], starts_by_label["6m"]]
        symbols = set(positions)
        start_symbols = {d: held_symbols_at(rows, d) for d in starts}
        symbols |= set.union(*start_symbols.values()) if start_symbols else set()
        overrides = snapshot.get("historical_price_overrides", {})
        hist, hw = historical_prices(symbols, account["market"], starts, as_of, overrides)
        current = replay(rows, positions, {})
        equity_dates = [r["_date"] for r in rows if r.get("type") in ("buy", "sell") and r.get("symbol")]
        overall_start = min(equity_dates) if equity_dates else as_of
        overall_spy, overall_spy_warning = spy_return(overall_start, as_of)
        periods = {}
        for label, start in zip(("1y", "6m"), starts):
            # Replay only events inside the window, carrying opening positions at start-date prices.
            window_rows = [r for r in rows if r["_date"] >= start]
            start_marks = {s: hist.get(s, {}).get(start) for s in start_symbols[start]}
            # Seed the inventory from all pre-window trades by retaining those rows; replay() resets
            # their carrying basis to the start mark at the boundary.
            metrics = replay(rows, positions, {s: start_marks[s] for s in start_symbols[start] if start_marks.get(s) is not None}, start=start)
            # replays return only post-start realized/income/fees and ending unrealized above start marks
            periods[label] = {k: metrics[k] for k in ("realized", "unrealized", "income", "fees", "net_pnl")}
            periods[label]["start"] = start.isoformat()
            periods[label]["warnings"] = metrics["warnings"]
            missing = sorted(s for s in start_symbols[start] if start_marks.get(s) is None)
            if missing:
                periods[label]["warnings"].append("Missing start-date prices: " + ", ".join(missing))
        out = {"currency": account["currency"], "market": account["market"],
               "source": account.get("source"), "cash": account.get("cash"),
               "current_value": sum(positions.values()) + float(account.get("cash") or 0) + float(account.get("options_mv") or 0),
               "positions_market_value": sum(positions.values()), "overall": current,
               "periods": periods, "overall_start": overall_start.isoformat(),
               "overall_spy_return": overall_spy, "overall_spy_warning": overall_spy_warning,
               "price_warnings": hw,
               "notes": account.get("notes", [])}
        if account.get("options_mv") is not None and account.get("options_cost_basis") is not None:
            out["options"] = {"market_value": account["options_mv"], "cost_basis": account["options_cost_basis"],
                               "unrealized_pnl": account["options_mv"]-account["options_cost_basis"]}
        results["accounts"][name] = out
    json.dump(results, sys.stdout, indent=2, default=str)
    print()


if __name__ == "__main__":
    main()
