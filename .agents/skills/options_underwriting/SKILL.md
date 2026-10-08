---
name: options_underwriting
description: >-
  Options position audit and setup structuring for one market (IN = NSE F&O, US = listed US options). Audits every open position against the 4-action matrix, screens setups, and writes a beginner-friendly report. Market-specific blocks are marked.

---

> **Market blocks (binding):** this skill covers both markets. Read `.agents/config/markets.json` for the market in this run (`IN` or `US`). Follow the text that is not inside a market block, and inside a market block follow only the block whose label matches the run's market. Ignore the other block. Figures, currency, exchange names and data sources differ by market; never mix them.

<!-- MARKET IN -->
# Quantitative Institutional Options Underwriting & Lifecycle Engine (NSE F&O)
<!-- /MARKET -->
<!-- MARKET US -->
# Quantitative Institutional US Options Underwriting & Lifecycle Engine (CBOE / NYSE / NASDAQ)
<!-- /MARKET -->

> **Voice (binding):** read `../_shared/REPORT_VOICE.md` before writing. Explain every heading and subsection in plain English with reasoning and consequences; no template phrases; each verdict names its rule and the level that would change it. Colours come only from `../_shared/REPORT_PALETTE.md`: use the `verdict-*` classes and no emoji status markers.

<!-- MARKET IN -->
Act as a **Senior Institutional Equity Derivatives Strategist**, **Quantitative Volatility Portfolio Manager**, and **Lead F&O Underwriter** covering Indian Equity Markets (NSE).
<!-- /MARKET -->
<!-- MARKET US -->
Act as a **Senior Institutional Equity Derivatives Strategist**, **Lead US Volatility Portfolio Manager**, and **Chief Options Underwriter** covering US Equity Markets (NYSE / NASDAQ / CBOE).
<!-- /MARKET -->

<!-- MARKET IN -->
Execute the **Quantitative Institutional Options Underwriting & Lifecycle Engine**:
1. Ingest qualified candidates from **`data/shortlist/IN.json`** and **`data/watchlist/IN.json`** that possess active listings in the **NSE Equity Derivatives (F&O) Segment**.
2. Execute the **4-Layer Lead Generation & Quantitative Underwriting Radar** across:
   - **Layer 1: Underlying Technical & Support Gate** (Weinstein Stage 2, distance $\le 0.5\times \text{ATR}(14)$ to verified base/support).
   - **Layer 2: Volatility Surface Squeeze** ($IV_{30} \le RV_{30} \times 1.10$, IV Percentile $< 40\%$, pre-catalyst expansion runway).
   - **Layer 3: NSE F&O Institutional Footprint** (Price $\uparrow$ + Cumulative Futures OI $\uparrow \ge 5\% = \text{Long Build-up}$, Strike Call OI unwinding, Put OI clustering at support, Strike PCR $\ge 1.20$).
   - **Layer 4: Contract Structuring & Greek Sizing** (Delta $0.48\text{–}0.58$ ATM Long Call, Delta $0.22\text{–}0.30$ OTM Short Call for Bull Call Vertical Spreads; Theta burn $< 1.5\%$/day).
3. Conduct the **Active Options Position Health Audit** on all active Indian options from **`Portfolio Research System/05_Options_Book.md`** and **`data/options/<MKT>.json`**, mapping each contract to one of four discrete institutional actions:
   - **`HOLD`** (Healthy trend, Delta $0.40\text{–}0.70$, DTE $>25$, P&L within bounds).
   - **`ROLL_UP_OUT`** (Harvest gamma when Delta $>0.75$ or P&L $\ge +80\%$; roll to Delta $0.50$ next month).
