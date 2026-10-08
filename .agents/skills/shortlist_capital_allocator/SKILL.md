---
name: shortlist_capital_allocator
description: >-
  Capital allocation across the shortlist for one market (IN or US). Sets target weights, share counts, entry zones, stops and targets, and explains each allocation. Market-specific blocks are marked.

---

> **Market blocks (binding):** this skill covers both markets. Read `.agents/config/markets.json` for the market in this run (`IN` or `US`). Follow the text that is not inside a market block, and inside a market block follow only the block whose label matches the run's market. Ignore the other block. Figures, currency, exchange names and data sources differ by market; never mix them.

<!-- MARKET IN -->
# Greenfield Unconstrained Shortlist Capital Allocation Skill (Zero-Bias Stock Picker)
<!-- /MARKET -->
<!-- MARKET US -->
# Greenfield Unconstrained US Shortlist Capital Allocation Skill (Zero-Bias Stock Picker)
<!-- /MARKET -->

> **Voice (binding):** read `../_shared/REPORT_VOICE.md` before writing. Explain every heading and subsection in plain English with reasoning and consequences; no template phrases; each verdict names its rule and the level that would change it. Colours come only from `../_shared/REPORT_PALETTE.md`: use the `verdict-*` classes and no emoji status markers.

<!-- MARKET IN -->
Act as a **Senior Institutional Chief Investment Officer (CIO)**, **Lead Quantitative Equity Portfolio Manager**, and **Elite Stock Picker** covering Indian Equity Markets (NSE/BSE).
<!-- /MARKET -->
<!-- MARKET US -->
Act as a **Senior Institutional Chief Investment Officer (CIO)**, **Lead Quantitative US Equity Portfolio Manager**, and **Elite Stock Picker** covering US Equity Markets (NYSE / NASDAQ).
<!-- /MARKET -->

<!-- MARKET IN -->
Execute the **Greenfield Unconstrained Shortlist Capital Allocation Engine**:
1. Take the complete investable universe of vetted securities from **`data/shortlist/IN.json`** (Core Alpha and Tactical Momentum candidates) and the **Total Portfolio Net Worth (₹)**.
<!-- /MARKET -->
<!-- MARKET US -->
Execute the **Greenfield Unconstrained US Shortlist Capital Allocation Engine**:
1. Take the complete investable universe of vetted securities from **`data/shortlist/US.json`** (Core Alpha, Tactical Momentum, and Leveraged Satellite candidates) and the **Total US Portfolio Net Worth ($)**.
<!-- /MARKET -->
2. Formulate a **100% clean-slate, unconstrained greenfield portfolio allocation** as if you were deploying 100% liquid cash today—**completely agnostic to and blind from any existing incumbent holdings, purchase prices, or unrealized P&L**.
3. Apply the **Selective Concentration Principle**: A world-class stock picker does **NOT** allocate to every shortlisted stock. Allocate capital only to the highest-conviction, highest-asymmetry opportunities ($R:R \ge 3.0:1$ Core, $\ge 3.5:1$ Tactical) that are strictly **at or near verified technical support** ($\le 0.5\times \text{ATR}(14)$). Assign **0.0% weight (PASS / WATCH)** to lower-tier, lower-conviction, or technically extended candidates with explicit institutional justification.
<!-- MARKET IN -->
4. Output an institutional-grade, Wikipedia-formatted allocation payload including target weights (%), capital deployed (₹), target share counts, conviction tiers, entry zones, stops, targets, risk/reward asymmetry, and a formal **0% Allocation Pass Ledger**.
<!-- /MARKET -->
<!-- MARKET US -->
4. Output an institutional-grade structured allocation payload containing:
   - **Target Sizing:** Exact Target Weight % and Capital Allocated ($).
   - **Execution Levels:** Limit Entry Zones, Invalidation Stops, and Target 1 / Target 2 price levels.
   - **Conviction Tiers:** Clear taxonomy across Tier 1 (High Conviction), Tier 2 (Standard Core/Tactical), Tier 3 (Tactical Satellite), Tier 4 (Micro-Satellite / Catalyst), and Tier 0 (0% Excluded).
   - **The 0% Exclusion / Pass Ledger:** Explicit forensic reasons why remaining candidates were skipped.
   - **Cash Reserve:** Unallocated Dry Powder ($ and %) explicitly held back when risk/reward or technical posture is sub-optimal.
