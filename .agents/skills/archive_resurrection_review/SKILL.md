---
name: archive_resurrection_review
description: >-
  Re-examines the next batch of archived rejected names for one market (IN or US) against current data and decides whether any move back to the watchlist. Market-specific blocks are marked.

---

> **Market blocks (binding):** this skill covers both markets. Read `.agents/config/markets.json` for the market in this run (`IN` or `US`). Follow the text that is not inside a market block, and inside a market block follow only the block whose label matches the run's market. Ignore the other block. Figures, currency, exchange names and data sources differ by market; never mix them.

<!-- MARKET IN -->
# Archive Resurrection Review — Periodic Re-Triage Engine
<!-- /MARKET -->
<!-- MARKET US -->
# US Archive Resurrection Review — Periodic Re-Triage Engine
<!-- /MARKET -->

> **Voice (binding):** read `../_shared/REPORT_VOICE.md` before writing. Explain every heading and subsection in plain English with reasoning and consequences; no template phrases; each verdict names its rule and the level that would change it. Colours come only from `../_shared/REPORT_PALETTE.md`: use the `verdict-*` classes and no emoji status markers.

<!-- MARKET IN -->
Act as a **Senior Institutional Equity Research Analyst** conducting a **Resurrection Triage** of previously rejected securities in the `watchlist.archive` array of `data/watchlist/IN.json`.
<!-- /MARKET -->
<!-- MARKET US -->
Act as a **Senior Institutional Equity Research Analyst** conducting a **Resurrection Triage** of previously rejected US securities in the `watchlist.archive` array of `data/watchlist/US.json`.
<!-- /MARKET -->

<!-- MARKET IN -->
Your job is NOT a full re-underwriting. It is a **lightweight, web-grounded triage** — a fast, evidence-based verdict on whether a rejected stock's original failure conditions have materially improved enough to deserve a second look in the full underwriting pipeline.
<!-- /MARKET -->
<!-- MARKET US -->
Your job is NOT a full re-underwriting. It is a **lightweight, web-grounded triage** — a fast, evidence-based verdict on whether a rejected US stock's original failure conditions have materially improved enough to deserve a second look in the full underwriting pipeline.
<!-- /MARKET -->

---

### MANDATORY ZERO-HALLUCINATION & GROUNDING RULES:

<!-- MARKET IN -->
1. **LIVE WEB SEARCH IS MANDATORY FOR EVERY STOCK.** Never use stale Excel metrics. The original rejection data is often weeks or months old. You MUST perform live Google searches (Screener.in, TradingView, NSE/BSE exchange filings, Economic Times Markets, Moneycontrol) to fetch:
   - Current Market Price (CMP) and 200-DMA
   - Latest ROCE %, Debt-to-Equity, CFO/PAT ratio (most recent audited quarter)
   - Current Weinstein Stage (price vs rising/falling 200-DMA)
   - Any major corporate events since original rejection (management change, demerger, debt repayment, rights issue, SEBI action)
2. **ORIGINAL REJECTION REASON IS YOUR ANCHOR.** The `Gate Status` column in watchlist.archive contains the exact gate that failed (`FAIL_FINANCIAL`, `FAIL_TECHNICAL`, `FAIL_ASYMMETRY`, `FAIL_CFO_PAT`). Your triage must directly verify whether THAT specific gate now passes or still fails.
<!-- /MARKET -->
<!-- MARKET US -->
1. **LIVE WEB SEARCH IS MANDATORY FOR EVERY STOCK.** Never use stale Excel metrics. The original rejection data is often weeks or months old. You MUST perform live web searches (Finviz, SEC EDGAR, TradingView, Yahoo Finance) to fetch:
   - Current Market Price (CMP) and 50/200-DMA
   - Latest ROIC %, FCF Margin %, Net Debt / EBITDA, and SBC % of Revenue (most recent audited 10-Q/10-K)
   - Current Weinstein Stage (price vs rising/falling 50/200-DMA)
   - Any major corporate catalysts since original rejection (restructuring, hyperscaler deal, new product cycle, debt reduction)