<!-- /MARKET -->
<!-- MARKET US -->
Execute the **Quantitative Institutional US Options Underwriting & Lifecycle Engine**:
1. Ingest qualified candidates from **`data/shortlist/US.json`** and **`data/watchlist/US.json`** that possess active, highly liquid equity options on CBOE/OPRA.
2. Execute the **4-Layer Lead Generation & Quantitative Underwriting Radar**:
   - **Layer 1: Underlying Setup & Support Gate** (Weinstein Stage 2 structure, distance $\le 0.5\times \text{ATR}(14)$ to verified base/support).
   - **Layer 2: Volatility Surface Squeeze Gate** ($IV_{30} \le RV_{30} \times 1.10$, IV Percentile $< 40\%$, pre-catalyst expansion runway).
   - **Layer 3: CBOE Institutional Flow & Net Gamma Exposure (GEX)** (Positive Gamma regime $>\text{Vol Trigger}$, Call Wall migration, Unusual Options Activity / Dark Pool accumulation).
   - **Layer 4: Contract Structuring & Greek Sizing** (Tactical: Bull Call Spreads Delta $0.50/0.25$, 30–75 DTE; LEAPS: Deep ITM Delta $0.65\text{–}0.75$, 180–720 DTE).
3. Conduct the **Active Options Position Health Audit** across all active US options positions in **`Portfolio Research System/05_Options_Book.md`** and **`data/options/<MKT>.json`** (including Robinhood & Charles Schwab LEAPS holdings), mapping each contract to one of four discrete institutional actions:
   - **`HOLD`** (Healthy trend, Delta $0.40\text{–}0.70$, DTE $>60$ on LEAPS / $>25$ on tactical, P&L within bounds).
   - **`ROLL_UP_OUT`** (Harvest gamma when Delta $>0.80$ or P&L $\ge +80\%$; roll to Delta $0.50$ in subsequent cycle).
<!-- /MARKET -->
   - **`CONVERT_SPREAD`** (Freeze delta and stop theta decay at Resistance 1 by selling OTM call).
<!-- MARKET IN -->
   - **`KILL`** (Option loss $\le -40\%$, or underlying breaks 50-DMA, or DTE $<20$ without breakout).
4. Persist an exhaustive, Wikipedia-styled HTML report to **`docs/reports/Options_Underwriting_NSE_<YYYY-MM-DD>.html`**, update **`Portfolio Research System/05_Options_Book.md`**, and synchronize **`data/options/<MKT>.json`** in-place.
<!-- /MARKET -->
<!-- MARKET US -->
   - **`KILL`** (Option loss $\le -40\%$, or underlying breaks 50-DMA, or far OTM delta decay trap $\Delta < 0.25$).
4. Persist an exhaustive, Wikipedia-styled HTML report to **`docs/reports/Options_Underwriting_US_<YYYY-MM-DD>.html`**, update **`Portfolio Research System/05_Options_Book.md`**, and synchronize **`data/options/<MKT>.json`** in-place.
<!-- /MARKET -->

---

<!-- MARKET IN -->
### MANDATORY ZERO-HALLUCINATION & DERIVATIVES DATA RULES:
<!-- /MARKET -->
<!-- MARKET US -->
### MANDATORY ZERO-HALLUCINATION & US DERIVATIVES DATA RULES:
<!-- /MARKET -->

<!-- MARKET IN -->
1. **NO DERIVATIVES HALLUCINATIONS:** Strictly verify all Strike Prices, Lot Sizes, Implied Volatilities (IV), Historical Realized Volatilities (30-day RV), Cumulative Futures Open Interest (OI), Strike-level Call/Put OI, and Option Premiums (LTP/VWAP) against live verified market data (NSE Bhavcopy, NSE Option Chain, TradingView, Sensibull, Trendlyne).
<!-- /MARKET -->
<!-- MARKET US -->
1. **NO DERIVATIVES HALLUCINATIONS:** Strictly verify all Strike Prices, CBOE Implied Volatility (IV), 30-day Realized Volatility (RV), Open Interest, Daily Option Volume, Bid-Ask Spreads, Delta, Gamma, Theta, and Vega against live verified market data (CBOE, OptionStrat, Barchart, Market Chameleon, TradingView, Yahoo Finance).
<!-- /MARKET -->
2. **MANDATORY TWO-STEP SEARCH & DEEP FETCH PROTOCOL:**
<!-- MARKET IN -->
   - **Never Stop at Search Snippets:** Subagents MUST NEVER rely solely on high-level search snippets. High-level snippets omit detailed strike OI, bid-ask spreads, and rolling Greeks.
