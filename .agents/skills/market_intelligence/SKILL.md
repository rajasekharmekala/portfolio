---
name: market_intelligence
description: >-
  Daily market intelligence briefing for one market (IN = NSE/BSE, US = NYSE/NASDAQ). Builds the facts ledger, runs the research pass, and writes a Wikipedia-style book report in beginner-friendly prose with sections, tables, options and sector analysis, Stage 2 breakouts and Stage 4 breakdowns, and a tactical playbook. Market-specific blocks are marked; figures, currency and sources differ by market.

---

> **Market blocks (binding):** this skill covers both markets. Read `.agents/config/markets.json` for the market in this run (`IN` or `US`). Follow the text that is not inside a market block, and inside a market block follow only the block whose label matches the run's market. Ignore the other block. Figures, currency, exchange names and data sources differ by market; never mix them.

<!-- MARKET IN -->
# Wikipedia-Style Institutional Daily Market Intelligence Newsletter Skill
<!-- /MARKET -->
<!-- MARKET US -->
# Wikipedia-Style Institutional Daily US Market Intelligence Newsletter Skill
<!-- /MARKET -->

> **Voice (binding):** read `../_shared/REPORT_VOICE.md` before writing. Explain every heading and subsection in plain English with reasoning and consequences; no template phrases; each verdict names its rule and the level that would change it. Colours come only from `../_shared/REPORT_PALETTE.md`: use the `verdict-*` classes and no emoji status markers.

<!-- MARKET IN -->
Act as a **Senior Institutional Equity Research Analyst**, **Derivatives Strategist**, and **Wikipedia Financial Editor** covering Indian Equity Markets (NSE/BSE).
<!-- /MARKET -->
<!-- MARKET US -->
Act as a **Senior Institutional Equity Research Analyst**, **US Derivatives Strategist**, and **Wikipedia Financial Editor** covering US Equity Markets (NYSE / NASDAQ).
<!-- /MARKET -->

<!-- MARKET IN -->
Execute the **Daily Market Intelligence & Watchlist Ingestion Engine**:
<!-- /MARKET -->
<!-- MARKET US -->
Execute the **Daily US Market Intelligence & Watchlist Ingestion Engine**:
<!-- /MARKET -->
1. Generate an exhaustive daily market intelligence briefing formatted in authentic **Wikipedia Design System** (NPOV encyclopedic tone, floating infobox, wikitables, footnotes, verified citations).
<!-- MARKET IN -->
2. Maintain and synchronize the deliverable in Google Drive at **`docs/reports/Daily_Market_Intelligence_<YYYY-MM-DD>.html`** (maintaining **strictly only the single latest generated report showing the run date on the page**, and automatically deleting all prior versions).
<!-- /MARKET -->
<!-- MARKET US -->
2. Maintain and synchronize the deliverable in Google Drive at **`docs/reports/US_Market_Intelligence_<YYYY-MM-DD>.html`** (maintaining **strictly only the single latest generated report showing the run date on the page**, and automatically deleting all prior versions).
<!-- /MARKET -->
3. Transmit the complete deliverable via Gmail to **`rajasekharreddymekala732@gmail.com`**.
<!-- MARKET IN -->
4. Synchronize and maintain **`data/watchlist/IN.json`** (feeding the top 1–3 standout setups of the day directly into the top of the deep research funnel).
<!-- /MARKET -->
<!-- MARKET US -->
4. Synchronize and maintain **`data/watchlist/US.json`** (feeding the top 1–3 standout setups of the day directly into the top of the deep research funnel).
<!-- /MARKET -->

The tone is **neutral (Wikipedia NPOV) and explanatory**. Follow `../_shared/REPORT_VOICE.md`: explain every heading in plain English, give the reasoning and the consequence for every number, name the rule behind every verdict, and tie each section forward to the next. No promotional slang, no template phrases.

---

### EDITORIAL, DATA-COMPLETENESS & COHERENCE STANDARD (MANDATORY — READ FIRST):

Before anything else, read `.agents/skills/_shared/REPORT_EDITORIAL_STANDARD.md` in full; it is binding and overrides any terser skeleton text below. Non-negotiables:

<!-- MARKET IN -->
1. **Data first:** run `python3 scripts/market_facts.py --market IN --date <session> --screen nifty500 --run-dir "<RUN_DIR>"`. Every price, DMA, RSI, ATR, volume multiple, Weinstein stage, regime label, breadth figure, sector quadrant and both 30-name lists must come from `<RUN_DIR>/cache/facts_IN_<date>.json`. `N/A` is a last resort after the ledger, the mandatory duck-duck-go MCP research pass (`search` + `fetch_content`, protocol in section 6 of the standard; results recorded in `<RUN_DIR>/cache/research_IN_<date>.json` with source URL and as-of date) and a second source have all failed (max 5% of table cells). FII/DII flows, NSE option-chain OI/PCR, FII index futures, bulk/block deals, delivery %, results dates and catalysts come from that pass, not from memory. Use precise date-stamped queries, fetch and read the actual page (snippets are not evidence), try direct NSE archive URLs first, and cross-check headline figures with a second source. Never carry forward the previous report's names or publish a "revalidation pending" list; publish exactly `screen.bull_pick` and `screen.bear_pick` (10 per cap tier, company names and sectors from the pick rows, `qualifier` shown and explained).
2. **Write it as a book for a beginner (section 3 and blueprint 7A of the standard):** append `.agents/skills/_shared/report_base.css and book_components.css` to the report's `<style>`; open with a 450+ word `primer` ("Start here": every key idea with an everyday analogy), then a 250-400 word lede; every section opens with a 200+ word essay and closes with a "what this means for you" paragraph; every table has a `howto` block before it (read one real row aloud) and a 120+ word `takeaway` after it; `casenote` stories (80+ words: what the company does, the numbers and what they mean, the verdict and the exact rule behind it, what would change it, with prices) for the Top 3 setups, three spotlights per list and each leading/lagging sector; at least one worked `example` with rupee arithmetic; a `triggers` if/then block per section; a glossary and a methodology/data-gaps note. Target 12,000+ words; the validator floor is 9,000. Never leave a number unexplained.
3. **One story:** one regime label (ledger `regime.label`) used verbatim in the infobox, Section 1 and Section 6; the Bull List is drawn from leading sectors and the Bear List from lagging ones (exceptions named); the Section 6 Top 3 come only from Section 3 and are sized by the regime table; Section 7 ingests only those names. Read the same-date `Portfolio_Audit_*.html` first and reconcile every shared ticker's price and stage.
4. **Gate:** `python3 scripts/validate_report.py --report docs/reports/Daily_Market_Intelligence_<date>.html --kind market_intel --facts <RUN_DIR>/cache/facts_IN_<date>.json` must print `PASS` before the Drive save and email. The HTML skeleton below is table scaffolding only: every `{{NARRATIVE_*}}` slot, plus an intro `<p>` before and a takeaway `<p>` after every table, must be written as full prose.
<!-- /MARKET -->
<!-- MARKET US -->
1. **Data first:** run `python3 scripts/market_facts.py --market US --date <session> --screen sp1500 --run-dir "<RUN_DIR>"`. Every price, DMA, RSI, ATR, volume multiple, Weinstein stage, regime label, breadth figure, Treasury yield, sector quadrant and both 30-name lists must come from `<RUN_DIR>/cache/facts_US_<date>.json`. `N/A` is a last resort after the ledger, the mandatory duck-duck-go MCP research pass (`search` + `fetch_content`, protocol in section 6 of the standard; results recorded in `<RUN_DIR>/cache/research_US_<date>.json` with source URL and as-of date) and a second source have all failed (max 5% of table cells). CBOE put/call, SPY/QQQ/IWM option walls (compute from the live chain where possible), SEC Form 4 cluster buys, earnings dates and catalysts come from that pass, not from memory. Use precise date-stamped queries, fetch and read the actual page (snippets are not evidence), try primary sources (SEC, CBOE, FRED) first, and cross-check headline figures with a second source. Never invent or carry forward prices/names from a previous report; publish exactly `screen.bull_pick` and `screen.bear_pick` (10 per cap tier, company names and sectors from the pick rows, `qualifier` shown and explained).
2. **Write it as a book for a beginner (section 3 and blueprint 7A of the standard):** append `.agents/skills/_shared/report_base.css and book_components.css` to the report's `<style>`; open with a 450+ word `primer` ("Start here": every key idea with an everyday analogy), then a 250-400 word lede; every section opens with a 200+ word essay and closes with a "what this means for you" paragraph; every table has a `howto` block before it (read one real row aloud) and a 120+ word `takeaway` after it; `casenote` stories (80+ words: what the company does, the numbers and what they mean, the verdict and the exact rule behind it, what would change it, with prices) for the Top 3 setups, three spotlights per list and each leading/lagging sector; at least one worked `example` with dollar arithmetic; a `triggers` if/then block per section; a glossary and a methodology/data-gaps note. Target 12,000+ words; the validator floor is 9,000. Never leave a number unexplained.
3. **One story:** one regime label (ledger `regime.label`) used verbatim in the infobox, Section 1 and Section 6; the Bull List is drawn from leading sectors and the Bear List from lagging ones (exceptions named); the Section 6 Top 3 come only from Section 3 and are sized by the regime table; Section 7 ingests only those names. Read the same-date `US_Portfolio_Audit_*.html` first and reconcile every shared ticker's price and stage (a name on the Bull List cannot be shown by the audit as below its 50-DMA).
4. **Gate:** `python3 scripts/validate_report.py --report docs/reports/US_Market_Intelligence_<date>.html --kind market_intel --facts <RUN_DIR>/cache/facts_US_<date>.json` must print `PASS` before the Drive save and email. The HTML skeleton below is table scaffolding only: every `{{NARRATIVE_*}}` slot, plus an intro `<p>` before and a takeaway `<p>` after every table, must be written as full prose.
<!-- /MARKET -->

---

<!-- MARKET IN -->
### MANDATORY ZERO-HALLUCINATION & DATA ACCURACY RULES:
<!-- /MARKET -->
<!-- MARKET US -->
### MANDATORY ZERO-HALLUCINATION & DERIVATIVES ACCURACY RULES:
<!-- /MARKET -->

<!-- MARKET IN -->
1. **NO HALLUCINATIONS:** Strictly base all technical levels, market prices, moving averages, RSI values, volume multiples, derivative metrics (OI, PCR, VIX, FII flows), and corporate catalysts on verified market closing data and exchange disclosures.
2. **MANDATORY USE OF `N/A` (NO GUESSING / NO FABRICATION):** If any specific metric (e.g., historical delivery volume, promoter pledge, or consensus broker target) is not deterministically verified, output **`N/A`** with a specific reason rather than fabricating or estimating numbers. `N/A` is allowed only after `scripts/market_facts.py`, an alternate source and web search have all failed; it must never stand in for data that price history can supply (returns, DMAs, RSI, ATR, volume multiple, stage).
3. **AUTHORITATIVE 2-TIER MASTER TAXONOMY:** Classify and group all sector heatmap movers, momentum themes, and stock lists according to the **Embedded 2-Tier Master Taxonomy** (*Macro Sector Group* / *Fine-Grained Subsector*).
4. **MANDATORY TRADINGVIEW & SCREENER NAVIGATION LINKS:**
<!-- /MARKET -->
<!-- MARKET US -->
1. **NO HALLUCINATIONS:** Strictly base all technical levels, market prices, moving averages, RSI values, volume multiples, derivative metrics (OI, PCR, VIX, Treasury yields), and corporate catalysts on verified market closing data and SEC disclosures.
2. **MANDATORY USE OF `N/A` (NO GUESSING / NO FABRICATION):** If any specific metric (e.g., historical dark pool volume, insider cluster buying, or consensus price target) is not deterministically verified, output **`N/A`** with a specific reason rather than fabricating numbers. `N/A` is allowed only after `scripts/market_facts.py`, an alternate source and web search have all failed; it must never stand in for data that price history can supply (returns, DMAs, RSI, ATR, volume multiple, stage).
3. **AUTHORITATIVE 11-GROUP MASTER US TAXONOMY:** Classify and group all sector heatmap movers, momentum themes, and stock lists according to the **Embedded 11-Group Master US Taxonomy** (*Macro Sector Group* / *Fine-Grained Subsector*).
4. **MANDATORY TRADINGVIEW & FINVIZ NAVIGATION LINKS:**
<!-- /MARKET -->
   - For every security referenced in the report, provide direct clickable links:
<!-- MARKET IN -->
     - **TradingView Chart:** `https://www.tradingview.com/chart/?symbol=NSE%3A{SYMBOL}`
     - **Screener.in Financials:** `https://www.screener.in/company/{SYMBOL}/`
