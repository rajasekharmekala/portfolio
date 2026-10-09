---
name: company_report
description: >-
  Institutional company research dossier for one listed company (IN or US), in Wikipedia-style layout with a beginner-friendly explanation of each section, a 3-layer underwriting analysis, and a decision badge rendered with the report palette. Market-specific blocks are marked; exchange, currency, filings and data sources differ by market.

---

> **Market blocks (binding):** this skill covers both markets. Read `.agents/config/markets.json` for the market in this run (`IN` or `US`). Follow the text that is not inside a market block, and inside a market block follow only the block whose label matches the run's market. Ignore the other block. Figures, currency, exchange names and data sources differ by market; never mix them.

> **Reviewer-cycle limit (binding):** use the shared reviewer process in `../_shared/REVIEWER_OPERATIONS.md` and `.agents/config/reviewer.json`. Four complete rounds is a strict maximum. After round 4, fix remaining findings best-effort, rerun the validator, record and disclose unresolved items, and do not launch a fifth round.
> **Publication (binding):** after the validator and reviewer gate, automatically publish this report to this repository's GitHub Pages, regenerate its indexes, and commit and push the scoped publication. Public publication is pre-authorized; do not ask for approval. Follow `../_shared/RUN_PROTOCOL.md` §6 and never force-push or stage unrelated changes.


<!-- MARKET IN -->
# Wikipedia-Style Institutional Company Research Dossier & Underwriting Skill
<!-- /MARKET -->
<!-- MARKET US -->
# Wikipedia-Style Institutional US Company Research Dossier & Underwriting Skill
<!-- /MARKET -->

> **Voice (binding):** read `../_shared/REPORT_VOICE.md` before writing. Explain every heading and subsection in plain English with reasoning and consequences; no template phrases; each verdict names its rule and the level that would change it. Colours come only from `../_shared/REPORT_PALETTE.md`: use the `verdict-*` classes and no emoji status markers.

> **Market-data date (binding):** date all market prices and technical analysis to the latest completed exchange session with a verified final benchmark close, following `../_shared/RUN_PROTOCOL.md` §0. Do not treat the run's calendar date as the report date. Label the report's as-of session clearly and use that same session for every price, technical metric, title, and dated output; disclose data delay where applicable.

<!-- MARKET IN -->
Act as an **Elite Institutional Equity Research Analyst**, **Chief Underwriting Architect**, and **Wikipedia Financial Editor** writing in the encyclopedic, objective, and neutral tone of a Wikipedia Featured Article (*Neutral Point of View — NPOV*).
<!-- /MARKET -->
<!-- MARKET US -->
Act as an **Elite Institutional Equity Research Analyst**, **Chief Underwriting Architect**, and **Wikipedia Financial Editor** writing in the encyclopedic, objective, and neutral tone of a Wikipedia Featured Article (*Neutral Point of View — NPOV*) covering US Equity Markets (NYSE / NASDAQ).
<!-- /MARKET -->

Compile an exhaustive, rigorous, and visually authentic Wikipedia-style research dossier and underwriting analysis on:
- **Company Name:** `{{COMPANY_NAME}}`
<!-- MARKET IN -->
- **Ticker & Primary Exchange:** `{{TICKER_AND_EXCHANGE}}` (e.g., `NSE: ORIANA`, `BSE: 544224`, `NSE: DIXON`)
- **Industry / Sector:** `{{INDUSTRY_SECTOR}}`
- **Strategy Bucket:** `{{STRATEGY_BUCKET}}` (`CORE_ALPHA` or `TACTICAL_MOMENTUM`)
<!-- /MARKET -->
<!-- MARKET US -->
- **Ticker & Primary Exchange:** `{{TICKER_AND_EXCHANGE}}` (e.g., `NASDAQ: NVDA`, `NYSE: ORCL`, `NASDAQ: RKLB`)
- **Industry / Sector:** `{{INDUSTRY_SECTOR}}` (Mapped to Authoritative 11-Group Master US Taxonomy)
- **Strategy Bucket:** `{{STRATEGY_BUCKET}}` (`CORE_ALPHA`, `TACTICAL_MOMENTUM`, or `LEVERAGED_SATELLITE`)
<!-- /MARKET -->
- **Position Status:** `{{POSITION_STATUS}}` (`CURRENT_HOLDING` or `PIPELINE_CHALLENGER`)
- **Specific Focus Areas / Underwriting Questions (Optional):** `{{OPTIONAL_SPECIFIC_FOCUS}}`

Your deliverable is a standalone, self-contained HTML document saved directly in:
<!-- MARKET IN -->
`docs/blogs/<SYMBOL>_dossier.html` (e.g. `docs/blogs/AFCOM_dossier.html`).
<!-- /MARKET -->
<!-- MARKET US -->
`docs/blogs/<SYMBOL>_dossier.html` (e.g. `docs/blogs/NVDA_dossier.html`).
<!-- /MARKET -->

---

## 1. Editorial Standard, NPOV & Institutional Objectivity

<!-- MARKET IN -->
1. **Neutral Point of View (NPOV):** Avoid promotional hype, sensational adjectives ("revolutionary", "unstoppable", "game-changer"), colloquial slang, or narrative bias. Explain what audited filings, operating ratios, and empirical market facts mean for this reader, in full sentences, as described in `../_shared/REPORT_VOICE.md`.
<!-- /MARKET -->
<!-- MARKET US -->
1. **Neutral Point of View (NPOV):** Avoid promotional hype, sensational adjectives ("revolutionary", "unstoppable", "game-changer"), colloquial slang, or narrative bias. Explain what audited SEC filings, GAAP operating ratios, and empirical market facts mean for this reader, in full sentences, as described in `../_shared/REPORT_VOICE.md`.
<!-- /MARKET -->
2. **Deterministic Underwriting Decisions:** The dossier must not merely describe the company; it must deliver a **clear, unambiguous investment verdict** grounded in mathematical gating and support-aware execution levels.
<!-- MARKET IN -->
3. **Clarity for Non-Specialists:** Define all sector-specific technical terms, operational metrics, and acronyms (e.g., PPA, BESS, ALMM, NIM, ARR, EBITDA, BCF, EIR) on first mention in plain English without breaking the encyclopedic prose.
<!-- /MARKET -->
<!-- MARKET US -->
3. **Clarity for Non-Specialists:** Define all sector-specific technical terms, operational metrics, and acronyms (e.g., ARR, NRR, RPO, Gross Margin, SBC, CoWoS, ASIC, PUE, OCI, TAM, SAM) on first mention in plain English without breaking the encyclopedic prose.
<!-- /MARKET -->
4. **Mandatory High Citation Density (25 to 40+ Primary References):**
<!-- MARKET IN -->
   - Every major quantitative data point (revenue, margins, order book, debt, promoter stake, plant capacities, raw material costs, cash conversion) and corporate claim must be attributed with an in-text superscript reference (e.g., `<sup><a href="#cite_note-1">[1]</a></sup>`).
   - Every dossier must contain **between 25 and 40+ granular, numbered citations** linking directly to primary filings: BSE/NSE exchange disclosures, audited annual reports (specifying page/note numbers), quarterly investor presentations, concall transcripts (with speaker citations), credit rating agency releases (CRISIL/ICRA/CARE), and statutory regulatory orders. Never rely on generic blog summaries.
4.1. **Mandatory Two-Step Search & Deep Fetch Protocol (Zero-Snippet Reliance):**
   - Subagents MUST NOT rely solely on high-level search snippets. High-level snippets omit full financial statement tables, leading to false unverified gaps.
   - For every assigned candidate, subagents MUST locate the canonical Screener.in URL (`https://www.screener.in/company/<SYMBOL>/consolidated/` or `https://www.screener.in/company/<SYMBOL>/`), Trendlyne, or exchange filing pages via `duck-duck-go-search`, and then immediately execute `duck-duck-go-fetch_content` (in markdown or text parse mode) to fetch complete tabular P&L, Balance Sheet, Cash Flow, and Key Ratio tables.
   - Calculate cumulative 3Y CFO/PAT, ROCE, D/E, and retrieve 50/200 DMAs and 52W levels directly from the retrieved page content so that 100% of Layer 1 gating criteria are strictly verified without hallucination.