<!-- /MARKET -->
<!-- MARKET US -->
   - **Never Stop at Search Snippets:** Subagents MUST NEVER rely solely on high-level search snippets. High-level snippets omit option chain bid-ask spreads, strike-level OI, and historical IV percentile ranks.
<!-- /MARKET -->
   - **Mandatory Deep Fetch Execution:**
<!-- MARKET IN -->
     1. Search using `duck-duck-go-search` to locate the NSE Option Chain URL (`https://www.nseindia.com/option-chain`), Sensibull/Trendlyne F&O analysis page, or TradingView chart for the underlying symbol.
     2. Call `duck-duck-go-fetch_content` to extract the full strike-level open interest, change in OI, futures premium/discount, and IV levels.
<!-- /MARKET -->
<!-- MARKET US -->
     1. Search using `duck-duck-go-search` to locate Barchart options overview (`https://www.barchart.com/stocks/quotes/<SYMBOL>/options`), OptionStrat, or TradingView chart.
     2. Call `duck-duck-go-fetch_content` to extract the full strike-level open interest, IV Rank/Percentile, volume, and Greeks.
<!-- /MARKET -->
     3. Extract and verify:
<!-- MARKET IN -->
        - **ATM Strike IV & 52-Week IV Percentile:** Ensure IV is not inflated due to immediate binary events.
        - **Cumulative Futures OI Change %:** Classify precisely into Long Build-up, Short Covering, Short Build-up, or Long Unwinding.
        - **Max Pain & Strike OI Walls:** Identify the Call Wall (Major Resistance) and Put Wall (Major Floor).
3. **MANDATORY USE OF `N/A`:** If any specific Greek (e.g. precise Vega or Gamma at an illiquid strike) cannot be deterministically verified, output **`N/A`** with a brief reason rather than fabricating numbers.
4. **NSE SINGLE-STOCK DTE CONSTRAINTS:**
   - Single-stock options on NSE are liquid **ONLY in the Current Monthly Expiry cycle (20–35 DTE)**.
   - Never recommend far-month single-stock naked options (45–75+ DTE) without warning of 5–15% bid-ask slippage. For single stocks, use the current month expiry; for multi-month horizon, use **Bull Call Spreads** or roll monthly.
5. **MANDATORY TICKER LINKIFICATION:** Format all stock symbols with clickable navigation links:
   - `[SYMBOL Chart](https://in.tradingview.com/chart/?symbol=NSE:SYMBOL)`
   - `[SYMBOL Screener](https://www.screener.in/company/SYMBOL/consolidated/)`
<!-- /MARKET -->
<!-- MARKET US -->
        - **IV Percentile / IV Rank (52-Week):** Verify whether current IV is cheap ($<40\%$) or inflated ($>70\%$).
        - **Net Gamma Exposure (GEX):** Determine if market makers are long gamma (damping volatility) or short gamma (amplifying moves).
        - **Catalyst Date (Earnings / FDA / Product Launch):** Ensure trade runway does not blindly hold through an earnings IV crush.
3. **MANDATORY USE OF `N/A`:** If any specific Greek cannot be deterministically verified, output **`N/A`** with a brief reason rather than fabricating numbers.
4. **MANDATORY TICKER LINKIFICATION:** Format all stock symbols with clickable navigation links:
   - `[SYMBOL Chart](https://www.tradingview.com/chart/?symbol=SYMBOL)`
   - `[SYMBOL Finviz](https://finviz.com/quote.ashx?t=SYMBOL)`
<!-- /MARKET -->

<!-- MARKET IN -->
6. **MANDATORY ONE-OFF SCRIPT LIFECYCLE & CACHE HYGIENE (NO RESIDUAL ARTIFACTS):**
<!-- /MARKET -->
<!-- MARKET US -->
5. **MANDATORY ONE-OFF SCRIPT LIFECYCLE & CACHE HYGIENE (NO RESIDUAL ARTIFACTS):**
<!-- /MARKET -->
   - Scratch code lives only in `<RUN_DIR>` and is deleted with it (RUN_PROTOCOL sections 1 and 5).
   - **Run directory:** nothing from earlier runs is read. Cleanup follows `../_shared/RUN_PROTOCOL.md` section 5. Repository scripts are never deleted.
   - **Permanent repository scripts (never delete or modify without the user):** `scripts/send_email.py`, `scripts/build_dossier_portal.py`, `scripts/serve_blogs.py`, `scripts/market_facts.py`, `scripts/validate_report.py`.
   - **Pre-termination verification:** run `ls scripts/` and confirm ONLY whitelisted files remain. Leaving one-off generator/update scripts behind is a pipeline failure.

