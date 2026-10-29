#!/usr/bin/env python3
"""Review packet for the single reviewer (and the conditional red team).

The mechanical part of the review is done here, in code, once. The reviewer
reads the small packet this script writes instead of digging through the raw
report, ledger and research files.

  build   Write <out-dir>/review_packet.md, conclusions_digest.md,
          report_text.md and packet.json.
  check   Validate a reviewer's JSON output against the packet (shape, item
          dispositions, quotes really in the report, report not stale).

What `build` verifies without a model:
  - every number in the report is traced to the facts ledger or the research
    record; only the numbers that cannot be traced are listed for judgment
  - session date on the head of the report vs the ledger as-of and the file name
  - Stage, RSI and close claims about one ticker vs the ledger
  - table totals recomputed, asymmetry ratios recomputed
  - verdict conflicts for the same ticker, and diffs against the sibling report
  - validate_report.py, citation_check.py and readability_check.py results
In delta mode (--prev-packet) only sections changed since the previous round
are listed, and each previous finding is checked for whether its quoted text is
still in the report.

Usage:
  .venv/bin/python scripts/review_packet.py build --report R.html --kind market_intel \\
      --facts F.json --research RS.json --out-dir "$RUN_DIR/review/round_1" --round 1 \\
      [--sibling S.html] [--inputs-dir "$RUN_DIR/inputs"] [--symbol ADBE]
  .venv/bin/python scripts/review_packet.py build ... --round 2 \\
      --prev-packet "$RUN_DIR/review/round_1/packet.json" \\
      --prev-review "$RUN_DIR/review/round_1/round_1_review.json" --out-dir "$RUN_DIR/review/round_2"
  .venv/bin/python scripts/review_packet.py check --review round_1_review.json \\
      --packet packet.json --report R.html
"""
import argparse
import bisect
import hashlib
import json
import os
import re
import subprocess
import sys

from bs4 import BeautifulSoup, NavigableString, Tag

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KINDS = ("market_intel", "portfolio_audit", "dossier")
SKIP_TAGS = {"style", "script", "head", "nav", "noscript"}
SKIP_CLS = re.compile(r"\b(toc|reflist|references|bibliography)\b", re.I)
SKIP_ID = re.compile(r"^(toc|references|bibliography|reflist)$", re.I)
PROSE_CLS = re.compile(
    r"\b(primer|howto|casenote|triggers|example|callout|alert|takeaway|lede|"
    r"key-figures|estimate|verdict-box|verdict-badge)\b")
CONTAINERS = {"div", "section", "aside", "dl", "article"}
VERDICTS = ("KEEP|HOLD|TRIM|EXIT|ACCUMULATE|ADD|WATCH|BUY|SELL|REDUCE|AVOID|REJECTED|REJECT|"
            "QUALIFIED|SHORTLISTED|SHORTLIST|ARCHIVED|ARCHIVE|PROMOTE|DEFERRED|DEFER|ROLL|CLOSE|ADJUST")
VERDICT_RE = re.compile(rf"\b({VERDICTS})\b")
VERDICT_CELL_RE = re.compile(rf"^\W*({VERDICTS})\b")
VERDICT_CELL_I = re.compile(rf"^\W*({VERDICTS})\b", re.I)
TICKER_RE = re.compile(r"(?<![A-Za-z0-9&])([A-Z][A-Z0-9&\-\.]{1,14})(?![a-z0-9])")
TICKER_STOP = {"ON", "ALL", "IT", "ARE", "FOR", "CAN", "NOW", "ONE", "TWO", "NEW", "USD", "INR", "NSE",
               "BSE", "ETF", "RSI", "ATR", "SMA", "EMA", "N/A", "PASS", "FAIL", "TOTAL", "NET", "CORE",
               "CMP", "EPS", "ROIC", "FCF", "SBC", "VIX", "PCR", "FII", "DII", "IPO", "CEO", "CFO"}
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August",
          "September", "October", "November", "December"]

NUM_RE = re.compile(
    r"(?<![A-Za-z0-9_.\-/#=])"
    r"(?P<sign>[-\u2212+]?)(?P<cur>[$\u20b9])?\s?"
    r"(?P<int>\d{1,3}(?:,\d{2,3})+|\d+)(?P<dec>\.\d+)?"
    r"\s?(?P<unit>%|x\b|\u00d7|bps?\b|pp\b|[KMB]n?\b|cr\b|crore\b|lakh\b|trillion\b|billion\b|million\b)?"
    r"(?![A-Za-z0-9_])")
DATE_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
STRIP_RE = [
    re.compile(r"\b\d{4}-\d{2}-\d{2}\b"),
    re.compile(r"\[\d+(?:[,\u2013-]\s?\d+)*\]"),
    re.compile(r"\b(?:Q[1-4]|H[12]|FY|CY)\s?'?\d{2,4}\b"),
    re.compile(r"\b(?:Stage|Chapter|Section|Table|Figure|Step|Rank|Part|ch-)\s?\d+(?:\.\d+)*\b", re.I),
    re.compile(r"\b(?:19|20)\d{2}\b"),
    re.compile(r"\b\d{1,2}(?:st|nd|rd|th)\b"),
    re.compile(r"\b\d{1,3}-(?:day|week|month|year|session|bar|period)\b", re.I),
    re.compile(r"\b(?:SMA|EMA|DMA|ATR|RSI)\s?\(?\d+\)?", re.I),
    re.compile(r"\b\d+\s?(?:-|\u2013)\s?\d+\b"),
]


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha_text(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]


def norm(s):
    s = (s or "").replace("\u00a0", " ").replace("\u2019", "'").replace("\u2018", "'")
    s = s.replace("\u201c", '"').replace("\u201d", '"').replace("\u2212", "-").replace("\u2013", "-").replace("\u2014", "-")
    return re.sub(r"\s+", " ", s).strip().lower()


def clean(s):
    return re.sub(r"\s+", " ", (s or "").replace("\u00a0", " ")).strip()


