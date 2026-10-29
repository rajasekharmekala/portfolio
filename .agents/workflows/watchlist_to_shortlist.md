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
3. Claim the next batch of up to 4 eligible symbols:
   ```bash
   .venv/bin/python scripts/run_claims.py batch --workflow watchlist_to_shortlist --market <MKT> --run-id <run_id> --size 4
   ```
   Ensure the claimed batch symbols are included in `<RUN_DIR>/cache/snapshots_<MKT>_<date>.json` (re-run `stock_snapshot.py --symbols ...` if needed).

## 2. Dedicated Per-Company Deep Business-Monograph Dossiers

Spawn **1 dedicated subagent per company** (`invoke_subagent`) for each symbol in the batch:
- Each subagent reads its symbol's TradingView + Screener.in/Finviz + TheWrap Stage 2 snapshot from `<RUN_DIR>/cache/snapshots_<MKT>_<date>.json` and follows `.agents/skills/company_report/SKILL.md`.
- Each subagent writes and assembles `docs/blogs/<MKT>/<SYMBOL>_dossier.html` (`scripts/assemble_report.py --market <MKT> --kind dossier --workflow "Company research" --as-of <date>`) covering:
  1. What the company does & day-to-day operational processes across each business vertical.
  2. External learning hub (curated links to websites, YouTube videos/interviews/factory tours, investor presentations, and concalls).
  3. Core operational KPIs, moat, and business story.
  4. Management "Walk the Talk" audit (past guidance vs. delivered reality) and whether the company is reaching its potential.
  5. Financials & valuation sanity (Screener.in / Finviz).
  6. Stage 2 & TradingView technical structure (`30W SMA`, `10W EMA`, `50D/200D SMA`, `RSI-14`, volume, pivots).
  7. Multi-horizon view (Short-term momentum, Medium-term catalysts, Long-term compounding) and **No-FOMO Action Plan** (`IMMEDIATE_BUY` at CMP vs. `WAIT_FOR_SUPPORT` limit zone vs. `REJECTED`).

## 3. Shortlist & Watchlist Updates

1. Promote qualified candidates (`IMMEDIATE_BUY`, `ACCUMULATE_ON_DIP`, `WAIT_FOR_SUPPORT`) into `data/shortlist/<MKT>.json` with exact TradingView/Screener/Finviz metrics and support buy zones.
2. Move `REJECTED` candidates from `watchlist.active` to `watchlist.archive` in `data/watchlist/<MKT>.json` so the active watchlist remains focused.
3. Update completed status on surviving active rows and validate with `.venv/bin/python scripts/data_layer.py --market <MKT> --validate`.

## 4. Batch Report, Review Gate & Publication

1. Assemble `docs/reports/<MKT>_Watchlist_to_Shortlist.html` using `scripts/assemble_report.py --market <MKT> --kind report --workflow "Watchlist underwriting" --as-of <date>`.
2. Run the reviewer and red-team gate (`scripts/review_packet.py`, `report_reviewer`, `red_team`) on each dossier and the batch summary report.
3. Publish via `scripts/publish_run.py` (email delivery is disabled for `watchlist_to_shortlist`).