---

<!-- MARKET IN -->
### THE 4-LAYER QUANTITATIVE OPTIONS UNDERWRITING RADAR:
<!-- /MARKET -->
<!-- MARKET US -->
### THE 4-LAYER QUANTITATIVE US OPTIONS UNDERWRITING RADAR:
<!-- /MARKET -->

```
 ┌────────────────────────────────────────────────────────────────────────────────────────┐
 │ Layer 1: Underlying Setup (Weinstein Stage 2 + Support Proximity <= 0.5x ATR(14))      │
 ├────────────────────────────────────────────────────────────────────────────────────────┤
 │ Layer 2: Volatility Surface Squeeze (IV <= RV30 x 1.10, IV Percentile < 40%)          │
 ├────────────────────────────────────────────────────────────────────────────────────────┤
<!-- MARKET IN -->
 │ Layer 3: NSE F&O Institutional Footprint (Price ↑ + Futures OI ↑ >= 5%, Strike PCR >= 1.2) │
<!-- /MARKET -->
<!-- MARKET US -->
 │ Layer 3: CBOE Institutional Flow & GEX (Positive Gamma, Call Wall Migration, UOA Flow) │
<!-- /MARKET -->
 ├────────────────────────────────────────────────────────────────────────────────────────┤
<!-- MARKET IN -->
 │ Layer 4: Contract Structuring (Bull Call Vertical Spread Delta 0.50/0.25, Theta < 1.5%)│
<!-- /MARKET -->
<!-- MARKET US -->
 │ Layer 4: Contract Structuring (Tactical Spreads 30–75 DTE vs Compounder LEAPS 1–2Y)   │
<!-- /MARKET -->
 └────────────────────────────────────────────────────────────────────────────────────────┘
```

#### Layer 1: Underlying Setup & Support Gate
<!-- MARKET IN -->
- **Weinstein Stage 2 Structure:** Price $> 20\text{-DMA} > 50\text{-DMA} > 200\text{-DMA}$ with expanding volume.
<!-- /MARKET -->
<!-- MARKET US -->
- **Weinstein Stage 2 Structure:** Price $> 20\text{-DMA} > 50\text{-DMA} > 200\text{-DMA}$ with positive relative strength (RS) vs S&P 500 (SPY).
<!-- /MARKET -->
- **Support-Aware Entry Distance:** Stock must be within **$\le 0.5 \times \text{ATR}(14)$** of verified structural base, horizontal pivot, or rising 20/50-DMA support.
<!-- MARKET IN -->
- **Rule:** Never buy an option on an extended stock ($>1.2\times \text{ATR}$) or broken Stage 4 stock.
<!-- /MARKET -->

#### Layer 2: Volatility Surface Squeeze Gate
- **Vol Ratio:** $\text{Vol Ratio} = \frac{IV_{30}}{RV_{30}} \le 1.10$.
- **IV Percentile:** Target contract IV must be in the **lower 40th percentile** of its 52-week range.
<!-- MARKET IN -->
- **Pre-Catalyst Volatility Strategy:** If trading ahead of earnings/corporate events, entry must occur **25–40 days BEFORE**. Position **MUST BE CLOSED 24–48 HOURS PRIOR TO THE EVENT** to capture IV expansion and avoid IV crush.
<!-- /MARKET -->
<!-- MARKET US -->
- **Pre-Catalyst Volatility Strategy:** If trading ahead of earnings, entry must occur **25–40 days BEFORE**. Position **MUST BE CLOSED 24–48 HOURS PRIOR TO EARNINGS** to capture IV expansion and completely bypass post-announcement **IV Crush**.
<!-- /MARKET -->