def read_text(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------- parsing

def parse_report(html):
    soup = BeautifulSoup(html, "html.parser")
    title = clean(soup.title.get_text(" ")) if soup.title else ""
    root = soup.body or soup
    blocks = []
    state = {"n2": 0, "n3": 0, "sid": "S0", "title": "Head", "h2": "", "h3": ""}

    def add(kind, **kw):
        b = {"kind": kind, "sid": state["sid"], "sec": state["title"]}
        b.update(kw)
        blocks.append(b)

    def citation(tag):
        return bool(tag.find("sup")) or bool(re.search(r"\[\d+\]", tag.get_text(" ")))

    def walk(node):
        for ch in node.children:
            if isinstance(ch, NavigableString) or not isinstance(ch, Tag):
                continue
            name = ch.name
            cls = " ".join(ch.get("class", []))
            if name in SKIP_TAGS or SKIP_CLS.search(cls) or SKIP_ID.match(ch.get("id", "") or ""):
                continue
            if name in ("h1", "h2", "h3"):
                text = clean(ch.get_text(" "))
                if name == "h2":
                    state["n2"] += 1
                    state["n3"] = 0
                    state["sid"] = "S%d" % state["n2"]
                    state["h2"], state["h3"] = text, ""
                    state["title"] = text
                elif name == "h3":
                    state["n3"] += 1
                    state["sid"] = "S%d.%d" % (state["n2"], state["n3"])
                    state["h3"] = text
                    state["title"] = (state["h2"] + " > " + text) if state["h2"] else text
                add(name, text=text)
            elif name == "table":
                rows = []
                for tr in ch.find_all("tr"):
                    cells = [clean(c.get_text(" ")) for c in tr.find_all(["th", "td"])]
                    if cells:
                        rows.append(cells)
                add("table", rows=rows, infobox="infobox" in cls, text=" ".join(" ".join(r) for r in rows),
                    cited=citation(ch))
            elif name in CONTAINERS and PROSE_CLS.search(cls):
                verdicts = [clean(s.get_text(" ")) for s in ch.find_all(class_=re.compile(r"verdict-"))]
                add("prose", cls=cls, text=clean(ch.get_text(" ")), symbol=ch.get("data-symbol", ""),
                    verdicts=verdicts, cited=citation(ch))
            elif name in ("p", "li", "dd", "blockquote", "figcaption"):
                text = clean(ch.get_text(" "))
                if text:
                    add("p", cls=cls, text=text, symbol="", verdicts=[], cited=citation(ch))
            else:
                walk(ch)

    walk(root)
    return {"title": title, "blocks": blocks, "html": html}


def block_plain(b):
    if b["kind"] == "table":
        return "\n".join("| " + " | ".join(r) + " |" for r in b["rows"])
    if b["kind"] in ("h1", "h2", "h3"):
        return "#" * int(b["kind"][1]) + " " + b["text"]
    return b["text"]


def section_hashes(blocks):
    parts, titles = {}, {}
    for b in blocks:
        parts.setdefault(b["sid"], []).append(block_plain(b))
        titles.setdefault(b["sid"], b["sec"])
    return {sid: {"title": titles[sid], "sha": sha_text("\n".join(p))} for sid, p in parts.items()}


def report_text_md(parsed):
    out, cur = [], None
    for b in parsed["blocks"]:
        if b["sid"] != cur:
            cur = b["sid"]
            out.append("\n<!-- [%s] %s -->" % (cur, b["sec"]))
        out.append(block_plain(b))
    return "\n".join(out).strip() + "\n"


# ---------------------------------------------------------------- ledger values

def flat_numbers(obj, out=None):
    if out is None:
        out = []
    if isinstance(obj, bool):
        return out
    if isinstance(obj, (int, float)):
        out.append(float(obj))
    elif isinstance(obj, dict):
        for v in obj.values():
            flat_numbers(v, out)
    elif isinstance(obj, list):
        for v in obj:
            flat_numbers(v, out)
    elif isinstance(obj, str):
        for m in re.finditer(r"-?\d[\d,]*\.?\d*", obj):
            try:
                out.append(float(m.group(0).replace(",", "")))
            except ValueError:
                pass
    return out


REC_KEYS = ("symbol", "Symbol", "ticker", "Ticker", "underlying", "SYMBOL", "TradingView Code")


def collect_records(obj, out):
    """symbol -> numeric fields, from any JSON record or snapshot file (shortlist, watchlist, options, stock_snapshot, stage2)."""
    if isinstance(obj, dict):
        sym = next((str(obj[k]).upper() for k in REC_KEYS if isinstance(obj.get(k), str)), None)
        if sym:
            out.setdefault(sym, []).extend(flat_numbers(obj))
        for v in obj.values():
            collect_records(v, out)
    elif isinstance(obj, list):
        for v in obj:
            collect_records(v, out)


def load_positions(market, close_of):
    """Replay the transaction logs (scripts/data_layer.py) and value them at the ledger close.
    Returns (per-symbol numbers, global numbers)."""
    sys.path.insert(0, os.path.join(ROOT, "scripts"))
    try:
        import data_layer
    except Exception:  # noqa: BLE001
        return {}, []
    pos, cash_total = {}, 0.0
    try:
        for path in data_layer.accounts_for(market):
            _, p, cash = data_layer.account_state(path)
            cash_total += cash
            for sym, v in p.items():
                a = pos.setdefault(sym.upper(), {"quantity": 0.0, "cost_basis": 0.0, "realized_pl": 0.0})
                a["quantity"] += v["quantity"]
                a["cost_basis"] += v["cost_basis"]
                a["realized_pl"] += v["realized_pl"]
    except SystemExit:
        return {}, []
    mv = {s: v["quantity"] * close_of(s) for s, v in pos.items() if close_of(s)}
    invested = sum(mv.values())
    nw = invested + cash_total
    per, cost_total = {}, 0.0
    for s, v in pos.items():
        c = close_of(s)
        row = [v["quantity"], v["cost_basis"], v["realized_pl"]]
        if v["quantity"]:
            row.append(v["cost_basis"] / v["quantity"])
        if c:
            m = mv[s]
            row += [m, m - v["cost_basis"]]
            if nw:
                row.append(m / nw * 100)
            if v["cost_basis"]:
                row.append((m / v["cost_basis"] - 1) * 100)
        cost_total += v["cost_basis"]
        per[s] = row
    top = sorted(mv.values(), reverse=True)
    glob_vals = [nw, cash_total, invested, cost_total, invested - cost_total, float(len(pos))]
    if nw:
        glob_vals += [cash_total / nw * 100, invested / nw * 100]
        glob_vals += [sum(top[:k]) / nw * 100 for k in (1, 3, 5) if top]
        glob_vals += [v / nw * 100 for v in top[:10]]
    if cost_total:
        glob_vals.append((invested / cost_total - 1) * 100)
    return per, glob_vals


class Facts:
    def __init__(self, facts, research, record_paths=()):
        self.f = facts or {}
        self.inst = self.f.get("instruments", {}) or {}
        self.asof = self.f.get("asof")
        self.global_vals = flat_numbers(self.f.get("regime", {})) + flat_numbers(self.f.get("macro", {}))
        for name, m in self.inst.items():
            if isinstance(m, dict) and m.get("kind") in ("index", "sector"):
                self.global_vals += [v for v in flat_numbers(m)]
        self.research_items = (research or {}).get("items", []) if isinstance(research, dict) else (research or [])
        self.research_vals = {}
        self.research_all = []
        for it in self.research_items:
            vals = flat_numbers(it.get("value")) + flat_numbers(it.get("notes"))
            sym = str(it.get("symbol", "")).upper()
            self.research_vals.setdefault(sym, []).extend(vals)
            self.research_all.extend(vals)
        self.records = {}
        for p in record_paths:
            try:
                collect_records(load_json(p), self.records)
            except (OSError, ValueError):
                pass
        market = self.f.get("market")
        self.pos, pos_global = ({}, [])
        if market:
            self.pos, pos_global = load_positions(
                market, lambda s: (self.inst.get(s) or {}).get("close") if isinstance(self.inst.get(s), dict) else None)
        self.global_vals += pos_global
        self._pos_global = pos_global
        self._cache = {}

    def sym_vals(self, sym):
        if sym not in self._cache:
            m = self.inst.get(sym)
            vals = flat_numbers({k: v for k, v in m.items() if k not in ("bars",)}) if isinstance(m, dict) else []
            self._cache[sym] = (vals + self.research_vals.get(sym, []) + self.records.get(sym, [])
                                + self.pos.get(sym, []))
        return self._cache[sym]

    def symbols_in(self, text):
        found = []
        for m in TICKER_RE.finditer(text):
            t = m.group(1)
            if t in TICKER_STOP:
                continue
            if (t in self.inst or t in self.pos) and t not in found:
                found.append(t)
        return found

    def derived_big(self, sym):
        """a-b, a+b, a*b of the symbol's and the portfolio's money-sized numbers (|n| >= 1000 only)."""
        key = ("derived", sym)
        if key not in self._cache:
            base = [v for v in (self.sym_vals(sym) + self._pos_global) if v and abs(v) >= 1]
            base = base[:60]
            out = set()
            for i, a in enumerate(base):
                for b in base[i:]:
                    for v in (a - b, a + b, a * b):
                        if abs(v) >= 1000:
                            out.add(round(abs(v), 2))
            self._cache[key] = sorted(out)
        return self._cache[key]


UNIT_SCALES = {"": (1.0,), "%": (1.0, 0.01), "x": (1.0,), "\u00d7": (1.0,), "bp": (1.0, 1e-4), "bps": (1.0, 1e-4), "pp": (1.0,),
               "k": (1e3,), "m": (1e6,), "mn": (1e6,), "million": (1e6,), "b": (1e9,), "bn": (1e9,), "billion": (1e9,),
               "trillion": (1e12,), "cr": (1e7,), "crore": (1e7,), "lakh": (1e5,)}


def matches(n, dec, cands, unit=""):
    tol = 0.5 * (10 ** -dec) + 1e-9
    scales = UNIT_SCALES.get((unit or "").lower(), (1.0,))
    for v in cands:
        for sc in scales:
            if abs(abs(v / sc) - n) <= tol:
                return True
    return False


def near_sorted(sorted_vals, x, tol):
    i = bisect.bisect_left(sorted_vals, x - tol)
    return i < len(sorted_vals) and sorted_vals[i] <= x + tol


def extract_numbers(text):
    """Claim-like numbers: (token, value, decimals, context)."""
    t = text
    for rx in STRIP_RE:
        t = rx.sub(lambda m: " " * len(m.group(0)), t)
    out = []
    for m in NUM_RE.finditer(t):
        raw_int = m.group("int").replace(",", "")
        dec = m.group("dec") or ""
        unit = m.group("unit")
        cur = m.group("cur")
        try:
            val = float(raw_int + dec)
        except ValueError:
            continue
        claim_like = bool(unit or cur or dec or val >= 100)
        if not claim_like:
            continue
        a, b = max(0, m.start() - 50), min(len(text), m.end() + 40)
        out.append((text[m.start():m.end()].strip(), val, max(0, len(dec) - 1), clean(text[a:b]), (unit or "")))
    return out


# ---------------------------------------------------------------- mechanical checks

PRIORITY_CLS = re.compile(r"casenote|key-figures|primer|lede|triggers|estimate|verdict|example")
PRIORITY_HDR = re.compile(r"verdict|action|close|cmp|price|target|stop|asymmetr|weight|qty|quantity|value|risk")


def is_priority(b):
    if b["sid"] == "S0":
        return True
    if b["kind"] == "prose":
        return bool(PRIORITY_CLS.search(b.get("cls", "")))
    if b["kind"] == "table" and b.get("rows"):
        return bool(PRIORITY_HDR.search(" ".join(b["rows"][0]).lower()))
    return False


def trace_numbers(parsed, facts, kind, default_symbol, only_sids=None, sample_per_section=4):
    """Returns (priority groups, sampled groups, traced count, cited-untraced count, unlisted count).
    One group is one block (or table row); every number in it that could not be traced."""
    prio, other, traced, cited_untraced = [], [], 0, 0
    for b in parsed["blocks"]:
        if b["kind"] in ("h1", "h2", "h3"):
            continue
        if only_sids is not None and b["sid"] not in only_sids:
            continue
        units = []
        if b["kind"] == "table":
            if b.get("infobox"):
                continue
            for ri, r in enumerate(b["rows"][1:], 1):
                units.append((" | ".join(r), "%s (table row %d)" % (b["sec"], ri)))
        else:
            units.append((b["text"], b["sec"]))
        for text, loc in units:
            syms = facts.symbols_in(text)
            if b.get("symbol"):
                syms = [b["symbol"]] + [s for s in syms if s != b["symbol"]]
            if default_symbol and default_symbol not in syms:
                syms.append(default_symbol)
            cands = list(facts.global_vals)
            derived = []
            for s in syms:
                cands += facts.sym_vals(s)
                derived += facts.derived_big(s)
            cands += facts.research_all
            derived = sorted(set(derived + facts.derived_big("")))
            toks = []
            for token, val, dec, ctx, unit in extract_numbers(text):
                if matches(val, dec, cands, unit):
                    traced += 1
                    continue
                if val >= 1000 and any(near_sorted(derived, val / sc, (0.5 * 10 ** -dec) / sc + 0.01)
                                       for sc in (1.0, 1e-3, 1e-5, 1e-7)):
                    traced += 1
                    continue
                if kind == "dossier" and b.get("cited"):
                    cited_untraced += 1
                    continue
                toks.append((token, ctx))
            if toks:
                g = {"type": "number", "loc": loc, "sid": b["sid"], "symbols": syms[:3] if syms != [default_symbol] else [],
                     "tokens": toks, "priority": is_priority(b)}
                (prio if g["priority"] else other).append(g)
    sampled, unlisted = [], 0
    by_sid = {}
    for g in other:
        by_sid.setdefault(g["sid"], []).append(g)
    for sid, gs in by_sid.items():
        if len(gs) <= sample_per_section:
            sampled += gs
        else:
            step = len(gs) / float(sample_per_section)
            idx = sorted({int(i * step) for i in range(sample_per_section)})
            sampled += [gs[i] for i in idx]
            unlisted += sum(len(g["tokens"]) for i, g in enumerate(gs) if i not in idx)
    return prio, sampled, traced, cited_untraced, unlisted


def date_items(parsed, facts, report_path):
    items = []
    asof = facts.asof
    if not asof:
        return items
    y, m, d = asof.split("-")
    mname = MONTHS[int(m) - 1]
    forms = [asof, "%s %d, %s" % (mname, int(d), y), "%s %d, %s" % (mname[:3], int(d), y),
             "%d %s %s" % (int(d), mname, y), "%d %s %s" % (int(d), mname[:3], y)]
    head_blocks = []
    for b in parsed["blocks"]:
        if b["sid"] != "S0" and b["kind"] != "h1":
            break
        head_blocks.append(block_plain(b))
    head = parsed["title"] + " " + " ".join(head_blocks)
    if not any(f.lower() in head.lower() for f in forms):
        items.append({"type": "date", "loc": "Head, title",
                      "problem": "ledger as-of %s does not appear in the title or opening blocks" % asof})
    fm = DATE_RE.search(os.path.basename(report_path))
    if fm and fm.group(0) != asof:
        items.append({"type": "date", "loc": "file name",
                      "problem": "file name dated %s but ledger as-of is %s" % (fm.group(0), asof)})
    return items


def claim_regexes():
    return {
        "stage": re.compile(r"\bStage ([1-4])\b"),
        "rsi": re.compile(r"\bRSI(?:\s?\(14\))?\D{0,12}(\d{1,3}(?:\.\d+)?)"),
        "close": re.compile(r"(?:\bCMP|\bclose[sd]?|\blatest close)(?!\s*(?:above|below|over|under|through|beyond|near))\D{0,6}[$\u20b9]?\s?(\d[\d,]*\.\d+|\d[\d,]{2,})", re.I),
    }


def ledger_claim_items(parsed, facts, only_sids=None, price_tol=1.5):
    rx = claim_regexes()
    items, seen = [], set()

    def check(text, sym, loc, sid):
        m = facts.inst.get(sym)
        if not isinstance(m, dict) or m.get("error") or m.get("kind") in ("index", "sector"):
            return
        for sm in rx["stage"].finditer(text):
            if m.get("stage") and int(sm.group(1)) != m["stage"]:
                k = (sym, "stage", sm.group(1), loc)
                if k not in seen:
                    seen.add(k)
                    items.append({"type": "ledger", "loc": loc, "sid": sid, "symbols": [sym],
                                  "problem": "%s: report says Stage %s, ledger says Stage %s" % (sym, sm.group(1), m["stage"])})
        for rm in rx["rsi"].finditer(text):
            v = float(rm.group(1))
            if m.get("rsi14") is not None and abs(v - m["rsi14"]) > 1.0 and v <= 100:
                k = (sym, "rsi", rm.group(1), loc)
                if k not in seen:
                    seen.add(k)
                    items.append({"type": "ledger", "loc": loc, "sid": sid, "symbols": [sym],
                                  "problem": "%s: report says RSI %s, ledger RSI14 is %s" % (sym, rm.group(1), m["rsi14"])})
        for cm in rx["close"].finditer(text):
            if re.search(r"\b(if|unless|until|once|when|should|whether)\b[^.]{0,30}$", text[max(0, cm.start() - 40):cm.start()], re.I):
                continue
            v = float(cm.group(1).replace(",", ""))
            if m.get("close") and abs(v / m["close"] - 1) * 100 > price_tol:
                k = (sym, "close", cm.group(1), loc)
                if k not in seen:
                    seen.add(k)
                    items.append({"type": "ledger", "loc": loc, "sid": sid, "symbols": [sym],
                                  "problem": "%s: report says close %s, ledger close is %s (%s)" % (sym, cm.group(1), m["close"], m.get("asof_bar"))})

    for b in parsed["blocks"]:
        if only_sids is not None and b["sid"] not in only_sids:
            continue
        if b["kind"] == "table" and not b.get("infobox"):
            for ri, r in enumerate(b["rows"][1:], 1):
                syms = facts.symbols_in(" ".join(r[:3]))
                if len(syms) == 1:
                    check(" | ".join(r), syms[0], "%s (table row %d)" % (b["sec"], ri), b["sid"])
        elif b["kind"] in ("p", "prose"):
            sym = b.get("symbol") or ""
            syms = [sym] if sym else facts.symbols_in(b["text"])
            if len(syms) == 1:
                check(b["text"], syms[0], b["sec"], b["sid"])
    return items


def to_float(cell):
    s = cell.replace(",", "").replace("\u2212", "-")
    m = re.search(r"-?\d+(?:\.\d+)?", s)
    if not m or not re.fullmatch(r"\s*[-+$\u20b9]?\s*-?\d[\d.,]*\s*(?:%|x|cr|crore|lakh|[KMB])?\s*", cell.replace("\u2212", "-")):
        return None, 0
    txt = m.group(0)
    return float(txt), len(txt.split(".")[1]) if "." in txt else 0


def table_items(parsed, only_sids=None):
    items = []
    for b in parsed["blocks"]:
        if b["kind"] != "table" or b.get("infobox") or len(b["rows"]) < 3:
            continue
        if only_sids is not None and b["sid"] not in only_sids:
            continue
        rows = b["rows"]
        hdr = [h.lower() for h in rows[0]]
        # totals
        start = 1
        for ri in range(1, len(rows)):
            lab = rows[ri][0].strip().lower() if rows[ri] else ""
            if re.match(r"^(grand\s+)?(total|sum|net worth|portfolio total|combined)\b", lab):
                for ci in range(1, len(rows[ri])):
                    tot, td = to_float(rows[ri][ci])
                    if tot is None:
                        continue
                    vals = []
                    for rj in range(start, ri):
                        if ci < len(rows[rj]):
                            v, d = to_float(rows[rj][ci])
                            if v is not None:
                                vals.append((v, d))
                    if len(vals) < 2 or len(vals) < 0.7 * (ri - start):
                        continue
                    s = sum(v for v, _ in vals)
                    d = max([td] + [d for _, d in vals])
                    tol = max(0.5 * (10 ** -d) * len(vals), 0.002 * abs(tot))
                    if abs(s - tot) > tol:
                        items.append({"type": "total", "loc": b["sec"] + " (table)", "sid": b["sid"],
                                      "problem": "column '%s': rows add to %s but the %s row says %s" % (
                                          rows[0][ci] if ci < len(rows[0]) else ci, round(s, d + 1), rows[ri][0], rows[ri][ci])})
                start = ri + 1
    return items


def collect_verdicts(parsed, facts):
    """symbol -> list of {verdict, loc, sid, text}; casenotes and table rows only."""
    out = {}

    def put(sym, verdict, loc, sid, text, src):
        out.setdefault(sym, []).append({"verdict": verdict, "loc": loc, "sid": sid, "text": text, "src": src})

    for b in parsed["blocks"]:
        if b["kind"] == "prose" and "casenote" in b.get("cls", ""):
            sym = b.get("symbol") or (facts.symbols_in(b["text"][:80]) or [""])[0]
            verdict = ""
            for v in b.get("verdicts", []):
                mm = VERDICT_RE.search(v.upper())
                if mm:
                    verdict = mm.group(1)
                    break
            if not verdict:
                mm = VERDICT_RE.search(b["text"])
                verdict = mm.group(1) if mm else ""
            if sym:
                put(sym, verdict, b["sec"], b["sid"], b["text"], "casenote")
        elif b["kind"] == "table" and not b.get("infobox"):
            for ri, r in enumerate(b["rows"][1:], 1):
                syms = facts.symbols_in(" ".join(r[:2]))
                if len(syms) != 1:
                    continue
                for c in r[1:]:
                    cell = c.strip()
                    mm = VERDICT_CELL_RE.match(cell) or (VERDICT_CELL_I.match(cell) if len(cell) <= 30 else None)
                    if mm:
                        put(syms[0], mm.group(1).upper(), "%s (table row %d)" % (b["sec"], ri), b["sid"], " | ".join(r), "table")
                        break
    return out


def verdict_conflict_items(verdicts, only_sids=None):
    items = []
    for sym, rows in sorted(verdicts.items()):
        seen = {}
        for r in rows:
            if r["verdict"]:
                seen.setdefault(r["verdict"], []).append(r["loc"])
        if len(seen) > 1 and (only_sids is None or any(r["sid"] in only_sids for r in rows)):
            items.append({"type": "verdict_conflict", "loc": "; ".join(sorted({r["loc"] for r in rows}))[:200],
                          "symbols": [sym],
                          "problem": "%s carries different verdicts: %s" % (sym, "; ".join("%s at %s" % (v, ", ".join(l[:2])) for v, l in seen.items()))})
    return items


def claims_of(parsed, facts):
    rx = claim_regexes()
    claims = {}
    for sym, rows in collect_verdicts(parsed, facts).items():
        claims.setdefault(sym, {"verdicts": set(), "stages": set(), "closes": set()})["verdicts"].update(r["verdict"] for r in rows if r["verdict"])
    for b in parsed["blocks"]:
        units = []
        if b["kind"] == "table" and not b.get("infobox"):
            for r in b["rows"][1:]:
                syms = facts.symbols_in(" ".join(r[:3]))
                if len(syms) == 1:
                    units.append((syms[0], " | ".join(r)))
        elif b["kind"] in ("p", "prose"):
            syms = [b["symbol"]] if b.get("symbol") else facts.symbols_in(b["text"])
            if len(syms) == 1:
                units.append((syms[0], b["text"]))
        for sym, text in units:
            c = claims.setdefault(sym, {"verdicts": set(), "stages": set(), "closes": set()})
            c["stages"].update(int(x) for x in rx["stage"].findall(text))
            c["closes"].update(float(x.replace(",", "")) for x in rx["close"].findall(text))
    return claims


def sibling_items(parsed, sibling, facts, only_sids=None):
    items = []
    a, b = claims_of(parsed, facts), claims_of(sibling, facts)
    for sym in sorted(set(a) & set(b)):
        for field in ("verdicts", "stages"):
            if a[sym][field] and b[sym][field] and not (a[sym][field] & b[sym][field]):
                items.append({"type": "sibling", "loc": "sibling report", "symbols": [sym],
                              "problem": "%s %s differ: this report %s, sibling %s" % (
                                  sym, field, sorted(a[sym][field]), sorted(b[sym][field]))})
        if a[sym]["closes"] and b[sym]["closes"]:
            if not any(abs(x / y - 1) < 0.005 for x in a[sym]["closes"] for y in b[sym]["closes"] if y):
                items.append({"type": "sibling", "loc": "sibling report", "symbols": [sym],
                              "problem": "%s closes differ: this report %s, sibling %s" % (
                                  sym, sorted(a[sym]["closes"]), sorted(b[sym]["closes"]))})
    return items


def run_checks(kind, report, facts_path, research_path, cache_dir, allow_stale):
    py = sys.executable
    results = {}

    def run(name, cmd):
        try:
            p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=300)
            text = (p.stdout or "") + (p.stderr or "")
            lines = [l.rstrip() for l in text.splitlines() if l.strip()]
            bad = [l.strip() for l in lines if re.search(r"\bFAIL\b|^\s*-\s|EXCEPTION|ERROR|MISMATCH", l)]
            results[name] = {"exit": p.returncode, "ok": p.returncode == 0, "lines": (bad or lines)[-40:]}
        except Exception as e:  # noqa: BLE001
            results[name] = {"exit": None, "ok": False, "lines": ["could not run: %s" % e]}

    vkind = "market_intel" if kind == "market_intel" else "portfolio_audit"
    if kind != "dossier":
        cmd = [py, "scripts/validate_report.py", "--report", report, "--kind", vkind]
        if facts_path:
            cmd += ["--facts", facts_path]
        run("validate_report", cmd)
    cmd = [py, "scripts/citation_check.py", report]
    if research_path:
        cmd += ["--research", research_path]
    if cache_dir:
        cmd += ["--cache-dir", cache_dir]
    if allow_stale:
        cmd.append("--allow-stale-asof")
    if kind != "dossier":
        cmd += ["--min-sources", "0"]
    run("citation_check", cmd)
    run("readability_check", [py, "scripts/readability_check.py", report,
                              "--glossary", os.path.join(".agents", "config", "glossary.json"), "--max-grade", "13.0"])
    if kind != "dossier" and "readability_check" in results:
        # the primer/estimate/chapter-7/notes structure belongs to the company-report book standard only
        r = results["readability_check"]
        findings = [l for l in r["lines"] if l.strip().startswith("- ")]
        kept = [l for l in findings if not re.match(r"\s*-\s*(ESTIMATE|CHAPTER 7|PRIMER|NOTES)\b", l)]
        r["lines"] = kept or r["lines"][-1:]
        r["ok"] = not kept
    return results


