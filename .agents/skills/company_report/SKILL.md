---
name: company_report
description: >-
  Institutional company research dossier for one listed company (IN or US),
  written as a readable book: fixed chapters that answer the reader's
  questions, every estimate showing its working, the 3-layer underwriting
  analysis behind the decision, and a verdict badge rendered with the report
  palette. Market-specific blocks are marked; exchange, currency, filings and
  data sources differ by market.
---

> **Design (binding):** read `../_shared/REPORT_DESIGN.md`. Write the complete research body, then assemble with `scripts/assemble_report.py --market <MARKET> --kind dossier --workflow "Company research" --as-of <verified-session-date>`. Older Wikipedia heads and styles are obsolete; never copy a prior dossier shell. The renderer owns the homepage-matched design, Pacific generation header and interactions. Retain every research chapter, table, calculation, citation and end reference. All existing quality gates remain mandatory, and newly completed publication rejects missing Research Desk layout.

> **Market blocks (binding):** this skill covers both markets. Read `.agents/config/markets.json` for the market in this run (`IN` or `US`). Follow the text that is not inside a market block, and inside a market block follow only the block whose label matches the run's market. Ignore the other block. Figures, currency, exchange names and data sources differ by market; never mix them.

> **Reviewer-cycle limit (binding):** use the shared reviewer process in `../_shared/REVIEWER_OPERATIONS.md` and `.agents/config/reviewer.json`. Four complete rounds is a strict maximum. After round 4, fix remaining findings best-effort, rerun the validators, record and disclose unresolved items, and do not launch a fifth round.

> **Publication (binding):** after the validators and reviewer gate, automatically publish this report to this repository's GitHub Pages, regenerate its indexes, and commit and push the scoped publication. Public publication is pre-authorized; do not ask for approval. Follow `../_shared/RUN_PROTOCOL.md` §6 and never force-push or stage unrelated changes.

> **Voice (binding):** read `../_shared/REPORT_VOICE.md` before writing. Plain English with reasoning and consequences; no banned filler phrases; each verdict names its rule and the level that would change it. Colours come only from `../_shared/REPORT_PALETTE.md`: use the `verdict-*` classes and no emoji status markers.

> **Book standard (binding):** read `../_shared/BOOK_STANDARD.md` before writing. The report is a short book for a capable adult with no finance training: fixed chapters (section 1), every estimate shows its working (section 2), technical terms are defined at first use per `../_shared/GLOSSARY.md` and `.agents/config/glossary.json`, and the code checks in section 5 must pass.

> **Research contract (binding):** every quantitative claim traces to a research record per `../_shared/RESEARCH_CONTRACT.md`. Fetch every cited page into the execution cache with `scripts/fetch_cache.py` before writing; the citation gate proves values against what was actually fetched.

> **Market-data date (binding):** date all market prices and technical analysis to the latest completed exchange session with a verified final benchmark close, following `../_shared/RUN_PROTOCOL.md` §0. Do not treat the run's calendar date as the report date. Label the report's as-of session clearly and use that same session for every price, technical metric, title, and dated output; disclose data delay where applicable.

<!-- MARKET IN -->
Write as an **institutional equity research analyst** and **underwriter**, in a plain, objective, neutral voice. The reader is a capable adult with no finance training: explain every idea until the reader can use it.
<!-- /MARKET -->
<!-- MARKET US -->
Write as an **institutional equity research analyst** and **underwriter**, in a plain, objective, neutral voice, covering US equity markets (NYSE / NASDAQ). The reader is a capable adult with no finance training: explain every idea until the reader can use it.
<!-- /MARKET -->

