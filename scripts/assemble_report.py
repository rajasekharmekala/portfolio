#!/usr/bin/env python3
"""Assemble a finished report: build the head <style> from the shared files and wrap the body.

Usage:
  python3 scripts/assemble_report.py --body <RUN_DIR>/work/body.html --out docs/reports/<Name>.html

The body is the section HTML (everything between <body> and </body>, or a bare fragment).
The head is never written by the report writer. This script:
  1. Takes the :root palette block from .agents/skills/_shared/REPORT_PALETTE.md.
  2. Appends report_base.css and book_components.css.
  3. Wraps the body in <div class="report"> and wraps every bare <table class="wikitable">
     in <div class="table-wrap"> (infobox tables are left alone).
  4. Sets the <title> from the first <h1> and adds the viewport meta tag.
"""
import argparse
import html
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
from zoneinfo import ZoneInfo
from bs4 import BeautifulSoup, NavigableString

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from report_links import body_sources, linkify, research_sources, symbol_universe  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHARED = os.path.join(ROOT, ".agents", "skills", "_shared")
GLOSSARY_FILE = os.path.join(ROOT, ".agents", "config", "glossary.json")
DEFINE_MARKERS = (" is ", " are ", " means ", " stands for ", " \u2014 ", " - ")
PLAIN_GLOSS = {
    "20-day moving average": "the 20-day average closing price",
    "50-day moving average": "the 50-day average closing price",
    "200-day moving average": "the 200-day average closing price",
    "Stage 2": "the rising uptrend phase",
    "Stage 4": "the falling downtrend phase",
    "base": "a flat consolidation floor",
    "pivot": "the breakout trigger level",
    "breakout": "a move above resistance",
    "retest": "a pullback that tests prior support",
    "stop loss": "the exit price if the trade is wrong",
    "limit order": "an order capped at a chosen price",
    "entry zone": "the target buy price range",
    "asymmetry": "upside reward relative to downside risk",
    "reward-to-risk": "expected gain divided by stop-loss risk",
    "gross margin": "the share of revenue left after direct costs",
    "operating margin": "the share of revenue left after operating costs",
    "net margin": "the share of revenue left as net profit",
    "debt-to-equity": "total borrowings divided by shareholder equity",
    "net debt": "total debt minus cash and liquid securities",
    "price-to-earnings": "share price divided by earnings per share",
    "free cash flow": "operating cash left after capital spending",
    "cash flow from operations": "cash actually collected by core operations",
    "guidance": "management's official forecast",
    "measured move": "a target projected from the height of the base",
    "book-to-bill": "new orders received divided by revenue billed",
    "take rate": "the fee share kept by a platform",
    "dilution": "the increase in share count that shrinks each share's slice",
    "capital expenditure": "cash spent on long-term plant and equipment",
    "buyback": "company repurchases of its own shares",
    "working capital": "cash tied up in inventory and customer bills minus supplier credit",
    "consensus estimate": "the average forecast of Wall Street or institutional analysts",
}


def _term_rx(term: str) -> re.Pattern:
    return re.compile(r"(?<![A-Za-z0-9])" + re.escape(term) + r"(?![A-Za-z0-9])", re.IGNORECASE)


def auto_glossary(document: BeautifulSoup) -> None:
    """Ensure first prose occurrence of every glossary term is wrapped in <dfn> with its expansion/definition."""
    if not os.path.exists(GLOSSARY_FILE):
        return
    with open(GLOSSARY_FILE, encoding="utf-8") as f:
        glossary = json.load(f)
    skip_tags = {"script", "style", "head", "title", "header", "footer", "nav",
                 "aside", "select", "button", "h1", "h2", "h3", "h4", "h5", "h6",
                 "dt", "th", "caption"}

    def find_first(rx: re.Pattern):
        for node in document.find_all(string=True):
            ancestors = [p.name for p in node.parents if p and p.name]
            if any(t in skip_tags for t in ancestors):
                continue
            if any("key-figures" in (p.get("class") or []) for p in node.parents if hasattr(p, "get")):
                continue
            m = rx.search(str(node))
            if m:
                in_dfn = node.parent.name == "dfn" or any(p.name == "dfn" for p in node.parent.parents)
                para = node.parent.find_parent(["p", "li", "td", "dd"])
                return node, m, in_dfn, para
        return None, None, False, None

    for entry in glossary.get("must_define", []):
        term, exp = entry["term"], entry["expansion"]
        rx = _term_rx(term)
        node, m, in_dfn, para = find_first(rx)
        if node is None or para is None:
            continue
        where = str(para.get_text(" ", strip=True))
        need_exp = exp.lower() not in where.lower()
        if in_dfn and not need_exp:
            continue
        if in_dfn and need_exp:
            dfn_tag = node.parent if node.parent.name == "dfn" else node.parent.find_parent("dfn")
            if dfn_tag is not None:
                dfn_tag.insert_after(NavigableString(f" ({exp})"))
            continue
        text = str(node)
        before, matched, after = text[:m.start()], text[m.start():m.end()], text[m.end():]
        dfn_tag = document.new_tag("dfn")
        dfn_tag.string = matched
        tail = f" ({exp})" + after if need_exp else after
        node.replace_with(NavigableString(before), dfn_tag, NavigableString(tail))

    for term in glossary.get("plain", []):
        rx = _term_rx(term)
        node, m, in_dfn, para = find_first(rx)
        if node is None or para is None:
            continue
        where = " " + str(para.get_text(" ", strip=True)).lower() + " "
        has_marker = any(mk in where for mk in DEFINE_MARKERS)
        if in_dfn and has_marker:
            continue
        gloss = PLAIN_GLOSS.get(term, "a key operating metric")
        if in_dfn and not has_marker:
            dfn_tag = node.parent if node.parent.name == "dfn" else node.parent.find_parent("dfn")
            if dfn_tag is not None:
                dfn_tag.insert_after(NavigableString(f" — {gloss} —"))
            continue
        text = str(node)
        before, matched, after = text[:m.start()], text[m.start():m.end()], text[m.end():]
        dfn_tag = document.new_tag("dfn")
        dfn_tag.string = matched
        tail = (f" — {gloss} —" + after) if not has_marker else after
        node.replace_with(NavigableString(before), dfn_tag, NavigableString(tail))


