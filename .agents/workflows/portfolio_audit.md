---
description: Portfolio audit for one market (IN or US) across all declared accounts. Reconciles holdings, shortlist and watchlist against the same-session ledger, writes the audit in sections, passes the validator and reviewer gate, then delivers.
---

# Portfolio Audit Workflow (generic: IN or US)

Read `_COMMON.md` first.

**Input:** market `<MKT>`. Accounts come from `config/portfolios.json` (every source whose role is `holding`). Parameters come from `config/markets.json`.

## 1. Session date and run directory

Start the run session first (`_COMMON.md`, "Run session"): `run_session.py start --workflow portfolio_audit --market <MKT>`. It is refused while another portfolio audit for this market is live; stop and report the holder. Work only in the printed worktree.

As in `market_intelligence.md` §1–2: the report date is the latest completed session with a verified benchmark close, which can be earlier than the run's calendar date. Use that same resolved date throughout the audit, including the sibling-report lookup.

## 2. Accounts and holdings

Run the input check. The manifest lists every holding source with its row count and hash. Positions that appear in more than one account are summed by the run and listed with their account split. Report the account split in the methodology note. For US, the consolidated snapshot (`cache/positions_US_<date>.json`) is the record of truth; see `../skills/_shared/HOLDINGS_UPDATE.md`.

## 3. Ledger & Stage 2 Consumer-Tool Snapshots

1. Build the ledger for this market and session:
   ```bash
   .venv/bin/python scripts/market_facts.py --market <MKT> --date <session> --screen <screen> --run-dir "<RUN_DIR>" --allow-stale-holdings
   ```
2. Enrich all held and shortlisted symbols with live TradingView technicals (30W SMA, 10W EMA, 20/50/200-DMA, RSI-14, volume ratios, classic pivots), Screener.in / Finviz valuation cards, and TheWrap Stage 2 sector/stock breadth:
   ```bash
   .venv/bin/python scripts/stock_snapshot.py \
     --market <MKT> \
     --from-holdings --from-shortlist \
     --stage2-file data/views/stage2_<MKT>_latest.json \
     --out "<RUN_DIR>/cache/snapshots_<MKT>_<date>.json"
   ```
3. Treat the user's transaction log as the authoritative and accurate holdings record. Always build with `--allow-stale-holdings`; a `HOLDINGS NOT CURRENT` freshness-metadata warning does not stop the audit. Record the warning and this assumption in the manifest and explain it in the methodology note.

## 4. Research and story brief

Research the held and shortlisted names that the ledger's `research_needs` flag. Record results in the research file. Write the brief at `<RUN_DIR>/work/brief.md`, following the audit skill.

## 5. Plan and draft in sections

Follow `skills/_shared/SECTION_DRAFTING.md` with blueprint 7B from `REPORT_EDITORIAL_STANDARD.md`. Each holding and each position needs its own case note. Each section gets only the fact-pack names it covers.

## 6. Assemble and gate

Assemble `<RUN_DIR>/report.html`, then run the full validator with `--kind portfolio_audit` and `--facts` pointing to the ledger. It must print `RESULT: PASS`.

## 7. Orders and JSON record files

Chapter 6 orders are exactly the deltas in Chapter 5. Update the holdings and shortlist JSON record files for this market only with changes the audit approves, and only through header-name lookup.

## 8. Reviewer gate and delivery

Follow `_COMMON.md`, including its strict two-round maximum, best-effort finalization after round 2, and mandatory GitHub Pages publication with automatic commit and push. The report file name is `output.portfolio_audit` in `markets.json`.

## 9. Cleanup

Follow `_COMMON.md`.