Compile the full book and underwriting analysis on:
- **Company Name:** `{{COMPANY_NAME}}`
<!-- MARKET IN -->
- **Ticker & Primary Exchange:** `{{TICKER_AND_EXCHANGE}}` (e.g., `NSE: ORIANA`, `BSE: 544224`)
- **Industry / Sector:** `{{INDUSTRY_SECTOR}}`
- **Strategy Bucket:** `{{STRATEGY_BUCKET}}` (`CORE_ALPHA` or `TACTICAL_MOMENTUM`)
<!-- /MARKET -->
<!-- MARKET US -->
- **Ticker & Primary Exchange:** `{{TICKER_AND_EXCHANGE}}` (e.g., `NASDAQ: NVDA`, `NYSE: ORCL`)
- **Industry / Sector:** `{{INDUSTRY_SECTOR}}`
- **Strategy Bucket:** `{{STRATEGY_BUCKET}}` (`CORE_ALPHA`, `TACTICAL_MOMENTUM`, or `LEVERAGED_SATELLITE`)
<!-- /MARKET -->
- **Position Status:** `{{POSITION_STATUS}}` (`CURRENT_HOLDING` or `PIPELINE_CHALLENGER`)
- **Specific Focus Areas / Underwriting Questions (Optional):** `{{OPTIONAL_SPECIFIC_FOCUS}}`

<!-- MARKET IN -->
Currency: Indian rupees. Exchange figures in ₹ crore or ₹ lakh as filed. Primary sources: BSE/NSE exchange disclosures, audited annual reports (page/note numbers), quarterly investor presentations, concall transcripts (speaker citations), CRISIL/ICRA/CARE releases, statutory regulatory orders.
<!-- /MARKET -->
<!-- MARKET US -->
Currency: US dollars. Exchange figures in $ millions or $ billions. Primary sources: SEC EDGAR filings (10-K, 10-Q, 8-K, DEF 14A), audited annual financial statements (page/note numbers), investor day presentations, concall transcripts (executive citations), Moody's/S&P/Fitch releases, regulatory orders.
<!-- /MARKET -->

Your deliverable is a standalone, self-contained HTML document saved directly in:
`docs/blogs/<SYMBOL>_dossier.html` (e.g. `docs/blogs/AFCOM_dossier.html`, `docs/blogs/ADBE_dossier.html`).

---

## 1. The book structure (binding)

The report reads as chapters, fixed in order, each answering one question the
reader would ask. Full standard, per-chapter rules and the readability checks:
`../_shared/BOOK_STANDARD.md` (section 1). The skeleton in section 6 shows the
exact HTML.

| order | id | chapter | question answered |
|---|---|---|---|
| 0 | `primer` | Before you read | what is the company, the conclusion, and what would make it wrong (3–5 sentences) |
| 1 | `ch-1` | What the company does | who pays, for what, how it makes money; ends with the report's glossary |
| 2 | `ch-2` | Why the business is strong or weak | competitive position with reasons and cited evidence |
| 3 | `ch-3` | The numbers, in plain words | five years of revenue, profit, cash, debt; every table followed by what it means and what it does not show |
| 4 | `ch-4` | What the price is doing | the momentum test result in plain words, and what would confirm or reject the idea |
| 5 | `ch-5` | What could happen next | bull / base / bear: story, driver, number, probability and its reason, then the expected outcome |
| 6 | `ch-6` | Why these estimates might be wrong | each estimate's weakest assumption, the evidence that would show it wrong, and when we know |
| 7 | `ch-7` | What we would do, and when | the decision, the trigger that changes it, entry zone, stop, targets, each with the reason |
| 8 | `notes` | Notes and sources | numbered, with page/section for each filing |

Leveraged/ETF names are not analysed as companies: the book covers the index,
the trend, and the decay risk, and says so in the primer.

## 2. Every estimate shows its working (binding)

Each estimate appears as a `<section class="estimate">` with exactly these five
labelled parts, in this order (`../_shared/BOOK_STANDARD.md` section 2):

1. `<h4>The number</h4>` — the number, in plain words.
2. `<h4>How it was calculated</h4>` — one or two sentences.
3. `<h4>The inputs</h4>` — each input cited to a research record.
4. `<h4>The range</h4>` — the bull and bear values, and why.
5. `<h4>If the number is off</h4>` — what changes for the reader.

Pattern (not real data): "We estimate next year's profit per share at $X. We
got this by taking this year's profit (cited), adding the growth the company
guided to (cited), and assuming the margin stays where it was last year
(cited). If margins fall by two points, profit would be about $Y, and the case
for buying would weaken."

## 3. The 3-Layer Underwriting Framework (the engine behind chapters 2, 5 and 7)

