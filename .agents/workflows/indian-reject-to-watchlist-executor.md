---
description: "Indian Archive Resurrection Review — Processes the next batch of 6 NSE/BSE Archive_Rejected stocks, uses live web search to verify current fundamentals and technical posture against original rejection reasons, and updates Zerodha_Watchlist.xlsx in-place."
---

# Indian Reject to Watchlist Workflow Executor

This workflow is the **Indian Archive Resurrection Review Engine**. It processes the next batch of 6 NSE/BSE Archive_Rejected stocks, uses live web search to verify current fundamentals and technical posture against the original rejection reasons, and updates `Zerodha_Watchlist.xlsx` in-place.

This workflow is designed to run **daily at 20:00** (after Indian market close) to review rejected stocks that may have changed their fundamental or technical posture.

---

## 0. Governing Standards & Non-Negotiable Rules

Before executing any step, you MUST read and internalize the following governing documents. These are the **single source of truth** for all underwriting logic, data rules, and report formatting.

### 0.1 Required Skill & Standard Files

| File | Purpose |
|---|---|
| [Archive Resurrection Review Skill](file:///Users/mereddy/Desktop/github/portfolio/.agents/skills/archive_resurrection_review/SKILL.md) | Resurrection triage criteria, batch processing rules, watchlist update format, 90-day review cycle |
| [Report Editorial Standard](file:///Users/mereddy/Desktop/github/portfolio/.agents/skills/_shared/REPORT_EDITORIAL_STANDARD.md) | HTML report structure, typography, color palette, callout boxes, validation rules |

### 0.2 Core Non-Negotiables

1. **Batch Size = 6**: Process exactly 6 Archive_Rejected stocks per run. Do NOT process more or fewer.
2. **Lightweight Triage**: This is a triage, not a full underwriting. Focus on whether the original rejection reason has been invalidated.
3. **Live Web Search**: Use DuckDuckGo web search to verify current fundamentals and technical posture. Do NOT rely on stale data.
4. **Original Rejection Reason**: Each stock must be evaluated against its specific original rejection reason. A stock rejected for weak margins is only resurrected if margins have improved.
5. **NSE/BSE Only**: Only process stocks listed on NSE or BSE.
6. **In-Place Update**: `Zerodha_Watchlist.xlsx` must be updated in-place. Do NOT create a new file.
7. **90-Day Review**: Stocks resurrected to the watchlist are eligible for re-review after 90 days.
8. **Rupee Arithmetic**: All financial figures in INR. Use Indian number formatting (lakh/crore) where appropriate.

---

## 1. Execution Pipeline (Step-by-Step)

```mermaid
graph TD
    A[Step 1: Read Governing Standards] --> B[Step 2: Load Archive_Rejected List]
    B --> C[Step 3: Select Next Batch of 6]
    C --> D[Step 4: Live Web Search & Verification]
    D --> E[Step 5: Evaluate Against Original Rejection Reason]
    E --> F[Step 6: Apply Indian-Specific Gates]
    F --> G[Step 7: Classify: RESURRECT or REMAIN REJECTED]
    G --> H[Step 8: Update Zerodha_Watchlist.xlsx In-Place]
    H --> I[Step 9: Generate Summary Report]
    I --> J[Step 10: Validate & Dispatch]
    J --> K[Step 11: Workspace Hygiene]
```

---

### Step 1: Read Governing Standards

1. Read the full `archive_resurrection_review` skill file.
2. Read the `REPORT_EDITORIAL_STANDARD.md`.
3. Confirm you understand the triage criteria, batch processing rules, and watchlist update format.

> [!NOTE]
> Do NOT proceed to Step 2 until you have fully internalized the skill's triage logic.

---

### Step 2: Load Archive_Rejected List

1. Read the Archive_Rejected list from the portfolio (typically `Zerodha_Archive.xlsx` or the rejected section of the watchlist).
2. Parse all rejected stocks: symbol, original rejection reason, rejection date, key metrics at rejection.
3. Identify stocks that have already been resurrected — exclude these.

```bash
# Verify the archive file exists and is readable
ls -la watchlist/Zerodha_Archive.xlsx
```

---

### Step 3: Select Next Batch of 6

1. From the remaining rejected stocks (not yet resurrected), select the **next 6** in priority order.
2. Priority order is determined by:
   - Time since rejection (longest rejected first)
   - Recent news or catalysts
   - Sector diversification
3. Log the selected batch with symbols and original rejection reasons.

---

### Step 4: Live Web Search & Verification

For **each of the 6 stocks**, perform live web search:

1. **Current Fundamentals**: Latest revenue, margins, FCF, debt, promoter holding.
2. **Technical Posture**: Current price, trend, key levels, volume.
3. **Recent News**: Any material events since rejection (earnings, M&A, regulatory, management changes).
4. **Analyst Consensus**: Current ratings and price targets.

> [!CAUTION]
> Use DuckDuckGo web search extensively for each stock. Verify current data. Do NOT rely on cached or stale information.

---

### Step 5: Evaluate Against Original Rejection Reason

For each stock, compare current state against the original rejection reason:

1. **Was the rejection reason specific?** (e.g., "Operating margin < 15%")
2. **Has that specific reason been invalidated?** (e.g., "Operating margin now 22%")
3. **Are there new positive catalysts?** (e.g., "New capacity expansion, government policy tailwind")
4. **Are there new negative risks?** (e.g., "Promoter pledge increase, regulatory probe")

Document the evaluation with specific data points.

---

### Step 6: Apply Indian-Specific Gates

For each stock, apply the Indian-specific rejection gates:

| Gate | Threshold | Status |
|---|---|---|
| `FAIL_MARGIN` | Operating margin < 15% | PASS/FAIL |
| `FAIL_DEBT` | Debt/Equity > 1.0 | PASS/FAIL |
| `FAIL_PROMOTER_PLEDGE` | Promoter pledge > 10% | PASS/FAIL |
| Other gates from skill | As defined | PASS/FAIL |

A stock must pass ALL gates to be eligible for resurrection.

---

### Step 7: Classify: RESURRECT or REMAIN REJECTED

For each stock, assign a classification:

- **RESURRECT**: Original rejection reason invalidated, all gates passed, positive catalysts present.
- **REMAIN REJECTED**: Original rejection reason still valid, or new negative risks outweigh positives.

Document the classification with a 2–3 sentence rationale.

---

### Step 8: Update Zerodha_Watchlist.xlsx In-Place

1. For each **RESURRECT** stock:
   - Add to `watchlist/Zerodha_Watchlist.xlsx` with: symbol, sector, current price, resurrection date, original rejection reason, new thesis.
   - Set status to `WATCHLIST`.
   - Set 90-day review date.
2. For each **REMAIN REJECTED** stock:
   - Update the rejection date to today (reset the 90-day clock).
   - Add a note with the re-evaluation rationale.
3. Do NOT create a new file. Modify the existing workbook.

---

### Step 9: Generate Summary Report

1. Create a brief HTML summary report:
   - **Header**: Date, "Indian Archive Resurrection Review — Batch of 6"
   - **Table**: Symbol, Original Rejection, Current Status, Classification, Rationale
   - **Summary**: X resurrected, Y remain rejected
2. Write to `googledrive/newsletters/IND_Archive_Resurrection_<YYYY-MM-DD>.html`.

```bash
# Verify the report was created
ls -la googledrive/newsletters/IND_Archive_Resurrection_$(date +%Y-%m-%d).html
```

---

### Step 10: Validate & Dispatch

```bash
python3 scripts/validate_report.py --kind summary
```

- If `RESULT: PASS` → upload to Google Drive and send email.
- If `RESULT: FAIL` → fix and re-validate.

```bash
python3 scripts/send_email.py --report "googledrive/newsletters/IND_Archive_Resurrection_$(date +%Y-%m-%d).html" --subject "Indian Archive Resurrection Review - $(date +%Y-%m-%d)"
```

---

### Step 11: Workspace Hygiene

1. Delete any transient scripts or temp files created during execution.
2. Preserve the permanent infrastructure whitelist:
   - `scripts/validate_report.py`
   - `scripts/send_email.py`
   - `watchlist/Zerodha_Watchlist.xlsx`
   - `watchlist/Zerodha_Archive.xlsx`
   - `googledrive/` directory structure

> [!NOTE]
> The workflow is complete when the watchlist is updated, the report is dispatched, and the workspace is clean.
