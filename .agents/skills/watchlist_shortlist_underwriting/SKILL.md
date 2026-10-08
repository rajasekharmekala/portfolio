---
name: watchlist_shortlist_underwriting
description: >-
  Underwrites the next batch of watchlist names for one market (IN or US) through the 360-degree underwriting gates, writes one dossier per name, and updates the watchlist and shortlist JSON record files. Market-specific blocks are marked.

---

> **Market blocks (binding):** this skill covers both markets. Read `.agents/config/markets.json` for the market in this run (`IN` or `US`). Follow the text that is not inside a market block, and inside a market block follow only the block whose label matches the run's market. Ignore the other block. Figures, currency, exchange names and data sources differ by market; never mix them.

<!-- MARKET IN -->
# Autonomous Incremental Watchlist-to-Shortlist Deep Underwriting Engine
<!-- /MARKET -->
<!-- MARKET US -->
# US Autonomous Incremental Watchlist-to-Shortlist Deep Underwriting Skill
<!-- /MARKET -->

> **Voice (binding):** read `../_shared/REPORT_VOICE.md` before writing. Explain every heading and subsection in plain English with reasoning and consequences; no template phrases; each verdict names its rule and the level that would change it. Colours come only from `../_shared/REPORT_PALETTE.md`: use the `verdict-*` classes and no emoji status markers.

> **Market-data date (binding):** use the latest completed exchange session with a verified final benchmark close, following `../_shared/RUN_PROTOCOL.md` §0. Do not treat the run's calendar date as the data date. Use that same session for ledger prices, technical gates, dossier as-of dates, and dated batch summaries; disclose a data delay where applicable.

<!-- MARKET IN -->
Act as a **Senior Institutional Equity Research Analyst**, **Quantitative Strategist**, and **Chief Underwriting Architect** covering Indian Equity Markets (NSE/BSE).
<!-- /MARKET -->
<!-- MARKET US -->
Act as an **Institutional Equity Portfolio Director**, **Chief US Underwriting Officer**, and **Senior Equity Research Architect** covering US Equities (NYSE / NASDAQ).
<!-- /MARKET -->

<!-- MARKET IN -->
Execute the **Autonomous Incremental Watchlist-to-Shortlist Deep Underwriting Engine**.

Your objective is to process the broad watchlist in continuous, stateful batches of **exactly 4 securities per run**. To eliminate context compression, diluted focus, and truncated research, the orchestrator MUST launch an **independent, dedicated research subagent for each individual company** (1 agent per company). Each dedicated agent conducts an exhaustive 360-degree fundamental and technical deep-dive on its assigned candidate, persists a standalone in-depth **Wikipedia-style HTML research dossier / company blog** (60–80 KB, with 25–40+ formal citations) in **`docs/blogs/<SYMBOL>_dossier.html`**, and returns a structured underwriting payload. The orchestrator dynamically maintains an elite, capacity-constrained **`data/shortlist/IN.json`** (strictly capped at **Max 10 Core Alpha** and **Max 10 Tactical Momentum** autowritten slots) using institutional displacement economics and **company-specific KPI underwriting**. The active watchlist in **`data/watchlist/IN.json`** is strictly capped at **Max 150 companies** across a two-sheet architecture (`watchlist.active` and `watchlist.archive`).
<!-- /MARKET -->
<!-- MARKET US -->
Execute the **Autonomous Incremental Watchlist-to-Shortlist Deep Underwriting Engine**:
1. Incrementally process exactly **4 pending securities per run** from `watchlist.active` in **`data/watchlist/US.json`**.
2. For each security, dispatch a dedicated, independent research subagent (1 subagent per company) to conduct an exhaustive 360-degree fundamental and technical underwriting analysis.
3. Generate and persist a comprehensive, standalone Wikipedia-style HTML research dossier saved directly to **`docs/blogs/<SYMBOL>_dossier.html`** (matching the exact design system, typography, infobox, wikitables, and 25–40+ primary SEC EDGAR citations defined in `us_company_report`).
4. Apply institutional **Displacement Economics** to update **`data/shortlist/US.json`** (strictly adhering to the 10 Core Alpha + 10 Tactical Momentum + 5 Leveraged Satellite autowritten capacity caps).
5. Update **`data/watchlist/US.json`** in-place (updating watchlist.active status and routing rejected candidates to watchlist.archive with full audit trails).
6. Automatically rebuild the master blog portal by executing `python3 scripts/build_dossier_portal.py`.
<!-- /MARKET -->

---

### MANDATORY ZERO-HALLUCINATION & UNDERWRITING INTEGRITY RULES:

<!-- MARKET IN -->
1. **NO HALLUCINATIONS:** Strictly verify all market prices (CMP), 52-week ranges, moving averages (20/50/200 DMA), 14-day RSI, volume multiples, market caps, P/E ratios, ROCE, ROE, debt-to-equity, cash conversion (CFO/PAT), and financial filings against live verified market data (Screener.in, TradingView, BSE/NSE exchange disclosures).
1.1. **MANDATORY TWO-STEP SEARCH & DEEP FETCH PROTOCOL (ZERO-SNIPPET RELIANCE):**
   - **Never Stop at Search Snippets:** Subagents MUST NEVER rely solely on high-level search snippets or summaries. High-level snippets do not contain full financial statements or rolling technical data, causing false `FAIL_UNVERIFIED` errors.
   - **Mandatory Deep Fetch Execution:** For every assigned candidate, subagents MUST:
     1. Search using `duck-duck-go-search` to locate the Screener.in consolidated company URL (`https://www.screener.in/company/<SYMBOL>/consolidated/` or `https://www.screener.in/company/<SYMBOL>/`), Trendlyne, or exchange filing pages.
     2. Call `duck-duck-go-fetch_content` (with `parse_mode='markdown'` or `text`, and paginating if necessary) on the Screener.in URL to ingest the complete tabular P&L, Balance Sheet, Cash Flow, and Key Financial Ratios.
     3. Extract and verify the exact figures:
        - **3Y Cumulative CFO / PAT:** Sum audited CFO across the last 3 reported fiscal years (FY24 + FY23 + FY22 or FY25 + FY24 + FY23) divided by cumulative PAT over the same 3 years.
        - **ROCE, ROE, D/E, OPM %, 3Y Sales & PAT CAGR:** Directly from the fetched financial tables.
        - **Technical Averages & Indicators:** Retrieve 50-DMA, 200-DMA, 52-week range, and current price from the fetched Screener quote header / TradingView / technical tables.
     4. This ensures 100% of Layer 1 Hard Gates are deterministically evaluated without unverified gaps.