def palette_root() -> str:
    text = open(os.path.join(SHARED, "REPORT_PALETTE.md"), encoding="utf-8").read()
    m = re.search(r"```css\s*(:root\s*\{.*?\})\s*```", text, re.S)
    if not m:
        sys.exit("assemble: no :root block found in REPORT_PALETTE.md")
    return m.group(1)


def strip_shell(body: str) -> str:
    m = re.search(r"<body[^>]*>(.*)</body>", body, re.S | re.I)
    body = m.group(1) if m else body
    # drop any writer-supplied head pieces that could fight the shared stylesheet
    body = re.sub(r"<style[^>]*>.*?</style>", "", body, flags=re.S | re.I)
    body = re.sub(r"<link[^>]*>", "", body, flags=re.I)
    return body.strip()


def wrap_tables(body: str) -> str:
    def repl(m: re.Match) -> str:
        return f'<div class="table-wrap">{m.group(0)}</div>'
    return re.sub(r'<table class="wikitable".*?</table>', repl, body, flags=re.S)


def references_block(body: str, research: list) -> str:
    """One References list: every external link in the body plus every research source, deduplicated."""
    rows, seen = [], set()
    for url, label in body_sources(body):
        if url not in seen:
            seen.add(url)
            rows.append((url, label, ""))
    for url, title, as_of, sym in research:
        if url in seen:
            continue
        seen.add(url)
        label = " — ".join(x for x in (sym, title) if x) or url
        rows.append((url, label, as_of))
    if not rows:
        return ""
    items = []
    for url, label, as_of in rows:
        suffix = f" (retrieved {html.escape(as_of)})" if as_of else ""
        items.append(f'<li><a href="{html.escape(url, quote=True)}">{html.escape(label)}</a>{suffix}</li>')
    return ('<h2 id="references">References</h2>\n<ol class="reflist">\n' + "\n".join(items) + "\n</ol>")