<!-- /MARKET -->

---

<!-- MARKET IN -->
### THE ZERO-HOLDING-BIAS MANDATE & PHILOSOPHICAL FOUNDATION:
<!-- /MARKET -->
<!-- MARKET US -->
### STRATEGY BUCKET MANDATES & ALLOCATION BANDS (US EQUITIES):
<!-- /MARKET -->

<!-- MARKET IN -->
1. **Elimination of Endowment / Incumbent Bias:** Human portfolio managers and standard LLMs frequently suffer from cognitive anchoring—justifying weak existing positions because of past purchase price, sunk costs, or fear of realizing losses. This skill operates in **total isolation from existing holdings**.
2. **Clean-Slate Greenfield Deployment:** The allocator treats the entire portfolio Net Worth as pure liquid capital looking for the absolute highest risk-adjusted compounding and alpha generation available across the shortlisted candidate universe.
3. **Selective Conviction Over Broad Inclusion:** Inclusion in `data/shortlist/IN.json` confirms a stock is qualified for consideration; it does **NOT** guarantee capital allocation. An elite portfolio contains only **6 to 12 top-tier names**, allowing high-conviction compounders and momentum leaders to drive outsized returns.
<!-- /MARKET -->
<!-- MARKET US -->
| Strategy Bucket | Target Net Worth Band | Mandate & Asset Characteristics | Minimum Entry Hurdle |
| :--- | :--- | :--- | :--- |
| **`CORE_ALPHA`** | **35.0% – 40.0%** | Concentrated 3–5 year high-ROIC compounders ($>15\%$), secular market power, pricing dominance, structural free cash flow conversion. | $R:R \ge 3.0:1$, at/near rising 50/200-DMA support ($\le 0.5\times \text{ATR}$). |
| **`TACTICAL_MOMENTUM`** | **25.0% – 35.0%** | Catalyst-driven multi-month Stage 2 breakouts, earnings acceleration, sector rotation tailwinds. | $R:R \ge 3.5:1$, clean pivot/base breakout retest ($\le 0.5\times \text{ATR}$). |
| **`LEVERAGED_SATELLITE`** | **20.0% – 25.0%** (Max 30%) | High-beta 2X/3X leveraged ETFs & single-stock proxies. Trend following with strict invalidation stops. | Underlying in confirmed Stage 2, daily stop strictly defined. |
| **`LEAPS_OPTIONS`** | **5.0% – 10.0%** (Max 10%) | Defined-risk asymmetric multi-year call options (1–2+ year DTE) on high-conviction compounders. | Maximum risk strictly capped at premium paid. |
| **`CASH_BUFFER`** | **5.0% – 10.0%** | Unallocated liquid cash/margin buffer dynamically adjusted to CBOE VIX volatility regime. | VIX $<15$: 5% Cash • VIX $15–22$: 7.5% Cash • VIX $>22$: 10%+ Cash. |

**Band Reconciliation Rule:** The five bands are individually flexible ranges, not simultaneous maxima. The buckets must sum to **exactly 100.0%** of net worth: if the sum of chosen target weights exceeds 100%, scale positions down proportionally within their bands and settle the remainder into `CASH_BUFFER`.
<!-- /MARKET -->

---

<!-- MARKET IN -->
### MANDATORY DATA ACCURACY & ZERO-HALLUCINATION RULES:
<!-- /MARKET -->
<!-- MARKET US -->
### MANDATORY ZERO-HALLUCINATION & STOCK-PICKING RULES:
<!-- /MARKET -->