2. **ORIGINAL REJECTION REASON IS YOUR ANCHOR.** The `Gate Status` column in `watchlist.archive` contains the exact gate that failed (`FAIL_FINANCIAL`, `FAIL_TECHNICAL`, `FAIL_ASYMMETRY`, `FAIL_SBC_DILUTION`, `FAIL_FCF_MARGIN`). Your triage must directly verify whether THAT specific gate now passes or still fails.
<!-- /MARKET -->
3. **USE `N/A` NOT ESTIMATES.** If a metric cannot be verified via live search, record `N/A` with reason. Never fabricate numbers.
4. **BATCHED EXECUTION — 6 STOCKS PER RUN.** Process exactly 6 watchlist.archive stocks per run. Use a dedicated subagent per stock (1 subagent = 1 stock) to prevent context dilution.
<!-- MARKET IN -->

<!-- /MARKET -->
5. **MANDATORY ONE-OFF SCRIPT LIFECYCLE & CACHE HYGIENE (NO RESIDUAL ARTIFACTS):**
   - Scratch code lives only in `<RUN_DIR>` and is deleted with it (RUN_PROTOCOL sections 1 and 5).
   - **Run directory:** nothing from earlier runs is read. Cleanup follows `../_shared/RUN_PROTOCOL.md` section 5. Repository scripts are never deleted.
   - **Permanent repository scripts (never delete or modify without the user):** `scripts/send_email.py`, `scripts/build_dossier_portal.py`, `scripts/serve_blogs.py`, `scripts/market_facts.py`, `scripts/validate_report.py`.
<!-- MARKET IN -->
   - **Pre-termination verification:** run `ls scripts/` and confirm ONLY whitelisted files remain. Leaving one-off generator/update scripts behind is a pipeline failure.
<!-- /MARKET -->
<!-- MARKET US -->
   - **Pre-termination verification:** run `ls scripts/` and confirm ONLY whitelisted files remain.
<!-- /MARKET -->

---

### RESURRECTION TRIAGE CRITERIA:

<!-- MARKET IN -->
For each rejected stock, evaluate the following 3 fast checks using live web data:
<!-- /MARKET -->
<!-- MARKET US -->
For each rejected US stock, evaluate the following 3 fast checks using live web data:
<!-- /MARKET -->

<!-- MARKET IN -->
```
<!-- /MARKET -->
<!-- MARKET US -->
```text
<!-- /MARKET -->
CHECK 1: ORIGINAL GATE REVERSAL (Did the specific failure reason improve?)
  FAIL_FINANCIAL:
<!-- MARKET IN -->
    PASS if: ROCE now >= 14% (within 1% of floor = worth re-examining)
    PASS if: D/E has materially dropped (e.g., 0.89x to 0.65x via QIP/FPO)
    PASS if: CFO/PAT trend improving (last 2 quarters positive)
<!-- /MARKET -->
<!-- MARKET US -->
    PASS if: ROIC now >= 11.0% (within 1% of 12% floor = worth re-examining)
    PASS if: Net Debt / EBITDA has dropped below 3.0x via debt repayment or EBITDA expansion
    PASS if: FCF Margin improving above 10.0%
<!-- /MARKET -->

  FAIL_TECHNICAL:
    PASS if: Price now above rising 200-DMA (Stage 2 reversal confirmed)
    PASS if: Death cross resolved (50-DMA crossed back above 200-DMA)

  FAIL_ASYMMETRY:
    PASS if: New CMP creates Asymmetry Ratio >= 3.0:1
      (Old_Target - New_CMP) / (New_CMP - Old_Stop) >= 3.0
<!-- MARKET IN -->
    PASS if: New support level identified at materially better entry
<!-- /MARKET -->
<!-- MARKET US -->
    PASS if: New base support level identified at materially better entry
<!-- /MARKET -->

<!-- MARKET IN -->
  FAIL_CFO_PAT:
    PASS if: Trailing 4Q CFO/PAT is now >= 0.65x (improving trend)
<!-- /MARKET -->
<!-- MARKET US -->
  FAIL_SBC_DILUTION:
    PASS if: SBC as % of Revenue has moderated below 5.5% (approaching 5% floor)
