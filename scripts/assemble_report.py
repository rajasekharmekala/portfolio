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
import os
import re
import sys
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from report_links import body_sources, linkify, research_sources, symbol_universe  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHARED = os.path.join(ROOT, ".agents", "skills", "_shared")


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


def build(body_raw: str, market: str = "IN", facts: str = "", research: Optional[list] = None) -> str:
    body = wrap_tables(strip_shell(body_raw))
    universe = symbol_universe(facts, *(research or []))
    body, added = linkify(body, market, universe)
    if added:
        print(f"assemble: added {added} ticker link set(s)")
    if not re.search(r'<h2[^>]*id="references"|class="reflist"', body):
        block = references_block(body, research_sources(facts, *(research or [])))
        if block:
            body = body + "\n" + block
    h1 = re.search(r"<h1[^>]*>(.*?)</h1>", body, re.S | re.I)
    title = html.unescape(re.sub(r"<[^>]+>", "", h1.group(1))).strip() if h1 else "Report"
    base = open(os.path.join(SHARED, "report_base.css"), encoding="utf-8").read()
    comp = open(os.path.join(SHARED, "book_components.css"), encoding="utf-8").read()
    style = "\n".join([palette_root(), base, comp])
    return (
        "<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n"
        "<meta charset=\"utf-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
        f"<title>{html.escape(title)}</title>\n"
        f"<style>\n{style}\n</style>\n"
        "</head>\n<body>\n"
        f"<div class=\"report\">\n{body}\n</div>\n"
        "</body>\n</html>\n"
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--body", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--market", choices=["IN", "US"], default="IN")
    ap.add_argument("--facts", default="", help="ledger facts_<MKT>_<date>.json (symbol universe and sources)")
    ap.add_argument("--research", action="append", default=[], help="research_<MKT>_<date>.json (repeatable)")
    a = ap.parse_args()
    raw = open(a.body, encoding="utf-8").read()
    out = build(raw, a.market, a.facts, a.research)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        f.write(out)
    print(f"assembled {a.out}")


if __name__ == "__main__":
    main()
