---
name: market_intelligence
description: >-
  Institutional daily market intelligence newsletter, derivatives radar, and watchlist ingestion engine
  for Indian equity markets (NSE/BSE). Generates a comprehensive, encyclopedic briefing formatted in
  Wikipedia design system (infobox internals, wikitables, serif headers, footnotes, NPOV tone) covering
  benchmark indices, options gamma walls, sector rotation matrix, symmetric 30 Stage 2 breakouts & 30
  Stage 4 breakdowns, smart money radar, and tactical playbook, with automated ingestion into
  watchlist/Zerodha_Watchlist.xlsx and email delivery via Gmail.
---

# Wikipedia-Style Institutional Daily Market Intelligence Newsletter Skill

Act as a **Senior Institutional Equity Research Analyst**, **Derivatives Strategist**, and **Wikipedia Financial Editor** covering Indian Equity Markets (NSE/BSE).

Execute the **Daily Market Intelligence & Watchlist Ingestion Engine**:
1. Generate an exhaustive daily market intelligence briefing formatted in authentic **Wikipedia Design System** (NPOV encyclopedic tone, floating infobox, wikitables, footnotes, verified citations).
2. Maintain and synchronize the deliverable in Google Drive at **`googledrive/newsletters/Daily_Market_Intelligence_<YYYY-MM-DD>.html`** (maintaining **strictly only the single latest generated report showing the run date on the page**, and automatically deleting all prior versions).
3. Transmit the complete deliverable via Gmail to **`rajasekharreddymekala732@gmail.com`**.
4. Synchronize and maintain **`watchlist/Zerodha_Watchlist.xlsx`** (feeding the top 1–3 standout setups of the day directly into the top of the deep research funnel).

The tone is **neutral (Wikipedia NPOV) and explanatory**. Follow `../_shared/REPORT_VOICE.md`: explain every heading in plain English, give the reasoning and the consequence for every number, name the rule behind every verdict, and tie each section forward to the next. No promotional slang, no template phrases.

---

### EDITORIAL, DATA-COMPLETENESS & COHERENCE STANDARD (MANDATORY — READ FIRST):

Before anything else, read `.agents/skills/_shared/REPORT_EDITORIAL_STANDARD.md` in full; it is binding and overrides any terser skeleton text below. Non-negotiables:

1. **Data first:** run `python3 scripts/market_facts.py --market IN --date <session> --screen nifty500`. Every price, DMA, RSI, ATR, volume multiple, Weinstein stage, regime label, breadth figure, sector quadrant and both 30-name lists must come from `scripts/.cache/facts_IN_<date>.json`. `N/A` is a last resort after the ledger, the mandatory duck-duck-go MCP research pass (`search` + `fetch_content`, protocol in section 6 of the standard; results recorded in `scripts/.cache/research_IN_<date>.json` with source URL and as-of date) and a second source have all failed (max 5% of table cells). FII/DII flows, NSE option-chain OI/PCR, FII index futures, bulk/block deals, delivery %, results dates and catalysts come from that pass, not from memory. Use precise date-stamped queries, fetch and read the actual page (snippets are not evidence), try direct NSE archive URLs first, and cross-check headline figures with a second source. Never carry forward the previous report's names or publish a "revalidation pending" list; publish exactly `screen.bull_pick` and `screen.bear_pick` (10 per cap tier, company names and sectors from the pick rows, `qualifier` shown and explained).
2. **Write it as a book for a beginner (section 3 and blueprint 7A of the standard):** append `.agents/skills/_shared/book_components.css` to the report's `<style>`; open with a 450+ word `primer` ("Start here": every key idea with an everyday analogy), then a 250-400 word lede; every section opens with a 200+ word essay and closes with a "what this means for you" paragraph; every table has a `howto` block before it (read one real row aloud) and a 120+ word `takeaway` after it; `casenote` stories (80+ words: what the company does, the numbers and what they mean, the verdict and the exact rule behind it, what would change it, with prices) for the Top 3 setups, three spotlights per list and each leading/lagging sector; at least one worked `example` with rupee arithmetic; a `triggers` if/then block per section; a glossary and a methodology/data-gaps note. Target 12,000+ words; the validator floor is 9,000. Never leave a number unexplained.
3. **One story:** one regime label (ledger `regime.label`) used verbatim in the infobox, Section 1 and Section 6; the Bull List is drawn from leading sectors and the Bear List from lagging ones (exceptions named); the Section 6 Top 3 come only from Section 3 and are sized by the regime table; Section 7 ingests only those names. Read the same-date `Portfolio_Audit_*.html` first and reconcile every shared ticker's price and stage.
4. **Gate:** `python3 scripts/validate_report.py --report googledrive/newsletters/Daily_Market_Intelligence_<date>.html --kind market_intel --facts scripts/.cache/facts_IN_<date>.json` must print `PASS` before the Drive save and email. The HTML skeleton below is table scaffolding only: every `{{NARRATIVE_*}}` slot, plus an intro `<p>` before and a takeaway `<p>` after every table, must be written as full prose.