2. **MANDATORY USE OF `N/A` (NO GUESSING / NO ESTIMATING):** If any specific metric (e.g. promoter pledge change, 3-year median P/E, intraday VWAP, or consensus target) cannot be deterministically verified even after deep fetching, output **`N/A`** with a brief reason rather than fabricating numbers.
3. **ADVERSARIAL RED-TEAM UNDERWRITING:** A transcript mention or watchlist entry is merely an **unverified idea seed**. Analyze each candidate with institutional skepticism. High valuation froth, low ROCE (<15%), promoter pledge, debt burden, cyclical peak margins, or broken technical structure must lead to immediate gate rejection.
4. **NO ARBITRARY 0–100 POINT SCORING:** Do NOT assign generic composite scores (e.g. 78/100 or 82/100). Ground all evaluations in the **3-Layer Framework**:
   - **Layer 1: Binary Hard Gating Floors (Pass/Fail)**
   - **Layer 2: 3–5 Company/Sector-Specific KPIs (Traffic-Light Scorecard)**
   - **Layer 3: Support-Aware Entry Posture (Execution Timing Gate)**
5. **WIKIPEDIA-STYLE HTML COMPANY BLOG DOSSIERS (NO DOCX):** This schedule writes standalone institutional research dossiers as self-contained **Wikipedia-style HTML files** directly to **`docs/blogs/<SYMBOL>_dossier.html`** (incorporating floating infoboxes, wikitables, table of contents, in-text superscript citations, and 3-layer underwriting scorecards). Word `.docx` output is deprecated.
6. **MANDATORY INDEPENDENT SUBAGENT PER COMPANY (DEDICATED SINGLE-COMPANY EXECUTION):**
   - **Strict Prohibition Against Single-Agent Sequential Batches:** The orchestrator MUST NEVER analyze multiple companies sequentially within a single agent context. Running all 4 batch companies through a single agent dilutes attention, exhausts context tokens, and forces the model to compress rich narrative into shallow scorecard summaries and truncate citations.
   - **Dedicated Subagent Spawning Mandate:** For every 4-security batch selected from the queue, the orchestrator MUST spawn/launch an **independent, dedicated research subagent for each individual company** (1 agent per company).
   - **Subagent Mission & Deliverable:** Each dedicated company subagent focuses exclusively on its assigned ticker. It conducts the full 360-degree fundamental, operational, supply chain, and technical deep dive using live web searches, calculates exact mathematical levels, and generates the complete, unabbreviated **Wikipedia-style HTML blog dossier (`docs/blogs/<SYMBOL>_dossier.html`)** (targeting ~60–80 KB) with **25 to 40+ granular primary citations**.
   - **Payload Return to Orchestrator:** Once its company dossier is finalized, the dedicated subagent returns its standardized 3-layer underwriting payload (metrics, gate statuses, KPI health, entry posture, action verdict, and peer candidates) to the orchestrator.
   - **Orchestrator Role:** The orchestrator orchestrates the subagents, reconciles displacement economics across the 10+10 capacity books in `data/shortlist/IN.json`, updates `data/watchlist/IN.json`, and handles Google Drive synchronization strictly in-place.
7. **MANDATORY HIGH CITATION DENSITY (25 TO 40+ FORMAL REGULATORY & MARKET CITATIONS):**
   - Every generated dossier MUST feature an exhaustive reference list (`<ol class="reflist">`) containing **between 25 and 40+ formal, numbered citations** (`<sup><a href="#cite_note-X">[X]</a></sup>`).
   - References must cite concrete, verifiable primary sources:
     1. Audited Annual Reports (FY23, FY24, FY25, FY26) with specific page references, Director's Reports, and Notes to Financial Statements.
     2. Quarterly Earnings Call Transcripts (Q1, Q2, Q3, Q4) with attributed management commentary.
     3. Investor Presentations & Corporate Factsheets (exact quarter and date).
     4. BSE / NSE Regulatory Filings (SEBI LODR Reg 30 disclosures, promoter shareholding patterns, credit rating letters, board meeting outcomes).
     5. Credit Rating Rationales (CRISIL, ICRA, CARE, India Ratings) with rating actions and liquidity assessments.
     6. DRHP / RHP Industry Chapters & Prospectuses.
     7. Industry Associations & Government Reports (e.g. CRISIL MI&A, SIAM, CEA, DGTR, Ministry of Heavy Industries).
     8. Interactive Technical & Fundamental Platforms (Screener.in consolidated financials, TradingView charts).
   - In-text superscript tags (`<sup>[X]</sup>`) must be densely distributed across EVERY section—corporate history, operating segments, unit economics, supply chain inputs, forensic cash flows, peer multiples, and technical levels. Zero uncited figures or floating assertions.
