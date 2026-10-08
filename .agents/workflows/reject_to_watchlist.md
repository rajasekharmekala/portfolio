---
description: Archive resurrection review for one market (IN or US). Re-examines the next batch of rejected names against current data, moves any that now pass back to the watchlist, and delivers the review report.
---

# Archive Resurrection Review Workflow (generic: IN or US)

Read `_COMMON.md` first.

**Input:** market `<MKT>`. The archive is the `watchlist.archive` array of the market's watchlist JSON record file (declared in `config/portfolios.json`). Select names by header name. The batch size comes from the skill (`skills[reject_to_watchlist]`).

## 1. Session date and run directory

As in `market_intelligence.md` §1–2.

## 2. Batch

Take the next batch of archived names in archive order. Record the batch in `manifest.json`.

## 3. Ledger and research

Build the ledger so that current price and stage are from the same session. Research each name's current fundamentals and technical posture through the duck-duck-go MCP, and record the results.

## 4. Resurrection test

Apply the archive resurrection skill (`skills[reject_to_watchlist]`) to each name. A name moves back to the watchlist only when the skill's test passes on current data. A name that still fails stays in the archive, with the reason recorded.

## 5. Report and delivery

Write the review in sections (`skills/_shared/SECTION_DRAFTING.md`). The report file name is `output.reject_to_watchlist` in `markets.json`. Run the validator, the reviewer gate, and deliver, as in `_COMMON.md`.

## 6. Workbook updates

Move the names that pass to the watchlist, and leave the rest in the archive. Use header names only.