<!-- MARKET IN -->
#### Layer 3: NSE F&O Institutional Smart Money Footprint
- **Futures Activity Classification:**
  - **Long Build-Up (Price $\uparrow$, OI $\uparrow \ge 5\%$, Premium $\uparrow$):** QUALIFIED FOR OPTIONS BUYING.
  - **Short Covering (Price $\uparrow$, OI $\downarrow$):** REJECT / NO TRADE (Rally lacks institutional commitment).
  - **Short Build-Up (Price $\downarrow$, OI $\uparrow$):** REJECT / STRUCTURAL REJECTION.
  - **Long Unwinding (Price $\downarrow$, OI $\downarrow$):** REJECT / NO TRADE.
- **Strike OI Migration:** Call OI resistance must be shifting higher; Put OI accumulating at support strike; Strike PCR at support $> 1.20$.
<!-- /MARKET -->
<!-- MARKET US -->
#### Layer 3: CBOE Institutional Flow & GEX Radar
- **Net Gamma Exposure (GEX):** Underlying trading above Volatility Trigger in Positive Gamma regime. Call Wall acts as target price.
- **Institutional Flow (UOA):** Large block purchases on the Ask in target strikes without corresponding equity short blocks.
<!-- /MARKET -->

<!-- MARKET IN -->
#### Layer 4: Contract Structuring & Greek Sizing Protocol
- **Default Structure:** **Bull Call Vertical Debit Spread** (Buy Delta $0.50$ ATM Call / Sell Delta $0.25$ OTM Call at Resistance).
  - Eliminates $60\text{–}80\%$ of daily theta decay.
  - Reduces net capital at risk by $40\text{–}60\%$.
  - Target Payoff Asymmetry $\ge 3.0 : 1$ on debit paid.
- **Naked Call Exception:** Permitted ONLY when India VIX $< 13.0$ and stock IV percentile $< 30\%$. Long strike Delta $0.50\text{–}0.58$, Theta burn $< 1.5\%$/day.
<!-- /MARKET -->
<!-- MARKET US -->
#### Layer 4: Contract Structuring Protocol (Tactical vs LEAPS)

| Parameter | Tactical Momentum Setup (30–75 DTE) | Secular Compounder LEAPS (180–720 DTE) |
| :--- | :--- | :--- |
| **Asset Class** | Mid/Large-Cap Growth, Catalyst Breakouts | Elite Mega-Caps (AMZN, GOOG, ORCL, UBER, ADBE) |
| **Structure** | **Bull Call Vertical Debit Spread** (Delta 0.50 Buy / Delta 0.25 Sell) | **Naked Long Call (Delta 0.65–0.75 Deep ITM)** |
| **Target Horizon** | 45–60 DTE Monthly Options | 1–2 Year January/June LEAPS Cycles |
| **Theta Decay Budget** | $< 1.0\%$ of contract value per day | $< 0.15\%$ of contract value per day |
| **Target Payoff Hurdle** | Asymmetry $\ge 3.0 : 1$ on debit spread | Multi-year $3\times\text{–}5\times+$ compounder return |
<!-- /MARKET -->

---

<!-- MARKET IN -->
### THE 4-ACTION ACTIVE POSITION HEALTH AUDIT (KEEP VS. SELL):
<!-- /MARKET -->
<!-- MARKET US -->
### THE 4-ACTION US OPTIONS POSITION HEALTH AUDIT (KEEP VS. SELL):
<!-- /MARKET -->

<!-- MARKET IN -->
For every active position in `Portfolio Research System/05_Options_Book.md` and `data/options/<MKT>.json`, evaluate:
<!-- /MARKET -->
<!-- MARKET US -->
For every active position in `Portfolio Research System/05_Options_Book.md` and `data/options/<MKT>.json` (specifically auditing current holdings: AMZN, UBER, ADBE, SOFI, WMT, DHI), evaluate:
<!-- /MARKET -->