8. **MANDATORY INDEPENDENT REVIEWER AGENT & EXTENSIVE GOOGLE SEARCH VERIFICATION:**
   - Before writing or persisting the final research dossiers `docs/blogs/<SYMBOL>_dossier.html`, `data/watchlist/IN.json`, and `data/shortlist/IN.json`, an **Independent Reviewer Agent** (dual-pass verification audit) must double-check all analysis, data values, calculations, and financial metrics.
   - The reviewer agent must **extensively perform live Google searches** (Screener.in, TradingView, BSE/NSE exchange disclosures) to cross-verify:
     - Real-time / closing market prices (CMP)
     - 52-week ranges, 20/50/200 DMAs, 14-day RSI, volume multiples
     - Financial fundamentals: ROCE, ROE, Debt/Equity, CFO/PAT, P/E, Sales & PAT CAGR, OPM %
     - Exact mathematical calculations for Asymmetry Ratios, stop losses, and target prices.
   - Any hallucination, discrepancy, or unverified estimation must be immediately corrected or marked with explicit verifiable `N/A`.
9. **MANDATORY ZERO-OMISSION RESEARCH DOSSIER COMPLETENESS:**
   - In every generated/updated `docs/blogs/<SYMBOL>_dossier.html`, **NONE of the standard dossier template sections may be omitted or abbreviated**. The 3-layer gating, company-specific KPI scorecard, peer benchmarking wikitable, fatal flaws red-team, and clear verdict must be completely rendered with no placeholders.
10. **MANDATORY DOSSIER-FIRST GATE — NO STOCK MAY BE MARKED `COMPLETED` WITHOUT A VERIFIED DOSSIER FILE:**
   - **Hard Prerequisite:** A stock's `Status` in `data/watchlist/IN.json` MUST NEVER be set to `COMPLETED` unless the corresponding dossier file `docs/blogs/<SYMBOL>_dossier.html` has been physically written to disk and verified to exist.
   - **Verification Protocol:** Before the orchestrator writes any `status = COMPLETED` record back to the watchlist JSON, it MUST execute a filesystem check confirming `os.path.exists('docs/blogs/<SYMBOL>_dossier.html')` returns `True` AND the file size is ≥ 30 KB (a non-trivial, complete dossier).
   - **If the dossier file is missing or undersized:** The orchestrator MUST:
     1. Leave `Status = PENDING` for that stock — do NOT mark it `COMPLETED`.
     2. Log a clear error in the run summary: `DOSSIER MISSING: <SYMBOL>_dossier.html not found or < 30 KB. Status remains PENDING.`
     3. Re-queue the stock at the top of the next batch until the dossier is successfully generated.
   - **Applies to ALL source types:** `HOLDING_SEED`, `DEEP_RESEARCH_PEER`, `MARKET_INTELLIGENCE`, `TRANSCRIPT`, and `MANUAL` — no exceptions.
   - **Symbol vs. Filename Mismatch Rule:** If a company's legal name resolves to a different symbol than the watchlist ticker (e.g., watchlist has `MEDANTA` but dossier saved as `GLOBALHEALTH_dossier.html`), the orchestrator MUST update the watchlist `Symbol` column to match the dossier filename, OR rename the dossier to match the watchlist ticker. Both must be in sync before `COMPLETED` status is written.
11. **MANDATORY GOOGLE DRIVE SYNCHRONIZATION & STRICT IN-PLACE OVERWRITE (NEVER GENERATE DUPLICATES OR NEW FILES):**
   - **Always Fetch Fresh from Google Drive:** At the start of every run/task, ALL JSON record files (`data/watchlist/IN.json`, `data/accounts/IN/zerodha.transactions.jsonl`, `data/shortlist/IN.json`) MUST always be actively fetched/synced fresh from sheets/ and shortlist/. **NEVER rely on local cached or stale files**, as the user may update holdings, watchlists, notes, or candidate entries directly on Google Drive between runs.
   - **MANDATORY IN-PLACE FILE OVERWRITE (ZERO DUPLICATION TOLERANCE):** Every update, state change, and newly generated dossier in `data/watchlist/IN.json`, `data/shortlist/IN.json`, and `docs/blogs/<SYMBOL>_dossier.html` MUST be updated **strictly IN-PLACE**.
     - **Google Drive API / Tool Semantics:** When running under Gemini Spark or Google Drive tools, **DO NOT call file creation endpoints (`files.create`) or upload as a new file**. You MUST search for the existing file by name in the target folder to retrieve its existing `fileId`, and call file update (`files.update`) with media replacement to overwrite the existing file object directly. If the tool platform lacks an update endpoint and generates a new copy, you MUST immediately trash/delete the older copy and ensure no duplicate display names exist.
     - **Local Filesystem Semantics:** When writing to paths (`docs/...`, `watchlist/...`, `shortlist/...`), directly overwrite the exact target file path in-place (`mode='wb'` in python).
     - **STRICTLY FORBIDDEN - NO BACKUP OR CHECKPOINT FILES IN CODE:** When generating Python scripts or modifying files, agents MUST NEVER write code that copies, renames, or creates backups (e.g. `shutil.copy(..., "..._old.xlsx")` or saving `*_Batch*.xlsx` or `*_Cycle*.xlsx` are STRICTLY FORBIDDEN). All transformations must be done in memory and saved directly to the single canonical file.
     - **STRICTLY FORBIDDEN - NO CYCLE SUFFIXES IN RESEARCH DOSSIERS:** Research dossier filenames must ALWAYS strictly be `<SYMBOL>_dossier.html` (e.g. `AFCOM_dossier.html`). NEVER name dossiers with cycle tags like `<SYMBOL>_Cycle1_dossier.html`. Cycle numbers belong inside the document metadata table, never in the filename.
     - **STRICTLY FORBIDDEN - NO COLLISION SUFFIXES:** Creating duplicate files or appending version counters, copy numbers, timestamps, or suffixes (e.g. `Zerodha_Shortlist (1).xlsx`, `<SYMBOL> (1)_dossier.html`, `_new.xlsx`) is strictly prohibited.
     - **COMPREHENSIVE PRE-SAVE & POST-SAVE DUPLICATE PURGE PROTOCOL:**
       - Before AND immediately after saving any research dossier in `docs/blogs/`, scan the directory and delete all duplicate variants matching `<SYMBOL> (*)*`, `<SYMBOL>_Cycle*.*`, `<SYMBOL>_old*.*`, `<SYMBOL>_bak*.*`, `<SYMBOL>_copy*.*`, or `<SYMBOL>*.gdoc` so that ONLY the single canonical `<SYMBOL>_dossier.html` exists.
       - For registries in `watchlist/` and `shortlist/`, scan for and remove any `* (*).json`, `*_old*.json`, `*_Batch*.xlsx`, or `*_Cycle*.xlsx`. If any duplicate file with newly updated rows is detected, consolidate the new rows into the canonical file and delete the duplicate immediately.
   - **Fail Closed on Sync Failure:** If fresh files cannot be fetched from Google Drive or changes cannot be pushed back to Google Drive, halt execution and report the exact sync blocker.

