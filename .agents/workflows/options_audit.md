---
description: Options position audit and setup structuring for one market (IN or US). Audits every open options position against the options skill's action matrix, screens the shortlist for setups, then passes the validator and reviewer gate before delivery.
---

# Options Audit Workflow (generic: IN or US)

Read `_COMMON.md` first.

**Input:** market `<MKT>`. The positions file is `data/options/<MKT>.json`. Its book sheets (for IN and US) have title rows above the table, so locate the header row by its header names (`Symbol` or `Underlying`, plus the expiry and strike columns) and stop if none is found. Do not assume a row number.

## 1. Session date and run directory

As in `market_intelligence.md` §1–2. The options report uses the latest completed, data-verified exchange session date, even when that date precedes the run date.

## 2. Positions

Read every open position from the market's book sheet. Record each position's row, header names used, and count in `manifest.json`. Positions that are expired or closed are not audited.

## 3. Ledger and volatility inputs

Build the ledger as in the market intelligence workflow. For each underlying, the options skill (`skills[options]`) defines the volatility inputs it needs. Source them from the ledger and the research record only.

## 4. Audit and setups

Apply the options skill to each position and to each setup it screens from the shortlist. Each verdict names its rule and the level that would change it.

## 5. Report

Write the report in sections using `skills/_shared/SECTION_DRAFTING.md`. Each position gets a case note. The report file name is `output.options` in `markets.json`.

## 6. Gate, reviewer, delivery, cleanup

Assemble, run the full validator with `--kind portfolio_audit` (options reports use the audit floors), run up to two reviewer rounds, then follow `_COMMON.md` best-effort finalization if round 2 is not approved. Delivery includes mandatory GitHub Pages publication, index regeneration, and automatic commit and push; then clean up as specified there.