# ---------------------------------------------------------------- packet rendering

LEDGER_KEYS = ("asof_bar", "close", "stage", "rsi14", "sma50", "sma200", "hi52", "lo52", "pct_from_52w_high",
               "chg_1d_pct", "vol_mult_20d", "roles")


def ledger_slice(facts, sym):
    m = facts.inst.get(sym)
    if not isinstance(m, dict):
        return "not in ledger"
    return ", ".join("%s=%s" % (k, m[k]) for k in LEDGER_KEYS if k in m and m[k] is not None)


def research_slice(facts, sym):
    rows = []
    for it in facts.research_items:
        if str(it.get("symbol", "")).upper() == sym:
            v = json.dumps(it.get("value"), ensure_ascii=False)
            rows.append("- %s [%s]: %s (as_of %s, %s)" % (it.get("key"), it.get("status"), v[:160], it.get("as_of"), it.get("source_url")))
    return "\n".join(rows) if rows else "- none recorded"


def number_ids(items):
    counters = {}
    prefix = {"number": "N", "ledger": "L", "total": "T", "asymmetry": "A", "date": "D", "sibling": "S",
              "verdict_conflict": "V", "check": "K"}
    for it in items:
        p = prefix[it["type"]]
        counters[p] = counters.get(p, 0) + 1
        it["id"] = "%s-%03d" % (p, counters[p])
    return items


