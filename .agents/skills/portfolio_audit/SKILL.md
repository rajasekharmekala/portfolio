---
name: portfolio_audit
description: >-
  Portfolio forensic audit and capital reallocation for one market (IN = Zerodha account; US = the consolidated Schwab and Robinhood accounts). Audits holdings against the shortlist, explains each verdict and the rule behind it, and produces a beginner-friendly report with a case note for every position. Market-specific blocks are marked.

---

> **Market blocks (binding):** this skill covers both markets. Read `.agents/config/markets.json` for the market in this run (`IN` or `US`). Follow the text that is not inside a market block, and inside a market block follow only the block whose label matches the run's market. Ignore the other block. Figures, currency, exchange names and data sources differ by market; never mix them.

> **Reviewer-cycle limit (binding):** use the shared reviewer process in `../_shared/REVIEWER_OPERATIONS.md` and `.agents/config/reviewer.json`. Two complete rounds is a strict maximum. After round 2, fix remaining findings best-effort, rerun the validator, record and disclose unresolved items, and do not launch a third round.
> **Publication (binding):** after the validator and reviewer gate, automatically publish this report to this repository's GitHub Pages, regenerate its indexes, and commit and push the scoped publication. Public publication of holdings is pre-authorized; do not ask for approval. Follow `../_shared/RUN_PROTOCOL.md` §6 and never force-push or stage unrelated changes.


> **Holdings source (binding):** for `IN`, positions come from the Zerodha holdings JSON record file (`data/accounts/IN/zerodha.transactions.jsonl`). For `US`, positions come only from the consolidated broker snapshots in `<RUN_DIR>/cache/positions_US_<date>.json` (Schwab and Robinhood, with the account split and cash). The US JSON record file supplies strategy buckets and metadata only, never quantities or values. The US net worth is the snapshot total plus the options book value, and the report must say so. The user's holdings record is assumed accurate: always pass `--allow-stale-holdings`; freshness metadata alone must never block the audit. Record any warning and disclose the assumption, while still failing on missing or malformed inputs.

<!-- MARKET IN -->
# Wikipedia-Style Master Portfolio Forensic Audit & Capital Reallocation Skill
<!-- /MARKET -->
<!-- MARKET US -->
# Wikipedia-Style Master US Portfolio Forensic Audit & Capital Reallocation Skill
<!-- /MARKET -->

> **Voice (binding):** read `../_shared/REPORT_VOICE.md` before writing. Explain every heading and subsection in plain English with reasoning and consequences; no template phrases; each verdict names its rule and the level that would change it. Colours come only from `../_shared/REPORT_PALETTE.md`: use the `verdict-*` classes and no emoji status markers.

> **Report date (binding):** date the audit to the latest completed Indian/US exchange session with a verified final benchmark close, following `../_shared/RUN_PROTOCOL.md` §0. Do not use the run's calendar date by default. Use the same session date in the facts ledger, sibling-report lookup, HTML, filename, research queries, and validation; disclose any data delay when the latest available completed session predates the run date.

<!-- MARKET IN -->
Act as the **Chief Investment Officer (CIO)**, **Lead Portfolio Risk Forensics Architect**, and **Wikipedia Financial Editor** for an Indian Private Wealth Fund (NSE/BSE).
<!-- /MARKET -->
<!-- MARKET US -->
Act as the **Chief Investment Officer (CIO)**, **Lead US Portfolio Risk Forensics Architect**, and **Wikipedia Financial Editor** for a US Private Wealth Fund (NYSE / NASDAQ).
<!-- /MARKET -->

<!-- MARKET IN -->
Execute the **Master Portfolio Audit & Capital Reallocation Blueprint**:
<!-- /MARKET -->
<!-- MARKET US -->
Execute the **Master US Portfolio Audit & Capital Reallocation Blueprint**:
<!-- /MARKET -->
1. Conduct an exhaustive, adversarial, multi-agent portfolio forensic audit and capital reallocation analysis.
2. Render the final output as a standalone, self-contained HTML document in authentic **Wikipedia Design System** (NPOV encyclopedic tone, floating infobox, wikitables, footnotes, verified citations).
<!-- MARKET IN -->
3. Maintain and synchronize the deliverable in Google Drive at **`docs/reports/Portfolio_Audit_<YYYY-MM-DD>.html`**, where the date is the resolved latest completed market session (not necessarily the run date). Maintain strictly the single latest generated report and display that session date on the page.
<!-- /MARKET -->
<!-- MARKET US -->
3. Maintain and synchronize the deliverable in Google Drive at **`docs/reports/US_Portfolio_Audit_<YYYY-MM-DD>.html`**, where the date is the resolved latest completed market session (not necessarily the run date). Maintain strictly the single latest generated report and display that session date on the page.
<!-- /MARKET -->
4. Transmit the complete deliverable via Gmail to **`rajasekharreddymekala732@gmail.com`**.

---

### EDITORIAL, DATA-COMPLETENESS & COHERENCE STANDARD (MANDATORY — READ FIRST):

Before anything else, read `.agents/skills/_shared/REPORT_EDITORIAL_STANDARD.md` in full; it is binding and overrides any terser skeleton text below. Non-negotiables:

<!-- MARKET IN -->
1. **Data first:** build it in this run (reuse of another run's ledger is not allowed) for the latest completed market session resolved under `../_shared/RUN_PROTOCOL.md` §0: `.venv/bin/python scripts/market_facts.py --market IN --date <session> --screen nifty500 --run-dir "<RUN_DIR>"`. Every CMP, DMA, RSI, ATR, stage, regime label, breadth figure and sector quadrant in every chapter comes from `<RUN_DIR>/cache/facts_IN_<date>.json`. If the JSON record file's `Current Price` differs from the ledger close, value positions at the ledger close and state the JSON record file price once in the methodology note. Never write a technical claim ("Stage 2", "above rising 50-DMA", "support at X") that the ledger does not back. `N/A` only after the ledger, the mandatory duck-duck-go MCP research pass (`search` + `fetch_content`, protocol in section 6 of the standard; results in `<RUN_DIR>/cache/research_IN_<date>.json`) and a second source all fail (max 5% of cells). Results dates, promoter pledge, catalysts behind every EXIT/TRIM and any market-flow figure you quote come from that pass; use precise date-stamped queries, read the fetched page, and cite URL + as-of date.
2. **Write it as a book for a beginner who owns this portfolio (section 3 and blueprint 7B of the standard):** append `.agents/skills/_shared/report_base.css and book_components.css` to the report's `<style>`; open with a 450+ word `primer` (what the audit is, the three independent analysts, every action label and the exact rule that triggers it, every key term with an everyday analogy), then a 250-400 word lede stating the portfolio's condition and the decision; every chapter opens with a 200+ word essay and closes with a "what this means for you" paragraph; every table has a `howto` before it and a 120+ word `takeaway` after it; **a `casenote` for every holding** (what the company does, why you own it, the numbers and what they mean, the verdict and the rule behind it, what would change it, with prices), every greenfield buy and every notable exclusion; worked `example`s in rupees (position sizing, the trim arithmetic, the swap test); a `triggers` if/then block per chapter; a money-at-risk table, a step-by-step cash waterfall and scenario analysis in Chapter 5; orders in Chapter 6 written as plain-English instructions with trigger, expiry and what to do if not filled; a new Chapter 7 (rulebook and monitoring); glossary and methodology/data-gaps note. If a recommendation contradicts a skill rule (for example trimming a super-performer the rule says not to trim into strength), state the rule and either follow it or justify the override with numbers. Target 12,000+ words; the validator floor is 9,000.
3. **One story:** read the same-date `Daily_Market_Intelligence_*.html` first. Chapter 1 restates its regime label and sector map verbatim; Chapter 2 verdicts cite that regime; Chapter 3 uses the same gates and stages; Chapter 4 explains every displacement or non-displacement; Chapter 5 totals reconcile to the rupee with Chapters 2 and 3; Chapter 6 orders are exactly the Chapter 5 deltas. A held name on the market report's Bull or Bear list must be addressed explicitly.
4. **Gate:** `.venv/bin/python scripts/validate_report.py --report docs/reports/Portfolio_Audit_<date>.html --kind portfolio_audit --facts <RUN_DIR>/cache/facts_IN_<date>.json` must print `PASS` before the Drive save and email. The skeleton below is scaffolding only: every `{{NARRATIVE_*}}` slot, and an intro `<p>` before and takeaway `<p>` after every table, must be written as full prose.
<!-- /MARKET -->
<!-- MARKET US -->
1. **Data first:** Always generate a fresh facts ledger from scratch for the latest completed market session resolved under `../_shared/RUN_PROTOCOL.md` §0: `.venv/bin/python scripts/market_facts.py --market US --date <session> --screen sp1500 --run-dir "<RUN_DIR>"`. Every price, DMA, RSI, ATR, stage, regime label, breadth figure, Treasury yield and sector quadrant in every chapter comes from `<RUN_DIR>/cache/facts_US_<date>.json`. If the JSON record file's `Current Price` differs from the ledger close, value positions at the ledger close and state the JSON record file price once in the methodology note. Never write a technical claim ("Stage 2", "above rising 50-DMA", "support at X") that the ledger does not back. `N/A` only after the ledger, the mandatory duck-duck-go MCP research pass (`search` + `fetch_content`, protocol in section 6 of the standard; results in `<RUN_DIR>/cache/research_US_<date>.json`) and a second source all fail (max 5% of cells); for the greenfield gates (ROIC, CFO/NI, net debt/EBITDA) pull SEC companyfacts / Finviz pages through that pass rather than blanket-marking every candidate N/A. Earnings dates, catalysts behind every EXIT/TRIM and any market-flow figure you quote come from the same pass; use precise date-stamped queries, read the fetched page, and cite URL + as-of date.
2. **Write it as a book for a beginner who owns this portfolio (section 3 and blueprint 7B of the standard):** append `.agents/skills/_shared/report_base.css and book_components.css` to the report's `<style>`; open with a 450+ word `primer` (what the audit is, the three independent analysts, every action label and the exact rule that triggers it, every key term with an everyday analogy including daily-reset leveraged ETFs and LEAPS), then a 250-400 word lede stating the portfolio's condition and the decision; every chapter opens with a 200+ word essay and closes with a "what this means for you" paragraph; every table has a `howto` before it and a 120+ word `takeaway` after it; **a `casenote` for every holding, every leveraged ETF and every LEAPS position** (what it is, why you own it, the numbers and what they mean, the verdict and the rule behind it, what would change it, with prices), every greenfield buy and every notable exclusion; worked `example`s in dollars (position sizing, the trim arithmetic, the swap test, how daily-reset leverage decays); a `triggers` if/then block per chapter; a money-at-risk table, a step-by-step cash waterfall and scenario analysis in Chapter 5; orders in Chapter 6 written as plain-English instructions with trigger, expiry and what to do if not filled (Schwab and Robinhood steps for stop and limit orders); a new Chapter 7 (rulebook and monitoring); glossary and methodology/data-gaps note. If a recommendation contradicts a skill rule, state the rule and either follow it or justify the override with numbers. Target 12,000+ words; the validator floor is 9,000.
3. **One story:** read the same-date `US_Market_Intelligence_*.html` first. Chapter 1 restates its regime label and sector map verbatim; Chapter 2 verdicts cite that regime; Chapter 3 uses the same gates and stages; Chapter 4 explains every displacement or non-displacement; Chapter 5 totals reconcile to the dollar with Chapters 2 and 3; Chapter 6 orders are exactly the Chapter 5 deltas. A held name on the market report's Bull or Bear list must be addressed explicitly.
4. **Gate:** `.venv/bin/python scripts/validate_report.py --report docs/reports/US_Portfolio_Audit_<date>.html --kind portfolio_audit --facts <RUN_DIR>/cache/facts_US_<date>.json` must print `PASS` before the Drive save and email. The skeleton below is scaffolding only: every `{{NARRATIVE_*}}` slot, and an intro `<p>` before and takeaway `<p>` after every table, must be written as full prose.
<!-- /MARKET -->

---

### MANDATORY ZERO-HALLUCINATION & DATA ACCURACY RULES:

<!-- MARKET IN -->
1. **NO FABRICATION OF POSITIONS:** Ingest holdings strictly from `data/accounts/IN/zerodha.transactions.jsonl` and vetted shortlist candidates strictly from `data/shortlist/IN.json`.
2. **MATHEMATICAL PRECISION:** All table percentages must sum to 100.0% ($\sum \text{Allocated Wt} + \text{Cash Buffer} = 100.0\%$). Capital values must reconcile exactly to the total account net worth.
3. **MANDATORY USE OF `N/A`:** If any specific metric (e.g. historical delivery volume or pledge) is not deterministically verified after `scripts/market_facts.py`, an alternate source and web search have all failed, output **`N/A`** with a specific reason (never for data price history can supply).
4. **MANDATORY TRADINGVIEW & SCREENER LINKS:**
<!-- /MARKET -->
<!-- MARKET US -->
1. **NO FABRICATION OF POSITIONS:** Ingest holdings strictly from `data/metadata/symbols.json` and vetted shortlist candidates strictly from `data/shortlist/US.json`.
2. **MATHEMATICAL PRECISION:** All table percentages must sum to 100.0% ($\sum \text{Allocated Wt} + \text{Cash Buffer} = 100.0\%$). Capital values in USD ($) must reconcile exactly to the total account net worth.
3. **MANDATORY USE OF `N/A`:** If any specific metric (e.g. historical short interest, institutional dark pool ratio, or insider cluster trades) is not deterministically verified after `scripts/market_facts.py`, an alternate source and web search have all failed, output **`N/A`** with a specific reason (never for data price history can supply).
4. **MANDATORY TRADINGVIEW & FINVIZ LINKS:**
<!-- /MARKET -->
   - In all data tables, format the Security / Symbol column with clickable sub-links:
<!-- MARKET IN -->
     `<b>{SYMBOL}</b><br><span style="font-size: 11px;"><a href="https://www.tradingview.com/chart/?symbol=NSE%3A{SYMBOL}" style="color: #0645ad;">Chart</a> • <a href="https://www.screener.in/company/{SYMBOL}/" style="color: #14532d;">Screener</a></span>`
<!-- /MARKET -->
<!-- MARKET US -->
     `<b>{SYMBOL}</b><br><span style="font-size: 11px;"><a href="https://www.tradingview.com/chart/?symbol=NASDAQ%3A{SYMBOL}" style="color: #0645ad;">Chart</a> • <a href="https://finviz.com/quote.ashx?t={SYMBOL}" style="color: #14532d;">Finviz</a></span>`
<!-- /MARKET -->
5. **MANDATORY ZERO-OMISSION INTEGRITY:** Every single chapter (Chapters 1 through 6) and every table must be completely rendered without truncation or placeholder dots (`...`).
6. **MANDATORY AUTOMATED EMAIL DISPATCH:**
   - Automated dispatch of the generated briefing to `rajasekharreddymekala732@gmail.com` via `scripts/send_email.py` is a **STRICT, MANDATORY PIPELINE REQUIREMENT**.
   - Programmatically run `send_email.py` in the terminal as the final automated step without asking manual confirmation.
7. **MANDATORY ONE-OFF SCRIPT LIFECYCLE & CACHE HYGIENE:**
   - Scratch code lives only in `<RUN_DIR>` and is deleted with it (RUN_PROTOCOL sections 1 and 5).
   - **Run directory:** nothing from earlier runs is read. Cleanup follows `../_shared/RUN_PROTOCOL.md` section 5. Repository scripts are never deleted.
   - Permanent repository scripts (never delete): `scripts/send_email.py`, `scripts/build_dossier_portal.py`, `scripts/serve_blogs.py`, `scripts/market_facts.py`, `scripts/validate_report.py`.

---

### DECOUPLED MULTI-AGENT ARCHITECTURE (ZERO-BIAS EXECUTION):

To eliminate incumbent holding bias, the audit is synthesized across 3 decoupled specialist subagents and 1 master CIO orchestrator:

<!-- MARKET IN -->
#### 1. Subagent 1: `macro_regime_specialist` (Independent Market Intelligence Agent)
- Evaluates Nifty 50 regime, India VIX, FII flows, and 4-quadrant sector rotation to establish the macro portfolio posture.
<!-- /MARKET -->
<!-- MARKET US -->
#### 1. Subagent 1: `us_macro_regime_specialist` (Independent Market Intelligence Agent)
- Evaluates S&P 500 / Nasdaq 100 regime, CBOE VIX, US 10Y/2Y Yields, and 11-group sector rotation to establish the macro portfolio posture.
<!-- /MARKET -->

<!-- MARKET IN -->
#### 2. Subagent 2: `forensic_holdings_auditor` (Adversarial Holding-Risk & Defense Agent)
- Evaluates every position in `data/accounts/IN/zerodha.transactions.jsonl` against quantitative gating criteria (moving average breakdown, 14-day RSI divergence, earnings deceleration, promoter pledges, dead money >6 months, binary earnings event risks).
- Outputs the **Active Holdings Extraction & Capital Liberation Ladder (Rank 1 to N)** categorizing holdings into `EXIT (Immediate)`, `TRIM (Climax/Over-concentration)`, `HOLD / HARD STOP`, `HOLD / TRAIL`, and quantifying exact capital liberated (₹ and %).
<!-- /MARKET -->
<!-- MARKET US -->
#### 2. Subagent 2: `us_forensic_holdings_auditor` (Adversarial Holding-Risk & Defense Agent)
- Evaluates every position in `data/metadata/symbols.json` against quantitative gating criteria (moving average breakdown, 14-day RSI divergence, SBC dilution acceleration, dead money >6 months, binary earnings event risks).
- Outputs the **Active Holdings Extraction & Capital Liberation Ladder (Rank 1 to N)** categorizing holdings into `EXIT (Immediate)`, `TRIM (Climax/Over-concentration)`, `HOLD / HARD STOP`, `HOLD / TRAIL`, and quantifying exact capital liberated ($ and %).
<!-- /MARKET -->

<!-- MARKET IN -->
#### 3. Subagent 3: `shortlist_capital_allocator` (Unconstrained Greenfield Stock Picker Agent)
- **Absolute Zero-Holding-Bias Mandate:** Operates with **NO data about current holdings, cost bases, or unrealized P&L**. It solves: *"If given ₹Total Net Worth in 100% pure cash today, what is the optimal capital allocation across the vetted shortlist?"*
<!-- /MARKET -->
<!-- MARKET US -->
#### 3. Subagent 3: `us_shortlist_capital_allocator` (Unconstrained Greenfield Stock Picker Agent)
- **Absolute Zero-Holding-Bias Mandate:** Operates with **NO data about current holdings, cost bases, or unrealized P&L**. It solves: *"If given $Total Net Worth in 100% pure cash today, what is the optimal capital allocation across the vetted US shortlist?"*
<!-- /MARKET -->
- Selectively concentrates capital into top 6–12 highest-conviction ideas at support, assigning **0.0% weight (PASS)** to extended or lower-conviction names.

#### 4. Master Orchestrator / CIO Reconciler
- Ingests outputs from Subagents 1, 2, and 3.
- Builds Chapter 1 (Macro Alignment), Chapter 2 (Holdings Extraction Ladder), Chapter 3 (Greenfield Target Portfolio), Chapter 4 (Shortlist Strategy Funnel), Chapter 5 (Master Capital Reallocation & Money Bridge), and Chapter 6 (3-Phase Actionable Execution Orders).
- Formats in authentic Wikipedia Design System, syncs Google Drive, and dispatches via Gmail.

---

<!-- MARKET IN -->
### STRATEGY BUCKET MANDATES & CAP ALLOCATION:
<!-- /MARKET -->
<!-- MARKET US -->
### STRATEGY BUCKET MANDATES & CAP ALLOCATION (US EQUITIES):
<!-- /MARKET -->

<!-- MARKET IN -->
- **CORE ALPHA (Long-Term Compounding Book — Target 30%–40% of Net Worth):**
  - High ROCE (>18%), strong moat, clean balance sheet (D/E < 0.5), secular runway (>15% 3-year sales CAGR). Horizon: 1 to 3+ years.
- **TACTICAL MOMENTUM (Stage 2 Breakout & Satellite Growth — Target 50%–65% of Net Worth):**
  - Active Stage 2 markup, trading above rising 20/50/200 DMAs, RS Rating > 75 vs Nifty 500, volume expansion (>1.8x 20-DMA). Horizon: 3 weeks to 6 months.
- **CASH & LIQUID MARGIN BUFFER (Risk Management & Dry Powder — Target 5%–10% of Net Worth):**
  - Protects against market drawdowns and seizes high-asymmetry opportunistic pullbacks.
<!-- /MARKET -->
<!-- MARKET US -->
- **CORE ALPHA (Long-Term Compounding Book — Target 35%–45% of Net Worth):**
  - High ROIC (>16%), wide moat, strong FCF conversion, secular tech/industrial tailwinds. Horizon: 1 to 3+ years.
- **TACTICAL MOMENTUM (Stage 2 Breakout & High Growth — Target 40%–55% of Net Worth):**
  - Active Stage 2 markup, trading above rising 20/50/200 DMAs, RS Rating > 75 vs S&P 500, high revenue acceleration. Horizon: 3 weeks to 6 months.
- **LEVERAGED SATELLITE (High-Beta Structural Growth / Options Proxies — Target 5%–15% of Net Worth):**
  - Hyper-growth or leveraged momentum instruments with strict asymmetric stops.
- **CASH & DRY POWDER BUFFER (Target 5%–10% of Net Worth):**
  - Hedging and opportunistic dip deployment.
<!-- /MARKET -->

---

### DETERMINISTIC DECISION RULES & ACTION LABELS:

1. **Stop Methodology (per `.agents/config/scoring.json` `stop_placement`):**
   - Core Alpha: Nearest structural invalidation support — $\text{Stop} = \min(\text{20d Swing Low}, \text{50-DMA}) - 1.0 \times \text{ATR}(14)$ for Stage 2 uptrends, or $\text{63d Base Low} - 1.0 \times \text{ATR}(14)$ for Stage 1 / turnaround bases (do not mechanically use a distant 200-DMA in a Stage 2 advance).
   - Tactical Momentum: $\text{Stop} = \min(\text{20d Swing Low}, \text{20/50-DMA}) - 0.5 \times \text{ATR}(14)$.
2. **Targets & Asymmetry (per `.agents/config/scoring.json` `asymmetry_floor`):** Target must be mathematically anchored to 12–24M Forward EPS $\times$ 3Y Median P/E, DCF, or Technical Base Measured-Move. Asymmetry Ratio must be $\ge 2.5:1$ Tactical / Turnaround, $\ge 2.0:1$ Core (at CMP or at the planned limit-order Entry Zone).
3. **Concentration, Risk-Unit Sizing & Letting Winners Run (per `.agents/config/scoring.json`):**
   - Initial entries are sized by **Risk-Unit Sizing (Portfolio Heat)**: `weight_pct = min(tier_max_pct, risk_budget_bps / stop_distance_pct)` with an initial cost-basis cap of `10.0%` and a standard single-stock cap of `15.0%` (`position_sizing.hard_cap_pct`). Total portfolio heat across open stops is capped at `12.0%`.
   - **The Let-Winners-Run Rule (`runaway_winner_cap_pct: 22%`):** Never mechanically trim a Stage 2 winner with intact fundamentals and stable/rising earnings revisions solely because RSI > 70 or its appreciated weight crossed `15.0%`. Allow appreciated weight up to `22.0%` while trailing the stop to the rising 21-day EMA or 50-day SMA.
4. **Effective Market Exposure & Hidden Overlap (`portfolio_risk_and_overlap`):**
   - In Chapter 1 and Chapter 2, include and explain in plain English the two portfolio-level risk readings computed in `<RUN_DIR>/cache/positions_<MKT>_<date>.json` (`portfolio_risk_and_overlap`):
     - **"What your portfolio really behaves like" (`plain_english_exposure`):** Total beta- and leverage-adjusted market exposure (`effective_market_exposure_pct`) and how much a 1% index drop moves the portfolio in dollars/rupees.
     - **"Which holdings move in lockstep" (`plain_english_overlap`):** Any pair or cluster of holdings (`lockstep_clusters`, `high_correlation_pairs`) with 1-year daily return correlation $\ge 0.65$ that acts as one combined bet.
5. **The 3-Condition Swap Decision Framework:**
   - Condition 1: Holding triggered exit or trim.
   - Condition 2: Challenger passed 100% of gates and is strictly `AT_SUPPORT` ($\le 0.5\times \text{ATR}$).
<!-- MARKET IN -->
   - Condition 3: Challenger Asymmetry exceeds Holding Asymmetry by $\ge 1.5\times$, clearing tax and friction.
<!-- /MARKET -->
<!-- MARKET US -->
   - Condition 3: Challenger Asymmetry exceeds Holding Asymmetry by $\ge 1.5\times$, clearing capital gains friction.
<!-- /MARKET -->
5. **Action Labels:**
   - Holding Actions: `HOLD / TRAIL`, `HOLD / HARD STOP`, `TRIM`, `EXIT`, `NO TRADE / WATCH`.
   - Holding Verdicts: `KEEP_COMPOUNDING`, `ACCUMULATE_ON_DIP`, `TRIM_PROFIT_BOOKING`, `REPLACE_UNDERPERFORMER`.
   - Pipeline Verdicts: `IMMEDIATE_BUY`, `ACCUMULATE_ON_DIP`, `WAIT_FOR_SUPPORT`, `REJECTED`.

---

### DESIGN & ASSEMBLY (DELEGATED TO `scripts/assemble_report.py`):

Write only the HTML body fragments (`<h1>`, `<dl class="key-figures">`, `<table class="infobox">`, and the chapter sections). Never write a `<head>`, `<style>`, or custom CSS block—`scripts/assemble_report.py` injects the shared Research Desk stylesheet (`REPORT_PALETTE.md`, `report_base.css`, `book_components.css`, `report_desk.css`), wraps tables in `.table-wrap`, applies first-use `<dfn>` glossary definitions, and embeds the Pacific generation timestamp.

---

### REQUIRED 7-CHAPTER BRIEFING STRUCTURE (the skeleton shows Chapters 1-6; add Chapter 7 "Rulebook & Monitoring" and the Start-here primer per blueprint 7B of the standard):

```html
<!-- SKELETON NOTE: write only the body (the section fragments). Pass the assembled body to scripts/assemble_report.py --market <MKT> --kind report --workflow "Portfolio audit" --as-of <SESSION_DATE>. -->
<div class="clearfix">

<!-- FLOATED INFOBOX: EXECUTIVE PORTFOLIO SNAPSHOT -->
<table class="infobox" role="presentation">
<!-- MARKET IN -->
  <caption>Portfolio Executive Snapshot</caption>
<!-- /MARKET -->
<!-- MARKET US -->
  <caption>US Portfolio Executive Snapshot</caption>
<!-- /MARKET -->
  <tr><th colspan="2" class="infobox-header">Session Date: {{SESSION_DATE}}</th></tr>
<!-- MARKET IN -->
  <tr><th>Total Net Worth</th><td><strong>₹{{NET_WORTH}}</strong></td></tr>
  <tr><th>Invested Equities</th><td>₹{{EQUITIES_VALUE}} ({{EQUITIES_WT}}%)</td></tr>
  <tr><th>Cash / Margin Buffer</th><td>₹{{CASH_VALUE}} ({{CASH_WT}}%)</td></tr>
  <tr><th>Total Cost Basis</th><td>₹{{COST_BASIS}}</td></tr>
  <tr><th>Total Unrealized P&amp;L</th><td>₹{{TOTAL_PNL}} ({{TOTAL_PNL_PCT}}%)</td></tr>
  <tr><th>Core Alpha Allocation</th><td>{{CORE_WT}}% (Target: 30–40%)</td></tr>
  <tr><th>Tactical Momentum</th><td>{{TACTICAL_WT}}% (Target: 50–65%)</td></tr>
<!-- /MARKET -->
<!-- MARKET US -->
  <tr><th>Total Net Worth</th><td><strong>${{NET_WORTH}}</strong></td></tr>
  <tr><th>Invested Equities</th><td>${{EQUITIES_VALUE}} ({{EQUITIES_WT}}%)</td></tr>
  <tr><th>Cash / Margin Buffer</th><td>${{CASH_VALUE}} ({{CASH_WT}}%)</td></tr>
  <tr><th>Total Cost Basis</th><td>${{COST_BASIS}}</td></tr>
  <tr><th>Total Unrealized P&amp;L</th><td>${{TOTAL_PNL}} ({{TOTAL_PNL_PCT}}%)</td></tr>
  <tr><th>Core Alpha Allocation</th><td>{{CORE_WT}}% (Target: 35–45%)</td></tr>
  <tr><th>Tactical Momentum</th><td>{{TACTICAL_WT}}% (Target: 40–55%)</td></tr>
  <tr><th>Leveraged Satellite</th><td>{{LEVERAGED_WT}}% (Target: 5–15%)</td></tr>
<!-- /MARKET -->
  <tr><th>Top 3 Concentration</th><td>{{TOP3_WT}}% of Portfolio</td></tr>
  <tr><th>Portfolio Beta / RSI</th><td>Beta: {{PORTFOLIO_BETA}} &bull; Avg RSI: {{PORTFOLIO_RSI}}</td></tr>
</table>

<!-- CHAPTER 1: MACRO & SECTOR REGIME ALIGNMENT -->
<!-- MARKET IN -->
<h2 id="chapter1">Chapter 1: Macro &amp; Sector Regime Alignment</h2>
<!-- /MARKET -->
<!-- MARKET US -->
<h2 id="chapter1">Chapter 1: US Macro &amp; Sector Regime Alignment</h2>
<!-- /MARKET -->
<p>
  {{NARRATIVE_LEDE_AND_CH1_OPENING}}<!-- lede 150+ words (portfolio condition, three numbers that matter, the decision, chapter map), then 60+ words restating the market report's regime label and what it implies for this book. -->
</p>
<div class="table-wrapper">
<table class="wikitable">
  <thead>
    <tr>
      <th>Macro Dimension</th>
      <th>Current Regime State</th>
      <th>Institutional Significance</th>
      <th>Portfolio Mandate</th>
    </tr>
  </thead>
  <tbody>
    <tr>
<!-- MARKET IN -->
      <td><strong>Market Regime</strong></td>
      <td>{{MARKET_REGIME}} (Nifty: {{NIFTY_CLOSE}})</td>
<!-- /MARKET -->
<!-- MARKET US -->
      <td><strong>S&amp;P 500 / Nasdaq Regime</strong></td>
      <td>{{MARKET_REGIME}} (SPY: ${{SPY_CLOSE}}, QQQ: ${{QQQ_CLOSE}})</td>
<!-- /MARKET -->
      <td>Stage 2 Trend Structure intact above 50/200-DMA</td>
      <td>Maintain full long exposure, deploy pullbacks at support</td>
    </tr>
    <tr>
<!-- MARKET IN -->
      <td><strong>Volatility Regime</strong></td>
      <td>India VIX: {{VIX_VALUE}}</td>
<!-- /MARKET -->
<!-- MARKET US -->
      <td><strong>CBOE VIX Regime</strong></td>
      <td>VIX: {{VIX_VALUE}}</td>
<!-- /MARKET -->
      <td>{{VIX_REGIME}} regime</td>
      <td>{{VIX_PORTFOLIO_RULE}}</td>
    </tr>
    <tr>
      <td><strong>Sector Rotation Bias</strong></td>
      <td>Leading: {{LEADING_SECTORS}}</td>
      <td>Institutional rotation out of {{LAGGING_SECTORS}} into {{LEADING_SECTORS}}</td>
      <td>Overweight top-quadrant leaders, trim lagging laggards</td>
    </tr>
  </tbody>
</table>
</div>

<!-- CHAPTER 2: ACTIVE PORTFOLIO HEALTH & RISK AUDIT -->
<!-- MARKET IN -->
<h2 id="chapter2">Chapter 2: Active Portfolio Health &amp; Concentration Risk Audit</h2>
<!-- /MARKET -->
<!-- MARKET US -->
<h2 id="chapter2">Chapter 2: Active US Portfolio Health &amp; Concentration Risk Audit</h2>
<!-- /MARKET -->

<div class="callout-box">
  <strong>Super-Performer Momentum Exception:</strong> Top winning compounders exceeding the 20.0% concentration cap with intact Stage 2 momentum (above rising 20-DMA, RS &gt; 80) are protected from mechanical trimming. Stops are ratcheted to the 21-day EMA.
</div>

<h3>2.1 Active Holdings Extraction &amp; Capital Liberation Ladder (Rank 1 to N)</h3>
<div class="table-wrapper">
<table class="wikitable">
  <thead>
    <tr>
      <th>Rank</th>
      <th>Security &amp; Subsector</th>
      <th class="num">Net-Worth Wt (%)</th>
<!-- MARKET IN -->
      <th class="num">P&amp;L (₹ / %)</th>
<!-- /MARKET -->
<!-- MARKET US -->
      <th class="num">P&amp;L ($ / %)</th>
<!-- /MARKET -->
      <th>1D / 1W / 2W %</th>
      <th>RSI &amp; Stage</th>
      <th>Liberation Rationale</th>
      <th>Action Verdict</th>
<!-- MARKET IN -->
      <th class="num">Capital Liberated (₹)</th>
<!-- /MARKET -->
<!-- MARKET US -->
      <th class="num">Capital Liberated ($)</th>
<!-- /MARKET -->
    </tr>
  </thead>
  <tbody>
<!-- MARKET IN -->
    <!-- All active holdings ranked from Priority 1 (Exit/Trim) to Protected Compounders -->
<!-- /MARKET -->
<!-- MARKET US -->
    <!-- All active US holdings ranked from Priority 1 (Exit/Trim) to Protected Compounders -->
<!-- /MARKET -->
  </tbody>
</table>
</div>

<!-- MARKET IN -->
<h3>2.2 Holdings Forensic Health Matrix</h3>
<!-- /MARKET -->
<!-- MARKET US -->
<h3>2.2 US Holdings Forensic Health Matrix</h3>
<!-- /MARKET -->
<div class="table-wrapper">
<table class="wikitable">
  <thead>
    <tr>
      <th>Security</th>
      <th>Strategy Bucket</th>
<!-- MARKET IN -->
      <th class="num">Cost vs CMP (₹)</th>
      <th>ROCE / D/E / CFO</th>
<!-- /MARKET -->
<!-- MARKET US -->
      <th class="num">Cost vs CMP ($)</th>
      <th>ROIC / FCF Margin / SBC</th>
<!-- /MARKET -->
      <th>Technical Structure</th>
<!-- MARKET IN -->
      <th>Invalidation Stop (₹)</th>
<!-- /MARKET -->
<!-- MARKET US -->
      <th>Invalidation Stop ($)</th>
<!-- /MARKET -->
      <th>Forensic Verdict</th>
    </tr>
  </thead>
  <tbody>
<!-- MARKET IN -->
    <!-- Forensic audit rows for every holding -->
<!-- /MARKET -->
<!-- MARKET US -->
    <!-- Forensic audit rows for every US holding -->
<!-- /MARKET -->
  </tbody>
</table>
</div>

<!-- CHAPTER 3: GREENFIELD UNCONSTRAINED SHORTLIST ALLOCATION -->
<h2 id="chapter3">Chapter 3: Greenfield Unconstrained Shortlist Capital Allocation (Zero-Bias Stock Picker)</h2>
<div class="callout-box">
<!-- MARKET IN -->
  <strong>Zero-Holding-Bias Framework:</strong> This allocation is generated by the dedicated <code>shortlist_capital_allocator</code> agent operating with 100% independence from incumbent holdings. If deploying ₹{{NET_WORTH}} in pure cash across the vetted shortlist candidates today, this table reflects the optimal conviction-weighted capital distribution.
<!-- /MARKET -->
<!-- MARKET US -->
  <strong>Zero-Holding-Bias Framework:</strong> This allocation is generated by the dedicated <code>us_shortlist_capital_allocator</code> agent operating with 100% independence from incumbent holdings. If deploying ${{NET_WORTH}} in pure cash across the vetted shortlist candidates today, this table reflects the optimal conviction-weighted capital distribution.
<!-- /MARKET -->
</div>

<div class="table-wrapper">
<table class="wikitable">
  <thead>
    <tr>
      <th>Rank</th>
      <th>Security &amp; Links</th>
      <th>Bucket</th>
      <th>Conviction Tier</th>
      <th class="num">Target Wt (%)</th>
<!-- MARKET IN -->
      <th class="num">Capital (₹)</th>
      <th>Entry Zone (₹)</th>
      <th>Stop Loss (₹)</th>
      <th>Base Target (₹)</th>
<!-- /MARKET -->
<!-- MARKET US -->
      <th class="num">Capital ($)</th>
      <th>Entry Zone ($)</th>
      <th>Stop Loss ($)</th>
      <th>Base Target ($)</th>
<!-- /MARKET -->
      <th>Asymmetry (R:R)</th>
      <th>Catalyst &amp; Moat</th>
    </tr>
  </thead>
  <tbody>
<!-- MARKET IN -->
    <!-- Top conviction shortlisted ideas -->
<!-- /MARKET -->
<!-- MARKET US -->
    <!-- Top conviction shortlisted US ideas -->
<!-- /MARKET -->
  </tbody>
  <tfoot>
    <tr>
      <td colspan="4" style="text-align: right;">Total Active Equities Deployed:</td>
      <td class="num">{{TOTAL_TARGET_EQUITIES_WT}}%</td>
<!-- MARKET IN -->
      <td class="num">₹{{TOTAL_TARGET_EQUITIES_CAP}}</td>
<!-- /MARKET -->
<!-- MARKET US -->
      <td class="num">${{TOTAL_TARGET_EQUITIES_CAP}}</td>
<!-- /MARKET -->
      <td colspan="5"></td>
    </tr>
    <tr>
      <td colspan="4" style="text-align: right;">Dry Powder Cash Reserve:</td>
      <td class="num">{{TARGET_CASH_WT}}%</td>
<!-- MARKET IN -->
      <td class="num">₹{{TARGET_CASH_CAP}}</td>
<!-- /MARKET -->
<!-- MARKET US -->
      <td class="num">${{TARGET_CASH_CAP}}</td>
<!-- /MARKET -->
      <td colspan="5"></td>
    </tr>
  </tfoot>
</table>
</div>

<!-- CHAPTER 4: SHORTLIST STRATEGY FUNNEL -->
<!-- MARKET IN -->
<h2 id="chapter4">Chapter 4: Shortlist Strategy Funnel &amp; Deep Underwriting Pipeline</h2>
<!-- /MARKET -->
<!-- MARKET US -->
<h2 id="chapter4">Chapter 4: US Shortlist Strategy Funnel &amp; Deep Underwriting Pipeline</h2>
<!-- /MARKET -->
<p>{{NARRATIVE_CH4_FUNNEL}}</p><!-- how each candidate fared against the 3 layers, which displaced which holding and why, which were rejected and the specific gate they failed. -->
<div class="table-wrapper">
<table class="wikitable">
  <thead>
    <tr>
      <th>Security</th>
      <th>Strategy Bucket</th>
      <th>Financial Gate</th>
      <th>Technical Gate</th>
      <th>Asymmetry Gate</th>
      <th>Operational KPIs</th>
      <th>Entry Posture</th>
      <th>Funnel Verdict</th>
    </tr>
  </thead>
  <tbody>
<!-- MARKET IN -->
    <!-- All shortlisted candidates evaluated -->
<!-- /MARKET -->
<!-- MARKET US -->
    <!-- All shortlisted US candidates evaluated -->
<!-- /MARKET -->
  </tbody>
</table>
</div>

<!-- CHAPTER 5: MASTER CAPITAL REALLOCATION (MONEY BRIDGE) -->
<h2 id="chapter5">Chapter 5: Master Capital Reallocation &amp; Money Bridge (Holding vs Target)</h2>
<p>{{NARRATIVE_CH5_BRIDGE}}</p><!-- walk the reader through the bridge in words: capital freed by sells/trims, capital deployed, cash left, and proof the totals reconcile to Chapters 2 and 3. -->
<div class="table-wrapper">
<table class="wikitable">
  <thead>
    <tr>
      <th>Security / Asset</th>
<!-- MARKET IN -->
      <th class="num">Current Value (₹)</th>
<!-- /MARKET -->
<!-- MARKET US -->
      <th class="num">Current Value ($)</th>
<!-- /MARKET -->
      <th class="num">Current Wt (%)</th>
<!-- MARKET IN -->
      <th class="num">Target Value (₹)</th>
<!-- /MARKET -->
<!-- MARKET US -->
      <th class="num">Target Value ($)</th>
<!-- /MARKET -->
      <th class="num">Target Wt (%)</th>
<!-- MARKET IN -->
      <th class="num">Variance (₹)</th>
<!-- /MARKET -->
<!-- MARKET US -->
      <th class="num">Variance ($)</th>
<!-- /MARKET -->
      <th class="num">Variance (%)</th>
      <th>Action Mandate</th>
    </tr>
  </thead>
  <tbody>
    <!-- Every position (Holdings + New Buys + Cash) -->
  </tbody>
  <tfoot>
    <tr>
      <td><strong>Total Portfolio</strong></td>
<!-- MARKET IN -->
      <td class="num">₹{{NET_WORTH}}</td>
<!-- /MARKET -->
<!-- MARKET US -->
      <td class="num">${{NET_WORTH}}</td>
<!-- /MARKET -->
      <td class="num">100.0%</td>
<!-- MARKET IN -->
      <td class="num">₹{{NET_WORTH}}</td>
<!-- /MARKET -->
<!-- MARKET US -->
      <td class="num">${{NET_WORTH}}</td>
<!-- /MARKET -->
      <td class="num">100.0%</td>
<!-- MARKET IN -->
      <td class="num">₹0</td>
<!-- /MARKET -->
<!-- MARKET US -->
      <td class="num">$0</td>
<!-- /MARKET -->
      <td class="num">0.0%</td>
      <td><strong>Rebalanced</strong></td>
    </tr>
  </tfoot>
</table>
</div>

<!-- CHAPTER 6: 3-PHASE ACTIONABLE EXECUTION ORDERS -->
<h2 id="chapter6">Chapter 6: 3-Phase Actionable Execution Orders</h2>

<h3>Phase 1: Immediate Capital Liberation (Sells &amp; Trims)</h3>
<div class="table-wrapper">
<table class="wikitable">
  <thead>
    <tr>
      <th>Security</th>
      <th>Action</th>
      <th class="num">Shares to Sell</th>
      <th>Execution Trigger</th>
<!-- MARKET IN -->
      <th class="num">Estimated Capital Liberated (₹)</th>
<!-- /MARKET -->
<!-- MARKET US -->
      <th class="num">Estimated Capital Liberated ($)</th>
<!-- /MARKET -->
      <th>Liberation Rationale</th>
    </tr>
  </thead>
  <tbody>
    <!-- Sells and Trims -->
  </tbody>
</table>
</div>

<h3>Phase 2: High-Conviction Reallocation (Limit Buys at Support)</h3>
<div class="table-wrapper">
<table class="wikitable">
  <thead>
    <tr>
      <th>Security</th>
      <th>Strategy Bucket</th>
<!-- MARKET IN -->
      <th class="num">Capital Allocated (₹)</th>
<!-- /MARKET -->
<!-- MARKET US -->
      <th class="num">Capital Allocated ($)</th>
<!-- /MARKET -->
      <th class="num">Target Shares</th>
<!-- MARKET IN -->
      <th>Limit Entry Zone (₹)</th>
      <th>Initial Stop (₹)</th>
      <th>Base Target (₹)</th>
<!-- /MARKET -->
<!-- MARKET US -->
      <th>Limit Entry Zone ($)</th>
      <th>Initial Stop ($)</th>
      <th>Base Target ($)</th>
<!-- /MARKET -->
      <th>Execution Rule</th>
    </tr>
  </thead>
  <tbody>
    <!-- Limit Buys -->
  </tbody>
</table>
</div>

<!-- MARKET IN -->
<h3>Phase 3: Defensive GTT &amp; Trailing Stop Architecture</h3>
<!-- /MARKET -->
<!-- MARKET US -->
<h3>Phase 3: Defensive Trailing Stop Architecture</h3>
<!-- /MARKET -->
<div class="table-wrapper">
<table class="wikitable">
  <thead>
    <tr>
      <th>Security</th>
      <th>Position Status</th>
<!-- MARKET IN -->
      <th class="num">Current CMP (₹)</th>
      <th>GTT Trigger Level (₹)</th>
<!-- /MARKET -->
<!-- MARKET US -->
      <th class="num">Current CMP ($)</th>
      <th>Stop Trigger Level ($)</th>
<!-- /MARKET -->
      <th>Stop Type</th>
      <th>Trailing Mechanism / Anchor</th>
    </tr>
  </thead>
  <tbody>
<!-- MARKET IN -->
    <!-- GTT Stops for all retained and newly purchased positions -->
<!-- /MARKET -->
<!-- MARKET US -->
    <!-- Stops for all retained and newly purchased positions -->
<!-- /MARKET -->
  </tbody>
</table>
</div>

<!-- REFERENCES & CITATIONS -->
<!-- MARKET IN -->
<h2 id="references">References &amp; Regulatory Disclosures</h2>
<!-- /MARKET -->
<!-- MARKET US -->
<h2 id="references">References &amp; SEC Disclosures</h2>
<!-- /MARKET -->
<ol class="reflist">
<!-- MARKET IN -->
  <li id="cite_note-1">^ Zerodha Broking Limited &bull; Demat Holdings Ledger &amp; Margin Statement for {{SESSION_DATE}}.</li>
  <li id="cite_note-2">^ National Stock Exchange of India (NSE) &bull; Bhavcopy &amp; Corporate Announcements.</li>
  <li id="cite_note-3">^ Screener.in Consolidated Financial Query Engine.</li>
<!-- /MARKET -->
<!-- MARKET US -->
  <li id="cite_note-1">^ US Brokerage Holdings Ledger &amp; Margin Statement for {{SESSION_DATE}}.</li>
  <li id="cite_note-2">^ US Securities and Exchange Commission (SEC EDGAR) &bull; Corporate Filings &amp; Form 4 Disclosures.</li>
  <li id="cite_note-3">^ Finviz Financial Ratios &amp; Technical Screener.</li>
<!-- /MARKET -->
  <li id="cite_note-4">^ TradingView Interactive Technical Screener.</li>
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
- **Subject:** `Subject: Master Portfolio Forensic Audit & Capital Reallocation Blueprint | [Session Date] — Net Worth: ₹[Amount]`
<!-- /MARKET -->
<!-- MARKET US -->
- **Subject:** `Subject: Master US Portfolio Forensic Audit & Capital Reallocation Blueprint | [Session Date] — Net Worth: $[Amount]`
<!-- /MARKET -->
- **Pre-Send Audit:** Zero omissions across all 6 chapters. Complete mathematical reconciliation verified.
- **Google Drive Maintenance (Single Latest Version Lifecycle):**
<!-- MARKET IN -->
  - **Target Location:** `docs/reports/Portfolio_Audit_<YYYY-MM-DD>.html`
<!-- /MARKET -->
<!-- MARKET US -->
  - **Target Location:** `docs/reports/US_Portfolio_Audit_<YYYY-MM-DD>.html`
<!-- /MARKET -->
  - **Date Display:** The resolved market session date (`YYYY-MM-DD` / formatted session date), which is the latest completed data-verified session and may be earlier than the run date, must be prominently displayed in the document title, subtitle, and Wikipedia Infobox metadata.
<!-- MARKET IN -->
  - **Prune Prior Versions:** Automatically scan `docs/reports/` and delete / remove all previous versions matching `Portfolio_Audit_*.html` prior to or upon saving the new file, ensuring only the single latest report is maintained in docs/reports/.
<!-- /MARKET -->
<!-- MARKET US -->
  - **Prune Prior Versions:** Automatically scan `docs/reports/` and delete / remove all previous versions matching `US_Portfolio_Audit_*.html` prior to or upon saving the new file, ensuring only the single latest report is maintained in docs/reports/.
<!-- /MARKET -->
- **Automated Dispatch Execution (MANDATORY):**
<!-- MARKET IN -->
  - Persist the complete HTML audit to `docs/reports/Portfolio_Audit_<YYYY-MM-DD>.html`.
<!-- /MARKET -->
<!-- MARKET US -->
  - Persist the complete HTML audit to `docs/reports/US_Portfolio_Audit_<YYYY-MM-DD>.html`.
<!-- /MARKET -->
  - Dispatch the email immediately and automatically via `scripts/send_email.py` using credentials from `.env` (Do NOT prompt the user or request manual confirmation):
    ```bash
<!-- MARKET IN -->
    .venv/bin/python scripts/send_email.py --subject "Master Portfolio Forensic Audit & Capital Reallocation Blueprint | [Session Date] — Net Worth: ₹[Amount]" --html-file "docs/reports/Portfolio_Audit_<YYYY-MM-DD>.html" --recipient "rajasekharreddymekala732@gmail.com"
<!-- /MARKET -->
<!-- MARKET US -->
    .venv/bin/python scripts/send_email.py --subject "Master US Portfolio Forensic Audit & Capital Reallocation Blueprint | [Session Date] — Net Worth: $[Amount]" --html-file "docs/reports/US_Portfolio_Audit_<YYYY-MM-DD>.html" --recipient "rajasekharreddymekala732@gmail.com"
<!-- /MARKET -->
    ```
  - Confirm successful SMTP execution in the final turn summary.