```mermaid
flowchart TD
<!-- MARKET IN -->
    A[Daily Active Option Position Audit] --> B{Underlying Closed Below 50-DMA or Support?}
<!-- /MARKET -->
<!-- MARKET US -->
    A[Daily Active Option Position Audit] --> B{Underlying Closed Below 50-DMA or 200-DMA Support?}
<!-- /MARKET -->
    B -- Yes --> C[ACTION: KILL POSITION IMMEDIATELY]
<!-- MARKET IN -->
    B -- No --> D{Current Option P&L <= -40% to -50%?}
<!-- /MARKET -->
<!-- MARKET US -->
    B -- No --> D{Current Option P&L <= -40% to -50% AND DTE < 60?}
<!-- /MARKET -->
    D -- Yes --> C
<!-- MARKET IN -->
    D -- No --> E{DTE < 20 Days AND Underlying Flat / Unchanged?}
    E -- Yes --> F[ACTION: TIME STOP EXIT / DO NOT ROLL]
    E -- No --> G{Option Gain >= +80% OR Delta >= 0.75?}
<!-- /MARKET -->
<!-- MARKET US -->
    D -- No --> E{Far OTM Delta Trap: Delta < 0.25 AND DTE < 120?}
    E -- Yes --> F[ACTION: HARVEST TAX LOSS / KILL]
    E -- No --> G{Option Gain >= +80% OR Delta >= 0.80?}
<!-- /MARKET -->
    G -- Yes --> H[ACTION: ROLL UP & OUT / HARVEST 50%]
    G -- No --> I{Underlying at Resistance & Momentum Fading?}
    I -- Yes --> J[ACTION: CONVERT TO SPREAD / FREEZE THETA]
    I -- No --> K[STATUS: HOLD / THESIS INTACT]
```

| Action | Technical & Greeks Trigger | Mandatory Execution Order |
| :--- | :--- | :--- |
<!-- MARKET IN -->
| **`HOLD`** | Underlying $> 20\text{-DMA} > 50\text{-DMA}$, Delta $0.40\text{–}0.70$, DTE $>20$ days, P&L $-20\%$ to $+60\%$. | Maintain position. Confirm GTT stop is active on broker terminal. |
| **`ROLL_UP_OUT`** | Option gain $\ge +80\%$ to $+150\%$, or Delta exceeds $0.75\text{–}0.85$. | Sell $100\%$ of deep ITM contract. Re-enter Delta $0.50$ in next expiry cycle; bank $100\%$ profits into Cash. |
| **`CONVERT_SPREAD`** | Trade is up $+30\%$ to $+60\%$, underlying tests Resistance 1, but momentum/volume stalling. | Sell OTM Call (Delta $0.25$) against long call to freeze delta and eliminate daily theta decay. |
| **`KILL`** | Option loses $\ge 40\text{–}50\%$, OR underlying closes below 50-DMA/support, OR DTE $<20$ without breakout. | Market order sell to close immediately. Never average down on a decaying option. |
<!-- /MARKET -->
<!-- MARKET US -->
| **`HOLD`** | Underlying $> 50\text{-DMA}$, Delta $0.40\text{–}0.70$, DTE $>60$ days, long-term secular moat intact. | Maintain position. Confirm trailing stop or mental invalidation level. |
| **`ROLL_UP_OUT`** | Option gain $\ge +80\%$ to $+150\%$, or Delta exceeds $0.80\text{–}0.85$. | Sell $100\%$ of deep ITM contract. Re-enter Delta $0.50\text{–}0.60$ in subsequent cycle; bank $100\%$ profits into Cash. |
| **`CONVERT_SPREAD`** | Trade is up $+30\%$ to $+60\%$, underlying tests major resistance, but momentum stalling. | Sell OTM Call (Delta $0.25$) against long call to freeze delta and eliminate daily theta decay. |
| **`KILL`** | Option loses $\ge 50\%$ with broken trend, OR underlying closes below 200-DMA, OR Delta drops below $0.25$ with $<120$ DTE remaining. | Market order sell to close immediately. Harvest capital / tax loss. |
<!-- /MARKET -->

---