def tone_sample(parsed, only_sids=None):
    """Deterministic sample for the tone read: the primer, lede and how-to blocks; the opening and
    closing paragraph of each H2 (where the bridge sits); the opening paragraph of every third H3;
    every fourth case note. In delta mode, every prose block of the changed sections."""
    prose = [b for b in parsed["blocks"] if b["kind"] in ("p", "prose")]
    if only_sids is not None:
        return [b for b in prose if b["sid"] in only_sids]
    picked, case_i, h3_i = [], 0, 0
    by_h2, first_h3 = {}, {}
    for b in prose:
        h2 = b["sid"].split(".")[0]
        if re.search(r"primer|lede|howto", b.get("cls", "")):
            picked.append(b)
        elif "casenote" in b.get("cls", ""):
            if case_i % 4 == 0:
                picked.append(b)
            case_i += 1
        else:
            by_h2.setdefault(h2, []).append(b)
            if "." in b["sid"] and b["sid"] not in first_h3:
                first_h3[b["sid"]] = b
    for h2, blks in by_h2.items():
        picked.append(blks[0])
        if len(blks) > 1:
            picked.append(blks[-1])
    for sid, b in first_h3.items():
        if h3_i % 3 == 0:
            picked.append(b)
        h3_i += 1
    seen, out = set(), []
    for b in prose:
        if any(b is x for x in picked) and id(b) not in seen:
            seen.add(id(b))
            out.append(b)
    return out


