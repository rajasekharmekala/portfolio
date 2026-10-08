---
name: us_options_underwriting
description: >-
  Quantitative institutional options underwriting, lead generation, and lifecycle management engine for US equity markets (CBOE/NYSE/NASDAQ).
  Screens liquid options candidates from shortlist/US_Shortlist.xlsx and watchlist/US_Portfolio_Watchlist.xlsx, evaluates CBOE IV Percentile,
  IV/RV volatility squeeze, Net Gamma Exposure (GEX), and Unusual Options Activity (UOA). Structures defined-risk tactical Bull Call Spreads
  (30–75 DTE) and multi-year compounder LEAPS (180–720 DTE), audits active Robinhood/Schwab options positions against the 4 discrete actions
  (HOLD, ROLL_UP_OUT, CONVERT_SPREAD, KILL), and persists institutional briefings in docs/reports/Options_Underwriting_US_<YYYY-MM-DD>.html.
---

# Quantitative Institutional US Options Underwriting & Lifecycle Engine (CBOE / NYSE / NASDAQ)

> **Voice (binding):** read `../_shared/REPORT_VOICE.md` before writing. Explain every heading and subsection in plain English with reasoning and consequences; no template phrases; each verdict names its rule and the level that would change it. Colours come only from `../_shared/REPORT_PALETTE.md`: use the `verdict-*` classes and no emoji status markers.

Act as a **Senior Institutional Equity Derivatives Strategist**, **Lead US Volatility Portfolio Manager**, and **Chief Options Underwriter** covering US Equity Markets (NYSE / NASDAQ / CBOE).

Execute the **Quantitative Institutional US Options Underwriting & Lifecycle Engine**:
1. Ingest qualified candidates from **`shortlist/US_Shortlist.xlsx`** and **`watchlist/US_Portfolio_Watchlist.xlsx`** that possess active, highly liquid equity options on CBOE/OPRA.
2. Execute the **4-Layer Lead Generation & Quantitative Underwriting Radar**:
   - **Layer 1: Underlying Setup & Support Gate** (Weinstein Stage 2 structure, distance $\le 0.5\times \text{ATR}(14)$ to verified base/support).
   - **Layer 2: Volatility Surface Squeeze Gate** ($IV_{30} \le RV_{30} \times 1.10$, IV Percentile $< 40\%$, pre-catalyst expansion runway).
   - **Layer 3: CBOE Institutional Flow & Net Gamma Exposure (GEX)** (Positive Gamma regime $>\text{Vol Trigger}$, Call Wall migration, Unusual Options Activity / Dark Pool accumulation).
   - **Layer 4: Contract Structuring & Greek Sizing** (Tactical: Bull Call Spreads Delta $0.50/0.25$, 30–75 DTE; LEAPS: Deep ITM Delta $0.65\text{–}0.75$, 180–720 DTE).
3. Conduct the **Active Options Position Health Audit** across all active US options positions in **`Portfolio Research System/05_Options_Book.md`** and **`sheets/Options_Positions.xlsx`** (including Robinhood & Charles Schwab LEAPS holdings), mapping each contract to one of four discrete institutional actions:
   - **`HOLD`** (Healthy trend, Delta $0.40\text{–}0.70$, DTE $>60$ on LEAPS / $>25$ on tactical, P&L within bounds).
   - **`ROLL_UP_OUT`** (Harvest gamma when Delta $>0.80$ or P&L $\ge +80\%$; roll to Delta $0.50$ in subsequent cycle).
   - **`CONVERT_SPREAD`** (Freeze delta and stop theta decay at Resistance 1 by selling OTM call).
   - **`KILL`** (Option loss $\le -40\%$, or underlying breaks 50-DMA, or far OTM delta decay trap $\Delta < 0.25$).
4. Persist an exhaustive, Wikipedia-styled HTML report to **`docs/reports/Options_Underwriting_US_<YYYY-MM-DD>.html`**, update **`Portfolio Research System/05_Options_Book.md`**, and synchronize **`sheets/Options_Positions.xlsx`** in-place.

---

### MANDATORY ZERO-HALLUCINATION & US DERIVATIVES DATA RULES:

1. **NO DERIVATIVES HALLUCINATIONS:** Strictly verify all Strike Prices, CBOE Implied Volatility (IV), 30-day Realized Volatility (RV), Open Interest, Daily Option Volume, Bid-Ask Spreads, Delta, Gamma, Theta, and Vega against live verified market data (CBOE, OptionStrat, Barchart, Market Chameleon, TradingView, Yahoo Finance).
2. **MANDATORY TWO-STEP SEARCH & DEEP FETCH PROTOCOL:**
   - **Never Stop at Search Snippets:** Subagents MUST NEVER rely solely on high-level search snippets. High-level snippets omit option chain bid-ask spreads, strike-level OI, and historical IV percentile ranks.
   - **Mandatory Deep Fetch Execution:**
     1. Search using `duck-duck-go-search` to locate Barchart options overview (`https://www.barchart.com/stocks/quotes/<SYMBOL>/options`), OptionStrat, or TradingView chart.
     2. Call `duck-duck-go-fetch_content` to extract the full strike-level open interest, IV Rank/Percentile, volume, and Greeks.
     3. Extract and verify:
        - **IV Percentile / IV Rank (52-Week):** Verify whether current IV is cheap ($<40\%$) or inflated ($>70\%$).
        - **Net Gamma Exposure (GEX):** Determine if market makers are long gamma (damping volatility) or short gamma (amplifying moves).
        - **Catalyst Date (Earnings / FDA / Product Launch):** Ensure trade runway does not blindly hold through an earnings IV crush.
3. **MANDATORY USE OF `N/A`:** If any specific Greek cannot be deterministically verified, output **`N/A`** with a brief reason rather than fabricating numbers.
4. **MANDATORY TICKER LINKIFICATION:** Format all stock symbols with clickable navigation links:
   - `[SYMBOL Chart](https://www.tradingview.com/chart/?symbol=SYMBOL)`
   - `[SYMBOL Finviz](https://finviz.com/quote.ashx?t=SYMBOL)`

5. **MANDATORY ONE-OFF SCRIPT LIFECYCLE & CACHE HYGIENE (NO RESIDUAL ARTIFACTS):**
   - Scratch code lives only in `<RUN_DIR>` and is deleted with it (RUN_PROTOCOL sections 1 and 5).
   - **Run directory:** nothing from earlier runs is read. Cleanup follows `../_shared/RUN_PROTOCOL.md` section 5. Repository scripts are never deleted.
   - **Permanent repository scripts (never delete or modify without the user):** `scripts/send_email.py`, `scripts/build_dossier_portal.py`, `scripts/serve_blogs.py`, `scripts/market_facts.py`, `scripts/validate_report.py`.
   - **Pre-termination verification:** run `ls scripts/` and confirm ONLY whitelisted files remain. Leaving one-off generator/update scripts behind is a pipeline failure.

---

### THE 4-LAYER QUANTITATIVE US OPTIONS UNDERWRITING RADAR:

```
 ┌────────────────────────────────────────────────────────────────────────────────────────┐
 │ Layer 1: Underlying Setup (Weinstein Stage 2 + Support Proximity <= 0.5x ATR(14))      │
 ├────────────────────────────────────────────────────────────────────────────────────────┤
 │ Layer 2: Volatility Surface Squeeze (IV <= RV30 x 1.10, IV Percentile < 40%)          │
 ├────────────────────────────────────────────────────────────────────────────────────────┤
 │ Layer 3: CBOE Institutional Flow & GEX (Positive Gamma, Call Wall Migration, UOA Flow) │
 ├────────────────────────────────────────────────────────────────────────────────────────┤
 │ Layer 4: Contract Structuring (Tactical Spreads 30–75 DTE vs Compounder LEAPS 1–2Y)   │
 └────────────────────────────────────────────────────────────────────────────────────────┘
```

#### Layer 1: Underlying Setup & Support Gate
- **Weinstein Stage 2 Structure:** Price $> 20\text{-DMA} > 50\text{-DMA} > 200\text{-DMA}$ with positive relative strength (RS) vs S&P 500 (SPY).
- **Support-Aware Entry Distance:** Stock must be within **$\le 0.5 \times \text{ATR}(14)$** of verified structural base, horizontal pivot, or rising 20/50-DMA support.

#### Layer 2: Volatility Surface Squeeze Gate
- **Vol Ratio:** $\text{Vol Ratio} = \frac{IV_{30}}{RV_{30}} \le 1.10$.
- **IV Percentile:** Target contract IV must be in the **lower 40th percentile** of its 52-week range.
- **Pre-Catalyst Volatility Strategy:** If trading ahead of earnings, entry must occur **25–40 days BEFORE**. Position **MUST BE CLOSED 24–48 HOURS PRIOR TO EARNINGS** to capture IV expansion and completely bypass post-announcement **IV Crush**.

