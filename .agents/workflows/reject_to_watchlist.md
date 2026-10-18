---
description: Archive resurrection review for one market (IN or US). Re-examines the next batch of rejected names against current data, moves any that now pass back to the watchlist, and delivers the review report.
---

# Archive Resurrection Review Workflow (generic: IN or US)

Read `_COMMON.md` first.

**Input:** market `<MKT>`. The archive is the `watchlist.archive` array of the market's watchlist JSON record file (declared in `config/portfolios.json`). Select names by header name. The batch size comes from the skill (`skills[reject_to_watchlist]`).

## 1. Session date and run directory

As in `market_intelligence.md` §1–2. Date the review and its market facts to the latest completed session with a verified benchmark close, not automatically to the run date.

## 2. Batch

Start the run session (`run_session.py start --workflow reject_to_watchlist --market <MKT>`), then claim the batch from inside the worktree: `.venv/bin/python scripts/run_claims.py batch --workflow reject_to_watchlist --market <MKT> --run-id <run_id> --pool archive --size <skill batch size>`. It returns the next archived names in archive order that no other live run holds. Work on exactly those names, and record the batch, the claim output and `base_commit` in `manifest.json`.

## 3. Ledger and research

Build the ledger so that current price and stage are from the same session. Research each name's current fundamentals and technical posture through the duck-duck-go MCP, and record the results.

## 4. Resurrection test

Apply the archive resurrection skill (`skills[reject_to_watchlist]`) to each name. A name moves back to the watchlist only when the skill's test passes on current data. A name that still fails stays in the archive, with the reason recorded.

## 5. Report and delivery

Write the review in sections (`skills/_shared/SECTION_DRAFTING.md`). The report file name is `output.reject_to_watchlist` in `markets.json`. Run the validator and reviewer process as in `_COMMON.md`; the reviewer cap is two rounds, followed by best-effort fixes and validator pass without a third review. Delivery includes mandatory GitHub Pages publication, index regeneration, and automatic commit and push.

## 6. Workbook updates

Move the names that pass to the watchlist, and leave the rest in the archive. Use header names only.

## Email Delivery Policy

Do not email routine archive resurrection reports or archive-to-watchlist promotions. Always publish the validated report and refresh the homepage catalog as `_COMMON.md` requires. Send only if this run also completes full underwriting and a company newly qualifies for the shortlist, or a shortlisted candidate newly passes all displacement gates against an actual current holding. Compare against the frozen starting state and retain evidence in the manifest; unchanged eligibility is not a new alert. After successful publication, use `--report-type archive` with verified `--shortlisted SYMBOL` or `--displacement "CANDIDATE replaces HOLDING: gate evidence"` flags, a short summary and highlights. Never email the full report. Without qualifying events, record email as intentionally skipped and complete normal publication/cleanup.