The book is the presentation; the underwriting is the engine. Every report
evaluates all three layers and states the outcome; Chapter 2 carries the
Layer 2 reasoning, Chapter 5 the Layer 1 gate results, Chapter 7 the Layer 3
posture. Thresholds that live in `.agents/config/scoring.json` (asymmetry
floors, tier sizing, support ladder, momentum gate) are cited from the config,
not restated.

<!-- MARKET IN -->
```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ LAYER 1: BINARY HARD GATING FLOORS (Pass / Fail)                            │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. Financial Health Floor:                                                  │
│    - ROCE ≥ 15.0% (Core prefers > 18.0%)                                    │
│    - Debt-to-Equity < 0.70 (Excluding financial institutions/NBFCs)         │
│    - 3-Year Cumulative CFO / PAT ≥ 0.70 (Audited cash flow conversion)      │
│ 2. Technical Posture Floor:                                                 │
│    - Tactical: Weinstein Stage 2 Markup above rising 50-DMA and 200-DMA     │
│    - Core: Stage 1 Base Breakout or Stage 2 Markup                          │
│    - No Stage 4 Breakdown / No Death Cross on heavy distribution volume     │
│ 3. Asymmetry Floor (per scoring.json asymmetry_floor):                      │
│    - Tactical ≥ 3.5:1, Core ≥ 3.0:1                                         │
│    - Formula: (Target - Entry) / (Entry - Stop)                             │
│    - Target Anchoring: Forward EPS × 3Y Median P/E OR Base Measured-Move.   │
│      Unanchored targets = REJECT                                            │
│ DISPOSITION: If ANY gate fails → FAIL_[REASON] → REJECTED (no shortlist buy)│
└─────────────────────────────────────────────────────────────────────────────┘
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ LAYER 2: 3–5 COMPANY & SECTOR-SPECIFIC OPERATIONAL KPIs                     │
├─────────────────────────────────────────────────────────────────────────────┤
│ Pick the 3–5 metrics from BOOK_STANDARD.md section 3 that govern this exact │
│ business model, and say why each was picked. Score each KPI:                │
│ PASS | WATCH | FAIL (minimum 3/4 or 4/5 required)                           │
└─────────────────────────────────────────────────────────────────────────────┘
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ LAYER 3: SUPPORT-AWARE ENTRY POSTURE (per scoring.json)                     │
├─────────────────────────────────────────────────────────────────────────────┤
│ Distance from nearest verified support anchor in ATR(14), mapped to the     │
│ single support_distance_ladder in scoring.json:                             │
│ • FULL_SIZE band                    → IMMEDIATE BUY / ACCUMULATE            │
│ • STANDARD band                     → ACCUMULATE ON DIP                     │
│ • NO_BUY band, or RSI > 70          → WAIT FOR SUPPORT (do not chase)       │
│ • SUPPORT_BROKEN                    → REJECTED / BROKEN STRUCTURE           │
└─────────────────────────────────────────────────────────────────────────────┘
```
<!-- /MARKET -->
<!-- MARKET US -->
```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ LAYER 1: BINARY HARD GATING FLOORS (Pass / Fail)                            │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. Financial Health Floor:                                                  │
│    - ROIC ≥ 12.0% (Core prefers > 16.0%)                                    │
│    - Free Cash Flow (FCF) Margin ≥ 12.0%                                    │
│    - Net Debt-to-EBITDA < 3.0x (Excluding financial institutions/banks)     │
│    - Stock-Based Compensation (SBC) Dilution < 5.0% of Annual Revenue       │
│ 2. Technical Posture Floor:                                                 │
│    - Tactical: Weinstein Stage 2 Markup above rising 50-DMA and 200-DMA     │
│    - Core: Stage 1 Base Breakout or Stage 2 Markup                          │
│    - No Stage 4 Breakdown / No Death Cross on heavy distribution volume     │
│ 3. Asymmetry Floor (per scoring.json asymmetry_floor):                      │
│    - Tactical ≥ 3.5:1, Core ≥ 3.0:1                                         │
│    - Formula: (Target - Entry) / (Entry - Stop)                             │
│    - Mandatory Target Anchoring: Forward EPS × 3Y Median P/E, DCF, or Base  │
│      Measured-Move. Unverified → FAIL_ASYMMETRY.                            │
│ DISPOSITION: If ANY gate fails → FAIL_[REASON] → REJECTED (no shortlist buy)│
└─────────────────────────────────────────────────────────────────────────────┘
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ LAYER 2: SECTOR-SPECIFIC OPERATIONAL KPIs (3–5 Decision-Driving Metrics)    │
├─────────────────────────────────────────────────────────────────────────────┤
│ Pick from BOOK_STANDARD.md section 3:                                       │
│ - Cloud / Software / AI: ARR Growth, NRR %, RPO Backlog, Rule of 40, SBC    │
│ - Semiconductors / Hardware: Gross Margin, Fab Utilization, Book-to-Bill    │
│ - Data Center Infrastructure: Power Under Contract, PUE, Capex Backlog      │
│ - Consumer Tech / Platforms: Take Rate, GMV Growth, Active Users            │
│ - Healthcare / Biotech / MedTech: Pipeline Phase III, Regulatory Clearance  │
│ - Industrials / Aerospace / Defense: Firm Backlog / TTM Sales, Book-to-Bill │
│ Score each KPI: PASS | WATCH | FAIL (minimum 3/4 or 4/5 required)           │
└─────────────────────────────────────────────────────────────────────────────┘
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ LAYER 3: SUPPORT-AWARE ENTRY POSTURE & SIZING (per scoring.json)            │
├─────────────────────────────────────────────────────────────────────────────┤
│ - Distance from Primary Support Anchor (20-DMA / 50-DMA / Base Pivot)       │
│ - Stance: per the `support_distance_ladder` in `scoring.json`               │
│   (FULL_SIZE / STANDARD / NO_BUY bands)                                     │
│ - Capital Sizing: Conviction Tiers per `position_sizing.tier_table` in      │
│   `scoring.json` (hard single-name cap per `position_sizing.hard_cap_pct`)  │
└─────────────────────────────────────────────────────────────────────────────┘
```
<!-- /MARKET -->