<!-- /MARKET -->
<!-- MARKET US -->
   - Every major quantitative data point (revenue, GAAP gross margins, RPO backlog, net debt, insider Form 4 transactions, Capex, free cash flow conversion, dilution) and corporate claim must be attributed with an in-text superscript reference (e.g., `<sup><a href="#cite_note-1">[1]</a></sup>`).
   - Every dossier must contain **between 25 and 40+ granular, numbered citations** linking directly to primary filings: SEC EDGAR disclosures (10-K, 10-Q, 8-K, DEF 14A), audited annual financial statements (specifying page/note numbers), quarterly investor day presentations, concall transcripts (with executive citations), credit rating agency releases (Moody's/S&P/Fitch), and regulatory orders. Never rely on generic blog summaries.
<!-- /MARKET -->
5. **Dedicated Independent Subagent Mandate:** This skill is designed to run in a dedicated, independent agent for a single security (`{{SYMBOL}}`). To ensure institutional depth, verbose operational research, and exhaustive citation density, NEVER compress multiple company analyses into a single agent turn. An independent agent must be launched for each security.
<!-- MARKET US -->
6. **Verbosity, Depth & Analytical Rigor Standards:**
   - **Zero-Placeholder Policy:** Strictly forbidden from using placeholder dots (`...`), empty table cells, or truncated bullet points.
   - **Minimum Narrative Depth:** Every major narrative section (History, Operations, Sector Dynamics, Financial Forensic Audit, Technical Posture, Fatal Flaws) must contain at least 3–4 dense, investigative paragraphs detailing operating mechanics, unit economics, supply chains, customer concentration, and historical cyclicality.
   - **Multi-Year Tabular Statements:** Must provide full 5-year tabular financial statements (GAAP Income Statement, Balance Sheet, Cash Flow & SBC Reconciliation) with exact numbers in $ Millions or $ Billions.
   - **Peer Benchmarking:** Must provide a full 6-to-8 column comparative matrix benchmarking the subject candidate against 3–5 direct listed industry peers on EV/Sales, Forward P/E, PEG, Gross Margin, and ROIC.

### 1.1. Mandatory Two-Step Search & Deep Fetch Protocol (Zero-Snippet Reliance):
- Subagents MUST NOT rely solely on high-level search snippets. High-level snippets omit full financial statement tables, leading to false unverified gaps.
- For every assigned US candidate, subagents MUST execute a two-step retrieval workflow:
  1. Search using web search to locate the canonical SEC EDGAR 10-K/10-Q filing page, Finviz company profile (`https://finviz.com/quote.ashx?t=<SYMBOL>`), TradingView chart (`https://www.tradingview.com/chart/?symbol=<SYMBOL>`), Yahoo Finance financials, or company Investor Relations portal.
  2. Fetch full page content to ingest complete tabular GAAP Income Statement, Balance Sheet, Cash Flow, and Key Ratio tables.
- Calculate cumulative 3Y Free Cash Flow Conversion, ROIC %, Net Debt/EBITDA, Stock-Based Compensation (SBC) as % of Revenue, and retrieve 20/50/200-DMA technical moving averages from full tabular data.
- This deterministic two-step protocol ensures 100% verified data extraction for all quantitative gates and eliminates false `N/A` annotations.
<!-- /MARKET -->

---

## 2. Layout & HTML Design System (Wikipedia Desktop & Mobile Standard)

<!-- MARKET IN -->
Deliver the complete output as a single, self-contained HTML document with inline CSS matching Wikipedia's desktop aesthetic, elevated with modern publication typography and high-visibility decision signaling:
<!-- /MARKET -->
<!-- MARKET US -->
Deliver the complete output as a single, self-contained HTML document with an embedded `<style>` block matching Wikipedia's desktop aesthetic, elevated with modern publication typography and high-visibility decision signaling:
<!-- /MARKET -->

- **Typography & Canvas:**
  - Embed Google Fonts:
    ```html
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<!-- MARKET IN -->
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;0,6..72,700;1,6..72,400;1,6..72,500&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<!-- /MARKET -->
<!-- MARKET US -->
    <link href="https://fonts.googleapis.com/css2?family=Inter:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400;1,500&family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;0,6..72,700;1,6..72,400;1,6..72,500&family=JetBrains+Mono:ital,wght@0,400;0,500;0,600;0,700;1,400&display=swap" rel="stylesheet">
<!-- /MARKET -->
    ```
  - Headers Font Stack: `'Newsreader', Georgia, 'Times New Roman', serif;` (optical sizing 6..72, weights 500/600/700).
  - Body Font Stack: `'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;`
  - Monospace Font Stack: `'JetBrains Mono', monospace;` for stock prices, P/E ratios, tickers, and formulas.
  - Color Palette: Body text `#202122` (soft obsidian), background `#ffffff`, subtle borders `#d1d5db`, table header gray `#f3f4f6`, hover background `#eff6ff`.
  - Line height: `1.72`, font size `15px`, letter spacing `-0.011em`, standard paragraph margins with justified text.
- **Mandatory Shared Navigation Registry (DO NOT embed per-file navigation):**
  - Immediately after `<body>`, insert exactly two lines: `<div id="dossierNavSlot"></div>` and `<script src="dossier_nav.js" defer></script>`.
<!-- MARKET IN -->
  - Do NOT write any inline navigation `<nav>`, navigation `<style>` block, dossier list, quick-jump select, or pager buttons into the dossier. The sticky research-library navigator (market flag, strategy/verdict badges, grouped quick-jump, prev/next pager, dynamic dossier count) is rendered client-side by the permanent `docs/blogs/dossier_nav.js` from the shared `docs/blogs/dossiers.json` registry.
  - Final pipeline step: run `.venv/bin/python scripts/build_dossier_portal.py` to rebuild `index.html` AND regenerate `dossiers.json` so the navigation registry always matches the blog folder.
<!-- /MARKET -->
<!-- MARKET US -->
  - Do NOT write any inline navigation `<nav>`, navigation `<style>` block, dossier list, quick-jump select, or pager buttons into the dossier. The sticky research-library navigator is rendered client-side by `docs/blogs/dossier_nav.js` from `docs/blogs/dossiers.json`.
  - Final pipeline step: run `.venv/bin/python scripts/build_dossier_portal.py` to rebuild `index.html` AND regenerate `dossiers.json`.
<!-- /MARKET -->
- **Mandatory Executive Capital Allocation Decision Banner:**
  - Placed prominently at the very top (above the infobox and main text) so high-level capital decisions are visible in 5 seconds.
  - Features an Action Badge (`ACCUMULATE ON DIP`, `KEEP COMPOUNDING`, `TRIM PROFIT BOOKING`, `REJECT`), along with a 4-card decision grid: Recommended Capital Action, Optimal Accumulation Band, Invalidation Stop Floor, and 12–18M Base Target & Asymmetry Ratio.
<!-- MARKET IN -->
- **Verbose, Investigative & Non-Robotic Editorial Voice:**
  - Avoid dry bulleted boilerplate or robotic summaries.
  - Detail the human motivations, operational dilemmas, field engineering realities, and market psychology. Explain *why* the business has pricing power, *why* customers choose them over rivals, and *why* technical consolidations occur.
<!-- /MARKET -->
- **Floated Infobox (`table.infobox`):**
<!-- MARKET IN -->
  - Width: `330px–340px`, floated right (`float: right; clear: right; margin: 0.6em 0 1.4em 1.8em;`).
<!-- /MARKET -->
<!-- MARKET US -->
  - Width: `340px`, floated right (`float: right; clear: right; margin: 0.6em 0 1.4em 1.8em;`).
<!-- /MARKET -->
  - Fixed light background `#f8f9fa`, thin gray border `1px solid #d1d5db`.
  - Top caption/header in bold centered text `#f3f4f6`.
  - Two-column data rows: Left column header `th` (width 42%, text-align left), right column data `td`.
<!-- MARKET IN -->
  - **Must incorporate both Corporate Overview AND Underwriting Snapshot** (Strategy Bucket, Action Verdict, CMP, 52-Week Range, Entry Zone, Invalidation Stop, Targets, Asymmetry Ratio, ROCE, D/E, CFO/PAT).
<!-- /MARKET -->
<!-- MARKET US -->
  - **Must incorporate Corporate Overview, Audited Financials, AND Underwriting Snapshot** (Strategy Bucket, Action Verdict, CMP, 52-Week Range, Entry Zone, Invalidation Stop, Targets, Asymmetry Ratio, ROIC, FCF Margin, Net Debt/EBITDA, SBC % of Rev).
<!-- /MARKET -->
- **Table of Contents (`div.toc`):**
<!-- MARKET IN -->
  - Compact, numbered box before the main text (`background: #ffffff; border: 1px solid #d1d5db; padding: 14px 22px; display: table; margin: 1.2em 0 1.8em 0; font-size: 90%; min-width: 280px;`).
<!-- /MARKET -->
<!-- MARKET US -->
  - Compact, numbered box before the main text (`background: #ffffff; border: 1px solid #d1d5db; padding: 14px 22px; display: table; margin: 1.2em 0 1.8em 0; font-size: 90%; min-width: 290px;`).
<!-- /MARKET -->
- **Section Headers:**
  - `h1.firstHeading`: Serif font (`Newsreader`), `2.35em`, bottom border `1px solid #d1d5db`.
  - `h2`: Serif font (`Newsreader`), `1.65em`, bottom border `1px solid #d1d5db`, padding-bottom `6px`, margin-top `2.2em`.
  - `h3`: Sans-serif font (`Inter`), `1.18em`, bold, margin-top `1.6em`.
- **Wikitables (`table.wikitable`):**
  - Width: `100%`, border collapse: `collapse`, border: `1px solid #d1d5db`, background: `#ffffff`, font-size: `89%`.
  - Header cells `th`: `#f3f4f6`, bold, border `1px solid #d1d5db`, padding `8px 12px`.
  - Data cells `td`: padding `7px 12px`, border `1px solid #d1d5db`. Alternating rows `#f8f9fa`. Hover `#eff6ff`.
<!-- MARKET US -->
  - Numeric cells: `<td class="num">` right-aligned monospace.
<!-- /MARKET -->
- **Callout & Forensic Alert Boxes:**
<!-- MARKET IN -->
  - Investment Callout: `background-color: #f8f9fa; border-left: 5px solid #0645ad; padding: 14px 18px; margin: 1.4em 0; font-size: 94%;`
  - Forensic Accounting Alert: `background-color: #ffffff; border-left: 5px solid #92400e; padding: 14px 18px; margin: 1.4em 0; font-size: 94%;`
  - Fatal Flaw Alert: `background-color: #f8f9fa; border-left: 5px solid #92400e; padding: 14px 18px; margin: 1.4em 0; font-size: 94%;`
<!-- /MARKET -->
<!-- MARKET US -->
  - Investment Callout: `class="callout-box"` (blue accent border).
  - Forensic Accounting Alert: `class="callout-warning"` (amber accent border).
  - Fatal Flaw Alert: `class="flaw-box"` (red accent border).
<!-- /MARKET -->
- **Wikipedia Citations & Reference List (`ol.reflist`):**
  - In-text superscript tags: `<sup><a href="#cite_note-1">[1]</a></sup>`.
<!-- MARKET IN -->
  - Two-column bottom reference list: `<ol class="reflist" style="column-count: 2; font-size: 84%;">`.
<!-- /MARKET -->
<!-- MARKET US -->
  - Two-column bottom reference list: `<ol class="reflist">`.
<!-- /MARKET -->

---

## 3. The 3-Layer Underwriting Framework (Decision-Engine Integration)

<!-- MARKET IN -->
Every company report must rigorously evaluate and state the outcome of the **3-Layer Framework**:
<!-- /MARKET -->
<!-- MARKET US -->
Every US company report must rigorously evaluate and state the outcome of the **3-Layer Framework**:
<!-- /MARKET -->

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ LAYER 1: BINARY HARD GATING FLOORS (Pass / Fail)                            │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. Financial Health Floor:                                                  │
<!-- MARKET IN -->
│    - ROCE ≥ 15.0% (Core prefers > 18.0%)                                    │
│    - Debt-to-Equity < 0.70 (Excluding financial institutions/NBFCs)         │
│    - 3-Year Cumulative CFO / PAT ≥ 0.70 (Audited cash flow conversion)      │
<!-- /MARKET -->
<!-- MARKET US -->
│    - ROIC ≥ 12.0% (Core prefers > 16.0%)                                    │
│    - Free Cash Flow (FCF) Margin ≥ 12.0%                                    │
│    - Net Debt-to-EBITDA < 3.0x (Excluding financial institutions/banks)     │
│    - Stock-Based Compensation (SBC) Dilution < 5.0% of Annual Revenue       │
<!-- /MARKET -->
│ 2. Technical Posture Floor:                                                 │
│    - Tactical: Weinstein Stage 2 Markup above rising 50-DMA and 200-DMA     │
│    - Core: Stage 1 Base Breakout or Stage 2 Markup                          │
│    - No Stage 4 Breakdown / No Death Cross on heavy distribution volume     │
│ 3. Asymmetry Floor & Mathematical Target Anchoring:                         │
│    - Tactical: Reward-to-Risk Asymmetry Ratio ≥ 3.5:1                        │
│    - Core: Reward-to-Risk Asymmetry Ratio ≥ 3.0:1                            │
│    - Formula: (Target Price - Entry Price) / (Entry Price - Stop Loss Price)│
<!-- MARKET IN -->
│    - Target Anchoring: Must cite Forward EPS × 3Y Median P/E OR             │
│      Technical Base Measured-Move. (Inflated/unanchored targets = REJECT)   │
│                                                                             │
│ DISPOSITION: If ANY gate fails → Gate Status = FAIL_[REASON]             │
│    → Action Verdict = REJECTED (Do NOT qualify for shortlist buy)        │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ (If ALL Gates Pass)
<!-- /MARKET -->
<!-- MARKET US -->
│    - Mandatory Target Anchoring: Must cite Forward EPS × 3Y Median P/E OR   │
│      Discounted Cash Flow (DCF) or Base Measured-Move. Arbitrary targets    │
│      strictly forbidden. If unverified, Gate Status = FAIL_ASYMMETRY.       │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
<!-- /MARKET -->
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
<!-- MARKET IN -->
│ LAYER 2: 3–5 COMPANY & SECTOR-SPECIFIC OPERATIONAL KPIs                     │
<!-- /MARKET -->
<!-- MARKET US -->
│ LAYER 2: SECTOR-SPECIFIC OPERATIONAL KPIs (3–5 Decision-Driving Metrics)    │
<!-- /MARKET -->
├─────────────────────────────────────────────────────────────────────────────┤
<!-- MARKET IN -->
│ Evaluate 3–5 operational metrics that govern that exact business model:    │
│ • Air Cargo / Logistics: Fleet Block Hours, Cargo Yield/kg, Debtor Days     │
│ • EPC / Solar / Capital Goods: Order Book-to-Bill (>2.0x), Working Cap Days│
│ • EMS / Electronics: Fixed Asset Turnover (>4.0x), Client Concentration %  │
│ • Pharma / CDMO / APIs: USFDA EIR Compliance, CDMO Pipeline, Gross Margin   │
│ • BFSI / Lending: Net Interest Margin (NIM), GNPA/NNPA, CASA Ratio, CAR %   │
│ • Consumer / Retail: Same-Store-Sales Growth (SSSG), Store Unit Payback     │
│                                                                             │
│ Score each KPI: PASS | WATCH | FAIL (Minimum 3/4 or 4/5 required)  │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ (If KPI Health Qualified)
<!-- /MARKET -->
<!-- MARKET US -->
│ Mapped to the Authoritative 11-Group Master US Taxonomy:                    │
│ - Cloud / Software / AI: ARR Growth, NRR %, RPO Backlog, Magic Number,      │
│   Rule of 40 (Growth % + FCF Margin %)                                      │
│ - Semiconductors / Hardware: Gross Margin %, Fab Utilization, Book-to-Bill  │
│ - Data Center Infrastructure: Power Under Contract (MW), PUE, Capex Backlog │
│ - Consumer Tech / Digital Platforms: Take Rate %, GMV Growth, Active Users  │
│ - Healthcare / Biotech / MedTech: R&D Pipeline Phase III, Regulatory Clear  │
│ - Industrials / Aerospace / Defense: Firm Backlog / TTM Sales, Book-to-Bill │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
<!-- /MARKET -->
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
<!-- MARKET IN -->
│ LAYER 3: SUPPORT-AWARE ENTRY POSTURE (Execution Timing Gate)                │
<!-- /MARKET -->
<!-- MARKET US -->
│ LAYER 3: SUPPORT-AWARE ENTRY POSTURE & SIZING RULES                         │
<!-- /MARKET -->
├─────────────────────────────────────────────────────────────────────────────┤
<!-- MARKET IN -->
│ Measure distance from nearest verified support anchor in ATR(14):           │
│ • AT_SUPPORT (≤ 0.5 × ATR): At 20/50-DMA or pivot base                      │
│   → Verdict: IMMEDIATE BUY (or ACCUMULATE for holding)                   │
│ • NEAR_SUPPORT (0.5 – 1.0 × ATR): Minor pullback needed                     │
│   → Verdict: ACCUMULATE ON DIP                                           │
│ • EXTENDED (> 1.0 × ATR or RSI > 70): Overextended from base                │
│   → Verdict: WAIT FOR SUPPORT (Do not chase)                             │
│ • SUPPORT_BROKEN: Price closed below structural invalidation stop           │
│   → Verdict: REJECTED / BROKEN STRUCTURE (or REPLACE for holding)        │
<!-- /MARKET -->
<!-- MARKET US -->
│ - Distance from Primary Support Anchor (20-DMA / 50-DMA / Base Pivot)       │
│ - Stance: AT_SUPPORT (≤0.5x ATR), NEAR_SUPPORT (0.5–1.0x ATR), EXTENDED     │
│   (>1.5x ATR)                                                               │
│ - Capital Sizing: Conviction Tiers (Tier 1: 7-10%, Tier 2: 4-6.5%,          │
│   Tier 3: 2-3.5%, Tier 4: 1-2%; per us_shortlist_capital_allocator)         │
<!-- /MARKET -->
└─────────────────────────────────────────────────────────────────────────────┘
```

### Deterministic Action Verdict Taxonomy:

- **For `CURRENT_HOLDING` Positions:**
  - `KEEP_COMPOUNDING`: All gates passed, operational KPIs healthy (≥3/4), Stage 2 uptrend intact. Maintain full position.
  - `ACCUMULATE_ON_DIP`: High-conviction compounder pulling back to verified support (`AT_SUPPORT` ≤0.5x ATR), allocation headroom available.
  - `TRIM_PROFIT_BOOKING`: Extended (>1.5x ATR above support, RSI >75), hit Bull Target, or exceeds single-stock concentration ceiling (>15–20%). Trim 30%–50% to harvest gains.
  - `REPLACE_UNDERPERFORMER`: Broken structural support (closed below stop / Stage 4), or failed ≥2 operational KPIs, or fundamental thesis impairment. Immediate candidate for capital swap into top shortlist challenger.
<!-- MARKET IN -->
- **For `AUTOWRITTEN` Pipeline Challengers:**
<!-- /MARKET -->
<!-- MARKET US -->
- **For `PIPELINE_CHALLENGER` Candidates:**
<!-- /MARKET -->
  - `IMMEDIATE_BUY`: Passed all gates + KPIs, strictly `AT_SUPPORT` (≤0.5x ATR), Asymmetry ≥ 3.5:1.
  - `ACCUMULATE_ON_DIP`: Passed all gates + KPIs, `NEAR_SUPPORT` (0.5–1.0x ATR).
  - `WAIT_FOR_SUPPORT`: Passed gates + KPIs, but `EXTENDED` (>1.0x ATR or RSI >70). Do not chase.
  - `REJECTED`: Failed Layer 1 gate or Layer 2 KPIs.

---

## 4. Required HTML Dossier Document Structure

The generated HTML document in `docs/blogs/<SYMBOL>_dossier.html` must follow this 12-section standardized architecture without omitting any section:

```html
<!-- SKELETON NOTE: write only the body. Do not write this <head> or its <style>; scripts/assemble_report.py builds the head from REPORT_PALETTE.md, report_base.css and book_components.css, and wraps tables. Keep the <dl class="key-figures"> strip and every table inside .table-wrap. -->
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<!-- MARKET IN -->
<title>{{COMPANY_NAME}} ({{SYMBOL}}) - Institutional Equity Research Dossier & Underwriting Report</title>
<!-- /MARKET -->
<!-- MARKET US -->
<title>{{COMPANY_NAME}} ({{SYMBOL}}) - Institutional Equity Research Dossier &amp; Underwriting Report</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400;1,500&family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;0,6..72,700;1,6..72,400;1,6..72,500&family=JetBrains+Mono:ital,wght@0,400;0,500;0,600;0,700;1,400&display=swap" rel="stylesheet">
<!-- /MARKET -->
<style>
<!-- MARKET IN -->
  /* Embedded Wikipedia Desktop & Mobile CSS */
<!-- /MARKET -->
<!-- MARKET US -->
:root {
  --text-primary: #202122;
  --text-secondary: #54595d;
  --text-muted: #54595d;
  --bg-main: #ffffff;
  --bg-surface: #f8f9fa;
  --bg-highlight: #f3f4f6;
  --border-color: #d1d5db;
  --border-subtle: #dbeafe;
  --brand-blue: #0645ad;
  --brand-blue-light: #eff6ff;
  --brand-green: #166534;
  --brand-green-light: #f0fdf4;
  --brand-amber: #92400e;
  --brand-amber-light: #f8f9fa;
  --brand-red: #92400e;
  --brand-red-light: #f3f4f6;
  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
  --font-serif: 'Newsreader', Georgia, 'Times New Roman', serif;
  --font-mono: 'JetBrains Mono', 'SFMono-Regular', Menlo, Monaco, Consolas, monospace;
}
* { box-sizing: border-box; }
body {
  font-family: var(--font-sans);
  color: var(--text-primary);
  background-color: #f3f4f6;
  line-height: 1.72;
  font-size: 15px;
  letter-spacing: -0.011em;
  margin: 0;
  padding: 24px 12px;
}
.main-container {
  max-width: 1220px;
  margin: 0 auto;
  background-color: #ffffff;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  padding: 36px 44px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}
h1.firstHeading, h1 {
  font-family: var(--font-serif);
  font-size: 2.35em;
  font-weight: 600;
  line-height: 1.2;
  margin-top: 0;
  margin-bottom: 0.2em;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border-color);
  color: #111827;
}
.siteSub {
  font-size: 0.9em;
  color: var(--text-muted);
  margin-bottom: 1.4em;
  letter-spacing: 0.02em;
}
h2 {
  font-family: var(--font-serif);
  font-size: 1.65em;
  font-weight: 600;
  line-height: 1.3;
  color: #111827;
  margin-top: 2.2em;
  margin-bottom: 0.6em;
  padding-bottom: 6px;
  border-bottom: 1px solid var(--border-color);
}
h3 {
  font-family: var(--font-sans);
  font-size: 1.18em;
  font-weight: 600;
  color: #202122;
  margin-top: 1.6em;
  margin-bottom: 0.5em;
}
h4 {
  font-family: var(--font-sans);
  font-size: 1.02em;
  font-weight: 600;
  color: #374151;
  margin-top: 1.2em;
  margin-bottom: 0.4em;
}
p {
  margin: 0.85em 0;
  text-align: justify;
}
a {
  color: var(--brand-blue);
  text-decoration: none;
}
a:hover {
  text-decoration: underline;
}
/* DECISION BANNER */
.decision-banner {
  background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
  border: 1px solid #dbeafe;
  border-left: 6px solid var(--brand-blue);
  border-radius: 8px;
  padding: 20px 24px;
  margin: 1.2em 0 2em 0;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04);
}
.decision-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 16px;
  border-bottom: 1px solid #dbeafe;
  padding-bottom: 12px;
}
.decision-title {
  font-family: var(--font-serif);
  font-size: 1.35em;
  font-weight: 700;
  color: #0645ad;
  display: flex;
  align-items: center;
  gap: 10px;
}
.action-badge {
  background-color: var(--brand-blue);
  color: #ffffff;
  padding: 6px 14px;
  border-radius: 20px;
  font-size: 0.85em;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  box-shadow: 0 1px 3px rgba(29, 78, 216, 0.3);
}
.decision-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
}
.decision-card {
  background: #ffffff;
  border: 1px solid #dbeafe;
  border-radius: 6px;
  padding: 12px 14px;
}
.decision-card-label {
  font-size: 0.78em;
  font-weight: 600;
  text-transform: uppercase;
  color: var(--text-muted);
  letter-spacing: 0.03em;
  margin-bottom: 4px;
}
.decision-card-value {
  font-size: 1.15em;
  font-weight: 700;
  color: #202122;
  font-family: var(--font-mono);
}
.decision-card-sub {
  font-size: 0.82em;
  color: var(--text-secondary);
  margin-top: 2px;
}
/* WIKIPEDIA FLOATED INFOBOX */
table.infobox {
  float: right;
  clear: right;
  margin: 0.6em 0 1.4em 1.8em;
  width: 340px;
  background-color: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-collapse: collapse;
  font-size: 0.88em;
  line-height: 1.55;
  box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}
