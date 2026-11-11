#!/usr/bin/env python3
"""
Monograph Companion Book Builder (narrative HTML + WeasyPrint PDF).

The narrative HTML is an internal intermediate: it is never published as a
standalone page. It is rasterized by WeasyPrint into the single PDF edition
that accompanies the Web Research Dossier.

Matches the literary design and narrative flow of:
  - Indian_Market_Intelligence_Nov4_2026_Book_Companion.pdf ("The Anatomy of the Tape")
  - Indian_Portfolio_Audit_Nov4_2026_Book_Companion.pdf ("The Portfolio Architect")

Visual & Editorial Signature:
  - Warm archival cream paper (#fdfbf7 / #fbf8f2), deep charcoal ink (#1a1a1a),
    Oxford navy (#0f2738 / #17344a), and antique gold (#d4af37 / #c99738).
  - Typography: Cinzel (display/chapter numerals/drop-caps), Newsreader (literary serif body & headings),
    Inter (kickers, callout headers, stat strips), JetBrains Mono (prices, multiples, tickers).
  - Chapter Architecture: Roman numeral kicker, monumental serif title, framed italic Epigraph Quote,
    Drop-Cap opening paragraph in second-person mentor voice, and interleaved callout boxes:
      * NARRATOR'S REFLECTION (gold-bordered italic reflection)
      * GLOBAL PARALLEL (US / INDIA / EUROPE comparative company case study)
      * MENTAL MODEL (navy-bordered conceptual framework)
"""
from __future__ import annotations

import datetime as dt
import html
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List
from zoneinfo import ZoneInfo

ROMAN = ["PROLOGUE", "CHAPTER I", "CHAPTER II", "CHAPTER III", "CHAPTER IV", "CHAPTER V",
         "CHAPTER VI", "CHAPTER VII", "CHAPTER VIII", "CHAPTER IX", "CHAPTER X"]


