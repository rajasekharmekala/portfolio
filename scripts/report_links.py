#!/usr/bin/env python3
"""Shared helpers for ticker navigation links and source citations.

Used by assemble_report.py (adds the links and the References list) and by validate_report.py
(fails a report whose tickers lack links or whose sources are too few).

A ticker is any bold symbol in the body, written as <b>SYMBOL</b>, that is in the universe of
symbols found in the ledger or research record (or ends in .NS / .BO). Each such ticker must carry
a chart link and a screener link inside the ticker-links span, which the skills template already defines:
  India: TradingView NSE:SYMBOL + screener.in/company/SYMBOL/
  US:    TradingView SYMBOL      + finviz.com/quote.ashx?t=SYMBOL
"""
import json
import re

TICKER_BOLD = re.compile(r"<b>([A-Z][A-Z0-9&\-]{1,15}(?:\.NS|\.BO)?)</b>")
EXTERNAL_HREF = re.compile(r'<a\s+[^>]*href="(https?://[^"]+)"[^>]*>(.*?)</a>', re.S | re.I)
NAV_HOSTS = ("tradingview.com", "screener.in", "finviz.com")
STOP = {"NSE", "BSE", "SEBI", "FII", "DII", "USD", "INR", "ETF", "GDP", "CPI", "ATR", "RSI", "SMA", "EMA",
        "MACD", "FOMC", "CEO", "CFO", "API", "PDF", "HTML", "NAV", "PE", "EPS", "ROE", "ROCE", "NA", "AI",
        "YOY", "QOQ", "BUY", "SELL", "HOLD", "KEEP", "TRIM", "EXIT", "WATCH", "NYSE", "NASDAQ", "SEC", "IPO"}


def symbol_universe(*json_paths: str) -> set:
    """Collect every 'symbol' value from the given JSON files (ledger, research record)."""
    found = set()

    def walk(node):
        if isinstance(node, dict):
            for k, v in node.items():
                if k == "symbol" and isinstance(v, str):
                    found.add(v.strip().upper())
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    for p in json_paths:
        if p:
            with open(p, encoding="utf-8") as f:
                walk(json.load(f))
    return found


def is_ticker(sym: str, universe: set) -> bool:
    if sym in STOP:
        return False
    if sym in universe or sym.endswith((".NS", ".BO")) or sym.split(".")[0] in universe:
        return True
    # no ledger supplied: treat any bold all-caps token of 3+ characters as a ticker
    return not universe and len(sym.split(".")[0]) >= 3


def nav_links(sym: str, market: str) -> tuple:
    base = sym.split(".")[0]
    if market == "IN":
        chart = f"https://www.tradingview.com/chart/?symbol=NSE%3A{base}"
        second = f"https://www.screener.in/company/{base}/"
        second_label = "Screener"
    else:
        chart = f"https://www.tradingview.com/chart/?symbol={base}"
        second = f"https://finviz.com/quote.ashx?t={base}"
        second_label = "Finviz"
    return (chart, "Chart"), (second, second_label)


def window_after(body: str, end: int) -> str:
    """Text after a ticker's </b> up to the next ticker or 400 characters."""
    nxt = body.find("<b>", end)
    stop = min(x for x in (nxt if nxt != -1 else len(body), end + 400, len(body)))
    return body[end:stop]


def linkify(body: str, market: str, universe: set) -> tuple:
    """Add missing chart/screener links next to each bold ticker. Returns (new_body, added_count)."""
    added = 0
    out, pos = [], 0
    for m in TICKER_BOLD.finditer(body):
        sym = m.group(1)
        if not is_ticker(sym, universe):
            continue
        win = window_after(body, m.end())
        has_chart = "tradingview.com" in win
        has_second = "screener.in" in win or "finviz.com" in win
        if has_chart and has_second:
            continue
        (chart, chart_label), (second, second_label) = nav_links(sym, market)
        a_chart = f'<a href="{chart}" style="color:var(--link);">{chart_label}</a>'
        a_second = f'<a href="{second}" style="color:var(--link);">{second_label}</a>'
        if not has_chart and not has_second:
            insert = f'<br/><span class="ticker-links" style="font-size:.85em;">{a_chart} • {a_second}</span>'
            out.append(body[pos:m.end()])
            out.append(insert)
            pos = m.end()
            added += 1
        else:
            # one link present: append the missing one inside the existing span, if it has one
            span_end = body.find("</span>", m.end(), m.end() + 400)
            missing = a_second if has_chart else a_chart
            if span_end != -1:
                out.append(body[pos:span_end])
                out.append(" • " + missing)
                pos = span_end
            else:
                out.append(body[pos:m.end()])
                out.append(f'<br/><span class="ticker-links" style="font-size:.85em;">{missing}</span>')
                pos = m.end()
            added += 1
    out.append(body[pos:])
    return "".join(out), added


def missing_ticker_links(body: str, universe: set) -> list:
    bad = []
    for m in TICKER_BOLD.finditer(body):
        sym = m.group(1)
        if not is_ticker(sym, universe):
            continue
        win = window_after(body, m.end())
        if not ("tradingview.com" in win and ("screener.in" in win or "finviz.com" in win)):
            bad.append(sym)
    return list(dict.fromkeys(bad))


def body_sources(body: str) -> list:
    """External (non-navigation) links cited in the body, as (url, label) pairs, deduplicated by URL."""
    seen, out = set(), []
    for href, label in EXTERNAL_HREF.findall(body):
        if any(h in href for h in NAV_HOSTS):
            continue
        if href in seen:
            continue
        seen.add(href)
        text = re.sub(r"<[^>]+>", "", label).strip() or href
        out.append((href, text))
    return out


def research_sources(*json_paths: str) -> list:
    """Every research entry with a source_url: (url, title, as_of, symbol)."""
    items = []

    def walk(node):
        if isinstance(node, dict):
            url = node.get("source_url") or node.get("url")
            if isinstance(url, str) and url.startswith("http"):
                items.append((url, node.get("title") or node.get("item") or node.get("topic") or "",
                              node.get("as_of", ""), node.get("symbol", "")))
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    for p in json_paths:
        if p:
            with open(p, encoding="utf-8") as f:
                walk(json.load(f))
    return items
