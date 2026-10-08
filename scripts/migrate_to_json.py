#!/usr/bin/env python3
"""
One-time migration from the Excel workbooks and broker markdown snapshots to the JSON data layer.
Run once per market. It writes opening transactions (the starting position of each account), metadata,
and the watchlist, shortlist and options records. Afterwards the workbooks are historical only.

  python3 scripts/migrate_to_json.py --market US --snapshot-date 2026-10-05
"""
import argparse
import datetime as dt
import importlib.util
import json
import os
import re
import sys

import openpyxl

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
NUM = re.compile(r"^-?\d+(\.\d+)?$")


def slug(h):
    h = str(h).strip()
    for a, b in (("P&L", "pnl"), ("%", "pct"), ("($)", "usd"), ("(₹)", "inr"), ("(Cr)", "cr"), ("(Δ)", "delta"), ("$", "usd")):
        h = h.replace(a, f" {b} ")
    return re.sub(r"[^a-z0-9]+", "_", h.lower()).strip("_")


def clean(v):
    if v is None or (isinstance(v, str) and v.strip() in ("", "None")):
        return None
    if isinstance(v, dt.datetime):
        return v.date().isoformat()
    if isinstance(v, str) and NUM.match(v.strip()):
        return float(v) if "." in v else int(v)
    if isinstance(v, str):
        return v.strip()
    return v


def records(path, sheet, header_row=1):
    ws = openpyxl.load_workbook(path, read_only=True, data_only=True)[sheet]
    rows = list(ws.iter_rows(values_only=True))
    header = [slug(h) if h is not None else None for h in rows[header_row - 1]]
    out = []
    for r in rows[header_row:]:
        if not any(v is not None for v in r):
            continue
        rec = {}
        for k, v in zip(header, r):
            if k:
                rec[k] = clean(v)
        if any(v is not None for v in rec.values()):
            out.append(rec)
    return out