---

### MANDATORY ZERO-HALLUCINATION & DATA ACCURACY RULES:

1. **NO HALLUCINATIONS:** Strictly base all technical levels, market prices, moving averages, RSI values, volume multiples, derivative metrics (OI, PCR, VIX, FII flows), and corporate catalysts on verified market closing data and exchange disclosures.
2. **MANDATORY USE OF `N/A` (NO GUESSING / NO FABRICATION):** If any specific metric (e.g., historical delivery volume, promoter pledge, or consensus broker target) is not deterministically verified, output **`N/A`** with a specific reason rather than fabricating or estimating numbers. `N/A` is allowed only after `scripts/market_facts.py`, an alternate source and web search have all failed; it must never stand in for data that price history can supply (returns, DMAs, RSI, ATR, volume multiple, stage).
3. **AUTHORITATIVE 2-TIER MASTER TAXONOMY:** Classify and group all sector heatmap movers, momentum themes, and stock lists according to the **Embedded 2-Tier Master Taxonomy** (*Macro Sector Group* / *Fine-Grained Subsector*).
4. **MANDATORY TRADINGVIEW & SCREENER NAVIGATION LINKS:**
   - For every security referenced in the report, provide direct clickable links:
     - **TradingView Chart:** `https://www.tradingview.com/chart/?symbol=NSE%3A{SYMBOL}`
     - **Screener.in Financials:** `https://www.screener.in/company/{SYMBOL}/`
   - In all data tables, format the Symbol column with clickable sub-links:
     `<b>{SYMBOL}</b><br><span style="font-size: 11px;"><a href="https://www.tradingview.com/chart/?symbol=NSE%3A{SYMBOL}" style="color: #1d4ed8;">Chart</a> • <a href="https://www.screener.in/company/{SYMBOL}/" style="color: #006600;">Screener</a></span>`
5. **MANDATORY ZERO-OMISSION REPORT INTEGRITY (NO SECTIONS SKIPPED IN EMAIL NEWSLETTER):**
   - Every single section (Sections 1 through 7) and every table must be 100% fully rendered.
   - Strictly forbidden: Truncating sections, omitting tables, using placeholder comments (e.g. `<!-- rest of table omitted -->`, `[Remaining setups continue...]`), or skipping any breakout/breakdown candidates or sector heatmaps.
   - The full 30 breakout alerts and 30 breakdown alerts, all sector movers, and top tactical setups must be completely populated.
6. **MANDATORY INDEPENDENT REVIEWER AGENT & EXTENSIVE DUCK-DUCK-GO MCP WEB VERIFICATION:**
   - Double-check all closing prices (CMP), 52-week ranges, moving averages, 14-day RSI, volume expansion multiples, PCR, India VIX, and FII/DII net flows via live online search (the `duck-duck-go` MCP `search` then `fetch_content`, per section 6 of `.agents/skills/_shared/REPORT_EDITORIAL_STANDARD.md`).