def digest_note(text, limit=650):
    """First sentence plus the sentences that carry targets, stops, risks and triggers."""
    sents = re.split(r"(?<=[.!?])\s+", text)
    keep = sents[:1] + [x for x in sents[1:] if re.search(r"target|stop|asymmetr|reward|risk|\bif\b|unless|would|trigger|below|above", x, re.I)]
    return " ".join(keep)[:limit]


def render_item(it):
    sym = (" [%s]" % ",".join(it["symbols"])) if it.get("symbols") else ""
    if it["type"] == "number":
        toks = it["tokens"]
        shown = "; ".join("`%s` (...%s...)" % (t, c[:70]) for t, c in toks[:3])
        more = ("; plus %s" % ", ".join("`%s`" % t for t, _ in toks[3:12])) if len(toks) > 3 else ""
        return "- **%s** %s%s — %d untraced: %s%s" % (it["id"], it["loc"], sym, len(toks), shown, more)
    return "- **%s** %s%s — %s" % (it["id"], it["loc"], sym, it["problem"])


def build(args):
    kind = args.kind
    report = os.path.abspath(args.report)
    html = read_text(report)
    parsed = parse_report(html)
    facts_json = load_json(args.facts) if args.facts else {}
    research_json = load_json(args.research) if args.research else {}
    record_paths = []
    for inp in facts_json.get("inputs", []) or []:
        pth = inp.get("path", "")
        cand = os.path.join(ROOT, pth)
        if pth.endswith(".json") and os.path.isfile(cand):
            record_paths.append(cand)
        elif pth.endswith(".json") and args.inputs_dir and os.path.isfile(os.path.join(args.inputs_dir, os.path.basename(pth))):
            record_paths.append(os.path.join(args.inputs_dir, os.path.basename(pth)))
    for extra in (
        "data/options/%s.json" % facts_json.get("market", ""),
        "data/views/stage2_%s_latest.json" % facts_json.get("market", ""),
    ):
        if os.path.isfile(os.path.join(ROOT, extra)) and os.path.join(ROOT, extra) not in record_paths:
            record_paths.append(os.path.join(ROOT, extra))
    if getattr(args, "snapshots", None) and os.path.isfile(args.snapshots):
        record_paths.append(args.snapshots)
    facts = Facts(facts_json, research_json, record_paths)
    default_symbol = args.symbol or ""
    if not default_symbol and kind == "dossier":
        m = re.match(r"([A-Z0-9&\-\.]+)_dossier", os.path.basename(report))
        default_symbol = m.group(1) if m else ""

    hashes = section_hashes(parsed["blocks"])
    changed, prev_status = None, []
    prev_packet = load_json(args.prev_packet) if args.prev_packet else None
    if prev_packet:
        old = prev_packet.get("sections", {})
        changed = {sid for sid, v in hashes.items() if old.get(sid, {}).get("sha") != v["sha"]}
        if args.prev_review and os.path.isfile(args.prev_review):
            text_norm = norm(report_text_md(parsed))
            for f in load_json(args.prev_review).get("findings", []):
                if f.get("severity") not in ("BLOCK", "REVISE"):
                    continue
                q = norm(f.get("quote", ""))
                still = bool(q) and q in text_norm
                prev_status.append({"location": f.get("location", ""), "kind": f.get("kind", "judgment"),
                                    "severity": f.get("severity"), "quote": f.get("quote", ""),
                                    "fix": f.get("fix", ""), "quote_still_in_report": still})

    items = []
    prio, sampled, traced, cited_untraced, unlisted = trace_numbers(parsed, facts, kind, default_symbol, changed)
    items += prio + sampled
    items += date_items(parsed, facts, report)
    items += ledger_claim_items(parsed, facts, changed)
    items += table_items(parsed, changed)
    verdicts = collect_verdicts(parsed, facts)
    items += verdict_conflict_items(verdicts, changed)
    sibling_path = args.sibling if args.sibling and os.path.isfile(args.sibling) else None
    if sibling_path:
        sib = parse_report(read_text(sibling_path))
        items += sibling_items(parsed, sib, facts, changed)

    checks = {}
    if not args.skip_checks:
        rpath = args.research
        checks = run_checks(kind, report, args.facts, rpath, args.cache_dir, args.allow_stale_asof)
        for name, r in checks.items():
            if not r["ok"]:
                for line in r["lines"][:25]:
                    items.append({"type": "check", "loc": name, "problem": line[:260]})
    items = number_ids(items)

    verdict_rows = []
    for sym in sorted(verdicts):
        for r in verdicts[sym]:
            if changed is None or r["sid"] in changed:
                verdict_rows.append((sym, r))
    case_rows = [(s, r) for s, r in verdict_rows if r["src"] == "casenote"]
    table_rows = [(s, r) for s, r in verdict_rows if r["src"] == "table"]

    os.makedirs(args.out_dir, exist_ok=True)
    text_md = report_text_md(parsed)
    with open(os.path.join(args.out_dir, "report_text.md"), "w", encoding="utf-8") as f:
        f.write(text_md)

    mode = "DELTA (round %d)" % args.round if prev_packet else "FULL (round %d)" % args.round
    P = []
    P.append("# Review packet — %s" % os.path.basename(report))
    P.append("")
    P.append("kind: %s · mode: %s · ledger as-of: %s · report sha256: %s" % (kind, mode, facts.asof or "n/a", sha256_file(report)[:16]))
    P.append("")
    P.append("This packet is the review input. Code has already done the mechanical checks below; do not redo them. "
             "Your job is the judgment items. Full report text, sectioned and searchable by `[S#]` anchors, is in `report_text.md`; "
             "the ledger and research files are listed in `packet.json` for resolving one specific item.")
    P.append("")
    P.append("## 1. What code already verified")
    P.append("")
    listed = sum(len(i["tokens"]) for i in items if i["type"] == "number")
    P.append("- numbers traced to the ledger, research record, positions replay or arithmetic on them: **%d**" % traced)
    P.append("- numbers not traced: **%d listed** in section 2 (every number in verdict notes, the head, key figures and decision tables, plus a "
             "deterministic sample of each other section), **%d more** in other sections not listed%s. Untraced means 'could not be matched by code', "
             "not 'wrong': many are the writer's own arithmetic. Check that each is derivable from the numbers around it." % (
                 listed, unlisted,
                 ("; %d numbers sit in cited prose and cannot be machine-traced" % cited_untraced) if kind == "dossier" else ""))
    for name, r in checks.items():
        P.append("- %s: **%s**" % (name, "PASS" if r["ok"] else "FAIL (lines in section 2)"))
    if not checks:
        P.append("- validators were not run (--skip-checks)")
    P.append("- date, ticker Stage/RSI/close claims, table totals, asymmetry recompute, verdict conflicts%s: checked; only failures are listed" % (
        ", sibling diff" if sibling_path else ""))
    if prev_packet:
        P.append("- sections changed since the previous round: **%s**" % (", ".join(sorted(changed, key=lambda s: [int(x) for x in s[1:].split('.')])) or "none"))
    P.append("")
    if prev_status:
        P.append("## 1b. Previous findings (round %d)" % (args.round - 1))
        P.append("")
        for i, f in enumerate(prev_status, 1):
            P.append("- **P-%02d** [%s/%s] %s — quote %s. Fix asked: %s" % (
                i, f["severity"], f["kind"], f["location"],
                "STILL IN REPORT" if f["quote_still_in_report"] else "no longer in report", f["fix"][:200]))
        P.append("")
        P.append("Confirm each previous finding is fixed, using the changed sections. Do not re-review unchanged sections.")
        P.append("")
    P.append("## 2. Items that need a disposition (judgment)")
    P.append("")
    P.append("Give each id a result in your output: `ok` (supported, derived correctly, or explained) or `finding`.")
    P.append("")
    titles = {"number": "Numbers not traced to the ledger or research record",
              "ledger": "Claims that disagree with the ledger", "total": "Table totals that do not add up",
              "asymmetry": "Asymmetry ratios that do not recompute", "date": "Session date",
              "sibling": "Differences against the sibling report", "verdict_conflict": "Verdict conflicts",
              "check": "Validator, citation and readability failures"}
    for t, title in titles.items():
        sel = [i for i in items if i["type"] == t]
        if sel:
            P.append("### %s (%d)" % (title, len(sel)))
            P.extend(render_item(i) for i in sel)
            P.append("")
    if not items:
        P.append("None. Every mechanical check passed.")
        P.append("")
    P.append("## 3. Verdicts and their evidence (%d rows)" % len(verdict_rows))
    P.append("")
    P.append("For each row: does the verdict follow from the numbers and rule the note cites, do the numbers match the ledger slice, "
             "and is every company claim in the note supported by the research slice? Report `verdict_rows_reviewed` in your output.")
    P.append("")
    for sym, r in case_rows:
        P.append("### %s — %s  (%s)" % (sym, r["verdict"] or "no verdict word", r["loc"]))
        P.append("ledger: %s" % ledger_slice(facts, sym))
        P.append("research:\n%s" % research_slice(facts, sym))
        P.append("note: %s" % r["text"])
        P.append("")
    if table_rows:
        P.append("### Verdicts in tables")
        for sym, r in table_rows:
            P.append("- %s — %s (%s): %s" % (sym, r["verdict"], r["loc"], r["text"][:200]))
        P.append("")
    sample = tone_sample(parsed, changed)
    P.append("## 4. Prose for the tone read (%s)" % ("every prose block of the changed sections" if changed is not None else "deterministic sample"))
    P.append("")
    P.append("Judge against the tone checklist in the rubric. Banned phrases, readability grade and glossary first-use are already in the code checks above.")
    P.append("")
    cur = None
    for b in sample:
        if b["sid"] != cur:
            cur = b["sid"]
            P.append("**[%s] %s**" % (cur, b["sec"]))
        P.append("> " + (b["text"] if len(b["text"]) <= 1200 else b["text"][:1200] + " [...truncated; full text in report_text.md]"))
        P.append("")
    with open(os.path.join(args.out_dir, "review_packet.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(P))

    # conclusions digest for the red team
    D = ["# Conclusions digest — %s" % os.path.basename(report), "",
         "Verdicts, the numbers they rest on, scenarios and triggers. Nothing else from the report.", ""]
    kf = [b for b in parsed["blocks"] if b["kind"] == "prose" and "key-figures" in b.get("cls", "")]
    for b in kf[:1]:
        D += ["## Key figures", b["text"], ""]
    D.append("## Verdicts")
    for sym in sorted(verdicts):
        for r in verdicts[sym]:
            if r["src"] == "casenote":
                D += ["### %s — %s  (%s)" % (sym, r["verdict"] or "no verdict word", r["loc"]),
                      "ledger: %s" % ledger_slice(facts, sym), "research:\n%s" % research_slice(facts, sym),
                      digest_note(r["text"]), ""]
            else:
                D.append("- %s — %s: %s" % (sym, r["verdict"], r["text"][:260]))
    D.append("")
    D.append("## Scenario, target and stop tables")
    for b in parsed["blocks"]:
        if b["kind"] == "table" and re.search(r"target|stop|scenario|bear|base|bull|asymmetry|expected", " ".join(b["rows"][0]).lower() if b["rows"] else ""):
            D += ["**%s**" % b["sec"], block_plain(b), ""]
    D.append("## Triggers and risks")
    for b in parsed["blocks"]:
        if b["kind"] == "prose" and re.search(r"triggers|estimate", b.get("cls", "")):
            D += ["- [%s] %s" % (b["sid"], b["text"][:700])]
    ge = [b for b in parsed["blocks"] if "gate" in b["sec"].lower() and b["kind"] in ("p", "prose")]
    if ge:
        D += ["", "## Gate exceptions disclosed"] + ["- " + b["text"][:500] for b in ge]
    with open(os.path.join(args.out_dir, "conclusions_digest.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(D) + "\n")

    pk = {"report": report, "report_sha256": sha256_file(report), "kind": kind, "round": args.round,
          "mode": "delta" if prev_packet else "full", "asof": facts.asof,
          "files": {"facts": args.facts, "research": args.research, "sibling": sibling_path,
                    "inputs_dir": args.inputs_dir},
          "file_sha256": {k: sha256_file(v) for k, v in (("facts", args.facts), ("research", args.research),
                                                          ("sibling", sibling_path)) if v and os.path.isfile(v)},
          "item_ids": [i["id"] for i in items], "items": items,
          "verdict_rows": len(verdict_rows), "changed_sections": sorted(changed) if changed is not None else None,
          "sections": hashes, "previous_findings": prev_status,
          "checks": {k: {"ok": v["ok"]} for k, v in checks.items()}}
    # skip rule for round 2: every open previous finding was mechanical, its quote is gone, and code is clean
    if prev_packet:
        open_prev = [f for f in prev_status]
        mech_only = bool(open_prev) and all(f["kind"] == "mechanical" for f in open_prev)
        fixed = all(not f["quote_still_in_report"] for f in open_prev)
        clean_code = not items
        pk["agent_needed"] = not (mech_only and fixed and clean_code)
        pk["agent_needed_reason"] = (
            "all open findings were mechanical, their quotes are gone and the code checks are clean" if not pk["agent_needed"]
            else "judgment findings were open, a quoted text remains, or code checks still show items")
    with open(os.path.join(args.out_dir, "packet.json"), "w", encoding="utf-8") as f:
        json.dump(pk, f, indent=1, ensure_ascii=False)
    size = sum(os.path.getsize(os.path.join(args.out_dir, n)) for n in ("review_packet.md",))
    print("PACKET %s: %d items, %d verdict rows, %d numbers traced; review_packet.md %d KB (report %d KB)" % (
        pk["mode"], len(items), len(verdict_rows), traced, size // 1024, len(html) // 1024))
    if prev_packet:
        print("AGENT NEEDED: %s (%s)" % (pk["agent_needed"], pk["agent_needed_reason"]))
    return 0


# ---------------------------------------------------------------- check

def check(args):
    problems = []
    try:
        rv = load_json(args.review)
    except (OSError, ValueError) as e:
        print("REVIEW CHECK: FAIL\n  - not valid JSON: %s" % e)
        return 1
    pk = load_json(args.packet)
    for k in ("verdict", "round", "pass", "findings"):
        if k not in rv:
            problems.append("missing key '%s'" % k)
    if rv.get("verdict") not in ("APPROVE", "REVISE", "BLOCK"):
        problems.append("verdict must be APPROVE, REVISE or BLOCK")
    if args.report and sha256_file(args.report) != pk.get("report_sha256"):
        problems.append("STALE: the report changed after the packet was built; rebuild the packet and re-run the review")
    if rv.get("report_sha256") and rv["report_sha256"][:16] != pk.get("report_sha256", "")[:16]:
        problems.append("review was written against a different report hash")
    text = ""
    if args.report:
        text = norm(report_text_md(parse_report(read_text(args.report))))
    for i, f in enumerate(rv.get("findings", []), 1):
        sev = f.get("severity")
        if sev not in ("BLOCK", "REVISE", "NOTE"):
            problems.append("finding %d: severity must be BLOCK, REVISE or NOTE" % i)
        if sev in ("BLOCK", "REVISE"):
            for k in ("location", "quote", "fix"):
                if not f.get(k):
                    problems.append("finding %d (%s): missing '%s'" % (i, sev, k))
            if f.get("kind") not in ("mechanical", "judgment"):
                problems.append("finding %d: 'kind' must be 'mechanical' or 'judgment'" % i)
        q = norm(f.get("quote", ""))
        if q and text:
            parts = [p.strip() for p in re.split(r"\.\.\.|\u2026", q) if len(p.strip()) > 8]
            if parts and not all(p in text for p in parts):
                problems.append("finding %d: quote not found in the report (paraphrased or invented): %.80s" % (i, f.get("quote")))
    disp = {}
    for d in rv.get("items", []):
        if isinstance(d, dict) and d.get("id"):
            disp[d["id"]] = d.get("result")
    missing = [i for i in pk.get("item_ids", []) if i not in disp]
    if missing:
        problems.append("no disposition for packet items: %s" % ", ".join(missing[:20]) + (" ..." if len(missing) > 20 else ""))
    for i, r in disp.items():
        if r not in ("ok", "finding"):
            problems.append("item %s: result must be 'ok' or 'finding'" % i)
    if pk.get("verdict_rows") and rv.get("verdict_rows_reviewed") != pk["verdict_rows"] and pk.get("mode") == "full":
        problems.append("verdict_rows_reviewed is %s, packet has %s verdict rows" % (rv.get("verdict_rows_reviewed"), pk["verdict_rows"]))
    if rv.get("verdict") == "APPROVE" and any(f.get("severity") in ("BLOCK", "REVISE") for f in rv.get("findings", [])):
        problems.append("APPROVE with BLOCK or REVISE findings")
    if problems:
        print("REVIEW CHECK: FAIL (malformed; rerun the review once per reviewer.json)")
        for p in problems:
            print("  - " + p)
        return 1
    print("REVIEW CHECK: PASS (%s, %d findings)" % (rv.get("verdict"), len(rv.get("findings", []))))
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--report", required=True)
    b.add_argument("--kind", required=True, choices=KINDS)
    b.add_argument("--facts")
    b.add_argument("--research")
    b.add_argument("--snapshots", help="optional path to snapshots_<MKT>_<date>.json from stock_snapshot.py")
    b.add_argument("--out-dir", required=True)
    b.add_argument("--round", type=int, default=1)
    b.add_argument("--sibling")
    b.add_argument("--inputs-dir")
    b.add_argument("--symbol", help="default ticker for a single-company dossier")
    b.add_argument("--prev-packet")
    b.add_argument("--prev-review")
    b.add_argument("--cache-dir", default=os.path.join("scripts", ".cache", "fetched"))
    b.add_argument("--allow-stale-asof", action="store_true")
    b.add_argument("--skip-checks", action="store_true", help="do not run the three validators")
    c = sub.add_parser("check")
    c.add_argument("--review", required=True)
    c.add_argument("--packet", required=True)
    c.add_argument("--report")
    args = ap.parse_args()
    return build(args) if args.cmd == "build" else check(args)


if __name__ == "__main__":
    sys.exit(main())
