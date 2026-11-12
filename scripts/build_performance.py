#!/usr/bin/env python3
"""Build portfolio performance, P&L timelines, and XIRR metrics for docs/portal-performance.json."""
from __future__ import annotations

import argparse
import calendar
import json
import re
import time
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from data_layer import accounts_for

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
OUTPUT = DOCS / "portal-performance.json"
OPTIONS_PATH = ROOT / "data" / "options" / "US.json"
CACHE_DIR = Path(__file__).resolve().parent / ".cache" / "prices"
CACHE_TTL_SECONDS = 6 * 3600


def yf_candidates(symbol: str, market: str) -> list[str]:
    if market == "IN":
        base = symbol[:-3] if symbol.endswith("-SM") else symbol
        cands = [f"{base}.NS", f"{base}.BO"]
        if base != symbol:
            cands = [f"{symbol}.NS", f"{symbol}.BO"] + cands
        return cands
    return [symbol]


def fetch_symbol_history(
    symbol: str,
    market: str,
    start_date: date,
    end_date: date,
    *,
    use_adj_close: bool = False,
    refresh: bool = False,
) -> tuple[dict[str, float], str | None]:
    """Fetch daily closes from Yahoo Finance with a local disk cache."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[^A-Za-z0-9._-]", "_", f"{market}_{symbol}{'_adj' if use_adj_close else ''}")
    cache_path = CACHE_DIR / f"{safe}.json"

    if not refresh and cache_path.exists():
        try:
            cached = json.loads(cache_path.read_text(encoding="utf-8"))
            fetched_at = cached.get("fetched_at", 0)
            cached_start = cached.get("start_date", "9999-12-31")
            cached_end = cached.get("end_date", "0000-01-01")
            if (
                time.time() - fetched_at < CACHE_TTL_SECONDS
                and cached_start <= start_date.isoformat()
                and cached_end >= end_date.isoformat()
            ):
                return cached.get("prices", {}), cached.get("ticker")
        except (OSError, ValueError):
            pass

    import yfinance as yf

    req_start = (start_date - timedelta(days=14)).isoformat()
    req_end = (end_date + timedelta(days=2)).isoformat()
    candidates = [symbol] if symbol.startswith("^") or symbol == "SPY" else yf_candidates(symbol, market)

    prices: dict[str, float] = {}
    used_ticker = None
    for ticker in candidates:
        try:
            hist = yf.Ticker(ticker).history(start=req_start, end=req_end, auto_adjust=False)
            if hist is not None and not hist.empty:
                col = "Adj Close" if (use_adj_close and "Adj Close" in hist.columns) else "Close"
                series = hist[col].dropna()
                if not series.empty:
                    prices = {ts.date().isoformat(): round(float(val), 4) for ts, val in series.items()}
                    used_ticker = ticker
                    break
        except Exception:
            continue

    payload = {
        "symbol": symbol,
        "market": market,
        "ticker": used_ticker,
        "fetched_at": time.time(),
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "prices": prices,
    }
    try:
        cache_path.write_text(json.dumps(payload), encoding="utf-8")
    except OSError:
        pass
    return prices, used_ticker


def price_on_or_before(sorted_dates: list[str], prices: dict[str, float], target_iso: str) -> float | None:
    """Binary search for the latest available close <= target_iso."""
    if not sorted_dates:
        return None
    lo, hi = 0, len(sorted_dates) - 1
    ans = -1
    while lo <= hi:
        mid = (lo + hi) // 2
        if sorted_dates[mid] <= target_iso:
            ans = mid
            lo = mid + 1
        else:
            hi = mid - 1
    if ans == -1:
        return None
    return prices[sorted_dates[ans]]


def classify_cash_row(account: str, row: dict) -> str:
    """Classify cash row into external contribution/withdrawal, income, closed_pos, or options."""
    note = (row.get("note") or "").lower()
    if account == "Zerodha":
        return "external"
    if account == "Charles Schwab":
        if "journal" in note:
            return "external"
        if "dividend" in note or "interest" in note:
            return "income"
        if "closed position" in note:
            return "closed_realized"
        return "other_income"
    if account == "Robinhood":
        if "opening balance" in note:
            return "opening_state"
        if any(k in note for k in ("rtp", "ach", "instant deposit")):
            return "external"
        if "closed position" in note:
            return "closed_realized"
        if any(k in note for k in ("call", "put", "option")):
            return "options_cash"
        if any(k in note for k in ("int", "cdiv", "slip", "stock lending", "dividend")):
            return "income"
        return "other_income"
    return "other_income"


def compute_xirr(cashflows: list[tuple[date, float]]) -> float | None:
    """Solve XIRR via bracketed bisection. Returns annualized decimal (e.g. 0.185 = 18.5%)."""
    if not cashflows or len(cashflows) < 2:
        return None
    # Aggregate same-day cashflows for stability
    by_day: dict[date, float] = defaultdict(float)
    for d, amt in cashflows:
        if abs(amt) > 1e-9:
            by_day[d] += amt
    merged = sorted(by_day.items())
    if len(merged) < 2:
        return None
    if not (any(a > 0 for _, a in merged) and any(a < 0 for _, a in merged)):
        return None
    d0 = merged[0][0]
    dmax = merged[-1][0]
    if (dmax - d0).days < 1:
        return None

    cfs = [((d - d0).days / 365.0, a) for d, a in merged]

    def npv(r: float) -> float:
        base = 1.0 + r
        if base <= 0:
            return float("inf")
        total = 0.0
        for t, a in cfs:
            try:
                total += a / (base ** t)
            except OverflowError:
                return 0.0 if a > 0 else -float("inf")
        return total

    lo, hi = -0.9999, 10.0
    f_lo, f_hi = npv(lo), npv(hi)
    while f_lo * f_hi > 0 and hi < 50000.0:
        hi *= 2.0
        f_hi = npv(hi)
    if f_lo * f_hi > 0:
        return None

    for _ in range(120):
        mid = 0.5 * (lo + hi)
        f_mid = npv(mid)
        if abs(f_mid) < 1e-7 or (hi - lo) < 1e-9:
            return round(mid, 6)
        if f_lo * f_mid <= 0:
            hi, f_hi = mid, f_mid
        else:
            lo, f_lo = mid, f_mid
    return round(0.5 * (lo + hi), 6)


def subtract_months(d: date, months: int) -> date:
    y = d.year
    m = d.month - months
    while m <= 0:
        y -= 1
        m += 12
    day = min(d.day, calendar.monthrange(y, m)[1])
    return date(y, m, day)


def load_account_rows(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            row = json.loads(line)
            row["_line"] = line_no
            row["_date"] = date.fromisoformat(row["date"])
            rows.append(row)
    return sorted(rows, key=lambda r: (r["_date"], r["_line"]))


def replay_through_dates(
    rows: list[dict],
    target_dates: list[date],
    price_lookup: dict[str, tuple[list[str], dict[str, float]]],
) -> list[dict]:
    """Replay transactions chronologically and snapshot portfolio state at each target date."""
    qty: dict[str, float] = defaultdict(float)
    basis: dict[str, float] = defaultdict(float)
    sym_realized: dict[str, float] = defaultdict(float)
    realized = 0.0
    cash = 0.0
    external_in = 0.0
    income = 0.0
    fees = 0.0
    closed_realized = 0.0
    options_cash = 0.0
    cum_buys = 0.0
    cum_sells = 0.0

    snapshots = []
    idx = 0
    n_rows = len(rows)
    account_name = rows[0]["account"] if rows else ""

    for d in target_dates:
        while idx < n_rows and rows[idx]["_date"] <= d:
            r = rows[idx]
            idx += 1
            typ = r["type"]
            sym = r.get("symbol")
            amt = float(r.get("amount") or 0.0)
            q = float(r.get("quantity") or 0.0)

            if typ in ("opening", "buy") and sym:
                qty[sym] += q
                basis[sym] += amt
                if typ == "buy":
                    cash -= amt
                    cum_buys += amt
            elif typ == "sell" and sym:
                cur_q = qty[sym]
                avg = (basis[sym] / cur_q) if cur_q > 1e-9 else 0.0
                used = min(q, cur_q) if cur_q > 1e-9 else 0.0
                gain = amt - avg * used
                realized += gain
                sym_realized[sym] += gain
                basis[sym] -= avg * used
                qty[sym] -= q
                cash += amt
                cum_sells += amt
                if qty[sym] <= 1e-9:
                    qty[sym] = 0.0
                    basis[sym] = 0.0
            elif typ == "split" and sym:
                note = r.get("note") or ""
                m = re.search(r"([A-Z0-9.-]+) became ([A-Z0-9.-]+)", note)
                if m:
                    old_s, new_s = m.groups()
                    if old_s != new_s and old_s in qty:
                        qty[new_s] += qty.pop(old_s, 0.0)
                        basis[new_s] += basis.pop(old_s, 0.0)
                        sym_realized[new_s] += sym_realized.pop(old_s, 0.0)
                if r.get("factor") is not None:
                    qty[sym] *= float(r["factor"])
                else:
                    qty[sym] += q
            elif typ == "fee":
                fees += abs(amt)
                cash -= abs(amt)
            elif typ == "cash":
                cash += amt
                kind = classify_cash_row(account_name, r)
                if kind == "external":
                    external_in += amt
                elif kind == "closed_realized":
                    closed_realized += amt
                elif kind == "options_cash":
                    options_cash += amt
                elif kind == "income" or kind == "other_income":
                    income += amt

        d_iso = d.isoformat()
        equity_mv = 0.0
        open_basis = 0.0
        missing_marks = []
        for s, s_qty in qty.items():
            if s_qty <= 1e-9:
                continue
            open_basis += basis[s]
            sdates, pmap = price_lookup.get(s, ([], {}))
            px = price_on_or_before(sdates, pmap, d_iso)
            if px is not None:
                equity_mv += s_qty * px
            else:
                equity_mv += basis[s]
                missing_marks.append(s)

        unrealized = equity_mv - open_basis
        snapshots.append({
            "date": d_iso,
            "equityMv": round(equity_mv, 2),
            "costBasis": round(open_basis, 2),
            "cash": round(cash, 2),
            "accountValue": round(equity_mv + cash, 2),
            "capitalPutIn": round(external_in, 2),
            "netBuys": round(max(0.0, cum_buys - cum_sells), 2),
            "cumBuys": round(cum_buys, 2),
            "cumSells": round(cum_sells, 2),
            "realizedPnl": round(realized, 2),
            "unrealizedPnl": round(unrealized, 2),
            "equityTotalPnl": round(realized + unrealized, 2),
            "closedPosCash": round(closed_realized, 2),
            "optionsCash": round(options_cash, 2),
            "income": round(income, 2),
            "fees": round(fees, 2),
            "netAccountPnl": round(realized + unrealized + closed_realized + options_cash + income - fees, 2),
            "missingMarks": missing_marks,
            "_qty": {s: round(v, 6) for s, v in qty.items() if v > 1e-9},
            "_basis": {s: round(basis[s], 2) for s, v in qty.items() if v > 1e-9},
            "_sym_realized": {s: round(v, 2) for s, v in sym_realized.items()},
        })
    return snapshots


def compute_window_metrics(
    rows: list[dict],
    start_date: date,
    as_of: date,
    price_lookup: dict[str, tuple[list[str], dict[str, float]]],
    end_snap: dict,
    is_all: bool,
    has_dated_deposits: bool,
    options_mv: float,
    has_options: bool,
) -> dict:
    """Window P&L (start-mark carried), Modified Dietz return and XIRR for [start_date, as_of]."""
    account_name = rows[0]["account"] if rows else ""
    first_date = rows[0]["_date"] if rows else as_of
    effective_start = first_date if (is_all or start_date <= first_date) else start_date
    has_full_window = is_all or (first_date <= start_date)

    qty: dict[str, float] = defaultdict(float)
    basis: dict[str, float] = defaultdict(float)
    cash_start = 0.0
    pre_buys = 0.0
    pre_sells = 0.0

    for r in rows:
        if not is_all and r["_date"] < effective_start:
            typ, sym = r["type"], r.get("symbol")
            amt = float(r.get("amount") or 0.0)
            q = float(r.get("quantity") or 0.0)
            if typ in ("opening", "buy") and sym:
                qty[sym] += q
                basis[sym] += amt
                if typ == "buy":
                    cash_start -= amt
                    pre_buys += amt
            elif typ == "sell" and sym:
                cur_q = qty[sym]
                avg = (basis[sym] / cur_q) if cur_q > 1e-9 else 0.0
                used = min(q, cur_q) if cur_q > 1e-9 else 0.0
                basis[sym] -= avg * used
                qty[sym] -= q
                cash_start += amt
                pre_sells += amt
                if qty[sym] <= 1e-9:
                    qty[sym] = 0.0
                    basis[sym] = 0.0
            elif typ == "split" and sym:
                note = r.get("note") or ""
                m = re.search(r"([A-Z0-9.-]+) became ([A-Z0-9.-]+)", note)
                if m:
                    old_s, new_s = m.groups()
                    if old_s != new_s and old_s in qty:
                        qty[new_s] += qty.pop(old_s, 0.0)
                        basis[new_s] += basis.pop(old_s, 0.0)
                if r.get("factor") is not None:
                    qty[sym] *= float(r["factor"])
                else:
                    qty[sym] += q
            elif typ == "fee":
                cash_start -= abs(amt)
            elif typ == "cash":
                cash_start += amt

    start_iso = effective_start.isoformat()
    start_equity_mv = 0.0
    missing_start = []
    if not is_all:
        for s, s_qty in list(qty.items()):
            if s_qty <= 1e-9:
                continue
            sdates, pmap = price_lookup.get(s, ([], {}))
            px = price_on_or_before(sdates, pmap, start_iso)
            if px is not None:
                basis[s] = s_qty * px
                start_equity_mv += basis[s]
            else:
                start_equity_mv += basis[s]
                missing_start.append(s)

    if start_equity_mv <= 1e-6 and pre_buys == 0.0 and pre_sells == 0.0:
        first_trade = next((r["_date"] for r in rows if r["type"] in ("buy", "sell") and r["_date"] >= effective_start), None)
        if first_trade is not None:
            effective_start = first_trade

    span_days = (as_of - effective_start).days

    def weight(d: date) -> float:
        return (span_days - (d - effective_start).days) / span_days if span_days > 0 else 1.0

    w_realized = 0.0
    w_income = 0.0
    w_fees = 0.0
    w_closed_pos = 0.0
    w_options_cash = 0.0
    w_buys = 0.0
    w_sells = 0.0
    dietz_flow = 0.0

    equity_cfs: list[tuple[date, float]] = []
    if not is_all and start_equity_mv > 1e-6:
        equity_cfs.append((effective_start, -start_equity_mv))

    acct_cfs: list[tuple[date, float]] = []
    if has_dated_deposits and not is_all:
        start_acct_val = start_equity_mv + cash_start
        if abs(start_acct_val) > 1e-6:
            acct_cfs.append((effective_start, -start_acct_val))

    for r in rows:
        d = r["_date"]
        if not is_all and d < effective_start:
            continue
        if d > as_of:
            break
        typ, sym = r["type"], r.get("symbol")
        amt = float(r.get("amount") or 0.0)
        q = float(r.get("quantity") or 0.0)
        if typ in ("opening", "buy") and sym:
            qty[sym] += q
            basis[sym] += amt
            if typ == "buy":
                w_buys += amt
                dietz_flow += weight(d) * amt
                equity_cfs.append((d, -amt))
        elif typ == "sell" and sym:
            cur_q = qty[sym]
            avg = (basis[sym] / cur_q) if cur_q > 1e-9 else 0.0
            used = min(q, cur_q) if cur_q > 1e-9 else 0.0
            w_realized += amt - avg * used
            basis[sym] -= avg * used
            qty[sym] -= q
            w_sells += amt
            dietz_flow -= weight(d) * amt
            equity_cfs.append((d, amt))
            if qty[sym] <= 1e-9:
                qty[sym] = 0.0
                basis[sym] = 0.0
        elif typ == "split" and sym:
            note = r.get("note") or ""
            m = re.search(r"([A-Z0-9.-]+) became ([A-Z0-9.-]+)", note)
            if m:
                old_s, new_s = m.groups()
                if old_s != new_s and old_s in qty:
                    qty[new_s] += qty.pop(old_s, 0.0)
                    basis[new_s] += basis.pop(old_s, 0.0)
            if r.get("factor") is not None:
                qty[sym] *= float(r["factor"])
            else:
                qty[sym] += q
        elif typ == "fee":
            w_fees += abs(amt)
        elif typ == "cash":
            kind = classify_cash_row(account_name, r)
            if kind == "external":
                if has_dated_deposits:
                    acct_cfs.append((d, -amt))
            elif kind == "closed_realized":
                w_closed_pos += amt
            elif kind == "options_cash":
                w_options_cash += amt
            elif kind == "opening_state":
                if has_dated_deposits:
                    acct_cfs.append((d, -amt))
            elif kind in ("income", "other_income"):
                w_income += amt

    end_equity_mv = end_snap["equityMv"]
    end_basis = sum(basis[s] for s, q in qty.items() if q > 1e-9)
    w_unrealized = end_equity_mv - end_basis
    w_equity_pnl = w_realized + w_unrealized
    w_options_pnl = (w_options_cash + options_mv) if is_all else 0.0
    w_net_pnl = w_equity_pnl + w_closed_pos + w_options_pnl + w_income - w_fees

    dietz_capital = start_equity_mv + dietz_flow
    return_pct = w_equity_pnl / dietz_capital if dietz_capital > 1e-6 else None

    span_start = min((d for d, _ in equity_cfs), default=None)
    xirr_eligible = span_start is not None and (as_of - span_start).days >= 365
    equity_cfs.append((as_of, end_equity_mv))
    eq_xirr = compute_xirr(equity_cfs) if xirr_eligible else None

    acct_xirr = None
    if has_dated_deposits and not (has_options and not is_all):
        acct_cfs.append((as_of, end_snap["accountValue"] + (options_mv if is_all else 0.0)))
        acct_span = min((d for d, _ in acct_cfs[:-1]), default=None)
        if acct_span is not None and (as_of - acct_span).days >= 365:
            acct_xirr = compute_xirr(acct_cfs)

    return {
        "startDate": effective_start.isoformat(),
        "endDate": as_of.isoformat(),
        "hasFullWindow": has_full_window,
        "horizonDays": span_days,
        "spanStart": span_start.isoformat() if span_start else None,
        "xirrEligible": xirr_eligible,
        "startEquityMv": round(start_equity_mv, 2),
        "endEquityMv": round(end_equity_mv, 2),
        "buysInWindow": round(w_buys, 2),
        "sellsInWindow": round(w_sells, 2),
        "baseBuys": round(pre_buys, 2),
        "baseSells": round(pre_sells, 2),
        "realizedPnl": round(w_realized, 2),
        "unrealizedPnl": round(w_unrealized, 2),
        "equityPnl": round(w_equity_pnl, 2),
        "closedPosCash": round(w_closed_pos, 2),
        "optionsPnl": round(w_options_pnl, 2),
        "optionsIncluded": is_all,
        "income": round(w_income, 2),
        "fees": round(w_fees, 2),
        "netPnl": round(w_net_pnl, 2),
        "returnPct": round(return_pct, 6) if return_pct is not None else None,
        "equityXirr": eq_xirr,
        "accountXirr": acct_xirr,
        "missingStartMarks": sorted(set(missing_start)),
    }


def load_options_book(account_name: str) -> list[dict]:
    """Open option contracts for one broker account, as recorded in data/options (not marked to market)."""
    if not OPTIONS_PATH.exists():
        return []
    data = json.loads(OPTIONS_PATH.read_text(encoding="utf-8"))
    return [p for p in data.get("positions", []) if p.get("broker_account") == account_name]


def build_performance(refresh: bool = False) -> dict:
    """Compute performance, timelines, and XIRR for all profiles and write docs/portal-performance.json."""
    today = date.today()
    profiles = []
    benchmark_cache: dict[str, tuple[list[str], dict[str, float]]] = {}

    # Preload benchmarks: SPY (US) and ^NSEI (IN)
    for b_sym, b_mkt in (("SPY", "US"), ("^NSEI", "IN")):
        b_prices, _ = fetch_symbol_history(b_sym, b_mkt, date(2020, 11, 1), today, use_adj_close=True, refresh=refresh)
        benchmark_cache[b_sym] = (sorted(b_prices.keys()), b_prices)

    for market in ("IN", "US"):
        currency = "INR" if market == "IN" else "USD"
        bench_sym = "^NSEI" if market == "IN" else "SPY"
        bench_label = "NIFTY 50" if market == "IN" else "S&P 500 (SPY)"

        for path_str in accounts_for(market):
            path = Path(path_str)
            rows = load_account_rows(path)
            if not rows:
                continue
            account_name = rows[0]["account"]
            first_date = rows[0]["_date"]
            last_tx_date = rows[-1]["_date"]
            has_dated_deposits = account_name in ("Robinhood", "Charles Schwab")

            # Fetch historical prices for every symbol in this account
            syms = sorted({r["symbol"] for r in rows if r.get("symbol")})
            price_lookup: dict[str, tuple[list[str], dict[str, float]]] = {}
            all_price_dates: set[str] = set()
            for sym in syms:
                pmap, _ = fetch_symbol_history(sym, market, first_date, today, use_adj_close=False, refresh=refresh)
                sdates = sorted(pmap.keys())
                price_lookup[sym] = (sdates, pmap)
                all_price_dates.update(sdates)

            as_of_iso = max(all_price_dates) if all_price_dates else today.isoformat()
            as_of = date.fromisoformat(as_of_iso)

            period_defs = [
                ("1M", subtract_months(as_of, 1), False),
                ("3M", subtract_months(as_of, 3), False),
                ("6M", subtract_months(as_of, 6), False),
                ("1Y", subtract_months(as_of, 12), False),
                ("YTD", date(as_of.year, 1, 1), False),
                ("ALL", first_date, True),
            ]

            one_year_ago = subtract_months(as_of, 12)
            trading_dates = sorted(
                date.fromisoformat(d)
                for d in all_price_dates
                if first_date <= date.fromisoformat(d) <= as_of
            )
            if not trading_dates or trading_dates[-1] != as_of:
                trading_dates.append(as_of)

            timeline_dates: list[date] = []
            last_week = None
            for td in trading_dates:
                if td >= one_year_ago or td == trading_dates[0] or td == as_of:
                    timeline_dates.append(td)
                else:
                    yr_wk = td.isocalendar()[:2]
                    if yr_wk != last_week:
                        timeline_dates.append(td)
                        last_week = yr_wk
            timeline_dates = sorted(set(timeline_dates) | {start for _, start, _ in period_defs})

            snapshots = replay_through_dates(rows, timeline_dates, price_lookup)
            end_snap = snapshots[-1]

            options_book = load_options_book(account_name)
            options_mv = round(sum(float(p["current_mv_usd"]) for p in options_book), 2)
            options_cost = round(sum(float(p["cost_basis_usd"]) for p in options_book), 2)
            options_pnl_total = round(end_snap["optionsCash"] + options_mv, 2) if options_book else end_snap["optionsCash"]
            has_options = bool(options_book)

            holdings_rows = []
            for sym, qty_val in sorted(end_snap["_qty"].items()):
                cb = end_snap["_basis"].get(sym, 0.0)
                sdates, pmap = price_lookup.get(sym, ([], {}))
                px = price_on_or_before(sdates, pmap, as_of_iso)
                mv = round(qty_val * px, 2) if px is not None else cb
                unr = round(mv - cb, 2)
                unr_pct = round(unr / cb, 6) if cb > 1e-6 else None
                holdings_rows.append({
                    "symbol": sym,
                    "costBasis": round(cb, 2),
                    "marketValue": mv,
                    "unrealizedPnl": unr,
                    "unrealizedPct": unr_pct,
                    "realizedPnl": round(end_snap["_sym_realized"].get(sym, 0.0), 2),
                    "priceMissing": px is None,
                })
            holdings_rows.sort(key=lambda x: x["marketValue"], reverse=True)

            options_rows = [
                {
                    "contract": p["contract_symbol"],
                    "underlying": p["underlying"],
                    "type": p["type"],
                    "strikeUsd": p["strike_usd"],
                    "expiry": p["expiry_date"],
                    "contracts": p["contracts"],
                    "costBasis": round(float(p["cost_basis_usd"]), 2),
                    "marketValue": round(float(p["current_mv_usd"]), 2),
                    "unrealizedPnl": round(float(p["unrealized_pnl_usd"]), 2),
                    "unrealizedPct": round(float(p["pnl_pct"]), 6),
                }
                for p in sorted(options_book, key=lambda p: (p["underlying"], p["expiry_date"]))
            ]

            periods_out = {}
            b_dates, b_map = benchmark_cache[bench_sym]
            b_end = price_on_or_before(b_dates, b_map, as_of_iso)
            for label, start_d, is_all in period_defs:
                pm = compute_window_metrics(
                    rows, start_d, as_of, price_lookup, end_snap, is_all, has_dated_deposits,
                    options_mv, has_options,
                )
                b_start = price_on_or_before(b_dates, b_map, pm["startDate"])
                pm["benchmarkReturn"] = (
                    round(b_end / b_start - 1.0, 6) if (b_start and b_end and b_start > 0) else None
                )
                pm["benchmarkCagr"] = None
                if pm["xirrEligible"] and b_end:
                    b_span = price_on_or_before(b_dates, b_map, pm["spanStart"])
                    if b_span and b_span > 0:
                        pm["benchmarkCagr"] = round((b_end / b_span) ** (365.0 / pm["horizonDays"]) - 1.0, 6)
                pm["benchmarkLabel"] = bench_label
                periods_out[label] = pm

            clean_timeline = [
                {
                    "date": s["date"],
                    "equityMv": s["equityMv"],
                    "costBasis": s["costBasis"],
                    "cumBuys": s["cumBuys"],
                    "cumSells": s["cumSells"],
                    "capitalPutIn": s["capitalPutIn"],
                    "netBuys": s["netBuys"],
                    "realizedPnl": s["realizedPnl"],
                    "unrealizedPnl": s["unrealizedPnl"],
                    "equityTotalPnl": s["equityTotalPnl"],
                    "cash": s["cash"],
                    "accountValue": s["accountValue"],
                    "netAccountPnl": s["netAccountPnl"],
                }
                for s in snapshots
            ]

            notes = [
                "Period returns are Modified Dietz on equity: equity P&L divided by starting market value plus "
                "time-weighted net purchases. Annualized XIRR and benchmark CAGR are shown only when capital has "
                "been invested for at least one year.",
                "Window P&L carries shares held at the window start at their start-date close, so the chart "
                "and period table reconcile to the same figure. A window that starts before any capital was "
                "invested is measured from the first equity trade.",
            ]
            if options_book:
                notes.append(
                    "Open option contracts are valued at the marks recorded in data/options/US.json, which are not "
                    "marked to market. Option P&L (premium cash plus recorded value) is included only in the "
                    "All-time column because historical option values are unavailable."
                )
            if account_name == "Zerodha":
                notes.append(
                    "Zerodha Tradebook has no dated bank transfers before the 2026-10 statement. Net deployed "
                    "capital is reconstructed from live cash less trade-derived cash, so it is an estimate."
                )
            if account_name == "Robinhood":
                notes.append(
                    "The 2025-01-02 implied opening margin debit is reconciled to month-end statements. It is the "
                    "account's starting value in Account XIRR, not a deposit, so profit is measured against the true "
                    "starting net worth. Equity trades in the export begin in May 2026, so equity XIRR is not "
                    "annualized until one year of invested capital exists."
                )
            if account_name == "Charles Schwab":
                notes.append(
                    "Closed positions without symbol-level trade rows are included in Total Account P&L "
                    "but not in equity P&L."
                )

            cap_in = end_snap["capitalPutIn"]
            overall_net = round(
                end_snap["equityTotalPnl"] + end_snap["closedPosCash"] + options_pnl_total
                + end_snap["income"] - end_snap["fees"], 2,
            )
            overall_return_on_cap = round(overall_net / cap_in, 6) if cap_in > 1e-6 else None
            equity_first_trade = next((r["_date"].isoformat() for r in rows if r["type"] in ("buy", "sell")), None)

            profiles.append({
                "id": account_name.lower().replace(" ", "-"),
                "name": account_name,
                "market": market,
                "currency": currency,
                "firstTxDate": first_date.isoformat(),
                "lastTxDate": last_tx_date.isoformat(),
                "equityFirstTradeDate": equity_first_trade,
                "asOf": as_of_iso,
                "hasDatedDeposits": has_dated_deposits,
                "capitalLabel": (
                    "Net deployed capital (Tradebook-reconciled, estimate)"
                    if account_name == "Zerodha" else "Total Money Put In"
                ),
                "benchmarkLabel": bench_label,
                "summary": {
                    "equityMarketValue": end_snap["equityMv"],
                    "openCostBasis": end_snap["costBasis"],
                    "cash": end_snap["cash"],
                    "optionsMarketValue": options_mv,
                    "optionsCostBasis": options_cost,
                    "optionsUnrealizedPnl": round(options_mv - options_cost, 2),
                    "totalAccountValue": round(end_snap["accountValue"] + options_mv, 2),
                    "capitalPutIn": cap_in,
                    "equityRealizedPnl": end_snap["realizedPnl"],
                    "unrealizedPnl": end_snap["unrealizedPnl"],
                    "equityTotalPnl": end_snap["equityTotalPnl"],
                    "closedPosCash": end_snap["closedPosCash"],
                    "optionsCash": end_snap["optionsCash"],
                    "optionsPnl": options_pnl_total,
                    "income": end_snap["income"],
                    "fees": end_snap["fees"],
                    "overallNetPnl": overall_net,
                    "overallReturnOnCapital": overall_return_on_cap,
                },
                "optionsBook": {
                    "positions": options_rows,
                    "source": "data/options/US.json (recorded marks, not marked to market)" if options_book else None,
                },
                "periods": periods_out,
                "holdings": holdings_rows,
                "timeline": clean_timeline,
                "notes": notes,
            })

    result = {
        "schemaVersion": 1,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "profiles": profiles,
    }
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"Performance built: {len(profiles)} profiles -> {OUTPUT}")
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--refresh", action="store_true", help="Ignore price cache and re-fetch from Yahoo Finance")
    args = ap.parse_args()
    build_performance(refresh=args.refresh)


if __name__ == "__main__":
    main()

