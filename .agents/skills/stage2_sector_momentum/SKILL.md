---
name: stage2_sector_momentum
description: >-
  Stan Weinstein Stage 2 market breadth, sector rotation, and breakout scanner for India (IN = NSE/BSE) and the United States (US = NYSE/NASDAQ). Automates extraction from TheWrap's live PowerBI dashboards (https://thewrap.in/data-tools/stage2 for IN and https://thewrap.in/data-tools/ustocks for US) via Chrome Apple Events, enriches candidates with live TradingView technicals and Screener.in / Finviz valuations (scripts/stock_snapshot.py), evaluates No-FOMO entry timing (Immediate Buy vs. Wait for Support), prunes broken Stage 4 names from the watchlist, and funnels fresh Stage 2 breakouts into data/watchlist/<MKT>.json.
---

# Stan Weinstein Stage 2 Sector Rotation & Momentum Scanner Skill (IN & US)

> **Design & Quality Standards (binding):**
> - Read `../_shared/REPORT_DESIGN.md`, `../_shared/REPORT_VOICE.md`, and `../_shared/REPORT_PALETTE.md`.
> - **Zero LLM Math:** Never compute moving averages, RSI, volume ratios, or P/E multiples in your head. All numbers must come directly from `scripts/stage2_scanner.py` (`data/views/stage2_<MKT>_latest.json`) and `scripts/stock_snapshot.py` (TradingView + Screener.in / Finviz).
> - Distinctly separate **Stage 2 Trend Quality** (durability of sector & institutional trend) from **No-FOMO Entry Timing** (`IMMEDIATE_BUY` at CMP vs. `WAIT_FOR_SUPPORT` / `ACCUMULATE_ON_DIP` when extended from the 10-week EMA / 50-day SMA).

---

## 1. Objective & Role

Act as a **Senior Momentum Strategist & Institutional Portfolio Manager** for `<MKT>` (`IN` or `US`).

Execute the **Stage 2 Sector Momentum & Consumer-Tool Snapshot Engine**:
1. **Extract Sector & Universe Stage 2 Breadth (`scripts/stage2_scanner.py`):**
   - **IN:** `https://thewrap.in/data-tools/stage2` (filtered to Market Cap $\ge$ ₹1,000 Cr; updates weekly on Saturdays).
   - **US:** `https://thewrap.in/data-tools/ustocks` (filtered to Market Cap $\ge$ \$1.0B; updates daily).
2. **Pull Per-Stock TradingView Technicals & Valuation Cards + Prune Watchlist (`scripts/stock_snapshot.py`):**
   - Query live TradingView technicals (`SMA10`, `SMA20`, `SMA50`, `SMA200`, `SMA30|1W` [30-week SMA], `EMA10`, `EMA20`, `EMA50`, `EMA200`, `EMA10|1W`, `RSI-14`, `ATR-14`, 10d/30d volume ratios, classic pivots, Technical Rating) and Screener.in (`IN`) / Finviz (`US`) valuation metrics.
   - Automatically prune broken `STAGE_4` / rejected entries from `data/watchlist/<MKT>.json` (`active` $\to$ `archive`) so the watchlist stays focused.
3. **Rank Momentum Sectors & Industries:**
   - Identify **Super-Clusters** ($>60\%$ in Stage 2 for IN; $>75\%$ outperforming S&P 500 and $>65\%$ above 200D/50D EMA for US).
   - Identify **Emerging Rotation Clusters** ($40\text{--}60\%$ in Stage 2 or surging 1W/2W industry returns with low stock correlation).
   - Identify **Deteriorating / Avoid Zones** ($<30\%$ in Stage 2 or $<35\%$ above 50D EMA).
