---
description: Stan Weinstein Stage 2 sector rotation, TradingView technicals, and valuation scanner for one market (IN or US). Extracts TheWrap PowerBI data via Chrome automation, enriches with TradingView & Screener.in/Finviz snapshots, prunes Stage 4 dead weight from the watchlist, and ingests fresh Stage 2 breakouts.
---

# Stage 2 Sector Momentum Workflow (Market: `<MKT>`)

Read `_COMMON.md` first. Choose `<MKT>` = `IN` or `US` and look up its row in `.agents/config/markets.json`.

**Target Cadence:**
- `IN`: Weekly (every Saturday / Sunday after TheWrap's weekly Stage 2 dashboard update) or on demand.
- `US`: Daily or multiple times per week (TheWrap's US Stocks dashboard updates daily).

---

## 1. Run Directory and Preflight

1. Start the isolated run worktree and singleton claim per `_COMMON.md`:
   ```bash
   .venv/bin/python scripts/run_session.py start --workflow stage2_sector_momentum --market <MKT>
   ```
   `cd` into the printed `worktree` path and set `RUN_DIR` to `run_dir`.
2. Verify Google Chrome is running with Apple Events JavaScript enabled (`View > Developer > Allow JavaScript from Apple Events`).

---

## 2. Automated Browser Extraction (`scripts/stage2_scanner.py`)

Run the browser extractor for `<MKT>`:
- **For `IN` ($\ge$ ₹1,000 Cr):**
  ```bash
  .venv/bin/python scripts/stage2_scanner.py --market IN --min-mcap 1000 --out data/views/stage2_IN_latest.json
  ```
- **For `US` ($\ge$ \$1.0B):**
  ```bash
  .venv/bin/python scripts/stage2_scanner.py --market US --min-mcap 1.0 --out data/views/stage2_US_latest.json
  ```
Copy `data/views/stage2_<MKT>_latest.json` to `<RUN_DIR>/cache/stage2_<MKT>_<date>.json`.

---

## 3. TradingView + Screener/Finviz Snapshot & Automatic Watchlist Pruning (`scripts/stock_snapshot.py`)

Run `scripts/stock_snapshot.py` across active watchlist, shortlist, holdings, and the top 10–15 fresh Stage 2 breakout symbols from Step 2:
```bash
.venv/bin/python scripts/stock_snapshot.py \
  --market <MKT> \
  --from-watchlist --from-shortlist --from-holdings \
  --symbols <TOP_STAGE2_SYMBOLS...> \
  --stage2-file data/views/stage2_<MKT>_latest.json \
  --prune-watchlist \
  --out "<RUN_DIR>/cache/snapshots_<MKT>_<date>.json"
```
This deterministically computes each symbol's Weinstein stage, extension from the 10-week EMA and 50-day SMA, RSI(14), support buy zone, invalidation stop, valuation assessment, and prunes any Stage 4 breakdowns from `data/watchlist/<MKT>.json`.

---

## 4. Fundamental & Catalyst Research Pass

Follow `.agents/skills/stage2_sector_momentum/SKILL.md`:
1. Initialize `<RUN_DIR>/cache/research_<MKT>_<date>.json` using `scripts/research_log.py init --market <MKT> --date <date> --out "<RUN_DIR>/cache/research_<MKT>_<date>.json"`.
2. Verify quarterly revenue/earnings growth, order-book / product catalysts, and balance sheet health for the top candidate setups via `search_web` and log each source with `scripts/research_log.py add`.

---

## 5. Watchlist Ingestion & Validation

1. Add the top 2–5 fresh, unowned Stage 2 breakout candidates into `data/watchlist/<MKT>.json` with all 9 required schema fields (`symbol`, `company_name`, `date_added`, `macro_sector`, `strategy_bucket`, `source_type`: `"STAGE2_BREAKOUT"`, `status`: `"RESEARCH_REQUIRED"`, `catalyst_timeline`, `summary_rationale`).
2. Validate JSON schemas:
   ```bash
   .venv/bin/python scripts/data_layer.py --market <MKT> --validate
   ```

---

## 6. Write, Assemble & Publish Report

1. Write `<RUN_DIR>/work/body.html` following `.agents/skills/stage2_sector_momentum/SKILL.md` and `.agents/skills/_shared/REPORT_DESIGN.md`.
2. Assemble into the stable report path (`docs/reports/<MKT>_Stage2_Sector_Momentum.html`):
   ```bash
   .venv/bin/python scripts/assemble_report.py \
     --body "<RUN_DIR>/work/body.html" \
     --out "docs/reports/<MKT>_Stage2_Sector_Momentum.html" \
     --market <MKT> \
     --research "<RUN_DIR>/cache/research_<MKT>_<date>.json" \
     --kind report \
     --workflow stage2_sector_momentum \
     --as-of <date>
   ```
3. Run the reviewer gate (`scripts/review_packet.py` + `report_reviewer`) per `_COMMON.md` §3b.
4. Publish via `scripts/publish_run.py` when authorized.