7. **MANDATORY GOOGLE DRIVE SYNCHRONIZATION, REPORT LIFECYCLE & IN-PLACE OVERWRITE:**
   - Ingest `sheets/Zerodha_Holdings.xlsx` and `shortlist/Zerodha_Shortlist.xlsx` fresh from Google Drive.
   - Modify and persist `watchlist/Zerodha_Watchlist.xlsx` strictly IN-PLACE.
   - **Single Latest Report Maintenance in Google Drive:** Save the generated HTML briefing to `googledrive/newsletters/Daily_Market_Intelligence_<YYYY-MM-DD>.html`. The document title, page header, and infobox must clearly display the session date (`YYYY-MM-DD`). Automatically scan `googledrive/newsletters/` and delete all previous `Daily_Market_Intelligence_*.html` files before/upon writing the new one, ensuring Google Drive holds strictly only the single latest generated report.
8. **MANDATORY AUTOMATED EMAIL DISPATCH (NO MANUAL CONFIRMATION / NO BLOCKED POLICY):**
   - Automated email dispatch of the generated newsletter to `rajasekharreddymekala732@gmail.com` via `scripts/send_email.py` is a **STRICT, MANDATORY PIPELINE REQUIREMENT** for every run.
   - You MUST programmatically run the `send_email.py` command in the terminal as the final automated step.
   - NEVER skip email dispatch, NEVER prompt the user asking for manual sending permission, and NEVER report that automated email is blocked by security policy. The workspace environment explicitly pre-authorizes programmatic email dispatch via `scripts/send_email.py`.
9. **MANDATORY ONE-OFF SCRIPT LIFECYCLE & CACHE HYGIENE (NO RESIDUAL ARTIFACTS):**
   - Any one-off execution scripts created during this run (e.g., `generate_*.py`, `build_*_dossiers*.py`, `expand_*.py`, `update_*_workbooks.py`, `update_*_watchlist*.py`) are **transient pipeline artifacts**. IMMEDIATELY after the pipeline completes successfully (HTML written, workbooks updated, portal rebuilt, email dispatched), you MUST delete them in the terminal as the final step: `rm scripts/<one-off-script>.py`, and also remove any `scripts/__pycache__/` directory created during the run.
   - **Zero Prior-Session Bias & Cache Cleanup**: Stale cache artifacts from prior session dates in `scripts/.cache/` (e.g. `facts_*`, `research_*`, `audit_*`, `screen_*`) must be pruned. Every run starts from a clean, unbiased baseline. Only persistent configuration (`scripts/.cache/aliases.json`) is preserved across sessions.
   - **PERMANENT INFRASTRUCTURE WHITELIST (NEVER DELETE):** `scripts/send_email.py`, `scripts/build_dossier_portal.py`, `scripts/serve_blogs.py`, `scripts/dossier_builder_template.py`, `scripts/com.portfolio.blogs.fileserver.plist`, `googledrive/blogs/dossier_nav.js`, `googledrive/blogs/dossiers.json`, `scripts/market_facts.py`, `scripts/validate_report.py`, `scripts/.cache/aliases.json`.
   - **Pre-termination verification:** run `ls scripts/` and confirm ONLY whitelisted files remain. Leaving one-off generator/update scripts behind is a pipeline failure.

---

### DECOUPLED SPECIALIST SUBAGENT WORKFLOW (ELIMINATING DIRECTIONAL BIAS & CONTEXT FATIGUE):

To eliminate directional bias and context exhaustion, the newsletter is synthesized by 4 independent specialist subagents and 1 master editor:

#### 1. Specialist 1: `macro_derivatives_strategist` (Macro Regime, Gamma Walls & Sector Rotation)
- **Focus:** Nifty 50, Bank Nifty, India VIX, FII/DII Net Cash, FII Index Futures Long/Short Ratio, Options Open Interest Clusters (Call/Put Walls, Max Pain, PCR), and 4-Quadrant Sector Rotation Matrix.
- **Protocol:** Uses web search to retrieve Bhavcopy, NSE derivatives open interest stats, India VIX closing levels, and sector index performances.

