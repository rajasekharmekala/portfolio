#!/usr/bin/env python3
"""Deterministic Multi-Timeframe Chartist + Options Chain & Beginner Payoff Engine.

Powers both:
  1. Standalone `options_desk` runs (fast intraday/daily re-pricing without rewriting dossiers).
  2. Integrated `#options-overlay` & Chapter 8 multi-timeframe analysis inside
     `company_report` and `dossier_refresh`.

Features:
  - Multi-timeframe TradingView read (Weekly 1W + Daily 1D + 4-Hour 4H) for shelves,
    Bollinger squeeze (VCP), RSI divergence, and Fibonacci/Classic pivots.
  - Optional read-only macOS Chrome probe (`macos-browser-automation`) for logged-in
    Robinhood quotes/positions and open TradingView charts. If Chrome is closed, JS
    events are off, or Robinhood is not logged in, it NEVER fails — it records
    `robinhood_session.status = "not_logged_in_or_unavailable"` and falls back to
    public chain data cleanly.
  - Exact Black-Scholes Delta, Theta ($/day), Vega, HV20 vs. Implied Volatility,
    liquidity gates (OI & bid-ask spread), fundamental safety interlock
    (`FUNDAMENTAL_FAIL` blocks bullish calls), and beginner-friendly dollar/rupee
    scenario payoff tables.
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import math
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import requests
import yfinance as yf

REPO = Path(__file__).resolve().parents[1]
CHROME_SKILL_SCRIPTS = Path.home() / ".agents" / "skills" / "macos-browser-automation" / "scripts"

MTF_TV_COLUMNS = [
    "name",
    "description",
    "exchange",
    "close",
    "change",
    "Perf.W",
    "Perf.1M",
    "Perf.3M",
    "RSI",
    "RSI|240",
    "RSI|1W",
    "SMA20",
    "SMA50",
    "SMA200",
    "SMA30|1W",
    "EMA20",
    "EMA20|240",
    "SMA50|240",
    "EMA10|1W",
    "ATR",
    "BB.upper",
    "BB.lower",
    "Pivot.M.Classic.S1",
    "Pivot.M.Classic.S2",
    "Pivot.M.Classic.Middle",
    "Pivot.M.Classic.R1",
    "Pivot.M.Classic.R2",
    "price_52_week_high",
    "price_52_week_low",
    "volume",
    "average_volume_30d_calc",
    "Recommend.All",
    "Recommend.All|240",
    "Recommend.All|1W",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    )
}


def _round(val: Any, digits: int = 2) -> Optional[float]:
    if val is None or isinstance(val, bool):
        return None
    try:
        f = float(val)
        return round(f, digits) if math.isfinite(f) else None
    except (TypeError, ValueError):
        return None


def _norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _norm_pdf(x: float) -> float:
    return math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)


def black_scholes_call_greeks(
    spot: float,
    strike: float,
    dte_days: int,
    iv: float,
    risk_free: float = 0.045,
) -> Dict[str, float]:
    """Compute exact per-share Black-Scholes call price, delta, daily theta, and vega."""
    t = max(dte_days / 365.0, 1.0 / 365.0)
    sigma = max(iv, 0.05)
    if spot <= 0 or strike <= 0:
        return {"bs_price": 0.0, "delta": 0.0, "theta_per_day": 0.0, "vega_per_1pct": 0.0}
    sqrt_t = math.sqrt(t)
    d1 = (math.log(spot / strike) + (risk_free + 0.5 * sigma * sigma) * t) / (sigma * sqrt_t)
    d2 = d1 - sigma * sqrt_t
    nd1 = _norm_cdf(d1)
    nd2 = _norm_cdf(d2)
    npd1 = _norm_pdf(d1)
    disc = math.exp(-risk_free * t)
    price = spot * nd1 - strike * disc * nd2
    theta_annual = -(spot * npd1 * sigma) / (2.0 * sqrt_t) - risk_free * strike * disc * nd2
    vega_1pct = spot * npd1 * sqrt_t * 0.01
    return {
        "bs_price": round(max(0.0, price), 4),
        "delta": round(nd1, 3),
        "theta_per_day": round(theta_annual / 365.0, 4),
        "vega_per_1pct": round(vega_1pct, 4),
    }


def probe_browser_sessions(symbol: str, market: str, enabled: bool = True) -> Dict[str, Any]:
    """Read-only macOS Chrome probe for Robinhood (US) and TradingView tabs.

    Never throws if Chrome is closed, Apple Events JS is disabled, or Robinhood is
    logged out — cleanly reports status so workflows continue uninterrupted.
    """
    result: Dict[str, Any] = {
        "robinhood": {
            "checked": False,
            "accessible": False,
            "logged_in": False,
            "status": "skipped" if not enabled else "not_applicable_for_market",
            "note": "Browser check disabled." if not enabled else "Robinhood applies to US market.",
            "observed_quotes": None,
        },
        "tradingview": {
            "checked": False,
            "accessible": False,
            "status": "skipped" if not enabled else "unavailable",
            "active_tabs": [],
        },
    }
    if not enabled or sys.platform != "darwin" or not CHROME_SKILL_SCRIPTS.is_dir():
        if enabled:
            result["robinhood"]["status"] = "unavailable"
            result["robinhood"]["note"] = "macOS Chrome automation skill unavailable in this environment; using public options data."
        return result

    try:
        if str(CHROME_SKILL_SCRIPTS) not in sys.path:
            sys.path.insert(0, str(CHROME_SKILL_SCRIPTS))
        import chrome_ctl  # type: ignore
        status = chrome_ctl.check_status()
    except Exception as exc:
        msg = f"Chrome session inaccessible ({exc}); continuing with public chain data."
        result["robinhood"].update(checked=True, status="unavailable", note=msg)
        result["tradingview"].update(checked=True, status="unavailable")
        return result

    if not status.get("ok"):
        msg = f"{status.get('message', 'Chrome not running')} — continuing with public chain data."
        result["robinhood"].update(checked=True, status="unavailable", note=msg)
        result["tradingview"].update(checked=True, status="unavailable")
        return result

    # 1. Inspect open TradingView tabs (read-only)
    try:
        tv_tabs = chrome_ctl.list_tabs("tradingview\\.com")
        result["tradingview"] = {
            "checked": True,
            "accessible": bool(tv_tabs),
            "status": "connected" if tv_tabs else "no_open_tab",
            "active_tabs": [{"title": t.get("title"), "url": t.get("url")} for t in tv_tabs[:3]],
        }
    except Exception:
        result["tradingview"].update(checked=True, status="unavailable")

    # 2. Inspect Robinhood login & quotes for US symbols (strictly read-only)
    if market.upper() == "US":
        try:
            rh_tabs = chrome_ctl.list_tabs("robinhood\\.com")
            if not rh_tabs:
                result["robinhood"] = {
                    "checked": True,
                    "accessible": False,
                    "logged_in": False,
                    "status": "no_robinhood_tab",
                    "note": "No open Robinhood tab in Chrome; live account quotes skipped, using public options chain.",
                    "observed_quotes": None,
                }
            else:
                js_probe = (
                    "(() => {"
                    "  const path = window.location.pathname || '';"
                    "  const txt = (document.body && document.body.innerText) ? document.body.innerText.slice(0, 4000) : '';"
                    "  const loggedOut = path.startsWith('/login') || /Log in to Robinhood|Sign Up/i.test(txt.slice(0, 600));"
                    "  return JSON.stringify({url: window.location.href, title: document.title, logged_in: !loggedOut, snippet: txt.slice(0, 800)});"
                    "})()"
                )
                raw_eval = chrome_ctl.eval_js(js_probe, match="robinhood\\.com")
                parsed = json.loads(raw_eval) if raw_eval else {}
                if not parsed.get("logged_in"):
                    result["robinhood"] = {
                        "checked": True,
                        "accessible": False,
                        "logged_in": False,
                        "status": "not_logged_in",
                        "note": "Robinhood tab is not logged in; live account data skipped, using public options chain & recorded ledger.",
                        "observed_quotes": None,
                    }
                else:
                    result["robinhood"] = {
                        "checked": True,
                        "accessible": True,
                        "logged_in": True,
                        "status": "connected",
                        "note": f"Connected to live Robinhood browser tab ({parsed.get('title', 'Robinhood')}).",
                        "observed_quotes": {"url": parsed.get("url"), "title": parsed.get("title")},
                    }
        except Exception as exc:
            result["robinhood"] = {
                "checked": True,
                "accessible": False,
                "logged_in": False,
                "status": "unavailable",
                "note": f"Robinhood live data could not be accessed ({exc}); using public options chain.",
                "observed_quotes": None,
            }
    return result


def fetch_multitimeframe_chart(market: str, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
    """Fetch Weekly (1W) + Daily (1D) + 4-Hour (4H) structure from TradingView scanner."""
    if not symbols:
        return {}
    region = "india" if market == "IN" else "america"
    exchanges = ["NSE", "BSE"] if market == "IN" else ["NASDAQ", "NYSE", "AMEX"]
    tickers, t2s = [], {}
    for sym in symbols:
        for ex in exchanges:
            tk = f"{ex}:{sym.upper()}"
            tickers.append(tk)
            t2s[tk] = sym.upper()
    try:
        resp = requests.post(
            f"https://scanner.tradingview.com/{region}/scan",
            json={"symbols": {"tickers": tickers, "query": {"types": []}}, "columns": MTF_TV_COLUMNS},
            headers=HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
        rows = resp.json().get("data", [])
    except Exception:
        return {}

    out: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        tk = row.get("s", "")
        sym = t2s.get(tk)
        if not sym:
            continue
        if sym in out and market == "IN" and out[sym].get("exchange") == "NSE":
            continue
        d = dict(zip(MTF_TV_COLUMNS, row.get("d", [])))
        close = _round(d.get("close"))
        sma20 = _round(d.get("SMA20"))
        sma50 = _round(d.get("SMA50"))
        sma200 = _round(d.get("SMA200"))
        sma30w = _round(d.get("SMA30|1W")) or sma200
        ema10w = _round(d.get("EMA10|1W")) or sma50
        bb_up = _round(d.get("BB.upper"))
        bb_lo = _round(d.get("BB.lower"))
        bb_width_pct = _round(((bb_up - bb_lo) / close) * 100.0, 2) if (close and bb_up and bb_lo and close > 0) else None
        rsi_d = _round(d.get("RSI"))
        rsi_4h = _round(d.get("RSI|240"))
        rsi_w = _round(d.get("RSI|1W"))
        ema20_4h = _round(d.get("EMA20|240"))
        perf_1m = _round(d.get("Perf.1M"))

        # Classify professional multi-timeframe setup archetype
        shelf_candidates = [
            x for x in (sma200, sma30w, _round(d.get("Pivot.M.Classic.S1")), _round(d.get("Pivot.M.Classic.S2")), _round(d.get("price_52_week_low")))
            if x and close and x <= close * 1.03
        ]
        major_shelf = max(shelf_candidates) if shelf_candidates else (sma200 or sma50)
        dist_to_200d_pct = _round(((close / sma200) - 1.0) * 100.0, 2) if (close and sma200 and sma200 > 0) else None
        intraday_turning_up = bool(close and ema20_4h and close >= ema20_4h and (rsi_4h or 50) >= (rsi_d or 50))
        confirmed_base_turn = bool(
            intraday_turning_up
            and major_shelf
            and close >= major_shelf
            and ((sma20 and close >= sma20 * 0.98) or (d.get("Perf.W") or 0) > 1.0)
        )

        if close and sma200 and sma50 and close < sma50 and (
            (close >= sma200 * 0.95 and ((perf_1m or 0) <= -5.0 or (rsi_d or 50) <= 46))
            or (close < sma200 * 0.95 and confirmed_base_turn)
        ):
            setup_type = "DISLOCATION_AT_MAJOR_SHELF"
            if confirmed_base_turn:
                setup_note = (
                    f"Dislocated below 50D SMA ({sma50}) after a {perf_1m or 0:+.1f}% 1M move, now stabilizing above "
                    f"structural support ({major_shelf}) with 4H momentum turning up (4H RSI {rsi_4h} vs Daily RSI {rsi_d}, "
                    f"above 4H EMA20 {ema20_4h}) — actionable mean-reversion call-spread window toward {sma50}."
                )
            else:
                setup_note = (
                    f"Dislocated below 50D SMA ({sma50}) after a {perf_1m or 0:+.1f}% 1M move near structural support "
                    f"({major_shelf}), but the repair is unconfirmed: the 4H chart has not turned up (4H RSI {rsi_4h} vs Daily RSI {rsi_d}; "
                    f"close {close} vs 4H EMA20 {ema20_4h}), so there is no confirmed mean-reversion window yet."
                )
        elif close and sma50 and sma30w and close >= sma30w and close >= sma50 * 0.99 and bb_width_pct is not None and bb_width_pct <= 14.0:
            setup_type = "STAGE2_VCP_VOLATILITY_SQUEEZE"
            setup_note = (
                f"Tight Stage 2 volatility contraction (Bollinger bandwidth {bb_width_pct}%) above rising 50D SMA ({sma50}) and 30W SMA ({sma30w})."
            )
        elif close and sma50 and sma30w and close >= sma30w and 0.98 <= (close / sma50) <= 1.08:
            setup_type = "STAGE2_SUPPORT_PULLBACK"
            setup_note = f"Constructive Stage 2 trend trading near 50D SMA ({sma50}) / 10W EMA ({ema10w}) support."
        elif close and sma50 and sma30w and close >= sma30w and (close / sma50) > 1.08:
            setup_type = "STAGE2_EXTENDED"
            setup_note = f"In Stage 2 uptrend, but extended above 50D SMA ({sma50}); chasing short-dated calls carries pullback risk."
        else:
            setup_type = "STAGE4_BELOW_STRUCTURAL_FLOOR"
            setup_note = f"Trading below both 50D SMA ({sma50}) and 200D/30W floor ({sma200}); trend is broken."

        out[sym] = {
            "tv_symbol": tk,
            "exchange": tk.split(":")[0],
            "company_name": d.get("description") or sym,
            "close": close,
            "change_1d_pct": _round(d.get("change")),
            "perf_1w_pct": _round(d.get("Perf.W")),
            "perf_1m_pct": perf_1m,
            "perf_3m_pct": _round(d.get("Perf.3M")),
            "rsi_1d": rsi_d,
            "rsi_4h": rsi_4h,
            "rsi_1w": rsi_w,
            "sma20": sma20,
            "sma50": sma50,
            "sma200": sma200,
            "sma30_weekly": sma30w,
            "ema10_weekly": ema10w,
            "ema20_4h": ema20_4h,
            "sma50_4h": _round(d.get("SMA50|240")),
            "atr14": _round(d.get("ATR")),
            "bb_width_pct": bb_width_pct,
            "pivot_s1": _round(d.get("Pivot.M.Classic.S1")),
            "pivot_s2": _round(d.get("Pivot.M.Classic.S2")),
            "pivot_r1": _round(d.get("Pivot.M.Classic.R1")),
            "pivot_r2": _round(d.get("Pivot.M.Classic.R2")),
            "high_52w": _round(d.get("price_52_week_high")),
            "low_52w": _round(d.get("price_52_week_low")),
            "dist_to_200d_pct": dist_to_200d_pct,
            "major_shelf": major_shelf,
            "intraday_4h_turn": intraday_turning_up,
            "setup_archetype": setup_type,
            "setup_summary": setup_note,
        }
    return out


def fetch_historical_volatility_20d(symbol: str, market: str) -> Optional[float]:
    """Compute annualized 20-day realized volatility (HV20) from daily closes."""
    yf_sym = f"{symbol}.NS" if market == "IN" else symbol
    try:
        hist = yf.Ticker(yf_sym).history(period="3mo", interval="1d")
        closes = hist["Close"].dropna().values
        if len(closes) < 22:
            return None
        log_rets = np.diff(np.log(closes[-22:]))
        hv = float(np.std(log_rets, ddof=1) * math.sqrt(252.0))
        return round(hv, 4) if math.isfinite(hv) else None
    except Exception:
        return None


def fetch_public_call_chains(symbol: str, market: str) -> Dict[str, Any]:
    """Fetch listed Call options chains for US (yfinance) or IN (NSE/yfinance)."""
    yf_sym = f"{symbol}.NS" if market == "IN" else symbol
    try:
        tk = yf.Ticker(yf_sym)
        expiries = list(tk.options or [])
        if not expiries:
            return {"optionable": False, "expiries": [], "chains": {}}
        today = dt.date.today()
        selected_exps: List[Tuple[str, int]] = []
        dated = []
        for e in expiries:
            try:
                d = (dt.date.fromisoformat(e) - today).days
                if d >= 21:
                    dated.append((e, d))
            except ValueError:
                continue
        # Pick tactical (45-120 DTE) and LEAPS (>= 250 DTE) windows
        tactical = [x for x in dated if 35 <= x[1] <= 135]
        leaps = [x for x in dated if x[1] >= 240]
        if tactical:
            selected_exps.append(min(tactical, key=lambda x: abs(x[1] - 75)))
        elif dated:
            selected_exps.append(dated[0])
        if leaps:
            best_leap = min(leaps, key=lambda x: abs(x[1] - 330))
            if best_leap not in selected_exps:
                selected_exps.append(best_leap)

        chains: Dict[str, List[Dict[str, Any]]] = {}
        for exp_str, dte in selected_exps:
            ch = tk.option_chain(exp_str).calls
            rows = []
            for _, r in ch.iterrows():
                bid = _round(r.get("bid")) or 0.0
                ask = _round(r.get("ask")) or 0.0
                last = _round(r.get("lastPrice")) or 0.0
                mid = round((bid + ask) / 2.0, 2) if (bid > 0 and ask > 0) else last
                oi_raw = r.get("openInterest")
                oi = int(oi_raw) if (oi_raw is not None and not (isinstance(oi_raw, float) and math.isnan(oi_raw))) else 0
                iv_raw = _round(r.get("impliedVolatility"), 4) or 0.0
                rows.append({
                    "contract": str(r.get("contractSymbol") or ""),
                    "expiry": exp_str,
                    "dte": dte,
                    "strike": float(r["strike"]),
                    "bid": bid,
                    "ask": ask,
                    "mid": mid,
                    "last": last,
                    "open_interest": oi,
                    "iv": iv_raw,
                    "spread_pct": round((ask - bid) / mid, 4) if (mid > 0 and ask >= bid > 0) else None,
                })
            chains[exp_str] = rows
        return {"optionable": bool(chains), "expiries": [e for e, _ in selected_exps], "chains": chains}
    except Exception:
        return {"optionable": False, "expiries": [], "chains": {}}


def open_options_for_symbol(market: str, symbol: str, options_path: Path | None = None) -> List[Dict[str, Any]]:
    path = options_path or (REPO / "data" / "options" / f"{market.upper()}.json")
    if not path.is_file():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    sym = symbol.upper()
    return [
        row for row in (data.get("positions") or [])
        if str(row.get("underlying") or row.get("ticker") or "").upper() == sym
    ]


def structure_options_setup(
    symbol: str,
    market: str,
    spot: float,
    mtf: Dict[str, Any],
    chain_data: Dict[str, Any],
    hv20: Optional[float],
    business_quality_verdict: str = "COMPOUNDER_PASS",
    target_base: Optional[float] = None,
    target_bull: Optional[float] = None,
    stop_underlying: Optional[float] = None,
    net_worth: float = 100000.0,
    lot_size: int = 100,
    open_positions: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Deterministically select & price the optimal beginner-clear Call or Bull Call Spread (or pass)."""
    cur = "₹" if market == "IN" else "$"
    multiplier = lot_size if market == "IN" else 100
    open_positions = open_positions or []

    # Audit any existing open contracts on this symbol
    open_audits = []
    today_date = dt.date.today()
    for pos in open_positions:
        exp_raw = str(pos.get("expiry_date") or "").strip()
        try:
            dte = (dt.date.fromisoformat(exp_raw) - today_date).days if exp_raw else int(pos.get("dte") or 60)
        except ValueError:
            dte = int(pos.get("dte") or 60)
        inv = pos.get("invalidation_stop_usd") or pos.get("invalidation_stop_inr")
        pnl_pct = pos.get("pnl_pct") or 0.0
        if dte < 0:
            act, why = "EXPIRED_REMOVE_FROM_LEDGER", f"Contract expired on {exp_raw} ({abs(dte)}d ago); reconcile and remove from data/options/{market}.json."
        elif business_quality_verdict == "FUNDAMENTAL_FAIL" or (isinstance(inv, (int, float)) and spot <= inv):
            act, why = "CLOSE", f"Underlying ({cur}{spot:,.2f}) breached invalidation ({cur}{inv}) or fundamentals failed."
        elif dte <= 30:
            act, why = "ROLL_OR_CLOSE", f"Only {dte} DTE left; accelerating daily theta decay requires rolling out or closing."
        elif pnl_pct >= 0.80:
            act, why = "TRIM_HALF_LOCK_GAIN", f"Position is up {pnl_pct * 100:.1f}%; harvest half to recover principal."
        else:
            act, why = "HOLD", f"{dte} DTE runway intact above invalidation floor ({cur}{inv})."
        open_audits.append({
            "contract": pos.get("contract_symbol") or pos.get("ticket_id") or symbol,
            "type": pos.get("type") or pos.get("contract_type") or "Call",
            "strike": pos.get("strike_usd") or pos.get("long_strike"),
            "expiry": pos.get("expiry_date"),
            "dte": dte,
            "contracts": pos.get("contracts", 1),
            "action": act,
            "rationale": why,
        })

    if not chain_data.get("optionable") or not chain_data.get("chains") or spot <= 0:
        return {
            "symbol": symbol,
            "market": market,
            "optionable": False,
            "options_verdict": "NOT_OPTIONABLE_OR_ILLIQUID",
            "headline": f"{symbol} has no liquid listed options chain ({'not in NSE F&O segment' if market == 'IN' else 'no liquid chain'}) — express any thesis strictly via cash equity.",
            "open_positions_audit": open_audits,
            "recommended_trade": None,
        }

    if business_quality_verdict == "FUNDAMENTAL_FAIL":
        return {
            "symbol": symbol,
            "market": market,
            "optionable": True,
            "options_verdict": "NO_OPTIONS_EDGE",
            "headline": f"Stand aside on {symbol} calls: Pass 1 fundamental audit rated business quality FUNDAMENTAL_FAIL. Never buy 'rebound' calls on impaired fundamentals.",
            "open_positions_audit": open_audits,
            "recommended_trade": None,
        }

    setup_type = mtf.get("setup_archetype") or "STAGE2_SUPPORT_PULLBACK"
    if setup_type == "STAGE4_BELOW_STRUCTURAL_FLOOR" and business_quality_verdict != "COMPOUNDER_PASS":
        return {
            "symbol": symbol,
            "market": market,
            "optionable": True,
            "options_verdict": "NO_OPTIONS_EDGE",
            "headline": f"No call setup on {symbol}: price ({cur}{spot:,.2f}) is below both 50D and 200D/30W structural floors and fundamentals do not qualify as COMPOUNDER_PASS.",
            "open_positions_audit": open_audits,
            "recommended_trade": None,
        }

    r1 = mtf.get("pivot_r1") or round(spot * 1.12, 2)
    eff_base = target_base if (isinstance(target_base, (int, float)) and target_base > spot * 1.05) else max(r1, round(spot * 1.15, 2))
    eff_bull = target_bull if (isinstance(target_bull, (int, float)) and target_bull > eff_base) else round(eff_base * 1.15, 2)
    eff_stop = stop_underlying if (isinstance(stop_underlying, (int, float)) and 0 < stop_underlying < spot) else (mtf.get("major_shelf") or round(spot * 0.92, 2))
    if eff_stop >= spot:
        eff_stop = round(spot * 0.93, 2)

    chains = chain_data["chains"]
    exp_list = sorted(chains.keys())
    tactical_exp = exp_list[0]
    leaps_exp = next((e for e in exp_list if (chains[e][0]["dte"] if chains[e] else 0) >= 240), None)

    def liquid_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        good = [
            r for r in rows
            if r["mid"] > 0 and (r["open_interest"] >= 25 or r["bid"] > 0)
            and (r["spread_pct"] is None or r["spread_pct"] <= 0.14)
        ]
        return good

    # Check ATM IV on tactical expiry
    tac_rows = liquid_rows(chains.get(tactical_exp, []))
    if not tac_rows:
        return {
            "symbol": symbol,
            "market": market,
            "optionable": False,
            "options_verdict": "NOT_OPTIONABLE_OR_ILLIQUID",
            "headline": f"{symbol} options bid-ask spreads exceed 14% or lack open interest — avoid illiquid slippage; trade equity only.",
            "open_positions_audit": open_audits,
            "recommended_trade": None,
        }

    atm_row = min(tac_rows, key=lambda r: abs(r["strike"] - spot))
    atm_iv = atm_row["iv"] if atm_row["iv"] > 0.01 else (hv20 or 0.35)
    iv_vs_hv = round(atm_iv / hv20, 2) if (hv20 and hv20 > 0.01) else 1.0
    iv_regime = "IV_ELEVATED" if iv_vs_hv > 1.15 else ("IV_CHEAP" if iv_vs_hv < 0.90 else "IV_FAIR")

    if setup_type == "STAGE2_EXTENDED" and iv_regime == "IV_ELEVATED":
        return {
            "symbol": symbol,
            "market": market,
            "optionable": True,
            "options_verdict": "WAIT_FOR_DIP_OR_IV_COOL",
            "headline": f"Wait before buying {symbol} calls: stock is extended above its 50D SMA AND implied volatility ({atm_iv * 100:.1f}%) is {iv_vs_hv:.2f}x realized HV20 ({(hv20 or 0) * 100:.1f}%).",
            "open_positions_audit": open_audits,
            "recommended_trade": None,
        }

    risk_budget_cash = max(multiplier * 1.0, round(net_worth * 0.006, 2))  # 60 bps of NAV cap

    # Decide structure:
    # - Dislocation rebound OR elevated IV OR IN market -> Bull Call Debit Spread
    # - US LEAPS available + cheap/fair IV + COMPOUNDER_PASS + Stage 2 VCP/pullback -> 0.70-delta LEAPS Call
    use_leaps = (
        market == "US"
        and leaps_exp is not None
        and iv_regime != "IV_ELEVATED"
        and business_quality_verdict == "COMPOUNDER_PASS"
        and setup_type in {"STAGE2_VCP_VOLATILITY_SQUEEZE", "STAGE2_SUPPORT_PULLBACK"}
    )

    if use_leaps and leaps_exp:
        l_rows = liquid_rows(chains[leaps_exp])
        # Target ~0.68-0.75 delta (strike ~ 0.88-0.95 * spot)
        enriched = []
        for r in l_rows:
            iv_use = r["iv"] if r["iv"] > 0.05 else atm_iv
            g = black_scholes_call_greeks(spot, r["strike"], r["dte"], iv_use)
            enriched.append({**r, **g, "iv_used": iv_use})
        cand_pool = [r for r in enriched if 0.62 <= r["delta"] <= 0.82] or enriched
        leg = min(cand_pool, key=lambda r: abs(r["delta"] - 0.70))
        cost_per_contract = round(leg["mid"] * multiplier, 2)
        contracts = max(1, int(risk_budget_cash // cost_per_contract)) if cost_per_contract <= risk_budget_cash else 1
        total_debit = round(cost_per_contract * contracts, 2)
        breakeven = round(leg["strike"] + leg["mid"], 2)

        def leap_payoff(px: float, rem_dte: int) -> Tuple[float, float, float]:
            val_sh = black_scholes_call_greeks(px, leg["strike"], max(1, rem_dte), leg["iv_used"])["bs_price"] if rem_dte > 5 else max(0.0, px - leg["strike"])
            cv = round(val_sh * multiplier * contracts, 2)
            pnl = round(cv - total_debit, 2)
            pct = round((pnl / total_debit) * 100.0, 1) if total_debit > 0 else 0.0
            return cv, pnl, pct

        half_dte = max(30, leg["dte"] // 2)
        scenarios = []
        for name, px, d_rem in (
            (f"Bear / Stop Hit ({cur}{eff_stop:,.2f})", eff_stop, max(60, leg["dte"] - 45)),
            (f"Flat in 60 Days ({cur}{spot:,.2f})", spot, max(30, leg["dte"] - 60)),
            (f"Base Target ({cur}{eff_base:,.2f})", eff_base, half_dte),
            (f"Bull Target ({cur}{eff_bull:,.2f})", eff_bull, half_dte),
        ):
            cv, pnl, pct = leap_payoff(px, d_rem)
            eq_pct = round(((px / spot) - 1.0) * 100.0, 1)
            scenarios.append({"scenario": name, "stock_price": px, "stock_move_pct": eq_pct,
                              "contract_value": cv, "net_pnl": pnl, "return_on_risk_pct": pct})

        return {
            "symbol": symbol,
            "market": market,
            "optionable": True,
            "options_verdict": "LONG_CALL_LEAPS",
            "iv_regime": iv_regime,
            "atm_iv_pct": round(atm_iv * 100.0, 1),
            "hv20_pct": round(hv20 * 100.0, 1) if hv20 else None,
            "open_positions_audit": open_audits,
            "headline": (
                f"Buy {contracts}x {symbol} {leg['expiry']} {cur}{leg['strike']:g} LEAPS Call ({leg['dte']} DTE, {leg['delta']:.2f} Delta) "
                f"near {cur}{leg['mid']:.2f}/sh ({cur}{total_debit:,.2f} max possible loss)."
            ),
            "recommended_trade": {
                "structure": "Long ITM/Near-ATM LEAPS Call (Stock-Replacement Convexity)",
                "expiry": leg["expiry"],
                "dte": leg["dte"],
                "legs": [{"side": "BUY", "type": "CALL", "strike": leg["strike"], "mid": leg["mid"], "bid": leg["bid"], "ask": leg["ask"], "open_interest": leg["open_interest"]}],
                "contracts": contracts,
                "multiplier": multiplier,
                "net_debit_per_share": leg["mid"],
                "max_loss_total": total_debit,
                "max_loss_nav_bps": round((total_debit / net_worth) * 10000.0, 1) if net_worth > 0 else None,
                "max_profit_total": "Uncapped upside",
                "breakeven_at_expiry": breakeven,
                "breakeven_move_pct": round(((breakeven / spot) - 1.0) * 100.0, 2),
                "net_delta_dollars_per_1_move": round(leg["delta"] * multiplier * contracts, 2),
                "daily_theta_dollars": round(leg["theta_per_day"] * multiplier * contracts, 2),
                "underlying_stop_trigger": eff_stop,
                "profit_taking_rule": f"Trim half at +75%–100% contract gain or when {symbol} reaches {cur}{eff_base:,.2f}; exit early on a weekly close below {cur}{eff_stop:,.2f}.",
                "scenarios": scenarios,
                "beginner_explainer": [
                    f"Why LEAPS instead of a short-dated call: With {leg['dte']} days until {leg['expiry']} and {leg['delta']:.2f} delta, this option behaves ~{int(leg['delta']*100)}% like owning {contracts * multiplier} shares for a fraction of the cash, while losing only {cur}{abs(leg['theta_per_day'] * multiplier * contracts):.2f}/day to time decay.",
                    f"Worst-case wallet risk: You pay {cur}{leg['mid']:.2f} x {multiplier} shares x {contracts} = {cur}{total_debit:,.2f} upfront. Even if {symbol} crashed 50% overnight, you cannot lose more than {cur}{total_debit:,.2f}.",
                    f"Volatility check: Implied Volatility is {atm_iv * 100:.1f}% vs. 20-day actual stock volatility of {(hv20 or atm_iv) * 100:.1f}% ({iv_regime.replace('_', ' ')}), so you are not overpaying panic premiums.",
                ],
            },
        }

    # Otherwise build a defined-risk Bull Call Debit Spread on tactical expiry
    enriched_tac = []
    for r in tac_rows:
        iv_use = r["iv"] if r["iv"] > 0.05 else atm_iv
        g = black_scholes_call_greeks(spot, r["strike"], r["dte"], iv_use)
        enriched_tac.append({**r, **g, "iv_used": iv_use})

    long_pool = [r for r in enriched_tac if 0.50 <= r["delta"] <= 0.68] or enriched_tac
    long_leg = min(long_pool, key=lambda r: abs(r["delta"] - 0.58))
    short_pool = [r for r in enriched_tac if r["strike"] > long_leg["strike"] * 1.04 and r["mid"] > 0.05]
    if not short_pool:
        return {
            "symbol": symbol,
            "market": market,
            "optionable": True,
            "options_verdict": "NO_OPTIONS_EDGE",
            "headline": f"No clean call-spread strikes available above {cur}{long_leg['strike']:g} on {tactical_exp}; stand aside.",
            "open_positions_audit": open_audits,
            "recommended_trade": None,
        }
    short_leg = min(short_pool, key=lambda r: abs(r["strike"] - eff_base))
    net_debit_sh = round(max(0.05, long_leg["mid"] - short_leg["mid"]), 2)
    width_sh = round(short_leg["strike"] - long_leg["strike"], 2)
    max_profit_sh = round(width_sh - net_debit_sh, 2)
    rr_ratio = round(max_profit_sh / net_debit_sh, 2) if net_debit_sh > 0 else 0.0

    if rr_ratio < 1.25:
        return {
            "symbol": symbol,
            "market": market,
            "optionable": True,
            "options_verdict": "NO_OPTIONS_EDGE",
            "headline": f"Stand aside on {symbol} call spreads: {cur}{long_leg['strike']:g}/{cur}{short_leg['strike']:g} spread costs {cur}{net_debit_sh:.2f} for only {cur}{max_profit_sh:.2f} max gain ({rr_ratio:.2f}:1 R:R < 1.25:1 minimum).",
            "open_positions_audit": open_audits,
            "recommended_trade": None,
        }

    debit_per_spread = round(net_debit_sh * multiplier, 2)
    contracts = max(1, int(risk_budget_cash // debit_per_spread)) if debit_per_spread <= risk_budget_cash else 1
    total_debit = round(debit_per_spread * contracts, 2)
    total_max_profit = round(max_profit_sh * multiplier * contracts, 2)
    breakeven = round(long_leg["strike"] + net_debit_sh, 2)
    net_delta = round((long_leg["delta"] - short_leg["delta"]) * multiplier * contracts, 2)
    net_theta = round((long_leg["theta_per_day"] - short_leg["theta_per_day"]) * multiplier * contracts, 2)

    scenarios = []
    for name, px in (
        (f"At or Below {cur}{long_leg['strike']:g} at Expiry", min(eff_stop, long_leg["strike"])),
        (f"At Breakeven ({cur}{breakeven:,.2f})", breakeven),
        (f"At Short Cap / Base Target ({cur}{short_leg['strike']:g})", short_leg["strike"]),
        (f"Bull Overshoot ({cur}{eff_bull:,.2f})", max(eff_bull, short_leg["strike"] * 1.05)),
    ):
        intrinsic_sh = min(width_sh, max(0.0, px - long_leg["strike"]))
        cv = round(intrinsic_sh * multiplier * contracts, 2)
        pnl = round(cv - total_debit, 2)
        pct = round((pnl / total_debit) * 100.0, 1) if total_debit > 0 else 0.0
        eq_pct = round(((px / spot) - 1.0) * 100.0, 1)
        scenarios.append({"scenario": name, "stock_price": round(px, 2), "stock_move_pct": eq_pct,
                          "contract_value": cv, "net_pnl": pnl, "return_on_risk_pct": pct})

    is_stage4_conditional = (setup_type == "STAGE4_BELOW_STRUCTURAL_FLOOR")
    final_verdict = "WAIT_FOR_SUPPORT_OR_BASE" if is_stage4_conditional else "BULL_CALL_DEBIT_SPREAD"
    if is_stage4_conditional:
        why_lens = (
            f"{symbol} is in an active Stage 4 correction below its 50D and 200D averages. "
            f"While buying calls right now at CMP ({cur}{spot:,.2f}) is a trap due to accelerating theta decay on an unconfirmed knife-drop, "
            f"this defined-risk Bull Call Spread ({cur}{long_leg['strike']:g}/{cur}{short_leg['strike']:g}) is structured to be deployed once "
            f"{symbol} tests its major {cur}{eff_stop:,.2f} support shelf and stabilizes. "
            f"Selling the upper {cur}{short_leg['strike']:g} call funds your entry, reduces daily theta decay by over 60%, and caps your worst-case loss at {cur}{total_debit:,.2f}."
        )
        final_headline = (
            f"Stand aside at CMP ({cur}{spot:,.2f}): stock is in an active Stage 4 correction below 50D/200D averages. "
            f"If {symbol} tests its major {cur}{eff_stop:,.2f} support shelf and stabilizes, deploy this conditional defined-risk Call Spread "
            f"({tactical_exp} {cur}{long_leg['strike']:g}/{cur}{short_leg['strike']:g}) at {cur}{net_debit_sh:.2f} debit toward {cur}{eff_base:,.2f} "
            f"({cur}{total_debit:,.2f} max loss -> {cur}{total_max_profit:,.2f} max profit, {rr_ratio:.2f}:1 R:R)."
        )
    elif setup_type == "DISLOCATION_AT_MAJOR_SHELF":
        why_lens = (
            f"{symbol} pulled back into its major {cur}{mtf.get('major_shelf') or eff_stop:,.2f} support shelf while Pass 1 confirmed {business_quality_verdict} fundamentals — "
            "even though Stage 2 equity rules wait for trend repair, a defined-risk Bull Call Spread captures a rebound with strictly capped downside."
        )
        final_headline = (
            f"Buy {contracts}x {symbol} {tactical_exp} {cur}{long_leg['strike']:g}/{cur}{short_leg['strike']:g} Bull Call Spread "
            f"({long_leg['dte']} DTE) at {cur}{net_debit_sh:.2f} net debit ({cur}{total_debit:,.2f} max loss -> {cur}{total_max_profit:,.2f} max profit, {rr_ratio:.2f}:1 R:R)."
        )
    else:
        why_lens = f"Selling the upper {cur}{short_leg['strike']:g} call collects {cur}{short_leg['mid']:.2f}/sh upfront, lowering your breakeven to {cur}{breakeven:,.2f} and protecting you against post-news volatility crush."
        final_headline = (
            f"Buy {contracts}x {symbol} {tactical_exp} {cur}{long_leg['strike']:g}/{cur}{short_leg['strike']:g} Bull Call Spread "
            f"({long_leg['dte']} DTE) at {cur}{net_debit_sh:.2f} net debit ({cur}{total_debit:,.2f} max loss -> {cur}{total_max_profit:,.2f} max profit, {rr_ratio:.2f}:1 R:R)."
        )

    return {
        "symbol": symbol,
        "market": market,
        "optionable": True,
        "options_verdict": final_verdict,
        "iv_regime": iv_regime,
        "atm_iv_pct": round(atm_iv * 100.0, 1),
        "hv20_pct": round(hv20 * 100.0, 1) if hv20 else None,
        "open_positions_audit": open_audits,
        "headline": final_headline,
        "recommended_trade": {
            "structure": "Bull Call Debit Spread (Defined-Risk Rebound / Catalyst Structure)",
            "expiry": tactical_exp,
            "dte": long_leg["dte"],
            "legs": [
                {"side": "BUY", "type": "CALL", "strike": long_leg["strike"], "mid": long_leg["mid"], "bid": long_leg["bid"], "ask": long_leg["ask"], "open_interest": long_leg["open_interest"]},
                {"side": "SELL", "type": "CALL", "strike": short_leg["strike"], "mid": short_leg["mid"], "bid": short_leg["bid"], "ask": short_leg["ask"], "open_interest": short_leg["open_interest"]},
            ],
            "contracts": contracts,
            "multiplier": multiplier,
            "net_debit_per_share": net_debit_sh,
            "max_loss_total": total_debit,
            "max_loss_nav_bps": round((total_debit / net_worth) * 10000.0, 1) if net_worth > 0 else None,
            "max_profit_total": f"{cur}{total_max_profit:,.2f} ({rr_ratio:.2f}:1 reward-to-risk)",
            "breakeven_at_expiry": breakeven,
            "breakeven_move_pct": round(((breakeven / spot) - 1.0) * 100.0, 2),
            "net_delta_dollars_per_1_move": net_delta,
            "daily_theta_dollars": net_theta,
            "underlying_stop_trigger": eff_stop,
            "profit_taking_rule": f"Close spread at 65%–75% of max profit ({cur}{round(total_max_profit * 0.70, 2):,.2f} gain) or exit early if {symbol} closes below {cur}{eff_stop:,.2f}.",
            "scenarios": scenarios,
            "beginner_explainer": [
                f"Why this spread works differently from buying shares: {why_lens}",
                f"Exact wallet math (1 contract = {multiplier} shares): You buy the {cur}{long_leg['strike']:g} Call for {cur}{long_leg['mid']:.2f} and simultaneously sell the {cur}{short_leg['strike']:g} Call for {cur}{short_leg['mid']:.2f}, paying {cur}{net_debit_sh:.2f}/sh net ({cur}{total_debit:,.2f} total for {contracts} spread(s)). That {cur}{total_debit:,.2f} is the absolute maximum you can lose.",
                f"Breakeven & profit ceiling: At expiry ({tactical_exp}), you start making money above {cur}{breakeven:,.2f} ({((breakeven / spot) - 1.0) * 100:+.1f}% from {cur}{spot:,.2f}). Anywhere at or above {cur}{short_leg['strike']:g}, your {cur}{total_debit:,.2f} turns into {cur}{total_debit + total_max_profit:,.2f} (+{cur}{total_max_profit:,.2f} net profit).",
                f"Speed & time decay in plain English: Today, each {cur}1 move up in {symbol} adds ~{cur}{net_delta:,.2f} to your spread (Net Delta), while sitting flat costs ~{cur}{abs(net_theta):,.2f}/day in time decay (Net Theta) — much lower than an unhedged call because the sold {cur}{short_leg['strike']:g} call decays in your favor.",
            ],
        },
    }


def render_options_section_html(plan: Dict[str, Any], mtf: Optional[Dict[str, Any]] = None, browser_info: Optional[Dict[str, Any]] = None) -> str:
    """Render a beginner-clear, Research Desk compliant HTML section for an options setup."""
    sym = html.escape(str(plan.get("symbol") or ""))
    mkt = str(plan.get("market") or "US").upper()
    cur = "₹" if mkt == "IN" else "$"
    verdict = str(plan.get("options_verdict") or "NO_OPTIONS_EDGE")
    v_cls = (
        "verdict-keep" if verdict in {"LONG_CALL_LEAPS", "BULL_CALL_DEBIT_SPREAD"}
        else "verdict-watch"
    )
    rh_note = ((browser_info or {}).get("robinhood") or {}).get("note") or "Public options chain snapshot."
    if mkt == "IN":
        rh_note = "Public NSE data only; the Robinhood account feed does not apply to India symbols."
    tv_note = (mtf or {}).get("setup_summary") or "Multi-timeframe structure evaluated against daily/weekly moving averages."

    parts = [
        f'<section class="chapter" id="options-overlay" data-options-verdict="{html.escape(verdict)}">',
        f"<h2>Options &amp; Call-Convexity Playbook ({sym})</h2>",
        f'<p><span class="verdict {v_cls}">{html.escape(verdict.replace("_", " "))}</span> &mdash; '
        f'<strong>{html.escape(str(plan.get("headline") or ""))}</strong></p>',
        f'<p><strong>Multi-Timeframe Chart Context (1W / 1D / 4H):</strong> {html.escape(tv_note)} '
        f'<em>Account / Chain Feed: {html.escape(rh_note)}</em></p>',
    ]
    raw_tv_symbol = str((mtf or {}).get("tv_symbol") or f"{'NSE' if mkt == 'IN' else 'NYSE'}:{sym}").upper()
    symbol_parts = raw_tv_symbol.split(":", 1)
    exchange = re.sub(r"[^A-Z0-9]", "", symbol_parts[0]) if len(symbol_parts) == 2 else ("NSE" if mkt == "IN" else "NYSE")
    ticker = re.sub(r"[^A-Z0-9._-]", "", symbol_parts[-1])
    chart_symbol = f"{exchange}:{ticker}"
    chart_id = f"tradingview_{re.sub(r'[^a-z0-9]+', '_', ticker.lower())}_options_chart"
    parts.extend([
        f'<p><strong>Interactive TradingView chart:</strong> public live chart for {html.escape(chart_symbol)}. '
        "Use its on-chart controls for visual context; the report's decision remains tied to the verified session cutoff.</p>",
        '<div class="tradingview-widget-container" style="height: 520px; width: 100%; margin: 1.25rem 0;">'
        f'<div id="{chart_id}" role="img" aria-label="Interactive TradingView daily chart for {html.escape(chart_symbol)}" style="height: 100%; width: 100%;"></div>'
        '<script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>'
        '<script type="text/javascript">'
        f'new TradingView.widget({{"autosize":true,"symbol":{json.dumps(chart_symbol)},"interval":"D",'
        '"timezone":"Etc/UTC","theme":"light","style":"1","locale":"en",'
        '"toolbar_bg":"#f4f6f8","enable_publishing":false,"hide_top_toolbar":false,'
        f'"allow_symbol_change":true,"container_id":{json.dumps(chart_id)}}});'
        '</script></div>',
    ])

    # Existing open options audit if present
    open_audits = plan.get("open_positions_audit") or []
    if open_audits:
        o_rows = "".join(
            f"<tr><td>{html.escape(str(a['contract']))}</td><td>{html.escape(str(a['type']))}</td>"
            f"<td>{html.escape(str(a['strike']))}</td><td>{html.escape(str(a['expiry']))} ({a['dte']}d)</td>"
            f"<td>{a['contracts']}</td><td><strong>{html.escape(str(a['action']))}</strong></td>"
            f"<td>{html.escape(str(a['rationale']))}</td></tr>"
            for a in open_audits
        )
        parts.append(
            '<div class="table-wrap"><table class="wikitable">'
            f"<caption>Active Open Options Audit for {sym}</caption>"
            "<thead><tr><th>Contract</th><th>Structure</th><th>Strike</th><th>Expiry (DTE)</th><th>Qty</th><th>Action</th><th>Rule &amp; Rationale</th></tr></thead>"
            f"<tbody>{o_rows}</tbody></table></div>"
            "<p>Open option contracts above are audited against underlying structural support and remaining DTE theta runway.</p>"
        )

    trade = plan.get("recommended_trade")
    if not trade:
        parts.append("</section>")
        return "\n".join(parts)

    explainer_ps = "".join(f"<p>{html.escape(line)}</p>" for line in (trade.get("beginner_explainer") or []))
    parts.append(
        '<div class="callout callout-rule">\n'
        '<p class="callout-title">Beginner Guide: How This Call Trade Works in Plain Dollars</p>\n'
        f"{explainer_ps}\n</div>"
    )

    leg_desc = " + ".join(
        f"{l['side']} {l['expiry'] if 'expiry' in l else trade['expiry']} {cur}{l['strike']:g} {l['type']} @ {cur}{l['mid']:.2f} mid (bid {cur}{l['bid']:.2f} / ask {cur}{l['ask']:.2f}, OI {l['open_interest']})"
        for l in trade.get("legs", [])
    )
    spec_rows = [
        ("Strategy Structure", trade["structure"], "Matches volatility regime and chart support shelf."),
        ("Exact Option Leg(s)", leg_desc, "Always use limit orders near the mid-price; never place market orders on options."),
        ("Contracts & Multiplier", f"{trade['contracts']} contract(s) x {trade['multiplier']} shares", f"Controls {trade['contracts'] * trade['multiplier']} underlying shares."),
        ("Total Upfront Cost (Max Possible Loss)", f"{cur}{trade['max_loss_total']:,.2f} ({trade.get('max_loss_nav_bps', 'N/A')} bps of NAV)", "100% of your downside is capped at the cash paid upfront."),
        ("Breakeven Stock Price at Expiry", f"{cur}{trade['breakeven_at_expiry']:,.2f} ({trade['breakeven_move_pct']:+.2f}% vs CMP)", f"Stock price required by {trade['expiry']} to recover full upfront cost."),
        ("Maximum Profit Potential", str(trade["max_profit_total"]), "Net profit after subtracting upfront debit."),
        ("Net Delta & Daily Time Decay (Theta)", f"{cur}{trade['net_delta_dollars_per_1_move']:+,.2f} per {cur}1 move | {cur}{trade['daily_theta_dollars']:+,.2f}/day decay", "Initial sensitivity to a 1-unit stock move vs. daily time decay."),
        ("Profit-Taking & Early Stop Rule", trade["profit_taking_rule"], "Advisory exit discipline to protect premium before late-stage theta accelerates."),
    ]
    spec_tr = "".join(
        f"<tr><td><strong>{html.escape(k)}</strong></td><td>{html.escape(str(v))}</td><td>{html.escape(n)}</td></tr>"
        for k, v, n in spec_rows
    )
    parts.append(
        '<div class="table-wrap"><table class="wikitable">'
        f"<caption>Structured Call Setup &amp; Risk-Capped Wallet Math for {sym}</caption>"
        "<thead><tr><th>Option Parameter</th><th>Exact Value</th><th>What This Means for a Beginner</th></tr></thead>"
        f"<tbody>{spec_tr}</tbody></table></div>"
        f"<p>Every figure above is computed deterministically from live option-chain mid-prices ({trade['expiry']}, {trade['dte']} DTE) and capped within our portfolio risk budget.</p>"
    )

    sc_tr = "".join(
        f"<tr><td>{html.escape(s['scenario'])}</td><td>{cur}{s['stock_price']:,.2f} ({s['stock_move_pct']:+.1f}%)</td>"
        f"<td>{cur}{s['contract_value']:,.2f}</td><td>{cur}{s['net_pnl']:+,.2f}</td>"
        f"<td><strong>{s['return_on_risk_pct']:+.1f}%</strong></td></tr>"
        for s in (trade.get("scenarios") or [])
    )
    parts.append(
        '<div class="table-wrap"><table class="wikitable">'
        f"<caption>What Happens to Your {cur}{trade['max_loss_total']:,.2f} Across Stock Scenarios ({sym})</caption>"
        "<thead><tr><th>Scenario</th><th>Underlying Stock Price (% Move)</th><th>Option Value</th><th>Your Net Profit / Loss</th><th>Return on Risk (%)</th></tr></thead>"
        f"<tbody>{sc_tr}</tbody></table></div>"
        "<p>Compare the underlying percentage move in column 2 against your option return in column 5: defined-risk call structures amplify upside above breakeven while strictly capping worst-case loss.</p>"
    )
    parts.append("</section>")
    return "\n".join(parts)


def build_symbol_options_package(
    symbol: str,
    market: str,
    use_browser: bool = True,
    net_worth: float = 100000.0,
    business_quality_override: str = "",
    target_base: Optional[float] = None,
    target_bull: Optional[float] = None,
    stop_underlying: Optional[float] = None,
) -> Dict[str, Any]:
    sym = symbol.upper()
    mkt = market.upper()
    bq = business_quality_override
    canon_dir = REPO / "data" / "dossiers" / mkt / sym
    if not bq and (canon_dir / "business_quality.json").is_file():
        bq = json.loads((canon_dir / "business_quality.json").read_text(encoding="utf-8")).get("business_quality_verdict") or ""
    if (canon_dir / "spine.json").is_file():
        sp = json.loads((canon_dir / "spine.json").read_text(encoding="utf-8"))
        bq = bq or sp.get("business_quality_verdict") or ("FUNDAMENTAL_FAIL" if sp.get("verdict") == "REJECTED" else "COMPOUNDER_PASS")
        target_base = target_base if target_base is not None else sp.get("target_base")
        target_bull = target_bull if target_bull is not None else sp.get("target_bull")
        stop_underlying = stop_underlying if stop_underlying is not None else sp.get("stop_loss")
    bq = bq or "COMPOUNDER_PASS"

    browser_info = probe_browser_sessions(sym, mkt, enabled=use_browser)
    mtf = fetch_multitimeframe_chart(mkt, [sym]).get(sym, {})
    spot = float(mtf.get("close") or 0.0)
    hv20 = fetch_historical_volatility_20d(sym, mkt)
    chains = fetch_public_call_chains(sym, mkt)
    open_pos = open_options_for_symbol(mkt, sym)
    lot = int(open_pos[0].get("lot_size") or 100) if (mkt == "IN" and open_pos) else (250 if mkt == "IN" else 100)

    plan = structure_options_setup(
        symbol=sym,
        market=mkt,
        spot=spot,
        mtf=mtf,
        chain_data=chains,
        hv20=hv20,
        business_quality_verdict=bq,
        target_base=target_base,
        target_bull=target_bull,
        stop_underlying=stop_underlying,
        net_worth=net_worth,
        lot_size=lot,
        open_positions=open_pos,
    )
    return {
        "symbol": sym,
        "market": mkt,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "business_quality_verdict": bq,
        "browser_sessions": browser_info,
        "multitimeframe_chart": mtf,
        "options_plan": plan,
        "rendered_html": render_options_section_html(plan, mtf, browser_info),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--market", choices=["IN", "US"], required=True)
    ap.add_argument("--symbols", nargs="*", default=[], help="Explicit symbols to evaluate")
    ap.add_argument("--from-options", action="store_true", help="Include all underlyings in data/options/<MKT>.json")
    ap.add_argument("--from-shortlist", action="store_true", help="Include active shortlist symbols")
    ap.add_argument("--net-worth", type=float, default=100000.0, help="Portfolio NAV for bps risk sizing")
    ap.add_argument("--no-browser", action="store_true", help="Skip macOS Chrome Robinhood/TradingView session check")
    ap.add_argument("--patch-dossier-specs", action="store_true", help="Save options_plan.json into data/dossiers/<MKT>/<SYM>/ when present")
    ap.add_argument("--out", required=True, help="Output JSON path")
    args = ap.parse_args()

    mkt = args.market.upper()
    syms = list(dict.fromkeys([s.upper() for s in args.symbols]))
    if args.from_options:
        opt_p = REPO / "data" / "options" / f"{mkt}.json"
        if opt_p.is_file():
            for row in json.loads(opt_p.read_text(encoding="utf-8")).get("positions", []):
                u = (row.get("underlying") or row.get("ticker") or "").upper()
                if u and u not in syms:
                    syms.append(u)
    if args.from_shortlist:
        sl_p = REPO / "data" / "shortlist" / f"{mkt}.json"
        if sl_p.is_file():
            for row in json.loads(sl_p.read_text(encoding="utf-8")).get("active", []):
                u = (row.get("symbol") or "").upper()
                if u and u not in syms:
                    syms.append(u)
    if not syms:
        raise SystemExit("Specify --symbols, --from-options, or --from-shortlist")

    packages: Dict[str, Any] = {}
    for s in syms:
        pkg = build_symbol_options_package(s, mkt, use_browser=not args.no_browser, net_worth=args.net_worth)
        packages[s] = pkg
        if args.patch_dossier_specs:
            cdir = REPO / "data" / "dossiers" / mkt / s
            if cdir.is_dir():
                (cdir / "options_plan.json").write_text(
                    json.dumps(pkg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
                )

    out_obj = {
        "market": mkt,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "symbol_count": len(packages),
        "packages": packages,
    }
    out_p = Path(args.out)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    out_p.write_text(json.dumps(out_obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[+] Wrote options & multi-timeframe chart snapshot for {len(packages)} {mkt} symbol(s) to {args.out}")


if __name__ == "__main__":
    main()
