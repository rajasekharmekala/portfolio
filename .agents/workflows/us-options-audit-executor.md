---
description: "US Options Position Audit & Setup Structuring — Audits all active options positions in Options_Positions.xlsx against the 4-action matrix, recommends actions, and screens US_Shortlist.xlsx for high-conviction IV/RV squeeze and Long Build-up setups to structure the Top 3."
---

# US Options Audit & Setup Structuring Workflow Executor

This workflow is the **US Options Position Audit & Setup Structuring Engine**. It performs two distinct but related tasks:

1. **Position Audit**: Audits all current active options positions in `Options_Positions.xlsx` against the 4-action matrix (HOLD, ROLL_UP_OUT, CONVERT_SPREAD, KILL) and recommends actions using the `us_options_underwriting` skill.
2. **Setup Screening**: Screens the shortlisted candidates in `US_Shortlist.xlsx` for high-conviction options setups with IV/RV squeeze and Long Build-up signals, and structures the Top 3 setups.

This workflow is designed to run **daily at 09:00** (pre-market) to ensure positions are reviewed before the US market opens.

---

## 0. Governing Standards & Non-Negotiable Rules

Before executing any step, you MUST read and internalize the following governing documents. These are the **single source of truth** for all underwriting logic, data rules, and report formatting.

### 0.1 Required Skill & Standard Files