def write(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print("wrote", os.path.relpath(path, ROOT))


# Broker snapshot parsing (one-time; the markdown snapshots are historical after migration)
def money(cell):
    """'$2,711.85' -> 2711.85, '-$61.20' -> -61.2, '+11.42%' -> 11.42 (percent as a number), '—' or '' -> None."""
    if cell is None:
        return None
    t = re.sub(r"\*+", "", str(cell)).strip()
    if t in ("", "—", "-", "–", "N/A", "None"):
        return None
    neg = t.startswith("-") or t.startswith("−")
    t = re.sub(r"[^0-9.]", "", t)
    if not t:
        return None
    v = float(t)
    return -v if neg else v


def md_tables(path):
    """All pipe tables in a markdown file, as (header, rows) with header names cleaned of bold markers."""
    tables, cur = [], []
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if line.startswith("|"):
            cur.append(line)
        elif cur:
            tables.append(cur)
            cur = []
    if cur:
        tables.append(cur)
    out = []
    for t in tables:
        cells = [[c.strip() for c in ln.strip("|").split("|")] for ln in t]
        header = [re.sub(r"\*+", "", c).strip() for c in cells[0]]
        body = [r for r in cells[1:] if r and not set("".join(r)) <= set("-: ")]
        out.append((header, body))
    return out


def read_md_positions(src, path):
    """Positions and cash from one broker snapshot. Derives a missing cost basis or market value from the
    other columns that the snapshot does carry, and records which numbers were derived."""
    positions, cash, derived_notes = [], None, []
    sym_h = src["symbol_header"]
    for header, body in md_tables(path):
        if sym_h in header:
            col = header.index(sym_h)
            for r in body:
                if len(r) <= col:
                    continue
                sym = re.sub(r"\*+", "", r[col]).strip().upper()
                if sym in ("CASH", ""):
                    continue
                if not re.match(r"^[A-Z0-9][A-Z0-9&\-\.]{0,19}$", sym) or re.match(r"^[A-Z]{1,6}\d{6}[CP]\d{8}$", sym):
                    continue
                def g(key):
                    h = src.get(key)
                    return money(r[header.index(h)]) if h and h in header else None
                qty = g("qty_header")
                price = g("price_header")
                mv = g("value_header")
                cost = g("cost_header")
                gain = g("gain_header")
                pct = g("gain_pct_header")
                flags = []
                if mv is None and qty is not None and price is not None:
                    mv = round(qty * price, 2); flags.append("value=qty*price")
                if cost is None and gain is not None and pct:
                    cost = round(gain / (pct / 100.0), 2); flags.append("cost=gain/gain%")
                if cost is None and mv is not None and gain is not None:
                    cost = round(mv - gain, 2); flags.append("cost=value-gain")
                if gain is None and mv is not None and cost is not None:
                    gain = round(mv - cost, 2); flags.append("gain=value-cost")
                if mv is None and cost is not None and gain is not None:
                    mv = round(cost + gain, 2); flags.append("value=cost+gain")
                if price is None and mv is not None and qty:
                    price = round(mv / qty, 4); flags.append("price=value/qty")
                positions.append({"symbol": sym, "quantity": qty, "price": price, "market_value": mv,
                                  "cost_basis": cost, "gain": gain, "gain_pct": pct, "derived": flags})
        cash_h = src.get("cash_value_header")
        if cash_h and cash_h in header:
            vcol = header.index(cash_h)
            for r in body:
                first = re.sub(r"\*+", "", r[0]).strip() if r else ""
                if cash is None and re.match(r"(?i)^cash", first) and "buying power" not in first.lower() and len(r) > vcol:
                    cash = money(r[vcol]) or 0  # first cash line only: summary tables repeat the same balance
    return positions, cash


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--market", required=True, choices=["IN", "US"])
    ap.add_argument("--snapshot-date", required=True, help="date the holdings were copied out (YYYY-MM-DD)")
    a = ap.parse_args()
    m, snap = a.market, a.snapshot_date
    dt.date.fromisoformat(snap)
    os.makedirs(DATA, exist_ok=True)

    if m == "IN":
        hold = os.path.join(ROOT, "sheets", "Zerodha_Holdings.xlsx")
        all_rows = records(hold, "Holdings")
        # The sheet has a summary block below the table; keep only real position rows.
        meta_rows = [r for r in all_rows if r.get("symbol") and re.match(r"^[A-Z][A-Z0-9.\-&]{0,19}$", str(r["symbol"]))
                     and isinstance(r.get("quantity"), (int, float))]
        print(f"IN holdings: {len(meta_rows)} position rows kept, {len(all_rows) - len(meta_rows)} non-position rows skipped")
        opening = []
        for r in meta_rows:
            qty = r.get("quantity")
            total = r.get("total_invested")
            if total is None and r.get("avg_buy_price") and qty:
                total = round(r["avg_buy_price"] * qty, 2)
            opening.append({"date": snap, "type": "opening", "market": "IN", "account": "Zerodha", "symbol": r["symbol"],
                            "quantity": qty, "amount": total, "source": "sheets/Zerodha_Holdings.xlsx",
                            "note": None if total is not None else "cost not in the workbook"})
        # Cash and the sync stamp come from the summary block under the table.
        raw = list(openpyxl.load_workbook(hold, read_only=True, data_only=True)["Holdings"].iter_rows(values_only=True))
        cash = None
        for r in raw:
            if r[0] == "Available Cash / Liquid Margin" and r[1]:
                mm = re.search(r"([\d,]+\.?\d*)", str(r[1]))
                cash = float(mm.group(1).replace(",", "")) if mm else None
        if cash is not None:
            opening.append({"date": snap, "type": "cash", "market": "IN", "account": "Zerodha", "symbol": None, "amount": cash,
                            "source": "sheets/Zerodha_Holdings.xlsx", "note": "opening cash from the workbook summary (Kite funds)"})
        lines = "\n".join(json.dumps(x, ensure_ascii=False) for x in opening) + "\n"
        os.makedirs(os.path.join(DATA, "accounts", "IN"), exist_ok=True)
        open(os.path.join(DATA, "accounts", "IN", "zerodha.transactions.jsonl"), "w", encoding="utf-8").write(lines)
        print("wrote data/accounts/IN/zerodha.transactions.jsonl", len(opening), "opening rows")
        meta = {r["symbol"]: {k: r.get(k) for k in ("company_name", "asset_type", "exchange", "strategy_bucket", "sub_theme", "strategy_mandate_moat")} for r in meta_rows}
        shortlist_path, watch_path = "shortlist/Zerodha_Shortlist.xlsx", "watchlist/Zerodha_Watchlist.xlsx"
        opt_path, opt_sheet, opt_hdr = "sheets/Options_Positions.xlsx", "NSE_Options_Book", 4
        watch_sheets = {"active": ("Active_Watchlist", 1), "archive": ("Archive_Rejected", 1)}
    else:
        hold = os.path.join(ROOT, "sheets", "US_Portfolio_Holdings.xlsx")
        meta_rows = records(hold, "Holdings")
        opt_contract = re.compile(r"^[A-Z]{1,6}\d{6}[CP]\d{8}$")
        meta = {r["symbol"]: {k: r.get(k) for k in ("company_name", "asset_type", "exchange", "strategy_bucket", "sub_theme", "strategy_mandate_moat")} for r in meta_rows if r.get("symbol") and re.match(r"^[A-Z][A-Z0-9.\-]{0,11}$", str(r["symbol"])) and not opt_contract.match(str(r["symbol"]))}
        os.makedirs(os.path.join(DATA, "accounts", "US"), exist_ok=True)
        for src_id, label, path, note in [
            ("schwab", "Charles Schwab", "sheets/charles_schwab.md", None),
            ("robinhood", "Robinhood", "sheets/robinhood_current_holdings.md", None)]:
            full = os.path.join(ROOT, path)
            cfg = {"schwab": {"symbol_header": "Symbol", "qty_header": "Quantity", "price_header": "Current Price", "value_header": "Market Value", "cost_header": "Cost Basis", "gain_header": "Total Gain/Loss ($)", "gain_pct_header": "Total Gain/Loss (%)", "cash_value_header": "Market Value"},
                   "robinhood": {"symbol_header": "Ticker", "qty_header": "Shares", "gain_header": "Gain / Loss ($)", "gain_pct_header": "Gain / Loss (%)", "cash_value_header": "Balance / Value"}}[src_id]
            positions, cash = read_md_positions(cfg, full)
            rows = []
            for p in positions:
                amount = p["cost_basis"]
                flags = [f for f in p["derived"] if f.startswith("cost")]
                rows.append({"date": snap, "type": "opening", "market": "US", "account": label, "symbol": p["symbol"],
                             "quantity": p["quantity"], "amount": amount,
                             "source": path, "note": ("cost " + "; ".join(flags)) if flags else (None if amount is not None else "cost not shown in the snapshot")})
            if cash:
                rows.append({"date": snap, "type": "cash", "market": "US", "account": label, "symbol": None,
                             "amount": cash, "source": path, "note": "opening cash balance"})
            with open(os.path.join(DATA, "accounts", "US", f"{src_id}.transactions.jsonl"), "w", encoding="utf-8") as f:
                for r in rows:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")
            print(f"wrote data/accounts/US/{src_id}.transactions.jsonl: {len(positions)} positions, cash {cash}")
        shortlist_path, watch_path = "shortlist/US_Shortlist.xlsx", "watchlist/US_Portfolio_Watchlist.xlsx"
        opt_path, opt_sheet, opt_hdr = "sheets/Options_Positions.xlsx", "US_Options_Book", 4
        watch_sheets = {"active": ("Active_Watchlist", 1), "archive": ("Archive_Rejected", 1)}
    write(os.path.join(DATA, "metadata", "symbols.json"), {"_comment": "Strategy bucket and name per symbol. Add a row when a new name is bought.", m: meta}) if False else None
    meta_file = os.path.join(DATA, "metadata", "symbols.json")
    allmeta = json.load(open(meta_file, encoding="utf-8")) if os.path.exists(meta_file) else {"_comment": "Strategy bucket and name per symbol, by market. Add a row when a new name is bought."}
    allmeta[m] = {"symbols": meta}
    write(meta_file, allmeta)

    w = {k: records(os.path.join(ROOT, watch_path), sheet, hdr) for k, (sheet, hdr) in watch_sheets.items()}
    write(os.path.join(DATA, "watchlist", f"{m}.json"), {"market": m, "migrated_from": watch_path, **w})
    sl = {}
    wb = openpyxl.load_workbook(os.path.join(ROOT, shortlist_path), read_only=True)
    for sheet in wb.sheetnames:
        sl[sheet] = records(os.path.join(ROOT, shortlist_path), sheet)
    write(os.path.join(DATA, "shortlist", f"{m}.json"), {"market": m, "migrated_from": shortlist_path, "sheets": sl})
    opts = records(os.path.join(ROOT, opt_path), opt_sheet, opt_hdr)
    write(os.path.join(DATA, "options", f"{m}.json"), {"market": m, "migrated_from": f"{opt_path} / {opt_sheet}", "positions": opts})


if __name__ == "__main__":
    main()