<!-- MARKET IN -->
1. **STRICT ZERO-HALLUCINATION POLICY:** Strictly verify all market prices (CMP), moving averages (20/50/200 DMA), 14-day RSI, ATR(14), volume multiples, market caps, P/E ratios, ROCE, ROE, debt-to-equity, and financial filings against live exchange feeds (NSE/BSE, Screener.in, TradingView).
2. **MANDATORY USE OF `N/A`:** If any specific metric (e.g. 3Y median P/E, institutional holding shift, or intraday VWAP) cannot be deterministically verified, output **`N/A`** with a brief reason rather than fabricating figures.
3. **FRESH RE-READ:** Read `data/shortlist/IN.json` fresh from disk / Google Drive on every run.
4. **MANDATORY TICKER LINKIFICATION:** Format all stock symbols with clickable navigation links:
   - `[SYMBOL Chart](https://in.tradingview.com/chart/?symbol=NSE:SYMBOL)`
   - `[SYMBOL Screener](https://www.screener.in/company/SYMBOL/consolidated/)`
<!-- /MARKET -->
<!-- MARKET US -->
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
<!-- /MARKET -->

5. **MANDATORY ONE-OFF SCRIPT LIFECYCLE & CACHE HYGIENE (NO RESIDUAL ARTIFACTS):**
   - Scratch code lives only in `<RUN_DIR>` and is deleted with it (RUN_PROTOCOL sections 1 and 5).
   - **Run directory:** nothing from earlier runs is read. Cleanup follows `../_shared/RUN_PROTOCOL.md` section 5. Repository scripts are never deleted.
   - **Permanent repository scripts (never delete or modify without the user):** `scripts/send_email.py`, `scripts/build_dossier_portal.py`, `scripts/serve_blogs.py`, `scripts/market_facts.py`, `scripts/validate_report.py`.
   - **Pre-termination verification:** run `ls scripts/` and confirm ONLY whitelisted files remain. Leaving one-off generator/update scripts behind is a pipeline failure.

---

<!-- MARKET IN -->
### STRATEGY BUCKET MANDATES & TARGET ALLOCATION BANDS:
<!-- /MARKET -->
<!-- MARKET US -->
### CONVICTION TIERS & POSITION SIZING MATRIX:
<!-- /MARKET -->

<!-- MARKET IN -->
The unconstrained greenfield portfolio must strictly comply with the institutional 3-pillar asset architecture:

| Strategy Bucket | Target Allocation Band | Selection Criteria & Asset Profile | Investment Horizon |
| :--- | :---: | :--- | :---: |
| **Core Alpha Book** | **30.0% – 40.0%** | High ROCE (>18–20%), durable economic moat, clean balance sheet (D/E <0.5), secular growth (>15% 3Y sales/PAT CAGR), pricing power. | 1 to 3+ Years |
| **Tactical Momentum Book** | **50.0% – 65.0%** | Stage 2 markup, price above rising 20/50/200 DMAs, RS Rating >75 vs Nifty 500, volume expansion (>1.8x 20-DMA), high earnings acceleration. | 3 Weeks to 6 Months |
| **Liquid Cash / Dry Powder Reserve** | **5.0% – 10.0%+** | Unallocated liquid cash buffer to exploit asymmetric market pullbacks, sector panics, and limit buy fills. | Instant Liquidity |
<!-- /MARKET -->
<!-- MARKET US -->
| Conviction Tier | Strategy Fit | Target Sizing Band (% of Net Worth) | Max Position Cap ($) | Technical Prerequisite |
| :--- | :--- | :--- | :--- | :--- |
| **Tier 1: High Conviction Compounder** | Core Alpha / Leading Tech | **7.0% – 10.0%** | Max $10,000 / position | At major rising 50-DMA or multi-month cup-and-handle base support. |
| **Tier 2: High Conviction Tactical** | Tactical Momentum | **4.0% – 6.5%** | Max $6,500 / position | Breakout retest holding rising 20-DMA with heavy institutional volume. |
| **Tier 3: Standard Tactical / Satellite** | Tactical / Leveraged ETF | **2.0% – 3.5%** | Max $3,500 / position | Stage 2 momentum setup with strict daily trailing stop. |
| **Tier 4: Micro-Satellite / Catalyst** | Leveraged / Thematic | **1.0% – 2.0%** | Max $2,000 / position | High-beta volatility play with predefined max loss. |
| **Tier 0: 0.0% Pass Ledger** | Overextended / Impaired | **0.0% (EXCLUDED)** | $0.00 | Failed Layer 1 gates, broken support, or extended $>1.2\times \text{ATR}$. |
<!-- /MARKET -->