#### 2. Specialist 2: `bull_momentum_desk` (Long Stage 2 Breakout Screener)
- **Focus:** Long momentum universe (Exactly 30 Verified Setups: 10 Large-Cap >₹50,000 Cr, 10 Mid-Cap ₹15,000–50,000 Cr, 10 Small/Micro-Cap ₹500–15,000 Cr).
- **Hurdles:** Weinstein Stage 2 markup, Price > 50-DMA > 200-DMA, volume expansion ≥ 1.5x 20-DMA volume, 14-day RSI 55–72, reward/risk asymmetry ≥ 3.5:1.

#### 3. Specialist 3: `bear_distribution_desk` (Short & Distribution Risk Screener)
- **Focus:** Short/Distribution universe (Exactly 30 Verified Breakdown Setups: 10 Large, 10 Mid, 10 Small).
- **Hurdles:** Weinstein Stage 4 breakdown, Price < 50-DMA < 200-DMA (or death cross), heavy distribution volume (>1.5x 20-DMA volume on down days), 14-day RSI < 45.

#### 4. Specialist 4: `smart_money_catalyst_radar` (Institutional Deals & Event Defense)
- **Focus:** BSE/NSE Bulk & Block Deals (>₹10 Cr), promoter insider open-market purchases/sales, SAST pledge disclosures, and upcoming high-impact earnings/event dates.

#### 5. Master Editor & Watchlist Ingestion Gatekeeper (`tactical_playbook_and_ingestion`)
- **Tactical Playbook (Section 6):** Selects the **Top 3 Standout Setups of the Day** (Asymmetry $\ge 3.5:1$) with exact entry bands, stops, targets, and regime-aligned portfolio allocation stance.
- **Watchlist Ingestion (Section 7):** Ingests the standout ideas into `watchlist/Zerodha_Watchlist.xlsx`.
- **Integrity Audit & Delivery:** Verifies zero omissions and dispatches the briefing via Gmail and syncs Google Drive.

---

### WIKIPEDIA VISUAL DESIGN SYSTEM FOR EMAIL & WEB:

The newsletter is rendered as a standalone, self-contained HTML document with an embedded `<style>` block matching Wikipedia's desktop/mobile aesthetic:

- **Typography & Canvas:**
  - Embed Google Fonts:
    ```html
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400;1,500&family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;0,6..72,700;1,6..72,400;1,6..72,500&family=JetBrains+Mono:ital,wght@0,400;0,500;0,600;0,700;1,400&display=swap" rel="stylesheet">
    ```
  - Headers Font Stack: `'Newsreader', Georgia, 'Times New Roman', serif;` (optical sizing 6..72, weights 500/600/700).
  - Body Font Stack: `'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;`
  - Monospace Font Stack: `'JetBrains Mono', monospace;` for stock prices, P/E ratios, tickers, and formulas.
  - Color Palette: Body text `#1f2937` (soft obsidian), background `#ffffff`, subtle borders `#d1d5db`, table header gray `#f3f4f6`, hover background `#f0f7ff`.
  - Line height: `1.72`, font size `15px`, letter spacing `-0.011em`, standard paragraph margins with justified text.
- **Wikipedia Infobox (`table.infobox`):**
  - Floated right with width `320px`, border `1px solid #d1d5db`, background `#f9fafb`.
  - Captures market internal vital statistics: Market Regime, India VIX, FII Index Futures Long/Short Bias, Market Breadth (% > 50-DMA), Advance/Decline Ratio, Distribution Days, FII/DII Net Cash.
- **Wikitables (`table.wikitable`):**
  - Width: `100%`, border collapse: `collapse`, border: `1px solid #d1d5db`, background: `#ffffff`, font-size: `89%`.
  - Header cells `th`: `#f3f4f6`, bold, border `1px solid #d1d5db`, padding `8px 12px`.
  - Data cells `td`: padding `7px 12px`, border `1px solid #d1d5db`. Alternating rows `#fafbfc`. Hover `#f0f7ff`.
  - Numeric cells: `<td class="num">` right-aligned monospace.
  - Wrapped inside `<div class="table-wrapper">` for responsiveness.
