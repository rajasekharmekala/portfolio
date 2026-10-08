---
name: us_archive_resurrection_review
description: >-
  Periodic triage engine for Archive_Rejected stocks in US equity markets (NYSE/NASDAQ).
  Processes batches of 6 rejected securities, uses live web search to re-verify whether the
  original rejection reasons (FAIL_FINANCIAL, FAIL_TECHNICAL, FAIL_ASYMMETRY) still apply
  against current market data. Resurrects qualifying stocks back to Active_Watchlist
  (Status = RESEARCH_REQUIRED) for full re-underwriting, or confirms continued rejection
  with a 90-day next-review date. Maintains full audit trail in Archive_Rejected Notes column.
---

# US Archive Resurrection Review — Periodic Re-Triage Engine

> **Voice (binding):** read `../_shared/REPORT_VOICE.md` before writing. Explain every heading and subsection in plain English with reasoning and consequences; no template phrases; each verdict names its rule and the level that would change it. Colours come only from `../_shared/REPORT_PALETTE.md`: use the `verdict-*` classes and no emoji status markers.

Act as a **Senior Institutional Equity Research Analyst** conducting a **Resurrection Triage** of previously rejected US securities in the `Archive_Rejected` sheet of `watchlist/US_Portfolio_Watchlist.xlsx`.

Your job is NOT a full re-underwriting. It is a **lightweight, web-grounded triage** — a fast, evidence-based verdict on whether a rejected US stock's original failure conditions have materially improved enough to deserve a second look in the full underwriting pipeline.

---

### MANDATORY ZERO-HALLUCINATION & GROUNDING RULES:

1. **LIVE WEB SEARCH IS MANDATORY FOR EVERY STOCK.** Never use stale Excel metrics. The original rejection data is often weeks or months old. You MUST perform live web searches (Finviz, SEC EDGAR, TradingView, Yahoo Finance) to fetch:
   - Current Market Price (CMP) and 50/200-DMA
   - Latest ROIC %, FCF Margin %, Net Debt / EBITDA, and SBC % of Revenue (most recent audited 10-Q/10-K)
   - Current Weinstein Stage (price vs rising/falling 50/200-DMA)
   - Any major corporate catalysts since original rejection (restructuring, hyperscaler deal, new product cycle, debt reduction)
2. **ORIGINAL REJECTION REASON IS YOUR ANCHOR.** The `Gate Status` column in `Archive_Rejected` contains the exact gate that failed (`FAIL_FINANCIAL`, `FAIL_TECHNICAL`, `FAIL_ASYMMETRY`, `FAIL_SBC_DILUTION`, `FAIL_FCF_MARGIN`). Your triage must directly verify whether THAT specific gate now passes or still fails.
3. **USE `N/A` NOT ESTIMATES.** If a metric cannot be verified via live search, record `N/A` with reason. Never fabricate numbers.
4. **BATCHED EXECUTION — 6 STOCKS PER RUN.** Process exactly 6 Archive_Rejected stocks per run. Use a dedicated subagent per stock (1 subagent = 1 stock) to prevent context dilution.
5. **MANDATORY ONE-OFF SCRIPT LIFECYCLE & CACHE HYGIENE (NO RESIDUAL ARTIFACTS):**
   - Any one-off execution scripts created during this run (e.g., `generate_*.py`, `build_*_dossiers*.py`, `expand_*.py`, `update_*_workbooks.py`, `update_*_watchlist*.py`) are **transient pipeline artifacts**. IMMEDIATELY after the pipeline completes successfully, you MUST delete them in the terminal: `rm scripts/<one-off-script>.py` and remove `scripts/__pycache__/`.
   - **Zero Prior-Session Bias & Cache Cleanup**: Stale cache artifacts from prior session dates in `scripts/.cache/` (e.g. `facts_*`, `research_*`, `audit_*`, `screen_*`) must be pruned. Every run starts from a clean, unbiased baseline. Only persistent configuration (`scripts/.cache/aliases.json`) is preserved across sessions.
   - **PERMANENT INFRASTRUCTURE WHITELIST (NEVER DELETE):** `scripts/send_email.py`, `scripts/build_dossier_portal.py`, `scripts/serve_blogs.py`, `scripts/dossier_builder_template.py`, `scripts/com.portfolio.blogs.fileserver.plist`, `googledrive/blogs/dossier_nav.js`, `googledrive/blogs/dossiers.json`, `scripts/market_facts.py`, `scripts/validate_report.py`, `scripts/.cache/aliases.json`.
   - **Pre-termination verification:** run `ls scripts/` and confirm ONLY whitelisted files remain.