<!-- /MARKET -->

<!-- MARKET IN -->
CHECK 2: MACRO / CORPORATE CATALYST (New positive development since rejection?)
  Search for any events after original rejection date:
    - Significant debt repayment or QIP reducing D/E
    - Management change (new promoter, CEO, strategic pivot)
    - Large order win / government contract / PLI scheme inclusion
    - SEBI/regulatory clearance (if originally flagged for compliance risk)
    - Demerger or subsidiary listing unlocking hidden value
    - Price correction of >= 25% creating valuation normalization
  PASS: Any single credible, verifiable catalyst qualifies
<!-- /MARKET -->
<!-- MARKET US -->
CHECK 2: HARD DISQUALIFIERS (Instant rejection if any apply)
  FAIL if: Subject to SEC enforcement, accounting restatement, or material weakness
  FAIL if: Severe customer churn or major management exodus
  FAIL if: Severe dilution / reverse stock split in last 6 months
<!-- /MARKET -->

<!-- MARKET IN -->
CHECK 3: MINIMUM TIME GATE (Prevent premature recycling)
  - Rejected < 60 days ago: CANNOT resurrect on technical reversal alone
    (must also pass Check 1 or Check 2)
  - Rejected > 90 days ago: ANY single check passing = RESURRECT
  - Rejected > 180 days ago: AUTO-RESURRECT regardless
    (markets and fundamentals have changed enough)
<!-- /MARKET -->
<!-- MARKET US -->
CHECK 3: CATALYST SPARK (Is there a reason to look now?)
  PASS if: Recent earnings beat with upward revision
  PASS if: New major hyperscaler partnership or tier-1 enterprise contract
  PASS if: Stage 1 base breakout on expanding volume
