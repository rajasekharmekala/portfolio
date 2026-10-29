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
     - AVOID_STAGE4_OR_BROKEN (Below falling 30W SMA & 200D SMA -> prune from watchlist / exit candidate)

Usage:
  .venv/bin/python scripts/stock_snapshot.py --market IN --symbols FSL IGIL EXIDEIND
  .venv/bin/python scripts/stock_snapshot.py --market IN --from-watchlist --from-holdings --out <RUN_DIR>/cache/snapshots_IN.json
  .venv/bin/python scripts/stock_snapshot.py --market IN --prune-watchlist
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


def fetch_screener_in(symbol: str) -> Dict[str, Any]:
    """Extract top ratios and quarterly highlights from Screener.in for an Indian symbol."""
    for suffix in ("consolidated/", ""):
        url = f"https://www.screener.in/company/{symbol}/{suffix}"
        try:
            r = requests.get(url, headers=HEADERS, timeout=10)
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
                    ratios[k] = v
            if not ratios:
                continue
            # Also extract pros/cons if available
            pros = [li.get_text(" ", strip=True) for li in soup.select(".pros ul li")[:4]]
            cons = [li.get_text(" ", strip=True) for li in soup.select(".cons ul li")[:4]]
            return {
                "source_url": url,
                "ratios": ratios,
                "roce_pct": _parse_float(ratios.get("ROCE")),
                "roe_pct": _parse_float(ratios.get("ROE")),
                "stock_pe": _parse_float(ratios.get("Stock P/E")),
                "book_value": _parse_float(ratios.get("Book Value")),
                "dividend_yield_pct": _parse_float(ratios.get("Dividend Yield")),
                "pros": pros,
                "cons": cons,
            }
        except Exception:
            continue
    return {"source_url": f"https://www.screener.in/company/{symbol}/", "ratios": {}}


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
        return {
            "source_url": url,
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
        uni_syms = {r.get("TradingView Code", "").upper(): r for r in s2_data.get("stage2_universe", [])}
        row = uni_syms.get(symbol) or new_syms.get(symbol) or top25_syms.get(symbol)
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
                "asm_status": row.get("ASM") or row.get("Stage2 Status"),
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
    """
    close = tv.get("close")
    sma50 = tv.get("sma50")
    sma200 = tv.get("sma200")
    sma30w = tv.get("sma30_weekly") or sma200
    ema10w = tv.get("ema10_weekly") or tv.get("ema50") or sma50
    ema20d = tv.get("ema20") or tv.get("sma20")
    rsi = tv.get("rsi_14_daily")
    atr = tv.get("atr_14")
    in_wrap_s2 = bool(s2.get("in_thewrap_stage2"))

    if close is None:
        return {
            "weinstein_stage": "UNKNOWN",
            "entry_timing_posture": "DATA_UNAVAILABLE",
            "action_recommendation": "RESEARCH_REQUIRED",
        }

    ext_10w_pct = _round((close / ema10w - 1.0) * 100.0, 2) if (ema10w and ema10w > 0) else None
    ext_50d_pct = _round((close / sma50 - 1.0) * 100.0, 2) if (sma50 and sma50 > 0) else None
    ext_30w_pct = _round((close / sma30w - 1.0) * 100.0, 2) if (sma30w and sma30w > 0) else None

    # Determine Weinstein Stage
    if in_wrap_s2 or (sma30w and sma50 and close > sma30w and close >= sma50 * 0.98):
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
    pe = tv.get("pe_ttm") or val_card.get("stock_pe")
    fwd_pe = val_card.get("forward_pe")
    peg = val_card.get("peg")
    rev_g = tv.get("revenue_yoy_growth_ttm_pct") or val_card.get("sales_qq_pct")
    valuation_note = "Reasonable / In-line"
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
        (ext_10w_pct is not None and ext_10w_pct > 12.0)
        or (ext_50d_pct is not None and ext_50d_pct > 14.0)
        or (rsi is not None and rsi > 74.0)
    )

    if stage == "STAGE_4":
        posture = "AVOID_STAGE4_OR_BROKEN"
        verdict = "REJECTED"
        rationale = (
            f"Below 30-week SMA ({sma30w}) and 50-day SMA ({sma50}) with weak trend structure. "
            "Prune from watchlist / avoid until Stage 1 base and Stage 2 breakout form."
        )
    elif stage == "STAGE_2" and not is_extended and not valuation_stretched:
        posture = "BUY_AT_CMP_NO_FOMO"
        verdict = "IMMEDIATE_BUY"
        wk_str = f" (Week {int(weeks)} in Stage 2)" if weeks else ""
        rationale = (
            f"Confirmed Stage 2 uptrend{wk_str}, trading within a non-extended {ext_10w_pct or 0:+.1f}% of its "
            f"10-week EMA ({ema10w}) with RSI {rsi} and {valuation_note.lower()}."
        )
    elif stage == "STAGE_2" and (is_extended or valuation_stretched):
        posture = "WAIT_FOR_SUPPORT_PULLBACK"
        verdict = "WAIT_FOR_SUPPORT"
        rationale = (
            f"Strong Stage 2 trend, but extended ({ext_10w_pct or 0:+.1f}% above 10-week EMA, RSI {rsi}) "
            f"or valuation requires discipline ({valuation_note}). Do not chase on FOMO; wait for pullback "
            f"to support zone {support_zone_low}–{support_zone_high}."
        )
    elif stage in ("STAGE_3", "STAGE_1"):
        posture = "AT_STAGE2_SUPPORT_RETEST"
        verdict = "WAIT_FOR_SUPPORT"
        rationale = (
            f"Consolidating / pulling back near 30-week SMA ({sma30w}) and 50-day SMA ({sma50}). "
            f"Accumulate only if support holds in {support_zone_low}–{support_zone_high} and volume expands on turn."
        )
    else:
        posture = "WAIT_FOR_SUPPORT_PULLBACK"
        verdict = "WAIT_FOR_SUPPORT"
        rationale = "Monitor for low-risk support entry."

    return {
        "weinstein_stage": stage,
        "entry_timing_posture": posture,
        "recommended_verdict": verdict,
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
            for rows in (sl.get("sheets") or {}).values():
                if isinstance(rows, list):
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


def prune_watchlist(market: str, snapshots: Dict[str, Any], dry_run: bool = False) -> Dict[str, Any]:
    """
    Prune dead-weight or broken-trend stocks from data/watchlist/<MKT>.json (active -> archive)
    so the active watchlist remains focused on Stage 2 / emerging momentum candidates.
    Never prunes CURRENT_HOLDING rows.
    """
    wl_path = ROOT / "data" / "watchlist" / f"{market}.json"
    if not wl_path.exists():
        return {"pruned_count": 0, "pruned": []}

    wl = json.loads(wl_path.read_text(encoding="utf-8"))
    active = wl.get("active", [])
    archive = wl.get("archive", [])
    kept = []
    pruned = []
    today_str = dt.date.today().isoformat()

    for row in active:
        sym = row.get("symbol", "")
        if row.get("source_type") == "CURRENT_HOLDING":
            kept.append(row)
            continue

        snap = snapshots.get(sym, {})
        ev = snap.get("stage2_evaluation", {})
        tv = snap.get("tradingview", {})
        stage = ev.get("weinstein_stage")
        posture = ev.get("entry_timing_posture")
        perf_1m = tv.get("perf_1m_pct")
        perf_3m = tv.get("perf_3m_pct")

        should_prune = False
        prune_reason = ""
        if stage == "STAGE_4" and (perf_1m is not None and perf_1m < -5.0) and (perf_3m is not None and perf_3m < -8.0):
            should_prune = True
            prune_reason = (
                f"PRUNED_STAGE4_BREAKDOWN ({today_str}): Trading below 30-week SMA ({tv.get('sma30_weekly')}) "
                f"and 50-day SMA ({tv.get('sma50')}) with 1M return {perf_1m}% and 3M return {perf_3m}%."
            )
        elif row.get("action_verdict") == "REJECTED" or row.get("gate_status") == "FAIL":
            should_prune = True
            prune_reason = f"PRUNED_REJECTED_GATE ({today_str}): Previously failed underwriting gates."

        if should_prune:
            archived_row = dict(row)
            archived_row["status"] = "ARCHIVED"
            archived_row["action_verdict"] = "REJECTED"
            archived_row["gate_status"] = "FAIL"
            archived_row["as_of_date"] = today_str
            old_notes = archived_row.get("notes") or ""
            archived_row["notes"] = f"{prune_reason} | {old_notes}".strip(" |")
            archive.append(archived_row)
            pruned.append({"symbol": sym, "reason": prune_reason})
        else:
            kept.append(row)

    if pruned and not dry_run:
        wl["active"] = kept
        wl["archive"] = archive
        wl_path.write_text(json.dumps(wl, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    return {"pruned_count": len(pruned), "kept_active_count": len(kept), "pruned": pruned}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--market", choices=["IN", "US"], required=True)
    parser.add_argument("--symbols", nargs="*", default=[], help="Explicit symbols to snapshot")
    parser.add_argument("--from-watchlist", action="store_true", help="Include all active watchlist symbols")
    parser.add_argument("--from-shortlist", action="store_true", help="Include all shortlist symbols")
    parser.add_argument("--from-holdings", action="store_true", help="Include all current holding symbols")
    parser.add_argument("--stage2-file", default=None, help="Path to stage2_<MKT>_latest.json")
    parser.add_argument("--skip-web-card", action="store_true", help="Skip per-symbol Screener/Finviz HTTP fetch for fast bulk scan")
    parser.add_argument("--prune-watchlist", action="store_true", help="Prune Stage 4 / rejected names from active watchlist to archive")
    parser.add_argument("--dry-run", action="store_true", help="Preview watchlist pruning without modifying watchlist JSON")
    parser.add_argument("--out", default=None, help="Output JSON path")
    args = parser.parse_args()

    market = args.market.upper()
    symbols = list(dict.fromkeys([s.upper() for s in args.symbols]))
    if args.from_watchlist or args.from_shortlist or args.from_holdings or args.prune_watchlist:
        extra = collect_symbols_from_records(
            market,
            from_wl=(args.from_watchlist or args.prune_watchlist),
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
    s2_data = load_stage2_context(market, args.stage2_file)

    snapshots: Dict[str, Any] = {}
    for sym in symbols:
        tv = tv_map.get(sym, {})
        s2 = match_stage2_symbol(sym, market, tv, s2_data)
        if not args.skip_web_card and len(symbols) <= 25:
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

    prune_summary = None
    if args.prune_watchlist:
        prune_summary = prune_watchlist(market, snapshots, dry_run=args.dry_run)
        print(
            f"[*] Watchlist prune ({market}): {prune_summary['pruned_count']} pruned, "
            f"{prune_summary['kept_active_count']} active remaining."
        )

    output = {
        "market": market,
        "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
        "symbol_count": len(snapshots),
        "watchlist_prune": prune_summary,
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

