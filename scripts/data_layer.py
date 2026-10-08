#!/usr/bin/env python3
"""
Data layer for the portfolio. Holdings are computed from an append-only transaction log per account.
The log is the record of truth. Broker snapshots are optional reconciliation checks.

  data/accounts/<MKT>/<account>.transactions.jsonl   one JSON object per line (see TYPES below)
  data/accounts/<MKT>/<account>.snapshot.json        optional broker snapshot for reconciliation
  data/metadata/symbols.json                         strategy bucket and name per symbol, by market
  data/watchlist/<MKT>.json, data/shortlist/<MKT>.json, data/options/<MKT>.json   workflow records

Usage:
  python3 scripts/data_layer.py --market US --validate          check every file in the data layer
  python3 scripts/data_layer.py --market US --positions         print replayed positions per account
  python3 scripts/data_layer.py --market US --view               write data/views/holdings_US.md

Cost basis uses the average-cost method. A position whose cost is unknown keeps cost_known=false until the
missing purchase is recorded; it is never filled with a guess.
"""
import argparse
import datetime as dt
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
TYPES = {
    "opening": "a position already held when the log starts (quantity and total cost, cost may be null)",
    "buy": "quantity bought; amount = total cost including fees",
    "sell": "quantity sold; amount = total proceeds net of fees",
    "split": "quantity change with no cash; quantity = shares added (negative for a reverse split); amount = 0",
    "cash": "change in account cash balance; amount positive for deposit or income, negative for withdrawal or spend",
    "fee": "fee or tax that is not part of a trade; amount = cost, symbol may be empty",
}
REQUIRED = {"date", "type", "account", "market"}


def accounts_for(market):
    return sorted(glob.glob(os.path.join(DATA, "accounts", market, "*.transactions.jsonl")))