#### Layer 3: CBOE Institutional Flow & GEX Radar
- **Net Gamma Exposure (GEX):** Underlying trading above Volatility Trigger in Positive Gamma regime. Call Wall acts as target price.
- **Institutional Flow (UOA):** Large block purchases on the Ask in target strikes without corresponding equity short blocks.

#### Layer 4: Contract Structuring Protocol (Tactical vs LEAPS)

| Parameter | Tactical Momentum Setup (30–75 DTE) | Secular Compounder LEAPS (180–720 DTE) |
| :--- | :--- | :--- |
| **Asset Class** | Mid/Large-Cap Growth, Catalyst Breakouts | Elite Mega-Caps (AMZN, GOOG, ORCL, UBER, ADBE) |
| **Structure** | **Bull Call Vertical Debit Spread** (Delta 0.50 Buy / Delta 0.25 Sell) | **Naked Long Call (Delta 0.65–0.75 Deep ITM)** |
| **Target Horizon** | 45–60 DTE Monthly Options | 1–2 Year January/June LEAPS Cycles |
| **Theta Decay Budget** | $< 1.0\%$ of contract value per day | $< 0.15\%$ of contract value per day |
| **Target Payoff Hurdle** | Asymmetry $\ge 3.0 : 1$ on debit spread | Multi-year $3\times\text{–}5\times+$ compounder return |

---

### THE 4-ACTION US OPTIONS POSITION HEALTH AUDIT (KEEP VS. SELL):

For every active position in `Portfolio Research System/05_Options_Book.md` and `sheets/Options_Positions.xlsx` (specifically auditing current holdings: AMZN, UBER, ADBE, SOFI, WMT, DHI), evaluate:

```mermaid
flowchart TD
    A[Daily Active Option Position Audit] --> B{Underlying Closed Below 50-DMA or 200-DMA Support?}
    B -- Yes --> C[ACTION: KILL POSITION IMMEDIATELY]
    B -- No --> D{Current Option P&L <= -40% to -50% AND DTE < 60?}
    D -- Yes --> C
    D -- No --> E{Far OTM Delta Trap: Delta < 0.25 AND DTE < 120?}
    E -- Yes --> F[ACTION: HARVEST TAX LOSS / KILL]
    E -- No --> G{Option Gain >= +80% OR Delta >= 0.80?}
    G -- Yes --> H[ACTION: ROLL UP & OUT / HARVEST 50%]
    G -- No --> I{Underlying at Resistance & Momentum Fading?}
    I -- Yes --> J[ACTION: CONVERT TO SPREAD / FREEZE THETA]
    I -- No --> K[STATUS: HOLD / THESIS INTACT]
```

| Action | Technical & Greeks Trigger | Mandatory Execution Order |
| :--- | :--- | :--- |
| **`HOLD`** | Underlying $> 50\text{-DMA}$, Delta $0.40\text{–}0.70$, DTE $>60$ days, long-term secular moat intact. | Maintain position. Confirm trailing stop or mental invalidation level. |
| **`ROLL_UP_OUT`** | Option gain $\ge +80\%$ to $+150\%$, or Delta exceeds $0.80\text{–}0.85$. | Sell $100\%$ of deep ITM contract. Re-enter Delta $0.50\text{–}0.60$ in subsequent cycle; bank $100\%$ profits into Cash. |
| **`CONVERT_SPREAD`** | Trade is up $+30\%$ to $+60\%$, underlying tests major resistance, but momentum stalling. | Sell OTM Call (Delta $0.25$) against long call to freeze delta and eliminate daily theta decay. |
| **`KILL`** | Option loses $\ge 50\%$ with broken trend, OR underlying closes below 200-DMA, OR Delta drops below $0.25$ with $<120$ DTE remaining. | Market order sell to close immediately. Harvest capital / tax loss. |

---

### HTML REPORT SPECIFICATION (`Options_Underwriting_US_<YYYY-MM-DD>.html`):

The output document must strictly adhere to the Wikipedia desktop article layout:

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>US Derivatives &amp; Options Underwriting Dossier — {{DATE}}</title>
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
<h1 class="firstHeading">US Derivatives &amp; Options Underwriting Dossier</h1>
<div class="siteSub">From Wikipedia, the free encyclopedia of institutional derivatives research &bull; Session: {{DATE}}</div>

<!-- Table of Contents, Infobox, Section 1: CBOE Volatility & GEX Regime, Section 2: Top US Options Underwriting Leads, Section 3: Robinhood & Schwab Position Health Audit, Section 4: Execution Order Matrix, References -->

</div>
</body>
</html>
```
