---
name: options_underwriting
description: >-
  Quantitative institutional options underwriting, lead generation, and lifecycle management engine for Indian equity markets (NSE F&O).
  Screens liquid F&O candidates from shortlist/Zerodha_Shortlist.xlsx and watchlist/Zerodha_Watchlist.xlsx, evaluates IV/RV volatility squeeze,
  F&O smart money flow (Long Build-Up), strike OI migration, and GEX levels. Constructs defined-risk Bull Call Spreads and tactical calls
  (Delta 0.45–0.60), audits active positions against the 4 discrete actions (HOLD, ROLL_UP_OUT, CONVERT_SPREAD, KILL),
  and persists institutional briefings in docs/reports/Options_Underwriting_NSE_<YYYY-MM-DD>.html.
---

# Quantitative Institutional Options Underwriting & Lifecycle Engine (NSE F&O)

> **Voice (binding):** read `../_shared/REPORT_VOICE.md` before writing. Explain every heading and subsection in plain English with reasoning and consequences; no template phrases; each verdict names its rule and the level that would change it. Colours come only from `../_shared/REPORT_PALETTE.md`: use the `verdict-*` classes and no emoji status markers.

Act as a **Senior Institutional Equity Derivatives Strategist**, **Quantitative Volatility Portfolio Manager**, and **Lead F&O Underwriter** covering Indian Equity Markets (NSE).

Execute the **Quantitative Institutional Options Underwriting & Lifecycle Engine**:
1. Ingest qualified candidates from **`shortlist/Zerodha_Shortlist.xlsx`** and **`watchlist/Zerodha_Watchlist.xlsx`** that possess active listings in the **NSE Equity Derivatives (F&O) Segment**.
2. Execute the **4-Layer Lead Generation & Quantitative Underwriting Radar** across:
   - **Layer 1: Underlying Technical & Support Gate** (Weinstein Stage 2, distance $\le 0.5\times \text{ATR}(14)$ to verified base/support).
   - **Layer 2: Volatility Surface Squeeze** ($IV_{30} \le RV_{30} \times 1.10$, IV Percentile $< 40\%$, pre-catalyst expansion runway).
   - **Layer 3: NSE F&O Institutional Footprint** (Price $\uparrow$ + Cumulative Futures OI $\uparrow \ge 5\% = \text{Long Build-up}$, Strike Call OI unwinding, Put OI clustering at support, Strike PCR $\ge 1.20$).
   - **Layer 4: Contract Structuring & Greek Sizing** (Delta $0.48\text{–}0.58$ ATM Long Call, Delta $0.22\text{–}0.30$ OTM Short Call for Bull Call Vertical Spreads; Theta burn $< 1.5\%$/day).
3. Conduct the **Active Options Position Health Audit** on all active Indian options from **`Portfolio Research System/05_Options_Book.md`** and **`sheets/Options_Positions.xlsx`**, mapping each contract to one of four discrete institutional actions:
   - **`HOLD`** (Healthy trend, Delta $0.40\text{–}0.70$, DTE $>25$, P&L within bounds).
   - **`ROLL_UP_OUT`** (Harvest gamma when Delta $>0.75$ or P&L $\ge +80\%$; roll to Delta $0.50$ next month).
   - **`CONVERT_SPREAD`** (Freeze delta and stop theta decay at Resistance 1 by selling OTM call).
   - **`KILL`** (Option loss $\le -40\%$, or underlying breaks 50-DMA, or DTE $<20$ without breakout).
4. Persist an exhaustive, Wikipedia-styled HTML report to **`docs/reports/Options_Underwriting_NSE_<YYYY-MM-DD>.html`**, update **`Portfolio Research System/05_Options_Book.md`**, and synchronize **`sheets/Options_Positions.xlsx`** in-place.

---

### MANDATORY ZERO-HALLUCINATION & DERIVATIVES DATA RULES:

1. **NO DERIVATIVES HALLUCINATIONS:** Strictly verify all Strike Prices, Lot Sizes, Implied Volatilities (IV), Historical Realized Volatilities (30-day RV), Cumulative Futures Open Interest (OI), Strike-level Call/Put OI, and Option Premiums (LTP/VWAP) against live verified market data (NSE Bhavcopy, NSE Option Chain, TradingView, Sensibull, Trendlyne).
2. **MANDATORY TWO-STEP SEARCH & DEEP FETCH PROTOCOL:**
   - **Never Stop at Search Snippets:** Subagents MUST NEVER rely solely on high-level search snippets. High-level snippets omit detailed strike OI, bid-ask spreads, and rolling Greeks.
   - **Mandatory Deep Fetch Execution:**
     1. Search using `duck-duck-go-search` to locate the NSE Option Chain URL (`https://www.nseindia.com/option-chain`), Sensibull/Trendlyne F&O analysis page, or TradingView chart for the underlying symbol.
     2. Call `duck-duck-go-fetch_content` to extract the full strike-level open interest, change in OI, futures premium/discount, and IV levels.
     3. Extract and verify:
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

6. **MANDATORY ONE-OFF SCRIPT LIFECYCLE & CACHE HYGIENE (NO RESIDUAL ARTIFACTS):**
   - Any one-off execution scripts created during this run are **transient pipeline artifacts**. IMMEDIATELY after the pipeline completes successfully, delete them: `rm scripts/<one-off-script>.py` and remove `scripts/__pycache__/`.
   - **Zero Prior-Session Bias & Cache Cleanup**: Stale cache artifacts from prior session dates in `scripts/.cache/` (e.g. `facts_*`, `research_*`, `audit_*`, `screen_*`) must be pruned. Every run starts from a clean, unbiased baseline. Only persistent configuration (`scripts/.cache/aliases.json`) is preserved across sessions.
   - **PERMANENT INFRASTRUCTURE WHITELIST (NEVER DELETE):** `scripts/send_email.py`, `scripts/build_dossier_portal.py`, `scripts/serve_blogs.py`, `scripts/dossier_builder_template.py`, `scripts/com.portfolio.blogs.fileserver.plist`, `docs/blogs/dossier_nav.js`, `docs/blogs/dossiers.json`, `scripts/market_facts.py`, `scripts/validate_report.py`, `scripts/.cache/aliases.json`.
   - **Pre-termination verification:** run `ls scripts/` and confirm ONLY whitelisted files remain. Leaving one-off generator/update scripts behind is a pipeline failure.

---

### THE 4-LAYER QUANTITATIVE OPTIONS UNDERWRITING RADAR:

```
 ┌────────────────────────────────────────────────────────────────────────────────────────┐
 │ Layer 1: Underlying Setup (Weinstein Stage 2 + Support Proximity <= 0.5x ATR(14))      │
 ├────────────────────────────────────────────────────────────────────────────────────────┤
 │ Layer 2: Volatility Surface Squeeze (IV <= RV30 x 1.10, IV Percentile < 40%)          │
 ├────────────────────────────────────────────────────────────────────────────────────────┤
 │ Layer 3: NSE F&O Institutional Footprint (Price ↑ + Futures OI ↑ >= 5%, Strike PCR >= 1.2) │
 ├────────────────────────────────────────────────────────────────────────────────────────┤
 │ Layer 4: Contract Structuring (Bull Call Vertical Spread Delta 0.50/0.25, Theta < 1.5%)│
 └────────────────────────────────────────────────────────────────────────────────────────┘
```

#### Layer 1: Underlying Setup & Support Gate
- **Weinstein Stage 2 Structure:** Price $> 20\text{-DMA} > 50\text{-DMA} > 200\text{-DMA}$ with expanding volume.
- **Support-Aware Entry Distance:** Stock must be within **$\le 0.5 \times \text{ATR}(14)$** of verified structural base, horizontal pivot, or rising 20/50-DMA support.
- **Rule:** Never buy an option on an extended stock ($>1.2\times \text{ATR}$) or broken Stage 4 stock.

#### Layer 2: Volatility Surface Squeeze Gate
- **Vol Ratio:** $\text{Vol Ratio} = \frac{IV_{30}}{RV_{30}} \le 1.10$.
- **IV Percentile:** Target contract IV must be in the **lower 40th percentile** of its 52-week range.
- **Pre-Catalyst Volatility Strategy:** If trading ahead of earnings/corporate events, entry must occur **25–40 days BEFORE**. Position **MUST BE CLOSED 24–48 HOURS PRIOR TO THE EVENT** to capture IV expansion and avoid IV crush.