12. **MANDATORY ONE-OFF SCRIPT LIFECYCLE & CACHE HYGIENE (NO RESIDUAL ARTIFACTS):**
<!-- /MARKET -->
<!-- MARKET US -->
1. **LIVE WEB SEARCH & TWO-STEP DEEP FETCH PROTOCOL:** Subagents must NEVER rely solely on search snippets. Execute `duck-duck-go-search` to find canonical SEC 10-K/10-Q, Finviz, and TradingView pages, and `duck-duck-go-fetch_content` to retrieve complete tabular financial statements.
2. **STRICT VERBOSITY & ANALYTICAL DEPTH:** Every generated dossier must contain 3–4 dense, investigative narrative paragraphs per section, full 5-year GAAP financial statement wikitables, a peer comparison matrix, 3 fatal flaw scenarios, and 25–40+ granular SEC EDGAR citations (`<ol class="reflist">`).
3. **MANDATORY USE OF `N/A`:** If any specific metric (e.g. historical short interest, institutional dark pool ratio, or insider cluster trades) is not deterministically verified, output **`N/A`** with a brief reason.
4. **MANDATORY ONE-OFF SCRIPT LIFECYCLE & CACHE HYGIENE:**
<!-- /MARKET -->
   - Scratch code lives only in `<RUN_DIR>` and is deleted with it (RUN_PROTOCOL sections 1 and 5).
   - **Run directory:** nothing from earlier runs is read. Cleanup follows `../_shared/RUN_PROTOCOL.md` section 5. Repository scripts are never deleted.
<!-- MARKET IN -->
   - **Permanent repository scripts (never delete or modify without the user):** `scripts/send_email.py`, `scripts/build_dossier_portal.py`, `scripts/serve_blogs.py`, `scripts/market_facts.py`, `scripts/validate_report.py`.
   - **Pre-termination verification:** run `ls scripts/` and confirm ONLY whitelisted files remain. Leaving one-off generator/update scripts behind is a pipeline failure.

---

### REPOSITORY PATHS & FILE CONVENTIONS:

All file operations reference these canonical project workspace paths (`docs/`, `sheets/`, `watchlist/`, `shortlist/`):

- **Broad Watchlist (Input Queue):** `data/watchlist/IN.json` (workspace custody)
- **Active Portfolio Holdings (Exclusion & Audit Check):** `data/accounts/IN/zerodha.transactions.jsonl` (workspace custody)
- **Curated Shortlist (Output Registry):** `data/shortlist/IN.json` (workspace custody)
- **Company Blogs & Research Dossiers (Output):** `docs/blogs/<SYMBOL>_dossier.html` (GitHub Pages docs/blogs/ repository; updated in-place across round-robin cycles)
<!-- /MARKET -->
<!-- MARKET US -->
   - Permanent repository scripts (never delete): `scripts/send_email.py`, `scripts/build_dossier_portal.py`, `scripts/serve_blogs.py`, `scripts/market_facts.py`, `scripts/validate_report.py`.
<!-- /MARKET -->

---

### SHORTLIST CAPACITY & SOURCE-TYPE ARCHITECTURE:

<!-- MARKET IN -->
The Shortlist registry enforces strict capacity limits, source differentiation, and holding isolation:

1. **Pipeline Strategy Book Capacity (Autowritten Challenger Slots):**
   - **Core Alpha:** Maximum **10 Autowritten Challenger Positions** (High ROCE >18%, durable moats, clean balance sheets, 1–3+ year compounding horizon).
   - **Tactical Momentum:** Maximum **10 Autowritten Challenger Positions** (Stage 2 markup, 20/50/200 DMA alignment, relative strength leadership vs Nifty 500, volume expansion, turnaround/operating leverage, 3-week to 6-month horizon).
2. **Three Shortlist Source Types (Capacity Isolation):**
   - `AUTOWRITTEN` (or `DEEP_RESEARCH`): Automatically discovered, underwritten, and managed by this scheduled deep research engine. Strictly subject to the **10 Core / 10 Tactical challenger capacity cap** and competitive displacement.
   - `CURRENT_HOLDING`: Dedicated category for active portfolio holdings (from `data/accounts/IN/zerodha.transactions.jsonl`) that undergo rigorous deep underwriting. **DOES NOT CONSUME or count against the 10+10 autowritten challenger slots.** Current holdings reside in the shortlist with explicit portfolio management verdicts (`KEEP_COMPOUNDING`, `ACCUMULATE_ON_DIP`, `TRIM_PROFIT_BOOKING`, `REPLACE_UNDERPERFORMER`) to benchmark active capital against new pipeline ideas.
   - `MANUAL`: Hand-curated securities manually added by the user. **Strictly immune and protected from automatic eviction or displacement.**
