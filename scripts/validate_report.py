#!/usr/bin/env python3
"""
Pre-send gate for newsletters and portfolio audits ("book edition"). Fails (exit 1) when a report is a data
dump, is too thin to teach a beginner, has too many N/A cells, contradicts the facts ledger, lacks a sourced
web-research record, or has unrendered/boilerplate content.

Usage:
  python3 scripts/validate_report.py --report googledrive/newsletters/US_Market_Intelligence_2026-09-28.html \
      --kind market_intel --facts scripts/.cache/facts_US_2026-09-28.json
  --kind: market_intel | portfolio_audit

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
]
STOP = {"N/A", "ETF", "USD", "INR", "NSE", "BSE", "CFO", "NET", "PASS", "EXIT", "HOLD", "TRIM", "BUY", "CORE", "TOTAL"}
THRESH = {
    "market_intel": dict(h2=600, total=9000, intro=50, take=120, casenotes=12, howto=6, triggers=6, primer=450),
    "portfolio_audit": dict(h2=500, total=9000, intro=50, take=120, casenotes=12, howto=6, triggers=8, primer=450),
}
CASE_MIN_WORDS = 80


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


def words(s):
    return len(re.findall(r"[A-Za-z0-9$₹%.,'’-]+", s))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", required=True)
    ap.add_argument("--kind", required=True, choices=list(THRESH))
    ap.add_argument("--facts")
    ap.add_argument("--max-na-pct", type=float, default=5.0)
    ap.add_argument("--price-tol-pct", type=float, default=1.5)
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
    for s in sections:
        if not re.search(r"reference|disclosure|methodology|glossary", s["title"], re.I) and s["words"] < T["h2"]:
            errors.append(f"THIN SECTION '{s['title'][:60]}': {s['words']} prose words < {T['h2']}")
    if total < T["total"]:
        errors.append(f"TOTAL PROSE {total} words < {T['total']} (not book-length; a beginner cannot learn the reasoning from this)")

    # 2. beginner scaffolding: primer, how-to-read blocks, worked example, triggers, case notes
    def blocks_with(c):
        return [b for b in B if b["kind"] == "p" and c in b.get("cls", "")]
    primers = blocks_with("primer")
    if not primers or max(words(p["text"]) for p in primers) < T["primer"]:
        errors.append(f"NO 'START HERE' PRIMER (<div class=\"primer\">, >= {T['primer']} words explaining the report, key terms with analogies, and how to read it)")
    if len(blocks_with("howto")) < T["howto"]:
        errors.append(f"HOW-TO-READ blocks: {len(blocks_with('howto'))} < {T['howto']} (<div class=\"howto\"> before tables; explain each column and read one real row aloud)")
    if not blocks_with("example"):
        errors.append("NO WORKED EXAMPLE (<div class=\"example\"> walking one real number chain from data to decision, e.g. position-size and stop arithmetic)")
    if len(blocks_with("triggers")) < T["triggers"]:
        errors.append(f"TRIGGER blocks: {len(blocks_with('triggers'))} < {T['triggers']} (<div class=\"triggers\">: 'what would change this view' with explicit if/then levels)")
    cases = blocks_with("casenote")
    if len(cases) < T["casenotes"]:
        errors.append(f"CASE NOTES: {len(cases)} < {T['casenotes']} (<div class=\"casenote\"> per stock/position: story, numbers with meaning, verdict, rule that triggered it, what changes it)")
    for c in cases:
        t = c["text"]
        if words(t) < CASE_MIN_WORDS:
            errors.append(f"CASE NOTE TOO SHORT ({words(t)} words < {CASE_MIN_WORDS}): '{t[:50]}...'")
        elif not re.search(r"\d", t) or not re.search(r"\b(if|unless|until|would|trigger|below|above|breaks?|closes?)\b", t, re.I):
            errors.append(f"CASE NOTE LACKS NUMBERS OR IF/THEN TRIGGER: '{t[:50]}...'")
    if args.kind == "portfolio_audit" and F:
        holds = [s for s, m in F["instruments"].items() if "holding" in m.get("roles", []) and not m.get("error")]
        alltext = " ".join(c["text"] for c in cases)
        missing = [s for s in holds if not re.search(rf"(?<![A-Z0-9]){re.escape(s)}(?![A-Z0-9])", alltext)]
        if missing:
            errors.append(f"HOLDINGS WITHOUT A CASE NOTE ({len(missing)}/{len(holds)}): {', '.join(missing[:20])}")
    if not any(re.search(r"glossary", b["text"], re.I) for b in B if b["kind"] in ("h2", "h3")):
        errors.append("NO GLOSSARY heading")

    # 3. every data table needs a reading-guide before it and a takeaway after it
    tables = [i for i, b in enumerate(B) if b["kind"] == "table" and not b["infobox"] and len(b["rows"]) > 2]
    for i in tables:
        prev = next((B[j] for j in range(i - 1, -1, -1) if B[j]["kind"] != "h3"), None)
        nxt = B[i + 1] if i + 1 < len(B) else None
        title = next((B[j]["text"] for j in range(i - 1, -1, -1) if B[j]["kind"] in ("h3", "h2")), "?")[:55]
        if not prev or prev["kind"] != "p" or words(prev["text"]) < T["intro"]:
            errors.append(f"TABLE WITHOUT INTRO / HOW-TO-READ (>= {T['intro']} words) under '{title}'")
        if not nxt or nxt["kind"] != "p" or words(nxt["text"]) < T["take"]:
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
        rpath = os.path.join(os.path.dirname(os.path.abspath(args.facts)), "..", "..", F.get("research_file", ""))
        if not os.path.isfile(rpath):
            errors.append(f"NO WEB RESEARCH RECORD at {F.get('research_file')} (use the duck-duck-go MCP for every research_needs item)")
        else:
            got = {}
            for it in json.load(open(rpath)).get("items", []):
                got.setdefault(it.get("key"), []).append(it)
            for need in F.get("research_needs", []):
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

    # 8. readability warning (average sentence length in prose)
    prose = " ".join(b["text"] for b in B if b["kind"] == "p")
    sents = [s for s in re.split(r"(?<=[.!?])\s+", prose) if len(s.split()) > 3]
    if sents and sum(len(s.split()) for s in sents) / len(sents) > 26:
        warns.append(f"Average sentence is {sum(len(s.split()) for s in sents) / len(sents):.0f} words; aim for <= 22 so a beginner can follow")

    print(f"{args.report}\n  prose words: {total} | sections: {len(sections)} | data tables: {len(tables)} | "
          f"primer/howto/example/triggers/casenotes: {len(primers)}/{len(blocks_with('howto'))}/{len(blocks_with('example'))}/"
          f"{len(blocks_with('triggers'))}/{len(cases)} | N/A cells: {na}/{cells} ({pct:.1f}%)")
    for w in warns:
        print("  WARN ", w)
    for e in dict.fromkeys(errors):
        print("  FAIL ", e)
    print("RESULT:", "FAIL" if errors else "PASS")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