### Chapter 4 content: the momentum gate

Chapter 4 does not re-derive the chart story by hand. It reads the frozen-
snapshot output of `scripts/momentum_gate.py` for this symbol (Test A: in
momentum now; Test B: entering momentum; thresholds in `.agents/config/
scoring.json`, `momentum_gate`) and states it in plain words: which test
passed or failed, the measured values in language the reader understands, and
the consequence — what the chart would need to do to confirm or reject the
idea. A stock that fails both tests is not allocated, however good its
business; say so.

### Deterministic Action Verdict Taxonomy (rendered with the palette)

- **For `CURRENT_HOLDING` positions:**
  - `KEEP_COMPOUNDING`: all gates passed, operational KPIs healthy (≥3/4), Stage 2 uptrend intact. Maintain full position.
  - `ACCUMULATE_ON_DIP`: high-conviction compounder pulling back to verified support (inside the buyable bands of the `support_distance_ladder` in `scoring.json`), allocation headroom available.
  - `TRIM_PROFIT_BOOKING`: extended (in the `NO_BUY` band, or RSI > 75), hit bull target, or exceeds the hard single-name cap in `scoring.json` (`position_sizing.hard_cap_pct`). Trim 30%–50% to harvest gains.
  - `REPLACE_UNDERPERFORMER`: broken structural support (closed below stop / Stage 4), or failed ≥2 operational KPIs, or fundamental thesis impairment. Candidate for capital swap into a top shortlist challenger (use the displacement workflow, advisory only).
- **For `PIPELINE_CHALLENGER` candidates:**
  - `IMMEDIATE_BUY`: passed all gates + KPIs, strictly in the `FULL_SIZE` band of the `support_distance_ladder`.
  - `ACCUMULATE_ON_DIP`: passed all gates + KPIs, in the `STANDARD` band.
  - `WAIT_FOR_SUPPORT`: passed gates + KPIs, but in the `NO_BUY` band (or RSI > 70). Do not chase.
  - `REJECTED`: failed a Layer 1 gate or Layer 2 KPIs.