3. **Action Verdict Taxonomy:**
   - **For `CURRENT_HOLDING` Positions:**
     - `KEEP_COMPOUNDING`: All gates passed, operational KPIs healthy (≥3/4), Stage 2 uptrend intact. Maintain full position.
     - `ACCUMULATE_ON_DIP`: High-conviction compounder pulling back to verified support (`AT_SUPPORT` ≤0.5x ATR), allocation headroom available. Add to position.
     - `TRIM_PROFIT_BOOKING`: Extended (>1.5x ATR above support, RSI >75), hit Bull Target, or exceeds single-stock concentration limit (>15–20%). Trim 30%–50% to harvest gains.
     - `REPLACE_UNDERPERFORMER`: Broken structural support (closed below stop / Stage 4), or failed ≥2 operational KPIs, or fundamental thesis impairment. **Immediate candidate for capital swap** into a top-ranked shortlist challenger.
   - **For `AUTOWRITTEN` Pipeline Challengers:**
     - `IMMEDIATE_BUY` (at support with high asymmetry)
     - `ACCUMULATE_ON_DIP` (near support)
     - `WAIT_FOR_SUPPORT` (extended, do not chase)
     - `REJECTED` (failed gating hurdle)
<!-- /MARKET -->
<!-- MARKET US -->
`data/shortlist/US.json` enforces strict capacity constraints for autowritten candidates:
- **Core Alpha Book:** Exactly 10 autowritten slots maximum.
- **Tactical Momentum Book:** Exactly 10 autowritten slots maximum.
- **Leveraged Satellite Book:** Exactly 5 autowritten slots maximum.
- **Displacement Economics:** When a book is full, incoming challengers are evaluated against the weakest incumbent in that book based on:
  1. Layer 2 KPI Pass Rate (e.g. 4/4 vs 2/4)
  2. Support Proximity (e.g. $\le 0.5\times \text{ATR}$ vs $>1.5\times \text{ATR}$)
  3. Catalyst Proximity (upcoming catalyst vs distant/stale catalyst)
  4. Reward/Risk Asymmetry Ratio ($R:R$)
  - If Challenger is superior: Evict weakest incumbent and insert challenger.
  - If Challenger is inferior: Mark as `QUALIFIED_DEFERRED` (persisting the dossier for future cycles without displacing).
<!-- /MARKET -->

---

<!-- MARKET IN -->
### CANONICAL JSON RECORD SCHEMAS:

#### 1. `data/shortlist/IN.json` Canonical Schema (43 Columns):

Header columns:

```text
Symbol,Company Name,Strategy Bucket,Action Verdict,Gate Status,KPI Health,Entry Posture,Source Type,Macro Sector,Fine Subsector,Cap Tier,Market Cap (Cr),CMP,Entry Zone Low,Entry Zone High,Stop Loss,Target Base,Target Bull,Asymmetry Ratio,ROCE %,ROE %,Debt to Equity,CFO to PAT,3Y Sales CAGR %,3Y PAT CAGR %,OPM %,P/E,Weinstein Stage,RSI 14,RS Rating,Distance from Support ATR,1D Return %,1W Return %,2W Return %,Dist from 20DMA %,Momentum State,Primary Catalyst,Primary KPI Summary,Moat Description,Invalidation Condition,Research Dossier Path,Last Researched Date,As of Date
```

*Note on `Research Dossier Path`:* This column records `blogs/<SYMBOL>_dossier.html` (or `docs/blogs/<SYMBOL>_dossier.html`).

#### 2. `data/watchlist/IN.json` Architecture & Canonical Schema (22 Columns):

The JSON record file operates under a **Strict Max 150-Company Capacity Limit** enforced across a **Two-Sheet Architecture**:
- **Sheet 1: `watchlist.active` (Strictly Capped at Max 150 Companies):** The stateful round-robin execution queue containing active holdings (`HOLDING_SEED`), qualified watchlist ideas (`ACTIVE_WATCH`), and pending seeds (`RESEARCH_REQUIRED`). This sheet must NEVER exceed 150 rows.
- **Sheet 2: `watchlist.archive`:** Permanent repository for evaluated candidates that failed Layer 1 Hard Gates (`Action Verdict = REJECT`). Retains full audit trail and failed metrics, but completely removed from the active round-robin queue so it never clutters execution.

Canonical 22-column header schema:

```text
Symbol,Company Name,Source Type,Status,Action Verdict,Deep Research Status,Research Cycle,Gate Status,KPI Health,Entry Posture,Strategy Fit,Shortlist Action,Last Researched Date,Strategy Bucket,Strategy Book,Account Scope,As of Date,Theme Tags,Catalyst Timeline,Investment Thesis,Summary Rationale,Notes
```

---

### THE 3-LAYER INSTITUTIONAL UNDERWRITING FRAMEWORK:

Every candidate must be processed through the following 3 layers sequentially:
<!-- /MARKET -->
<!-- MARKET US -->
### THE US 3-LAYER INSTITUTIONAL UNDERWRITING FRAMEWORK:
<!-- /MARKET -->

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ LAYER 1: BINARY HARD GATING FLOORS (Must Pass 100% of Gates)                │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. Financial Health Floor:                                                  │
<!-- MARKET IN -->
│    - ROCE ≥ 15.0% (Core prefers >18.0%)                                     │
│    - Debt-to-Equity < 0.70 (Excluding financial institutions/NBFCs)         │
│    - 3-Year Cumulative CFO / PAT ≥ 0.70 (Earnings backed by real cash flows)│
<!-- /MARKET -->
<!-- MARKET US -->
│    - ROIC ≥ 12.0% (Core prefers >16.0%)                                     │
│    - Free Cash Flow Margin ≥ 12.0% (Core prefers >18.0%)                    │
│    - Net Debt / EBITDA < 3.0x (Excluding financial institutions)            │
│    - Stock-Based Compensation (SBC) Dilution < 5.0% of Annual Revenue       │
<!-- /MARKET -->
│ 2. Technical Posture Floor:                                                 │
│    - Tactical: Weinstein Stage 2 Markup above rising 50-DMA and 200-DMA     │
│    - Core: Stage 1 Base Breakout or Stage 2 Markup                          │
│    - No Stage 4 Breakdown / No Death Cross on heavy volume                  │
<!-- MARKET IN -->
│ 3. Asymmetry Floor & Mathematical Target Anchoring:                         │
<!-- /MARKET -->
<!-- MARKET US -->
│ 3. Asymmetry Floor & Target Anchoring:                                      │
<!-- /MARKET -->
│    - Tactical: Reward-to-Risk Asymmetry Ratio ≥ 3.5:1                        │
│    - Core: Reward-to-Risk Asymmetry Ratio ≥ 3.0:1                            │
│    - Mandatory Target Anchoring: Must cite Forward EPS × 3Y Median P/E OR   │
<!-- MARKET IN -->
│      Technical Base Measured-Move. Arbitrary inflated targets strictly      │
│      forbidden. If target unverified, Gate Status = FAIL_ASYMMETRY.          │
<!-- /MARKET -->
<!-- MARKET US -->
│      Discounted Cash Flow (DCF) or Base Measured-Move. Arbitrary targets    │
│      strictly forbidden. If unverified, Gate Status = FAIL_ASYMMETRY.       │
<!-- /MARKET -->
│                                                                             │
│ DISPOSITION: If ANY gate fails → Gate Status = FAIL_[REASON]             │
<!-- MARKET IN -->
│    → Action Verdict = REJECTED → Do NOT evaluate Layer 2 or Layer 3.     │
<!-- /MARKET -->
<!-- MARKET US -->
│    → Action Verdict = REJECTED → Archive candidate to watchlist.archive.  │
<!-- /MARKET -->
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ (If ALL Gates Pass)
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
<!-- MARKET IN -->
│ LAYER 2: 3–5 COMPANY & SECTOR-SPECIFIC KPIs (The Deep Dossier Scorecard)    │
<!-- /MARKET -->
<!-- MARKET US -->
│ LAYER 2: 3–5 OPERATIONAL SECTOR KPIS (Traffic-Light Scorecard)              │
<!-- /MARKET -->
├─────────────────────────────────────────────────────────────────────────────┤
<!-- MARKET IN -->
│ Select 3–5 primary operational metrics that drive THAT specific business:   │
│ • Capital Goods / Cranes / Infra: Fleet/Capacity Utilization, Order Book    │
│   to Bill Ratio (>2.0x), Working Capital/Debtor Days (<75 days).            │
│ • EMS / Electronics / Tech: Fixed Asset Turnover (>4.0x), Client            │
│   Concentration (<40%), Value-Add Margin Expansion (+YoY).                  │
│ • Pharma / CDMO / APIs: USFDA EIR Compliance (Zero 483 warnings), Pipeline  │
│   Commercialization, Gross Margin Stability.                                │
│ • Consumer / Retail: Same-Store-Sales Growth (SSSG), Store Unit Economics.  │
│                                                                             │
│ Score each KPI: PASS (Healthy) | WATCH (Moderate Risk) | FAIL      │
│ DISPOSITION: Minimum 3/4 or 4/5 PASS required to qualify.                 │
<!-- /MARKET -->
<!-- MARKET US -->
│ Evaluate candidate against 3–5 company-specific operational metrics:        │
│ • Cloud/SaaS: ARR Growth, Net Revenue Retention (NRR >110%), CAC Payback    │
│ • Semiconductors: Gross Margin (>50%), Fab Capacity, Design Win Pipeline    │
│ • AI/Compute: GPU Cluster Utilization, Power Availability, Backlog ($B)     │
│ • E-Commerce: Take Rate, Active Buyers, Logistics Unit Economics            │
│ Score: PASS (All Healthy) | WATCH (1 Amber) | FAIL (≥2 Red)        │
<!-- /MARKET -->
└──────────────────────────────────────┬──────────────────────────────────────┘
<!-- MARKET IN -->
                                       │ (If KPI Health Qualified)
<!-- /MARKET -->
<!-- MARKET US -->
                                       │ (If Layer 2 Passes)
<!-- /MARKET -->
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ LAYER 3: SUPPORT-AWARE ENTRY POSTURE (Execution Timing Gate)                │
├─────────────────────────────────────────────────────────────────────────────┤
<!-- MARKET IN -->
│ Measure distance from nearest verified support anchor in `ATR(14)`:         │
│ • AT_SUPPORT (≤ 0.5 × ATR): Price at 20/50-DMA / pivot base                 │
│   → Action Verdict: IMMEDIATE BUY                                        │
│ • NEAR_SUPPORT (0.5 – 1.0 × ATR): Minor pullback required                   │
│   → Action Verdict: ACCUMULATE ON DIP                                    │
│ • EXTENDED (> 1.0 × ATR or RSI > 70): Price overextended from base          │
│   → Action Verdict: WAIT FOR SUPPORT (Do not chase)                      │
│ • SUPPORT_BROKEN: Price closed below structural invalidation stop           │
│   → Action Verdict: REJECTED / BROKEN STRUCTURE                          │
<!-- /MARKET -->
<!-- MARKET US -->
│ Determines exact execution timing and entry zone:                           │
│ • AT_SUPPORT (0.0 to 1.0 ATR from rising 20/50 DMA) → IMMEDIATE_BUY      │
│ • NEAR_SUPPORT (1.0 to 2.0 ATR from support) → ACCUMULATE_ON_DIP          │
│ • OVEREXTENDED (>2.5 ATR above 20 DMA, RSI > 72) → WAIT_FOR_SUPPORT      │
│ • OVERBOUGHT_CLIMAX (>3.5 ATR extension) → TRIM_PROFIT_BOOKING          │
<!-- /MARKET -->
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### STEP-BY-STEP AUTONOMOUS EXECUTION ALGORITHM:

<!-- MARKET IN -->
```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ PHASE 1: FRESH GOOGLE DRIVE INGESTION, RECONCILIATION & INITIALIZATION       │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. Fetch & Ingest `data/watchlist/IN.json` fresh from sheets/ and shortlist/│
│ 2. Fetch & Ingest `data/shortlist/IN.json` fresh from sheets/ and shortlist/│
│ 3. Fetch & Ingest `data/accounts/IN/zerodha.transactions.jsonl` fresh from sheets/ and shortlist/    │
│ 4. Ensure `docs/blogs/` directory exists.                             │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ PHASE 2: STATEFUL ROUND-ROBIN QUEUE SELECTION (NEXT 4 STOCKS)               │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. Load `watchlist.active` array from `data/watchlist/IN.json`.   │
│ 2. Determine current `Research Cycle` = max(Research Cycle in the JSON records) or 1.   │
│ 3. Find eligible candidate rows where:                                      │
│    - `Deep Research Status` is 'PENDING' OR empty, OR                       │
│    - `Research Cycle` < current_cycle                                       │
│ 4. ROUND-ROBIN RESET CHECK:                                                 │
│    - If ZERO rows are pending:                                               │
│      • Set current_cycle = current_cycle + 1                                │
│      • Reset all watchlist.active rows to `Deep Research Status` = 'PENDING' │
│      • Select the first 4 rows from the top of the watchlist.active.         │
│ 5. If pending rows exist: Select first 4 pending rows in sequential order.  │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ PHASE 3: DISPATCHING 4 INDEPENDENT DEDICATED SUBAGENTS (1 PER COMPANY)      │
├─────────────────────────────────────────────────────────────────────────────┤
│ To prevent token exhaustion, diluted focus, and shallow scorecard shortcuts,│
│ the Orchestrator NEVER analyzes multiple companies in a single agent.       │
│ For the 4 selected candidates, the Orchestrator dispatches an independent,  │
│ dedicated research subagent for EACH company (1 agent per candidate).       │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ PHASE 4: SUBAGENT SINGLE-STOCK 360° DEEP DIVE & DOSSIER GENERATION          │
├─────────────────────────────────────────────────────────────────────────────┤
│ Each dedicated subagent operates autonomously on its assigned company:      │
│ 1. Active Holding Audit (if holding): Position health, P&L, Stop, Verdict.  │
│ 2. 3-Layer Underwriting: Layer 1 (Hard Gates), Layer 2 (3-5 Sector KPIs),   │
│    and Layer 3 (Support-Aware Entry Posture).                               │
│ 3. Peer Discovery & Benchmarking: Benchmarks 2–4 peers; identifies top      │
│    candidates for watchlist.active seeding (Source Type = DEEP_RESEARCH_PEER│
│ 4. Wikipedia HTML Dossier Generation (`docs/blogs/<SYMBOL>_dossier`): │
│    - Google Fonts (Newsreader serif + Inter body + JetBrains Mono math)     │
│    - Prominent top Executive Capital Allocation Decision Banner             │
│    - Floated infobox, wikitables, TOC, non-robotic verbose investigative    │
│      operational prose (history, unit economics, supply chain pass-through) │
│    - MANDATORY 25 TO 40+ GRANULAR REGULATORY & MARKET CITATIONS (<ol.reflist│
│ 5. Returns structured 3-layer underwriting payload back to Orchestrator.    │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ PHASE 5: PIPELINE CHALLENGER CAPACITY & DISPLACEMENT MANAGEMENT ENGINE      │
├─────────────────────────────────────────────────────────────────────────────┤
│ The Orchestrator collects payloads from all 4 dedicated subagents:          │
│ For each NEW pipeline candidate (`Source Type = 'AUTOWRITTEN'`):             │
│ Case A: Strategy Book < 10 autowritten entries → INSERT candidate.          │
│ Case B: Strategy Book == 10 autowritten entries (FULL):                     │
│   Identify weakest incumbent by Quality Precedence:                         │
│   Lowest KPI Pass Rate → Extended Posture → Distant Catalyst → Lower Asym.  │
│   If Challenger is superior → EVICT incumbent & INSERT challenger.          │
│   Else → QUALIFIED_DEFERRED (remains in blog dossier for future cycles).     │
│ Case C: Candidate Fails Layer 1 or Layer 2 → REJECTED_BELOW_HURDLE.         │
│ Seed qualified peers to `watchlist.active` (strictly observing 150 ceiling).│
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ PHASE 6: DOSSIER GATE CHECK, REVIEWER AUDIT, STATE SYNC & GOOGLE DRIVE PUSH │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. MANDATORY DOSSIER GATE (before ANY JSON writes):                       │
│    For each of the 4 stocks in this batch:                                  │
│    a. Confirm `docs/blogs/<SYMBOL>_dossier.html` exists on disk.      │
│    b. Confirm file size ≥ 30 KB.                                            │
│    c. If MISSING or undersized → Status stays PENDING. Log error. Skip      │
│       JSON update for that stock. Re-queue at top of next batch.             │
│    d. If OK → Proceed to JSON update for that stock only.                   │
│ 2. Independent Reviewer Audit: Double-check all metrics via live search.    │
│ 3. Update `data/watchlist/IN.json` strictly IN-PLACE.             │
│    - Only write `Status = COMPLETED` for stocks that PASSED step 1.         │
│ 4. Update `data/shortlist/IN.json` strictly IN-PLACE.             │
│ 5. Print console execution summary (include dossier gate pass/fail per stock)│
└─────────────────────────────────────────────────────────────────────────────┘
```
<!-- /MARKET -->
<!-- MARKET US -->
1. **Reconciliation & Queue Selection:**
   - Ingest `data/watchlist/US.json` and `data/shortlist/US.json`.
   - Select the next 4 pending candidates from `watchlist.active` where `Deep Research Status` is `'PENDING'` or empty.
