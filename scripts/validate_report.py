#!/usr/bin/env python3
"""
Pre-send gate for newsletters and portfolio audits ("book edition"). Fails (exit 1) when a report is a data
dump, is too thin to teach a beginner, has too many N/A cells, contradicts the facts ledger, lacks a sourced
web-research record, or has unrendered/boilerplate content.

Usage:
  python3 scripts/validate_report.py --report docs/reports/US_Market_Intelligence_2026-09-28.html \
      --kind market_intel --facts scripts/.cache/facts_US_2026-09-28.json
  --kind: market_intel | portfolio_audit | stage2_sector_momentum

Structural markers the writer must use (CSS classes on <div>, all styled as callouts):
  primer    "Start here" beginner guide (report opening)          howto    how to read the next table
  casenote  one stock/position story (add data-symbol="TICK")     triggers "what would change this view" if/then list
  example   worked numeric example
"""
import argparse
import json
import os
import re
import sys
from html.parser import HTMLParser

PROSE_DIV = re.compile(r"callout|alert|note|card|flaw|lede|primer|howto|casenote|triggers|example|takeaway")
SKIP_DIV = re.compile(r"toc|reflist|references")
BANNED = [
    r"Technical Revalidation Pending", r"carried forward", r"Encyclopedic evaluation of",
    r"Symmetric (institutional )?(screening|coverage|forensic)", r"not asserted", r"intentionally N/A",
    r"\{\{[A-Z_0-9]+\}\}", r"rest of table", r"remaining .* continue", r"\bTODO\b", r"lorem ipsum",
    r"No row is a (trade|short) alert", r"heavy institutional institutional",
    r"\bThis section\b", r"\bIn this section\b", r"\bThe following table\b", r"\bBelow is\b",
    r"It is important to note", r"It should be noted", r"\bLet us (explore|examine)\b", r"\bWe will (explore|examine)\b",
    r"\bFurthermore\b", r"\bMoreover\b", r"\bAdditionally\b", r"\bIn conclusion\b", r"\bIn summary\b",
    r"Overall, it is clear", r"\bdelve\b", r"\blandscape\b", r"\brobust\b", r"game-changer", r"\bunlock\b",
    r"speak(s)? for (it|them)self", r"pending revalidation", r"to be confirmed later",
]
STOP = {"N/A", "ETF", "USD", "INR", "NSE", "BSE", "CFO", "NET", "PASS", "EXIT", "HOLD", "TRIM", "BUY", "CORE", "TOTAL"}
THRESH = {
    "market_intel": dict(h2=150, total=2500, intro=0, take=60, casenotes=6, triggers=4),
    "portfolio_audit": dict(h2=150, total=2500, intro=0, take=60, casenotes=6, triggers=4),
    # A watchlist batch summary covers only the name(s) claimed by that run;
    # it must not be held to portfolio-wide case-note or research-needs floors.
    "watchlist": dict(h2=100, total=1200, intro=0, take=45, casenotes=1, triggers=4),
    "stage2_sector_momentum": dict(h2=150, total=2500, intro=0, take=60, casenotes=8, triggers=4),
}
CASE_MIN_WORDS = 80
# Checks that are meaningful on one section fragment. Whole-report floors (total words, primer, glossary, list counts)
# only run in full mode, on the assembled report.
PARTIAL_CHECKS = ("BANNED", "THIN SUBSECTION", "REPETITIVE", "PRICE MISMATCH", "CASE NOTE", "TABLE WITHOUT",
                  "COLOURS", "EMOJI", "DATE MISMATCH", "RESEARCH ITEM", "DUPLICATED", "HOLDINGS WITHOUT",
                  "EMPTY CELLS", "EMPTY HEADINGS")