Verdicts render as `<span class="verdict verdict-keep">KEEP_COMPOUNDING</span>`
style, class per `../_shared/REPORT_PALETTE.md` section 3.

## 4. Editing rules (binding)

1. **Neutral, non-promotional.** No hype, no sensational adjectives, no slang.
   Explain what audited filings, operating ratios and market facts mean for
   this reader, in full sentences (`../_shared/REPORT_VOICE.md`).
2. **Citation density: 25 to 40+ primary references.** Every major quantitative
   data point (revenue, margins, order book, debt, promoter stake, capacities,
   cash conversion) and every corporate claim carries an in-text superscript
   reference (`<sup><a href="#cite_note-1">[1]</a></sup>`) and a numbered entry
   in Notes and sources with the page or section.
3. **Zero-Placeholder Policy:** no placeholder dots, no empty table cells, no
   truncated bullets. If a figure is not published, the research record says
   so (`RESEARCH_CONTRACT.md` null rule) and the book says "not published",
   never an estimate in its place.
4. **Minimum narrative depth:** Chapters 1–3 each carry at least 3–4 dense
   paragraphs on operating mechanics, unit economics, customer concentration
   and historical cyclicality, adapted to the business.
5. **Multi-year tables:** Chapter 3 provides five-year tabular statements with
   exact numbers, and the peer comparison (3–5 direct peers) required for the
   Layer 2 judgment.
6. **Independent agent:** one company per run; never compress multiple
   companies into one agent turn.

### Mandatory two-step search & deep fetch (zero-snippet reliance)

- Never rely on search snippets alone; they omit the full financial tables.
<!-- MARKET IN -->
- Step 1: locate the canonical page via web search — Screener.in
  (`https://www.screener.in/company/<SYMBOL>/`), Trendlyne, or the exchange
  filing page. Step 2: fetch the full page with
  `python3 scripts/fetch_cache.py --url <page>` so the text is stored in the
  execution cache with its hash. Read the value from the cached text.
<!-- /MARKET -->
<!-- MARKET US -->
- Step 1: locate the canonical page via web search — the SEC EDGAR filing
  (10-K/10-Q/8-K/DEF 14A), the company IR page, or the concall transcript.
  Step 2: fetch the full page with
  `python3 scripts/fetch_cache.py --url <page>` so the text is stored in the
  execution cache with its hash. Read the value from the cached text.
<!-- /MARKET -->
- From the fetched pages: the 5-year P&L / balance sheet / cash flow, 3-year
  cash conversion, ROCE/ROIC, net debt, 50/200-day levels and 52-week range.
- Every fetched value becomes a research record (`RESEARCH_CONTRACT.md`) in
  `scripts/.cache/research_<MARKET>_<date>.json` before it is written into the
  book. The citation gate checks the record against the cached text, so a value
  read from memory — or from a page that changed after the fetch — fails the
  run.

## 5. Readability and validation gates (binding, in order)

The report is not finished until, in this order:

1. `python3 scripts/readability_check.py docs/blogs/<SYMBOL>_dossier.html`
   — BOOK_STANDARD section 5 in code: reading level, glossary first-use
   definitions, no bare tables, estimate working parts, Chapter 7 triggers,
   banned phrases, primer length, numbered notes.
2. `python3 scripts/citation_check.py docs/blogs/<SYMBOL>_dossier.html --research scripts/.cache/research_<MARKET>_<date>.json`
   — source floor (25 for dossiers), every found record's URL in the fetch
   cache, every value present in the cached text, as-of freshness (60 days).
3. `python3 scripts/validate_report.py docs/blogs/<SYMBOL>_dossier.html` — the
   shared structural and voice validator.
4. The reviewer cycle (`../_shared/REVIEWER_OPERATIONS.md`), including the
   red-team bear case for full reports.

Fix findings, rerun, and only then publish.

## 6. Required body structure

<!-- SKELETON NOTE: write only the body. Do not write a <head> or <style>;
`scripts/assemble_report.py` builds the head from REPORT_PALETTE.md,
report_base.css and book_components.css, wraps the body, and wraps every
wikitable in .table-wrap. Assemble before validation:
  python3 scripts/assemble_report.py --body <RUN_DIR>/work/body.html \
    --out docs/blogs/<SYMBOL>_dossier.html -->