2. **Dedicated Subagent Dispatch (1 Agent per Company):**
   - Launch an independent research subagent for each of the 4 companies to eliminate context dilution.
3. **Deep Underwriting & Wikipedia HTML Dossier Generation:**
   - Subagent executes two-step live web search, financial forensics, and support-level calculation.
   - Subagent generates the self-contained HTML research dossier in `docs/blogs/<SYMBOL>_dossier.html` using the complete Wikipedia HTML design system, fonts, floated infobox, decision banner, wikitables, and 25–40+ SEC EDGAR citations from `us_company_report`.
4. **Displacement Economics & Registry Updates:**
   - Reconcile the 10 Core + 10 Tactical + 5 Leveraged slots in `data/shortlist/US.json`.
   - Update `data/watchlist/US.json` marking evaluated rows `COMPLETED` and setting `Research Dossier Path`.
   - If Layer 1 failed, move candidate to `watchlist.archive` with full forensic reason.
5. **Master Portal Regeneration:**
   - Run `python3 scripts/build_dossier_portal.py` to regenerate `docs/blogs/index.html` and `docs/blogs/dossiers.json`.
6. **Report Summary:** Present a structured summary table of the 4 evaluated candidates and shortlist displacements to the user.
<!-- /MARKET -->

<!-- MARKET IN -->
---

### RUN SUMMARY OUTPUT FORMAT:

At the conclusion of each 4-stock run, print a clear console execution summary:

```text
================================================================================
AUTONOMOUS UNDERWRITING RUN COMPLETE (Batch of 4)
================================================================================
• Research Cycle: Cycle [X]
• Candidates Processed (4 Securities):
  1. [SYMBOL1] — Type: [CURRENT_HOLDING/AUTOWRITTEN] | Gate: [PASS/FAIL] | KPIs: [4/4_PASS] | Posture: [AT_SUPPORT/EXTENDED] | Verdict: [KEEP_COMPOUNDING / ACCUMULATE / TRIM / REPLACE / ADDED_NEW / DEFERRED]
  2. [SYMBOL2] — Type: [CURRENT_HOLDING/AUTOWRITTEN] | Gate: [PASS/FAIL] | KPIs: [3/4_PASS] | Posture: [AT_SUPPORT/EXTENDED] | Verdict: [KEEP_COMPOUNDING / ACCUMULATE / TRIM / REPLACE / ADDED_NEW / DEFERRED]
  3. [SYMBOL3] — Type: [CURRENT_HOLDING/AUTOWRITTEN] | Gate: [PASS/FAIL] | KPIs: [FAIL_KPIS] | Posture: [SUPPORT_BROKEN] | Verdict: [REPLACE_UNDERPERFORMER / REJECTED_BELOW_HURDLE]
  4. [SYMBOL4] — Type: [CURRENT_HOLDING/AUTOWRITTEN] | Gate: [PASS/FAIL] | KPIs: [4/4_PASS] | Posture: [AT_SUPPORT] | Verdict: [ADDED_NEW / QUALIFIED_DEFERRED]

• Active Holding Performance & Replacement Matrix:
  - [HOLDING_SYM] (Impaired: Broken 50-DMA, OPM compression) ──▶ Rotate into [CHALLENGER_SYM] (4/4 KPIs, AT_SUPPORT, Asym 4.2:1)
  - [HOLDING_SYM] (Profit Booking: Climax run >2.5x ATR, RSI >82) ──▶ Trim 40% position to harvest gains

• Peer Discoveries & Watchlist Additions (Source Type = DEEP_RESEARCH_PEER):
  - From [SYMBOL1]: [PEER_A] (Added to watchlist.active — Reason: ROCE 24%, 3Y Sales CAGR 28%)
  - From [SYMBOL2]: None / [PEER_B]

• Shortlist Status (data/shortlist/IN.json):
  - Current Holdings Underwritten: [K] positions monitored
  - Core Alpha Autowritten Challengers: [X]/10 slots filled
  - Tactical Momentum Autowritten Challengers: [Y]/10 slots filled
  - Manual Protected Entries: [Z] slots preserved

• Company Blogs Created/Updated (Wikipedia HTML Dossiers in docs/blogs/):
  - docs/blogs/[SYMBOL1]_dossier.html
  - docs/blogs/[SYMBOL2]_dossier.html
  - docs/blogs/[SYMBOL3]_dossier.html
  - docs/blogs/[SYMBOL4]_dossier.html

• Watchlist Status: [N]/150 rows in watchlist.active | [M] in watchlist.archive | [P] pending in Cycle [X]
• Google Drive Status: All JSON record files and company blogs synced in-place.
================================================================================
```

<!-- /MARKET -->