def _clean_audio_text(raw: str) -> str:
    """Strip inline citation superscripts and HTML tags while preserving clean spoken text."""
    text = re.sub(r"<sup[^>]*>.*?</sup>", "", raw or "", flags=re.S | re.I)
    text = re.sub(r"\[\d+(?:[,\u2013\-]\s*\d+)*\]", "", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def _strip_chapter_prefix(title: str) -> str:
    """Remove leading 'Prologue:' or 'Chapter N:' so the Roman numeral kicker stands cleanly above."""
    t = _clean_audio_text(title)
    t = re.sub(r"^(?:Prologue|Chapter\s+\d+|Chapter\s+[IVXLC]+)\s*[:\-\u2014]\s*", "", t, flags=re.I)
    t = re.sub(r"^\d+\.\s*", "", t)
    return t.strip() or title


def _render_book_callout_xhtml(callout: Dict[str, Any]) -> str:
    kind = (callout.get("kind") or "reflection").lower()
    label = _clean_audio_text(callout.get("label") or "")
    title = _clean_audio_text(callout.get("title") or "")
    text = _clean_audio_text(callout.get("text") or "")
    quote = _clean_audio_text(callout.get("quote") or "")
    bullets = [_clean_audio_text(b) for b in callout.get("bullets", []) if _clean_audio_text(b)]

    if kind == "parallel":
        default_prefix = "GLOBAL PARALLEL"
        cls = "mc-box mc-box-parallel"
    elif kind == "mental_model":
        default_prefix = "MENTAL MODEL"
        cls = "mc-box mc-box-model"
    elif kind == "execution":
        default_prefix = "THE EXECUTION PLAYBOOK"
        cls = "mc-box mc-box-exec"
    else:
        default_prefix = "NARRATOR'S REFLECTION"
        cls = "mc-box mc-box-reflection"

    header_text = f"{label} • {title}" if (label and title) else (title or label or default_prefix)
    if not header_text.upper().startswith(("NARRATOR", "GLOBAL PARALLEL", "PARALLEL", "MENTAL MODEL", "THE ")):
        header_text = f"{default_prefix} • {header_text}"

    parts = [f'<aside class="{cls}">', f'<div class="mc-box-header">{html.escape(header_text)}</div>']
    if quote:
        parts.append(f'<p class="mc-box-quote">"{html.escape(quote)}"</p>')
    if text:
        parts.append(f'<p class="mc-box-body">{html.escape(text)}</p>')
    if bullets:
        li_html = "".join(f"<li>{html.escape(b)}</li>" for b in bullets)
        parts.append(f'<ul class="mc-box-list">{li_html}</ul>')
    parts.append("</aside>")
    return "\n".join(parts)


MASTERCLASS_BOOK_CSS = """\
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@600;700&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@500;700&family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,600;1,6..72,400&display=swap');

:root {
  --mc-paper:        #fdfbf7;
  --mc-paper-alt:    #f6f1e7;
  --mc-ink:          #1a1a1a;
  --mc-ink-muted:    #475467;
  --mc-navy:         #0f2738;
  --mc-navy-mid:     #17344a;
  --mc-blue:         #1a5276;
  --mc-gold:         #c99738;
  --mc-gold-bright:  #d4af37;
  --mc-gold-soft:    #ebd8ab;
  --mc-gold-tint:    #fbf6e9;
  --mc-blue-tint:    #f2f7fb;
  --mc-green-tint:   #eef6f0;
  --mc-green-ink:    #145a32;
  --mc-crimson:      #8b1e1e;
  --mc-rule:         #dcd3c2;
  --font-display:    'Cinzel', 'Trajan Pro', 'Palatino Linotype', Georgia, serif;
  --font-serif:      'Newsreader', 'Iowan Old Style', 'Palatino Linotype', Palatino, Georgia, serif;
  --font-sans:       'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  --font-mono:       'JetBrains Mono', 'Inconsolata', 'SFMono-Regular', Menlo, monospace;
}

* { box-sizing: border-box; }

html {
  font-size: 16px;
  scroll-behavior: smooth;
  background: #ebe5d8;
}

body {
  margin: 0;
  background: var(--mc-paper);
  color: var(--mc-ink);
  font-family: var(--font-serif);
  line-height: 1.78;
  -webkit-font-smoothing: antialiased;
}

/* Top Interactive Audiobook & Edition Bar (Screen only) */
.mc-topbar {
  position: sticky;
  top: 0;
  z-index: 50;
  background: var(--mc-navy);
  color: #ffffff;
  border-bottom: 2px solid var(--mc-gold);
  padding: 0.55rem 1.25rem;
  font-family: var(--font-sans);
  font-size: 0.82rem;
}
.mc-topbar-inner {
  max-width: 980px;
  margin: 0 auto;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.65rem 1rem;
}
.mc-edition-links {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.45rem;
}
.mc-edition-links a {
  color: #e2e8f0;
  text-decoration: none;
  padding: 0.28rem 0.65rem;
  border: 1px solid rgba(212, 175, 55, 0.4);
  border-radius: 2px;
  font-weight: 600;
  font-size: 0.78rem;
}
.mc-edition-links a:hover,
.mc-edition-links a.is-active {
  background: var(--mc-gold);
  color: var(--mc-navy);
  border-color: var(--mc-gold);
}
.mc-audio-controls {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.4rem;
}
.mc-audio-btn {
  padding: 0.28rem 0.68rem;
  border: 1px solid var(--mc-gold);
  background: var(--mc-gold);
  color: var(--mc-navy);
  font-family: var(--font-sans);
  font-size: 0.78rem;
  font-weight: 700;
  border-radius: 2px;
  cursor: pointer;
}
.mc-audio-btn.secondary {
  background: transparent;
  color: #ffffff;
  border-color: rgba(255, 255, 255, 0.35);
}
.mc-audio-btn:hover {
  background: #e5c158;
  color: var(--mc-navy);
}
.mc-audio-select {
  padding: 0.24rem 0.45rem;
  border: 1px solid rgba(255, 255, 255, 0.35);
  background: var(--mc-navy-mid);
  color: #ffffff;
  font-family: var(--font-sans);
  font-size: 0.76rem;
}
.mc-audio-status {
  color: var(--mc-gold-soft);
  font-family: var(--font-mono);
  font-size: 0.75rem;
}

/* Book Container */
.mc-book-shell {
  max-width: 820px;
  margin: 0 auto;
  padding: 2.5rem 3.25rem 5rem;
  background: var(--mc-paper);
  box-shadow: 0 4px 28px rgba(15, 39, 56, 0.08);
}

/* Page 1: Masterclass Cover Page */
.mc-cover {
  min-height: 78vh;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 3.2rem 2.6rem;
  margin-bottom: 3.5rem;
  background: linear-gradient(165deg, #0f2738 0%, #17344a 65%, #102a3d 100%);
  color: #ffffff;
  border: 2px solid var(--mc-gold);
  box-shadow: inset 0 0 0 6px rgba(212, 175, 55, 0.18);
  page-break-after: always;
}
.mc-cover-kicker {
  font-family: var(--font-sans);
  font-size: 0.64rem;
  font-weight: 700;
  letter-spacing: 0.10em;
  white-space: nowrap;
  text-transform: uppercase;
  color: var(--mc-gold-bright);
  border-bottom: 1px solid rgba(212, 175, 55, 0.4);
  padding-bottom: 0.85rem;
  margin-bottom: 2rem;
}
.mc-cover-center {
  margin: auto 0;
  padding: 1.5rem 0;
}
.mc-cover-title {
  font-family: var(--font-display);
  font-size: clamp(2rem, 3.8vw, 3rem);
  font-weight: 700;
  line-height: 1.18;
  letter-spacing: 0.02em;
  color: #ffffff;
  margin: 0 0 1.15rem;
}
.mc-cover-subtitle {
  font-family: var(--font-serif);
  font-style: italic;
  font-size: 1.18rem;
  line-height: 1.62;
  color: #e2e8f0;
  margin: 0 0 1.8rem;
  max-width: 92%;
}
.mc-cover-rule {
  width: 90px;
  height: 3px;
  background: var(--mc-gold-bright);
  border: 0;
  margin: 1.5rem 0;
}
.mc-cover-meta {
  border-top: 1px solid rgba(212, 175, 55, 0.35);
  padding-top: 1.2rem;
  font-family: var(--font-sans);
  font-size: 0.84rem;
  line-height: 1.65;
  color: #cbd5e1;
}
.mc-cover-meta strong {
  color: var(--mc-gold-soft);
  font-weight: 600;
}

/* Page 2: Table of Contents & Executive Stat Strip */
.mc-toc {
  padding: 2rem 0 2.5rem;
  margin-bottom: 3rem;
  border-bottom: 2px solid var(--mc-rule);
  page-break-after: always;
}
.mc-toc-kicker {
  font-family: var(--font-display);
  font-size: 1.5rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  color: var(--mc-navy);
  text-align: center;
  margin: 0 0 0.25rem;
}
.mc-toc-sub {
  font-family: var(--font-serif);
  font-style: italic;
  font-size: 0.98rem;
  color: var(--mc-ink-muted);
  text-align: center;
  margin: 0 0 1.75rem;
}
.mc-toc-list {
  list-style: none;
  padding: 0;
  margin: 0 0 2rem;
  border-top: 1px solid var(--mc-rule);
}
.mc-toc-list li {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.62rem 0.25rem;
  border-bottom: 1px dotted var(--mc-rule);
  font-family: var(--font-serif);
  font-size: 1.02rem;
}
.mc-toc-list a {
  color: var(--mc-navy);
  text-decoration: none;
  font-weight: 600;
}
.mc-toc-list a:hover {
  color: var(--mc-blue);
  text-decoration: underline;
}
.mc-toc-roman {
  font-family: var(--font-display);
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: var(--mc-gold);
  white-space: nowrap;
}

/* 5-Card Executive Stat Strip */
.mc-stat-strip {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(135px, 1fr));
  gap: 0.65rem;
  margin: 1.5rem 0;
  font-family: var(--font-sans);
}
.mc-stat-card {
  background: var(--mc-paper-alt);
  border: 1px solid var(--mc-rule);
  border-top: 3px solid var(--mc-navy);
  padding: 0.65rem 0.75rem;
  text-align: center;
}
.mc-stat-label {
  display: block;
  font-size: 0.68rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--mc-ink-muted);
}
.mc-stat-val {
  display: block;
  font-family: var(--font-mono);
  font-size: 0.96rem;
  font-weight: 700;
  color: var(--mc-navy);
  margin-top: 0.2rem;
}

/* Primer / Preface Box */
.primer {
  background: var(--mc-gold-tint);
  border: 1px solid var(--mc-gold-soft);
  border-left: 4px solid var(--mc-gold);
  padding: 1.15rem 1.4rem;
  margin: 1.5rem 0 2.5rem;
}
.primer h2 {
  font-family: var(--font-sans);
  font-size: 0.78rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: var(--mc-gold);
  margin: 0 0 0.45rem;
  border: 0;
}
.primer p {
  margin: 0;
  font-size: 1.02rem;
  line-height: 1.68;
}

/* Chapter Architecture */
.mc-chapter {
  padding-top: 2.2rem;
  margin-bottom: 3.4rem;
  border-top: 2px solid var(--mc-navy);
  page-break-before: always;
}
.mc-chapter-kicker {
  font-family: var(--font-display);
  font-size: 0.84rem;
  font-weight: 700;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--mc-gold);
  text-align: center;
  margin: 0 0 0.4rem;
}
.mc-chapter h2 {
  font-family: var(--font-display);
  font-size: clamp(1.55rem, 2.6vw, 2.05rem);
  font-weight: 700;
  line-height: 1.24;
  color: var(--mc-navy);
  text-align: center;
  margin: 0 0 1.2rem;
  border: 0;
}
.mc-epigraph {
  margin: 0 auto 1.85rem;
  max-width: 92%;
  padding: 0.85rem 1.35rem;
  background: var(--mc-paper-alt);
  border-left: 3px solid var(--mc-gold);
  border-right: 3px solid var(--mc-gold);
  font-family: var(--font-serif);
  font-style: italic;
  font-size: 1.03rem;
  line-height: 1.6;
  color: var(--mc-navy-mid);
  text-align: center;
}
.mc-epigraph footer {
  margin-top: 0.4rem;
  font-family: var(--font-sans);
  font-style: normal;
  font-size: 0.76rem;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--mc-ink-muted);
}

.mc-chapter h3 {
  font-family: var(--font-serif);
  font-size: 1.28rem;
  font-weight: 600;
  color: var(--mc-navy);
  margin: 2rem 0 0.65rem;
  padding-bottom: 0.25rem;
  border-bottom: 1px solid var(--mc-rule);
}

.mc-chapter p {
  font-family: var(--font-serif);
  font-size: 1.12rem;
  line-height: 1.8;
  margin: 0.8rem 0 1.1rem;
  text-align: justify;
  color: var(--mc-ink);
}

/* Drop-Cap on the opening paragraph of every chapter */
.mc-chapter p.drop-cap::first-letter {
  float: left;
  font-family: var(--font-display);
  font-size: 3.35rem;
  line-height: 0.84;
  padding-top: 0.06rem;
  padding-right: 0.55rem;
  padding-bottom: 0.05rem;
  color: var(--mc-navy);
  font-weight: 700;
}

.mc-chapter p.is-speaking {
  background: var(--mc-gold-tint);
  border-left: 4px solid var(--mc-gold);
  padding-left: 0.75rem;
}

/* Masterclass Callout Boxes (Narrator's Reflection, Global Parallel, Mental Model, Execution) */
.mc-box {
  margin: 1.55rem 0;
  padding: 1.1rem 1.35rem;
  border-radius: 2px;
  page-break-inside: avoid;
}
.mc-box-reflection {
  background: var(--mc-gold-tint);
  border: 1px solid var(--mc-gold-soft);
  border-left: 5px solid var(--mc-gold);
}
.mc-box-parallel {
  background: var(--mc-blue-tint);
  border: 1px solid #cde0ed;
  border-left: 5px solid var(--mc-blue);
}
.mc-box-model {
  background: var(--mc-paper-alt);
  border: 1px solid var(--mc-rule);
  border-left: 5px solid var(--mc-navy);
}
.mc-box-exec {
  background: var(--mc-green-tint);
  border: 1px solid #b7dfc2;
  border-left: 5px solid var(--mc-green-ink);
}
.mc-box-header {
  font-family: var(--font-sans);
  font-size: 0.76rem;
  font-weight: 700;
  letter-spacing: 0.09em;
  text-transform: uppercase;
  color: var(--mc-navy);
  margin-bottom: 0.45rem;
}
.mc-box-reflection .mc-box-header { color: #8c6d1f; }
.mc-box-parallel .mc-box-header { color: var(--mc-blue); }
.mc-box-exec .mc-box-header { color: var(--mc-green-ink); }
.mc-box p.mc-box-quote {
  font-family: var(--font-serif);
  font-style: italic;
  font-size: 1.05rem;
  line-height: 1.65;
  color: var(--mc-navy);
  margin: 0.35rem 0 0.5rem;
  text-align: left;
}
.mc-box p.mc-box-body {
  font-family: var(--font-serif);
  font-size: 1.01rem;
  line-height: 1.68;
  color: var(--mc-ink);
  margin: 0.35rem 0 0;
  text-align: left;
}
.mc-box ul.mc-box-list {
  margin: 0.45rem 0 0;
  padding-left: 1.25rem;
  font-family: var(--font-serif);
  font-size: 0.99rem;
  line-height: 1.62;
}
.mc-box ul.mc-box-list li {
  margin: 0.25rem 0;
}

/* Endnotes & Colophon */
.mc-notes {
  padding-top: 2rem;
  border-top: 2px solid var(--mc-navy);
  page-break-before: always;
}
.mc-notes h2 {
  font-family: var(--font-display);
  font-size: 1.35rem;
  color: var(--mc-navy);
}
.mc-notes ol {
  font-family: var(--font-sans);
  font-size: 0.82rem;
  line-height: 1.55;
  color: var(--mc-ink-muted);
  padding-left: 1.4rem;
}
.mc-notes li { margin: 0.35rem 0; }
.mc-notes a { color: var(--mc-blue); text-decoration: none; }
.mc-colophon {
  margin-top: 3rem;
  padding-top: 1.2rem;
  border-top: 1px solid var(--mc-rule);
  text-align: center;
  font-family: var(--font-serif);
  font-style: italic;
  font-size: 0.92rem;
  color: var(--mc-ink-muted);
}

@media (max-width: 720px) {
  .mc-book-shell { padding: 1.25rem 1.1rem 3.5rem; }
  .mc-cover { padding: 2rem 1.35rem; min-height: auto; }
  .mc-chapter p { font-size: 1.04rem; text-align: left; }
}

@page {
  size: A4;
  margin: 22mm 20mm 22mm 20mm;
  @bottom-center {
    content: "— " counter(page) " —";
    font-family: 'Newsreader', Georgia, serif;
    font-size: 9pt;
    color: #556677;
  }
}
@page :first {
  margin: 0;
  @bottom-center { content: none; }
}

@media print {
  html, body { background: var(--mc-paper); font-size: 11pt; }
  .mc-topbar { display: none !important; }
  .mc-book-shell { max-width: none; padding: 0; box-shadow: none; }
  .mc-cover { min-height: 250mm; margin: 0; border-width: 3px; }
}
"""


def _interleave_paragraphs_and_callouts(
    paragraphs: List[str],
    callouts: List[Dict[str, Any]],
    is_first_block: bool = False,
) -> List[str]:
    """Interleave narrative paragraphs with Masterclass callouts (Narrator's Reflection, Global Parallel, Mental Model)."""
    out: List[str] = []
    by_after: Dict[int, List[Dict[str, Any]]] = {}
    tail_callouts: List[Dict[str, Any]] = []
    for c in callouts or []:
        pos = c.get("after_paragraph")
        if isinstance(pos, int) and 1 <= pos <= len(paragraphs):
            by_after.setdefault(pos, []).append(c)
        else:
            tail_callouts.append(c)

    for i, raw_p in enumerate(paragraphs, 1):
        clean_p = _clean_audio_text(raw_p)
        if not clean_p:
            continue
        cls = ' class="drop-cap"' if (is_first_block and i == 1) else ""
        out.append(f"<p{cls}>{html.escape(clean_p)}</p>")
        for c in by_after.get(i, []):
            out.append(_render_book_callout_xhtml(c))

    for c in tail_callouts:
        out.append(_render_book_callout_xhtml(c))
    return out


def render_masterclass_book_html(
    spec: Dict[str, Any],
    chapters: List[Dict[str, Any]],
    key_figures: List[tuple[str, str]],
    web_words: int,
    book_words: int,
    audio_minutes: int,
) -> str:
    """Render the narrative monograph HTML and print source for the companion PDF (`SYMBOL_book.pdf`)."""
    sym = spec["symbol"].upper()
    market = spec["market"].upper()
    as_of = spec.get("as_of", dt.date.today().isoformat())
    generated = dt.datetime.now(ZoneInfo("America/Los_Angeles"))
    book_title = spec.get("book_masterclass_title") or spec.get("book_title") or f"{spec['title']} — Masterclass Companion Book"
    book_subtitle = spec.get("book_subtitle") or (
        f"A step-by-step narrative walkthrough and audio companion to {spec['title']}: "
        "deconstructing the business engine, global historical parallels, ten-year financial forensics, "
        "both sides of the institutional debate, and the discipline of high-asymmetry execution."
    )

    # Extract 5 headline stats for the TOC Executive Stat Strip
    kf_map = {k: _clean_audio_text(v) for k, v in key_figures}
    monitor_only = (
        str(spec.get("new_capital_verdict", spec.get("verdict", ""))).upper() in {"WAIT_FOR_SUPPORT", "REJECTED"}
        or str(spec.get("entry_posture", "")).startswith(("WAIT_FOR_SUPPORT", "NO_NEW_ALLOCATION", "AVOID", "STAY_AWAY"))
    )
    stat_cards = [
        ("SESSION PRICE", next((v for k, v in kf_map.items() if "Session Price" in k), str(spec.get("cmp", "")))),
        ("NEW CAPITAL VERDICT", _clean_audio_text(spec.get("new_capital_verdict", spec.get("verdict", "")))),
        ("CURRENT HOLDING ACTION", kf_map.get("Current Holding Action", "NOT HELD")),
        ("STAGE POSTURE", _clean_audio_text(spec.get("weinstein_stage") or (spec.get("stage2") or {}).get("stage", ""))),
        (
            "VALUATION WATCH ZONE (CONDITIONAL)" if monitor_only else "BUY / SUPPORT ZONE",
            f"{'₹' if market == 'IN' else '$'}{spec['entry_zone_low']:,.2f}–{spec['entry_zone_high']:,.2f}",
        ),
        (
            f"{str(spec['scenario_horizon']).upper()} SCENARIO RANGE" if spec.get("scenario_horizon") else "PRICE TARGET",
            "Not assigned; valuation bridge is not decision-grade"
            if spec.get("target_base") is None
            else (
                f"Bear {'₹' if market == 'IN' else '$'}{spec['target_bear']:,.2f} / Base {'₹' if market == 'IN' else '$'}{spec['target_base']:,.2f} / Bull {'₹' if market == 'IN' else '$'}{spec['target_bull']:,.2f}"
                if spec.get("scenario_horizon")
                else f"{'₹' if market == 'IN' else '$'}{spec['target_base']:,.2f} / {'₹' if market == 'IN' else '$'}{spec['target_bull']:,.2f}"
            ),
        ),
    ]
    stat_strip_html = (
        '<div class="mc-stat-strip">\n'
        + "\n".join(
            f'<div class="mc-stat-card"><span class="mc-stat-label">{html.escape(k)}</span>'
            f'<span class="mc-stat-val">{html.escape(v)}</span></div>'
            for k, v in stat_cards
        )
        + "\n</div>"
    )

    toc_items = []
    chapter_sections = []

    for idx, ch in enumerate(chapters):
        cid = ch.get("id") or f"ch-{idx}"
        roman = ROMAN[idx] if idx < len(ROMAN) else f"CHAPTER {idx}"
        clean_title = _strip_chapter_prefix(ch.get("book_title") or ch.get("web_title") or f"Chapter {idx}")
        toc_items.append(
            f'<li><a href="#{html.escape(cid)}">{html.escape(clean_title)}</a>'
            f'<span class="mc-toc-roman">{html.escape(roman)}</span></li>'
        )

        epigraph = ch.get("epigraph") or {}
        epi_quote = _clean_audio_text(epigraph.get("quote") or ch.get("question") or "")
        epi_author = _clean_audio_text(epigraph.get("author") or "Institutional Research Desk Maxim")
        epi_html = (
            f'<blockquote class="mc-epigraph">"{html.escape(epi_quote)}"'
            f"<footer>&mdash; {html.escape(epi_author)}</footer></blockquote>"
            if epi_quote
            else ""
        )

        body_blocks = _interleave_paragraphs_and_callouts(
            ch.get("book_paragraphs", []),
            ch.get("book_callouts", []),
            is_first_block=True,
        )
        for sub in ch.get("book_subsections", []):
            if sub.get("title"):
                body_blocks.append(f"<h3>{html.escape(_clean_audio_text(sub['title']))}</h3>")
            body_blocks.extend(
                _interleave_paragraphs_and_callouts(
                    sub.get("paragraphs", []),
                    sub.get("callouts", []),
                    is_first_block=False,
                )
            )

        chapter_sections.append(
            f'<section class="chapter book-chapter mc-chapter" id="{html.escape(cid)}" data-audio-chapter="{idx}">\n'
            f'  <div class="mc-chapter-kicker">{html.escape(roman)}</div>\n'
            f"  <h2>{html.escape(clean_title)}</h2>\n"
            f"  {epi_html}\n"
            f"  {chr(10).join(body_blocks)}\n"
            "</section>"
        )

    cites_li = "\n".join(
        f'<li id="cite_note-{i}">{c}</li>'
        for i, c in enumerate(spec.get("citations", []), 1)
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="report-design" content="masterclass-book-v1">
  <meta name="report-market" content="{html.escape(market)}">
  <meta name="report-kind" content="book">
  <meta name="research-as-of" content="{html.escape(as_of)}">
  <meta name="generated-at" content="{html.escape(generated.isoformat())}">
  <title>{html.escape(book_title)}</title>
  <style>
{MASTERCLASS_BOOK_CSS}
  </style>
</head>
<body id="top">
  <header class="mc-topbar" role="navigation" aria-label="Masterclass Companion Book &amp; Audiobook Controls">
    <div class="mc-topbar-inner">
      <div class="mc-edition-links">
        <a href="../../index.html">&larr; Portfolio Desk</a>
        <a href="{sym}_dossier.html">Web Research Dossier ({web_words:,}w)</a>
        <a class="is-active" href="{sym}_book.pdf" download="{sym}_book.pdf">Download PDF ({book_words:,}w)</a>
      </div>
      <div class="mc-audio-controls book-audio-bar">
        <button type="button" class="mc-audio-btn" data-audio-action="play">Play Audiobook</button>
        <button type="button" class="mc-audio-btn secondary" data-audio-action="prev">&larr; Prev</button>
        <button type="button" class="mc-audio-btn secondary" data-audio-action="next">Next &rarr;</button>
        <button type="button" class="mc-audio-btn secondary" data-audio-action="stop">Stop</button>
        <select class="mc-audio-select" data-audio-rate aria-label="Playback speed">
          <option value="1.0" selected>1.0x</option>
          <option value="1.15">1.15x</option>
          <option value="1.25">1.25x</option>
          <option value="1.5">1.5x</option>
        </select>
        <span class="mc-audio-status" data-audio-status>Ready to narrate</span>
      </div>
    </div>
  </header>

  <main class="mc-book-shell report">
    <section class="mc-cover" aria-label="Book Cover">
      <div class="mc-cover-kicker">INSTITUTIONAL RESEARCH DESK &nbsp;&bull;&nbsp; MASTERCLASS MONOGRAPH</div>
      <div class="mc-cover-center">
        <h1 class="mc-cover-title">{html.escape(book_title)}</h1>
        <hr class="mc-cover-rule">
        <p class="mc-cover-subtitle">{html.escape(_clean_audio_text(book_subtitle))}</p>
      </div>
      <div class="mc-cover-meta">
        <div><strong>Company &amp; Market:</strong> {html.escape(spec['title'])} ({html.escape(market)})</div>
        <div><strong>Research Session Cutoff:</strong> {html.escape(as_of)} &bull; <strong>Generated:</strong> <time datetime="{html.escape(generated.isoformat())}">{html.escape(generated.strftime('%d %b %Y, %I:%M %p %Z'))}</time></div>
        <div><strong>Core Verdict:</strong> {html.escape(_clean_audio_text(spec.get('verdict', '')))} ({html.escape(_clean_audio_text(spec.get('entry_posture', '')))})</div>
        <div><strong>Authored &amp; Narrated by:</strong> Senior Institutional Equity Research Desk &bull; Masterclass Companion Audio-Reader Edition ({book_words:,} words &bull; ~{audio_minutes} min listen)</div>
      </div>
    </section>

    <nav class="mc-toc" aria-label="Table of Contents">
      <h2 class="mc-toc-kicker">CONTENTS</h2>
      <p class="mc-toc-sub">A Sequential Guide to the Business Engine, Global Parallels, Financial Forensics &amp; High-Asymmetry Execution</p>
      <ol class="mc-toc-list">
        {chr(10).join("        " + item for item in toc_items)}
      </ol>
      {stat_strip_html}
      <section class="primer" id="primer">
        <h2>Preface &amp; Core Thesis</h2>
        <p>{html.escape(_clean_audio_text(spec['primer']))}</p>
      </section>
    </nav>

    {chr(10).join(chapter_sections)}

    <section class="mc-notes" id="notes">
      <h2 id="references">Notes, Filings &amp; Primary Sources</h2>
      <ol class="sources reflist">
        {cites_li}
      </ol>
      <div class="mc-colophon">
        &bull; &bull; &bull;<br>
        This Masterclass Companion Book was authored for private study, audiobook narration, and disciplined portfolio execution.<br>
        Verified against the {html.escape(market)} Research Ledger &bull; Session Cutoff {html.escape(as_of)}
      </div>
    </section>
  </main>

  <script>
  (() => {{
    'use strict';
    const bar = document.querySelector('.book-audio-bar');
    if (!bar || !('speechSynthesis' in window)) return;
    const playBtn = bar.querySelector('[data-audio-action="play"]');
    const prevBtn = bar.querySelector('[data-audio-action="prev"]');
    const nextBtn = bar.querySelector('[data-audio-action="next"]');
    const stopBtn = bar.querySelector('[data-audio-action="stop"]');
    const rateSel = bar.querySelector('[data-audio-rate]');
    const statusEl = bar.querySelector('[data-audio-status]');
    const nodes = [...document.querySelectorAll('.mc-chapter p, .mc-chapter blockquote')];
    let idx = 0;
    let playing = false;
    const clear = () => nodes.forEach(n => n.classList.remove('is-speaking'));
    const speak = () => {{
      if (!playing || idx < 0 || idx >= nodes.length) {{
        playing = false;
        clear();
        if (playBtn) playBtn.textContent = 'Play Audiobook';
        if (statusEl) statusEl.textContent = 'Ready to narrate';
        return;
      }}
      speechSynthesis.cancel();
      clear();
      const node = nodes[idx];
      node.classList.add('is-speaking');
      node.scrollIntoView({{block: 'center', behavior: 'smooth'}});
      const ch = node.closest('.mc-chapter')?.querySelector('h2')?.textContent.trim() || 'Book';
      if (statusEl) statusEl.textContent = ` (${{idx + 1}}/${{nodes.length}}) • ${{ch.slice(0, 36)}}`;
      const u = new SpeechSynthesisUtterance(node.textContent.trim());
      u.rate = parseFloat(rateSel?.value || '1.0') || 1.0;
      u.onend = () => {{ if (playing) {{ idx += 1; speak(); }} }};
      speechSynthesis.speak(u);
    }};
    playBtn?.addEventListener('click', () => {{
      if (playing) {{
        playing = false;
        speechSynthesis.cancel();
        playBtn.textContent = 'Resume';
        if (statusEl) statusEl.textContent = `Paused (${{idx + 1}}/${{nodes.length}})`;
      }} else {{
        playing = true;
        playBtn.textContent = 'Pause';
        speak();
      }}
    }});
    prevBtn?.addEventListener('click', () => {{ idx = Math.max(0, idx - 1); if (playing) speak(); }});
    nextBtn?.addEventListener('click', () => {{ idx = Math.min(nodes.length - 1, idx + 1); if (playing) speak(); }});
    stopBtn?.addEventListener('click', () => {{
      playing = false;
      idx = 0;
      speechSynthesis.cancel();
      clear();
      if (playBtn) playBtn.textContent = 'Play Audiobook';
      if (statusEl) statusEl.textContent = 'Ready to narrate';
    }});
    rateSel?.addEventListener('change', () => {{ if (playing) speak(); }});
  }})();
  </script>
</body>
</html>
"""


def build_pdf_book(book_html_path: str | Path, out_pdf_path: str | Path) -> Path | None:
    """Compile the companion PDF book using WeasyPrint when available."""
    weasy = shutil.which("weasyprint") or (
        "/opt/homebrew/bin/weasyprint" if Path("/opt/homebrew/bin/weasyprint").exists() else None
    )
    out_p = Path(out_pdf_path)
    if not weasy:
        return None
    out_p.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([weasy, str(book_html_path), str(out_p)], check=True, capture_output=True, text=True)
    return out_p