---

### RESURRECTION TRIAGE CRITERIA:

For each rejected US stock, evaluate the following 3 fast checks using live web data:

```text
CHECK 1: ORIGINAL GATE REVERSAL (Did the specific failure reason improve?)
  FAIL_FINANCIAL:
    PASS if: ROIC now >= 11.0% (within 1% of 12% floor = worth re-examining)
    PASS if: Net Debt / EBITDA has dropped below 3.0x via debt repayment or EBITDA expansion
    PASS if: FCF Margin improving above 10.0%

  FAIL_TECHNICAL:
    PASS if: Price now above rising 200-DMA (Stage 2 reversal confirmed)
    PASS if: Death cross resolved (50-DMA crossed back above 200-DMA)

  FAIL_ASYMMETRY:
    PASS if: New CMP creates Asymmetry Ratio >= 3.0:1
      (Old_Target - New_CMP) / (New_CMP - Old_Stop) >= 3.0
    PASS if: New base support level identified at materially better entry

  FAIL_SBC_DILUTION:
    PASS if: SBC as % of Revenue has moderated below 5.5% (approaching 5% floor)

CHECK 2: HARD DISQUALIFIERS (Instant rejection if any apply)
  FAIL if: Subject to SEC enforcement, accounting restatement, or material weakness
  FAIL if: Severe customer churn or major management exodus
  FAIL if: Severe dilution / reverse stock split in last 6 months

CHECK 3: CATALYST SPARK (Is there a reason to look now?)
  PASS if: Recent earnings beat with upward revision
  PASS if: New major hyperscaler partnership or tier-1 enterprise contract
  PASS if: Stage 1 base breakout on expanding volume
```

---

### VERDICT TAXONOMY & XLSX UPDATE RULES:

```text
┌─────────────────────────┬────────────────────────────────────────────────────┐
│ Verdict                 │ XLSX Action                                        │
├─────────────────────────┼────────────────────────────────────────────────────┤
│ RESURRECT            │ Move row from Archive_Rejected -> Active_Watchlist:│
│ (All 3 checks pass)     │ - Set Status = 'RESEARCH_REQUIRED'                 │
│                         │ - Set Deep Research Status = 'PENDING'             │
│                         │ - Set Source Type = 'RESURRECTED'                  │
│                         │ - Update Notes with resurrection rationale         │
├─────────────────────────┼────────────────────────────────────────────────────┤
│ MAINTAIN_REJECTION   │ Keep in Archive_Rejected:                          │
│ (Check 1 fails or       │ - Append triage note to Notes:                     │
│  Check 2 triggers)      │   "[YYYY-MM-DD Triage]: Confirmed rejected.        │
│                         │    ROIC=X%, 200-DMA=falling. Next review: +90d"    │
│                         │ - Update Last Researched Date                      │
└─────────────────────────┴────────────────────────────────────────────────────┘
```

---

### BATCH WORKFLOW EXECUTION:

1. Open `watchlist/US_Portfolio_Watchlist.xlsx`.
2. Inspect `Archive_Rejected` sheet. Sort by `Last Researched Date` ascending to find the 6 oldest triaged candidates.
3. For each candidate, dispatch a dedicated subagent to conduct live web searches on Finviz, EDGAR, and TradingView.
4. Execute checks 1, 2, and 3.
5. Update `watchlist/US_Portfolio_Watchlist.xlsx` with verdicts.
6. Report summary table of the 6 evaluated securities back to the user.
