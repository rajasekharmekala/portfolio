#!/usr/bin/env python3
"""
Facts ledger builder: the single source of truth for every price, moving average,
RSI/ATR, volume multiple, Weinstein stage and regime label used by ALL report
sections (market intelligence + portfolio audit) for one market and one session.

Usage:
  python3 scripts/market_facts.py --market US --date 2026-09-28 --screen sp1500 --run-dir <RUN_DIR>
  python3 scripts/market_facts.py --market IN --date 2026-10-08 --screen nifty500 --extra RELIANCE,TCS --run-dir <RUN_DIR>
  python3 scripts/market_facts.py --market US --show NVDA,VRT --out <RUN_DIR>/cache/facts_US_2026-09-28.json
  python3 scripts/market_facts.py --market US --check-inputs [--run-dir <RUN_DIR>]   # validate sources only, no network

Output: <RUN_DIR>/cache/facts_<MKT>_<YYYY-MM-DD>.json. Every run writes into its own run
directory; nothing is read from a previous run. --date is required and is a hard requirement:
if the benchmark's last bar is not on that date, the build exits non-zero (no silent relabel).

Also written per run: cache/factpack_<MKT>_<date>.json (the compact subset that report sections are drafted
from; the full ledger is too large to give every section) and manifest.json (inputs with SHA-256, and per-symbol
freshness for every holding, shortlist and watchlist name). A holding that is not current on the session date
aborts the build unless --allow-stale-holdings is given. Input sources live in .agents/config/portfolios.json.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import datetime as dt
import hashlib
import io
import json
import math
import os
import re
import sys
import urllib.request

import pandas as pd
import yfinance as yf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG = os.path.join(ROOT, "scripts", "config")  # version-controlled config only (aliases), never run output
PORTFOLIOS_FILE = os.path.join(ROOT, ".agents", "config", "portfolios.json")  # input sources, see README in workflows
INPUTS = []  # set by load_sources(): one record per declared source
META = {}  # symbol -> metadata columns from the metadata workbook
POSITIONS = []  # per-account snapshots from md_positions sources
OPTIONS_BOOK = []  # option rows with their current market value (options sources)
OPTION_RE = re.compile(r"^[A-Z]{1,6}\d{6}[CP]\d{8}$")
TICKER_RE = re.compile(r"^[A-Z0-9][A-Z0-9&\-\.]{0,19}$")
# Zerodha symbol -> Yahoo symbol where they differ; extend via scripts/config/aliases.json
ALIASES = {"IN": {"KALPATPOWR": "KPIL.NS", "VINATIORG": "VINATIORGA.NS", "HBLPOWER": "HBLENGINE.NS"}, "US": {}}

BENCH = {
    "US": {
        "indices": {"S&P 500": "^GSPC", "Nasdaq-100": "^NDX", "Russell 2000": "^RUT",
                    "Dow Jones": "^DJI", "VIX": "^VIX", "US 10Y (x10)": "^TNX"},
        "etfs": ["SPY", "QQQ", "IWM", "DIA", "SOXX", "IGV", "XBI"],
        "sectors": {"Communication Services": "XLC", "Consumer Discretionary": "XLY",
                    "Consumer Staples": "XLP", "Energy": "XLE", "Financials": "XLF",
                    "Health Care": "XLV", "Industrials": "XLI", "Information Technology": "XLK",
                    "Materials": "XLB", "Real Estate": "XLRE", "Utilities": "XLU"},
        "primary": "^GSPC",
    },
    "IN": {
        "indices": {"Nifty 50": "^NSEI", "Bank Nifty": "^NSEBANK", "Sensex": "^BSESN",
                    "India VIX": "^INDIAVIX", "Nifty Midcap 150": "NIFTYMIDCAP150.NS",
                    "Nifty Smallcap 250": "NIFTYSMLCAP250.NS", "Nifty 500": "^CRSLDX"},
        "etfs": [],
        "sectors": {"IT": "^CNXIT", "Pharma": "^CNXPHARMA", "Auto": "^CNXAUTO", "FMCG": "^CNXFMCG",
                    "Metal": "^CNXMETAL", "Realty": "^CNXREALTY", "Energy": "^CNXENERGY",
                    "Infra": "^CNXINFRA", "PSU Bank": "^CNXPSUBANK", "Media": "^CNXMEDIA",
                    "Financial Services": "^CNXFIN"},
        "primary": "^NSEI",
    },
}

# Data Yahoo cannot supply: the agent fills these with the duck-duck-go MCP (search + fetch_content).
# Templates: {d1}=28 Sep 2026  {d2}=September 28 2026  {d3}=2026-09-28  {d4}=28092026
RESEARCH_NEEDS = {
    "IN": [
        {"key": "fii_dii_cash", "what": "FII/FPI and DII net cash-market flow (Rs Cr) for the session",
         "queries": ["FII DII provisional data {d1} net sold bought crore NSE", "FPI DII net {d2} cash segment moneycontrol"],
         "sources": ["nseindia.com", "moneycontrol.com", "economictimes.indiatimes.com", "business-standard.com"],
         "direct_urls": ["https://www.nseindia.com/api/fiidiiTradeReact"]},
        {"key": "fii_index_futures", "what": "FII index-futures long/short OI and ratio",
         "queries": ["FII index futures long short ratio participant wise open interest {d1}"],
         "sources": ["nsearchives.nseindia.com", "trendlyne.com", "sensibull.com"],
         "direct_urls": ["https://nsearchives.nseindia.com/content/nsccl/fao_participant_oi_{d4}.csv"]},
        {"key": "nifty_options", "what": "Nifty/BankNifty PCR, max pain, highest call/put OI strikes",
         "queries": ["Nifty option chain max pain PCR highest open interest strike {d1}", "Nifty PCR {d2} call put OI support resistance"],
         "sources": ["nseindia.com", "sensibull.com", "niftytrader.in", "trendlyne.com"], "direct_urls": []},
        {"key": "bulk_block_deals", "what": "Bulk/block deals over Rs 10 Cr with buyer/seller",
         "queries": ["bulk deals block deals {d1} NSE BSE buyer seller crore"],
         "sources": ["nseindia.com", "bseindia.com", "moneycontrol.com"],
         "direct_urls": ["https://nsearchives.nseindia.com/content/equities/bulk.csv", "https://nsearchives.nseindia.com/content/equities/block.csv"]},
        {"key": "delivery_pct", "what": "Delivery percentage for Bull/Bear list names",
         "queries": ["NSE security-wise delivery position {d1}"],
         "sources": ["nsearchives.nseindia.com"],
         "direct_urls": ["https://nsearchives.nseindia.com/products/content/sec_bhavdata_full_{d4}.csv"]},
        {"key": "results_calendar", "what": "Board-meeting/results dates for holdings and Top-3 setups (next 14 days)",
         "queries": ["{symbol} board meeting date quarterly results {d2}"], "sources": ["screener.in", "bseindia.com", "nseindia.com"],
         "per": "holding"},
        {"key": "promoter_pledge", "what": "Promoter holding/pledge and SAST changes",
         "queries": ["{symbol} promoter pledge shareholding pattern latest"], "sources": ["screener.in", "trendlyne.com"], "per": "holding"},
        {"key": "catalyst_news", "what": "Company-specific catalyst behind each Top-3 setup and each EXIT/TRIM",
         "queries": ["{symbol} news order win guidance {d2}"], "sources": ["reuters.com", "business-standard.com", "screener.in"], "per": "top"},
    ],
    "US": [
        {"key": "cboe_put_call", "what": "CBOE total / equity / index put-call ratio",
         "queries": ["CBOE total put call ratio {d2}", "CBOE equity put call ratio {d3}"],
         "sources": ["cboe.com", "ycharts.com", "barchart.com", "marketchameleon.com"], "direct_urls": []},
        {"key": "index_option_walls", "what": "SPY/QQQ/IWM call wall, put wall, gamma flip (volatility trigger)",
         "queries": ["SPY gamma exposure call wall put wall {d2}", "SPX GEX gamma flip level {d2}"],
         "sources": ["spotgamma.com", "squeezemetrics.com", "barchart.com", "marketchameleon.com"],
         "note": "Prefer computing walls yourself: yfinance Ticker(sym).option_chain(expiry) gives OI by strike; wall = strike with max call/put OI."},
        {"key": "form4_cluster_buys", "what": "SEC Form 4 open-market cluster buys (2+ insiders, last 14 days, > $250k)",
         "queries": ["openinsider cluster buys {d3}", "insider cluster buying last week Form 4 {d2}"],
         "sources": ["openinsider.com", "sec.gov", "secform4.com"],
         "direct_urls": ["https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=4"]},
        {"key": "earnings_calendar", "what": "Next earnings date for holdings and Top-3 setups",
         "queries": ["{symbol} next earnings date {d2}"], "sources": ["yfinance Ticker.calendar first", "investor relations page", "nasdaq.com"], "per": "holding"},
        {"key": "filing_gates", "what": "ROIC, 3Y CFO/NI, net debt/EBITDA for greenfield candidates",
         "queries": ["{symbol} 10-K free cash flow operating cash flow net income net debt EBITDA"],
         "sources": ["data.sec.gov companyfacts", "finviz.com", "stockanalysis.com"], "per": "shortlist"},
        {"key": "catalyst_news", "what": "Company-specific catalyst behind each Top-3 setup and each EXIT/TRIM",
         "queries": ["{symbol} news guidance announcement {d2}"], "sources": ["reuters.com", "company IR page", "sec.gov 8-K"], "per": "top"},
    ],
}


def render_research(market: str, asof: str, roles: dict) -> list:
    d = dt.date.fromisoformat(asof)
    fmt = {"d1": d.strftime("%d %b %Y"), "d2": d.strftime("%B %d %Y").replace(" 0", " "),
           "d3": d.isoformat(), "d4": d.strftime("%d%m%Y")}
    out = []
    for item in RESEARCH_NEEDS[market]:
        it = {k: v for k, v in item.items() if k != "per"}
        it["queries"] = [q.format(symbol="<SYMBOL>", **fmt) for q in item["queries"]]
        it["direct_urls"] = [u.format(**fmt) for u in item.get("direct_urls", [])]
        per = item.get("per")
        if per:
            it["symbols"] = sorted(s for s, r in roles.items() if per in r) if per != "top" else "Top-3 setups + every EXIT/TRIM (decided while writing)"
        out.append(it)
    return out


def wilder(series: pd.Series, n: int) -> pd.Series:
    return series.ewm(alpha=1 / n, adjust=False, min_periods=n).mean()


def rsi14(close: pd.Series):
    d = close.diff()
    up, dn = wilder(d.clip(lower=0), 14), wilder((-d).clip(lower=0), 14)
    rs = up / dn.replace(0, math.nan)
    return 100 - 100 / (1 + rs)


def atr14(df: pd.DataFrame):
    pc = df["Close"].shift()
    tr = pd.concat([df["High"] - df["Low"], (df["High"] - pc).abs(), (df["Low"] - pc).abs()], axis=1).max(axis=1)
    return wilder(tr, 14)


def classify_stage(c, s50, s200, s50_prev):
    if None in (c, s50, s200, s50_prev):
        return None
    if c > s50 > s200 and s50 > s50_prev:
        return 2
    if c < s50 < s200 and s50 < s50_prev:
        return 4
    return 3 if c >= s200 else 1


def num(x, nd=2):
    return None if x is None or (isinstance(x, float) and math.isnan(x)) else round(float(x), nd)


def metrics(df: pd.DataFrame) -> dict:
    df = df.dropna(subset=["Close"])
    if len(df) < 30:
        return {"error": f"only {len(df)} bars"}
    c = df["Close"]
    s20, s50, s200 = (c.rolling(n).mean() for n in (20, 50, 200))
    r, a = rsi14(c), atr14(df)
    last = len(df) - 1
    at = lambda s, k=0: num(s.iloc[last - k]) if last - k >= 0 else None
    pct = lambda k: num((c.iloc[last] / c.iloc[last - k] - 1) * 100) if last - k >= 0 else None
    vol = df["Volume"]
    v20 = vol.iloc[last - 20:last].mean() if last >= 20 else math.nan
    vmult = num(vol.iloc[last] / v20) if v20 and v20 > 0 else None
    hi52, lo52 = df["High"].iloc[-252:].max(), df["Low"].iloc[-252:].min()
    swing_low_20d = num(df["Low"].iloc[-20:].min()) if df["Low"].iloc[-20:].notna().any() else None
    close = at(c)
    s50v, s200v, s50p = at(s50), at(s200), at(s50, 10)
    stage = classify_stage(close, s50v, s200v, s50p)
    atrv = at(a)
    # momentum gate (scoring.json): SMA history over the test windows, 63-day base pivot, volume dryup
    s20v = at(s20)
    s50_21, s200_63 = at(s50, 21), at(s200, 63)
    low63 = df["Low"].iloc[-63:]
    base_low_63d = num(low63.min()) if low63.notna().any() else None
    vol63 = vol.iloc[-63:]
    vol_dryup = num(vol63.min() / vol63.mean()) if len(vol63) >= 20 and vol63.notna().any() and vol63.mean() > 0 else None
    support_anchor, support_dist_atr = None, None
    if close is not None and atrv:
        anchors = [x for x in (s50v, base_low_63d) if x is not None]
        if anchors:
            if s50v is not None and base_low_63d is not None and (s50v - base_low_63d) > 2.5 * atrv:
                near = [x for x in (s50v, swing_low_20d, s20v) if x is not None and x <= close]
                support_anchor = max(near) if near else s50v
            else:
                support_anchor = min(anchors)
            support_dist_atr = num((close - support_anchor) / atrv)
    # distribution days: down >= 0.2% on higher volume than the prior session, last 25 sessions
    dist = None
    if vol.iloc[-25:].sum() > 0:
        ch = c.pct_change().iloc[-25:]
        dist = int(((ch <= -0.002) & (vol.iloc[-25:] > vol.shift().iloc[-25:])).sum())
    return {
        "asof_bar": df.index[-1].strftime("%Y-%m-%d"),
        "close": close, "prev_close": at(c, 1),
        "chg_1d_pct": pct(1), "chg_1w_pct": pct(5), "chg_2w_pct": pct(10), "chg_1m_pct": pct(21),
        "sma20": s20v, "sma50": s50v, "sma200": s200v,
        "sma50_10d_ago": s50p,
        "sma50_trend": None if s50p is None or s50v is None else ("RISING" if s50v > s50p else "FALLING/FLAT"),
        "rsi14": at(r), "atr14": atrv,
        "vol": int(vol.iloc[last]) if not math.isnan(vol.iloc[last]) else None,
        "vol_mult_20d": vmult,
        "swing_low_20d": swing_low_20d,
        "hi52": num(hi52), "lo52": num(lo52),
        "pct_from_52w_high": num((close / hi52 - 1) * 100),
        "delta_50dma_atr": num((close - s50v) / atrv) if s50v and atrv else None,
        "support_anchor": support_anchor,
        "support_distance_atr": support_dist_atr,
        "sma50_21d_ago": s50_21, "sma200_63d_ago": s200_63,
        "base_low_63d": base_low_63d,
        "base_pivot_atr": num((close - base_low_63d) / atrv) if (base_low_63d is not None and atrv) else None,
        "vol_dryup_ratio_63d": vol_dryup,
        "dist_days_25": dist,
        "stage": stage,
        "stage_label": {1: "Stage 1 (Basing)", 2: "Stage 2 (Markup)", 3: "Stage 3 (Topping / Pullback)",
                        4: "Stage 4 (Markdown)"}.get(stage, "N/A (insufficient history)"),
        "bars": len(df),
    }


def is_option(sym: str) -> bool:
    return bool(OPTION_RE.match(sym.replace(" ", "")))


def yahoo_symbol(market: str, sym: str) -> str:
    sym = sym.strip().upper()
    if sym in ALIASES[market]:
        return ALIASES[market][sym]
    if sym.startswith("^") or sym.endswith((".NS", ".BO")):
        return sym
    return sym + ".NS" if market == "IN" else sym.replace(".", "-")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_sources(market: str):
    """Read every source declared for this market from data/ (see .agents/config/portfolios.json).
    Returns (roles, sources). Sets the globals INPUTS, META, POSITIONS and OPTIONS_BOOK. Aborts on a missing input."""
    global META, POSITIONS, OPTIONS_BOOK
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import data_layer
    cfg = json.load(open(PORTFOLIOS_FILE, encoding="utf-8"))[market]
    meta_path = os.path.join(ROOT, "data", "metadata", "symbols.json")
    META = json.load(open(meta_path, encoding="utf-8")).get(market, {}).get("symbols", {}) if os.path.exists(meta_path) else {}
    roles, sources = {}, []
    POSITIONS, OPTIONS_BOOK = [], []
    for src in cfg["sources"]:
        path = os.path.join(ROOT, src["path"])
        rec = {"id": src["id"], "role": src["role"], "path": src["path"], "kind": src["kind"],
               "sha256": None, "rows": 0, "symbols": 0, "status": "ok"}
        if not os.path.exists(path):
            raise SystemExit(f"INPUT MISSING: {src['path']} ({src['id']}). Aborting.")
        rec["sha256"] = sha256(path)
        if src["kind"] == "transactions":
            meta, pos, cash = data_layer.account_state(path)
            if meta.get("market") not in (None, market):
                raise SystemExit(f"{src['path']} is a {meta.get('market')} log but is listed under {market}")
            positions = [{"symbol": sym, "quantity": p["quantity"],
                          "cost_basis": p["cost_basis"] if p["cost_known"] else None,
                          "realized_pl": p["realized_pl"]} for sym, p in sorted(pos.items())]
            POSITIONS.append({"id": src["id"], "label": meta.get("account", src["id"]),
                              "snapshot_date": meta.get("last_date"), "cash": cash, "positions": positions})
            symbols = [p["symbol"] for p in positions]
            rec["rows"] = meta.get("transactions", 0)
        elif src["kind"] == "records":
            data = json.load(open(path, encoding="utf-8"))
            node = data
            for part in src["key"].split("."):
                node = node[part]
            symbols = []
            for r in node:
                sym = r.get(src["symbol_key"])
                if not sym or not isinstance(sym, str):
                    continue
                sym = sym.strip().upper()
                symbols.append(sym)
                if src["role"] == "options" and src.get("value_key") and isinstance(r.get(src["value_key"]), (int, float)):
                    OPTIONS_BOOK.append({"source": src["id"], "underlying": sym, "market_value": float(r[src["value_key"]])})
            rec["rows"] = len(node)
        else:
            raise SystemExit(f"Unknown source kind {src['kind']} for {src['id']}")
        if not symbols and src.get("required", True) and src["role"] == "holding":
            raise SystemExit(f"{src['id']} produced no positions. Check the transaction log.")
        for sym in set(symbols):
            roles.setdefault(sym, set()).add(src["role"])
        rec["symbols"] = len(set(symbols))
        sources.append(rec)
    return roles, sources


CLOSES_CACHE = {}
BENCH_CLOSE_CACHE = None
MARKET_CACHE = None


def compute_portfolio_risk_and_overlap(per_sym: dict, equities: float, cash_total: float, options_value: float, net_worth: float | None):
    """Compute Effective Market Exposure (beta/leverage-adjusted) and Hidden Overlap (pairwise return correlations >= 0.65)
    from the 2-year daily price series already downloaded in memory."""
    if not net_worth or net_worth <= 0 or not per_sym:
        return None
    cur_sym = "₹" if MARKET_CACHE == "IN" else "$"
    bench_name = "Nifty 50" if MARKET_CACHE == "IN" else "S&P 500"
    bench_ret = BENCH_CLOSE_CACHE.pct_change().dropna().iloc[-252:] if BENCH_CLOSE_CACHE is not None and len(BENCH_CLOSE_CACHE) > 30 else None

    weighted_beta_sum = 0.0
    held_returns = {}
    per_holding_exposure = []
    for sym, d in sorted(per_sym.items(), key=lambda kv: -(kv[1].get("market_value") or 0)):
        mv = d.get("market_value") or 0.0
        wt_pct = round(mv / net_worth * 100.0, 2)
        meta = d.get("metadata") or {}
        lev = float(meta.get("leverage_multiplier") or 1.0)
        if sym in ("SOXL", "TQQQ", "UPRO", "SPXL", "TECL", "FNGU", "LABU") and lev == 1.0:
            lev = 3.0
        elif sym in ("USD", "SSO", "QLD", "NVDL", "CONL", "MSTU") and lev == 1.0:
            lev = 2.0
        s_close = CLOSES_CACHE.get(sym)
        beta_raw = 1.0
        if s_close is not None and len(s_close) > 30:
            s_ret = s_close.pct_change().dropna().iloc[-252:]
            held_returns[sym] = s_ret
            if bench_ret is not None:
                joined = pd.DataFrame({"s": s_ret, "b": bench_ret}).dropna()
                if len(joined) >= 30 and joined["b"].var() > 0:
                    beta_raw = round(float(joined["s"].cov(joined["b"]) / joined["b"].var()), 2)
        eff_beta = round(beta_raw if lev == 1.0 else max(beta_raw, lev), 2)
        d["beta_1y"] = beta_raw
        d["effective_beta"] = eff_beta
        d["weight_pct"] = wt_pct
        weighted_beta_sum += (mv / net_worth) * eff_beta
        per_holding_exposure.append({
            "symbol": sym, "weight_pct": wt_pct, "beta_1y": beta_raw,
            "leverage_multiplier": lev, "effective_beta": eff_beta,
            "effective_exposure_pct": round(wt_pct * eff_beta, 2)
        })

    # Options carry higher effective delta/leverage (~2.5x notional proxy when live delta is not in log)
    options_eff_beta = 2.5 if options_value > 0 else 0.0
    weighted_beta_sum += (options_value / net_worth) * options_eff_beta
    eff_pct = round(weighted_beta_sum * 100.0, 1)
    eff_val = round(net_worth * weighted_beta_sum, 2)
    one_pct_drop_loss = round(eff_val * 0.01, 2)

    # Pairwise correlation matrix across held stocks
    high_corr_pairs = []
    adj = {s: set() for s in held_returns}
    if len(held_returns) >= 2:
        ret_df = pd.DataFrame(held_returns).dropna(how="all")
        corr = ret_df.corr(min_periods=30)
        syms = sorted(held_returns.keys())
        for i in range(len(syms)):
            for j in range(i + 1, len(syms)):
                s1, s2 = syms[i], syms[j]
                val = corr.loc[s1, s2] if (s1 in corr.index and s2 in corr.columns) else math.nan
                if not math.isnan(val) and val >= 0.60:
                    r_val = round(float(val), 2)
                    w1 = per_sym[s1].get("weight_pct", 0.0)
                    w2 = per_sym[s2].get("weight_pct", 0.0)
                    high_corr_pairs.append({
                        "pair": f"{s1}-{s2}", "symbol_a": s1, "symbol_b": s2,
                        "correlation_1y": r_val,
                        "same_direction_pct_approx": round(50.0 + 50.0 * r_val, 0),
                        "combined_weight_pct": round(w1 + w2, 2)
                    })
                    if r_val >= 0.65:
                        adj[s1].add(s2)
                        adj[s2].add(s1)
        high_corr_pairs.sort(key=lambda x: -x["correlation_1y"])

    # Connected components for lockstep clusters (correlation >= 0.65)
    visited, clusters = set(), []
    for s in sorted(adj, key=lambda k: -(per_sym[k].get("market_value") or 0)):
        if s in visited or not adj[s]:
            continue
        comp, queue = [], [s]
        while queue:
            cur = queue.pop(0)
            if cur in visited:
                continue
            visited.add(cur)
            comp.append(cur)
            for nb in sorted(adj[cur]):
                if nb not in visited:
                    queue.append(nb)
        if len(comp) >= 2:
            comb_wt = round(sum(per_sym[x].get("weight_pct", 0.0) for x in comp), 2)
            clusters.append({"symbols": comp, "count": len(comp), "combined_weight_pct": comb_wt})
    clusters.sort(key=lambda c: -c["combined_weight_pct"])

    plain_exposure = (
        f"Your total net worth is {cur_sym}{net_worth:,.2f}, but because of stock volatility (beta), "
        f"leveraged positions, and options, your portfolio behaves like {cur_sym}{eff_val:,.2f} "
        f"({eff_pct:.1f}% effective exposure to {bench_name}). In plain words: a 1% drop in the "
        f"{bench_name} is expected to move your portfolio by about {weighted_beta_sum:.2f}% "
        f"(roughly {cur_sym}{one_pct_drop_loss:,.2f})."
    )
    if clusters:
        top_c = clusters[0]
        plain_overlap = (
            f"Although you hold {len(per_sym)} separate equity tickers, {top_c['count']} of them "
            f"({', '.join(top_c['symbols'])}) move closely together (1-year return correlation >= 0.65) "
            f"and make up {top_c['combined_weight_pct']:.1f}% of your net worth — acting like one combined bet."
        )
    elif high_corr_pairs:
        top_p = high_corr_pairs[0]
        plain_overlap = (
            f"Your highest-overlap pair is {top_p['pair']} (1-year return correlation {top_p['correlation_1y']:.2f}, "
            f"combined weight {top_p['combined_weight_pct']:.1f}% of net worth); no multi-stock cluster exceeds the 0.65 lockstep threshold."
        )
    else:
        plain_overlap = (
            f"Across your {len(per_sym)} equity holdings, no pair has a 1-year daily return correlation of 0.60 or higher, "
            f"indicating low hidden overlap between positions."
        )

    return {
        "portfolio_beta_weighted": round(weighted_beta_sum, 2),
        "effective_market_exposure_pct": eff_pct,
        "effective_market_exposure_value": eff_val,
        "expected_move_per_1pct_index": round(weighted_beta_sum, 2),
        "expected_dollar_per_1pct_index": one_pct_drop_loss,
        "per_holding_exposure": per_holding_exposure,
        "high_correlation_pairs": high_corr_pairs[:15],
        "lockstep_clusters": clusters,
        "plain_english_exposure": plain_exposure,
        "plain_english_overlap": plain_overlap,
    }


def consolidate_positions(inst=None):
    """One view per symbol across accounts, valued at the ledger close (inst) when available.
    Cost basis comes from the transaction log; a missing cost stays None, never guessed."""
    per_sym, cash_total = {}, 0.0
    for acct in POSITIONS:
        cash_total += acct["cash"] or 0
        for p in acct["positions"]:
            close = (inst or {}).get(p["symbol"], {}).get("close")
            mv = round(p["quantity"] * close, 2) if close else None
            d = per_sym.setdefault(p["symbol"], {"symbol": p["symbol"], "accounts": [], "quantity": 0.0,
                                                 "market_value": 0.0, "cost_basis": 0.0, "cost_complete": True,
                                                 "priced": True})
            d["accounts"].append({"account": acct["id"], "quantity": p["quantity"], "cost_basis": p["cost_basis"],
                                  "market_value": mv, "realized_pl": p["realized_pl"]})
            d["quantity"] += p["quantity"] or 0
            if mv is None:
                d["priced"] = False
            else:
                d["market_value"] += mv
            if p["cost_basis"] is None:
                d["cost_complete"] = False
            else:
                d["cost_basis"] += p["cost_basis"]
    for d in per_sym.values():
        d["quantity"] = round(d["quantity"], 6)
        d["market_value"] = round(d["market_value"], 2) if d["priced"] else None
        d["cost_basis"] = round(d["cost_basis"], 2) if d["cost_complete"] else None
        d["gain"] = round(d["market_value"] - d["cost_basis"], 2) if (d["cost_complete"] and d["priced"]) else None
        d["metadata"] = META.get(d["symbol"])
    equities = round(sum(d["market_value"] or 0 for d in per_sym.values()), 2)
    options_value = round(sum(o["market_value"] for o in OPTIONS_BOOK), 2)
    net_worth = round(equities + cash_total + options_value, 2) if inst else None
    risk_overlap = compute_portfolio_risk_and_overlap(per_sym, equities, cash_total, options_value, net_worth) if inst else None
    return {
        "accounts": [{"id": a["id"], "label": a["label"], "last_transaction": a["snapshot_date"], "positions": len(a["positions"]),
                      "cash": a["cash"], "market_value": round(sum((inst or {}).get(p["symbol"], {}).get("close", 0) * p["quantity"]
                                                                  for p in a["positions"]), 2) if inst else None}
                     for a in POSITIONS],
        "consolidated": sorted(per_sym.values(), key=lambda d: -(d["market_value"] or 0)),
        "equities_value": equities, "cash_total": round(cash_total, 2),
        "options_value": options_value, "options_rows": OPTIONS_BOOK,
        "net_worth": net_worth,
        "portfolio_risk_and_overlap": risk_overlap,
        "reconciliation": {
            "unclassified": sorted(s for s in per_sym if not META.get(s)),
            "in_metadata_but_no_position": sorted(s for s in META if s not in per_sym),
            "unpriced": sorted(s for s, d in per_sym.items() if not d["priced"]),
            "cost_unknown": sorted(s for s, d in per_sym.items() if not d["cost_complete"]),
        },
    }


def workbook_symbols(market: str):
    global INPUTS
    roles, INPUTS = load_sources(market)
    return roles


def load_universe(spec: str, market: str):
    """Return (symbols, meta) where meta[symbol] = {name, sector, industry} from the constituent list."""
    if not spec:
        return [], {}
    try:
        if spec.startswith("file:"):
            return [l.strip().upper() for l in open(spec[5:]) if l.strip()], {}
        if spec in ("sp500", "sp1500"):
            pages = ["List_of_S%26P_500_companies"] + (
                ["List_of_S%26P_400_companies", "List_of_S%26P_600_companies"] if spec == "sp1500" else [])
            syms, meta = [], {}
            for page in pages:
                req = urllib.request.Request(f"https://en.wikipedia.org/wiki/{page}", headers={"User-Agent": "Mozilla/5.0"})
                tables = pd.read_html(io.BytesIO(urllib.request.urlopen(req, timeout=30).read()))
                df = next(t for t in tables if {"Symbol", "Security"} <= set(map(str, t.columns)))
                for s, n, sec, ind in zip(df["Symbol"], df["Security"], df["GICS Sector"], df["GICS Sub-Industry"]):
                    s = str(s).replace(".", "-")
                    if s not in meta:
                        syms.append(s)
                        meta[s] = {"name": n, "sector": sec, "industry": ind}
            return syms, meta
        if spec == "nifty500":
            req = urllib.request.Request("https://nsearchives.nseindia.com/content/indices/ind_nifty500list.csv",
                                         headers={"User-Agent": "Mozilla/5.0"})
            df = pd.read_csv(io.BytesIO(urllib.request.urlopen(req, timeout=30).read()))
            meta = {s: {"name": n, "sector": None, "industry": ind}
                    for s, n, ind in zip(df["Symbol"], df["Company Name"], df["Industry"])}
            return list(df["Symbol"]), meta
    except Exception as e:  # noqa: BLE001
        print(f"[warn] universe '{spec}' unavailable ({e}); supply --screen file:<path>", file=sys.stderr)
    return [], {}


def download(tickers, period="2y"):
    tickers = sorted(set(tickers))
    out, failed = {}, []
    for i in range(0, len(tickers), 100):
        chunk = tickers[i:i + 100]
        data = yf.download(chunk, period=period, interval="1d", auto_adjust=False, group_by="ticker",
                           threads=True, progress=False)
        for t in chunk:
            try:
                df = data[t] if len(chunk) > 1 else data
                df = df.dropna(subset=["Close"])
                if df.empty:
                    raise ValueError("no data")
                out[t] = df
            except Exception:  # noqa: BLE001
                failed.append(t)
    return out, failed


def market_cap(market: str, yt: str):
    try:
        mc = yf.Ticker(yt).fast_info["market_cap"]
    except Exception:  # noqa: BLE001
        return None
    if not mc:
        return None
    return num(mc / 1e7, 0) if market == "IN" else num(mc / 1e9, 2)


def cap_tier(market: str, mc):
    if mc is None:
        return None
    if market == "IN":
        return "Large" if mc > 50000 else "Mid" if mc >= 15000 else "Small" if mc >= 500 else "Micro"
    return "Large" if mc > 50 else "Mid" if mc >= 10 else "Small" if mc >= 1 else "Micro"


def fred(series: str):
    try:
        df = pd.read_csv(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}")
        df = df[pd.to_numeric(df.iloc[:, 1], errors="coerce").notna()]
        return {"date": df.iloc[-1, 0], "value": float(df.iloc[-1, 1]), "prior_week": float(df.iloc[-6, 1])}
    except Exception:  # noqa: BLE001
        return None


def ymap_rev(ymap, rep):
    return next(k for k, v in ymap.items() if v == rep)


def solve_reverse_dcf(target_val: float, base_cf: float, r_pct: float, term_mult: float, years: int = 10) -> float | None:
    """Solve for the 10-year annual growth rate g (%) such that PV(10y cash flows + terminal value) == target_val."""
    if not target_val or target_val <= 0 or not base_cf or base_cf <= 0:
        return None
    r = r_pct / 100.0
    lo, hi = -0.35, 0.75
    for _ in range(45):
        mid = (lo + hi) / 2.0
        pv = 0.0
        cf = base_cf
        for t in range(1, years + 1):
            cf *= (1.0 + mid)
            pv += cf / ((1.0 + r) ** t)
        pv += (cf * term_mult) / ((1.0 + r) ** years)
        if pv < target_val:
            lo = mid
        else:
            hi = mid
    return round(((lo + hi) / 2.0) * 100.0, 2)


def enrich_symbol_expectations(market: str, sym: str, yt: str, close: float | None, scoring: dict) -> dict:
    """Fetch free yfinance consensus revisions, analyst targets, and compute Reverse DCF implied growth."""
    rdcf_cfg = scoring.get("reverse_dcf", {})
    r_pct = float(rdcf_cfg.get("discount_rate_pct", {}).get(market, 10.0 if market == "US" else 12.0))
    term_mult = float(rdcf_cfg.get("terminal_multiple_fcf", {}).get(market, 18.0 if market == "US" else 20.0))
    years = int(rdcf_cfg.get("projection_years", 10))
    scale = 1e7 if market == "IN" else 1e9
    unit_lbl = "₹ Cr" if market == "IN" else "$B"

    info = {}
    eps_trend_dict = {}
    try:
        tk = yf.Ticker(yt)
        info = tk.info or {}
        if info.get("quoteType") != "ETF":
            try:
                et = tk.eps_trend
                if et is not None and not et.empty:
                    eps_trend_dict = et.to_dict()
            except Exception:  # noqa: BLE001
                pass
    except Exception:  # noqa: BLE001
        pass

    mc_raw = info.get("marketCap")
    ev_raw = info.get("enterpriseValue") or mc_raw
    fcf_raw = info.get("freeCashflow")
    ocf_raw = info.get("operatingCashflow")
    rev_raw = info.get("totalRevenue")
    opm_raw = info.get("operatingMargins")
    pm_raw = info.get("profitMargins")
    tpe = num(info.get("trailingPE"))
    fpe = num(info.get("forwardPE"))

    # Determine base cash flow for Reverse DCF with transparent fallback hierarchy
    base_cf_raw = None
    basis = None
    if isinstance(fcf_raw, (int, float)) and fcf_raw > 0 and (not rev_raw or fcf_raw >= 0.02 * rev_raw):
        base_cf_raw = float(fcf_raw)
        basis = "TTM Free Cash Flow"
    elif isinstance(ocf_raw, (int, float)) and ocf_raw > 0:
        base_cf_raw = float(ocf_raw) * 0.75
        basis = "Normalized Owner's Cash Flow (75% of TTM Operating Cash Flow; FCF depressed by capex)"
    elif mc_raw and tpe and tpe > 0:
        base_cf_raw = float(mc_raw) / float(tpe)
        basis = "TTM Net Profit (derived from Market Cap / Trailing P/E)"
    elif rev_raw and opm_raw and opm_raw > 0:
        tax = 0.25 if market == "IN" else 0.21
        base_cf_raw = float(rev_raw) * float(opm_raw) * (1.0 - tax)
        basis = "Normalized NOPAT (TTM Revenue x Operating Margin after tax)"

    val_raw = ev_raw if (basis and "Free Cash Flow" in basis and ev_raw and ev_raw > 0) else mc_raw
    implied_g = solve_reverse_dcf(val_raw, base_cf_raw, r_pct, term_mult, years) if (val_raw and base_cf_raw) else None
    fcf_yield_pct = num(fcf_raw / mc_raw * 100.0) if (isinstance(fcf_raw, (int, float)) and mc_raw and mc_raw > 0) else None

    if implied_g is not None:
        plain_rdcf = (
            f"At the current price ({close}), the market is pricing in {implied_g:+.1f}% annual growth in "
            f"{basis} for the next {years} years (using a {r_pct:.0f}% discount rate and {term_mult:.0f}x terminal multiple)."
        )
    else:
        plain_rdcf = "Reverse DCF implied growth is N/A (negative or unverified trailing cash flow and earnings)."

    # Consensus EPS revisions (0y = FY1, +1y = FY2)
    cur_map = eps_trend_dict.get("current", {}) if isinstance(eps_trend_dict, dict) else {}
    d30_map = eps_trend_dict.get("30daysAgo", {}) if isinstance(eps_trend_dict, dict) else {}
    d90_map = eps_trend_dict.get("90daysAgo", {}) if isinstance(eps_trend_dict, dict) else {}

    def _valid_eps(v):
        return float(v) if isinstance(v, (int, float)) and not math.isnan(v) and abs(v) > 1e-6 else None

    fy1_cur = _valid_eps(cur_map.get("0y"))
    fy1_30d = _valid_eps(d30_map.get("0y"))
    fy1_90d = _valid_eps(d90_map.get("0y"))
    fy2_cur = _valid_eps(cur_map.get("+1y"))
    fy2_30d = _valid_eps(d30_map.get("+1y"))
    fy2_90d = _valid_eps(d90_map.get("+1y"))

    fy1_rev_30d = num((fy1_cur / fy1_30d - 1.0) * 100.0) if (fy1_cur and fy1_30d and fy1_30d > 0) else None
    fy1_rev_90d = num((fy1_cur / fy1_90d - 1.0) * 100.0) if (fy1_cur and fy1_90d and fy1_90d > 0) else None
    fy2_rev_30d = num((fy2_cur / fy2_30d - 1.0) * 100.0) if (fy2_cur and fy2_30d and fy2_30d > 0) else None
    fy2_rev_90d = num((fy2_cur / fy2_90d - 1.0) * 100.0) if (fy2_cur and fy2_90d and fy2_90d > 0) else None
    fy2_vs_fy1_growth = num((fy2_cur / fy1_cur - 1.0) * 100.0) if (fy2_cur and fy1_cur and fy1_cur > 0) else None

    rev_signals = [x for x in (fy1_rev_90d, fy2_rev_90d, fy1_rev_30d, fy2_rev_30d) if x is not None]
    if not rev_signals:
        rev_label = "NO_CONSENSUS"
    elif max(rev_signals) >= 1.5 and min(rev_signals) >= -0.5:
        rev_label = "RISING_ESTIMATES"
    elif min(rev_signals) <= -1.5:
        rev_label = "FALLING_ESTIMATES"
    else:
        rev_label = "STABLE_ESTIMATES"

    return {
        "reverse_dcf": {
            "implied_10y_cagr_pct": implied_g,
            "basis": basis,
            "base_cashflow_unit": unit_lbl,
            "base_cashflow_val": num(base_cf_raw / scale, 3) if base_cf_raw else None,
            "valuation_used_val": num(val_raw / scale, 2) if val_raw else None,
            "discount_rate_pct": r_pct,
            "terminal_multiple": term_mult,
            "fcf_yield_pct": fcf_yield_pct,
            "plain_english": plain_rdcf,
        },
        "consensus_revisions": {
            "revision_trend": rev_label,
            "fy1_eps_current": num(fy1_cur, 2),
            "fy1_eps_30d_ago": num(fy1_30d, 2),
            "fy1_eps_90d_ago": num(fy1_90d, 2),
            "fy1_eps_rev_30d_pct": fy1_rev_30d,
            "fy1_eps_rev_90d_pct": fy1_rev_90d,
            "fy2_eps_current": num(fy2_cur, 2),
            "fy2_eps_30d_ago": num(fy2_30d, 2),
            "fy2_eps_90d_ago": num(fy2_90d, 2),
            "fy2_eps_rev_30d_pct": fy2_rev_30d,
            "fy2_eps_rev_90d_pct": fy2_rev_90d,
            "implied_fy2_eps_growth_pct": fy2_vs_fy1_growth,
            "analyst_target_low": num(info.get("targetLowPrice"), 2),
            "analyst_target_mean": num(info.get("targetMeanPrice"), 2),
            "analyst_target_high": num(info.get("targetHighPrice"), 2),
            "num_analysts": info.get("numberOfAnalystOpinions"),
        },
        "fundamentals_snapshot": {
            "unit": unit_lbl,
            "market_cap": num(mc_raw / scale, 2) if mc_raw else None,
            "enterprise_value": num(ev_raw / scale, 2) if ev_raw else None,
            "revenue_ttm": num(rev_raw / scale, 2) if rev_raw else None,
            "free_cashflow_ttm": num(fcf_raw / scale, 3) if isinstance(fcf_raw, (int, float)) else None,
            "operating_cashflow_ttm": num(ocf_raw / scale, 3) if isinstance(ocf_raw, (int, float)) else None,
            "operating_margin_pct": num(opm_raw * 100.0, 2) if isinstance(opm_raw, (int, float)) else None,
            "profit_margin_pct": num(pm_raw * 100.0, 2) if isinstance(pm_raw, (int, float)) else None,
            "roe_pct": num(info.get("returnOnEquity") * 100.0, 2) if isinstance(info.get("returnOnEquity"), (int, float)) else None,
            "debt_to_equity_pct": num(info.get("debtToEquity"), 2),
            "trailing_pe": tpe,
            "forward_pe": fpe,
            "revenue_growth_yoy_pct": num(info.get("revenueGrowth") * 100.0, 2) if isinstance(info.get("revenueGrowth"), (int, float)) else None,
            "earnings_growth_yoy_pct": num(info.get("earningsGrowth") * 100.0, 2) if isinstance(info.get("earningsGrowth"), (int, float)) else None,
        },
    }


def build(args):
    market = args.market
    cfg = BENCH[market]
    alias_file = os.path.join(CONFIG, "aliases.json")
    if os.path.exists(alias_file):
        ALIASES[market].update(json.load(open(alias_file)).get(market, {}))
    roles = workbook_symbols(market)
    for s in filter(None, (args.extra or "").split(",")):
        roles.setdefault(s.strip().upper(), set()).add("extra")
    universe, umeta = load_universe(args.screen, market)

    ymap = {}  # yahoo symbol -> report symbol
    for name, ys in cfg["indices"].items():
        ymap[ys] = name
    for e in cfg["etfs"]:
        ymap[e] = e
    for name, ys in cfg["sectors"].items():
        ymap[ys] = name
    for s in roles:
        ymap.setdefault(yahoo_symbol(market, s), s)
    for s in universe:
        ymap.setdefault(yahoo_symbol(market, s), s)

    frames, failed = download(list(ymap))
    if market == "IN":  # retry failed .NS symbols on BSE
        retry = {t: t[:-3] + ".BO" for t in failed if t.endswith(".NS")}
        if retry:
            got, _ = download(list(retry.values()))
            for old, new in retry.items():
                if new in got:
                    frames[old] = got[new]
                    failed.remove(old)

    inst = {}
    closes = {}  # report symbol -> filtered Close series (for momentum-gate RS vs benchmark)
    for yt, df in frames.items():
        if args.date:  # replay a past session: drop bars after the requested date
            df = df[df.index <= pd.Timestamp(args.date)]
        m = metrics(df)
        rep = ymap[yt]
        m.update({"yahoo": yt, "roles": sorted(roles.get(rep, []))})
        m["kind"] = ("index" if rep in cfg["indices"] else "sector" if rep in cfg["sectors"] else
                     "etf" if rep in cfg["etfs"] else "stock")
        inst[rep] = m
        if m["kind"] == "stock" and not m.get("error"):
            closes[rep] = df["Close"]

    # momentum gate: 63d / 28d relative strength (excess return) vs the scoring.json benchmark
    global CLOSES_CACHE, BENCH_CLOSE_CACHE, MARKET_CACHE
    MARKET_CACHE = market
    CLOSES_CACHE = closes
    scoring = json.load(open(os.path.join(ROOT, ".agents", "config", "scoring.json")))
    mg_bench = scoring["momentum_gate"]["benchmark"][market]
    if mg_bench in frames:
        bc = frames[mg_bench]["Close"]
        if args.date:
            bc = bc[bc.index <= pd.Timestamp(args.date)]
        BENCH_CLOSE_CACHE = bc
        for rep, c in closes.items():
            j = pd.DataFrame({"s": c, "b": bc}).dropna()
            if len(j) >= 64:
                inst[rep]["rs_63d_pct"] = num((j["s"].iloc[-1] / j["s"].iloc[-64] - 1) * 100
                                               - (j["b"].iloc[-1] / j["b"].iloc[-64] - 1) * 100)
            if len(j) >= 29:
                inst[rep]["rs_28d_pct"] = num((j["s"].iloc[-1] / j["s"].iloc[-29] - 1) * 100
                                               - (j["b"].iloc[-1] / j["b"].iloc[-29] - 1) * 100)
    elif cfg["primary"] in frames:
        bc = frames[cfg["primary"]]["Close"]
        if args.date:
            bc = bc[bc.index <= pd.Timestamp(args.date)]
        BENCH_CLOSE_CACHE = bc

    # Attach momentum_gate (Test A, Test B, Test C) to every stock instrument
    import momentum_gate as mg_mod
    for sym_k, m_val in inst.items():
        if m_val.get("kind") == "stock" and not m_val.get("error") and m_val.get("close") is not None:
            m_val["momentum_gate"] = mg_mod.gate(m_val, scoring["momentum_gate"])

    # Enrich holding, shortlist, and extra symbols with Reverse DCF + Consensus EPS Revisions
    enrich_syms = [
        s for s, rs in roles.items()
        if ("holding" in rs or "shortlist" in rs or "extra" in rs)
        and s in inst and inst[s].get("kind") == "stock" and not inst[s].get("error")
    ]
    if enrich_syms:
        def _enrich_one(s):
            m_val = inst[s]
            return s, enrich_symbol_expectations(market, s, m_val.get("yahoo", s), m_val.get("close"), scoring)
        with ThreadPoolExecutor(max_workers=8) as pool_ex:
            for s, extra_data in pool_ex.map(_enrich_one, enrich_syms):
                inst[s].update(extra_data)

    primary_name = ymap[cfg["primary"]]
    # The session date is a requirement, not a label: the benchmark must have a bar on that date.
    asof = args.date
    bench_bar = inst.get(primary_name, {}).get("asof_bar")
    if bench_bar != asof:
        sys.exit(f"STALE DATA: benchmark {primary_name} last bar is {bench_bar}, session is {asof}. "
                 f"Source not yet updated or session not closed. Aborting; nothing written.")
    stale = sorted(k for k, v in inst.items() if v.get("asof_bar") and v["asof_bar"] < asof)

    # Per-symbol freshness for every name a report will quote as a holding, shortlist or watchlist entry.
    fetched_at = dt.datetime.now().isoformat(timespec="seconds")
    freshness = []
    for sym in sorted(roles):
        rs = sorted(roles[sym])
        m = inst.get(sym)
        if not m or m.get("error") or not m.get("asof_bar"):
            status, bar = "no_data", None
        else:
            bar = m["asof_bar"]
            status = "current" if bar == asof else "STALE"
        freshness.append({"symbol": sym, "roles": rs, "status": status, "asof_bar": bar, "fetched_at": fetched_at})
    blocked = [f["symbol"] for f in freshness if "holding" in f["roles"] and f["status"] != "current"]
    if blocked and not args.allow_stale_holdings:
        sys.exit(f"HOLDINGS NOT CURRENT on {asof}: {', '.join(blocked[:40])}"
                 f"{' ...' if len(blocked) > 40 else ''}. Aborting; nothing written. "
                 "Re-run after the source updates, or pass --allow-stale-holdings and state the reason in the report.")

    # breadth from the screening universe when supplied, otherwise from the book/watchlist
    pool = [inst[s] for s in (universe or roles) if s in inst and inst[s].get("sma50")]
    breadth50 = num(100 * sum(1 for m in pool if m["close"] > m["sma50"]) / len(pool), 1) if pool else None
    breadth200 = num(100 * sum(1 for m in pool if m.get("sma200") and m["close"] > m["sma200"]) / len(pool), 1) if pool else None
    sec = {n: inst[n] for n in cfg["sectors"] if n in inst}
    p = inst.get(primary_name, {})
    vix_name = "India VIX" if market == "IN" else "VIX"
    vix_inst = inst.get(vix_name, {})
    vix_1d = vix_inst.get("chg_1d_pct") if isinstance(vix_inst, dict) else None
    sub_regime = "STANDARD"
    if not p or p.get("error"):
        label = "N/A (benchmark series unavailable)"
    elif p["close"] > p["sma50"] > p["sma200"] and (breadth50 is None or breadth50 >= 55):
        label = "Uptrend (broad)"
    elif p["close"] > p["sma50"]:
        label = "Uptrend (narrow breadth)"
    elif p["close"] > p["sma200"]:
        label = "Correction (below 50-DMA, above 200-DMA)"
    else:
        # Check for Capitulation Reversal / Follow-Through Watch when breadth is washed out (<= 25%) and green shoots appear
        p_1d = p.get("chg_1d_pct")
        p_sw20 = p.get("swing_low_20d")
        green_shoot = (
            (p_1d is not None and p_1d >= 0.0)
            or (p_sw20 is not None and p_sw20 > 0 and p["close"] >= p_sw20 * 1.01)
            or (vix_1d is not None and vix_1d < 0.0)
        )
        if breadth50 is not None and breadth50 <= 25.0 and green_shoot:
            label = "Downtrend (capitulation bounce / follow-through watch)"
            sub_regime = "CAPITULATION_REVERSAL_WATCH"
        else:
            label = "Downtrend"
    regime = {
        "label": label, "sub_regime": sub_regime, "benchmark": primary_name,
        "breadth_pct_above_50dma": breadth50,
        "breadth_pct_above_200dma": breadth200, "breadth_pool_size": len(pool),
        "distribution_days_25": p.get("dist_days_25"),
        "sectors_above_20dma": sum(1 for m in sec.values() if m.get("sma20") and m["close"] > m["sma20"]),
        "sectors_above_50dma": sum(1 for m in sec.values() if m.get("sma50") and m["close"] > m["sma50"]),
        "sectors_above_200dma": sum(1 for m in sec.values() if m.get("sma200") and m["close"] > m["sma200"]),
        "sector_count": len(sec),
    }

    # sector rotation quadrant: 1M return vs benchmark, and 1W momentum direction
    bench_1m = p.get("chg_1m_pct")
    for n, m in sec.items():
        if m.get("chg_1m_pct") is None or bench_1m is None or m.get("chg_1w_pct") is None:
            m["quadrant"] = None
            continue
        rel, mom = m["chg_1m_pct"] - bench_1m, m["chg_1w_pct"] - (p.get("chg_1w_pct") or 0)
        m["quadrant"] = ("Leading" if rel >= 0 and mom >= 0 else "Weakening" if rel >= 0 else
                         "Improving" if mom >= 0 else "Lagging")
        m["rel_1m_vs_benchmark"] = num(rel)

    macro = {}
    if market == "US":
        for k, sid in (("us2y", "DGS2"), ("us10y", "DGS10")):
            macro[k] = fred(sid)
        if macro["us2y"] and macro["us10y"]:
            macro["spread_bp"] = round((macro["us10y"]["value"] - macro["us2y"]["value"]) * 100)

    screen = {"universe": args.screen, "size": len(universe), "bull": [], "bull_near": [], "bull_relaxed": [],
              "bear": [], "bear_near": [], "bear_relaxed": []}
    for s in universe:
        m = inst.get(s)
        if not m or m.get("error") or m.get("rsi14") is None or m.get("vol_mult_20d") is None:
            continue
        row = {"symbol": s, **{k: m[k] for k in ("close", "sma50", "sma200", "rsi14", "atr14", "vol_mult_20d",
                                                  "chg_1d_pct", "chg_1w_pct", "pct_from_52w_high", "stage")}}
        if m["stage"] == 2:
            if 55 <= m["rsi14"] <= 72:
                (screen["bull"] if m["vol_mult_20d"] >= 1.5 and m["chg_1d_pct"] > 0 else screen["bull_near"]).append(row)
            else:
                screen["bull_relaxed"].append(row)
        if m["stage"] == 4:
            if m["rsi14"] < 45:
                (screen["bear"] if m["vol_mult_20d"] >= 1.5 and m["chg_1d_pct"] < 0 else screen["bear_near"]).append(row)
            else:
                screen["bear_relaxed"].append(row)
    for k in ("bull", "bull_near", "bull_relaxed", "bear", "bear_near", "bear_relaxed"):
        screen[k].sort(key=lambda r: -r["vol_mult_20d"])
        screen[k] = screen[k][:120]
        for r in screen[k]:  # cap tier needs market cap; fetch only for the shortlisted rows
            r["market_cap"] = market_cap(market, ymap_rev(ymap, r["symbol"]))
            r["cap_tier"] = cap_tier(market, r["market_cap"])
    screen["cap_unit"] = "INR Cr" if market == "IN" else "USD B"

    # the 30-name lists the report must publish: 10 per cap tier, strict passes first, then 'near' passes
    def pick(strict, near, relaxed, side):
        out = {"Large": [], "Mid": [], "Small": []}
        for label, rows in (("confirmed", strict), ("awaiting volume confirmation" if side == "bull" else "no distribution-volume confirmation", near),
                            ("Stage 2 but RSI outside 55-72" if side == "bull" else "Stage 4 but RSI 45 or higher", relaxed)):
            for r in rows:
                t = r.get("cap_tier")
                if t in out and len(out[t]) < 10:
                    meta = umeta.get(r["symbol"], {})
                    out[t].append({**r, "name": meta.get("name"), "sector": meta.get("sector"),
                                   "industry": meta.get("industry"), "qualifier": label})
        return out
    screen["bull_pick"] = pick(screen["bull"], screen["bull_near"], screen["bull_relaxed"], "bull")
    screen["bear_pick"] = pick(screen["bear"], screen["bear_near"], screen["bear_relaxed"], "bear")

    return {
        "market": market, "asof": asof, "generated": dt.datetime.now().isoformat(timespec="seconds"),
        "source": "Yahoo Finance daily OHLCV via yfinance (SMA arithmetic; RSI/ATR Wilder 14)",
        "regime": regime, "macro": macro, "instruments": inst, "screen": screen,
        "failures": sorted(failed), "stale_vs_asof": stale, "freshness": freshness, "inputs": INPUTS,
        "research_needs": render_research(market, asof, roles),
        "research_file": f"<RUN_DIR>/cache/research_{market}_{asof}.json",
    }


def factpack(facts):
    """The compact subset that report sections are drafted from. Holdings and shortlist names keep full metrics;
    watchlist names keep only the fields needed to mention them. Sized for a section agent, not the whole ledger."""
    inst = facts["instruments"]
    fresh = {f["symbol"]: f for f in facts["freshness"]}
    names = {}
    for sym, f in fresh.items():
        m = inst.get(sym, {})
        if "holding" in f["roles"] or "shortlist" in f["roles"] or "extra" in f["roles"]:
            names[sym] = {**f, **m}
        else:
            names[sym] = {**f, "close": m.get("close"), "stage": m.get("stage"), "asof_bar": m.get("asof_bar")}
    screen = facts.get("screen", {})
    return {
        "market": facts["market"], "asof": facts["asof"], "generated": facts["generated"], "source": facts["source"],
        "regime": facts["regime"], "macro": facts["macro"],
        "benchmarks_and_sectors": {k: v for k, v in inst.items() if v.get("kind") in ("index", "sector", "etf")},
        "screen_universe": screen.get("universe"),
        "bull_pick": screen.get("bull_pick"), "bear_pick": screen.get("bear_pick"),
        "names": names, "failures": facts["failures"], "stale_vs_asof": facts["stale_vs_asof"],
        "research_needs": facts["research_needs"], "research_file": facts["research_file"],
        "positions": consolidate_positions(facts["instruments"]) if POSITIONS else None,
    }


def update_manifest(run_dir, section, payload):
    path = os.path.join(run_dir, "manifest.json")
    data = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {}
    data[section] = payload
    json.dump(data, open(path, "w", encoding="utf-8"), indent=2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--market", required=True, choices=["US", "IN"])
    ap.add_argument("--date", help="session date YYYY-MM-DD (required for a build)")
    ap.add_argument("--extra")
    ap.add_argument("--screen", help="US: sp1500 (500+400+600, recommended) | sp500 ; IN: nifty500 ; or file:<path>")
    ap.add_argument("--show", help="comma list of symbols to print from a ledger given by --out")
    ap.add_argument("--run-dir", help="this run's private directory; output goes to <run-dir>/cache/")
    ap.add_argument("--out", help="explicit ledger path (required with --show)")
    ap.add_argument("--check-inputs", action="store_true", help="validate declared sources and exit (no network)")
    ap.add_argument("--allow-stale-holdings", action="store_true", help="build even if a holding is not current; the reason must be stated in the report")
    args = ap.parse_args()

    if args.check_inputs:
        roles, sources = load_sources(args.market)
        for src in sources:
            print(f"{src['id']:<22} {src['status']:<18} rows {src['rows']:<5} symbols {src['symbols']:<5} sha256 {str(src['sha256'])[:12]}")
        held = sorted(s for s, r in roles.items() if "holding" in r)
        print(f"holdings across sources: {len(held)} unique symbols")
        if args.run_dir:
            os.makedirs(args.run_dir, exist_ok=True)
            update_manifest(args.run_dir, "inputs", {"market": args.market, "sources": sources, "checked_at": dt.datetime.now().isoformat(timespec="seconds")})
            print(f"recorded in {os.path.join(args.run_dir, 'manifest.json')}")
        return

    if args.show:
        if not args.out:
            sys.exit("--show requires an explicit --out path; no implicit 'latest file' lookup.")
        facts = json.load(open(args.out))
        for s in args.show.split(","):
            print(s, json.dumps(facts["instruments"].get(s.strip().upper()), indent=1))
        return

    if not args.date or not args.run_dir:
        sys.exit("A build requires --date YYYY-MM-DD and --run-dir <RUN_DIR>.")
    cache = os.path.join(os.path.abspath(args.run_dir), "cache")
    os.makedirs(cache, exist_ok=True)

    facts = build(args)
    out = os.path.join(cache, f"facts_{args.market}_{facts['asof']}.json")
    json.dump(facts, open(out, "w"), indent=1)
    fp = os.path.join(cache, f"factpack_{args.market}_{facts['asof']}.json")
    json.dump(factpack(facts), open(fp, "w"), indent=1)
    update_manifest(os.path.abspath(args.run_dir), "ledger", {
        "market": args.market, "asof": facts["asof"], "generated": facts["generated"],
        "ledger_file": out, "ledger_sha256": sha256(out), "factpack_file": fp, "factpack_sha256": sha256(fp),
        "screen": args.screen, "allow_stale_holdings": args.allow_stale_holdings,
        "stale_vs_asof": facts["stale_vs_asof"], "failures": facts["failures"], "freshness": facts["freshness"]})
    update_manifest(os.path.abspath(args.run_dir), "inputs", {"market": args.market, "sources": facts["inputs"]})
    pos = consolidate_positions(facts["instruments"])
    pos_file = os.path.join(cache, f"positions_{args.market}_{facts['asof']}.json")
    json.dump(pos, open(pos_file, "w"), indent=1)
    update_manifest(os.path.abspath(args.run_dir), "positions", {"file": pos_file, "sha256": sha256(pos_file),
                    "accounts": pos["accounts"], "net_worth": pos["net_worth"],
                    "reconciliation": pos["reconciliation"]})
    print(f"wrote {out}\n  as-of {facts['asof']} | instruments {len(facts['instruments'])} | failed {len(facts['failures'])} | "
          f"stale {len(facts['stale_vs_asof'])} | regime: {facts['regime']['label']} | "
          f"breadth>50DMA: {facts['regime']['breadth_pct_above_50dma']} | distribution days: {facts['regime']['distribution_days_25']}")
    s = facts["screen"]
    if s["universe"]:
        print(f"  screen {s['universe']}: bull {len(s['bull'])} (+{len(s['bull_near'])} near, +{len(s['bull_relaxed'])} relaxed) | "
              f"bear {len(s['bear'])} (+{len(s['bear_near'])} near, +{len(s['bear_relaxed'])} relaxed)")
        for side in ("bull_pick", "bear_pick"):
            print(f"  {side}: " + " | ".join(f"{t} {len(v)}" for t, v in s[side].items()))
    if facts["failures"]:
        print("  FAILED (needs alternate source before N/A):", ", ".join(facts["failures"][:40]))
    print(f"  WEB RESEARCH REQUIRED ({len(facts['research_needs'])} items, see 'research_needs'); "
          f"record findings in {facts['research_file']}")


if __name__ == "__main__":
    main()
