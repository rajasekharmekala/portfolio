---
name: options_desk
description: >-
  Fast standalone Options & Call-Convexity Desk skill (IN = NSE F&O, US = listed
  US options & LEAPS) with beginner-clear wallet math, multi-timeframe TradingView
  (1W/1D/4H) dislocation & VCP analysis, graceful read-only Robinhood Chrome session
  check, active open-options book audit, and optional surgical #options-overlay
  updates to published dossiers without regenerating 15,000-word company monographs.
---

# Skill: options_desk (Standalone Tactical Call-Convexity & Multi-Timeframe Options Desk)

> **Why this is a separate workflow:** Options bid/ask spreads, Implied Volatility (`IV`), DTE, and intraday chart shelves change every session — regenerating a 15,000-word 10-chapter monograph just to price a rebound call or audit open Robinhood LEAPS is wasteful. `options_desk` reuses the already-locked `business_quality.json` fundamental verdict from `data/dossiers/<MARKET>/<SYMBOL>/` (so you never buy rebound calls on a `FUNDAMENTAL_FAIL` business) and runs live options + multi-timeframe technical pricing in seconds.

---

## Core Rules (Professional Discipline + Beginner-Clear Explanations)

1. **Beginner-Clear Plain-Dollar Explanations (Mandatory):**
   - Every recommended trade and open-position audit must explain in plain English:
     - **Total Upfront Cost = Absolute Max Loss** (e.g., `1 contract x 100 shares x $4.20 = $420 max possible loss`, capped at `<= 60 bps` of portfolio NAV).
     - **Exact Breakeven Price at Expiry** and **Maximum Profit** (`$/₹` and `% return on risk`).
     - **Delta, IV vs. HV20, and Daily Theta in plain wallet terms** (`$/₹ gained per $1/₹1 stock move`, whether option insurance is cheap or inflated vs. 20-day actual stock volatility, and `$/₹ lost per day` if the stock sits flat).
     - **4-Scenario Payoff Table** (`Stop Hit`, `Flat / Breakeven`, `Base Target`, `Bull Target`) comparing exact option P&L against owning shares.
2. **Liquidity & Market Reality Gate (`NOT_OPTIONABLE_OR_ILLIQUID`):**
   - In India, only NSE F&O stocks (~200 liquid large/mid-caps, 1–3 month expiries; **no** single-stock LEAPS) are eligible; SME/small-caps automatically receive `NOT_OPTIONABLE_OR_ILLIQUID`.
   - Any chain with bid-ask spreads `> 14%` of mid or thin open interest is rejected automatically; always specify **limit orders near mid-price**.
3. **Equity vs. Options Lens & IV-Aware Structure Selection:**
   - Even when a `COMPOUNDER_PASS` stock temporarily breaks below its 50D SMA into a major 200D/30W shelf on news (`DISLOCATION_AT_MAJOR_SHELF`), options can structure a defined-risk rebound play **if** `business_quality_verdict != "FUNDAMENTAL_FAIL"`.
   - **Elevated IV (`IV > 1.15x HV20`) or 30–120 DTE tactical rebounds (all IN F&O + US dislocations):** use a **Bull Call Debit Spread** (selling the upper resistance call cuts cost, theta, and post-news IV crush).
   - **Calm/Fair IV (`IV <= 1.15x HV20`) on US `COMPOUNDER_PASS` bases/VCP coils:** use **0.65–0.80 Delta LEAPS Calls (`>= 240 DTE`)** so extrinsic time decay is minimal.
4. **Graceful macOS Chrome Robinhood & TradingView Check (`macos-browser-automation`):**
   - `scripts/options_snapshot.py` performs a strictly read-only check for an open, logged-in `robinhood.com` tab (US) and `tradingview.com` chart tabs.
   - **If Chrome is closed, Apple Events JS is off, or Robinhood is not logged in, do NOT block or fail:** `options_snapshot.py` automatically falls back to public options chains + `data/options/<MARKET>.json` and discloses in the report that live broker data was unavailable.
   - When TradingView is open in Chrome, use `macos-browser-automation` (`chrome_ctl.py`) to inspect Weekly (`1W`) and Daily (`1D`) support shelves, gaps, and volume profile alongside the deterministic `1W / 1D / 4H` scanner readout.

---

## Step-by-Step Execution Protocol

1. **Start Isolated Worktree (when publishing to `docs/reports/`):**
   ```bash
   .venv/bin/python scripts/run_session.py start --workflow options_desk --market <MARKET>
   ```
2. **Pull Live Options Chains, Multi-Timeframe Setup & Graceful Robinhood Probe:**
   ```bash
   # Evaluate specific tickers and/or all open options + active shortlist names:
   .venv/bin/python scripts/options_snapshot.py \
     --market <MARKET> \
     --symbols <SYMBOL_1> <SYMBOL_2> \
     --from-options --from-shortlist \
     --net-worth <PORTFOLIO_NAV> \
     --patch-dossier-specs \
     --out "<RUN_DIR>/cache/options_snapshot_<MARKET>_<date>.json"
   ```
3. **Compile Standalone Options Desk Report (+ Optional Zero-Rewrite Dossier Overlay Patch):**
   ```bash
   .venv/bin/python scripts/options_desk_builder.py \
     --snapshot "<RUN_DIR>/cache/options_snapshot_<MARKET>_<date>.json" \
     --as-of "<YYYY-MM-DD>" \
     --out "docs/reports/<MARKET>_Options_Desk.html" \
     --patch-published-dossiers
   ```
   `--patch-published-dossiers` surgically refreshes `<section id="options-overlay">` inside any matching `docs/blogs/<MARKET>/<SYMBOL>_dossier.html` in <1 second without touching Chapters 0–9!
4. **Validate & Publish:**
   - Verify `portal_publish.require_modern_report` on `docs/reports/<MARKET>_Options_Desk.html`, rebuild catalog via `scripts/build_dossier_portal.py --completed ...`, and publish via `scripts/publish_run.py`.
