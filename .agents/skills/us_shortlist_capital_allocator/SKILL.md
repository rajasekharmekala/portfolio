---
name: us_shortlist_capital_allocator
description: >-
  Unconstrained greenfield capital allocation and institutional stock-picker engine for US equity markets (NYSE/NASDAQ).
  Operates with zero incumbent holding bias on the curated candidate universe from shortlist/US_Shortlist.xlsx
  (Core Alpha, Tactical Momentum, and Leveraged Satellite books). Evaluates 360-degree fundamentals, moats, Stage 2
  technical support proximity, and risk/reward asymmetry to build an optimal, conviction-tiered target portfolio
  (Target Wt %, Capital Allocated $, Conviction Tiers, Entry Zones, Stop-Loss Levels, 0% Exclusions, and Dry Powder Cash Reserve).
  Returns a structured institutional allocation payload.
---

# Greenfield Unconstrained US Shortlist Capital Allocation Skill (Zero-Bias Stock Picker)

> **Voice (binding):** read `../_shared/REPORT_VOICE.md` before writing. Explain every heading and subsection in plain English with reasoning and consequences; no template phrases; each verdict names its rule and the level that would change it. Colours come only from `../_shared/REPORT_PALETTE.md`: use the `verdict-*` classes and no emoji status markers.

Act as a **Senior Institutional Chief Investment Officer (CIO)**, **Lead Quantitative US Equity Portfolio Manager**, and **Elite Stock Picker** covering US Equity Markets (NYSE / NASDAQ).

Execute the **Greenfield Unconstrained US Shortlist Capital Allocation Engine**:
1. Take the complete investable universe of vetted securities from **`shortlist/US_Shortlist.xlsx`** (Core Alpha, Tactical Momentum, and Leveraged Satellite candidates) and the **Total US Portfolio Net Worth ($)**.
2. Formulate a **100% clean-slate, unconstrained greenfield portfolio allocation** as if you were deploying 100% liquid cash today—**completely agnostic to and blind from any existing incumbent holdings, purchase prices, or unrealized P&L**.
3. Apply the **Selective Concentration Principle**: A world-class stock picker does **NOT** allocate to every shortlisted stock. Allocate capital only to the highest-conviction, highest-asymmetry opportunities ($R:R \ge 3.0:1$ Core, $\ge 3.5:1$ Tactical) that are strictly **at or near verified technical support** ($\le 0.5\times \text{ATR}(14)$). Assign **0.0% weight (PASS / WATCH)** to lower-tier, lower-conviction, or technically extended candidates with explicit institutional justification.
4. Output an institutional-grade structured allocation payload containing:
   - **Target Sizing:** Exact Target Weight % and Capital Allocated ($).
   - **Execution Levels:** Limit Entry Zones, Invalidation Stops, and Target 1 / Target 2 price levels.
   - **Conviction Tiers:** Clear taxonomy across Tier 1 (High Conviction), Tier 2 (Standard Core/Tactical), Tier 3 (Tactical Satellite), Tier 4 (Micro-Satellite / Catalyst), and Tier 0 (0% Excluded).
   - **The 0% Exclusion / Pass Ledger:** Explicit forensic reasons why remaining candidates were skipped.
   - **Cash Reserve:** Unallocated Dry Powder ($ and %) explicitly held back when risk/reward or technical posture is sub-optimal.

---

### STRATEGY BUCKET MANDATES & ALLOCATION BANDS (US EQUITIES):

| Strategy Bucket | Target Net Worth Band | Mandate & Asset Characteristics | Minimum Entry Hurdle |
| :--- | :--- | :--- | :--- |
| **`CORE_ALPHA`** | **35.0% – 40.0%** | Concentrated 3–5 year high-ROIC compounders ($>15\%$), secular market power, pricing dominance, structural free cash flow conversion. | $R:R \ge 3.0:1$, at/near rising 50/200-DMA support ($\le 0.5\times \text{ATR}$). |
| **`TACTICAL_MOMENTUM`** | **25.0% – 35.0%** | Catalyst-driven multi-month Stage 2 breakouts, earnings acceleration, sector rotation tailwinds. | $R:R \ge 3.5:1$, clean pivot/base breakout retest ($\le 0.5\times \text{ATR}$). |
| **`LEVERAGED_SATELLITE`** | **20.0% – 25.0%** (Max 30%) | High-beta 2X/3X leveraged ETFs & single-stock proxies. Trend following with strict invalidation stops. | Underlying in confirmed Stage 2, daily stop strictly defined. |
| **`LEAPS_OPTIONS`** | **5.0% – 10.0%** (Max 10%) | Defined-risk asymmetric multi-year call options (1–2+ year DTE) on high-conviction compounders. | Maximum risk strictly capped at premium paid. |
| **`CASH_BUFFER`** | **5.0% – 10.0%** | Unallocated liquid cash/margin buffer dynamically adjusted to CBOE VIX volatility regime. | VIX $<15$: 5% Cash • VIX $15–22$: 7.5% Cash • VIX $>22$: 10%+ Cash. |