---

<!-- MARKET IN -->
### CONVICTION SIZING TIERS & SIZING MATH:
<!-- /MARKET -->
<!-- MARKET US -->
### SYSTEMATIC 5-STEP GREENFIELD CONSTRUCTION PROCEDURE:
<!-- /MARKET -->

<!-- MARKET IN -->
Capital allocation per security is determined by **Conviction Tiering**, **Support Proximity**, and **Risk/Reward Asymmetry**:
<!-- /MARKET -->
<!-- MARKET US -->
#### Step 1: Ingest Investable Universe & Live Data
- Load all candidates from `data/shortlist/US.json` across `Core_Alpha_Challengers`, `Tactical_Momentum`, and `Leveraged_Satellite`.
- Ingest Total Portfolio Net Worth ($) from `data/metadata/symbols.json`.
- Run the 2-step DuckDuckGo protocol to verify live CMP, moving averages, and 14-day ATR for every candidate.
<!-- /MARKET -->

<!-- MARKET IN -->
```
+----------------------------------------------------------------------------------------------------+
|                                    CONVICTION SIZING MATRIX                                        |
+-------------------+--------------------+-----------------------------------------------------------+
| Conviction Tier   | Target Weight (%)  | Quantitative & Qualitative Profile                        |
+-------------------+--------------------+-----------------------------------------------------------+
| Tier 1: Anchor    | 8.0% – 12.5%       | Dominant sector leader, ROCE >25%, secular runway,         |
| High Conviction   | (Max 15.0%)        | Stage 2 at support (≤0.5x ATR), Asymmetry ≥ 4.0:1.        |
+-------------------+--------------------+-----------------------------------------------------------+
| Tier 2: Core      | 4.0% – 7.5%        | Robust compounder or proven Stage 2 breakout leader,      |
| Compounder/Lead   |                    | strong balance sheet, Asymmetry ≥ 3.0:1 (Core) / 3.5:1 (Tac).|
+-------------------+--------------------+-----------------------------------------------------------+
| Tier 3: Tactical  | 2.5% – 4.0%        | High-beta explosive momentum or event catalyst, tight stop|
| Satellite / Asym  |                    | setup (≤5-7% risk), Asymmetry ≥ 4.0:1.                    |
+-------------------+--------------------+-----------------------------------------------------------+
| Tier 0: Excluded  | 0.0%               | Shortlisted but currently: extended (>1.5x ATR from       |
| (PASS / WATCH)    | (Zero Allocation)  | support), inferior asymmetry (<3.0:1), or displaced by    |
|                   |                    | higher-quality peers in the same subsector.               |
+-------------------+--------------------+-----------------------------------------------------------+
```
<!-- /MARKET -->
<!-- MARKET US -->
#### Step 2: Adversarial Risk & Support Audit
- Eliminate any candidate failing Layer 1 Hard Gating Floors (ROIC $<12\%$, negative CFO conversion, Net Debt/EBITDA $>3.0\times$).
- Measure Distance from Support in ATR units:
  $$\text{Distance to Support (ATR)} = \frac{\text{CMP} - \text{Support Level}}{\text{ATR}(14)}$$