def read_log(path):
    rows, errors = [], []
    with open(path, encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                rows.append((n, json.loads(line)))
            except json.JSONDecodeError as e:
                errors.append(f"{os.path.basename(path)}:{n} not valid JSON ({e})")
    return rows, errors


def replay(rows):
    """Average-cost replay. Returns {symbol: {quantity, cost_basis, cost_known, realized_pl}} and cash balance."""
    pos, cash = {}, 0.0
    for _, t in sorted(rows, key=lambda r: (r[1]["date"], r[0])):
        typ = t["type"]
        if typ == "cash":
            cash += t.get("amount") or 0
            continue
        if typ == "fee":
            cash -= t.get("amount") or 0
            continue
        sym = t["symbol"]
        p = pos.setdefault(sym, {"quantity": 0.0, "cost_basis": 0.0, "cost_known": True, "realized_pl": 0.0})
        q = t.get("quantity") or 0
        amt = t.get("amount")
        if typ in ("opening", "buy"):
            p["quantity"] += q
            if amt is None:
                p["cost_known"] = False
            else:
                p["cost_basis"] += amt
            if typ == "buy" and amt is not None:
                cash -= amt
        elif typ == "sell":
            if p["quantity"] <= 0:
                raise SystemExit(f"{t.get('account')} {sym} {t['date']}: sell of {q} with no position held")
            avg = p["cost_basis"] / p["quantity"] if p["cost_known"] and p["quantity"] else None
            if avg is not None:
                cost_out = avg * q
                p["cost_basis"] -= cost_out
                if amt is not None:
                    p["realized_pl"] += amt - cost_out
            p["quantity"] -= q
            if amt is not None:
                cash += amt
            if p["quantity"] <= 1e-9:
                p["quantity"], p["cost_basis"] = 0.0, 0.0
        elif typ == "split":
            p["quantity"] += q
        else:
            raise SystemExit(f"unknown transaction type '{typ}' in {t.get('account')} {sym} {t['date']}")
    out = {s: {k: (round(v, 6) if isinstance(v, float) else v) for k, v in p.items()} for s, p in pos.items() if abs(p["quantity"]) > 1e-9}
    return out, round(cash, 2)


def account_state(path):
    rows, errors = read_log(path)
    if errors:
        raise SystemExit("\n".join(errors))
    pos, cash = replay(rows)
    meta = {"file": os.path.relpath(path, ROOT), "transactions": len(rows)}
    if rows:
        meta["account"] = rows[0][1]["account"]
        meta["market"] = rows[0][1]["market"]
        meta["last_date"] = max(r[1]["date"] for r in rows)
    return meta, pos, cash


def validate(market):
    """Schema-style checks on every file for one market. Returns a list of problems (empty = clean)."""
    problems = []
    meta_path = os.path.join(DATA, "metadata", "symbols.json")
    symbols = json.load(open(meta_path, encoding="utf-8")).get(market, {}) if os.path.exists(meta_path) else {}
    for path in accounts_for(market):
        rows, errors = read_log(path)
        problems += errors
        seen_open = set()
        for n, t in rows:
            where = f"{os.path.basename(path)}:{n}"
            missing = REQUIRED - set(t)
            if missing:
                problems.append(f"{where} missing {sorted(missing)}")
                continue
            if t["market"] != market:
                problems.append(f"{where} market '{t['market']}' does not match folder {market}")
            if t["type"] not in TYPES:
                problems.append(f"{where} unknown type '{t['type']}' (allowed: {', '.join(TYPES)})")
            try:
                dt.date.fromisoformat(t["date"])
            except (ValueError, TypeError):
                problems.append(f"{where} date '{t.get('date')}' is not YYYY-MM-DD")
            if t["type"] in ("opening", "buy", "sell", "split") and not t.get("symbol"):
                problems.append(f"{where} {t['type']} needs a symbol")
            if t.get("symbol") and symbols and t["symbol"] not in symbols.get("symbols", symbols):
                problems.append(f"{where} symbol {t['symbol']} has no entry in metadata/symbols.json")
            if t["type"] == "opening":
                if t["symbol"] in seen_open:
                    problems.append(f"{where} second opening row for {t['symbol']}; use buy or split instead")
                seen_open.add(t["symbol"])
            if t["type"] in ("buy", "sell", "opening") and (t.get("quantity") or 0) <= 0:
                problems.append(f"{where} quantity must be positive for {t['type']}")
        try:
            replay(rows)
        except SystemExit as e:
            problems.append(str(e))
    for name in ("watchlist", "shortlist", "options"):
        for path in glob.glob(os.path.join(DATA, name, f"{market}.json")):
            try:
                json.load(open(path, encoding="utf-8"))
            except json.JSONDecodeError as e:
                problems.append(f"{os.path.relpath(path, ROOT)} is not valid JSON ({e})")
    return problems


def view(market, out_dir):
    lines = [f"# {market} holdings (generated from the transaction log; do not edit)", "",
             f"Generated {dt.datetime.now().isoformat(timespec='seconds')}. Quantities and cost from `data/accounts/{market}/`. "
             "Market values need the ledger close and are added by the daily build.", ""]
    for path in accounts_for(market):
        meta, pos, cash = account_state(path)
        lines += [f"## {meta.get('account', os.path.basename(path))}", "",
                  f"Last transaction: {meta.get('last_date', 'n/a')}. Cash: {cash:,.2f}.", "",
                  "| Symbol | Quantity | Cost basis | Cost known | Realized P&L |", "|---|---:|---:|:---:|---:|"]
        for sym, p in sorted(pos.items()):
            cb = f"{p['cost_basis']:,.2f}" if p["cost_known"] else "unknown"
            lines.append(f"| {sym} | {p['quantity']:g} | {cb} | {'yes' if p['cost_known'] else 'no'} | {p['realized_pl']:,.2f} |")
        lines.append("")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"holdings_{market}.md")
    open(path, "w", encoding="utf-8").write("\n".join(lines))
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--market", required=True, choices=["IN", "US"])
    ap.add_argument("--validate", action="store_true")
    ap.add_argument("--positions", action="store_true")
    ap.add_argument("--view", action="store_true")
    a = ap.parse_args()
    if a.validate:
        problems = validate(a.market)
        for p in problems:
            print("FAIL", p)
        print("RESULT:", "FAIL" if problems else "PASS")
        sys.exit(1 if problems else 0)
    if a.positions:
        for path in accounts_for(a.market):
            meta, pos, cash = account_state(path)
            print(meta.get("account"), "cash", cash)
            for s, p in sorted(pos.items()):
                print(f"  {s:<8} qty {p['quantity']:<12g} cost {p['cost_basis'] if p['cost_known'] else 'unknown'}")
    if a.view:
        print("wrote", view(a.market, os.path.join(DATA, "views")))


if __name__ == "__main__":
    main()