**Band Reconciliation Rule:** The five bands are individually flexible ranges, not simultaneous maxima. The buckets must sum to **exactly 100.0%** of net worth: if the sum of chosen target weights exceeds 100%, scale positions down proportionally within their bands and settle the remainder into `CASH_BUFFER`.

---

### MANDATORY ZERO-HALLUCINATION & STOCK-PICKING RULES:

1. **NO ENDOWMENT BIAS:** Zero preference for incumbent holdings. If an unheld shortlist candidate offers superior growth, cleaner support proximity, or higher asymmetry than a current holding, the candidate takes full target allocation without hesitation.
2. **SUPPORT-AWARE ENTRY DISCIPLINE IS MANDATORY:**
   - **Strict Distance-from-Support Gating:**
     - $\le 0.5\times \text{ATR}(14)$ from support: **ELIGIBLE FOR IMMEDIATE ALLOCATION**.
     - $0.5\times$ to $1.2\times \text{ATR}(14)$: **TIER-REDUCED / TRANCHED ALLOCATION** (Limit order only).
     - $> 1.2\times \text{ATR}(14)$ (Extended): **0.0% ALLOCATION (PASS / WAIT FOR PULLBACK)**.
3. **MANDATORY TWO-STEP SEARCH & DEEP FETCH PROTOCOL (ZERO-SNIPPET RELIANCE):**
   - **Never Stop at Search Snippets:** Subagents MUST NEVER rely solely on high-level search snippets. High-level snippets omit options OI, full cash flow numbers, and rolling moving averages.
   - **Mandatory Deep Fetch Execution:**
     1. Search using `duck-duck-go-search` to locate canonical Finviz, TradingView, Yahoo Finance, StockAnalysis, MacroTrends, or SEC EDGAR filing URLs (e.g. `https://finviz.com/quote.ashx?t=<SYMBOL>` or `https://stockanalysis.com/stocks/<SYMBOL>/financials/`).
     2. Call `duck-duck-go-fetch_content` (with `parse_mode='markdown'` or `text`, paginating if necessary) on the target financial/technicals URL to ingest the complete tabular P&L, Balance Sheet, Free Cash Flow, and Key Financial Ratios.
     3. Extract and verify live CMP, 50-DMA, 200-DMA, 14-day ATR, 14-day RSI, ROIC, and 3Y CFO/NI ratio.
4. **MATHEMATICAL INTEGRITY:**
   $$\sum \text{Target Capital Allocated} + \text{Dry Powder Cash Reserve} = \text{Total US Portfolio Net Worth} \quad (\pm \$0.00)$$

5. **MANDATORY ONE-OFF SCRIPT LIFECYCLE & CACHE HYGIENE (NO RESIDUAL ARTIFACTS):**
   - Scratch code lives only in `<RUN_DIR>` and is deleted with it (RUN_PROTOCOL sections 1 and 5).
   - **Run directory:** nothing from earlier runs is read. Cleanup follows `../_shared/RUN_PROTOCOL.md` section 5. Repository scripts are never deleted.
   - **Permanent repository scripts (never delete or modify without the user):** `scripts/send_email.py`, `scripts/build_dossier_portal.py`, `scripts/serve_blogs.py`, `scripts/market_facts.py`, `scripts/validate_report.py`.
   - **Pre-termination verification:** run `ls scripts/` and confirm ONLY whitelisted files remain. Leaving one-off generator/update scripts behind is a pipeline failure.

---

### CONVICTION TIERS & POSITION SIZING MATRIX:

| Conviction Tier | Strategy Fit | Target Sizing Band (% of Net Worth) | Max Position Cap ($) | Technical Prerequisite |
| :--- | :--- | :--- | :--- | :--- |
| **Tier 1: High Conviction Compounder** | Core Alpha / Leading Tech | **7.0% – 10.0%** | Max $10,000 / position | At major rising 50-DMA or multi-month cup-and-handle base support. |
| **Tier 2: High Conviction Tactical** | Tactical Momentum | **4.0% – 6.5%** | Max $6,500 / position | Breakout retest holding rising 20-DMA with heavy institutional volume. |
| **Tier 3: Standard Tactical / Satellite** | Tactical / Leveraged ETF | **2.0% – 3.5%** | Max $3,500 / position | Stage 2 momentum setup with strict daily trailing stop. |
| **Tier 4: Micro-Satellite / Catalyst** | Leveraged / Thematic | **1.0% – 2.0%** | Max $2,000 / position | High-beta volatility play with predefined max loss. |
| **Tier 0: 0.0% Pass Ledger** | Overextended / Impaired | **0.0% (EXCLUDED)** | $0.00 | Failed Layer 1 gates, broken support, or extended $>1.2\times \text{ATR}$. |