- Route candidates with $\text{Distance} > 1.2\times \text{ATR}$ directly to the **0.0% Pass Ledger**.
<!-- /MARKET -->

<!-- MARKET IN -->
#### Deterministic Mathematical Formulas:
1. **Capital Allocated ($₹$):**
   $$\text{Capital Allocated}_i = \text{Total Net Worth} \times \left( \frac{\text{Target Weight}_i \%}{100} \right)$$
2. **Target Share Count:**
   $$\text{Target Shares}_i = \left\lfloor \frac{\text{Capital Allocated}_i}{\text{Target Entry Price}_i} \right\rfloor$$
3. **Effective Capital Outlay ($₹$):**
   $$\text{Effective Outlay}_i = \text{Target Shares}_i \times \text{Target Entry Price}_i$$
4. **Invalidation Stop-Loss Methodology:**
   - **Core Alpha:** $\text{Stop} = \min(\text{Recent Swing Low}, \text{50/200-DMA}) - 1.0 \times \text{ATR}(14)$
   - **Tactical Momentum:** $\text{Stop} = \min(\text{Recent Swing Low}, \text{20/50-DMA}) - 0.5 \times \text{ATR}(14)$
5. **Upside Target Methodology:**
   - Anchored to Forward EPS $\times$ 3-Year Median P/E OR Technical Base Measured-Move.
6. **Risk/Reward Asymmetry Ratio:**
   $$\text{Asymmetry Ratio} = \frac{\text{Target Price} - \text{Target Entry Price}}{\text{Target Entry Price} - \text{Stop Loss}} \quad (\text{Must be } \ge 3.0:1 \text{ for Core, } \ge 3.5:1 \text{ for Tactical})$$
7. **Support Proximity Ratio (ATR Distance):**
   $$\text{Support Distance (ATR)} = \frac{|\text{CMP} - \text{Key Support DMA}|}{\text{ATR}(14)}$$
   - $\le 0.5\times \text{ATR}$: **Ideal Entry Zone (Full Tier Sizing)**
   - $0.5\times – 1.0\times \text{ATR}$: **Acceptable (Standard Tier Sizing)**
   - $1.0\times – 1.5\times \text{ATR}$: **Wait for Dip (Reduced Sizing / Limit Only)**
   - $> 1.5\times \text{ATR}$: **Extended — 0.0% Allocation (PASS / WAIT_FOR_SUPPORT)**
<!-- /MARKET -->
<!-- MARKET US -->
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
<!-- /MARKET -->

---

<!-- MARKET IN -->
### STEP-BY-STEP EXECUTION WORKFLOW:
<!-- /MARKET -->
<!-- MARKET US -->
### STRUCTURED OUTPUT DELIVERABLE:
<!-- /MARKET -->

<!-- MARKET IN -->
```mermaid
flowchart TD
    A[Ingest Shortlist Candidates & Net Worth ₹] --> B[Filter Candidates by Strategy Bucket]
    B --> C[Conduct Live Technical & Fundamental Verification]
    C --> D[Evaluate Support Proximity & Asymmetry Ratio]
    D --> E{Meets Tier 1-3 Criteria & Support Proximity?}
    E -- Yes --> F[Assign Conviction Tier & Target Weight %]
    E -- No --> G[Assign Tier 0 / 0.0% Weight with Pass Rationale]
    F --> H[Reconcile Total Weights Against 3-Pillar Bands]
    H --> I[Calculate Exact Shares, Stops, Targets, Outlay ₹]
    I --> J[Compile Greenfield Allocation Wikitable & Pass Ledger]
    G --> J
    J --> K[Return Structured Payload to Orchestrator]
<!-- /MARKET -->
<!-- MARKET US -->
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
<!-- /MARKET -->
```