4. **Categorize Candidate Stocks into Conviction Tiers & No-FOMO Entry Groups:**
   - **Conviction Tiers:**
     - **Tier 1: "No Brainer" Advancing Leaders** (Dominant sector breadth, liquid institutional sponsorship, strong earnings growth).
     - **Tier 2: "Highly Positive Bet" Breakout Setups** (Fresh Week 1 Stage 2 additions, 52W High / Base Building / Consolidation breakouts on expanding volume).
     - **Tier 3: "Early Stage 2 / Cheat Entry" Opportunities** (Weeks 1–4 in Stage 2 or tight MA/Consolidation breakout near the 30-week SMA / 50-day SMA with minimal extension).
   - **No-FOMO Entry Timing (from `stage2_evaluation` in `stock_snapshot.py`):**
     - **`IMMEDIATE_BUY` (Buy at CMP):** In Stage 2 (or constructive pullback/base), within $10\%$ of the 10-week EMA and $12\%$ of the 50-day SMA, $\text{RSI}(14) \le 73$, and reasonable valuation relative to growth.
     - **`WAIT_FOR_SUPPORT` (Pullback Limit Order Only):** Strong Stage 2 trend and business, but extended ($>10\%$ above 10W EMA, $>12\%$ above 50D SMA, or $\text{RSI}(14) > 73$) or rich valuation. Do **not** chase; specify the exact 20D EMA / 10W EMA / 50D SMA buy zone.
5. **Audit Current Holdings & Shortlist Against Stage 2 Trends:**
   - Show how each open holding and shortlist candidate stacks up in the Stage 2 sector matrix and TradingView trend structure.
6. **Synchronize `data/watchlist/<MKT>.json` & Publish Report:**
   - Ingest top fresh Stage 2 breakout leads into `data/watchlist/<MKT>.json` (validated via `scripts/data_layer.py --market <MKT> --validate`) and assemble `docs/reports/<MKT>_Stage2_Sector_Momentum.html`.

---

## 2. Step-by-Step Execution Protocol

### Step 1: Extract TheWrap Stage 2 & Sector Momentum Snapshot
Run `scripts/stage2_scanner.py` for the target market:
- **India (`IN`):**
  ```bash
  .venv/bin/python scripts/stage2_scanner.py --market IN --min-mcap 1000 --out data/views/stage2_IN_latest.json
  ```
- **United States (`US`):**
  ```bash
  .venv/bin/python scripts/stage2_scanner.py --market US --min-mcap 1.0 --out data/views/stage2_US_latest.json
  ```
Also copy or save a dated copy in `<RUN_DIR>/cache/stage2_<MKT>_<date>.json`.

### Step 2: Enrich with TradingView + Screener.in/Finviz & Prune Watchlist
Select the top 10–15 candidate symbols from the Stage 2 scanner (`new_stage2_this_week`, `top_25_stage2`, or `breakout_scanner` / `volume_scanner_leaders`) and run `scripts/stock_snapshot.py` across those candidates plus all active watchlist, shortlist, and holding symbols:
```bash
.venv/bin/python scripts/stock_snapshot.py \
  --market <MKT> \
  --from-watchlist --from-shortlist --from-holdings \
  --symbols <SYM1> <SYM2> ... \
  --stage2-file data/views/stage2_<MKT>_latest.json \
  --prune-watchlist \
  --out "<RUN_DIR>/cache/snapshots_<MKT>_<date>.json"
```
This single command:
1. Prunes any active watchlist stocks that have deteriorated into a `STAGE_4` breakdown or carry a `REJECTED` verdict, moving them to `watchlist.archive`.
2. Produces exact TradingView + Screener.in (`IN`) / Finviz (`US`) + TheWrap Stage 2 cards and deterministic `stage2_evaluation` blocks (`weinstein_stage`, `entry_timing_posture`, `recommended_verdict`, `support_buy_zone`, `invalidation_stop`, `valuation_assessment`).

### Step 3: Fundamental & Catalyst Verification Pass
For the top 8–12 candidate stocks, run targeted web searches (`search_web`) to verify:
- Latest quarterly Revenue and PAT/EPS YoY growth and margin trajectory.
- Concrete catalysts: order-book wins, capacity expansion, debt reduction, new product cycles, regulatory approvals, or guidance raises.
- Exchange surveillance (`IN`: Mainboard vs SME, ASM/ESM flags) or earnings dates (`US`).
- Log every source URL in `<RUN_DIR>/cache/research_<MKT>_<date>.json` using `scripts/research_log.py`.