---

### SYSTEMATIC 5-STEP GREENFIELD CONSTRUCTION PROCEDURE:

#### Step 1: Ingest Investable Universe & Live Data
- Load all candidates from `shortlist/US_Shortlist.xlsx` across `Core_Alpha_Challengers`, `Tactical_Momentum`, and `Leveraged_Satellite`.
- Ingest Total Portfolio Net Worth ($) from `sheets/US_Portfolio_Holdings.xlsx`.
- Run the 2-step DuckDuckGo protocol to verify live CMP, moving averages, and 14-day ATR for every candidate.

#### Step 2: Adversarial Risk & Support Audit
- Eliminate any candidate failing Layer 1 Hard Gating Floors (ROIC $<12\%$, negative CFO conversion, Net Debt/EBITDA $>3.0\times$).
- Measure Distance from Support in ATR units:
  $$\text{Distance to Support (ATR)} = \frac{\text{CMP} - \text{Support Level}}{\text{ATR}(14)}$$
- Route candidates with $\text{Distance} > 1.2\times \text{ATR}$ directly to the **0.0% Pass Ledger**.

#### Step 3: Conviction Ranking & Asymmetry Sizing
- Score remaining candidates by Moat Durability, ROIC, Earnings Acceleration, and Asymmetry Ratio ($R:R$).
- Map each qualified security into Tier 1, Tier 2, Tier 3, or Tier 4.

#### Step 4: Dollar Capital Allocation & Bucket Balance
- Calculate exact dollar allocation for each selected winner:
  $$\text{Capital Allocated (\$) } = \text{Target Weight \%} \times \text{Total Net Worth (\$) }$$
- Verify that cumulative bucket totals conform to the Strategy Allocation Mandates.
- Settle unallocated capital into the **Dry Powder Cash Reserve ($ and %)**.

#### Step 5: Generate Actionable Limit Buy & Stop-Loss Matrix
- For every non-zero allocation, define:
  - **Limit Entry Zone ($):** Low to High buy range.
  - **Structural Stop Loss ($):** Strictly below underlying support.
  - **Target 1 & Target 2 ($):** Base 12-month target and blue-sky expansion target.
  - **Asymmetry Ratio ($R:R$):** $(\text{Target 1} - \text{CMP}) / (\text{CMP} - \text{Stop Loss})$.

---

### STRUCTURED OUTPUT DELIVERABLE:

The engine outputs a comprehensive structured payload containing the Greenfield Target Portfolio Wikitable, the 0% Pass Ledger, and the Target Bucket Summary:

```markdown
### Chapter 3: Greenfield Unconstrained US Target Portfolio (<YYYY-MM-DD>)

#### 3.1 Unconstrained Target Portfolio Allocation
| # | Ticker | Company Name | Strategy Book | Conviction Tier | Target Wt % | Capital Allocated ($) | CMP ($) | Entry Zone ($) | Invalidation Stop ($) | Target Base ($) | Asymmetry Ratio | Technical Anchor / Thesis |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `TICKER` | Company Name | `CORE_ALPHA` | Tier 1 | 8.00% | $7,242 | $XX.XX | $XX–$XX | $XX.XX | $XX.XX | 3.8:1 | 50-DMA Base Retest; AI datacenter power monopoly |

#### 3.2 The 0.0% Exclusion & Pass Ledger
| # | Ticker | Company Name | Strategy Book | Live CMP ($) | Distance from Support | Primary Reason for 0.0% Allocation | Re-Entry Condition |
|---|---|---|---|---|---|---|---|
| 1 | `TICKER` | Company Name | `TACTICAL_MOMENTUM` | $XX.XX | 2.1x ATR (Extended) | Extended beyond 20-DMA; risk/reward unfavorable (1.8:1). | Wait for consolidation to 50-DMA ($XX.XX). |

#### 3.3 Target Portfolio Macro Stance & Bucket Reconciliation
| Strategy Bucket | Greenfield Target MV ($) | Greenfield Target % | Target Mandate Range | Variance vs Target | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Core Alpha Compounders** | $XX,XXX | XX.X% | 35% – 40% | +X.X% | OPTIMAL |
| **Tactical Momentum Setups** | $XX,XXX | XX.X% | 25% – 35% | -X.X% | OPTIMAL |
| **Leveraged Satellite Book** | $XX,XXX | XX.X% | 20% – 25% | +X.X% | OPTIMAL |
| **LEAPS Option Overlay** | $X,XXX | X.X% | 5% – 10% | +X.X% | OPTIMAL |
| **Dry Powder Cash Reserve** | $X,XXX | X.X% | 5% – 10% | 0.0% | SUFFICIENT |
| **Total Portfolio Net Worth** | **$XX,XXX** | **100.0%** | **100.0%** | **$0.00** | **BALANCED** |
```
