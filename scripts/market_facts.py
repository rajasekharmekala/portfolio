#!/usr/bin/env python3
"""
Facts ledger builder: the single source of truth for every price, moving average,
RSI/ATR, volume multiple, Weinstein stage and regime label used by ALL report
sections (market intelligence + portfolio audit) for one market and one session.

Usage:
  python3 scripts/market_facts.py --market US [--date 2026-09-28] [--screen sp500]
  python3 scripts/market_facts.py --market IN --screen nifty500 --extra RELIANCE,TCS
  python3 scripts/market_facts.py --market US --show NVDA,VRT      # print cached facts

Output: scripts/.cache/facts_<MKT>_<YYYY-MM-DD>.json  (reused by the audit and the
market-intelligence run of the same date, and by scripts/validate_report.py --facts).
A ledger is built from real bars up to the session date; never copy/rename one to another date.
"""
import argparse
import datetime as dt
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
CACHE = os.path.join(ROOT, "scripts", ".cache")
OPTION_RE = re.compile(r"^[A-Z]{1,6}\d{6}[CP]\d{8}$")
TICKER_RE = re.compile(r"^[A-Z0-9][A-Z0-9&\-\.]{0,19}$")
# Zerodha symbol -> Yahoo symbol where they differ; extend via scripts/.cache/aliases.json
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

WORKBOOKS = {
    "US": [("googledrive/sheets/US_Portfolio_Holdings.xlsx", "Holdings", "holding"),
           ("googledrive/shortlist/US_Shortlist.xlsx", "Master_Shortlist", "shortlist"),
           ("googledrive/watchlist/US_Portfolio_Watchlist.xlsx", "Active_Watchlist", "watchlist")],
    "IN": [("googledrive/sheets/Zerodha_Holdings.xlsx", "Holdings", "holding"),
           ("googledrive/shortlist/Zerodha_Shortlist.xlsx", "Master_Shortlist", "shortlist"),
           ("googledrive/watchlist/Zerodha_Watchlist.xlsx", "Active_Watchlist", "watchlist")],
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
    # distribution days: down >= 0.2% on higher volume than the prior session, last 25 sessions
    dist = None
    if vol.iloc[-25:].sum() > 0:
        ch = c.pct_change().iloc[-25:]
        dist = int(((ch <= -0.002) & (vol.iloc[-25:] > vol.shift().iloc[-25:])).sum())
    return {
        "asof_bar": df.index[-1].strftime("%Y-%m-%d"),
        "close": close, "prev_close": at(c, 1),
        "chg_1d_pct": pct(1), "chg_1w_pct": pct(5), "chg_2w_pct": pct(10), "chg_1m_pct": pct(21),
        "sma20": at(s20), "sma50": s50v, "sma200": s200v,
        "sma50_10d_ago": s50p,
        "sma50_trend": None if s50p is None or s50v is None else ("RISING" if s50v > s50p else "FALLING/FLAT"),
        "rsi14": at(r), "atr14": atrv,
        "vol": int(vol.iloc[last]) if not math.isnan(vol.iloc[last]) else None,
        "vol_mult_20d": vmult,
        "swing_low_20d": swing_low_20d,
        "hi52": num(hi52), "lo52": num(lo52),
        "pct_from_52w_high": num((close / hi52 - 1) * 100),
        "delta_50dma_atr": num((close - s50v) / atrv) if s50v and atrv else None,
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


def workbook_symbols(market: str):
    import openpyxl
    out = {}
    for rel, sheet, role in WORKBOOKS[market]:
        path = os.path.join(ROOT, rel)
        if not os.path.exists(path):
            continue
        ws = openpyxl.load_workbook(path, read_only=True, data_only=True)[sheet]
        rows = ws.iter_rows(values_only=True)
        header = next(rows)
        col = header.index("Symbol")
        for row in rows:
            s = row[col]
            if s and isinstance(s, str) and TICKER_RE.match(s.strip().upper()) and not is_option(s):
                out.setdefault(s.strip().upper(), set()).add(role)
    return out


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


def build(args):
    market = args.market
    cfg = BENCH[market]
    alias_file = os.path.join(CACHE, "aliases.json")
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
    for yt, df in frames.items():
        if args.date:  # replay a past session: drop bars after the requested date
            df = df[df.index <= pd.Timestamp(args.date)]
        m = metrics(df)
        rep = ymap[yt]
        m.update({"yahoo": yt, "roles": sorted(roles.get(rep, []))})
        m["kind"] = ("index" if rep in cfg["indices"] else "sector" if rep in cfg["sectors"] else
                     "etf" if rep in cfg["etfs"] else "stock")
        inst[rep] = m

    primary_name = ymap[cfg["primary"]]
    asof = args.date or (inst.get(primary_name, {}).get("asof_bar")) or dt.date.today().isoformat()
    stale = sorted(k for k, v in inst.items() if v.get("asof_bar") and v["asof_bar"] < asof)

    # breadth from the screening universe when supplied, otherwise from the book/watchlist
    pool = [inst[s] for s in (universe or roles) if s in inst and inst[s].get("sma50")]
    breadth50 = num(100 * sum(1 for m in pool if m["close"] > m["sma50"]) / len(pool), 1) if pool else None
    breadth200 = num(100 * sum(1 for m in pool if m.get("sma200") and m["close"] > m["sma200"]) / len(pool), 1) if pool else None
    sec = {n: inst[n] for n in cfg["sectors"] if n in inst}
    p = inst.get(primary_name, {})
    if not p or p.get("error"):
        label = "N/A (benchmark series unavailable)"
    elif p["close"] > p["sma50"] > p["sma200"] and (breadth50 is None or breadth50 >= 55):
        label = "Uptrend (broad)"
    elif p["close"] > p["sma50"]:
        label = "Uptrend (narrow breadth)"
    elif p["close"] > p["sma200"]:
        label = "Correction (below 50-DMA, above 200-DMA)"
    else:
        label = "Downtrend"
    regime = {
        "label": label, "benchmark": primary_name, "breadth_pct_above_50dma": breadth50,
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
        "failures": sorted(failed), "stale_vs_asof": stale,
        "research_needs": render_research(market, asof, roles),
        "research_file": f"scripts/.cache/research_{market}_{asof}.json",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--market", required=True, choices=["US", "IN"])
    ap.add_argument("--date")
    ap.add_argument("--extra")
    ap.add_argument("--screen", help="US: sp1500 (500+400+600, recommended) | sp500 ; IN: nifty500 ; or file:<path>")
    ap.add_argument("--show", help="comma list of symbols to print from the cached ledger")
    ap.add_argument("--out")
    args = ap.parse_args()
    os.makedirs(CACHE, exist_ok=True)

    if args.show:
        path = args.out or sorted(f for f in os.listdir(CACHE) if f.startswith(f"facts_{args.market}_"))[-1]
        path = path if os.path.isabs(path) else os.path.join(CACHE, path)
        facts = json.load(open(path))
        for s in args.show.split(","):
            print(s, json.dumps(facts["instruments"].get(s.strip().upper()), indent=1))
        return

    facts = build(args)
    out = args.out or os.path.join(CACHE, f"facts_{args.market}_{facts['asof']}.json")
    json.dump(facts, open(out, "w"), indent=1)
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