### Step 4: Watchlist Ingestion (`data/watchlist/<MKT>.json`)
Add the top 2–5 fresh, unowned Stage 2 breakout candidates into `data/watchlist/<MKT>.json` (`active` array). Every record **must** include all 9 required fields defined in `schemas/watchlist_record.schema.json`:
- `symbol`: Ticker symbol
- `company_name`: Full company name
- `date_added`: `<YYYY-MM-DD>`
- `macro_sector`: Sector/industry from TheWrap / TradingView
- `strategy_bucket`: `"TACTICAL_MOMENTUM"` or `"CORE_ALPHA"`
- `source_type`: `"STAGE2_BREAKOUT"`
- `status`: `"RESEARCH_REQUIRED"`
- `catalyst_timeline`: Specific near/medium-term catalyst window
- `summary_rationale`: Concise synthesis citing Stage 2 sector density, TradingView technical structure, valuation multiple, and No-FOMO entry zone (`IMMEDIATE_BUY` vs. `WAIT_FOR_SUPPORT`).

Run `.venv/bin/python scripts/data_layer.py --market <MKT> --validate` immediately after updating `data/watchlist/<MKT>.json`.

---

## 3. Deliverable Structure (`docs/reports/<MKT>_Stage2_Sector_Momentum.html`)

Write a comprehensive, beginner-friendly Research Desk report (`<RUN_DIR>/work/body.html`) and assemble it with `scripts/assemble_report.py --market <MKT> --kind report --workflow stage2_sector_momentum --as-of <date>`:

1. **Executive Summary & Breadth Pulse:**
   - Summary KPI cards (`<dl class="key-figures">`): Universe filtered count, Continuing/Breakout counts, Top Stage 2 Sector, Watchlist Pruned count, and New Watchlist Additions.
   - Plain-English `primer` explaining Stan Weinstein's 4 stages and why we combine Sector Breadth + TradingView Support Distance + Valuation Sanity to avoid FOMO.
2. **Sector & Industry Rotation Matrix:**
   - Full ranked table of leading and lagging sectors/industries (`% in Stage 2` for IN; `% Outperforming S&P 500`, `% Above 200D/50D/20D EMA`, and `1W/1M/3M Returns` for US).
   - Narrative breakdown of Super-Clusters vs. Emerging Rotation Themes vs. Capital Outflow Zones.
3. **Top Stage 2 Breakout & Momentum Setups (TradingView + Valuation Matrix):**
   - Master comparison table showing Symbol, Industry, Stage 2 Status / Weeks or Breakout Type, CMP, 50D SMA, 30W SMA, Extension % from 10W EMA, RSI(14), Rel Volume, P/E (Screener/Finviz), ROE/ROCE, and **No-FOMO Action Verdict** (`IMMEDIATE BUY` vs. `WAIT FOR SUPPORT`).
4. **Per-Stock Deep-Dive Case Notes (`<div class="casenote" data-symbol="...">`):**
   - Dedicated case notes for the top 8–12 setups covering: (a) Sector & Stage 2 structure, (b) TradingView moving averages, volume & RSI, (c) Fundamental catalyst & Screener/Finviz valuation check, and (d) Exact execution plan (`IMMEDIATE_BUY` at CMP vs. `WAIT_FOR_SUPPORT` limit zone + invalidation stop).
5. **Current Holdings & Shortlist Stage 2 Health Check:**
   - Table and commentary auditing existing portfolio holdings and active shortlist names against the latest Stage 2 sector and TradingView snapshot (highlighting leaders to let run, extended names, and any Stage 3/4 warnings).
6. **Watchlist Pruning & Ingestion Manifest:**
   - Explicit record of broken Stage 4 / rejected names pruned to `watchlist.archive` and fresh Stage 2 leaders added to `watchlist.active`.