- **Callout & Forensic Alert Boxes:**
  - Investment Callout: `class="callout-box"` (blue accent border).
  - Forensic Warning: `class="callout-warning"` (amber accent border).
  - Breakdown / Flaw Box: `class="flaw-box"` (red accent border).
- **Wikipedia Citations & Reference List (`ol.reflist`):**
  - In-text superscript tags: `<sup><a href="#cite_note-1">[1]</a></sup>`.
  - Two-column bottom reference list: `<ol class="reflist">`.

---

### NEWSLETTER STRUCTURE (SECTIONS 1 THROUGH 7):

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Indian Equity Market Intelligence &amp; Derivatives Radar — {{SESSION_DATE}}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400;1,500&family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;0,6..72,700;1,6..72,400;1,6..72,500&family=JetBrains+Mono:ital,wght@0,400;0,500;0,600;0,700;1,400&display=swap" rel="stylesheet">
<style>
:root {
  --text-primary: #1f2937;
  --text-secondary: #4b5563;
  --text-muted: #6b7280;
  --bg-main: #ffffff;
  --bg-surface: #f9fafb;
  --bg-highlight: #f3f4f6;
  --border-color: #d1d5db;
  --border-subtle: #e5e7eb;
  --brand-blue: #1d4ed8;
  --brand-blue-light: #eff6ff;
  --brand-green: #15803d;
  --brand-green-light: #f0fdf4;
  --brand-amber: #b45309;
  --brand-amber-light: #fffbeb;
  --brand-red: #b91c1c;
  --brand-red-light: #fef2f2;
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
  color: #1f2937;
  margin-top: 1.6em;
  margin-bottom: 0.5em;
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
/* WIKIPEDIA FLOATED INFOBOX */
table.infobox {
  float: right;
  clear: right;
  margin: 0.6em 0 1.4em 1.8em;
  width: 330px;
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
  width: 45%;
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
  color: #1f2937;
  border-top: 1px solid var(--border-color);
  border-bottom: 1px solid var(--border-color);
  padding: 6px 10px;
  font-size: 0.9em;
  text-transform: uppercase;
  letter-spacing: 0.04em;
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
  color: #1f2937;
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
  background-color: #fafbfc;
}
table.wikitable tr:hover td {
  background-color: #f0f7ff;
}
table.wikitable td.num, table.wikitable th.num {
  text-align: right;
  font-family: var(--font-mono);
}
/* CALLOUT BOXES */
.callout-box {
  background-color: var(--brand-blue-light);
  border-left: 5px solid var(--brand-blue);
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
.flaw-box {
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
}
.pill-pass, .badge-green { background-color: #dcfce7; color: #166534; }
.pill-watch, .badge-amber { background-color: #fef3c7; color: #92400e; }
.pill-fail, .badge-red { background-color: #fee2e2; color: #991b1b; }
.badge-blue { background-color: #dbeafe; color: #1e40af; }
/* REFERENCES */
ol.reflist {
  font-size: 0.84em;
  line-height: 1.6;
  column-count: 2;
  column-gap: 28px;
  padding-left: 20px;
  margin-top: 1.2em;
}
ol.reflist li { margin-bottom: 8px; word-break: break-word; }
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
}
</style>
</head>
<body>
<div class="main-container">

<h1 class="firstHeading">Indian Equity Market Intelligence &amp; Derivatives Radar</h1>
<div class="siteSub">From Wikipedia, the institutional financial encyclopedia &bull; Daily Session Close &bull; NSE/BSE &bull; {{SESSION_DATE}}</div>

<div class="clearfix">

<!-- WIKIPEDIA FLOATED INFOBOX: MARKET REGIME INTERNALS -->
<table class="infobox" role="presentation">
  <caption>Market Internal Vitals</caption>
  <tr><th colspan="2" class="infobox-header">Session Snapshot: {{SESSION_DATE}}</th></tr>
  <tr><th>Market Regime</th><td><strong>{{MARKET_REGIME}}</strong> (Stage 2 / Neutral / Distribution)</td></tr>
  <tr><th>India VIX</th><td>{{VIX_VALUE}} &bull; {{VIX_REGIME}}</td></tr>
  <tr><th>FII Index Futures</th><td>Long: {{FII_LONG_PCT}}% &bull; Short: {{FII_SHORT_PCT}}%</td></tr>
  <tr><th>Market Breadth</th><td>{{BREADTH_PCT}}% of Nifty 500 &gt; 50-DMA</td></tr>
  <tr><th>Advance / Decline</th><td>Advances: {{ADVANCES}} &bull; Declines: {{DECLINES}} (Ratio: {{AD_RATIO}})</td></tr>
  <tr><th>Nifty Distribution Days</th><td>{{DISTRIBUTION_DAYS}} Days</td></tr>
  <tr><th>FII / DII Net Cash</th><td>FII: ₹{{FII_NET}} Cr &bull; DII: ₹{{DII_NET}} Cr</td></tr>
</table>

<!-- SECTION 1: THE BIG PICTURE -->
<h2 id="section1">1. The Big Picture: Market Regime, Benchmarks &amp; Derivatives</h2>

<p>{{NARRATIVE_LEDE_AND_S1_OPENING}}</p><!-- lede 150+ words (verdict, 3 numbers that matter, the action, section map) then 60+ words on what section 1 measures. Every table below: intro <p> before, takeaway <p> after. -->

<h3>1.1 Benchmark Indices Performance &amp; Valuation</h3>
<div class="table-wrapper">
<table class="wikitable">
  <thead>
    <tr>
      <th>Index / Benchmark</th>
      <th class="num">Latest Close</th>
      <th>Returns (1D / 1W / 2W)</th>
      <th>Technical State</th>
      <th>Valuation &amp; Risk Context</th>
    </tr>
  </thead>
  <tbody>
    <!-- Nifty 50, Nifty Midcap 150, Nifty Smallcap 250, Nifty 500 -->
  </tbody>
</table>
</div>

<h3>1.2 Options Gamma Wall &amp; Institutional Positioning Map</h3>
<div class="table-wrapper">
<table class="wikitable">
  <thead>
    <tr>
      <th>Barrier Level</th>
      <th class="num">Strike Price</th>
      <th class="num">Open Interest (Lakhs)</th>
      <th>Institutional Significance</th>
    </tr>
  </thead>
  <tbody>
    <!-- Call Wall, Spot, Put Wall -->
  </tbody>
</table>
</div>
<p style="font-size: 90%; color: #555;">Put-Call Ratio (PCR): <strong>{{PCR_VALUE}}</strong> &bull; Options Sentiment Bias: <strong>{{OPTIONS_BIAS}}</strong></p>

<h3>1.3 Global Macro Matrix &amp; Transmission Channels</h3>
<div class="table-wrapper">
<table class="wikitable">
  <thead>
    <tr>
      <th>Global Asset</th>
      <th class="num">Latest Price</th>
      <th>Weekly Trend</th>
      <th>Domestic Sector Transmission</th>
    </tr>
  </thead>
  <tbody>
    <!-- Brent Crude, US 10Y, DXY, USD/INR -->
  </tbody>
</table>
</div>

<!-- SECTION 2: SECTOR & THEMATIC ROTATION -->
<h2 id="section2">2. Sector &amp; Thematic Rotation Matrix</h2>

<h3>2.1 4-Quadrant Sector Rotation Map</h3>
<div class="table-wrapper">
<table class="wikitable">
  <thead>
    <tr>
      <th>Quadrant</th>
      <th>Cycle Phase</th>
      <th>Active Sectors &amp; Subsectors</th>
      <th>Institutional Flow &amp; Action</th>
    </tr>
  </thead>
  <tbody>
    <!-- Leading, Improving, Weakening, Lagging -->
  </tbody>
</table>
</div>

<h3>2.2 Thematic Rotation Narratives &amp; Superior Risk-Reward Proxies</h3>
<p>{{NARRATIVE_S2_THEMES}}</p><!-- 3-4 paragraphs, one per theme: operational driver, ledger evidence, best proxy, what would invalidate it. Close with the bridge to the Bull/Bear lists. -->

<!-- SECTION 3: THE BULL LIST (30 STAGE 2 LONGS) -->
<h2 id="section3">3. The Bull List: Top 30 Stage 2 Momentum Leaders</h2>
<p>{{NARRATIVE_S3_OPENING}}</p><!-- explain Stage 2, the hurdles applied, how many names passed strictly vs 'near', which sectors dominate and why (tie to section 2). -->

<h3>3.1 Large-Cap Leaders (&gt; ₹50,000 Cr) — Exactly 10 Stocks</h3>
<div class="table-wrapper">
<table class="wikitable">
  <thead>
    <tr><th>Security &amp; Links</th><th class="num">Market Cap (₹ Cr)</th><th>Breakout Level &amp; DMAs</th><th>Volume Multiple &amp; RSI</th><th>Catalyst, Target &amp; Stop</th></tr>
  </thead>
  <tbody>
    <!-- 10 Large-cap stocks -->
  </tbody>
</table>
</div>

<h3>3.2 Mid-Cap Leaders (₹15,000 Cr to ₹50,000 Cr) — Exactly 10 Stocks</h3>
<div class="table-wrapper">
<table class="wikitable">
  <thead>
    <tr><th>Security &amp; Links</th><th class="num">Market Cap (₹ Cr)</th><th>Breakout Level &amp; DMAs</th><th>Volume Multiple &amp; RSI</th><th>Catalyst, Target &amp; Stop</th></tr>
  </thead>
  <tbody>
    <!-- 10 Mid-cap stocks -->
  </tbody>
</table>
</div>

<h3>3.3 Small-Cap &amp; Micro-Cap Leaders (₹500 Cr to ₹15,000 Cr) — Exactly 10 Stocks</h3>
<div class="table-wrapper">
<table class="wikitable">
  <thead>
    <tr><th>Security &amp; Links</th><th class="num">Market Cap (₹ Cr)</th><th>Breakout Level &amp; DMAs</th><th>Volume Multiple &amp; RSI</th><th>Catalyst, Target &amp; Stop</th></tr>
  </thead>
  <tbody>
    <!-- 10 Small-cap stocks -->
  </tbody>
</table>
</div>

<!-- SECTION 4: THE BEAR LIST (30 STAGE 4 SHORTS) -->
<h2 id="section4">4. The Bear List: Top 30 Stage 4 Breakdown Watchlist</h2>
<p>{{NARRATIVE_S4_OPENING}}</p><!-- explain Stage 4 and distribution volume, what the bear list says about the regime, overlap with book/watchlist, how to use it (avoid/trim/hedge; not a short signal by itself). -->
<div class="table-wrapper">
<table class="wikitable">
  <thead>
    <tr><th>Security &amp; Links</th><th class="num">Market Cap (₹ Cr)</th><th>Breakdown Level &amp; DMAs</th><th>Volume Multiple &amp; RSI</th><th>Distribution Risk &amp; Floor</th></tr>
  </thead>
  <tbody>
    <!-- 30 Breakdown stocks across 3 tiers -->
  </tbody>
</table>
</div>

<!-- SECTION 5: SMART MONEY RADAR -->
<h2 id="section5">5. Smart Money Radar &amp; Pre-Earnings Defense Calendar</h2>
<p>{{NARRATIVE_S5_OPENING}}</p><!-- what the flows/deals say, whether they corroborate or dissent from sections 3-4, and the pre-earnings risk rule applied to named holdings. -->
<div class="table-wrapper">
<table class="wikitable">
  <thead>
    <tr><th>Security</th><th>Deal Type / Event</th><th>Entity / Executive</th><th class="num">Value (₹ Cr)</th><th>Significance &amp; Action Protocol</th></tr>
  </thead>
  <tbody>
    <!-- Bulk/block deals & catalyst radar -->
  </tbody>
</table>
</div>

<!-- SECTION 6: TACTICAL PLAYBOOK -->
<h2 id="section6">6. Tactical Playbook &amp; Capital Allocation</h2>
<div class="callout-box">
  <strong>Top 3 Tactical Setups of the Day:</strong>
  <ul>
    <li><strong>Setup 1:</strong> Exact entry band, stop loss, base target, asymmetry ratio ($R:R \ge 3.5:1$).</li>
    <li><strong>Setup 2:</strong> Exact entry band, stop loss, base target, asymmetry ratio ($R:R \ge 3.5:1$).</li>
    <li><strong>Setup 3:</strong> Exact entry band, stop loss, base target, asymmetry ratio ($R:R \ge 3.5:1$).</li>
  </ul>
</div>
<p><strong>Regime-Aligned Portfolio Stance:</strong> {{NARRATIVE_S6_STANCE}}</p><!-- state the ledger regime label, the posture from the standard's regime table, the Core/Tactical/Cash split, and a case note (2-4 sentences) for each of the Top 3 setups citing sector + flow evidence. -->

<!-- SECTION 7: WATCHLIST INGESTION -->
<h2 id="section7">7. Watchlist Synchronization &amp; Idea Ingestion</h2>
<p>{{NARRATIVE_S7_INGESTION}}</p><!-- why exactly these 1-3 names (they must be the section 6 setups), what the watchlist does next (3-layer underwriting), and any overlap with holdings. Source Type = 'MARKET_INTELLIGENCE' into watchlist/Zerodha_Watchlist.xlsx. -->

<!-- REFERENCES & CITATIONS -->
<h2 id="references">References &amp; Regulatory Filings</h2>
<ol class="reflist">
  <li id="cite_note-1">^ National Stock Exchange of India (NSE) &bull; Bhavcopy and Derivative Statistics for {{SESSION_DATE}}: <a href="https://www.nseindia.com" target="_blank">nseindia.com</a></li>
  <li id="cite_note-2">^ Bombay Stock Exchange (BSE) &bull; Bulk &amp; Block Deals Disclosures: <a href="https://www.bseindia.com" target="_blank">bseindia.com</a></li>
  <li id="cite_note-3">^ Screener.in Consolidated Financial Query Engine: <a href="https://www.screener.in" target="_blank">screener.in</a></li>
  <li id="cite_note-4">^ TradingView Interactive Technical Screener: <a href="https://www.tradingview.com" target="_blank">tradingview.com</a></li>
</ol>

</div>
</div>
</body>
</html>
```

---

### DELIVERABLES, GOOGLE DRIVE MAINTENANCE & EMAIL TRANSMISSION:

- **Recipient:** `rajasekharreddymekala732@gmail.com`
- **Subject:** `Subject: 📊 Daily Market Pulse | [Session Date] — Nifty [Trend/Status] | 30 Breakouts & 30 Breakdown Alerts`
- **Pre-Send Audit:** Zero omissions across all 7 sections. Complete 30 longs + 30 shorts rendered.
- **Google Drive Maintenance (Single Latest Version Lifecycle):**
  - **Target Location:** `googledrive/newsletters/Daily_Market_Intelligence_<YYYY-MM-DD>.html`
  - **Date Display:** The run date (`YYYY-MM-DD` / formatted session date) must be prominently displayed in the document title, subtitle, and Wikipedia Infobox metadata.
  - **Prune Prior Versions:** Automatically scan `googledrive/newsletters/` and delete / remove all previous versions matching `Daily_Market_Intelligence_*.html` prior to or upon saving the new file, ensuring only the single latest report is maintained in Google Drive.
- **Automated Dispatch Execution (MANDATORY):**
  - Persist the complete HTML newsletter to `googledrive/newsletters/Daily_Market_Intelligence_<YYYY-MM-DD>.html`.
  - Dispatch the email immediately and automatically via `scripts/send_email.py` using credentials from `.env` (Do NOT prompt the user or request manual confirmation):
    ```bash
    python3 scripts/send_email.py --subject "📊 Daily Market Pulse | [Session Date] — Nifty [Trend/Status] | 30 Breakouts & 30 Breakdown Alerts" --html-file "googledrive/newsletters/Daily_Market_Intelligence_<YYYY-MM-DD>.html" --recipient "rajasekharreddymekala732@gmail.com"
    ```
  - Confirm successful SMTP execution in the final turn summary.