def build(body_raw: str, market: str = "IN", facts: str = "", research: Optional[list] = None,
          generated_at: Optional[datetime] = None, kind: str = "report", workflow: str = "",
          as_of: str = "", layout_only: bool = False) -> str:
    generated = generated_at or datetime.now(ZoneInfo("America/Los_Angeles"))
    if generated.tzinfo is None or generated.utcoffset() is None:
        raise ValueError("generated_at must include a timezone")
    generated = generated.astimezone(ZoneInfo("America/Los_Angeles"))
    if market not in {"IN", "US"} or kind not in {"report", "dossier"}:
        raise ValueError("Choose market IN/US and kind report/dossier")
    source = BeautifulSoup(body_raw, "html.parser")
    content = source.select_one("main.report") or source.select_one(".report") or source.body or source
    for decoration in content.select("style, script, link, .report-generated, .report-as-of"):
        decoration.decompose()
    for wrapper in list(content.select(".report-header, .report")):
        wrapper.unwrap()
    for table in content.select("table:not(.infobox)"):
        if "table-wrap" not in table.parent.get("class", []):
            wrapper = source.new_tag("div", attrs={"class": "table-wrap"})
            table.wrap(wrapper)
    body = content.decode_contents()
    if not layout_only:
        universe = symbol_universe(facts, *(research or []))
        body, added = linkify(body, market, universe)
        if added:
            print(f"assemble: added {added} ticker link set(s)")
        parsed = BeautifulSoup(body, "html.parser")
        if not parsed.select_one(".reflist, #references, #notes"):
            block = references_block(body, research_sources(facts, *(research or [])))
            if block:
                body += "\n" + block
    document = BeautifulSoup(body, "html.parser")
    if not layout_only:
        auto_glossary(document)
    heading = document.find("h1")
    title = heading.get_text(" ", strip=True) if heading else "Report"
    if heading is None:
        heading = document.new_tag("h1")
        heading.string = title
        document.insert(0, heading)
    header = document.new_tag("header", attrs={"class": "report-header"})
    heading.wrap(header)
    label = "Layout updated" if layout_only else "Generated Date:"
    stamp = document.new_tag("p", attrs={"class": "report-generated"})
    stamp.append(label + " ")
    time = document.new_tag("time", attrs={"datetime": generated.isoformat()})
    time.string = generated.strftime("%d %b %Y, %I:%M %p %Z")
    stamp.append(time)
    header.append(stamp)
    if layout_only:
        notice = document.new_tag("p", attrs={"class": "report-as-of"})
        notice.string = "Generated Date: not recorded for the original research. Presentation update only."
        header.append(notice)
    if as_of:
        cutoff = document.new_tag("p", attrs={"class": "report-as-of"})
        cutoff.string = "Research as of " + as_of
        header.append(cutoff)
    body = str(document)
    style = "\n".join([palette_root()] + [Path(SHARED, name).read_text(encoding="utf-8")
                        for name in ("report_base.css", "book_components.css", "report_desk.css")])
    script = Path(SHARED, "report_desk.js").read_text(encoding="utf-8")
    workflow = workflow or ("Company research" if kind == "dossier" else "Research report")
    metadata = {"report-design": "research-desk-v1", "report-market": market,
                "report-kind": kind, "report-workflow": workflow, "research-as-of": as_of,
                "layout-updated-at" if layout_only else "generated-at": generated.isoformat()}
    meta = "\n".join(f'<meta name="{name}" content="{html.escape(value, quote=True)}">' for name, value in metadata.items())
    return (
        '<!DOCTYPE html>\n<html lang="en"><head><meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f'{meta}\n<title>{html.escape(title)}</title>\n'
        '<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&amp;family=IBM+Plex+Mono:wght@400;500&amp;family=Newsreader:opsz,wght@6..72,500;6..72,600&amp;display=swap" rel="stylesheet">\n'
        f'<style>\n{style}\n</style></head><body id="top">\n'
        '<progress class="desk-progress" max="100" value="0" aria-label="Reading progress" hidden></progress>\n'
        '<header class="desk-masthead"><a class="desk-wordmark" href="../index.html">RESEARCH / DESK</a>'
        f'<span class="desk-label">{"India" if market == "IN" else "US"} / {html.escape(workflow)}</span>'
        '<div class="desk-tools"><label class="desk-sr-only" for="desk-section">Report section</label>'
        '<select id="desk-section" hidden><option value="">Contents</option></select>'
        '<button id="desk-print" title="Print report" aria-label="Print report" hidden>'
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
        '<path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/>'
        '<path d="M6 9V3a1 1 0 0 1 1-1h10a1 1 0 0 1 1 1v6"/><rect x="6" y="14" width="12" height="8" rx="1"/></svg>'
        '</button></div></header>\n'
        f'<div class="desk-layout"><main class="report">{body}</main>'
        '<aside class="desk-contents" aria-label="Report contents" hidden><p class="desk-contents-label">CONTENTS</p><ol></ol></aside></div>\n'
        '<footer class="desk-footer"><span>Portfolio Research Desk</span><a href="#top">Back to top</a></footer>\n'
        f'<script data-report-desk>\n{script}\n</script></body></html>\n'
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--body", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--market", choices=["IN", "US"], default="IN")
    ap.add_argument("--facts", default="", help="ledger facts_<MKT>_<date>.json (symbol universe and sources)")
    ap.add_argument("--research", action="append", default=[], help="research_<MKT>_<date>.json (repeatable)")
    ap.add_argument("--kind", choices=["report", "dossier"], default="report")
    ap.add_argument("--workflow", default="")
    ap.add_argument("--as-of", default="", help="Verified research cutoff, not generation time")
    ap.add_argument("--layout-only", action="store_true", help="Restyle existing research; label date as layout update, never new research")
    a = ap.parse_args()
    raw = Path(a.body).read_text(encoding="utf-8")
    out = build(raw, a.market, a.facts, a.research, kind=a.kind, workflow=a.workflow,
                as_of=a.as_of, layout_only=a.layout_only)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        f.write(out)
    print(f"assembled {a.out}")


if __name__ == "__main__":
    main()