<!-- /MARKET -->
<!-- MARKET US -->
     - **TradingView Chart:** `https://www.tradingview.com/chart/?symbol={PRIMARY_EXCHANGE}%3A{SYMBOL}`
     - **Finviz Profile:** `https://finviz.com/quote.ashx?t={SYMBOL}`
<!-- /MARKET -->
   - In all data tables, format the Symbol column with clickable sub-links:
<!-- MARKET IN -->
     `<b>{SYMBOL}</b><br><span style="font-size: 11px;"><a href="https://www.tradingview.com/chart/?symbol=NSE%3A{SYMBOL}" style="color: #0645ad;">Chart</a> • <a href="https://www.screener.in/company/{SYMBOL}/" style="color: #14532d;">Screener</a></span>`
<!-- /MARKET -->
<!-- MARKET US -->
     `<b>{SYMBOL}</b><br><span style="font-size: 11px;"><a href="https://www.tradingview.com/chart/?symbol=NASDAQ%3A{SYMBOL}" style="color: #0645ad;">Chart</a> • <a href="https://finviz.com/quote.ashx?t={SYMBOL}" style="color: #14532d;">Finviz</a></span>`
<!-- /MARKET -->
5. **MANDATORY ZERO-OMISSION REPORT INTEGRITY (NO SECTIONS SKIPPED IN EMAIL NEWSLETTER):**
   - Every single section (Sections 1 through 7) and every table must be 100% fully rendered.
   - Strictly forbidden: Truncating sections, omitting tables, using placeholder comments (e.g. `<!-- rest of table omitted -->`, `[Remaining setups continue...]`), or skipping any breakout/breakdown candidates or sector heatmaps.
   - The full 30 breakout alerts and 30 breakdown alerts, all sector movers, and top tactical setups must be completely populated.
6. **MANDATORY INDEPENDENT REVIEWER AGENT & EXTENSIVE DUCK-DUCK-GO MCP WEB VERIFICATION:**
<!-- MARKET IN -->
   - Double-check all closing prices (CMP), 52-week ranges, moving averages, 14-day RSI, volume expansion multiples, PCR, India VIX, and FII/DII net flows via live online search (the `duck-duck-go` MCP `search` then `fetch_content`, per section 6 of `.agents/skills/_shared/REPORT_EDITORIAL_STANDARD.md`).
<!-- /MARKET -->
<!-- MARKET US -->
   - Double-check all closing prices (CMP), 52-week ranges, moving averages, 14-day RSI, volume expansion multiples, PCR, CBOE VIX, and Treasury yields via live online search (the `duck-duck-go` MCP `search` then `fetch_content`, per section 6 of `.agents/skills/_shared/REPORT_EDITORIAL_STANDARD.md`).
<!-- /MARKET -->
7. **MANDATORY GOOGLE DRIVE SYNCHRONIZATION, REPORT LIFECYCLE & IN-PLACE OVERWRITE:**
<!-- MARKET IN -->
   - Ingest `data/accounts/IN/zerodha.transactions.jsonl` and `data/shortlist/IN.json` fresh from sheets/ and shortlist/.
   - Modify and persist `data/watchlist/IN.json` strictly IN-PLACE.
   - **Single Latest Report Maintenance in docs/reports/:** Save the generated HTML briefing to `docs/reports/Daily_Market_Intelligence_<YYYY-MM-DD>.html`. The document title, page header, and infobox must clearly display the session date (`YYYY-MM-DD`). Automatically scan `docs/reports/` and delete all previous `Daily_Market_Intelligence_*.html` files before/upon writing the new one, ensuring Google Drive holds strictly only the single latest generated report.
<!-- /MARKET -->
<!-- MARKET US -->
   - Ingest `data/metadata/symbols.json` and `data/shortlist/US.json` fresh from sheets/ and shortlist/.
   - Modify and persist `data/watchlist/US.json` strictly IN-PLACE.
   - **Single Latest Report Maintenance in docs/reports/:** Save the generated HTML briefing to `docs/reports/US_Market_Intelligence_<YYYY-MM-DD>.html`. The document title, page header, and infobox must clearly display the session date (`YYYY-MM-DD`). Automatically scan `docs/reports/` and delete all previous `US_Market_Intelligence_*.html` files before/upon writing the new one, ensuring Google Drive holds strictly only the single latest generated report.
<!-- /MARKET -->
8. **MANDATORY AUTOMATED EMAIL DISPATCH (NO MANUAL CONFIRMATION / NO BLOCKED POLICY):**
   - Automated email dispatch of the generated newsletter to `rajasekharreddymekala732@gmail.com` via `scripts/send_email.py` is a **STRICT, MANDATORY PIPELINE REQUIREMENT** for every run.
   - You MUST programmatically run the `send_email.py` command in the terminal as the final automated step.
   - NEVER skip email dispatch, NEVER prompt the user asking for manual sending permission, and NEVER report that automated email is blocked by security policy. The workspace environment explicitly pre-authorizes programmatic email dispatch via `scripts/send_email.py`.
9. **MANDATORY ONE-OFF SCRIPT LIFECYCLE & CACHE HYGIENE (NO RESIDUAL ARTIFACTS):**
   - Scratch code lives only in `<RUN_DIR>` and is deleted with it (RUN_PROTOCOL sections 1 and 5).
   - **Run directory:** nothing from earlier runs is read. Cleanup follows `../_shared/RUN_PROTOCOL.md` section 5. Repository scripts are never deleted.
   - **Permanent repository scripts (never delete or modify without the user):** `scripts/send_email.py`, `scripts/build_dossier_portal.py`, `scripts/serve_blogs.py`, `scripts/market_facts.py`, `scripts/validate_report.py`.
   - **Pre-termination verification:** run `ls scripts/` and confirm ONLY whitelisted files remain. Leaving one-off generator/update scripts behind is a pipeline failure.

---

### DECOUPLED SPECIALIST SUBAGENT WORKFLOW (ELIMINATING DIRECTIONAL BIAS & CONTEXT FATIGUE):

To eliminate directional bias and context exhaustion, the newsletter is synthesized by 4 independent specialist subagents and 1 master editor:

<!-- MARKET IN -->
#### 1. Specialist 1: `macro_derivatives_strategist` (Macro Regime, Gamma Walls & Sector Rotation)
- **Focus:** Nifty 50, Bank Nifty, India VIX, FII/DII Net Cash, FII Index Futures Long/Short Ratio, Options Open Interest Clusters (Call/Put Walls, Max Pain, PCR), and 4-Quadrant Sector Rotation Matrix.
- **Protocol:** Uses web search to retrieve Bhavcopy, NSE derivatives open interest stats, India VIX closing levels, and sector index performances.
<!-- /MARKET -->
<!-- MARKET US -->
#### 1. Specialist 1: `us_macro_derivatives_strategist` (Macro Regime, Gamma Walls & Sector Rotation)
- **Focus:** S&P 500 (SPY), Nasdaq 100 (QQQ), Russell 2000 (IWM), CBOE VIX, US 10Y/2Y Treasury Yields, CBOE Total Put/Call Ratio, SPY/QQQ Options Gamma Walls (Call Wall, Put Wall, Volatility Trigger), and 11-Group US Sector Rotation Matrix.
- **Protocol:** Uses web search to retrieve CBOE options open interest data, FRED Treasury yields, and sector ETF performances (XLK, XLC, XLV, XLI, XLY, XLP, XLE, XLF, XLB, XLU, XLRE).
<!-- /MARKET -->

<!-- MARKET IN -->
#### 2. Specialist 2: `bull_momentum_desk` (Long Stage 2 Breakout Screener)
- **Focus:** Long momentum universe (Exactly 30 Verified Setups: 10 Large-Cap >₹50,000 Cr, 10 Mid-Cap ₹15,000–50,000 Cr, 10 Small/Micro-Cap ₹500–15,000 Cr).
<!-- /MARKET -->
<!-- MARKET US -->
#### 2. Specialist 2: `us_bull_momentum_desk` (Long Stage 2 Breakout Screener)
- **Focus:** Long momentum universe (Exactly 30 Verified Setups: 10 Mega/Large-Cap >$50B, 10 Mid-Cap $10B–$50B, 10 Small/Growth $1B–$10B).
<!-- /MARKET -->
- **Hurdles:** Weinstein Stage 2 markup, Price > 50-DMA > 200-DMA, volume expansion ≥ 1.5x 20-DMA volume, 14-day RSI 55–72, reward/risk asymmetry ≥ 3.5:1.

<!-- MARKET IN -->
#### 3. Specialist 3: `bear_distribution_desk` (Short & Distribution Risk Screener)
<!-- /MARKET -->
<!-- MARKET US -->
#### 3. Specialist 3: `us_bear_distribution_desk` (Short & Distribution Risk Screener)
<!-- /MARKET -->
- **Focus:** Short/Distribution universe (Exactly 30 Verified Breakdown Setups: 10 Large, 10 Mid, 10 Small).
- **Hurdles:** Weinstein Stage 4 breakdown, Price < 50-DMA < 200-DMA (or death cross), heavy distribution volume (>1.5x 20-DMA volume on down days), 14-day RSI < 45.

<!-- MARKET IN -->
#### 4. Specialist 4: `smart_money_catalyst_radar` (Institutional Deals & Event Defense)
- **Focus:** BSE/NSE Bulk & Block Deals (>₹10 Cr), promoter insider open-market purchases/sales, SAST pledge disclosures, and upcoming high-impact earnings/event dates.
<!-- /MARKET -->
<!-- MARKET US -->
#### 4. Specialist 4: `us_smart_money_catalyst_radar` (SEC Form 4 Insider Trades & 13F Whales)
- **Focus:** SEC Form 4 insider open-market cluster buying, 13F institutional whale accumulation, and upcoming high-impact earnings/catalyst dates.
<!-- /MARKET -->

<!-- MARKET IN -->
#### 5. Master Editor & Watchlist Ingestion Gatekeeper (`tactical_playbook_and_ingestion`)
<!-- /MARKET -->
<!-- MARKET US -->
#### 5. Master Editor & Watchlist Gatekeeper (`tactical_playbook_and_ingestion`)
<!-- /MARKET -->
- **Tactical Playbook (Section 6):** Selects the **Top 3 Standout Setups of the Day** (Asymmetry $\ge 3.5:1$) with exact entry bands, stops, targets, and regime-aligned portfolio allocation stance.
<!-- MARKET IN -->
- **Watchlist Ingestion (Section 7):** Ingests the standout ideas into `data/watchlist/IN.json`.
<!-- /MARKET -->
<!-- MARKET US -->
- **Watchlist Ingestion (Section 7):** Ingests the standout ideas into `data/watchlist/US.json`.
<!-- /MARKET -->
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
  - Color Palette: Body text `#202122` (soft obsidian), background `#ffffff`, subtle borders `#d1d5db`, table header gray `#f3f4f6`, hover background `#eff6ff`.
  - Line height: `1.72`, font size `15px`, letter spacing `-0.011em`, standard paragraph margins with justified text.
- **Wikipedia Infobox (`table.infobox`):**
  - Floated right with width `320px`, border `1px solid #d1d5db`, background `#f8f9fa`.
<!-- MARKET IN -->
  - Captures market internal vital statistics: Market Regime, India VIX, FII Index Futures Long/Short Bias, Market Breadth (% > 50-DMA), Advance/Decline Ratio, Distribution Days, FII/DII Net Cash.
<!-- /MARKET -->
<!-- MARKET US -->
  - Captures market internal vital statistics: Market Regime, CBOE VIX, S&P 500 / Nasdaq 100 Closes, US 10Y Yield, Total Put/Call Ratio, Breadth (% > 50-DMA), Distribution Days.