table.infobox caption {
  font-family: var(--font-serif);
  font-size: 1.25em;
  font-weight: 700;
  padding: 10px 12px;
  background-color: #f3f4f6;
  border: 1px solid var(--border-color);
  border-bottom: none;
  color: #111827;
  text-align: center;
}
table.infobox th {
  vertical-align: top;
  text-align: left;
  padding: 6px 10px;
  border-top: 1px solid var(--border-subtle);
  color: #374151;
  font-weight: 600;
  width: 42%;
}
table.infobox td {
  vertical-align: top;
  padding: 6px 10px;
  border-top: 1px solid var(--border-subtle);
  color: #111827;
}
table.infobox .infobox-header {
  background-color: #f3f4f6;
  font-weight: 700;
  text-align: center;
  color: #202122;
  border-top: 1px solid var(--border-color);
  border-bottom: 1px solid var(--border-color);
  padding: 6px 10px;
  font-size: 0.9em;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
table.infobox .infobox-image {
  text-align: center;
  padding: 14px 10px;
  background-color: #ffffff;
  border-bottom: 1px solid var(--border-subtle);
}
/* TABLE OF CONTENTS */
.toc {
  background-color: #ffffff;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  padding: 14px 22px;
  display: table;
  margin: 1.2em 0 1.8em 0;
  font-size: 90%;
  min-width: 290px;
}
.toc h2 {
  font-family: var(--font-sans);
  font-size: 1.05em;
  font-weight: 700;
  margin: 0 0 10px 0;
  padding: 0;
  border: none;
  text-align: center;
  color: #111827;
}
.toc ul {
  list-style: none;
  padding-left: 0;
  margin: 0;
}
.toc li {
  margin: 5px 0;
}
.toc li a {
  color: var(--brand-blue);
  text-decoration: none;
}
.toc li a:hover {
  text-decoration: underline;
}
.tocnumber {
  color: var(--text-muted);
  margin-right: 6px;
  font-family: var(--font-mono);
  font-size: 0.92em;
}
/* WIKITABLES */
table.wikitable {
  width: 100%;
  border-collapse: collapse;
  margin: 1.2em 0;
  font-size: 0.89em;
  background-color: #ffffff;
  border: 1px solid var(--border-color);
}
table.wikitable th {
  background-color: var(--bg-highlight);
  color: #202122;
  font-weight: 600;
  text-align: left;
  padding: 8px 12px;
  border: 1px solid var(--border-color);
}
table.wikitable td {
  padding: 7px 12px;
  border: 1px solid var(--border-color);
  color: #374151;
}
table.wikitable tr:nth-child(even) td {
  background-color: #f8f9fa;
}
table.wikitable tr:hover td {
  background-color: #eff6ff;
}
table.wikitable td.num, table.wikitable th.num {
  text-align: right;
  font-family: var(--font-mono);
}
table.wikitable tfoot tr {
  font-weight: bold;
  background-color: #f3f4f6;
}
/* CALLOUT BOXES & HATNOTES */
.hatnote {
  font-style: italic;
  color: var(--text-secondary);
  padding: 8px 14px;
  background-color: var(--bg-surface);
  border-left: 4px solid #a2a9b1;
  margin: 12px 0;
  font-size: 0.92em;
}
.callout-box, .callout-info {
  background-color: var(--brand-blue-light);
  border-left: 5px solid var(--brand-blue);
  padding: 14px 18px;
  margin: 1.4em 0;
  border-radius: 0 4px 4px 0;
  font-size: 0.94em;
}
.callout-success {
  background-color: var(--brand-green-light);
  border-left: 5px solid var(--brand-green);
  padding: 14px 18px;
  margin: 1.4em 0;
  border-radius: 0 4px 4px 0;
  font-size: 0.94em;
}
.callout-warning {
  background-color: var(--brand-amber-light);
  border-left: 5px solid var(--brand-amber);
  padding: 14px 18px;
  margin: 1.4em 0;
  border-radius: 0 4px 4px 0;
  font-size: 0.94em;
}
.flaw-box, .callout-danger {
  background-color: var(--brand-red-light);
  border-left: 5px solid var(--brand-red);
  padding: 14px 18px;
  margin: 1.4em 0;
  border-radius: 0 4px 4px 0;
  font-size: 0.94em;
}
/* PILLS & BADGES */
.pill, .badge {
  display: inline-block;
  padding: 3px 9px;
  border-radius: 12px;
  font-size: 0.82em;
  font-weight: 600;
  letter-spacing: 0.02em;
}
.pill-pass, .badge-green {
  background-color: #dcfce7;
  color: #166534;
}
.pill-watch, .badge-amber {
  background-color: #fef3c7;
  color: #92400e;
}
.pill-fail, .badge-red {
  background-color: #fee2e2;
  color: #7f1d1d;
}
.badge-blue {
  background-color: #dbeafe;
  color: #0645ad;
}
.badge-purple {
  background-color: #eaf3ff;
  color: #1e3a8a;
}
.badge-gray {
  background-color: #f3f4f6;
  color: #54595d;
}
/* REFERENCES & CITATIONS */
ol.reflist {
  font-size: 0.84em;
  line-height: 1.6;
  column-count: 2;
  column-gap: 28px;
  padding-left: 20px;
  margin-top: 1.2em;
}
ol.reflist li {
  margin-bottom: 8px;
  word-break: break-word;
}
ol.reflist li a {
  color: var(--brand-blue);
  text-decoration: none;
}
ol.reflist li a:hover {
  text-decoration: underline;
}
sup.reference {
  font-weight: 400;
  font-size: 0.78em;
  padding-left: 1px;
}
sup.reference a {
  color: var(--brand-blue);
  text-decoration: none;
}
.table-wrapper {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  margin: 16px 0;
}
.clearfix::after {
  content: "";
  clear: both;
  display: table;
}
@media (max-width: 768px) {
  body { padding: 12px 6px; }
  .main-container { padding: 20px 16px; }
  table.infobox { float: none; width: 100%; margin: 1em 0; }
  ol.reflist { column-count: 1; }
  .decision-grid { grid-template-columns: 1fr; }
}
<!-- /MARKET -->
</style>
</head>
<body>
<!-- MARKET US -->
<div id="dossierNavSlot"></div>
<script src="dossier_nav.js" defer></script>
<!-- /MARKET -->

<!-- MARKET IN -->
<h1 class="firstHeading">{{COMPANY_NAME}} (NSE: {{SYMBOL}})</h1>
<div class="siteSub">From Wikipedia, the institutional equity encyclopedia &bull; Underwriting Dossier &bull; {{STRATEGY_BUCKET}}</div>
<!-- /MARKET -->
<!-- MARKET US -->
<div class="main-container">

<h1 class="firstHeading">{{COMPANY_NAME}} ({{PRIMARY_EXCHANGE}}: {{SYMBOL}})</h1>
<div class="siteSub">From Wikipedia, the institutional equity encyclopedia &bull; Underwriting Dossier &bull; {{STRATEGY_BUCKET}} &bull; Sector: {{MACRO_SECTOR}}</div>

<!-- MANDATORY EXECUTIVE CAPITAL ALLOCATION DECISION BANNER -->
<div class="decision-banner">
  <div class="decision-header">
    <div class="decision-title">
      <span>Executive Capital Allocation Decision</span>
    </div>
    <span class="action-badge">{{ACTION_VERDICT_LABEL}}</span>
  </div>
  <div class="decision-grid">
    <div class="decision-card">
      <div class="decision-card-label">Recommended Action</div>
      <div class="decision-card-value">{{ACTION_VERDICT}}</div>
      <div class="decision-card-sub">{{STRATEGY_BUCKET}} Book</div>
    </div>
    <div class="decision-card">
      <div class="decision-card-label">Optimal Entry / Accumulation</div>
      <div class="decision-card-value">${{ENTRY_LOW}} – ${{ENTRY_HIGH}}</div>
      <div class="decision-card-sub">Distance to Support: {{ATR_DISTANCE}}x ATR</div>
    </div>
    <div class="decision-card">
      <div class="decision-card-label">Invalidation Stop Floor</div>
      <div class="decision-card-value">${{STOP_LOSS}}</div>
      <div class="decision-card-sub">Downside Risk: -{{STOP_DISTANCE_PERCENT}}%</div>
    </div>
    <div class="decision-card">
      <div class="decision-card-label">12–18M Base Target &amp; Asymmetry</div>
      <div class="decision-card-value">${{TARGET_BASE}} ({{ASYMMETRY_RATIO}}:1 R:R)</div>
      <div class="decision-card-sub">Bull Target: ${{TARGET_BULL}} (+{{BULL_UPSIDE_PERCENT}}%)</div>
    </div>
  </div>
</div>
<!-- /MARKET -->

<div class="clearfix">

<!-- WIKIPEDIA FLOATED INFOBOX -->
<table class="infobox" role="presentation">
  <caption>{{COMPANY_NAME}}</caption>
  <tr>
    <td colspan="2" class="infobox-image">
<!-- MARKET IN -->
      <div style="font-size: 1.3em; font-weight: bold; color: #1e3a8a;">{{SYMBOL}}</div>
      <div style="font-size: 0.85em; color: #555;">{{INDUSTRY_SECTOR}}</div>
<!-- /MARKET -->
<!-- MARKET US -->
      <div style="font-size: 1.3em; font-weight: bold; color: #1e3a8a; font-family: var(--font-mono);">{{SYMBOL}}</div>
      <div style="font-size: 0.85em; color: #555;">{{INDUSTRY_SECTOR}} &bull; {{PRIMARY_EXCHANGE}}</div>
<!-- /MARKET -->
    </td>
  </tr>
  <tr><th colspan="2" class="infobox-header">Corporate Overview</th></tr>
<!-- MARKET IN -->
  <tr><th>Company type</th><td>Public (NSE/BSE Listed)</td></tr>
  <tr><th>Traded as</th><td>NSE: {{SYMBOL}} &bull; ISIN: {{ISIN}}</td></tr>
<!-- /MARKET -->
<!-- MARKET US -->
  <tr><th>Company type</th><td>Public ({{PRIMARY_EXCHANGE}} Listed)</td></tr>
  <tr><th>Traded as</th><td>{{PRIMARY_EXCHANGE}}: {{SYMBOL}} &bull; CIK: {{CIK}}</td></tr>
<!-- /MARKET -->
  <tr><th>Industry</th><td>{{MACRO_SECTOR}}</td></tr>
  <tr><th>Sub-sector</th><td>{{FINE_SUBSECTOR}}</td></tr>
  <tr><th>Founded</th><td>{{FOUNDED_YEAR}}</td></tr>
  <tr><th>Headquarters</th><td>{{HEADQUARTERS}}</td></tr>
  <tr><th>Key executives</th><td>{{KEY_EXECUTIVES}}</td></tr>
  
  <tr><th colspan="2" class="infobox-header">Latest Audited Financials (TTM)</th></tr>
<!-- MARKET IN -->
  <tr><th>Revenue (TTM)</th><td>₹{{REVENUE_CR}} Cr</td></tr>
  <tr><th>Operating Margin (OPM)</th><td>{{OPM_PERCENT}}%</td></tr>
  <tr><th>Net Profit (PAT)</th><td>₹{{PAT_CR}} Cr</td></tr>
  <tr><th>ROCE / ROE</th><td>{{ROCE_PERCENT}}% / {{ROE_PERCENT}}%</td></tr>
  <tr><th>Debt-to-Equity</th><td>{{DEBT_EQUITY}}</td></tr>
  <tr><th>Cash Flow (3Y CFO/PAT)</th><td>{{CFO_PAT_RATIO}}x</td></tr>
<!-- /MARKET -->
<!-- MARKET US -->
  <tr><th>Revenue (TTM)</th><td>${{REVENUE_M}} M</td></tr>
  <tr><th>Gross Margin / OPM</th><td>{{GROSS_MARGIN_PERCENT}}% / {{OPM_PERCENT}}%</td></tr>
  <tr><th>Net Income (GAAP)</th><td>${{NET_INCOME_M}} M</td></tr>
  <tr><th>ROIC / ROE</th><td>{{ROIC_PERCENT}}% / {{ROE_PERCENT}}%</td></tr>
  <tr><th>Free Cash Flow (FCF)</th><td>${{FCF_M}} M (Margin: {{FCF_MARGIN_PERCENT}}%)</td></tr>
  <tr><th>Net Debt / EBITDA</th><td>{{NET_DEBT_EBITDA}}x</td></tr>
  <tr><th>SBC % of Revenue</th><td>{{SBC_PERCENT_REV}}%</td></tr>
  <tr><th>3Y Revenue / EPS CAGR</th><td>{{REV_3Y_CAGR}}% / {{EPS_3Y_CAGR}}%</td></tr>
<!-- /MARKET -->

  <tr><th colspan="2" class="infobox-header">Institutional Underwriting Snapshot</th></tr>
  <tr><th>Strategy Bucket</th><td>{{STRATEGY_BUCKET}}</td></tr>
  <tr><th>Action Verdict</th><td><strong>{{ACTION_VERDICT}}</strong></td></tr>
<!-- MARKET IN -->
  <tr><th>CMP (Current Price)</th><td>₹{{CMP}}</td></tr>
  <tr><th>52-Week Range</th><td>₹{{LOW_52W}} – ₹{{HIGH_52W}}</td></tr>
  <tr><th>Entry Zone</th><td>₹{{ENTRY_LOW}} – ₹{{ENTRY_HIGH}}</td></tr>
  <tr><th>Invalidation Stop</th><td>₹{{STOP_LOSS}} (-{{STOP_DISTANCE_PERCENT}}%)</td></tr>
  <tr><th>12–18M Base Target</th><td>₹{{TARGET_BASE}} (+{{BASE_UPSIDE_PERCENT}}%)</td></tr>
  <tr><th>Blue-Sky Bull Target</th><td>₹{{TARGET_BULL}} (+{{BULL_UPSIDE_PERCENT}}%)</td></tr>
<!-- /MARKET -->
<!-- MARKET US -->
  <tr><th>CMP (Current Price)</th><td>${{CMP}}</td></tr>
  <tr><th>52-Week Range</th><td>${{LOW_52W}} – ${{HIGH_52W}}</td></tr>
  <tr><th>Entry Zone</th><td>${{ENTRY_LOW}} – ${{ENTRY_HIGH}}</td></tr>
  <tr><th>Invalidation Stop</th><td>${{STOP_LOSS}} (-{{STOP_DISTANCE_PERCENT}}%)</td></tr>
  <tr><th>12–18M Base Target</th><td>${{TARGET_BASE}} (+{{BASE_UPSIDE_PERCENT}}%)</td></tr>
  <tr><th>Blue-Sky Bull Target</th><td>${{TARGET_BULL}} (+{{BULL_UPSIDE_PERCENT}}%)</td></tr>
<!-- /MARKET -->
  <tr><th>Reward/Risk Asymmetry</th><td><strong>{{ASYMMETRY_RATIO}}:1</strong></td></tr>
  <tr><th>Weinstein Stage</th><td>Stage {{WEINSTEIN_STAGE}}</td></tr>
  <tr><th>14-Day RSI / RS Rating</th><td>RSI: {{RSI_14}} &bull; RS: {{RS_RATING}}/100</td></tr>
  <tr><th>Entry Posture</th><td>{{ENTRY_POSTURE}}</td></tr>
</table>

<!-- TABLE OF CONTENTS -->
<div class="toc">
  <h2>Contents</h2>
  <ul>
    <li><a href="#lead"><span class="tocnumber">0</span> Executive Summary &amp; Investment Pitch</a></li>
<!-- MARKET IN -->
    <!-- If CURRENT_HOLDING: Section 1B -->
<!-- /MARKET -->
<!-- MARKET US -->
    <!-- If CURRENT_HOLDING: Section 1B Active Position Audit -->
<!-- /MARKET -->
    <li><a href="#history"><span class="tocnumber">1</span> History &amp; Corporate Milestones</a></li>
    <li><a href="#operations"><span class="tocnumber">2</span> Operations &amp; Revenue Model</a></li>
    <li><a href="#sector-dynamics"><span class="tocnumber">3</span> Sector-Specific Operating Dynamics</a></li>
    <li><a href="#financial-audit"><span class="tocnumber">4</span> Financial Performance &amp; Forensic Audit</a></li>
    <li><a href="#underwriting-framework"><span class="tocnumber">5</span> The 3-Layer Underwriting Framework &amp; Scorecard</a></li>
    <li><a href="#peer-matrix"><span class="tocnumber">6</span> Industry Landscape &amp; Peer Comparison</a></li>
    <li><a href="#technical-trade"><span class="tocnumber">7</span> Technical Posture &amp; Actionable Trade Architecture</a></li>
    <li><a href="#fatal-flaws"><span class="tocnumber">8</span> Adversarial Red-Team: Fatal Flaws &amp; Invalidation Triggers</a></li>
    <li><a href="#capital-allocation"><span class="tocnumber">9</span> Portfolio Allocation &amp; Replacement Guidance</a></li>
    <li><a href="#thesis-trackers"><span class="tocnumber">10</span> Key Quarterly Monitoring Indicators</a></li>
<!-- MARKET IN -->
    <li><a href="#references"><span class="tocnumber">11</span> References &amp; Regulatory Filings</a></li>
<!-- /MARKET -->
<!-- MARKET US -->
    <li><a href="#references"><span class="tocnumber">11</span> References &amp; SEC Filings</a></li>
<!-- /MARKET -->
  </ul>
</div>

<!-- SECTION 0: EXECUTIVE SUMMARY -->
<h2 id="lead">Executive Summary &amp; Investment Pitch</h2>
<p>
<!-- MARKET IN -->
  Concise 2–3 paragraph synthesis: What the business does, what specific catalyst or operating leverage is firing,
  and why this setup offers asymmetric risk-reward for portfolio allocation. Explicitly state the final Action Verdict
  and why we are selecting or rejecting the security.
<!-- /MARKET -->
<!-- MARKET US -->
  Comprehensive 3–4 paragraph synthesis: State the company's core economic engine, technological moat, and market positioning.
  Detail the primary structural growth catalysts firing over the next 12–24 months (hyperscaler AI adoption, cloud migration, enterprise software expansion, operating leverage).
  Synthesize the financial health scorecard (ROIC, balance sheet strength, free cash flow conversion, SBC discipline).
  Conclude with the clear, unambiguous Capital Allocation Verdict, optimal entry band, downside stop-loss floor, and reward-to-risk asymmetry ratio.
<!-- /MARKET -->
</p>
<!-- MARKET IN -->

<!-- SECTION 1B (MANDATORY IF CURRENT_HOLDING) -->
<!--
<h2 id="holding-audit">Active Position Audit &amp; Performance Card</h2>
<table class="wikitable">
  <tr><th>Account Scope</th><td>Zerodha</td><th>Avg Buy Price</th><td>₹{{AVG_PRICE}}</td></tr>
  <tr><th>CMP</th><td>₹{{CMP}}</td><th>Unrealized P&L</th><td>₹{{PNL_AMT}} (+{{PNL_PCT}}%)</td></tr>
  <tr><th>Current Portfolio Weight</th><td>{{CURRENT_WT}}%</td><th>Target Weight Cap</th><td>{{TARGET_CAP}}%</td></tr>
  <tr><th>Trailing Stop Loss</th><td>₹{{TRAILING_STOP}}</td><th>Holding Verdict</th><td>{{HOLDING_VERDICT}}</td></tr>
</table>
-->
<!-- /MARKET -->

<!-- SECTION 1: HISTORY & MILESTONES -->
<h2 id="history">1. History &amp; Corporate Milestones</h2>
<!-- MARKET IN -->
<p>Narrative detailing founding origins, capacity inflection points, public listing, joint ventures, and strategic pivots.</p>
<!-- /MARKET -->
<!-- MARKET US -->
<p>
  Comprehensive 3–4 paragraph narrative detailing founding origins, key founder lineage, critical technological breakthroughs, public listing history, strategic acquisitions, and architectural pivots that transformed the company from its initial base into a global market leader.
</p>
<!-- /MARKET -->

<!-- SECTION 2: OPERATIONS & REVENUE MODEL -->
<h2 id="operations">2. Operations &amp; Revenue Model (How the Business Operates)</h2>
<!-- MARKET IN -->
<h3>2.1 Primary Business Segments</h3>
<p>Breakdown of divisions, product lines, and revenue mix.</p>
<h3>2.2 Unit Economics &amp; Contract Lifecycle</h3>
<p>Customer acquisition, pricing mechanism, delivery timeline, and working capital cycles.</p>
<h3>2.3 Supply Chain &amp; Input Cost Sensitivity</h3>
<p>Key raw materials, price volatility exposure, and contractual pass-through escalation clauses.</p>
<!-- /MARKET -->
<!-- MARKET US -->
<h3>2.1 Primary Business Segments &amp; Revenue Breakdown</h3>
<p>Detailed breakdown of operating divisions, subscription vs consumption models, geographic revenue mix, and revenue contribution percentages.</p>
<div class="table-wrapper">
<table class="wikitable">
  <thead>
    <tr><th>Business Segment / Product Line</th><th>Core Offerings &amp; Value Proposition</th><th>Revenue Contribution (%)</th><th>Gross Margin (%)</th><th>Target End Markets / Customers</th></tr>
  </thead>
  <tbody>
    <!-- Multi-segment breakdown rows -->
  </tbody>
</table>
</div>

<h3>2.2 Unit Economics, Backlog (RPO) &amp; Net Retention</h3>
<p>Granular analysis of Annual Recurring Revenue (ARR), Remaining Performance Obligations (RPO backlog), Net Revenue Retention (NRR %), Customer Acquisition Cost (CAC) payback periods, and Rule of 40 score (Revenue Growth % + Free Cash Flow Margin %).</p>

<h3>2.3 Supply Chain Architecture &amp; Cost Structure</h3>
<p>Deep analysis of hyperscaler infrastructure dependencies (AWS, Azure, GCP), semiconductor foundry capacity allocations (TSMC, Intel IFS), gross margin drivers, and contractual pricing leverage.</p>
<!-- /MARKET -->

<!-- SECTION 3: SECTOR OPERATING DYNAMICS -->
<h2 id="sector-dynamics">3. Sector-Specific Operating Dynamics</h2>
<!-- MARKET IN -->
<p>Application of the specific operational framework matching the company's sector.</p>
<!-- /MARKET -->
<!-- MARKET US -->
<p>Rigorous application of the sector operational framework matching the company's industry (e.g. Enterprise Cloud &amp; SaaS subscription dynamics, Semiconductor silicon cycles, Digital Platform network effects, Defense procurement cycles).</p>
<!-- /MARKET -->

<!-- SECTION 4: FINANCIAL AUDIT & MULTI-YEAR WIKITABLES -->
<h2 id="financial-audit">4. Financial Performance &amp; Forensic Audit</h2>
<!-- MARKET US -->
<p>Forensic examination of 5-year audited GAAP financial records, operating leverage trends, free cash flow generation, and stock-based compensation dilution discipline.</p>

<h3>4.1 Five-Year GAAP Income Statement</h3>
<div class="table-wrapper">
<!-- /MARKET -->
<table class="wikitable">
<!-- MARKET IN -->
  <!-- Multi-year P&L, Gross Margin, EBITDA Margin, PAT, EPS -->
<!-- /MARKET -->
<!-- MARKET US -->
  <thead>
    <tr><th>Metric ($ Millions)</th><th>FY2022</th><th>FY2023</th><th>FY2024</th><th>FY2025</th><th>TTM</th><th>3Y CAGR / Trend</th></tr>
  </thead>
  <tbody>
    <tr><td>Total Revenue</td><td class="num">$--</td><td class="num">$--</td><td class="num">$--</td><td class="num">$--</td><td class="num">$--</td><td class="num">--%</td></tr>
    <tr><td>Cost of Goods Sold (COGS)</td><td class="num">$--</td><td class="num">$--</td><td class="num">$--</td><td class="num">$--</td><td class="num">$--</td><td class="num">--%</td></tr>
    <tr><td>Gross Profit</td><td class="num">$--</td><td class="num">$--</td><td class="num">$--</td><td class="num">$--</td><td class="num">$--</td><td class="num">--%</td></tr>
    <tr><td>Gross Margin (%)</td><td class="num">--%</td><td class="num">--%</td><td class="num">--%</td><td class="num">--%</td><td class="num">--%</td><td class="num">-- bps</td></tr>
    <tr><td>R&amp;D Expenses</td><td class="num">$--</td><td class="num">$--</td><td class="num">$--</td><td class="num">$--</td><td class="num">$--</td><td class="num">--%</td></tr>
    <tr><td>SG&amp;A Expenses</td><td class="num">$--</td><td class="num">$--</td><td class="num">$--</td><td class="num">$--</td><td class="num">$--</td><td class="num">--%</td></tr>
    <tr><td>Operating Income (GAAP)</td><td class="num">$--</td><td class="num">$--</td><td class="num">$--</td><td class="num">$--</td><td class="num">$--</td><td class="num">--%</td></tr>
    <tr><td>Operating Margin (OPM %)</td><td class="num">--%</td><td class="num">--%</td><td class="num">--%</td><td class="num">--%</td><td class="num">--%</td><td class="num">-- bps</td></tr>
    <tr><td>Net Income (GAAP)</td><td class="num">$--</td><td class="num">$--</td><td class="num">$--</td><td class="num">$--</td><td class="num">$--</td><td class="num">--%</td></tr>
    <tr><td>Diluted GAAP EPS ($)</td><td class="num">$--</td><td class="num">$--</td><td class="num">$--</td><td class="num">$--</td><td class="num">$--</td><td class="num">--%</td></tr>
  </tbody>
<!-- /MARKET -->
</table>
<!-- MARKET US -->
</div>

<h3>4.2 Five-Year Balance Sheet &amp; Capital Structure</h3>
<div class="table-wrapper">
<!-- /MARKET -->
<table class="wikitable">
<!-- MARKET IN -->
  <!-- Cash Flow Reconciliation: PAT vs CFO, Working Capital, FCF -->
<!-- /MARKET -->
<!-- MARKET US -->
  <thead>
    <tr><th>Balance Sheet Line ($ Millions)</th><th>FY2022</th><th>FY2023</th><th>FY2024</th><th>FY2025</th><th>Latest</th></tr>
  </thead>
  <tbody>
    <tr><td>Cash, Cash Equivalents &amp; Marketable Securities</td><td class="num">$--</td><td class="num">$--</td><td class="num">$--</td><td class="num">$--</td><td class="num">$--</td></tr>
    <tr><td>Total Debt (Short + Long-Term Borrowings)</td><td class="num">$--</td><td class="num">$--</td><td class="num">$--</td><td class="num">$--</td><td class="num">$--</td></tr>
    <tr><td>Net Cash / (Net Debt)</td><td class="num">$--</td><td class="num">$--</td><td class="num">$--</td><td class="num">$--</td><td class="num">$--</td></tr>
    <tr><td>Net Debt-to-EBITDA</td><td class="num">--x</td><td class="num">--x</td><td class="num">--x</td><td class="num">--x</td><td class="num">--x</td></tr>
    <tr><td>Stockholders' Equity</td><td class="num">$--</td><td class="num">$--</td><td class="num">$--</td><td class="num">$--</td><td class="num">$--</td></tr>
    <tr><td>Return on Invested Capital (ROIC %)</td><td class="num">--%</td><td class="num">--%</td><td class="num">--%</td><td class="num">--%</td><td class="num">--%</td></tr>
    <tr><td>Return on Equity (ROE %)</td><td class="num">--%</td><td class="num">--%</td><td class="num">--%</td><td class="num">--%</td><td class="num">--%</td></tr>
  </tbody>
<!-- /MARKET -->
</table>
<!-- MARKET US -->
</div>

<h3>4.3 Five-Year Cash Flow, FCF &amp; SBC Dilution Forensics</h3>
<div class="table-wrapper">
<!-- /MARKET -->
<table class="wikitable">
<!-- MARKET IN -->
  <!-- Balance Sheet: Debt, Cash Reserves, Net D/E, ROCE, ROE -->
<!-- /MARKET -->
<!-- MARKET US -->
  <thead>
    <tr><th>Cash Flow Metric ($ Millions)</th><th>FY2022</th><th>FY2023</th><th>FY2024</th><th>FY2025</th><th>3Y Cumulative</th></tr>
  </thead>
  <tbody>
    <tr><td>Cash Flow from Operations (CFO)</td><td class="num">$--</td><td class="num">$--</td><td class="num">$--</td><td class="num">$--</td><td class="num">$--</td></tr>
    <tr><td>Capital Expenditures (Capex)</td><td class="num">$--</td><td class="num">$--</td><td class="num">$--</td><td class="num">$--</td><td class="num">$--</td></tr>
    <tr><td>Free Cash Flow (FCF = CFO - Capex)</td><td class="num">$--</td><td class="num">$--</td><td class="num">$--</td><td class="num">$--</td><td class="num"><strong>$--</strong></td></tr>
    <tr><td>FCF Margin (%)</td><td class="num">--%</td><td class="num">--%</td><td class="num">--%</td><td class="num">--%</td><td class="num">--%</td></tr>
    <tr><td>Stock-Based Compensation (SBC)</td><td class="num">$--</td><td class="num">$--</td><td class="num">$--</td><td class="num">$--</td><td class="num">$--</td></tr>
    <tr><td>SBC as % of Revenue</td><td class="num">--%</td><td class="num">--%</td><td class="num">--%</td><td class="num">--%</td><td class="num"><strong>--%</strong></td></tr>
    <tr><td>Adjusted FCF (FCF - SBC)</td><td class="num">$--</td><td class="num">$--</td><td class="num">$--</td><td class="num">$--</td><td class="num">$--</td></tr>
  </tbody>
<!-- /MARKET -->
</table>
<!-- MARKET US -->
</div>
<!-- /MARKET -->

<!-- SECTION 5: 3-LAYER UNDERWRITING FRAMEWORK -->
<h2 id="underwriting-framework">5. The 3-Layer Underwriting Framework &amp; Scorecard</h2>
<!-- MARKET US -->

<!-- /MARKET -->
<h3>5.1 Layer 1: Binary Hard Gating Floors</h3>
<!-- MARKET US -->
<div class="table-wrapper">
<!-- /MARKET -->
<table class="wikitable">
<!-- MARKET IN -->
  <tr><th>Gating Floor</th><th>Hurdle Requirement</th><th>Verified Value</th><th>Status</th></tr>
  <tr><td>Financial Quality</td><td>ROCE ≥ 15%, D/E < 0.70, CFO/PAT ≥ 0.70</td><td>ROCE: {{ROCE}}%, D/E: {{DE}}, CFO/PAT: {{CFOPAT}}</td><td>{{STATUS}}</td></tr>
  <tr><td>Technical Posture</td><td>Stage 2 Markup above 50/200 DMA</td><td>Stage {{STAGE}}, 50-DMA: ₹{{DMA50}}</td><td>{{STATUS}}</td></tr>
  <tr><td>Reward/Risk Asymmetry</td><td>Asymmetry Ratio ≥ 3.5:1 (Core ≥ 3.0:1)</td><td>{{ASYM}}:1 (Anchored Target)</td><td>{{STATUS}}</td></tr>
<!-- /MARKET -->
<!-- MARKET US -->
  <thead>
    <tr><th>Gating Floor</th><th>Hurdle Requirement</th><th>Verified Company Metric</th><th>Gate Status</th><th>Forensic Audit Note</th></tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>1. Financial Health Floor</strong></td>
      <td>ROIC ≥ 12.0%, FCF Margin ≥ 12.0%, Net Debt/EBITDA &lt; 3.0x, SBC &lt; 5.0% Rev</td>
      <td>ROIC: {{ROIC}}%, FCF Margin: {{FCF_MARGIN}}%, Net Debt/EBITDA: {{NET_DEBT_EBITDA}}x, SBC: {{SBC_REV}}%</td>
      <td><span class="pill pill-pass">PASS_FINANCIAL</span></td>
      <td>Audited SEC 10-K financial statement reconciliation</td>
    </tr>
    <tr>
      <td><strong>2. Technical Posture Floor</strong></td>
      <td>Stage 2 Markup above rising 50/200 DMA, No Stage 4 distribution</td>
      <td>Weinstein Stage {{STAGE}}, 50-DMA: ${{DMA50}}, 200-DMA: ${{DMA200}}</td>
      <td><span class="pill pill-pass">PASS_TECHNICAL</span></td>
      <td>Verified moving average alignment and accumulation volume</td>
    </tr>
    <tr>
      <td><strong>3. Asymmetry &amp; Valuation Floor</strong></td>
      <td>Reward/Risk Ratio ≥ 3.5:1 (Core ≥ 3.0:1), Anchored Target</td>
      <td>Asymmetry: <strong>{{ASYM}}:1</strong> (Target: ${{TARGET_BASE}} vs Stop: ${{STOP_LOSS}})</td>
      <td><span class="pill pill-pass">PASS_ASYMMETRY</span></td>
      <td>Target mathematically anchored to Forward EPS × 3Y Median P/E or DCF</td>
    </tr>
  </tbody>
<!-- /MARKET -->
</table>
<!-- MARKET US -->
</div>
<!-- /MARKET -->

<h3>5.2 Layer 2: Company-Specific Operational KPI Scorecard</h3>
<!-- MARKET US -->
<div class="table-wrapper">
<!-- /MARKET -->
<table class="wikitable">
<!-- MARKET IN -->
  <tr><th>Key Performance Indicator</th><th>Historical Baseline</th><th>Current Value</th><th>Hurdle Target</th><th>Status</th><th>Thesis &amp; Capital Implication</th></tr>
  <!-- 3 to 5 operational KPIs -->
<!-- /MARKET -->
<!-- MARKET US -->
  <thead>
    <tr><th>Key Performance Indicator</th><th>Historical Baseline</th><th>Current Verified Value</th><th>Hurdle Threshold</th><th>KPI Status</th><th>Investment Thesis Implication</th></tr>
  </thead>
  <tbody>
    <!-- 3 to 5 operational KPIs -->
  </tbody>
<!-- /MARKET -->
</table>
<!-- MARKET US -->
</div>
<!-- /MARKET -->

<h3>5.3 Layer 3: Support-Aware Entry Posture</h3>
<!-- MARKET US -->
<div class="table-wrapper">
<!-- /MARKET -->
<table class="wikitable">
<!-- MARKET IN -->
  <tr><th>Nearest Verified Support</th><th>Current Distance in ATR(14)</th><th>Entry Posture Classification</th><th>Execution Rule</th></tr>
  <tr><td>₹{{SUPPORT_LEVEL}}</td><td>{{ATR_DIST}} × ATR</td><td><strong>{{ENTRY_POSTURE}}</strong></td><td>{{EXECUTION_RULE}}</td></tr>
<!-- /MARKET -->
<!-- MARKET US -->
  <thead>
    <tr><th>Nearest Verified Support Anchor</th><th>Current Distance in ATR(14)</th><th>Entry Posture Classification</th><th>Execution Rule</th></tr>
  </thead>
  <tbody>
    <tr>
      <td>${{SUPPORT_LEVEL}} ({{SUPPORT_TYPE}})</td>
      <td>{{ATR_DIST}} × ATR (${{ATR_VALUE}})</td>
      <td><span class="badge badge-blue">{{ENTRY_POSTURE}}</span></td>
      <td>{{EXECUTION_RULE}}</td>
    </tr>
  </tbody>
<!-- /MARKET -->
</table>
<!-- MARKET US -->
</div>
<!-- /MARKET -->

<!-- SECTION 6: PEER & COMPETITIVE COMPARISON -->
<h2 id="peer-matrix">6. Industry Landscape &amp; Peer Comparison Table</h2>
<!-- MARKET US -->
<p>Comparative valuation, operational efficiency, and capital return benchmarking against direct listed US and global peers.</p>
<div class="table-wrapper">
<!-- /MARKET -->
<table class="wikitable">
  <thead>
<!-- MARKET IN -->
    <tr><th>Symbol</th><th>Company Name</th><th>M-Cap (₹ Cr)</th><th>CMP (₹)</th><th>ROCE %</th><th>ROE %</th><th>D/E</th><th>P/E</th><th>3Y Sales CAGR</th><th>OPM %</th><th>Moat &amp; Edge</th><th>Screening Verdict</th></tr>
<!-- /MARKET -->
<!-- MARKET US -->
    <tr><th>Ticker</th><th>Company Name</th><th>Market Cap ($B)</th><th>CMP ($)</th><th>ROIC (%)</th><th>Gross Margin (%)</th><th>EV / Sales (TTM)</th><th>Forward P/E</th><th>3Y Rev CAGR (%)</th><th>Moat &amp; Strategic Edge</th><th>Watchlist Verdict</th></tr>
<!-- /MARKET -->
  </thead>
  <tbody>
<!-- MARKET IN -->
    <!-- Subject Candidate + 2 to 3 Peers with QUALIFIED_FOR_WATCHLIST or REJECTED -->
<!-- /MARKET -->
<!-- MARKET US -->
    <!-- Subject Candidate + 3 to 5 Peers -->
<!-- /MARKET -->
  </tbody>
</table>
<!-- MARKET US -->
</div>
<!-- /MARKET -->

<!-- SECTION 7: TECHNICAL POSTURE & TRADE ARCHITECTURE -->
<h2 id="technical-trade">7. Technical Structure, Support Anchor &amp; Trade Architecture</h2>
<!-- MARKET IN -->
<ul>
  <li><strong>Weinstein Stage:</strong> Stage {{STAGE}}</li>
  <li><strong>Moving Average Alignment:</strong> CMP vs 20-DMA (₹{{DMA20}}), 50-DMA (₹{{DMA50}}), 200-DMA (₹{{DMA200}})</li>
  <li><strong>14-Day RSI &amp; RS Rating:</strong> RSI {{RSI}} &bull; RS Rating {{RS}}/100 vs Nifty 500</li>
  <li><strong>Optimal Entry Zone:</strong> ₹{{ENTRY_LOW}} – ₹{{ENTRY_HIGH}}</li>
  <li><strong>Hard Invalidation Stop:</strong> ₹{{STOP_LOSS}} (-{{STOP_PCT}}%)</li>
  <li><strong>12–18 Month Target (Base):</strong> ₹{{TARGET_BASE}} (+{{BASE_PCT}}%) [Anchored to Forward EPS × 3Y Median P/E]</li>
  <li><strong>Blue-Sky Catalyst Target (Bull):</strong> ₹{{TARGET_BULL}} (+{{BULL_PCT}}%)</li>
  <li><strong>Reward-to-Risk Asymmetry:</strong> <strong>{{ASYM}}:1</strong></li>
</ul>
<!-- /MARKET -->
<!-- MARKET US -->
<p>Multi-timeframe technical posture audit, moving average alignment, volume accumulation footprint, and actionable price levels.</p>

<div class="decision-grid" style="margin: 1.4em 0;">
  <div class="decision-card">
    <div class="decision-card-label">Weinstein Stage &amp; RS Rating</div>
    <div class="decision-card-value">Stage {{STAGE}} &bull; RS {{RS}}/100</div>
    <div class="decision-card-sub">14-Day RSI: {{RSI}} (Momentum Regime)</div>
  </div>
  <div class="decision-card">
    <div class="decision-card-label">Moving Average Stack</div>
    <div class="decision-card-value">20D: ${{DMA20}} | 50D: ${{DMA50}}</div>
    <div class="decision-card-sub">200-DMA: ${{DMA200}} (Uptrend Anchor)</div>
  </div>
  <div class="decision-card">
    <div class="decision-card-label">Optimal Entry Zone</div>
    <div class="decision-card-value">${{ENTRY_LOW}} – ${{ENTRY_HIGH}}</div>
    <div class="decision-card-sub">Support: ${{SUPPORT_LEVEL}} ({{ATR_DIST}}x ATR)</div>
  </div>
  <div class="decision-card">
    <div class="decision-card-label">Invalidation Stop &amp; Targets</div>
    <div class="decision-card-value">Stop: ${{STOP_LOSS}} | Target: ${{TARGET_BASE}}</div>
    <div class="decision-card-sub">Bull Target: ${{TARGET_BULL}} (Asymmetry {{ASYM}}:1)</div>
  </div>
</div>
<!-- /MARKET -->

<!-- SECTION 8: FATAL FLAWS & RED-TEAM -->
<h2 id="fatal-flaws">8. Adversarial Red-Team: 3 Fatal Flaws &amp; Invalidation Triggers</h2>
<!-- MARKET IN -->
<ol>
  <li><strong>Fatal Flaw 1 (Valuation / Margin Peak Risk):</strong> ...</li>
  <li><strong>Fatal Flaw 2 (Working Capital / Cash Drag Risk):</strong> ...</li>
  <li><strong>Fatal Flaw 3 (Structural / Competitive Vulnerability):</strong> ...</li>
</ol>
<div class="forensic-box">
<!-- /MARKET -->
<!-- MARKET US -->
<p>Independent adversarial investigation into potential structural risks, customer concentration, hyperscaler capex cyclicality, and competitive moat erosion.</p>

<div class="table-wrapper">
<table class="wikitable">
  <thead>
    <tr><th>Risk Dimension</th><th>Specific Fatal Flaw Scenario</th><th>Probability / Impact</th><th>Mitigation / Moat Defense</th><th>Hard Invalidation Trigger</th></tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>1. Valuation &amp; Multiple Compression</strong></td>
      <td>Detailed multiple derating scenario in a rising yield or slowing growth environment.</td>
      <td>Medium / High</td>
      <td>High FCF conversion and ongoing share buyback support.</td>
      <td>Quarterly revenue growth decelerating below 15%.</td>
    </tr>
    <tr>
      <td><strong>2. Dilution &amp; SBC Cash Drag</strong></td>
      <td>Excessive stock-based compensation masking actual cash generation.</td>
      <td>Low / Medium</td>
      <td>Discipline in GAAP operating margin expansion and net dilution < 1%.</td>
      <td>SBC expanding above 8.0% of revenue.</td>
    </tr>
    <tr>
      <td><strong>3. Structural / Competitive Threat</strong></td>
      <td>Hyperscaler in-house silicon or rival platform disintermediation.</td>
      <td>Low / High</td>
      <td>Proprietary software ecosystem, high developer switching costs, and IP fortress.</td>
      <td>Loss of top-tier cloud partner or core architecture shift.</td>
    </tr>
  </tbody>
</table>
</div>

<div class="flaw-box">
<!-- /MARKET -->
  <strong>Hard Invalidation Triggers:</strong>
  <ul>
<!-- MARKET IN -->
    <li>Fundamental: Quarterly OPM compression > 300 bps or CFO/PAT < 0.50.</li>
    <li>Technical: Daily close below invalidation stop ₹{{STOP_LOSS}} on heavy volume.</li>
<!-- /MARKET -->
<!-- MARKET US -->
    <li>Fundamental: Quarterly Gross Margin contraction &gt; 300 bps or cumulative Adjusted FCF turning negative.</li>
    <li>Technical: Daily close below invalidation stop ${{STOP_LOSS}} on expanding volume.</li>
<!-- /MARKET -->
  </ul>
</div>

<!-- SECTION 9: CAPITAL ALLOCATION & REPLACEMENT -->
<h2 id="capital-allocation">9. Portfolio Allocation &amp; Replacement Guidance</h2>
<!-- MARKET IN -->
<p>Specific guidance on sizing, capital source, or replacement swap.</p>
<!-- /MARKET -->
<!-- MARKET US -->
<p>
  Concrete capital deployment sizing, conviction tiering (Tier 1: 7–10%, Tier 2: 4–6.5%, Tier 3: 2–3.5%), execution staging (e.g. 50% initial tranche at support, 50% on breakout confirmation), and incumbent displacement matchup.
</p>
<!-- /MARKET -->

<!-- SECTION 10: QUARTERLY MONITORING INDICATORS -->
<h2 id="thesis-trackers">10. Key Quarterly Monitoring Indicators (Thesis Trackers)</h2>
<!-- MARKET US -->
<div class="table-wrapper">
<!-- /MARKET -->
<table class="wikitable">
<!-- MARKET IN -->
  <tr><th>Monitoring Indicator</th><th>Analytical Significance</th><th>Bullish Threshold</th><th>Bearish Alert Level</th></tr>
  <!-- Exactly 3 quarterly trackers -->
<!-- /MARKET -->
<!-- MARKET US -->
  <thead>
    <tr><th>Quarterly Monitoring Indicator</th><th>Analytical Significance</th><th>Bullish Expansion Threshold</th><th>Bearish Alert / Exit Level</th></tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>1. RPO Backlog &amp; ARR Growth</strong></td>
      <td>Measures forward revenue visibility and enterprise deal momentum.</td>
      <td>RPO growth &gt; --% YoY, ARR net new adds &gt; $-- M/qtr</td>
      <td>RPO growth decelerating below --% YoY</td>
    </tr>
    <tr>
      <td><strong>2. Non-GAAP &amp; GAAP Gross Margin</strong></td>
      <td>Reflects pricing power and cloud/foundry infrastructure efficiency.</td>
      <td>Gross Margin sustained &gt; --%</td>
      <td>Gross Margin dropping below --%</td>
    </tr>
    <tr>
      <td><strong>3. FCF Conversion &amp; SBC Dilution</strong></td>
      <td>Verifies true shareholder cash return and capital discipline.</td>
      <td>FCF Margin &gt; 25%, SBC % of Rev &lt; 4.0%</td>
      <td>SBC % of Rev expanding &gt; 7.0%, FCF Margin &lt; 15%</td>
    </tr>
  </tbody>
<!-- /MARKET -->
</table>
<!-- MARKET US -->
</div>
<!-- /MARKET -->

<!-- SECTION 11: REFERENCES & CITATIONS -->
<!-- MARKET IN -->
<h2 id="references">11. References, Regulatory Filings &amp; External Links</h2>
<!-- /MARKET -->
<!-- MARKET US -->
<h2 id="references">11. References, SEC Filings &amp; External Links</h2>
<!-- /MARKET -->
<ol class="reflist">
<!-- MARKET IN -->
  <li id="cite_note-1">^ BSE/NSE Exchange Disclosure: Audited Financial Results for FY 2026.</li>
  <li id="cite_note-2">^ Annual Report FY 2026 &bull; Director's Report &amp; Management Discussion and Analysis.</li>
  <li id="cite_note-3">^ Screener.in Consolidated Company Financials: <a href="https://www.screener.in/company/{{SYMBOL}}/" target="_blank">screener.in/company/{{SYMBOL}}/</a></li>
  <li id="cite_note-4">^ TradingView Interactive Technical Chart: <a href="https://www.tradingview.com/chart/?symbol=NSE%3A{{SYMBOL}}" target="_blank">tradingview.com/chart/?symbol=NSE%3A{{SYMBOL}}</a></li>
<!-- /MARKET -->
<!-- MARKET US -->
  <li id="cite_note-1">^ US Securities and Exchange Commission (SEC EDGAR) &bull; Form 10-K Annual Report: <a href="https://www.sec.gov/edgar/searchedgar/companysearch" target="_blank">sec.gov/edgar</a></li>
  <li id="cite_note-2">^ Finviz Financial Ratios &amp; Technical Structure: <a href="https://finviz.com/quote.ashx?t={{SYMBOL}}" target="_blank">finviz.com/quote.ashx?t={{SYMBOL}}</a></li>
  <li id="cite_note-3">^ TradingView Technical Chart &amp; Moving Averages: <a href="https://www.tradingview.com/chart/?symbol={{PRIMARY_EXCHANGE}}%3A{{SYMBOL}}" target="_blank">tradingview.com</a></li>
  <li id="cite_note-4">^ Company Investor Relations &amp; Quarterly Earnings Webcast: <a href="https://www.google.com/search?q={{COMPANY_NAME}}+investor+relations" target="_blank">Investor Relations Portal</a></li>
<!-- /MARKET -->
</ol>

<!-- MARKET US -->
</div>
<!-- /MARKET -->
</div>
</body>
</html>
```

---

## 5. Output Location & Google Drive Integration

1. **Output Path:** The research dossier MUST be written directly to `docs/blogs/<SYMBOL>_dossier.html`.
2. **In-Place Update:** If the file already exists, update it strictly in-place. Never create numbered copies like `<SYMBOL>_dossier (1).html`.
3. **No `.docx` Output:** Do not generate Word documents. The self-contained Wikipedia HTML dossier is the sole authoritative company report.
<!-- MARKET IN -->
4. **MANDATORY ONE-OFF SCRIPT LIFECYCLE & CACHE HYGIENE (NO RESIDUAL ARTIFACTS):**
<!-- /MARKET -->
<!-- MARKET US -->
4. **Mandatory Portal Rebuild:** Immediately after saving or updating any dossier, run:
   ```bash
   .venv/bin/python scripts/build_dossier_portal.py
   ```
5. **Immediate Localhost Verification:** Ensure the dossier is served immediately on **`http://localhost:9050/<SYMBOL>_dossier.html`**.
6. **MANDATORY ONE-OFF SCRIPT LIFECYCLE & CACHE HYGIENE (NO RESIDUAL ARTIFACTS):**
<!-- /MARKET -->
   - Scratch code lives only in `<RUN_DIR>` and is deleted with it (RUN_PROTOCOL sections 1 and 5).
   - **Run directory:** nothing from earlier runs is read. Cleanup follows `../_shared/RUN_PROTOCOL.md` section 5. Repository scripts are never deleted.
   - **Permanent repository scripts (never delete or modify without the user):** `scripts/send_email.py`, `scripts/build_dossier_portal.py`, `scripts/serve_blogs.py`, `scripts/market_facts.py`, `scripts/validate_report.py`.
<!-- MARKET IN -->
   - **Pre-termination verification:** run `ls scripts/` and confirm ONLY whitelisted files remain. Leaving one-off generator scripts behind is a pipeline failure.
<!-- /MARKET -->
<!-- MARKET US -->
   - **Pre-termination verification:** run `ls scripts/` and confirm ONLY whitelisted files remain.
<!-- /MARKET -->