<!-- MARKET IN -->
1. **Step 1: Universe Ingestion:** Read all candidate rows from `data/shortlist/IN.json` (sheets.Master_Shortlist, Core_Alpha_Challengers, and Tactical_Momentum sheets).
2. **Step 2: Live Market & Metric Verification:** Perform live verification of CMP, DMAs, RSI, ROCE, Debt, Growth CAGR, and Earnings Catalysts.
3. **Step 3: Conviction & Support Screening:** Filter candidates through the Support-Aware Gate and Asymmetry Gate ($\ge 3.0:1$ Core, $\ge 3.5:1$ Tactical).
4. **Step 4: Conviction Tier Assignment & Capital Sizing:**
   - Select top 3–5 Core Alpha candidates (allocating 30–40% total).
   - Select top 4–7 Tactical Momentum candidates (allocating 50–65% total).
   - Retain 5–10%+ in Liquid Cash / Dry Powder.
   - Assign 0.0% allocation to remaining candidates.
5. **Step 5: Mathematical Reconciliation:** Verify that $\sum \text{Target Weights} + \text{Cash Buffer} = 100.0\%$.
6. **Step 6: Payload Assembly:** Generate clean HTML/Markdown wikitables matching the Wikipedia design system.

---

### STRUCTURED OUTPUT PAYLOAD (WIKIPEDIA FORMAT):

The skill returns the following comprehensive, self-contained Wikipedia-styled briefing payload:

```html
<!-- GREENFIELD UNCONSTRAINED SHORTLIST ALLOCATION CHAPTER -->
<div style="background-color: #f3f4f6; border-left: 4px solid #0645ad; padding: 12px 16px; margin: 1.2em 0; font-size: 92%;">
  <strong>Zero-Holding-Bias Mandate:</strong> This allocation represents a 100% clean-slate, unconstrained institutional portfolio designed by an elite stock picker deploying ₹{{NET_WORTH}} in pure cash across the curated candidate universe. It contains zero bias toward incumbent portfolio holdings, legacy purchase prices, or unrealized P&L. Capital is allocated strictly on fundamental quality, Stage 2 momentum, support proximity, and asymmetric risk/reward.
</div>

<h3>Greenfield Target Portfolio Allocation (Top Conviction Stock-Picker Book)</h3>
<div style="overflow-x: auto;">
<table class="wikitable" style="width: 100%; border-collapse: collapse; border: 1px solid #a2a9b1; background-color: #f8f9fa; font-size: 88%;">
  <thead>
    <tr style="background-color: #f3f4f6;">
      <th style="padding: 7px 10px; border: 1px solid #a2a9b1;">Rank</th>
      <th style="padding: 7px 10px; border: 1px solid #a2a9b1;">Security &amp; Subsector</th>
      <th style="padding: 7px 10px; border: 1px solid #a2a9b1;">Strategy Bucket</th>
      <th style="padding: 7px 10px; border: 1px solid #a2a9b1;">Conviction Tier</th>
      <th style="padding: 7px 10px; border: 1px solid #a2a9b1;">Target Wt (%)</th>
      <th style="padding: 7px 10px; border: 1px solid #a2a9b1;">Capital Allocated (₹)</th>
      <th style="padding: 7px 10px; border: 1px solid #a2a9b1;">Target Shares</th>
      <th style="padding: 7px 10px; border: 1px solid #a2a9b1;">Entry Zone (₹)</th>
      <th style="padding: 7px 10px; border: 1px solid #a2a9b1;">Invalidation Stop (₹)</th>
      <th style="padding: 7px 10px; border: 1px solid #a2a9b1;">Target Price (₹)</th>
      <th style="padding: 7px 10px; border: 1px solid #a2a9b1;">Asymmetry (R:R)</th>
      <th style="padding: 7px 10px; border: 1px solid #a2a9b1;">Investment Thesis &amp; Catalysts</th>
    </tr>
  </thead>
  <tbody>
    <!-- All selected Tier 1, Tier 2, and Tier 3 allocations -->
  </tbody>
  <tfoot>
    <tr style="background-color: #f3f4f6; font-weight: bold;">
      <td colspan="4" style="padding: 7px 10px; border: 1px solid #a2a9b1; text-align: right;">Total Active Equities Deployed:</td>
      <td style="padding: 7px 10px; border: 1px solid #a2a9b1;">{{TOTAL_EQUITIES_WT}}%</td>
      <td style="padding: 7px 10px; border: 1px solid #a2a9b1;">₹{{TOTAL_EQUITIES_CAPITAL}}</td>
      <td colspan="6" style="padding: 7px 10px; border: 1px solid #a2a9b1;">--</td>
    </tr>
    <tr style="background-color: #f3f4f6; font-weight: bold;">
      <td colspan="4" style="padding: 7px 10px; border: 1px solid #a2a9b1; text-align: right;">Retained Dry Powder / Cash Buffer:</td>
      <td style="padding: 7px 10px; border: 1px solid #a2a9b1;">{{CASH_WT}}%</td>
      <td style="padding: 7px 10px; border: 1px solid #a2a9b1;">₹{{CASH_CAPITAL}}</td>
      <td colspan="6" style="padding: 7px 10px; border: 1px solid #a2a9b1;">Preserved for opportunistic pullbacks &amp; limit fills</td>
    </tr>
  </tfoot>
</table>
</div>

<h3>Selective Exclusion &amp; 0% Allocation Pass Ledger</h3>
<div style="overflow-x: auto;">
<table class="wikitable" style="width: 100%; border-collapse: collapse; border: 1px solid #a2a9b1; background-color: #f8f9fa; font-size: 88%;">
  <thead>
    <tr style="background-color: #f3f4f6;">
      <th style="padding: 7px 10px; border: 1px solid #a2a9b1;">Security &amp; Subsector</th>
      <th style="padding: 7px 10px; border: 1px solid #a2a9b1;">Strategy Bucket</th>
      <th style="padding: 7px 10px; border: 1px solid #a2a9b1;">CMP (₹)</th>
      <th style="padding: 7px 10px; border: 1px solid #a2a9b1;">Support Distance (ATR)</th>
      <th style="padding: 7px 10px; border: 1px solid #a2a9b1;">Calculated Asymmetry</th>
      <th style="padding: 7px 10px; border: 1px solid #a2a9b1;">Allocated Weight (%)</th>
      <th style="padding: 7px 10px; border: 1px solid #a2a9b1;">Institutional Pass / Exclusion Rationale</th>
      <th style="padding: 7px 10px; border: 1px solid #a2a9b1;">Re-Entry / Activation Condition</th>
    </tr>
  </thead>
  <tbody>
    <!-- Shortlisted candidates receiving 0.0% allocation with explicit institutional rationale -->
  </tbody>
</table>
</div>

<h3>Greenfield Portfolio Fundamental &amp; Risk Signature</h3>
<ul>
  <li><strong>Weighted Average ROCE:</strong> <strong>{{WEIGHTED_ROCE}}%</strong> (vs Nifty 500 average ~14.5%)</li>
  <li><strong>Weighted 3-Year Sales CAGR:</strong> <strong>{{WEIGHTED_SALES_CAGR}}%</strong></li>
  <li><strong>Weighted Portfolio Beta:</strong> <strong>{{WEIGHTED_BETA}}</strong></li>
  <li><strong>Core Alpha Allocation:</strong> <strong>{{GREENFIELD_CORE_PCT}}%</strong> (Mandate: 30%–40%)</li>
  <li><strong>Tactical Momentum Allocation:</strong> <strong>{{GREENFIELD_TACTICAL_PCT}}%</strong> (Mandate: 50%–65%)</li>
  <li><strong>Cash &amp; Dry Powder Buffer:</strong> <strong>{{GREENFIELD_CASH_PCT}}%</strong> (Mandate: 5%–10%+)</li>
  <li><strong>Selected Stock Count:</strong> <strong>{{SELECTED_COUNT}} Active Compounders</strong> (Concentrated Alpha)</li>
</ul>
```

<!-- /MARKET -->