<!-- /MARKET -->
- **Wikitables (`table.wikitable`):**
  - Width: `100%`, border collapse: `collapse`, border: `1px solid #d1d5db`, background: `#ffffff`, font-size: `89%`.
  - Header cells `th`: `#f3f4f6`, bold, border `1px solid #d1d5db`, padding `8px 12px`.
  - Data cells `td`: padding `7px 12px`, border `1px solid #d1d5db`. Alternating rows `#f8f9fa`. Hover `#eff6ff`.
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
<!-- SKELETON NOTE: write only the body (the section fragments). Do not write this <head> or its <style>; scripts/assemble_report.py builds the head from REPORT_PALETTE.md, report_base.css and book_components.css, and it wraps tables. Keep the <div class="key-figures"> strip and every table inside .table-wrap. -->
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<!-- MARKET IN -->
<title>Indian Equity Market Intelligence &amp; Derivatives Radar — {{SESSION_DATE}}</title>
<!-- /MARKET -->
<!-- MARKET US -->
<title>US Equity Market Intelligence &amp; Derivatives Radar — {{SESSION_DATE}}</title>
<!-- /MARKET -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400;1,500&family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;0,6..72,700;1,6..72,400;1,6..72,500&family=JetBrains+Mono:ital,wght@0,400;0,500;0,600;0,700;1,400&display=swap" rel="stylesheet">
<style>
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
  color: #202122;
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
.pill-fail, .badge-red { background-color: #fee2e2; color: #7f1d1d; }
.badge-blue { background-color: #dbeafe; color: #0645ad; }
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

<!-- MARKET IN -->
<h1 class="firstHeading">Indian Equity Market Intelligence &amp; Derivatives Radar</h1>
<div class="siteSub">From Wikipedia, the institutional financial encyclopedia &bull; Daily Session Close &bull; NSE/BSE &bull; {{SESSION_DATE}}</div>
<!-- /MARKET -->
<!-- MARKET US -->
<h1 class="firstHeading">US Equity Market Intelligence &amp; Derivatives Radar</h1>
<div class="siteSub">From Wikipedia, the institutional financial encyclopedia &bull; Daily Session Close &bull; NYSE / NASDAQ &bull; {{SESSION_DATE}}</div>
<!-- /MARKET -->

<div class="clearfix">

<!-- MARKET IN -->
<!-- WIKIPEDIA FLOATED INFOBOX: MARKET REGIME INTERNALS -->
<!-- /MARKET -->
<!-- MARKET US -->
<!-- WIKIPEDIA FLOATED INFOBOX: US MARKET REGIME INTERNALS -->
<!-- /MARKET -->
<table class="infobox" role="presentation">
<!-- MARKET IN -->
  <caption>Market Internal Vitals</caption>
<!-- /MARKET -->
<!-- MARKET US -->
  <caption>US Market Internal Vitals</caption>
<!-- /MARKET -->
  <tr><th colspan="2" class="infobox-header">Session Snapshot: {{SESSION_DATE}}</th></tr>
  <tr><th>Market Regime</th><td><strong>{{MARKET_REGIME}}</strong> (Stage 2 / Neutral / Distribution)</td></tr>
<!-- MARKET IN -->
  <tr><th>India VIX</th><td>{{VIX_VALUE}} &bull; {{VIX_REGIME}}</td></tr>
  <tr><th>FII Index Futures</th><td>Long: {{FII_LONG_PCT}}% &bull; Short: {{FII_SHORT_PCT}}%</td></tr>
  <tr><th>Market Breadth</th><td>{{BREADTH_PCT}}% of Nifty 500 &gt; 50-DMA</td></tr>
  <tr><th>Advance / Decline</th><td>Advances: {{ADVANCES}} &bull; Declines: {{DECLINES}} (Ratio: {{AD_RATIO}})</td></tr>
  <tr><th>Nifty Distribution Days</th><td>{{DISTRIBUTION_DAYS}} Days</td></tr>
  <tr><th>FII / DII Net Cash</th><td>FII: ₹{{FII_NET}} Cr &bull; DII: ₹{{DII_NET}} Cr</td></tr>
<!-- /MARKET -->
<!-- MARKET US -->
  <tr><th>CBOE VIX</th><td>{{VIX_VALUE}} &bull; {{VIX_REGIME}}</td></tr>
  <tr><th>S&amp;P 500 (SPY) Close</th><td>${{SPY_CLOSE}} ({{SPY_1D_CHANGE}}%)</td></tr>
  <tr><th>Nasdaq 100 (QQQ) Close</th><td>${{QQQ_CLOSE}} ({{QQQ_1D_CHANGE}}%)</td></tr>
  <tr><th>US 10-Year Yield</th><td>{{US10Y_YIELD}}% ({{US10Y_TREND}})</td></tr>
  <tr><th>Total Put / Call Ratio</th><td>{{PCR_VALUE}} ({{PCR_SENTIMENT}})</td></tr>
  <tr><th>Market Breadth</th><td>{{BREADTH_PCT}}% of S&amp;P 500 &gt; 50-DMA</td></tr>
  <tr><th>NYSE/NASDAQ Adv/Dec</th><td>Advances: {{ADVANCES}} &bull; Declines: {{DECLINES}}</td></tr>
  <tr><th>Distribution Days</th><td>S&amp;P: {{SP_DIST_DAYS}} &bull; Nasdaq: {{NDX_DIST_DAYS}}</td></tr>
<!-- /MARKET -->
</table>

<!-- SECTION 1: THE BIG PICTURE -->
<!-- MARKET IN -->
<h2 id="section1">1. The Big Picture: Market Regime, Benchmarks &amp; Derivatives</h2>
<!-- /MARKET -->
<!-- MARKET US -->
<h2 id="section1">1. The Big Picture: Macro Regime, US Benchmarks &amp; Derivatives</h2>
<!-- /MARKET -->

<p>{{NARRATIVE_LEDE_AND_S1_OPENING}}</p><!-- lede 150+ words (verdict, 3 numbers that matter, the action, section map) then 60+ words on what section 1 measures. Every table below: intro <p> before, takeaway <p> after. -->

<h3>1.1 Benchmark Indices Performance &amp; Valuation</h3>
<div class="table-wrapper">
<table class="wikitable">
  <thead>
    <tr>
<!-- MARKET IN -->
      <th>Index / Benchmark</th>
<!-- /MARKET -->
<!-- MARKET US -->
      <th>Index / ETF</th>
<!-- /MARKET -->
      <th class="num">Latest Close</th>
      <th>Returns (1D / 1W / 2W)</th>
      <th>Technical State</th>
      <th>Valuation &amp; Risk Context</th>
    </tr>
  </thead>
  <tbody>
<!-- MARKET IN -->
    <!-- Nifty 50, Nifty Midcap 150, Nifty Smallcap 250, Nifty 500 -->
<!-- /MARKET -->
<!-- MARKET US -->
    <!-- S&P 500, Nasdaq 100, Russell 2000, Dow Jones -->
<!-- /MARKET -->
  </tbody>
</table>
</div>

<!-- MARKET IN -->
<h3>1.2 Options Gamma Wall &amp; Institutional Positioning Map</h3>
<!-- /MARKET -->
<!-- MARKET US -->
<h3>1.2 Options Gamma Wall &amp; Volatility Architecture</h3>
<!-- /MARKET -->
<div class="table-wrapper">
<table class="wikitable">
  <thead>
    <tr>
<!-- MARKET IN -->
      <th>Barrier Level</th>
      <th class="num">Strike Price</th>
      <th class="num">Open Interest (Lakhs)</th>
      <th>Institutional Significance</th>
<!-- /MARKET -->
<!-- MARKET US -->
      <th>Index / Underlying</th>
      <th>Call Wall Strike</th>
      <th>Put Wall Strike</th>
      <th>Volatility Trigger</th>
      <th>Gamma Regime</th>
<!-- /MARKET -->
    </tr>
  </thead>
  <tbody>
<!-- MARKET IN -->
    <!-- Call Wall, Spot, Put Wall -->
<!-- /MARKET -->
<!-- MARKET US -->
    <!-- SPY, QQQ, IWM -->
<!-- /MARKET -->
  </tbody>
</table>
</div>
<!-- MARKET IN -->
<p style="font-size: 90%; color: #555;">Put-Call Ratio (PCR): <strong>{{PCR_VALUE}}</strong> &bull; Options Sentiment Bias: <strong>{{OPTIONS_BIAS}}</strong></p>
<!-- /MARKET -->
<!-- MARKET US -->
<p style="font-size: 90%; color: #555;">Total Put-Call Ratio (PCR): <strong>{{PCR_VALUE}}</strong> &bull; CBOE VIX Regime: <strong>{{VIX_REGIME}}</strong></p>
<!-- /MARKET -->

<!-- MARKET IN -->
<h3>1.3 Global Macro Matrix &amp; Transmission Channels</h3>
<!-- /MARKET -->
<!-- MARKET US -->
<h3>1.3 US Treasury Yield Curve &amp; Macro Transmission</h3>
<!-- /MARKET -->
<div class="table-wrapper">
<table class="wikitable">
  <thead>
    <tr>
<!-- MARKET IN -->
      <th>Global Asset</th>
      <th class="num">Latest Price</th>
<!-- /MARKET -->
<!-- MARKET US -->
      <th>Macro Factor</th>
      <th class="num">Current Rate / Level</th>
<!-- /MARKET -->
      <th>Weekly Trend</th>
<!-- MARKET IN -->
      <th>Domestic Sector Transmission</th>
<!-- /MARKET -->
<!-- MARKET US -->
      <th>Equity Sector Transmission</th>
<!-- /MARKET -->
    </tr>
  </thead>
  <tbody>
<!-- MARKET IN -->
    <!-- Brent Crude, US 10Y, DXY, USD/INR -->
<!-- /MARKET -->
<!-- MARKET US -->
    <!-- 2Y Yield, 10Y Yield, 2Y/10Y Spread, DXY, WTI Crude -->
<!-- /MARKET -->
  </tbody>
</table>
</div>

<!-- SECTION 2: SECTOR & THEMATIC ROTATION -->
<!-- MARKET IN -->
<h2 id="section2">2. Sector &amp; Thematic Rotation Matrix</h2>
<!-- /MARKET -->
<!-- MARKET US -->
<h2 id="section2">2. US 11-Group Sector &amp; Thematic Rotation Matrix</h2>
<!-- /MARKET -->

<!-- MARKET IN -->
<h3>2.1 4-Quadrant Sector Rotation Map</h3>
<!-- /MARKET -->
<!-- MARKET US -->
<h3>2.1 4-Quadrant US Sector Rotation Map</h3>
<!-- /MARKET -->
<div class="table-wrapper">
<table class="wikitable">
  <thead>
    <tr>
      <th>Quadrant</th>
      <th>Cycle Phase</th>
<!-- MARKET IN -->
      <th>Active Sectors &amp; Subsectors</th>
      <th>Institutional Flow &amp; Action</th>
<!-- /MARKET -->
<!-- MARKET US -->
      <th>Active US Sector ETFs</th>
      <th>Institutional Flow &amp; Strategy</th>
<!-- /MARKET -->
    </tr>
  </thead>
  <tbody>
    <!-- Leading, Improving, Weakening, Lagging -->
  </tbody>
</table>
</div>

<h3>2.2 Thematic Rotation Narratives &amp; Superior Risk-Reward Proxies</h3>
<!-- MARKET IN -->
<p>{{NARRATIVE_S2_THEMES}}</p><!-- 3-4 paragraphs, one per theme: operational driver, ledger evidence, best proxy, what would invalidate it. Close with the bridge to the Bull/Bear lists. -->
<!-- /MARKET -->
<!-- MARKET US -->
<p>{{NARRATIVE_S2_THEMES}}</p><!-- 3-4 paragraphs, one per theme actually visible in the ledger (e.g. AI infrastructure, software, power/grid, defense): operational driver, ledger evidence, best proxy, what would invalidate it. Close with the bridge to the Bull/Bear lists. -->
<!-- /MARKET -->

<!-- SECTION 3: THE BULL LIST (30 STAGE 2 LONGS) -->
<!-- MARKET IN -->
<h2 id="section3">3. The Bull List: Top 30 Stage 2 Momentum Leaders</h2>
<!-- /MARKET -->
<!-- MARKET US -->
<h2 id="section3">3. The Bull List: Top 30 US Stage 2 Momentum Leaders</h2>
<!-- /MARKET -->
<p>{{NARRATIVE_S3_OPENING}}</p><!-- explain Stage 2, the hurdles applied, how many names passed strictly vs 'near', which sectors dominate and why (tie to section 2). -->

<!-- MARKET IN -->
<h3>3.1 Large-Cap Leaders (&gt; ₹50,000 Cr) — Exactly 10 Stocks</h3>
<!-- /MARKET -->
<!-- MARKET US -->
<h3>3.1 Mega &amp; Large-Cap Leaders (&gt; $50B) — Exactly 10 Stocks</h3>
<!-- /MARKET -->
<div class="table-wrapper">
<table class="wikitable">
  <thead>
<!-- MARKET IN -->
    <tr><th>Security &amp; Links</th><th class="num">Market Cap (₹ Cr)</th><th>Breakout Level &amp; DMAs</th><th>Volume Multiple &amp; RSI</th><th>Catalyst, Target &amp; Stop</th></tr>
<!-- /MARKET -->
<!-- MARKET US -->
    <tr><th>Security &amp; Links</th><th class="num">Market Cap ($B)</th><th>Breakout Level &amp; DMAs</th><th>Volume Multiple &amp; RSI</th><th>Catalyst, Target &amp; Stop</th></tr>
<!-- /MARKET -->
  </thead>
  <tbody>
    <!-- 10 Large-cap stocks -->
  </tbody>
</table>
</div>

<!-- MARKET IN -->
<h3>3.2 Mid-Cap Leaders (₹15,000 Cr to ₹50,000 Cr) — Exactly 10 Stocks</h3>
<!-- /MARKET -->
<!-- MARKET US -->
<h3>3.2 Mid-Cap Leaders ($10B to $50B) — Exactly 10 Stocks</h3>
<!-- /MARKET -->
<div class="table-wrapper">
<table class="wikitable">
  <thead>
<!-- MARKET IN -->
    <tr><th>Security &amp; Links</th><th class="num">Market Cap (₹ Cr)</th><th>Breakout Level &amp; DMAs</th><th>Volume Multiple &amp; RSI</th><th>Catalyst, Target &amp; Stop</th></tr>
<!-- /MARKET -->
<!-- MARKET US -->
    <tr><th>Security &amp; Links</th><th class="num">Market Cap ($B)</th><th>Breakout Level &amp; DMAs</th><th>Volume Multiple &amp; RSI</th><th>Catalyst, Target &amp; Stop</th></tr>
<!-- /MARKET -->
  </thead>
  <tbody>
    <!-- 10 Mid-cap stocks -->
  </tbody>
</table>
</div>

<!-- MARKET IN -->
<h3>3.3 Small-Cap &amp; Micro-Cap Leaders (₹500 Cr to ₹15,000 Cr) — Exactly 10 Stocks</h3>
<!-- /MARKET -->
<!-- MARKET US -->
<h3>3.3 Small-Cap &amp; Emerging Growth ($1B to $10B) — Exactly 10 Stocks</h3>
<!-- /MARKET -->
<div class="table-wrapper">
<table class="wikitable">
  <thead>
<!-- MARKET IN -->
    <tr><th>Security &amp; Links</th><th class="num">Market Cap (₹ Cr)</th><th>Breakout Level &amp; DMAs</th><th>Volume Multiple &amp; RSI</th><th>Catalyst, Target &amp; Stop</th></tr>
<!-- /MARKET -->
<!-- MARKET US -->
    <tr><th>Security &amp; Links</th><th class="num">Market Cap ($B)</th><th>Breakout Level &amp; DMAs</th><th>Volume Multiple &amp; RSI</th><th>Catalyst, Target &amp; Stop</th></tr>
<!-- /MARKET -->
  </thead>
  <tbody>
    <!-- 10 Small-cap stocks -->
  </tbody>
</table>
</div>

<!-- SECTION 4: THE BEAR LIST (30 STAGE 4 SHORTS) -->
<!-- MARKET IN -->
<h2 id="section4">4. The Bear List: Top 30 Stage 4 Breakdown Watchlist</h2>
<!-- /MARKET -->
<!-- MARKET US -->
<h2 id="section4">4. The Bear List: Top 30 US Stage 4 Breakdown Watchlist</h2>
<!-- /MARKET -->
<p>{{NARRATIVE_S4_OPENING}}</p><!-- explain Stage 4 and distribution volume, what the bear list says about the regime, overlap with book/watchlist, how to use it (avoid/trim/hedge; not a short signal by itself). -->
<div class="table-wrapper">
<table class="wikitable">
  <thead>
<!-- MARKET IN -->
    <tr><th>Security &amp; Links</th><th class="num">Market Cap (₹ Cr)</th><th>Breakdown Level &amp; DMAs</th><th>Volume Multiple &amp; RSI</th><th>Distribution Risk &amp; Floor</th></tr>
<!-- /MARKET -->
<!-- MARKET US -->
    <tr><th>Security &amp; Links</th><th class="num">Market Cap ($B)</th><th>Breakdown Level &amp; DMAs</th><th>Volume Multiple &amp; RSI</th><th>Distribution Risk &amp; Floor</th></tr>
<!-- /MARKET -->
  </thead>
  <tbody>
    <!-- 30 Breakdown stocks across 3 tiers -->
  </tbody>
</table>
</div>

<!-- SECTION 5: SMART MONEY RADAR -->
<h2 id="section5">5. Smart Money Radar &amp; Pre-Earnings Defense Calendar</h2>
<!-- MARKET IN -->
<p>{{NARRATIVE_S5_OPENING}}</p><!-- what the flows/deals say, whether they corroborate or dissent from sections 3-4, and the pre-earnings risk rule applied to named holdings. -->
<!-- /MARKET -->
<!-- MARKET US -->
<p>{{NARRATIVE_S5_OPENING}}</p><!-- what insider/13F flow says, whether it corroborates or dissents from sections 3-4, and the pre-earnings risk rule applied to named holdings. -->
<!-- /MARKET -->
<div class="table-wrapper">
<table class="wikitable">
  <thead>
<!-- MARKET IN -->
    <tr><th>Security</th><th>Deal Type / Event</th><th>Entity / Executive</th><th class="num">Value (₹ Cr)</th><th>Significance &amp; Action Protocol</th></tr>
<!-- /MARKET -->
<!-- MARKET US -->
    <tr><th>Security</th><th>Insider / Entity</th><th>Transaction Type</th><th class="num">Value ($M)</th><th>Significance &amp; Action Protocol</th></tr>
<!-- /MARKET -->
  </thead>
  <tbody>
<!-- MARKET IN -->
    <!-- Bulk/block deals & catalyst radar -->
<!-- /MARKET -->
<!-- MARKET US -->
    <!-- Form 4 buys & catalyst calendar -->
<!-- /MARKET -->
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
<!-- MARKET IN -->
<p><strong>Regime-Aligned Portfolio Stance:</strong> {{NARRATIVE_S6_STANCE}}</p><!-- state the ledger regime label, the posture from the standard's regime table, the Core/Tactical/Cash split, and a case note (2-4 sentences) for each of the Top 3 setups citing sector + flow evidence. -->
<!-- /MARKET -->
<!-- MARKET US -->
<p><strong>Regime-Aligned Portfolio Stance:</strong> {{NARRATIVE_S6_STANCE}}</p><!-- state the ledger regime label, the posture from the standard's regime table, the Core/Tactical/Leveraged/Cash split, and a case note (2-4 sentences) for each of the Top 3 setups citing sector + flow evidence. -->
<!-- /MARKET -->

<!-- SECTION 7: WATCHLIST INGESTION -->
<h2 id="section7">7. Watchlist Synchronization &amp; Idea Ingestion</h2>
<!-- MARKET IN -->
<p>{{NARRATIVE_S7_INGESTION}}</p><!-- why exactly these 1-3 names (they must be the section 6 setups), what the watchlist does next (3-layer underwriting), and any overlap with holdings. Source Type = 'MARKET_INTELLIGENCE' into data/watchlist/IN.json. -->
<!-- /MARKET -->
<!-- MARKET US -->
<p>{{NARRATIVE_S7_INGESTION}}</p><!-- why exactly these 1-3 names (they must be the section 6 setups), what the watchlist does next (3-layer underwriting), and any overlap with holdings. Source Type = 'MARKET_INTELLIGENCE' into data/watchlist/US.json. -->
<!-- /MARKET -->

<!-- REFERENCES & CITATIONS -->
<!-- MARKET IN -->
<h2 id="references">References &amp; Regulatory Filings</h2>
<!-- /MARKET -->
<!-- MARKET US -->
<h2 id="references">References &amp; SEC Filings</h2>
<!-- /MARKET -->
<ol class="reflist">
<!-- MARKET IN -->
  <li id="cite_note-1">^ National Stock Exchange of India (NSE) &bull; Bhavcopy and Derivative Statistics for {{SESSION_DATE}}: <a href="https://www.nseindia.com" target="_blank">nseindia.com</a></li>
  <li id="cite_note-2">^ Bombay Stock Exchange (BSE) &bull; Bulk &amp; Block Deals Disclosures: <a href="https://www.bseindia.com" target="_blank">bseindia.com</a></li>
  <li id="cite_note-3">^ Screener.in Consolidated Financial Query Engine: <a href="https://www.screener.in" target="_blank">screener.in</a></li>
  <li id="cite_note-4">^ TradingView Interactive Technical Screener: <a href="https://www.tradingview.com" target="_blank">tradingview.com</a></li>
<!-- /MARKET -->
<!-- MARKET US -->
  <li id="cite_note-1">^ US Securities and Exchange Commission (SEC EDGAR) &bull; Corporate Filings &amp; Form 4 Disclosures: <a href="https://www.sec.gov" target="_blank">sec.gov</a></li>
  <li id="cite_note-2">^ CBOE Volatility Index &amp; Options Open Interest Data: <a href="https://www.cboe.com" target="_blank">cboe.com</a></li>
  <li id="cite_note-3">^ Finviz Financial Ratios &amp; Technical Screener: <a href="https://finviz.com" target="_blank">finviz.com</a></li>
  <li id="cite_note-4">^ TradingView Interactive US Equities Charting: <a href="https://www.tradingview.com" target="_blank">tradingview.com</a></li>
<!-- /MARKET -->
</ol>

</div>
</div>
</body>
</html>
```

---

### DELIVERABLES, GOOGLE DRIVE MAINTENANCE & EMAIL TRANSMISSION:

- **Recipient:** `rajasekharreddymekala732@gmail.com`
<!-- MARKET IN -->
- **Subject:** `Subject: Daily Market Pulse | [Session Date] — Nifty [Trend/Status] | 30 Breakouts & 30 Breakdown Alerts`
<!-- /MARKET -->
<!-- MARKET US -->
- **Subject:** `Subject: Daily US Market Pulse | [Session Date] — S&P [Trend/Status] | 30 Breakouts & 30 Breakdown Alerts`
<!-- /MARKET -->
- **Pre-Send Audit:** Zero omissions across all 7 sections. Complete 30 longs + 30 shorts rendered.
- **Google Drive Maintenance (Single Latest Version Lifecycle):**
<!-- MARKET IN -->
  - **Target Location:** `docs/reports/Daily_Market_Intelligence_<YYYY-MM-DD>.html`
<!-- /MARKET -->
<!-- MARKET US -->
  - **Target Location:** `docs/reports/US_Market_Intelligence_<YYYY-MM-DD>.html`
<!-- /MARKET -->
  - **Date Display:** The run date (`YYYY-MM-DD` / formatted session date) must be prominently displayed in the document title, subtitle, and Wikipedia Infobox metadata.
<!-- MARKET IN -->
  - **Prune Prior Versions:** Automatically scan `docs/reports/` and delete / remove all previous versions matching `Daily_Market_Intelligence_*.html` prior to or upon saving the new file, ensuring only the single latest report is maintained in docs/reports/.
<!-- /MARKET -->
<!-- MARKET US -->
  - **Prune Prior Versions:** Automatically scan `docs/reports/` and delete / remove all previous versions matching `US_Market_Intelligence_*.html` prior to or upon saving the new file, ensuring only the single latest report is maintained in docs/reports/.
<!-- /MARKET -->
- **Automated Dispatch Execution (MANDATORY):**
<!-- MARKET IN -->
  - Persist the complete HTML newsletter to `docs/reports/Daily_Market_Intelligence_<YYYY-MM-DD>.html`.
<!-- /MARKET -->
<!-- MARKET US -->
  - Persist the complete HTML newsletter to `docs/reports/US_Market_Intelligence_<YYYY-MM-DD>.html`.
<!-- /MARKET -->
  - Dispatch the email immediately and automatically via `scripts/send_email.py` using credentials from `.env` (Do NOT prompt the user or request manual confirmation):
    ```bash
<!-- MARKET IN -->
    python3 scripts/send_email.py --subject "Daily Market Pulse | [Session Date] — Nifty [Trend/Status] | 30 Breakouts & 30 Breakdown Alerts" --html-file "docs/reports/Daily_Market_Intelligence_<YYYY-MM-DD>.html" --recipient "rajasekharreddymekala732@gmail.com"
<!-- /MARKET -->
<!-- MARKET US -->
    python3 scripts/send_email.py --subject "Daily US Market Pulse | [Session Date] — S&P [Trend/Status] | 30 Breakouts & 30 Breakdown Alerts" --html-file "docs/reports/US_Market_Intelligence_<YYYY-MM-DD>.html" --recipient "rajasekharreddymekala732@gmail.com"
<!-- /MARKET -->
    ```
  - Confirm successful SMTP execution in the final turn summary.
