---
description: Underwrites the next batch of watchlist names for one market (IN or US) using Stage 2 sector momentum, TradingView + Screener/Finviz snapshots, and No-FOMO support entry rules; prunes broken Stage 4 leads from the watchlist; writes a deep business-monograph dossier per company; and updates the shortlist and watchlist JSON files.
---

# Watchlist to Shortlist Workflow (Market: `<MKT>`)

Read `_COMMON.md` first.

**Input:** market `<MKT>` (`IN` or `US`). Follow `.agents/skills/watchlist_shortlist_underwriting/SKILL.md`.

## 1. Session Date, Run Worktree & Batch Claim

1. Start the isolated run session per `_COMMON.md`:
   ```bash
   .venv/bin/python scripts/run_session.py start --workflow watchlist_to_shortlist --market <MKT>
   ```
2. Refresh consumer-tool snapshots and prune broken Stage 4 / rejected names from `data/watchlist/<MKT>.json`:
   ```bash
   .venv/bin/python scripts/stock_snapshot.py \
     --market <MKT> \
     --from-watchlist --from-shortlist \
     --stage2-file data/views/stage2_<MKT>_latest.json \
     --prune-watchlist \
     --out "<RUN_DIR>/cache/snapshots_<MKT>_<date>.json"
   ```
3. Claim the next single eligible candidate (`--size 1` for deep, thorough underwriting):
   ```bash
   .venv/bin/python scripts/run_claims.py batch --workflow watchlist_to_shortlist --market <MKT> --run-id <run_id> --size 1
   ```
   Ensure the claimed symbol is included in `<RUN_DIR>/cache/snapshots_<MKT>_<date>.json` (re-run `stock_snapshot.py --symbols ...` if needed).

## 2. Dedicated Single-Company Deep Business-Monograph Dossier

Dedicate the full research budget, browser tooling, and multi-stage verification to **one company**:
- Read the candidate's TradingView + Screener.in/Finviz + TheWrap Stage 2 snapshot from `<RUN_DIR>/cache/snapshots_<MKT>_<date>.json` and follow `.agents/skills/company_report/SKILL.md`.
- Run the 4-loop persistent agentic research workflow:
  1. **Loop 1 (Quantitative Ground Truth):** Verify TradingView indicators (30W SMA, 10W EMA, 50D/200D SMA, RSI-14, volume, classic pivots) and valuation metrics (P/E, EV/Sales, ROIC/ROCE, Net Cash/Debt).
  2. **Loop 2 (Operational Forensics & Concall Ingestion):** Ingest recent earnings call transcripts and primary SEC 10-K/10-Q / BSE filings; extract at least 2 verified management quotes (CEO on product/demand, CFO on margins/guidance); analyze business verticals, unit economics, customer concentration, and true operational KPIs.
  3. **Loop 3 (Valuation Modeling & No-FOMO Execution):** Build multi-scenario valuation models (Bull/Base/Bear) and define explicit limit-order entry zones (`20D EMA / 10W EMA / 50D SMA`), invalidation stops, and catalyst event management.
  4. **Loop 4 (Interactive Dossier Assembly):** Render `docs/blogs/<MKT>/<SYMBOL>_dossier.html` with an embedded interactive TradingView chart widget, rich external learning hub links, and institutional voice (free of robotic phrasing or fake filler text).
- Assemble using `scripts/assemble_report.py --market <MKT> --kind dossier --workflow "Company research" --as-of <date>`.

## 3. Shortlist & Watchlist Updates

1. Promote qualified candidates (`IMMEDIATE_BUY`, `ACCUMULATE_ON_DIP`, `WAIT_FOR_SUPPORT`) into `data/shortlist/<MKT>.json` with exact TradingView/Screener/Finviz metrics and support buy zones.
2. Move `REJECTED` candidates from `watchlist.active` to `watchlist.archive` in `data/watchlist/<MKT>.json` so the active watchlist remains focused.
3. Update completed status on surviving active rows and validate with `.venv/bin/python scripts/data_layer.py --market <MKT> --validate`.

## 4. Batch Report, Review Gate & Publication

1. Assemble `docs/reports/<MKT>_Watchlist_to_Shortlist.html` using `scripts/assemble_report.py --market <MKT> --kind report --workflow "Watchlist underwriting" --as-of <date>`.
2. Run the reviewer and red-team gate (`scripts/review_packet.py`, `report_reviewer`, `red_team`) on each dossier and the batch summary report.
3. Publish via `scripts/publish_run.py` (email delivery is disabled for `watchlist_to_shortlist`).
