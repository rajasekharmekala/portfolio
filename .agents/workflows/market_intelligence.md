---
description: Daily market intelligence for one market (IN or US). Builds the facts ledger, runs the research pass, writes the report in sections, passes the validator and the reviewer gate, then delivers. Parameters come from config/markets.json.
---

# Market Intelligence Workflow (generic: IN or US)

Read `_COMMON.md` first. It sets the run directory, preflight, ledger, research, reviewer gate, delivery and cleanup rules that apply here.

**Input:** market `<MKT>` (`IN` or `US`). Everything else comes from `config/markets.json` (`markets.<MKT>`).

## 1. Session date

Run every time this workflow is invoked, including weekends, exchange holidays, closed-market days, and triggers that arrive later than usual. Do not impose a weekday, session-open, or time-of-day gate. Use the **latest completed market session with a verified final benchmark close**, not the calendar date of the run by default. Check the exchange calendar and local close time to resolve the data cutoff. For `US`, use the 30-minute publication allowance after the 16:00 ET close; for `IN`, use data after the 15:30 IST close. If today's session has not completed, use the previous completed session. If its bar remains missing after the publication allowance, retry once and then step back to the most recent earlier completed session whose final benchmark bar is verified. Use that exact date for the ledger, report title, research queries and validator. Record the separate run date and session date when they differ. At the top of the report, prominently state the verified session date and, if different from the run date, why: a weekend, holiday, incomplete session, or delayed benchmark data. Disclose a data delay only when data is actually delayed; a normal market closure is not a data failure. Stop only if no completed session can be verified or the exact-date ledger still fails; never invent or relabel a date.

## 2. Run directory and preflight

Follow `_COMMON.md`: start the run session first (`run_session.py start --workflow market_intelligence --market <MKT>`; refused if another market intelligence run for this market is live), work in its worktree, then create the run directory, check inputs, read `.env`.

## 3. Facts ledger

Build the ledger with `ledger_screen` from `markets.<MKT>`. Check the output: `regime.label`, `failures`, `freshness`. Record the regime label verbatim. Do not re-derive any number by hand.

## 4. Research pass

Work through the ledger's `research_needs` for the market (`research_key` in `markets.json`), using the duck-duck-go MCP as `_COMMON.md` describes. Record results in the research file.

## 4A. Integrated Stage 2 sector and stock scan (IN and US)

Run `stage2_scanner.py` once for the target market and write its fresh result to `<RUN_DIR>/cache/stage2_<MKT>_<date>.json` (IN minimum market cap ₹1,000 Cr; US minimum market cap $1.0B). Independently verify dashboard date, coverage, and filters. Then run:

```bash
.venv/bin/python scripts/stock_snapshot.py \
  --market <MKT> \
  --from-watchlist --from-shortlist --from-holdings --from-stage2-archive \
  --stage2-file "<RUN_DIR>/cache/stage2_<MKT>_<date>.json" \
  --prune-watchlist --resurface-stage2-archive --as-of <date> \
  --out "<RUN_DIR>/cache/snapshots_<MKT>_<date>.json"
```

The archive scan snapshots only archived symbols present in current dashboard candidates; it returns one to active research only when the fresh dashboard signal and TradingView Stage 2 structure agree and the 25-name active cap has room. Apply market-specific breadth rules and the No-FOMO entry gate; research the report's selected setups. The integrated results become Section 2A and feed the market playbook and watchlist ingestion. This is a single report and review cycle for the scan.

## 5. Story brief

Write the private story brief (6–8 bullets) as `<RUN_DIR>/work/brief.md`, following the market intelligence skill (`skills[market_intelligence]`). Every section must serve it.

## 6. Plan and draft in sections

Follow `skills/_shared/SECTION_DRAFTING.md`. Build `<RUN_DIR>/work/plan.json` from the blueprint table 7A in `REPORT_EDITORIAL_STANDARD.md`. Draft each section from its fact-pack entries, its research entries, the brief bullets for it, and the voice and palette guides. Run the partial validator after each section.

The writing rules for the skill (`skills[market_intelligence]`) apply to every section.

## 7. Assemble and gate

Assemble `<RUN_DIR>/report.html`, then run the full validator:

`.venv/bin/python scripts/validate_report.py --report "<RUN_DIR>/report.html" --kind market_intel --facts "<RUN_DIR>/cache/facts_<MKT>_<date>.json"`

It must print `RESULT: PASS`.

## 8. Watchlist ingestion

Update the watchlist JSON record file for this market with names allowed by the market-intelligence skill. Include only independently verified fresh Stage 2 candidates named in Section 2A.4 (2–5 maximum, 25-name cap); returning archived names must be explicitly named as rediscoveries. Use header names to find columns. Do not add a name the report does not name in its ingestion section.

## 9. Reviewer gate and delivery

Follow `_COMMON.md`, including its strict two-round maximum, best-effort finalization after round 2, and mandatory GitHub Pages publication with automatic commit and push. The report file name is `output.market_intelligence` in `markets.json`, filled with the session date.

## 10. Cleanup

Follow `_COMMON.md`.