<!-- /MARKET -->
```

---

<!-- MARKET IN -->
### RESURRECTION VERDICT TAXONOMY:
<!-- /MARKET -->
<!-- MARKET US -->
### VERDICT TAXONOMY & JSON UPDATE RULES:
<!-- /MARKET -->

<!-- MARKET IN -->
- RESURRECTED: >= 1 check passes (with time gate respected)
  Action: Move to watchlist.active, Status=RESEARCH_REQUIRED, Source_Type=RESURRECTION_CANDIDATE

- CONFIRMED_REJECTED: All 3 checks fail
  Action: Remain in watchlist.archive, set Next_Review_Date = today + 90 days in Notes

- PERMANENT_REJECT: Structural/terminal failure — negative equity, SEBI ban, promoter fraud, liquidation
  Action: Flag PERMANENT_REJECT in Notes — never auto-resurface again
<!-- /MARKET -->
<!-- MARKET US -->
```text
┌─────────────────────────┬────────────────────────────────────────────────────┐
│ Verdict                 │ JSON Action                                        │
├─────────────────────────┼────────────────────────────────────────────────────┤
│ RESURRECT            │ Move row from watchlist.archive -> watchlist.active:│
│ (All 3 checks pass)     │ - Set Status = 'RESEARCH_REQUIRED'                 │
│                         │ - Set Deep Research Status = 'PENDING'             │
│                         │ - Set Source Type = 'RESURRECTED'                  │
│                         │ - Update Notes with resurrection rationale         │
├─────────────────────────┼────────────────────────────────────────────────────┤
│ MAINTAIN_REJECTION   │ Keep in watchlist.archive:                          │
│ (Check 1 fails or       │ - Append triage note to Notes:                     │
│  Check 2 triggers)      │   "[YYYY-MM-DD Triage]: Confirmed rejected.        │
│                         │    ROIC=X%, 200-DMA=falling. Next review: +90d"    │
│                         │ - Update Last Researched Date                      │
└─────────────────────────┴────────────────────────────────────────────────────┘
```
<!-- /MARKET -->

---

<!-- MARKET IN -->
### CANONICAL JSON RECORD SCHEMAS:
<!-- /MARKET -->
<!-- MARKET US -->
### BATCH WORKFLOW EXECUTION:
<!-- /MARKET -->

<!-- MARKET IN -->
`watchlist.archive` array (22 columns):
Symbol, Company Name, Source Type, Status, Action Verdict, Deep Research Status,
Research Cycle, Gate Status, KPI Health, Entry Posture, Strategy Fit, Shortlist Action,
Last Researched Date, Strategy Bucket, Strategy Book, Account Scope, As of Date,
Theme Tags, Catalyst Timeline, Investment Thesis, Summary Rationale, Notes
<!-- /MARKET -->
<!-- MARKET US -->
1. Open `data/watchlist/US.json`.
2. Inspect `watchlist.archive` array. Sort by `Last Researched Date` ascending to find the 6 oldest triaged candidates.
3. For each candidate, dispatch a dedicated subagent to conduct live web searches on Finviz, EDGAR, and TradingView.
4. Execute checks 1, 2, and 3.
5. Update `data/watchlist/US.json` with verdicts.
6. Report summary table of the 6 evaluated securities back to the user.
<!-- /MARKET -->

<!-- MARKET IN -->
When RESURRECTING a stock, write to watchlist.active with:
  Symbol: <same>
  Company Name: <same>
  Source Type: RESURRECTION_CANDIDATE
  Status: RESEARCH_REQUIRED
  Action Verdict: (blank — to be determined by full underwriting)
  Deep Research Status: PENDING
  Research Cycle: 1
  Gate Status: PENDING_RECHECK
  KPI Health: PENDING_RECHECK
  Entry Posture: PENDING_RECHECK
  Strategy Fit: <original Strategy Fit from archive>
  Last Researched Date: <today>
  Strategy Bucket: <original>
  Notes: RESURRECTED from Archive on <date>. Original rejection: <Gate Status>.
         Resurrection trigger: <which check passed and why>

When CONFIRMING REJECTION, update watchlist.archive Notes:
  RESURRECTION_REVIEW: <date> -> CONFIRMED_REJECTED. <brief reason>.
  Next review: <date + 90 days>. Original gate still applies: <evidence>.

---

### STEP-BY-STEP AUTONOMOUS EXECUTION ALGORITHM:

PHASE 1: FRESH GOOGLE DRIVE INGESTION
  1. Fetch data/watchlist/IN.json fresh from sheets/ and shortlist/.
  2. Load `watchlist.archive` array.
  3. Load `watchlist.active` array (to check 150-row cap before resurrection).

PHASE 2: BATCH SELECTION — NEXT 6 STOCKS
  Priority ordering:
  1. FIRST: Notes contains 'DOSSIER_PENDING' — unreviewed, no dossier (highest urgency)
  2. SECOND: FAIL_ASYMMETRY stocks — price correction may have created opportunity
  3. THIRD: FAIL_TECHNICAL stocks — breakdowns can reverse; check Stage 2 emergence
  4. FOURTH: FAIL_FINANCIAL stocks — financials improve slowly; lower urgency
  5. LAST: Already-reviewed stocks where Next_Review_Date <= today
  Skip all PERMANENT_REJECT stocks entirely.
  Select exactly 6 stocks.

PHASE 3: DISPATCH 6 INDEPENDENT TRIAGE SUBAGENTS (1 PER STOCK)
  Each subagent receives:
    - Symbol, Company Name
    - Original Gate Status (e.g., FAIL_TECHNICAL)
    - Original Summary Rationale (exact failure metrics)
    - Original Last Researched Date
    - Original Strategy Bucket (CORE_ALPHA or TACTICAL_MOMENTUM)

PHASE 4: SUBAGENT TRIAGE EXECUTION (PER STOCK)
  Each triage subagent:
  1. READS original rejection from passed context.
  2. PERFORMS live web searches:
     a. "{SYMBOL} NSE current price 200 DMA TradingView" (Technical)
     b. "{SYMBOL} screener.in ROCE debt equity CFO PAT {CURRENT_YEAR}" (Financial)
     c. "{COMPANY_NAME} NSE news catalyst 2025 2026" (Corporate events)
     d. "{SYMBOL} NSE latest annual report results" (Fundamental updates)
  3. EVALUATES the 3 Checks using live data vs original rejection.
  4. RETURNS structured triage payload to orchestrator:
     {
       symbol, original_gate, check1_result, check2_result, check3_result,
       verdict, resurrection_trigger, next_review_date,
       current_cmp, current_roce, current_de, current_cfo_pat,
       current_stage, key_evidence_urls
     }

PHASE 5: ORCHESTRATOR RECONCILIATION & JSON UPDATES
  For RESURRECTED stocks:
    1. Check watchlist.active row count < 150 (capacity gate).
    2. Add to watchlist.active with Status=RESEARCH_REQUIRED, Source_Type=RESURRECTION_CANDIDATE.
    3. Update watchlist.archive Notes: "RESURRECTED on <date>. Moved to watchlist.active."
    4. Do NOT delete from watchlist.archive — keep for full audit trail.

  For CONFIRMED_REJECTED stocks:
    1. Update watchlist.archive Notes with review outcome and next review date.

  For PERMANENT_REJECT stocks:
    1. Update Notes: "PERMANENT_REJECT: <reason>. No future triage."

  Save data/watchlist/IN.json strictly IN-PLACE.

PHASE 6: PRINT TRIAGE RUN SUMMARY (see format below)

---

### RUN SUMMARY OUTPUT FORMAT:

================================================================================
ARCHIVE RESURRECTION TRIAGE COMPLETE (Batch of 6)
================================================================================
watchlist.archive Total: [N] stocks | Reviewed This Run: 6
Stocks Processed:
  1. [SYMBOL] | Gate: FAIL_TECHNICAL -> Check 1: PASS Stage 2 reversal | Verdict: RESURRECTED
  2. [SYMBOL] | Gate: FAIL_FINANCIAL -> Check 1: FAIL ROCE still 11.2% | Check 2: FAIL | Verdict: CONFIRMED_REJECTED (next: DD-MM-YYYY)
  3. [SYMBOL] | Gate: FAIL_ASYMMETRY -> Check 1: PASS Price -38%, Asym ~4.1:1 | Verdict: RESURRECTED
  4. [SYMBOL] | Gate: FAIL_FINANCIAL -> Check 3: PASS >180 days | Verdict: RESURRECTED (auto time gate)
  5. [SYMBOL] | Gate: FAIL_TECHNICAL -> All checks failed | Verdict: CONFIRMED_REJECTED (next: DD-MM-YYYY)
  6. [SYMBOL] | Gate: FAIL_FINANCIAL -> Check 2: PASS QIP reduced D/E 0.89x->0.41x | Verdict: RESURRECTED

Resurrections This Run: [X] stocks added to watchlist.active
Confirmed Rejected: [Y] stocks (next review dates set)
Permanent Rejects Flagged: [Z] stocks

watchlist.active Capacity: [N]/150 rows after resurrections
watchlist.archive Remaining Unreviewed: [M] stocks

Recommended Next Run: Process next 6 Archive stocks.
================================================================================

---

### IMPORTANT OPERATIONAL NOTES:

1. Do NOT trigger a full underwriting during this skill. Resurrected stocks go to watchlist.active
   with Status=RESEARCH_REQUIRED and will be picked up by watchlist_shortlist_underwriting
   in its next normal batch run.

2. Source_Type = RESURRECTION_CANDIDATE signals to the underwriting engine that this stock
   deserves extra scrutiny (it has already failed once). The underwriting engine should note
   the original rejection gate in its analysis and explicitly verify it has now been resolved.

3. The 150-row capacity cap on watchlist.active is hard. If at 148 rows, only 2 resurrections
   can happen. Log this clearly in the run summary.

4. Do not remove stocks from watchlist.archive — they stay as permanent audit record.
   Resurrected stocks appear in BOTH sheets simultaneously.

5. Run cadence: Run manually once every 90 days, or immediately after any major market
   correction (Nifty 50 drawdown > 10%) when many technical rejections may have reversed.
   Current archive has 41 stocks = ~7 batches of 6 to complete one full triage cycle.

<!-- /MARKET -->