---
description: Underwrites the next batch of watchlist names for one market (IN or US) through the shortlist underwriting skill, writes one dossier per name, updates the shortlist JSON record file, and delivers the batch summary.
---

# Watchlist to Shortlist Workflow (generic: IN or US)

Read `_COMMON.md` first.

**Input:** market `<MKT>`. The watchlist source and its shortlist are declared in `config/portfolios.json`. The batch size comes from the skill (`skills[watchlist_to_shortlist]`). Only names whose `Status` is `RESEARCH_REQUIRED` or `PENDING_RESEARCH` are eligible. Select them by header name.

## 1. Session date and run directory

As in `market_intelligence.md` §1–2.

## 2. Batch

Take the next batch of eligible names in watchlist order. Record the batch in `manifest.json`. Do not process a name twice in the same run.

## 3. Ledger and research

Build the ledger, as in the market intelligence workflow, so every name has its price and stage history from the same session. Research each name through the duck-duck-go MCP, following the underwriting skill, and record it in the research file.

## 4. Underwrite and write dossiers

Apply the underwriting skill to each name. Each name gets one dossier written in sections (`skills/_shared/SECTION_DRAFTING.md`). The output path for each dossier is `output.watchlist_to_shortlist` in `markets.json`, with `{symbol}` filled in. Each dossier passes the full validator and the reviewer gate before it is accepted.

## 5. Workbook updates

Update the watchlist and shortlist JSON record files with each name's verdict. Use header names, never column positions. A name that fails underwriting moves to the rejected list only as the skill describes.

## 6. Delivery and cleanup

Send one summary email for the batch, with the links to the dossiers. Clean up as in `_COMMON.md`.