| File | Purpose |
|---|---|
| [US Options Underwriting Skill](file:///Users/mereddy/Desktop/github/portfolio/.agents/skills/us_options_underwriting/SKILL.md) | 4-action matrix, CBOE IV Percentile rules, GEX/UOA data, Bull Call Spread & LEAPS structuring, report format |
| [Report Editorial Standard](file:///Users/mereddy/Desktop/github/portfolio/.agents/skills/_shared/REPORT_EDITORIAL_STANDARD.md) | HTML report structure, typography, color palette, callout boxes, validation rules |

### 0.2 Core Non-Negotiables

1. **4-Action Matrix Only**: Every position must be classified into exactly one of: `HOLD`, `ROLL_UP_OUT`, `CONVERT_SPREAD`, or `KILL`. No other actions are permitted.
2. **CBOE Data Rules**: IV Percentile must be sourced from CBOE. Never estimate or approximate.
3. **GEX & UOA**: Gamma Exposure and Unusual Options Activity must be verified from live data before any recommendation.
4. **DTE Constraints**: Bull Call Spreads must be 30–75 DTE. LEAPS must be 180–720 DTE.
5. **Top 3 Setups Only**: The screening phase must produce exactly 3 structured setups, ranked by conviction.
6. **Report Output**: Final report must be written to `googledrive/newsletters/Options_Underwriting_US_<YYYY-MM-DD>.html`.
7. **Validation Gate**: The report must pass `python3 scripts/validate_report.py --kind options` before dispatch.

---

## 1. Execution Pipeline (Step-by-Step)

```mermaid
graph TD
    A[Step 1: Read Governing Standards] --> B[Step 2: Load Options_Positions.xlsx]
    B --> C[Step 3: Audit Each Position vs 4-Action Matrix]
    C --> D{All positions classified?}
    D -->|No| C
    D -->|Yes| E[Step 4: Load US_Shortlist.xlsx]
    E --> F[Step 5: Screen for IV/RV Squeeze & Long Build-up]
    F --> G[Step 6: Structure Top 3 Setups]
    G --> H[Step 7: Generate HTML Report]
    H --> I[Step 8: Validate Report]
    I --> J{Validation PASS?}
    J -->|No| H
    J -->|Yes| K[Step 9: Upload to Google Drive & Dispatch]
    K --> L[Step 10: Workspace Hygiene]
```

---

### Step 1: Read Governing Standards

1. Read the full `us_options_underwriting` skill file.
2. Read the `REPORT_EDITORIAL_STANDARD.md`.
3. Confirm you understand the 4-action matrix, DTE constraints, and report format.

> [!NOTE]
> Do NOT proceed to Step 2 until you have fully internalized the skill's underwriting logic.

---

### Step 2: Load Options_Positions.xlsx

1. Read `Options_Positions.xlsx` from the portfolio root.
2. Parse all active positions: symbol, contract type (call/put), strike, expiry, quantity, entry price, current P&L.
3. Identify any positions that are expired, assigned, or closed — exclude these from the audit.

```bash
# Verify the file exists and is readable
ls -la Options_Positions.xlsx
```

---

### Step 3: Audit Each Position vs 4-Action Matrix

For **each active position**, perform the following:

1. **Fetch live data**: Current IV, IV Percentile (CBOE), GEX, UOA, underlying price, DTE remaining.
2. **Apply the 4-action matrix**:
   - **HOLD**: Position is performing as expected, IV Percentile is favorable, no adverse GEX shift.
   - **ROLL_UP_OUT**: Position is underperforming but the thesis is intact. Roll to a higher strike and/or later expiry.
   - **CONVERT_SPREAD**: Position has significant unrealized gain. Convert to a defined-risk spread to lock in profit and reduce delta.
   - **KILL**: Thesis is broken, IV Percentile is extreme, or GEX is working against the position. Close immediately.
3. **Document the recommendation** for each position with:
   - Action (one of the 4)
   - Rationale (2–3 sentences citing specific data points)
   - If ROLL/CONVERT: specific new strike/expiry
   - If KILL: target exit price and estimated loss

> [!CAUTION]
> Every recommendation MUST cite specific data (IV Percentile value, GEX number, UOA signal). No generic advice.

---

### Step 4: Load US_Shortlist.xlsx

1. Read `US_Shortlist.xlsx` from the portfolio root.
2. Parse all shortlisted candidates: symbol, sector, current price, key metrics.
3. These are the candidates for the setup screening phase.

---

### Step 5: Screen for IV/RV Squeeze & Long Build-up

For **each shortlisted candidate**, perform the following:

1. **IV/RV Squeeze Check**:
   - Current IV vs. Realized Volatility (20-day).
   - IV Percentile (CBOE) — look for IV < 30th percentile (compression).
   - RV trending up while IV is flat or declining = squeeze setup.
2. **Long Build-up Check**:
   - Unusual Options Activity: Large call purchases (not covered calls).
   - Strike OI migration: OI building at strikes above current price.
   - PCR (Put-Call Ratio) declining = bullish positioning.
3. **Score each candidate** on conviction (1–10) based on the strength of both signals.

> [!NOTE]
> Use live web search (DuckDuckGo) to verify current IV, RV, and OI data. Do NOT rely on stale data.

---

### Step 6: Structure Top 3 Setups

From the screened candidates, select the **Top 3** by conviction score and structure each setup:

1. **Setup Type**: Bull Call Spread (30–75 DTE) or LEAPS (180–720 DTE).
2. **Structure**:
   - Buy strike: ATM or slightly OTM
   - Sell strike: 10–15 points above (for spreads)
   - Expiry: Optimal DTE based on catalyst timeline
   - Position size: Based on account allocation rules
3. **Risk/Reward**:
   - Max loss (premium paid)
   - Max gain (spread width − premium)
   - Breakeven
   - R:R ratio
4. **Catalyst**: What event or trend drives the setup?

---

### Step 7: Generate HTML Report

1. Create the HTML report following the `REPORT_EDITORIAL_STANDARD.md`.
2. Structure:
   - **Header**: Date, "US Options Audit & Setup Structuring"
   - **Section 1: Position Audit** — Table of all positions with action, rationale, and specific recommendations
   - **Section 2: Top 3 Setups** — Detailed structure for each setup with risk/reward
   - **Section 3: Market Context** — Brief note on overall IV environment, GEX levels
3. Write to `googledrive/newsletters/Options_Underwriting_US_<YYYY-MM-DD>.html`.

```bash
# Verify the output file was created
ls -la googledrive/newsletters/Options_Underwriting_US_$(date +%Y-%m-%d).html
```

---

### Step 8: Validate Report

```bash
python3 scripts/validate_report.py --kind options
```

- If `RESULT: PASS` → proceed to Step 9.
- If `RESULT: FAIL` → fix the issues and re-validate. Do NOT dispatch an invalid report.

---

### Step 9: Upload to Google Drive & Dispatch

1. Upload the HTML report to Google Drive (single-latest versioning — replace any existing file with the same name).
2. Send the report via email using `scripts/send_email.py`.

```bash
python3 scripts/send_email.py --report "googledrive/newsletters/Options_Underwriting_US_$(date +%Y-%m-%d).html" --subject "US Options Audit & Setup Structuring - $(date +%Y-%m-%d)"
```

---

### Step 10: Workspace Hygiene & Cache Pruning

1. Delete any transient scripts or temp files created during execution (`rm -f scripts/build_*.py scripts/generate_*.py` and `rm -rf scripts/__pycache__/`).
2. Mandatory Cache Cleanup: Prune any stale prior-session cache files from `scripts/.cache/` (e.g. `find scripts/.cache/ -type f ! -name "aliases.json" -delete` for older session files) to ensure zero cross-session state pollution.
3. Preserve the permanent infrastructure whitelist:
   - `scripts/market_facts.py`
   - `scripts/validate_report.py`
   - `scripts/send_email.py`
   - `scripts/build_dossier_portal.py`
   - `scripts/serve_blogs.py`
   - `scripts/dossier_builder_template.py`
   - `scripts/com.portfolio.blogs.fileserver.plist`
   - `scripts/.cache/aliases.json`
   - `Options_Positions.xlsx`
   - `US_Shortlist.xlsx`
   - `googledrive/` directory structure

> [!NOTE]
> The workflow is complete when the report is dispatched and the workspace is clean.