class Doc(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.blocks, self.cur, self.tdepth, self.divs = [], None, 0, []
        self.skip = 0
        self.tbl = None
        self.cell = None

    def _open(self, kind, cls=""):
        self.cur = {"kind": kind, "cls": cls, "text": []}

    def _close(self):
        if self.cur:
            self.cur["text"] = re.sub(r"\s+", " ", " ".join(self.cur["text"])).strip()
            self.blocks.append(self.cur)
            self.cur = None

    def _in(self, what):
        return what in self.divs

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        cls = a.get("class", "")
        if tag in ("style", "script", "head"):
            self.skip += 1
        if tag == "table":
            self.tdepth += 1
            if self.tdepth == 1:
                self._close()
                self.tbl = {"kind": "table", "infobox": "infobox" in cls, "rows": []}
        elif self.tbl is not None and tag == "tr":
            self.tbl["rows"].append([])
        elif self.tbl is not None and tag in ("td", "th"):
            self.cell = {"text": []}
        elif self.tbl is None:
            if tag == "div":
                self.divs.append("skip" if SKIP_DIV.search(cls) else "prose" if PROSE_DIV.search(cls) else "plain")
                if self.divs[-1] == "prose" and self.divs.count("prose") == 1:
                    self._close(); self._open("p", cls)
            elif tag == "nav":
                self.divs.append("skip")
            elif tag in ("h1", "h2", "h3") and not self._in("prose"):
                self._close(); self._open(tag)
            elif tag in ("p", "li") and not self._in("prose") and not self._in("skip"):
                self._close(); self._open("p", cls)
            elif tag == "ol" and "reflist" in cls:
                self.divs.append("skip")

    def handle_endtag(self, tag):
        if tag in ("style", "script", "head"):
            self.skip = max(0, self.skip - 1)
        if tag == "table":
            self.tdepth -= 1
            if self.tdepth == 0 and self.tbl is not None:
                self.blocks.append(self.tbl)
                self.tbl = None
        elif self.tbl is not None and tag in ("td", "th") and self.cell is not None:
            txt = re.sub(r"\s+", " ", " ".join(self.cell["text"])).strip()
            if self.tbl["rows"]:
                self.tbl["rows"][-1].append(txt)
            self.cell = None
        elif self.tbl is None:
            if tag in ("div", "nav") and self.divs:
                popped = self.divs.pop()
                if popped == "prose" and not self._in("prose"):
                    self._close()
            elif tag == "ol" and self.divs and self.divs[-1] == "skip":
                self.divs.pop()
            elif not self._in("prose") and (tag in ("h1", "h2", "h3") or (tag in ("p", "li") and self.cur and self.cur["kind"] == "p")):
                self._close()

    def handle_data(self, data):
        if self.skip:
            return
        if self.cell is not None:
            self.cell["text"].append(data)
        elif self.tbl is None and self.cur is not None and not self._in("skip"):
            self.cur["text"].append(data)


class Stage2Markers(HTMLParser):
    def __init__(self):
        super().__init__()
        self.cases = set()
        self.meta = {}

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "div" and "casenote" in attrs.get("class", "").split() and attrs.get("data-symbol"):
            self.cases.add(attrs["data-symbol"].upper())
        if tag == "meta" and attrs.get("name"):
            self.meta[attrs["name"]] = attrs.get("content", "")


def words(s):
    return len(re.findall(r"[A-Za-z0-9$₹%.,'’-]+", s))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", required=True)
    ap.add_argument("--kind", required=True, choices=list(THRESH))
    ap.add_argument("--facts")
    ap.add_argument("--research", help="run-specific research record")
    ap.add_argument("--snapshots", help="run-specific technical snapshots")
    ap.add_argument("--stage2-file", help="run-specific freshly extracted dashboard snapshot")
    ap.add_argument("--max-na-pct", type=float, default=5.0)
    ap.add_argument("--price-tol-pct", type=float, default=1.5)
    ap.add_argument("--partial", action="store_true",
                    help="check one section fragment: only the checks that make sense on part of a report (see PARTIAL_CHECKS). Run the full validator on the assembled report.")
    args = ap.parse_args()
    T = THRESH[args.kind]
    raw = open(args.report, encoding="utf-8").read()
    d = Doc()
    d.feed(raw)
    B = d.blocks
    errors, warns = [], []
    F = json.load(open(args.facts)) if args.facts else None

    # 1. prose volume per H2 section and overall
    sections, cur = [], None
    for b in B:
        if b["kind"] == "h2":
            cur = {"title": b["text"], "words": 0}
            sections.append(cur)
        elif b["kind"] == "p" and cur is not None:
            cur["words"] += words(b["text"])
    total = sum(s["words"] for s in sections) + sum(words(b["text"]) for b in B[: next((i for i, b in enumerate(B) if b["kind"] == "h2"), 0)] if b["kind"] == "p")
    # 1b. every H3 explains itself (120+ prose words of its own) and H2s bridge forward
    OPTIONAL = r"reference|disclosure|methodology|glossary|bibliograph|sources"
    h3_cur, h3_words, h3_title = None, 0, None
    subs = []
    for b in B:
        if b["kind"] == "h2":
            if h3_title and not re.search(OPTIONAL, h3_title, re.I):
                subs.append((h3_title, h3_words))
            h3_title, h3_words = None, 0
        elif b["kind"] == "h3":
            if h3_title and not re.search(OPTIONAL, h3_title, re.I):
                subs.append((h3_title, h3_words))
            h3_title, h3_words = b["text"], 0
        elif b["kind"] == "p" and h3_title is not None:
            h3_words += words(b["text"])
    if h3_title and not re.search(OPTIONAL, h3_title, re.I):
        subs.append((h3_title, h3_words))
    for title, n in subs:
        if n < 120:
            errors.append(f"THIN SUBSECTION '{title[:60]}': {n} prose words < 120 (explain what it is, why it matters, what follows)")
    # bridge: the last prose paragraph before each H2 should point forward or name the consequence
    last_p, bridge_re = None, re.compile(r"\b(next|later|below|above|section|chapter|what this means|for you|turn|watch|trigger|unless|until)\b", re.I)
    for b in B:
        if b["kind"] == "h2":
            if last_p and not bridge_re.search(last_p) and not re.search(OPTIONAL, b["text"], re.I):
                warns.append(f"NO BRIDGE before '{b['text'][:50]}': end the previous section by tying it to the next")
        if b["kind"] == "p":
            last_p = b["text"]
    # repetitive openings (robotic cadence)
    openers = {}
    paras = [b["text"] for b in B if b["kind"] == "p" and words(b["text"]) > 8]
    for t in paras:
        k = " ".join(re.findall(r"[A-Za-z']+", t)[:2]).lower()
        openers[k] = openers.get(k, 0) + 1
    limit = max(6, int(0.12 * len(paras)))
    for k, v in openers.items():
        if v > limit:
            errors.append(f"REPETITIVE OPENINGS: {v} paragraphs start with '{k}' (limit {limit}); vary the sentence openings")

    for s in sections:
        if not re.search(r"reference|disclosure|methodology|glossary", s["title"], re.I) and s["words"] < T["h2"]:
            errors.append(f"THIN SECTION '{s['title'][:60]}': {s['words']} prose words < {T['h2']}")
    if total < T["total"]:
        errors.append(f"TOTAL PROSE {total} words < {T['total']} (not book-length; a beginner cannot learn the reasoning from this)")

    # 2. executive scaffolding: triggers, case notes
    def blocks_with(c):
        return [b for b in B if b["kind"] == "p" and c in b.get("cls", "")]
    if len(blocks_with("triggers")) < T.get("triggers", 0):
        errors.append(f"TRIGGER blocks: {len(blocks_with('triggers'))} < {T['triggers']} (<div class=\"triggers\">: 'what would change this view' with explicit if/then levels)")
    cases = blocks_with("casenote")
    if not args.partial and len(cases) < T.get("casenotes", 0):
        errors.append(f"CASE NOTES: {len(cases)} < {T['casenotes']} (<div class=\"casenote\"> per stock/position: story, numbers with meaning, verdict, rule that triggered it, what changes it)")
    if not args.partial and args.kind == "watchlist":
        markers = Stage2Markers()
        markers.feed(raw)
        if len(markers.cases) != 1:
            errors.append(f"WATCHLIST SCOPE: expected one underwritten symbol in case notes, found {len(markers.cases)}")
    for c in cases:
        t = c["text"]
        if words(t) < CASE_MIN_WORDS:
            errors.append(f"CASE NOTE TOO SHORT ({words(t)} words < {CASE_MIN_WORDS}): '{t[:50]}...'")
        elif not re.search(r"\d", t) or not re.search(r"\b(if|unless|until|would|trigger|below|above|breaks?|closes?)\b", t, re.I):
            errors.append(f"CASE NOTE LACKS NUMBERS OR IF/THEN TRIGGER: '{t[:50]}...'")
    if not args.partial and args.kind == "portfolio_audit" and F:
        holds = [s for s, m in F["instruments"].items() if "holding" in m.get("roles", []) and not m.get("error")]
        alltext = " ".join(c["text"] for c in cases)
        missing = [s for s in holds if not re.search(rf"(?<![A-Z0-9]){re.escape(s)}(?![A-Z0-9])", alltext)]
        if missing:
            errors.append(f"HOLDINGS WITHOUT A CASE NOTE ({len(missing)}/{len(holds)}): {', '.join(missing[:20])}")

    # 3. data table takeaways
    tables = [i for i, b in enumerate(B) if b["kind"] == "table" and not b["infobox"] and len(b["rows"]) > 2]
    for i in tables:
        nxt = B[i + 1] if i + 1 < len(B) else None
        title = next((B[j]["text"] for j in range(i - 1, -1, -1) if B[j]["kind"] in ("h3", "h2")), "?")[:55]
        if T.get("take", 0) > 0 and (not nxt or nxt["kind"] != "p" or words(nxt["text"]) < T["take"]):
            errors.append(f"TABLE WITHOUT TAKEAWAY (>= {T['take']} words explaining what the numbers mean) under '{title}'")

    # 4. N/A budget
    cells = na = 0
    for i in tables:
        t = B[i]
        body = [c for r in t["rows"][1:] for c in r]
        n = sum(1 for c in body if re.search(r"\bN/A\b", c))
        cells += len(body); na += n
        if body and n / len(body) > 0.25:
            errors.append(f"TABLE MOSTLY N/A ({n}/{len(body)} cells) under table starting '{' '.join(t['rows'][0])[:50]}'")
    pct = 100 * na / cells if cells else 0
    if pct > args.max_na_pct:
        errors.append(f"N/A CELLS {na}/{cells} = {pct:.1f}% > {args.max_na_pct}% (acquire the data: scripts/market_facts.py + duck-duck-go MCP)")
    if re.search(r"N/A[^<]{0,40}(fine subsector|not separately supplied)", raw, re.I):
        errors.append("Taxonomy fields left N/A; classify from the 11-group master taxonomy")

    # 5. boilerplate / unrendered / duplicate paragraphs
    for pat in BANNED:
        m = re.search(pat, raw, re.I)
        if m:
            errors.append(f"BANNED/BOILERPLATE TEXT: '{m.group(0)}'")
    seen = {}
    for b in B:
        if b["kind"] == "p" and words(b["text"]) > 15:
            seen[b["text"][:120]] = seen.get(b["text"][:120], 0) + 1
    for k, v in seen.items():
        if v > 1:
            errors.append(f"DUPLICATED PARAGRAPH x{v}: '{k[:70]}...'")

    # 6. bull/bear list completeness (market intelligence only)
    if args.kind == "market_intel":
        for name in ("bull", "bear"):
            n, active = 0, False
            for b in B:
                if b["kind"] == "h2":
                    active = bool(re.search(rf"\b{name}\b", b["text"], re.I))
                elif active and b["kind"] == "table" and not b["infobox"]:
                    n += len(b["rows"]) - 1
            expected = 30
            if F and F.get("screen", {}).get("universe"):
                expected = min(30, sum(len(v) for v in F["screen"][name + "_pick"].values()))
            if n != expected:
                errors.append(f"{name.upper()} LIST has {n} rows, ledger picks provide {expected} (10 per cap tier where available)")
            if F and F.get("screen", {}).get("universe"):
                allowed = {r["symbol"] for k in (name, name + "_near", name + "_relaxed") for r in F["screen"][k]}
                outside, active = [], False
                for b in B:
                    if b["kind"] == "h2":
                        active = bool(re.search(rf"\b{name}\b", b["text"], re.I))
                    elif active and b["kind"] == "table" and not b["infobox"]:
                        for r in b["rows"][1:]:
                            m = re.match(r"([A-Z][A-Z0-9&\-\.]{0,14})\b", r[0].strip()) if r else None
                            if m and m.group(1) not in allowed:
                                outside.append(m.group(1))
                if outside:
                    errors.append(f"{name.upper()} LIST names not in the ledger screen (hand-picked?): {', '.join(outside[:12])}")

    # 7. facts-ledger consistency + session date honesty
    if F:
        L = F["instruments"]
        title_date = re.search(r"(\d{4}-\d{2}-\d{2})", os.path.basename(args.report))
        if title_date and title_date.group(1) != F["asof"]:
            errors.append(f"DATE MISMATCH: report is dated {title_date.group(1)} but its ledger is as-of {F['asof']} (never relabel an older ledger)")
        bad = 0
        for i in tables:
            t = B[i]
            hdr = [h.lower() for h in t["rows"][0]] if t["rows"] else []
            close_col = next((k for k, h in enumerate(hdr) if h in ("close", "cmp", "latest close")), None)
            for r in t["rows"][1:]:
                tk = None
                for c in r[:3]:
                    if re.fullmatch(r"\d+", c.strip()):
                        continue
                    m = re.match(r"([A-Z][A-Z0-9&\-\.]{0,14})\b(?!\s+VIX)", c.strip().lstrip("^"))
                    if m and m.group(1) not in STOP:
                        tk = m.group(1)
                        break
                m = L.get(tk) if tk else None
                if not m or m.get("error") or m.get("kind") in ("index", "sector"):
                    continue
                rowtxt = " ".join(r)
                claims = [float(x.replace(",", "")) for x in re.findall(r"(?:CMP|Close)[:\s]*[$₹]?\s*([\d,]+\.?\d*)", rowtxt)]
                if close_col is not None and close_col < len(r):
                    mm = re.search(r"[\d,]+\.?\d*", r[close_col])
                    if mm:
                        claims.append(float(mm.group(0).replace(",", "")))
                for v in claims:
                    if m["close"] and abs(v / m["close"] - 1) * 100 > args.price_tol_pct:
                        errors.append(f"PRICE MISMATCH {tk}: report {v} vs ledger close {m['close']} ({m['asof_bar']})")
                        bad += 1
                for st in re.findall(r"Stage ([1-4])", rowtxt):
                    if m.get("stage") and int(st) != m["stage"]:
                        errors.append(f"STAGE MISMATCH {tk}: report says Stage {st}, ledger says Stage {m['stage']}")
                        bad += 1
                if bad > 25:
                    break
        # index-level claims in the infobox/tables (Nifty, S&P etc.) against ledger closes
        for name, m in L.items():
            if m.get("kind") == "index" and m.get("close") and not name.endswith("VIX") and name != "VIX":
                mm = re.search(rf"{re.escape(name)}(?![\d])(?:[^<]|<[^>]*>){{0,240}}?([\d,]{{5,}}\.\d{{2}})", raw)
                if mm:
                    v = float(mm.group(1).replace(",", ""))
                    if abs(v / m["close"] - 1) * 100 > args.price_tol_pct:
                        errors.append(f"INDEX MISMATCH {name}: report {v} vs ledger {m['close']}")
        if re.search(r"Stage 2[^<]{0,40}(uptrend|structural)", raw, re.I) and not F["regime"]["label"].startswith("Uptrend"):
            errors.append(f"REGIME MISMATCH: report claims a Stage 2 uptrend, ledger regime is '{F['regime']['label']}'")
        if F["regime"]["label"].split(" (")[0] not in raw:
            errors.append(f"REGIME LABEL '{F['regime']['label']}' from the ledger never appears verbatim in the report")

        # web-research record (duck-duck-go MCP)
        rf = F.get("research_file", "")
        rpath = args.research or os.path.join(os.path.dirname(os.path.abspath(args.facts)), os.path.basename(rf))
        if not os.path.isfile(rpath):
            rpath = os.path.join(os.path.dirname(os.path.abspath(args.facts)), "..", "..", rf)
        if not os.path.isfile(rpath):
            errors.append(f"NO WEB RESEARCH RECORD at {F.get('research_file')} (use the duck-duck-go MCP for every research_needs item)")
        else:
            got = {}
            for it in json.load(open(rpath)).get("items", []):
                got.setdefault(it.get("key"), []).append(it)
            for need in ([] if args.kind in ("stage2_sector_momentum", "watchlist") else F.get("research_needs", [])):
                items = got.get(need["key"])
                if not items:
                    errors.append(f"RESEARCH MISSING: {need['key']}")
                    continue
                if isinstance(need.get("symbols"), list) and need["symbols"]:
                    covered = {str(it.get("symbol", "")).upper() for it in items}
                    miss = [s for s in need["symbols"] if s.upper() not in covered]
                    if len(miss) > 0.2 * len(need["symbols"]):
                        errors.append(f"RESEARCH INCOMPLETE {need['key']}: {len(miss)}/{len(need['symbols'])} symbols missing ({', '.join(miss[:8])})")
                for it in items:
                    if it.get("status") == "found":
                        if not str(it.get("source_url", "")).startswith("http") or not it.get("as_of") or it.get("value") in (None, ""):
                            errors.append(f"RESEARCH ITEM '{need['key']}' lacks value / source_url / as_of")
                        elif need["key"] in ("fii_dii_cash", "cboe_put_call", "nifty_options", "fii_index_futures") and str(it["as_of"])[:10] != F["asof"]:
                            errors.append(f"RESEARCH ITEM '{need['key']}' is dated {it['as_of']}, not the session {F['asof']}")
                        if need["key"] in ("fii_dii_cash", "cboe_put_call", "nifty_options") and not str(it.get("confirmed_by", "")).startswith("http"):
                            errors.append(f"RESEARCH ITEM '{need['key']}' is single-source: add 'confirmed_by' (a second independent URL)")
                    elif len(it.get("queries_tried", [])) < 3:
                        errors.append(f"RESEARCH ITEM '{need['key']}' marked not_found after <3 distinct queries/sources")

    if args.kind == "stage2_sector_momentum" and not args.partial:
        if not F:
            errors.append("STAGE2 INPUT: session facts ledger required")
        required_sections = ("s2-sector-rotation", "s2-setups", "s2-case-notes", "s2-health", "s2-watchlist")
        for section in required_sections:
            if not re.search(r'id=["\']' + section + r'["\']', raw):
                errors.append(f"STAGE2 SECTION MISSING: {section}")
        markers = Stage2Markers()
        markers.feed(raw)
        case_names = markers.cases
        if len(case_names) < 8:
            errors.append(f"STAGE2 CANDIDATES: {len(case_names)} distinct case notes < 8")
        try:
            snapshots = json.load(open(args.snapshots, encoding="utf-8"))["snapshots"]
            dashboard = json.load(open(args.stage2_file, encoding="utf-8"))
            record = json.load(open(args.research, encoding="utf-8"))["items"]
        except (TypeError, OSError, ValueError, KeyError) as error:
            errors.append(f"STAGE2 INPUT: fresh dashboard, snapshots and research required ({error})")
        else:
            if not dashboard.get("summary", {}).get("last_updated") or not dashboard.get("extracted_at"):
                errors.append("STAGE2 FRESHNESS: dashboard update date and extraction time are required")
            elif dashboard["summary"]["last_updated"] not in raw:
                errors.append("STAGE2 FRESHNESS: dashboard update date must be disclosed")
            if not dashboard.get("sector_chart_complete") or not dashboard.get("stage2_universe_complete"):
                gate = re.search(r'<section\b[^>]*id=["\']gate-exceptions["\'][^>]*>(.*?)</section>', raw, re.I | re.S)
                if not gate or not re.search(r'incomplete|partial|unknown|not complete', gate.group(1), re.I):
                    errors.append("STAGE2 COVERAGE: incomplete extraction must be disclosed in gate exceptions")
            if dashboard.get("market") == "IN":
                states = dashboard.get("slicer_verification", {}).get("states", {})
                core = ("Industry", "TradingView Code", "SME Only Flag", "ASM ESM GSM", "Stage2 Status", "Cheat Entry")
                if any(states.get(key) != "All" for key in core):
                    gate = re.search(r'<section\b[^>]*id=["\']gate-exceptions["\'][^>]*>(.*?)</section>', raw, re.I | re.S)
                    if not gate or not re.search(r'slicer|filter', gate.group(1), re.I):
                        errors.append("STAGE2 FILTERS: unverified dashboard slicers must be disclosed in gate exceptions")
            if F and markers.meta.get("research-as-of") != F.get("asof"):
                errors.append("STAGE2 SESSION: research-as-of metadata must match the ledger session")
            removed = {r.get("TradingView Code", "") for r in dashboard.get("removed_this_week", [])}
            if removed.intersection(case_names):
                errors.append("STAGE2 MEMBERSHIP: a case note uses a dashboard-removed stock")
            found = {str(r.get("symbol", "")).upper() for r in record if r.get("status") == "found"}
            for symbol in sorted(case_names):
                if symbol not in snapshots:
                    errors.append(f"STAGE2 SNAPSHOT MISSING: {symbol}")
                elif not snapshots[symbol].get("thewrap_stage2", {}).get("stage2_snapshot_available"):
                    errors.append(f"STAGE2 MEMBERSHIP UNAVAILABLE: {symbol}")
                if symbol not in found:
                    errors.append(f"STAGE2 RESEARCH MISSING: {symbol}")
            if F:
                expected_holdings = {name for name, item in F.get("instruments", {}).items()
                                     if "holding" in item.get("roles", []) and not item.get("error")}
                health_rows = set()
                for i in tables:
                    header = [h.strip().lower() for h in B[i]["rows"][0]]
                    if "holding" in header:
                        column = header.index("holding")
                        health_rows.update(row[column].strip().upper() for row in B[i]["rows"][1:] if len(row) > column)
                missing_holdings = expected_holdings - health_rows
                if missing_holdings:
                    errors.append("STAGE2 HOLDINGS MISSING: " + ", ".join(sorted(missing_holdings)))
                expected_shortlist = {name for name, item in F.get("instruments", {}).items()
                                      if "shortlist" in item.get("roles", []) and not item.get("error")}
                health = re.search(r'<section\b[^>]*id=["\']s2-health["\'][^>]*>(.*?)</section>', raw, re.I | re.S)
                health_text = re.sub(r'<[^>]+>', ' ', health.group(1)) if health else ""
                missing_shortlist = {name for name in expected_shortlist
                                     if not re.search(r'(?<![A-Z0-9])' + re.escape(name) + r'(?![A-Z0-9])', health_text, re.I)}
                if missing_shortlist:
                    errors.append("STAGE2 SHORTLIST MISSING: " + ", ".join(sorted(missing_shortlist)))
            for i in tables:
                table = B[i]
                hdr = [h.strip().lower() for h in table["rows"][0]]
                if "symbol" not in hdr or "timing screen" not in hdr:
                    continue
                sym_i, action_i = hdr.index("symbol"), hdr.index("timing screen")
                for row in table["rows"][1:]:
                    if max(sym_i, action_i) >= len(row):
                        continue
                    action = re.sub(r"[\s_-]+", " ", row[action_i].upper())
                    if "IMMEDIATE BUY" not in action:
                        continue
                    symbol = row[sym_i].strip().upper()
                    item = snapshots.get(symbol, {})
                    tv, ev = item.get("tradingview", {}), item.get("stage2_evaluation", {})
                    a, b, rsi = ev.get("extension_from_10w_ema_pct"), ev.get("extension_from_50d_sma_pct"), tv.get("rsi_14_daily")
                    pe = tv.get("pe_ttm") if tv.get("pe_ttm") is not None else item.get("fundamental_card", {}).get("stock_pe")
                    growth = tv.get("revenue_yoy_growth_ttm_pct") if tv.get("revenue_yoy_growth_ttm_pct") is not None else item.get("fundamental_card", {}).get("sales_qq_pct")
                    close, ema, sma = tv.get("close"), tv.get("ema10_weekly"), tv.get("sma50")
                    gate = ev.get("technical_timing_gate") or ev.get("recommended_verdict")
                    if (any(x is None for x in (a, b, rsi, pe, growth, close, ema, sma))
                            or ema <= 0 or sma <= 0 or pe <= 0 or close / ema > 1.10 or close / sma > 1.12
                            or rsi > 73 or gate not in ("CLEAR_FOR_CONSIDERATION", "IMMEDIATE_BUY")):
                        errors.append(f"STAGE2 ENTRY RULE: {symbol} cannot be presented as immediate buy")
            if F and F.get("asof") not in raw:
                errors.append("STAGE2 SESSION: verified ledger session must appear in the report")
            if not re.search(r"run date", raw, re.I):
                errors.append("STAGE2 SESSION: run date must be disclosed separately")

    # 7b. colour palette: only the tokens defined in .agents/skills/_shared/REPORT_PALETTE.md
    pal_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".agents", "skills", "_shared", "REPORT_PALETTE.md")
    if os.path.isfile(pal_path):
        allowed = {c.lower() for c in re.findall(r"#[0-9a-fA-F]{6}\b", open(pal_path, encoding="utf-8").read())}
        allowed |= {"#ffffff", "#000000"}
        used = {c.lower() for c in re.findall(r"#[0-9a-fA-F]{6}\b", raw)}
        off = sorted(used - allowed)
        if off:
            warns.append(f"COLOURS OUTSIDE THE PALETTE: {', '.join(off[:12])} (use the tokens in REPORT_PALETTE.md)")
    if re.search(r"[\U0001F300-\U0001FAFF\u2600-\u27BF\U0001F7E0-\U0001F7EB]", raw):
        warns.append("EMOJI in report: use the verdict-* classes from REPORT_PALETTE.md instead")

    # 7c. layout: empty slots, key figures, shared stylesheet, mobile-safe tables, viewport
    empty_cells = len(re.findall(r"<t[dh][^>]*>\s*(?:&nbsp;)?\s*</t[dh]>", raw))
    if empty_cells:
        errors.append(f"EMPTY CELLS: {empty_cells} table cell(s) have no value; write N/A with a reason, or remove the slot")
    empty_heads = 0
    parts = re.split(r"(<h[23][^>]*>.*?</h[23]>)", re.sub(r"<style.*?</style>|<script.*?</script>", "", raw, flags=re.S), flags=re.S)
    for i in range(1, len(parts) - 1, 2):
        if len(re.sub(r"<[^>]+>", "", parts[i + 1]).strip()) < 20 and not re.search(r"<table", parts[i + 1]):
            empty_heads += 1
    if empty_heads:
        errors.append(f"EMPTY HEADINGS: {empty_heads} heading(s) with no text under them; remove the heading or write the section")
    if args.kind and not args.partial:
        if not re.search(r'name="viewport"', raw):
            errors.append("NO VIEWPORT META: the report will not scale on phones")
        if "report_base v2" not in raw and not (args.kind == "stage2_sector_momentum" and 'name="report-design" content="research-desk-v1"' in raw):
            errors.append("STYLE NOT BUILT FROM report_base.css (marker 'report_base v2' missing); rebuild the head as SECTION_DRAFTING.md says")
        if not re.search(r'<dl class="key-figures"', raw):
            errors.append("NO KEY FIGURES strip (<dl class=\"key-figures\">): put 4-6 headline numbers under the title")
        wrapped = re.findall(r'<div\b(?=[^>]*\bclass=["\'][^"\']*\btable-wrap\b[^"\']*["\'])[^>]*>\s*<table\b', raw, re.I)
        unwrapped = len(re.findall(r"<table(?![^>]*infobox)", raw)) - len(wrapped)
        if unwrapped > 0:
            warns.append(f"{unwrapped} data table(s) not inside <div class=\"table-wrap\"> (they will break the layout on phones)")
        # citations: every ticker linked, and enough distinct sources
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from report_links import body_sources, missing_ticker_links, symbol_universe
        universe = symbol_universe(args.facts) if getattr(args, "facts", None) else set()
        missing = missing_ticker_links(raw, universe)
        if missing:
            errors.append(f"TICKER LINKS MISSING for {len(missing)} ticker(s) ({', '.join(missing[:10])}): each needs a TradingView chart link and a Screener (IN) or Finviz (US) link; rebuild with scripts/assemble_report.py")
        n_sources = len(body_sources(raw))
        # A full company report (dossier) needs at least 25 distinct primary
        # sources; other report kinds keep the 12-source floor.
        source_floor = 25 if args.report.endswith('_dossier.html') else 12
        if n_sources < source_floor:
            errors.append(f"TOO FEW SOURCES: {n_sources} distinct external source(s) cited; the standard needs at least {source_floor}. Cite the research record's source_url for each figure (the assembler adds a References list from the research file). Run scripts/citation_check.py for the full citation gate (URL-in-cache, value-in-cached-text, as-of).")
    if args.partial:
        pass

    # 8. readability warning (average sentence length in prose)
    prose = " ".join(b["text"] for b in B if b["kind"] == "p")
    sents = [s for s in re.split(r"(?<=[.!?])\s+", prose) if len(s.split()) > 3]
    if sents and sum(len(s.split()) for s in sents) / len(sents) > 26:
        warns.append(f"Average sentence is {sum(len(s.split()) for s in sents) / len(sents):.0f} words; aim for <= 22 so a beginner can follow")

    print(f"{args.report}\n  prose words: {total} | sections: {len(sections)} | data tables: {len(tables)} | "
          f"primer/howto/example/triggers/casenotes: {len(blocks_with('primer'))}/{len(blocks_with('howto'))}/{len(blocks_with('example'))}/"
          f"{len(blocks_with('triggers'))}/{len(cases)} | N/A cells: {na}/{cells} ({pct:.1f}%)")
    if args.partial:
        errors = [e for e in errors if e.startswith(PARTIAL_CHECKS)]
    for w in warns:
        print("  WARN ", w)
    for e in dict.fromkeys(errors):
        print("  FAIL ", e)
    print("RESULT:", "FAIL" if errors else "PASS")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