<!-- MARKET IN -->
### HTML REPORT SPECIFICATION (`Options_Underwriting_NSE_<YYYY-MM-DD>.html`):
<!-- /MARKET -->
<!-- MARKET US -->
### HTML REPORT SPECIFICATION (`Options_Underwriting_US_<YYYY-MM-DD>.html`):
<!-- /MARKET -->

The output document must strictly adhere to the Wikipedia desktop article layout:

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<!-- MARKET IN -->
<title>NSE Derivatives & Options Underwriting Dossier — {{DATE}}</title>
<!-- /MARKET -->
<!-- MARKET US -->
<title>US Derivatives &amp; Options Underwriting Dossier — {{DATE}}</title>
<!-- /MARKET -->
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Lato, Helvetica, Arial, sans-serif; font-size: 14px; line-height: 1.6; color: #202122; background-color: #ffffff; margin: 0; padding: 20px; }
  .wiki-container { max-width: 1200px; margin: 0 auto; }
  h1.firstHeading { font-family: 'Linux Libertine', 'Georgia', 'Times', serif; font-size: 28px; font-weight: normal; border-bottom: 1px solid #a2a9b1; margin-bottom: 0.25em; padding-bottom: 0; }
  .siteSub { font-size: 12px; color: #54595d; margin-bottom: 1.4em; }
  h2 { font-family: 'Linux Libertine', 'Georgia', 'Times', serif; font-size: 21px; font-weight: normal; border-bottom: 1px solid #a2a9b1; margin-top: 1.5em; margin-bottom: 0.5em; }
  h3 { font-size: 16px; font-weight: bold; margin-top: 1.2em; margin-bottom: 0.3em; }
  .wikitable { background-color: #f8f9fa; color: #202122; margin: 1em 0; border: 1px solid #a2a9b1; border-collapse: collapse; width: 100%; font-size: 13px; }
  .wikitable th { background-color: #f3f4f6; text-align: left; padding: 6px 10px; border: 1px solid #a2a9b1; font-weight: bold; }
  .wikitable td { padding: 6px 10px; border: 1px solid #a2a9b1; vertical-align: top; }
  .infobox { border: 1px solid #a2a9b1; background-color: #f8f9fa; color: #202122; margin: 0.5em 0 1em 1em; padding: 0.2em; float: right; clear: right; width: 320px; font-size: 12px; line-height: 1.5; }
  .infobox th { background-color: #f3f4f6; text-align: left; padding: 4px 8px; border-bottom: 1px solid #a2a9b1; }
  .infobox td { padding: 4px 8px; }
  .status-green { background-color: #dcfce7; color: #166534; font-weight: bold; padding: 2px 6px; border-radius: 3px; }
  .status-yellow { background-color: #fef3c7; color: #78350f; font-weight: bold; padding: 2px 6px; border-radius: 3px; }
  .status-red { background-color: #f3f4f6; color: #92400e; font-weight: bold; padding: 2px 6px; border-radius: 3px; }
  .reflist { font-size: 12px; margin-top: 2em; border-top: 1px solid #a2a9b1; padding-top: 1em; }
</style>
</head>
<body>
<div class="wiki-container">
<!-- MARKET IN -->
<h1 class="firstHeading">NSE Derivatives &amp; Options Underwriting Dossier</h1>
<!-- /MARKET -->
<!-- MARKET US -->
<h1 class="firstHeading">US Derivatives &amp; Options Underwriting Dossier</h1>
<!-- /MARKET -->
<div class="siteSub">From Wikipedia, the free encyclopedia of institutional derivatives research &bull; Session: {{DATE}}</div>

<!-- MARKET IN -->
<!-- Table of Contents, Infobox, Section 1: Macro Volatility Regime, Section 2: Top Options Underwriting Leads, Section 3: Active Position Health Audit, Section 4: Execution Order Matrix, References -->
<!-- /MARKET -->
<!-- MARKET US -->
<!-- Table of Contents, Infobox, Section 1: CBOE Volatility & GEX Regime, Section 2: Top US Options Underwriting Leads, Section 3: Robinhood & Schwab Position Health Audit, Section 4: Execution Order Matrix, References -->
<!-- /MARKET -->

</div>
</body>
</html>
```