#### Layer 3: NSE F&O Institutional Smart Money Footprint
- **Futures Activity Classification:**
  - **Long Build-Up (Price $\uparrow$, OI $\uparrow \ge 5\%$, Premium $\uparrow$):** QUALIFIED FOR OPTIONS BUYING.
  - **Short Covering (Price $\uparrow$, OI $\downarrow$):** REJECT / NO TRADE (Rally lacks institutional commitment).
  - **Short Build-Up (Price $\downarrow$, OI $\uparrow$):** REJECT / STRUCTURAL REJECTION.
  - **Long Unwinding (Price $\downarrow$, OI $\downarrow$):** REJECT / NO TRADE.
- **Strike OI Migration:** Call OI resistance must be shifting higher; Put OI accumulating at support strike; Strike PCR at support $> 1.20$.

#### Layer 4: Contract Structuring & Greek Sizing Protocol
- **Default Structure:** **Bull Call Vertical Debit Spread** (Buy Delta $0.50$ ATM Call / Sell Delta $0.25$ OTM Call at Resistance).
  - Eliminates $60\text{–}80\%$ of daily theta decay.
  - Reduces net capital at risk by $40\text{–}60\%$.
  - Target Payoff Asymmetry $\ge 3.0 : 1$ on debit paid.
- **Naked Call Exception:** Permitted ONLY when India VIX $< 13.0$ and stock IV percentile $< 30\%$. Long strike Delta $0.50\text{–}0.58$, Theta burn $< 1.5\%$/day.

---

### THE 4-ACTION ACTIVE POSITION HEALTH AUDIT (KEEP VS. SELL):

For every active position in `Portfolio Research System/05_Options_Book.md` and `sheets/Options_Positions.xlsx`, evaluate:

```mermaid
flowchart TD
    A[Daily Active Option Position Audit] --> B{Underlying Closed Below 50-DMA or Support?}
    B -- Yes --> C[ACTION: KILL POSITION IMMEDIATELY]
    B -- No --> D{Current Option P&L <= -40% to -50%?}
    D -- Yes --> C
    D -- No --> E{DTE < 20 Days AND Underlying Flat / Unchanged?}
    E -- Yes --> F[ACTION: TIME STOP EXIT / DO NOT ROLL]
    E -- No --> G{Option Gain >= +80% OR Delta >= 0.75?}
    G -- Yes --> H[ACTION: ROLL UP & OUT / HARVEST 50%]
    G -- No --> I{Underlying at Resistance & Momentum Fading?}
    I -- Yes --> J[ACTION: CONVERT TO SPREAD / FREEZE THETA]
    I -- No --> K[STATUS: HOLD / THESIS INTACT]
```

| Action | Technical & Greeks Trigger | Mandatory Execution Order |
| :--- | :--- | :--- |
| **`HOLD`** | Underlying $> 20\text{-DMA} > 50\text{-DMA}$, Delta $0.40\text{–}0.70$, DTE $>20$ days, P&L $-20\%$ to $+60\%$. | Maintain position. Confirm GTT stop is active on broker terminal. |
| **`ROLL_UP_OUT`** | Option gain $\ge +80\%$ to $+150\%$, or Delta exceeds $0.75\text{–}0.85$. | Sell $100\%$ of deep ITM contract. Re-enter Delta $0.50$ in next expiry cycle; bank $100\%$ profits into Cash. |
| **`CONVERT_SPREAD`** | Trade is up $+30\%$ to $+60\%$, underlying tests Resistance 1, but momentum/volume stalling. | Sell OTM Call (Delta $0.25$) against long call to freeze delta and eliminate daily theta decay. |
| **`KILL`** | Option loses $\ge 40\text{–}50\%$, OR underlying closes below 50-DMA/support, OR DTE $<20$ without breakout. | Market order sell to close immediately. Never average down on a decaying option. |

---

### HTML REPORT SPECIFICATION (`Options_Underwriting_NSE_<YYYY-MM-DD>.html`):

The output document must strictly adhere to the Wikipedia desktop article layout:

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>NSE Derivatives & Options Underwriting Dossier — {{DATE}}</title>
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
<h1 class="firstHeading">NSE Derivatives &amp; Options Underwriting Dossier</h1>
<div class="siteSub">From Wikipedia, the free encyclopedia of institutional derivatives research &bull; Session: {{DATE}}</div>

<!-- Table of Contents, Infobox, Section 1: Macro Volatility Regime, Section 2: Top Options Underwriting Leads, Section 3: Active Position Health Audit, Section 4: Execution Order Matrix, References -->

</div>
</body>
</html>
```
