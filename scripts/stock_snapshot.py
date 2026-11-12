#!/usr/bin/env python3
"""
Deterministic Per-Stock Consumer Tool Snapshot & Watchlist Pruner (Zero LLM Math).

Pulls verified pre-computed indicators and valuation metrics from:
  1. TradingView Live Scanner Engine (daily/weekly SMAs & EMAs including 30-week SMA,
     RSI-14, Volume vs 10d/30d avg, ATR-14, Classic Pivots, Technical Ratings, TTM Multiples).
  2. TheWrap Stage 2 / Breakout Snapshot (data/views/stage2_<MKT>_latest.json):
     Sector Stage 2 density %, Weeks in Stage 2, RS %, Breakout Type, Volume Analysis.
  3. Screener.in (IN) / Finviz (US) Live Company Pages (via HTTP + optional Chrome DOM):
     ROCE/ROIC, P/E, Forward P/E, PEG, Book Value, Debt/Equity, Promoter/Insider holding,
     Quarterly Sales & Profit trajectory.
  4. Deterministic Stage 2 & No-FOMO Entry Timing Classification:
     - BUY_AT_CMP_NO_FOMO (Early Stage 2 / near support + reasonable valuation)
     - WAIT_FOR_SUPPORT_PULLBACK (In Stage 2, but extended above 10W EMA / 50D SMA -> limit order at support)
     - AT_STAGE2_SUPPORT_RETEST (Pulling back to rising 50D SMA / 30W SMA support)
     - AVOID_STAGE4_OR_BROKEN (Below falling 30W SMA & 200D SMA -> exit candidate)

Usage:
  .venv/bin/python scripts/stock_snapshot.py --market IN --symbols FSL IGIL EXIDEIND
  .venv/bin/python scripts/stock_snapshot.py --market IN --from-watchlist --from-holdings --out <RUN_DIR>/cache/snapshots_IN.json
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
ALIASES_FILE = ROOT / "scripts" / "config" / "aliases.json"
SCREENER_ALIASES_FILE = ROOT / "scripts" / "config" / "screener_aliases.json"

TV_COLUMNS = [
    "name",
    "description",
    "exchange",
    "sector",
    "industry",
    "close",
    "change",
    "volume",
    "average_volume_10d_calc",
    "average_volume_30d_calc",
    "RSI",
    "RSI|1W",
    "SMA10",
    "SMA20",
    "SMA50",
    "SMA200",
    "SMA30|1W",
    "EMA10",
    "EMA20",
    "EMA50",
    "EMA200",
    "EMA10|1W",
    "EMA40|1W",
    "ATR",
    "Recommend.All",
    "Recommend.MA",
    "Recommend.Other",
    "price_52_week_high",
    "price_52_week_low",
    "Perf.W",
    "Perf.1M",
    "Perf.3M",
    "Perf.6M",
    "Perf.Y",
    "Pivot.M.Classic.S1",
    "Pivot.M.Classic.Middle",
    "Pivot.M.Classic.R1",
    "market_cap_basic",
    "price_earnings_ttm",
    "price_book_fq",
    "debt_to_equity",
    "return_on_equity",
    "total_revenue_yoy_growth_ttm",
    "earnings_per_share_diluted_yoy_growth_ttm",
    "operating_margin_ttm",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    )
}


def _round(v: Any, digits: int = 2) -> Optional[float]:
    if v is None or isinstance(v, bool):
        return None
    try:
        return round(float(v), digits)
    except (ValueError, TypeError):
        return None


def _parse_float(s: Any) -> Optional[float]:
    if s is None:
        return None
    txt = re.sub(r"[,₹$%\s]", "", str(s))
    m = re.search(r"-?\d+(?:\.\d+)?", txt)
    return float(m.group(0)) if m else None


def load_aliases(market: str) -> Dict[str, str]:
    if not ALIASES_FILE.exists():
        return {}
    try:
        data = json.loads(ALIASES_FILE.read_text(encoding="utf-8"))
        return data.get(market, {})
    except Exception:
        return {}


def load_screener_aliases(market: str) -> Dict[str, str]:
    if not SCREENER_ALIASES_FILE.exists():
        return {}
    try:
        data = json.loads(SCREENER_ALIASES_FILE.read_text(encoding="utf-8"))
        return data.get(market, {})
    except Exception:
        return {}


def fetch_tradingview_batch(market: str, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
    """Query TradingView's official scanner API for exact technical & fundamental fields."""
    if not symbols:
        return {}
    region = "india" if market == "IN" else "america"
    url = f"https://scanner.tradingview.com/{region}/scan"
    aliases = load_aliases(market)

    # Build candidate tickers across primary exchanges for each symbol
    exchanges = ["NSE", "BSE"] if market == "IN" else ["NASDAQ", "NYSE", "AMEX"]
    tickers = []
    ticker_to_sym = {}
    for sym in symbols:
        clean_sym = aliases.get(sym, sym).replace(".NS", "").replace(".BO", "").upper()
        for ex in exchanges:
            t = f"{ex}:{clean_sym}"
            tickers.append(t)
            ticker_to_sym[t] = sym

    payload = {
        "symbols": {"tickers": tickers, "query": {"types": []}},
        "columns": TV_COLUMNS,
    }
    try:
        resp = requests.post(url, json=payload, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        rows = resp.json().get("data", [])
    except Exception as exc:
        print(f"[!] TradingView scan warning ({market}): {exc}", file=sys.stderr)
        return {}

    out: Dict[str, Dict[str, Any]] = {}
    # Prefer NSE over BSE for IN, and first matched exchange with highest volume for US
    for row in rows:
        t = row.get("s", "")
        sym = ticker_to_sym.get(t)
        if not sym:
            continue
        raw = dict(zip(TV_COLUMNS, row.get("d", [])))
        ex_prefix = t.split(":")[0]
        if sym in out:
            if market == "IN" and out[sym].get("_exchange_prefix") == "NSE":
                continue
        close = _round(raw.get("close"))
        hi52 = _round(raw.get("price_52_week_high"))
        lo52 = _round(raw.get("price_52_week_low"))
        vol = _round(raw.get("volume"), 0)
        avg30 = _round(raw.get("average_volume_30d_calc"), 0)
        vol_ratio = _round(vol / avg30, 2) if (vol and avg30 and avg30 > 0) else None
        pct_from_hi52 = _round((close / hi52 - 1.0) * 100.0, 2) if (close and hi52 and hi52 > 0) else None

        mcap_raw = raw.get("market_cap_basic")
        if market == "IN":
            # Convert INR to Crores (1 Cr = 1e7)
            mcap_display = _round(mcap_raw / 1e7, 2) if mcap_raw else None
            mcap_unit = "INR_Cr"
        else:
            # Convert USD to Billions (1B = 1e9)
            mcap_display = _round(mcap_raw / 1e9, 2) if mcap_raw else None
            mcap_unit = "USD_B"

        out[sym] = {
            "_exchange_prefix": ex_prefix,
            "tv_symbol": t,
            "tradingview_chart_url": f"https://www.tradingview.com/chart/?symbol={ex_prefix}%3A{raw.get('name', sym)}",
            "tradingview_technicals_url": f"https://www.tradingview.com/symbols/{ex_prefix}-{raw.get('name', sym)}/technicals/",
            "company_name": raw.get("description") or sym,
            "sector": raw.get("sector"),
            "industry": raw.get("industry"),
            "close": close,
            "change_1d_pct": _round(raw.get("change")),
            "perf_1w_pct": _round(raw.get("Perf.W")),
            "perf_1m_pct": _round(raw.get("Perf.1M")),
            "perf_3m_pct": _round(raw.get("Perf.3M")),
            "perf_6m_pct": _round(raw.get("Perf.6M")),
            "perf_1y_pct": _round(raw.get("Perf.Y")),
            "high_52w": hi52,
            "low_52w": lo52,
            "pct_from_52w_high": pct_from_hi52,
            "rsi_14_daily": _round(raw.get("RSI")),
            "rsi_14_weekly": _round(raw.get("RSI|1W")),
            "atr_14": _round(raw.get("ATR")),
            "sma10": _round(raw.get("SMA10")),
            "sma20": _round(raw.get("SMA20")),
            "sma50": _round(raw.get("SMA50")),
            "sma200": _round(raw.get("SMA200")),
            "sma30_weekly": _round(raw.get("SMA30|1W")),
            "ema10": _round(raw.get("EMA10")),
            "ema20": _round(raw.get("EMA20")),
            "ema50": _round(raw.get("EMA50")),
            "ema200": _round(raw.get("EMA200")),
            "ema10_weekly": _round(raw.get("EMA10|1W")),
            "ema40_weekly": _round(raw.get("EMA40|1W")),
            "volume": vol,
            "avg_vol_10d": _round(raw.get("average_volume_10d_calc"), 0),
            "avg_vol_30d": avg30,
            "vol_ratio_vs_30d": vol_ratio,
            "pivot_s1": _round(raw.get("Pivot.M.Classic.S1")),
            "pivot_middle": _round(raw.get("Pivot.M.Classic.Middle")),
            "pivot_r1": _round(raw.get("Pivot.M.Classic.R1")),
            "tv_rating_overall": _round(raw.get("Recommend.All"), 2),
            "tv_rating_ma": _round(raw.get("Recommend.MA"), 2),
            "tv_rating_oscillators": _round(raw.get("Recommend.Other"), 2),
            "market_cap": mcap_display,
            "market_cap_unit": mcap_unit,
            "pe_ttm": _round(raw.get("price_earnings_ttm")),
            "pb_fq": _round(raw.get("price_book_fq")),
            "debt_to_equity": _round(raw.get("debt_to_equity")),
            "roe_pct": _round(raw.get("return_on_equity")),
            "revenue_yoy_growth_ttm_pct": _round(raw.get("total_revenue_yoy_growth_ttm")),
            "eps_yoy_growth_ttm_pct": _round(raw.get("earnings_per_share_diluted_yoy_growth_ttm")),
            "operating_margin_ttm_pct": _round(raw.get("operating_margin_ttm")),
        }
    return out


def _extract_screener_table(soup: BeautifulSoup, section_id: str) -> Dict[str, Any]:
    """Extract headers and rows from a Screener.in data-table section."""
    sec = soup.select_one(f"#{section_id}")
    if not sec:
        return {}
    tbl = sec.select_one("table.data-table")
    if not tbl:
        return {}
    headers = [re.sub(r"\s+", " ", th.get_text(" ", strip=True)).strip() for th in tbl.select("thead th")]
    rows: Dict[str, List[str]] = {}
    for tr in tbl.select("tbody tr"):
        cells = [re.sub(r"\s+", " ", td.get_text(" ", strip=True)).strip() for td in tr.select("td, th")]
        if len(cells) >= 2:
            label = cells[0].rstrip("+").strip()
            if label:
                rows[label] = cells[1:]
    return {"headers": headers[1:] if len(headers) > 1 else headers, "rows": rows}


def _build_screener_waterfall_100(pl_tbl: Dict[str, Any], cf_tbl: Dict[str, Any]) -> Dict[str, Any]:
    """Compute a period-matched ₹100 waterfall from Screener's latest common audited FY column."""
    pl_headers = pl_tbl.get("headers") or []
    cf_headers = cf_tbl.get("headers") or []
    pl_rows = pl_tbl.get("rows") or {}
    cf_rows = cf_tbl.get("rows") or {}
    common = [h for h in pl_headers if h in cf_headers and h.upper() != "TTM"]
    if not common:
        return {}
    period = common[-1]
    p_idx = pl_headers.index(period)
    c_idx = cf_headers.index(period)

    def cell(rows_map: Dict[str, List[str]], idx: int, *names: str) -> Optional[float]:
        for name in names:
            vals = rows_map.get(name)
            if vals and idx < len(vals):
                v = _parse_float(vals[idx])
                if v is not None:
                    return v
        return None

    sales = cell(pl_rows, p_idx, "Sales", "Revenue", "Financing Profit")
    if not sales or sales <= 0:
        return {}
    expenses = cell(pl_rows, p_idx, "Expenses", "Operating Expenses")
    op_profit = cell(pl_rows, p_idx, "Operating Profit", "Financing Profit")
    other_inc = cell(pl_rows, p_idx, "Other Income") or 0.0
    interest = cell(pl_rows, p_idx, "Interest") or 0.0
    depr = cell(pl_rows, p_idx, "Depreciation") or 0.0
    pbt = cell(pl_rows, p_idx, "Profit before tax")
    net_profit = cell(pl_rows, p_idx, "Net Profit")
    cfo = cell(cf_rows, c_idx, "Cash from Operating Activity")
    cfi = cell(cf_rows, c_idx, "Cash from Investing Activity")

    def per100(val: Optional[float]) -> Optional[float]:
        return _round((val / sales) * 100.0, 2) if val is not None else None

    return {
        "period": period,
        "unit": "INR_Cr",
        "sales": sales,
        "expenses": expenses,
        "operating_profit": op_profit,
        "other_income": other_inc,
        "interest": interest,
        "depreciation": depr,
        "profit_before_tax": pbt,
        "net_profit": net_profit,
        "cfo": cfo,
        "investing_cash_flow": cfi,
        "per_100_revenue": {
            "revenue": 100.0,
            "operating_expenses": per100(-abs(expenses)) if expenses is not None else None,
            "operating_ebitda": per100(op_profit),
            "depreciation": per100(-abs(depr)),
            "interest": per100(-abs(interest)),
            "other_income": per100(other_inc),
            "profit_before_tax": per100(pbt),
            "net_profit": per100(net_profit),
            "cfo": per100(cfo),
            "investing_cash_flow": per100(cfi),
        },
    }


def fetch_screener_in(symbol: str) -> Dict[str, Any]:
    """Extract top ratios, 10-year financial tables, and quarterly highlights from Screener.in for an Indian symbol."""
    screener_symbol = load_screener_aliases("IN").get(symbol.upper(), symbol)
    for suffix in ("consolidated/", ""):
        url = f"https://www.screener.in/company/{screener_symbol}/{suffix}"
        try:
            r = requests.get(url, headers=HEADERS, timeout=12)
            if r.status_code != 200:
                continue
            soup = BeautifulSoup(r.text, "html.parser")
            ratios = {}
            for li in soup.select("#top-ratios li"):
                name_el = li.select_one(".name")
                val_el = li.select_one(".value, .number")
                if name_el and val_el:
                    k = re.sub(r"\s+", " ", name_el.get_text(" ", strip=True)).strip()
                    v = re.sub(r"\s+", " ", val_el.get_text(" ", strip=True)).strip()
                    if _parse_float(v) is None:
                        continue
                    ratios[k] = v
            if not ratios:
                continue
            pros = [li.get_text(" ", strip=True) for li in soup.select(".pros ul li")[:6]]
            cons = [li.get_text(" ", strip=True) for li in soup.select(".cons ul li")[:6]]
            about_el = soup.select_one(".company-profile .about p") or soup.select_one(".about p")
            about_text = re.sub(r"\s+", " ", about_el.get_text(" ", strip=True)).strip() if about_el else ""
            peer_links = [re.sub(r"\s+", " ", a.get_text(" ", strip=True)).strip()
                          for a in soup.select("#peers p.sub a") if a.get_text(strip=True)]
            sector_name = peer_links[0] if peer_links else None
            industry_name = peer_links[-1] if len(peer_links) >= 2 else sector_name
            tables = {
                "quarters": _extract_screener_table(soup, "quarters"),
                "profit_loss": _extract_screener_table(soup, "profit-loss"),
                "balance_sheet": _extract_screener_table(soup, "balance-sheet"),
                "cash_flow": _extract_screener_table(soup, "cash-flow"),
                "ratios": _extract_screener_table(soup, "ratios"),
                "shareholding": _extract_screener_table(soup, "shareholding"),
            }
            return {
                "source_url": url,
                "about": about_text,
                "sector": sector_name,
                "industry": industry_name,
                "ratios": ratios,
                "roce_pct": _parse_float(ratios.get("ROCE")),
                "roe_pct": _parse_float(ratios.get("ROE")),
                "stock_pe": _parse_float(ratios.get("Stock P/E")),
                "book_value": _parse_float(ratios.get("Book Value")),
                "dividend_yield_pct": _parse_float(ratios.get("Dividend Yield")),
                "pros": pros,
                "cons": cons,
                "tables": tables,
                "latest_waterfall_100": _build_screener_waterfall_100(tables["profit_loss"], tables["cash_flow"]),
            }
        except Exception:
            continue
    return {"source_url": f"https://www.screener.in/company/{screener_symbol}/", "ratios": {}}


def fetch_finviz_us(symbol: str) -> Dict[str, Any]:
    """Extract valuation and momentum ratios from Finviz for a US symbol."""
    url = f"https://finviz.com/quote.ashx?t={symbol}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code != 200:
            return {"source_url": url, "ratios": {}}
        soup = BeautifulSoup(r.text, "html.parser")
        ratios = {}
        for tr in soup.select("table.snapshot-table2 tr"):
            tds = [td.get_text(" ", strip=True) for td in tr.select("td")]
            for i in range(0, len(tds) - 1, 2):
                if tds[i]:
                    ratios[tds[i]] = tds[i + 1]
        sector_el = soup.select_one('a[href*="f=sec_"]')
        ind_el = soup.select_one('a[href*="f=ind_"]')
        return {
            "source_url": url,
            "sector": sector_el.get_text(" ", strip=True) if sector_el else None,
            "industry": ind_el.get_text(" ", strip=True) if ind_el else None,
            "ratios": ratios,
            "forward_pe": _parse_float(ratios.get("Forward P/E")),
            "peg": _parse_float(ratios.get("PEG")),
            "ps": _parse_float(ratios.get("P/S")),
            "pfcf": _parse_float(ratios.get("P/FCF")),
            "roic_pct": _parse_float(ratios.get("ROIC") or ratios.get("ROI")),
            "eps_qq_pct": _parse_float(ratios.get("EPS Q/Q")),
            "sales_qq_pct": _parse_float(ratios.get("Sales Q/Q")),
            "target_price": _parse_float(ratios.get("Target Price")),
            "short_float_pct": _parse_float(ratios.get("Short Float")),
        }
    except Exception:
        return {"source_url": url, "ratios": {}}


def load_stage2_context(market: str, stage2_path: Optional[str] = None) -> Dict[str, Any]:
    path = Path(stage2_path) if stage2_path else ROOT / "data" / "views" / f"stage2_{market}_latest.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def match_stage2_symbol(symbol: str, market: str, tv: Dict[str, Any], s2_data: Dict[str, Any]) -> Dict[str, Any]:
    """Cross-reference symbol and its industry against TheWrap Stage 2 / US Market Data snapshot."""
    if not s2_data:
        return {"stage2_snapshot_available": False}

    sector_ranks = {}
    for idx, s in enumerate(s2_data.get("strongest_sectors", []), 1):
        sec_name = (s.get("sector") or "").strip().lower()
        if sec_name:
            sector_ranks[sec_name] = {
                "rank": idx,
                "sector": s.get("sector"),
                "breadth_pct": s.get("pct_in_stage2") if market == "IN" else s.get("pct_outperforming_sp500"),
            }

    if market == "IN":
        new_syms = {r.get("TradingView Code", "").upper(): r for r in s2_data.get("new_additions_this_week", [])}
        top25_syms = {r.get("TradingView Code", "").upper(): r for r in s2_data.get("top_25_stage2", [])}
        removed_syms = {
            r.get("TradingView Code", "").upper()
            for r in s2_data.get("stage2_universe", []) + s2_data.get("removed_this_week", [])
            if r.get("Stage2 Status", "").strip().casefold() == "removed"
        }
        uni_syms = {
            r.get("TradingView Code", "").upper(): r
            for r in s2_data.get("stage2_universe", [])
            if r.get("Stage2 Status", "").strip().casefold() != "removed"
        }
        row = None if symbol in removed_syms else (uni_syms.get(symbol) or new_syms.get(symbol) or top25_syms.get(symbol))
        if row:
            ind = (row.get("Industry") or "").strip()
            sec_info = sector_ranks.get(ind.lower(), {})
            return {
                "stage2_snapshot_available": True,
                "in_thewrap_stage2": True,
                "is_new_addition_this_week": symbol in new_syms,
                "is_top_25_leader": symbol in top25_syms,
                "thewrap_industry": ind,
                "sector_stage2_density_pct": sec_info.get("breadth_pct"),
                "sector_rank": sec_info.get("rank"),
                "rs_pct": _parse_float(row.get("Relative Strength %")),
                "weeks_in_stage2": _parse_float(row.get("Weeks")),
                "stage2_return_pct": _parse_float(row.get("% Return")),
                "avg_weekly_vol_cr": _parse_float(row.get("Avg Weekly Vol (in cr.)")),
                "asm_status": row.get("ASM ESM GSM") or row.get("ASM") or None,
            }
        return {
            "stage2_snapshot_available": True,
            "in_thewrap_stage2": False,
            "is_new_addition_this_week": False,
            "is_top_25_leader": False,
        }
    else:
        bo_syms = {r.get("Symbol", "").upper(): r for r in s2_data.get("breakout_scanner", [])}
        vol_syms = {r.get("Symbol", "").upper(): r for r in s2_data.get("volume_scanner_leaders", [])}
        ind_matrix = {
            (r.get("Industry") or "").strip().lower(): r for r in s2_data.get("industry_breadth_matrix", [])
        }
        bo_row = bo_syms.get(symbol)
        vol_row = vol_syms.get(symbol)
        ind_name = (
            (bo_row or {}).get("Industry")
            or (vol_row or {}).get("Industry")
            or tv.get("industry")
            or ""
        ).strip()
        sec_info = sector_ranks.get(ind_name.lower(), {})
        ind_row = ind_matrix.get(ind_name.lower(), {})
        return {
            "stage2_snapshot_available": True,
            "thewrap_industry": ind_name,
            "sector_outperforming_sp500_pct": sec_info.get("breadth_pct"),
            "sector_rank": sec_info.get("rank"),
            "industry_pct_above_200d_ema": _parse_float(ind_row.get("% Above 200D EMA")),
            "industry_pct_above_50d_ema": _parse_float(ind_row.get("% Above 50D EMA")),
            "breakout_type": (bo_row or {}).get("Breakout Type", "None"),
            "volume_signal": (vol_row or {}).get("Volume Analysis", "Normal"),
        }


def evaluate_stage2_and_entry_posture(
    tv: Dict[str, Any],
    s2: Dict[str, Any],
    val_card: Dict[str, Any],
    market: str,
) -> Dict[str, Any]:
    """
    Deterministic Stage 2 + Valuation + No-FOMO Entry Timing Evaluator.
    Uses TradingView's pre-computed moving averages (30-week SMA, 10-week EMA, 50-day SMA, 200-day SMA)
    and RSI without any LLM math.

    The output `technical_timing_gate` is a *ceiling* on entry posture, never a
    buy signal: the business, valuation and management evidence must earn the
    call. It can clear a setup for consideration (`CLEAR_FOR_CONSIDERATION`),
    cap an extended/unverified one at a support pullback (`CAP_WAIT_FOR_SUPPORT`),
    or cap a broken one at avoidance (`CAP_REJECTED`). It never returns a verdict.
    """
    close = tv.get("close")
    sma50 = tv.get("sma50")
    sma200 = tv.get("sma200")
    sma30w = tv.get("sma30_weekly") or sma200
    ema10w = tv.get("ema10_weekly") or tv.get("ema50") or sma50
    ema20d = tv.get("ema20") or tv.get("sma20")
    rsi = tv.get("rsi_14_daily")
    atr = tv.get("atr_14")

    if close is None:
        return {
            "weinstein_stage": "UNKNOWN",
            "entry_timing_posture": "DATA_UNAVAILABLE",
            "technical_timing_gate": "DATA_UNAVAILABLE",
        }

    ext_10w_pct = _round((close / ema10w - 1.0) * 100.0, 2) if (ema10w and ema10w > 0) else None
    ext_50d_pct = _round((close / sma50 - 1.0) * 100.0, 2) if (sma50 and sma50 > 0) else None
    ext_30w_pct = _round((close / sma30w - 1.0) * 100.0, 2) if (sma30w and sma30w > 0) else None

    # TheWrap membership is an industry context signal, not a stock-stage
    # verdict. Classify the stock from its own price and moving averages.
    if sma30w and sma50 and close >= sma30w and close >= sma50 * 0.98:
        stage = "STAGE_2"
    elif sma30w and close >= sma30w and sma50 and close < sma50:
        stage = "STAGE_3"  # Pullback / consolidation above 30-week / 200-day average
    elif sma30w and close < sma30w and (tv.get("perf_1m_pct") or 0) > 0 and (rsi or 0) >= 48:
        stage = "STAGE_1"  # Basing / turning up from floor
    else:
        stage = "STAGE_4"  # Below 30-week & 50-day moving averages

    # Compute support zone & invalidation stop from TradingView moving averages
    support_anchors = [x for x in (ema20d, sma50, ema10w, tv.get("pivot_s1")) if x is not None and x <= close]
    nearest_support = max(support_anchors) if support_anchors else (sma50 or sma30w or close * 0.92)
    structural_floor = min([x for x in (sma50, sma30w) if x is not None] or [close * 0.90])
    stop_buffer = (0.5 * atr) if atr else (structural_floor * 0.03)
    invalidation_stop = _round(min(nearest_support, structural_floor) - stop_buffer, 2)
    support_zone_low = _round(min(nearest_support, ema10w or nearest_support) * 0.985, 2)
    support_zone_high = _round(nearest_support * 1.015, 2)

    # Valuation sanity check
    pe = tv.get("pe_ttm") if tv.get("pe_ttm") is not None else val_card.get("stock_pe")
    fwd_pe = val_card.get("forward_pe")
    peg = val_card.get("peg")
    rev_g = tv.get("revenue_yoy_growth_ttm_pct") if tv.get("revenue_yoy_growth_ttm_pct") is not None else val_card.get("sales_qq_pct")
    valuation_note = "Valuation unavailable" if pe is None or rev_g is None else "Reasonable / In-line"
    valuation_stretched = False
    if pe and pe > 85 and (rev_g is None or rev_g < 25):
        valuation_note = f"Rich trailing multiple (P/E {pe:.1f}x vs growth)"
        valuation_stretched = True
    elif peg and peg > 3.0:
        valuation_note = f"Elevated PEG ({peg:.2f}x)"
        valuation_stretched = True
    elif pe and pe < 25 and (rev_g or 0) >= 15:
        valuation_note = f"Attractive GARP valuation (P/E {pe:.1f}x with {rev_g:.1f}% revenue growth)"

    # No-FOMO Entry Timing Decision
    weeks = s2.get("weeks_in_stage2")
    is_extended = (
        (ema10w is not None and ema10w > 0 and close / ema10w > 1.10)
        or (sma50 is not None and sma50 > 0 and close / sma50 > 1.12)
        or (rsi is not None and rsi > 73.0)
    )
    entry_inputs_available = (all(x is not None for x in (tv.get("ema10_weekly"), sma50, rsi, pe, rev_g))
                              and tv["ema10_weekly"] > 0 and sma50 > 0 and pe > 0)

    if stage == "STAGE_4":
        posture = "AVOID_STAGE4_OR_BROKEN"
        gate = "CAP_REJECTED"
        rationale = (
            f"Below 30-week SMA ({sma30w}) and 50-day SMA ({sma50}) with weak trend structure. "
            "Technical ceiling: avoid for new entries until a Stage 1 base and Stage 2 breakout form."
        )
    elif stage == "STAGE_2" and not is_extended and not valuation_stretched and entry_inputs_available:
        posture = "BUY_AT_CMP_NO_FOMO"
        gate = "CLEAR_FOR_CONSIDERATION"
        wk_str = f" (Week {int(weeks)} in Stage 2)" if weeks else ""
        rationale = (
            f"Confirmed Stage 2 uptrend{wk_str}, trading within a non-extended {ext_10w_pct or 0:+.1f}% of its "
            f"10-week EMA ({ema10w}) with RSI {rsi} and {valuation_note.lower()}. No technical objection to "
            "entry at CMP, but the buy case must be earned by the business, valuation and management evidence."
        )
    elif stage == "STAGE_2":
        posture = "WAIT_FOR_SUPPORT_PULLBACK"
        gate = "CAP_WAIT_FOR_SUPPORT"
        rationale = (
            f"Strong Stage 2 trend, but extended ({ext_10w_pct or 0:+.1f}% above 10-week EMA, RSI {rsi}) "
            f"or valuation or entry inputs require verification ({valuation_note}). Technical ceiling: do not chase; "
            f"wait for a pullback to support zone {support_zone_low}–{support_zone_high}."
        )
    elif stage in ("STAGE_3", "STAGE_1"):
        posture = "WAIT_FOR_SUPPORT_RETEST"
        gate = "CAP_WAIT_FOR_SUPPORT"
        rationale = (
            f"Consolidating / pulling back near 30-week SMA ({sma30w}) and 50-day SMA ({sma50}). "
            f"Technical ceiling: wait; reassess only if support holds in {support_zone_low}–{support_zone_high} and "
            "volume expands on the turn."
        )
    else:
        posture = "WAIT_FOR_SUPPORT_PULLBACK"
        gate = "CAP_WAIT_FOR_SUPPORT"
        rationale = "Monitor for a low-risk support entry."

    return {
        "weinstein_stage": stage,
        "entry_timing_posture": posture,
        "technical_timing_gate": gate,
        "extension_from_10w_ema_pct": ext_10w_pct,
        "extension_from_50d_sma_pct": ext_50d_pct,
        "extension_from_30w_sma_pct": ext_30w_pct,
        "nearest_support": _round(nearest_support, 2),
        "support_buy_zone": [support_zone_low, support_zone_high],
        "invalidation_stop": invalidation_stop,
        "valuation_assessment": valuation_note,
        "summary_rationale": rationale,
    }


def collect_symbols_from_records(market: str, from_wl: bool, from_sl: bool, from_hold: bool) -> List[str]:
    syms: List[str] = []
    if from_wl:
        wl_path = ROOT / "data" / "watchlist" / f"{market}.json"
        if wl_path.exists():
            wl = json.loads(wl_path.read_text(encoding="utf-8"))
            for row in wl.get("active", []):
                if row.get("symbol") and row["symbol"] not in syms:
                    syms.append(row["symbol"])
    if from_sl:
        sl_path = ROOT / "data" / "shortlist" / f"{market}.json"
        if sl_path.exists():
            sl = json.loads(sl_path.read_text(encoding="utf-8"))
            rows = sl.get("active")
            if not isinstance(rows, list):
                rows = [row for sheet_rows in (sl.get("sheets") or {}).values()
                        if isinstance(sheet_rows, list) for row in sheet_rows]
            for row in rows:
                if isinstance(row, dict) and row.get("symbol") and row["symbol"] not in syms:
                    syms.append(row["symbol"])
    if from_hold:
        acc_dir = ROOT / "data" / "accounts" / market
        if acc_dir.exists():
            qty_map: Dict[str, float] = {}
            for p in acc_dir.glob("*.transactions.jsonl"):
                for line in p.read_text(encoding="utf-8").splitlines():
                    if not line.strip():
                        continue
                    tx = json.loads(line)
                    s = tx.get("symbol")
                    if not s:
                        continue
                    q = float(tx.get("quantity") or 0)
                    if tx.get("type") in ("opening", "buy", "split"):
                        qty_map[s] = qty_map.get(s, 0.0) + q
                    elif tx.get("type") == "sell":
                        qty_map[s] = qty_map.get(s, 0.0) - q
            for s, q in qty_map.items():
                if q > 1e-6 and s not in syms:
                    syms.append(s)
    return syms


_BLIND_DROP_RATIO_RE = re.compile(
    r"price|p/e|peg|p/s|p/b|p/fcf|market\s*cap|high|low|52w|rsi|sma|ema|perf|target|beta|atr|volat",
    re.I,
)
_BLIND_DROP_PROS_CONS_RE = re.compile(r"trading at|times its book|p/e|market cap", re.I)


def _strip_price_fields_for_blind_pass(val_card: Dict[str, Any]) -> Dict[str, Any]:
    """Return only price-blind operating, profitability, and statement fields for Pass 1."""
    raw_ratios = val_card.get("ratios") or {}
    blind_ratios = {k: v for k, v in raw_ratios.items() if not _BLIND_DROP_RATIO_RE.search(k)}
    out: Dict[str, Any] = {
        "source_url": val_card.get("source_url"),
        "sector": val_card.get("sector"),
        "industry": val_card.get("industry"),
        "ratios": blind_ratios,
    }
    if val_card.get("about"):
        out["about"] = val_card["about"]
    for key in ("roce_pct", "roe_pct", "roic_pct", "dividend_yield_pct", "eps_qq_pct", "sales_qq_pct"):
        if key in val_card and val_card[key] is not None:
            out[key] = val_card[key]
    for key in ("pros", "cons"):
        if isinstance(val_card.get(key), list):
            out[key] = [item for item in val_card[key] if not _BLIND_DROP_PROS_CONS_RE.search(str(item))]
    if val_card.get("tables"):
        out["tables"] = val_card["tables"]
    if val_card.get("latest_waterfall_100"):
        out["latest_waterfall_100"] = val_card["latest_waterfall_100"]
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--market", choices=["IN", "US"], required=True)
    parser.add_argument("--symbols", nargs="*", default=[], help="Explicit symbols to snapshot")
    parser.add_argument("--from-watchlist", action="store_true", help="Include all active watchlist symbols")
    parser.add_argument("--from-shortlist", action="store_true", help="Include all shortlist symbols")
    parser.add_argument("--from-holdings", action="store_true", help="Include all current holding symbols")
    parser.add_argument("--stage2-file", default=None, help="Path to stage2_<MKT>_latest.json")
    parser.add_argument("--skip-web-card", action="store_true", help="Skip per-symbol Screener/Finviz HTTP fetch for fast bulk scan")
    parser.add_argument("--blind-only", action="store_true", help="Fetch only price-blind operating & financial statement data (strips prices, multiples, and Stage 2 posture)")
    parser.add_argument("--out", default=None, help="Output JSON path")
    args = parser.parse_args()

    market = args.market.upper()
    symbols = list(dict.fromkeys([s.upper() for s in args.symbols]))
    explicit_symbols = set(symbols)
    if args.blind_only:
        if not symbols:
            print("--blind-only requires explicit --symbols.", file=sys.stderr)
            sys.exit(1)
        blind_map: Dict[str, Any] = {}
        for sym in symbols:
            raw_card = fetch_screener_in(sym) if market == "IN" else fetch_finviz_us(sym)
            blind_map[sym] = {
                "symbol": sym,
                "market": market,
                "retrieved_at": dt.datetime.now().isoformat(timespec="seconds"),
                "fundamental_card": _strip_price_fields_for_blind_pass(raw_card),
            }
        output = {
            "mode": "blind_fundamentals",
            "market": market,
            "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
            "symbol_count": len(blind_map),
            "snapshots": blind_map,
        }
        if args.out:
            out_p = Path(args.out)
            out_p.parent.mkdir(parents=True, exist_ok=True)
            out_p.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            print(f"[+] Wrote price-blind fundamentals for {len(blind_map)} symbols to {args.out}")
        else:
            print(json.dumps(output, indent=2, ensure_ascii=False))
        return

    stage2_data = load_stage2_context(market, args.stage2_file)
    if args.from_watchlist or args.from_shortlist or args.from_holdings:
        extra = collect_symbols_from_records(
            market,
            from_wl=args.from_watchlist,
            from_sl=args.from_shortlist,
            from_hold=args.from_holdings,
        )
        for s in extra:
            if s not in symbols:
                symbols.append(s)
    if not symbols:
        print("No symbols specified.", file=sys.stderr)
        sys.exit(1)

    print(f"[*] Fetching TradingView technical & fundamental snapshot for {len(symbols)} {market} symbols...")
    tv_map = fetch_tradingview_batch(market, symbols)
    s2_data = stage2_data

    snapshots: Dict[str, Any] = {}
    for sym in symbols:
        tv = tv_map.get(sym, {})
        s2 = match_stage2_symbol(sym, market, tv, s2_data)
        if not args.skip_web_card and (sym in explicit_symbols or len(symbols) <= 25):
            val_card = fetch_screener_in(sym) if market == "IN" else fetch_finviz_us(sym)
        else:
            val_card = {
                "source_url": f"https://www.screener.in/company/{sym}/" if market == "IN" else f"https://finviz.com/quote.ashx?t={sym}"
            }
        ev = evaluate_stage2_and_entry_posture(tv, s2, val_card, market)
        snapshots[sym] = {
            "symbol": sym,
            "market": market,
            "retrieved_at": dt.datetime.now().isoformat(timespec="seconds"),
            "tradingview": tv,
            "thewrap_stage2": s2,
            "fundamental_card": val_card,
            "stage2_evaluation": ev,
        }

    output = {
        "market": market,
        "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
        "symbol_count": len(snapshots),
        "snapshots": snapshots,
    }

    if args.out:
        out_p = Path(args.out)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"[+] Wrote snapshot for {len(snapshots)} symbols to {args.out}")
    else:
        print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