The body is, in order:

```html
<h1>Company name (TICKER) — the book report, as of <as-of session></h1>
<!-- keep the key-figures strip: exchange, price, as-of session, bucket,
     verdict, asymmetry, stage, ATR distance from support -->
<dl class="key-figures"> ... </dl>

<section class="primer" id="primer">
  <h2>Before you read</h2>
  <p>…3–5 sentences: what the company is, what this report concludes, what
  would make the conclusion wrong…</p>
</section>

<section class="chapter" id="ch-1">
  <h2>What the company does</h2>
  <!-- plain-English business model; who pays, for what; ends with the
       glossary of this report's terms -->
</section>

<section class="chapter" id="ch-2">
  <h2>Why the business is strong or weak</h2>
  <!-- competitive position, Layer 2 KPIs with PASS/WATCH/FAIL scores,
       each claim cited -->
</section>

<section class="chapter" id="ch-3">
  <h2>The numbers, in plain words</h2>
  <!-- five-year revenue, profit, cash, debt; every table in
       <div class="table-wrap"><table class="wikitable">…</table></div>
       followed by what it means and what it does not show; peer matrix -->
</section>

<section class="chapter" id="ch-4">
  <h2>What the price is doing</h2>
  <!-- momentum_gate.py output in plain words; confirm/reject consequence -->
</section>

<section class="chapter" id="ch-5">
  <h2>What could happen next</h2>
  <!-- bull / base / bear: story, driver, number, probability + reason;
       expected outcome; each estimate as <section class="estimate"> with
       the five <h4> parts from section 2 -->
</section>

<section class="chapter" id="ch-6">
  <h2>Why these estimates might be wrong</h2>
  <!-- weakest assumption per estimate; the evidence that would show it
       wrong; when it will be known (next earnings date, filing, index) -->
</section>

<section class="chapter" id="ch-7">
  <h2>What we would do, and when</h2>
  <!-- the verdict (palette span), entry zone, stop, targets with reasons;
       every decision carries <p class="trigger">…the price or event that
       changes it…</p> -->
</section>

<section id="notes">
  <h2>Notes and sources</h2>
  <ol class="sources">
    <li id="cite_note-1">…filing, page/section…</li>
    <!-- 25+ entries, every in-text [n] resolves here -->
  </ol>
</section>
```

Rules: tables use `class="wikitable"` inside `.table-wrap`; every glossary term
is `<dfn>` at first use; estimates use `<section class="estimate">`; triggers
use `<p class="trigger">`; no emoji; colours only via the palette classes.

## 7. Output location & pipeline

1. **Output path:** `docs/blogs/<SYMBOL>_dossier.html`. If the file exists,
   update it in place. Never numbered copies. No `.docx`.
2. **Assemble:** `python3 scripts/assemble_report.py --body … --out …`
   (the writer never writes the `<head>`).
3. **Validate:** the four gates in section 5, in order.
4. **Portal rebuild (immediately after saving):**
   `python3 scripts/build_dossier_portal.py`
   <!-- MARKET US --> and verify `http://localhost:9050/<SYMBOL>_dossier.html` serves. <!-- /MARKET -->
5. **Cache hygiene:** scratch code lives only in `<RUN_DIR>` and is deleted
   with it (`../_shared/RUN_PROTOCOL.md` sections 1 and 5). Permanent scripts
   (`scripts/send_email.py`, `scripts/build_dossier_portal.py`,
   `scripts/serve_blogs.py`, `scripts/market_facts.py`,
   `scripts/validate_report.py`, `scripts/assemble_report.py`,
   `scripts/citation_check.py`, `scripts/readability_check.py`,
   `scripts/fetch_cache.py`, `scripts/momentum_gate.py`,
   `scripts/recompute_check.py`, `scripts/normalize_data.py`,
   `scripts/validate_data.py`) are never deleted or modified without the user.
   Pre-termination: `ls scripts/` shows only whitelisted files.
