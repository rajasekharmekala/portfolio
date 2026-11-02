---
description: Stan Weinstein Stage 2 sector rotation, TradingView technicals, and valuation scanner for one market (IN or US). Extracts TheWrap PowerBI data via Chrome automation, enriches with TradingView & Screener.in/Finviz snapshots, prunes Stage 4 dead weight from the watchlist, and ingests fresh Stage 2 breakouts.
---

# Stage 2 Sector Momentum Workflow (Market: `<MKT>`)

Read `_COMMON.md` first. Choose `<MKT>` = `IN` or `US` and look up its row in `.agents/config/markets.json`.

**Execution timing:** Run whenever this workflow is invoked, including weekends, exchange holidays, closed-market days, and triggers that arrive earlier or later than usual. This workflow has no time-of-day or market-open window. Resolve the latest completed session for market data, then verify TheWrap's dashboard date and freshness independently; an unchanged weekly India dashboard is not a new scan.

---

## 1. Run Directory and Preflight

1. Start the isolated run worktree and singleton claim per `_COMMON.md`:
   ```bash
   .venv/bin/python scripts/run_session.py start --workflow stage2_sector_momentum --market <MKT>
   ```
   Work only in the printed `worktree`; create a private `RUN_DIR` per RUN_PROTOCOL §1.
2. Resolve the latest completed exchange session and verify its final benchmark close per `_COMMON.md` preflight and ledger rules, including the retry and fallback. Run the input check and build the ledger for that exact session. Record the run date and session date separately in the manifest; do not infer the session from the current date or assume weekends cannot have special sessions. A closed market or late trigger does not cancel this workflow.
3. Verify Google Chrome is running with Apple Events JavaScript enabled (`View > Developer > Allow JavaScript from Apple Events`). If browser extraction is unavailable, make the required best effort with independently verifiable current inputs and disclose missing data; never reuse a prior run's cached scan or invent a figure. A missing required input or other `_COMMON.md` hard stop remains a blocker.

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
Copy the freshly extracted output to `<RUN_DIR>/cache/stage2_<MKT>_<date>.json`. For India, use an owned dashboard tab with category slicers cleared, verify the cap filter, and check `sector_chart_complete` and `stage2_universe_complete` against the dashboard summary; disclose incomplete coverage rather than calling it a full ranking. Never read selections from another run's or the user's dashboard tab. Verify and record the dashboard's actual data date, retrieval time, and freshness separately from the market-session date. If its date cannot be verified, mark it unknown rather than assuming the retrieval or session date. An unchanged weekly dashboard is historical evidence, not a new scan or newly discovered breakout; identify it as such and do not manufacture watchlist additions. If the dashboard is stale, disclose its date and limitations, use independently verified current data where available, and apply the common hard-stop and gate-exception rules rather than silently presenting stale values as current.

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
1. Create `<RUN_DIR>/cache/research_<MKT>_<date>.json` in the format of `.agents/skills/_shared/RESEARCH_CONTRACT.md`, with a fresh fetch cache in the run directory. Do not use a prior run's research or cached pages.
2. Verify quarterly revenue/earnings growth, order-book / product catalysts, and balance sheet health for the top candidate setups using the research sources required by `_COMMON.md`. Record each claim and fetched source under the research contract; check citations against that run's cache.

---

## 5. Watchlist Ingestion & Validation

1. Add up to 2–5 independently verified fresh, unowned Stage 2 breakout candidates into `data/watchlist/<MKT>.json` with all 9 required schema fields (`symbol`, `company_name`, `date_added`, `macro_sector`, `strategy_bucket`, `source_type`: `"STAGE2_BREAKOUT"`, `status`: `"RESEARCH_REQUIRED"`, `catalyst_timeline`, `summary_rationale`). If no fresh breakout is supported, add none and explain why.
2. Validate JSON schemas:
   ```bash
   .venv/bin/python scripts/data_layer.py --market <MKT> --validate
   ```

---

## 6. Write, Assemble & Publish Report

1. Write `<RUN_DIR>/work/body.html` following `.agents/skills/stage2_sector_momentum/SKILL.md` and `.agents/skills/_shared/REPORT_DESIGN.md`. At the top, prominently state the verified market-session date, the local run date and why they differ when applicable; a normal weekend or holiday is not a data failure. Separately state the dashboard's actual data date or unknown status and its freshness. Label all older or unavailable inputs accurately.
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
3. Run the full Stage 2 validator with the explicit run files; do not use market-intelligence or portfolio-audit report requirements as a substitute:
   ```bash
   .venv/bin/python scripts/validate_report.py --report "docs/reports/<MKT>_Stage2_Sector_Momentum.html" --kind stage2_sector_momentum --facts "<RUN_DIR>/cache/facts_<MKT>_<date>.json" --research "<RUN_DIR>/cache/research_<MKT>_<date>.json" --snapshots "<RUN_DIR>/cache/snapshots_<MKT>_<date>.json" --stage2-file "<RUN_DIR>/cache/stage2_<MKT>_<date>.json"
   ```
   Run the citation check with the run's fetch-cache path and the report's 12-source floor; use `--allow-stale-asof` only when its exceptions are valid and disclosed per `_COMMON.md`. Run `scripts/readability_check.py --kind stage2_sector_momentum` and the Research Desk layout check. The readability gate checks prose, tables and banned text without demanding dossier-only primer or chapter-7 sections. Fix failures and record any allowed residual exceptions; do not bypass checks.
4. Build the review packet using `--kind stage2_sector_momentum`, the same explicit facts, research, snapshots and dashboard paths, and the run's `--cache-dir`. Run and check the reviewer gate per `_COMMON.md`; follow the configured model and two-round limit.
5. Publish via `scripts/publish_run.py` after the required checks and review process, per `_COMMON.md`. Apply the email policy and cleanup only after publication.
