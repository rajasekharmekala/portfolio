#!/usr/bin/env python3
"""
EPUB 3 & Narrative Markdown Builder for Company Investment Monographs (scripts/epub_builder.py).

Produces two synchronized audiobook/e-reader artifacts from the canonical monograph chapter spine:
  1. docs/blogs/<MKT>/<SYMBOL>_book.epub  (Standards-compliant EPUB 3 package)
  2. docs/blogs/<MKT>/<SYMBOL>_book.md    (Clean chapter-structured Markdown for book-companion / TTS)
"""
from __future__ import annotations

import datetime as dt
import html
import re
import uuid
import zipfile
from pathlib import Path
from typing import Any, Dict, List


def _clean_audio_text(raw: str) -> str:
    """Strip inline citation superscripts and HTML tags while preserving clean spoken text."""
    text = re.sub(r"<sup[^>]*>.*?</sup>", "", raw or "", flags=re.S | re.I)
    text = re.sub(r"\[\d+(?:[,\u2013\-]\s*\d+)*\]", "", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def _xhtml_paragraph(raw: str) -> str:
    return f"<p>{html.escape(_clean_audio_text(raw))}</p>"


EPUB_CSS = """\
body {
  font-family: Georgia, "Iowan Old Style", "Palatino Linotype", Palatino, serif;
  line-height: 1.68;
  color: #111111;
  margin: 1.2em 1em;
}
h1, h2, h3 {
  font-family: Optima, "Century Gothic", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  color: #174a61;
  line-height: 1.28;
}
h1 {
  font-size: 1.65em;
  border-bottom: 2px solid #174a61;
  padding-bottom: 0.35em;
  margin-bottom: 0.5em;
}
h2 {
  font-size: 1.35em;
  border-bottom: 1px solid #cccccc;
  padding-bottom: 0.25em;
  margin-top: 1.6em;
}
h3 {
  font-size: 1.12em;
  margin-top: 1.3em;
}
.kicker {
  font-size: 0.85em;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #556677;
  font-weight: bold;
  margin-bottom: 0.25em;
}
.verdict-box {
  background: #fdfbe8;
  border: 1px solid #d4a017;
  border-left: 5px solid #d4a017;
  padding: 0.85em 1em;
  margin: 1em 0 1.4em;
}
.verdict-box p {
  margin: 0.35em 0;
}
.chapter-question {
  background: #f4f6f8;
  border-left: 4px solid #174a61;
  padding: 0.6em 0.9em;
  font-style: italic;
  color: #223344;
  margin: 0.75em 0 1.25em;
}
p {
  margin: 0.65em 0;
  text-align: justify;
}
ol.sources {
  font-size: 0.88em;
  line-height: 1.45;
}
ol.sources li {
  margin: 0.4em 0;
}
"""


def build_markdown_book(
    spec: Dict[str, Any],
    chapters: List[Dict[str, Any]],
    key_figures: List[tuple[str, str]],
    audio_minutes: int,
    total_words: int,
    out_md_path: str | Path,
) -> Path:
    sym = spec["symbol"].upper()
    market = spec["market"].upper()
    as_of = spec.get("as_of", "")
    title = spec.get("book_title") or f"{spec['title']} — The Investment & Audiobook Monograph"

    lines: List[str] = [
        "---",
        f'title: "{title.replace(chr(34), chr(39))}"',
        f"symbol: {sym}",
        f"market: {market}",
        f"as_of: {as_of}",
        f"verdict: {spec.get('verdict', '')}",
        f"entry_posture: {spec.get('entry_posture', '')}",
        f"word_count: {total_words}",
        f"estimated_audio_minutes: {audio_minutes}",
        "---",
        "",
        f"# {title}",
        "",
        f"**Market:** {market} | **Symbol:** `{sym}` | **Research Cutoff:** {as_of} | "
        f"**Length:** {total_words:,} words (~{audio_minutes} min audiobook)",
        "",
        "## Executive Verdict & Price Card",
        "",
    ]
    for k, v in key_figures:
        clean_v = _clean_audio_text(v)
        lines.append(f"- **{k}:** {clean_v}")
    lines.append("")
    lines.append("---")
    lines.append("")

    for idx, ch in enumerate(chapters):
        b_title = ch.get("book_title") or ch.get("web_title") or f"Chapter {idx}"
        question = ch.get("question") or ch.get("kicker") or ""
        lines.append(f"## {b_title}")
        lines.append("")
        if question:
            lines.append(f"> **Core Investor Question:** {_clean_audio_text(question)}")
            lines.append("")
        for p in ch.get("book_paragraphs", []):
            lines.append(_clean_audio_text(p))
            lines.append("")
        for sub in ch.get("book_subsections", []):
            if sub.get("title"):
                lines.append(f"### {_clean_audio_text(sub['title'])}")
                lines.append("")
            for p in sub.get("paragraphs", []):
                lines.append(_clean_audio_text(p))
                lines.append("")
        lines.append("---")
        lines.append("")

    lines.append("## Sources & Primary Filings Appendix")
    lines.append("")
    for i, c in enumerate(spec.get("citations", []), 1):
        lines.append(f"{i}. {_clean_audio_text(c)}")
    lines.append("")

    out_p = Path(out_md_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    out_p.write_text("\n".join(lines), encoding="utf-8")
    return out_p


def build_epub_book(
    spec: Dict[str, Any],
    chapters: List[Dict[str, Any]],
    key_figures: List[tuple[str, str]],
    audio_minutes: int,
    total_words: int,
    out_epub_path: str | Path,
) -> Path:
    sym = spec["symbol"].upper()
    market = spec["market"].upper()
    as_of = spec.get("as_of", dt.date.today().isoformat())
    book_title = spec.get("book_title") or f"{spec['title']} — Investment & Audiobook Monograph"
    book_uid = f"urn:uuid:{uuid.uuid5(uuid.NAMESPACE_URL, f'https://rajasekharmekala.github.io/portfolio/{market}/{sym}/{as_of}')}"
    modified_iso = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    out_p = Path(out_epub_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)

    # Build XHTML chapter files
    xhtml_files: List[tuple[str, str, str, str]] = []  # (id, filename, title, content)

    # 1. Cover / Executive Verdict Card
    kf_rows = "\n".join(
        f"<p><strong>{html.escape(k)}:</strong> {html.escape(_clean_audio_text(v))}</p>"
        for k, v in key_figures
    )
    cover_xhtml = f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
<head>
  <meta charset="utf-8" />
  <title>{html.escape(book_title)}</title>
  <link rel="stylesheet" type="text/css" href="style.css" />
</head>
<body>
  <p class="kicker">Portfolio Research Desk • {html.escape(market)} Investment Monograph • As of {html.escape(as_of)}</p>
  <h1>{html.escape(book_title)}</h1>
  <p><em>Audio &amp; Reading Edition: {total_words:,} words (approx. {audio_minutes} minutes listening time)</em></p>
  <div class="verdict-box">
    <h3>Executive Price &amp; Opportunity Card</h3>
    {kf_rows}
  </div>
</body>
</html>"""
    xhtml_files.append(("cover", "cover.xhtml", "Title & Executive Verdict Card", cover_xhtml))

    # 2. Narrative Chapters
    for idx, ch in enumerate(chapters):
        ch_id = f"ch_{idx:02d}"
        fname = f"{ch_id}.xhtml"
        b_title = _clean_audio_text(ch.get("book_title") or ch.get("web_title") or f"Chapter {idx}")
        question = _clean_audio_text(ch.get("question") or ch.get("kicker") or "")
        body_parts: List[str] = []
        if question:
            body_parts.append(f'<div class="chapter-question"><strong>Core Investor Question:</strong> {html.escape(question)}</div>')
        for p in ch.get("book_paragraphs", []):
            body_parts.append(_xhtml_paragraph(p))
        for sub in ch.get("book_subsections", []):
            if sub.get("title"):
                body_parts.append(f"<h3>{html.escape(_clean_audio_text(sub['title']))}</h3>")
            for p in sub.get("paragraphs", []):
                body_parts.append(_xhtml_paragraph(p))
        ch_xhtml = f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
<head>
  <meta charset="utf-8" />
  <title>{html.escape(b_title)}</title>
  <link rel="stylesheet" type="text/css" href="style.css" />
</head>
<body>
  <h2>{html.escape(b_title)}</h2>
  {chr(10).join(body_parts)}
</body>
</html>"""
        xhtml_files.append((ch_id, fname, b_title, ch_xhtml))

    # 3. Sources & Filings Appendix
    cite_items = "\n".join(
        f"<li>{html.escape(_clean_audio_text(c))}</li>"
        for c in spec.get("citations", [])
    )
    sources_xhtml = f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
<head>
  <meta charset="utf-8" />
  <title>Sources &amp; Primary Filings</title>
  <link rel="stylesheet" type="text/css" href="style.css" />
</head>
<body>
  <h2>Sources &amp; Primary Filings</h2>
  <ol class="sources">
    {cite_items}
  </ol>
</body>
</html>"""
    xhtml_files.append(("sources", "sources.xhtml", "Sources & Primary Filings", sources_xhtml))

    # Navigation documents (nav.xhtml + toc.ncx)
    nav_lis = "\n      ".join(
        f'<li><a href="{fname}">{html.escape(t)}</a></li>'
        for _, fname, t, _ in xhtml_files
    )
    nav_xhtml = f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="en" lang="en">
<head>
  <meta charset="utf-8" />
  <title>Contents — {html.escape(book_title)}</title>
  <link rel="stylesheet" type="text/css" href="style.css" />
</head>
<body>
  <nav epub:type="toc" id="toc">
    <h1>Contents</h1>
    <ol>
      {nav_lis}
    </ol>
  </nav>
</body>
</html>"""

    ncx_points = "\n    ".join(
        f'<navPoint id="navPoint-{i}" playOrder="{i}"><navLabel><text>{html.escape(t)}</text></navLabel><content src="{fname}"/></navPoint>'
        for i, (_, fname, t, _) in enumerate(xhtml_files, 1)
    )
    toc_ncx = f"""<?xml version="1.0" encoding="utf-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
  <head>
    <meta name="dtb:uid" content="{book_uid}"/>
    <meta name="dtb:depth" content="1"/>
    <meta name="dtb:totalPageCount" content="0"/>
    <meta name="dtb:maxPageNumber" content="0"/>
  </head>
  <docTitle><text>{html.escape(book_title)}</text></docTitle>
  <navMap>
    {ncx_points}
  </navMap>
</ncx>"""

    manifest_items = [
        '<item id="style" href="style.css" media-type="text/css"/>',
        '<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>',
        '<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>',
    ] + [
        f'<item id="{cid}" href="{fname}" media-type="application/xhtml+xml"/>'
        for cid, fname, _, _ in xhtml_files
    ]
    spine_items = [f'<itemref idref="{cid}"/>' for cid, _, _, _ in xhtml_files]

    content_opf = f"""<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="BookId" xml:lang="en">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="BookId">{book_uid}</dc:identifier>
    <dc:title>{html.escape(book_title)}</dc:title>
    <dc:language>en</dc:language>
    <dc:creator>Portfolio Research Desk</dc:creator>
    <dc:publisher>Portfolio Research Desk</dc:publisher>
    <dc:date>{html.escape(as_of)}</dc:date>
    <dc:description>Comprehensive Investment &amp; Audiobook Monograph for {html.escape(sym)} ({html.escape(market)}) as of {html.escape(as_of)}</dc:description>
    <meta property="dcterms:modified">{modified_iso}</meta>
  </metadata>
  <manifest>
    {chr(10).join("    " + m for m in manifest_items)}
  </manifest>
  <spine toc="ncx">
    {chr(10).join("    " + s for s in spine_items)}
  </spine>
</package>"""

    container_xml = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>"""

    with zipfile.ZipFile(out_p, "w") as zf:
        # EPUB spec requires uncompressed mimetype as first entry
        zf.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        zf.writestr("META-INF/container.xml", container_xml, compress_type=zipfile.ZIP_DEFLATED)
        zf.writestr("OEBPS/style.css", EPUB_CSS, compress_type=zipfile.ZIP_DEFLATED)
        zf.writestr("OEBPS/content.opf", content_opf, compress_type=zipfile.ZIP_DEFLATED)
        zf.writestr("OEBPS/nav.xhtml", nav_xhtml, compress_type=zipfile.ZIP_DEFLATED)
        zf.writestr("OEBPS/toc.ncx", toc_ncx, compress_type=zipfile.ZIP_DEFLATED)
        for _, fname, _, content in xhtml_files:
            zf.writestr(f"OEBPS/{fname}", content, compress_type=zipfile.ZIP_DEFLATED)

    return out_p
