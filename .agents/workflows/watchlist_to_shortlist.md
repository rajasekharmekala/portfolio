---
description: Underwrites the next batch of watchlist names for one market (IN or US) through the shortlist underwriting skill, writes one dossier per name, updates the shortlist JSON record file, and delivers the batch summary.
---

# Watchlist to Shortlist Workflow (generic: IN or US)

Read `_COMMON.md` first.

**Input:** market `<MKT>`. The watchlist source and its shortlist are declared in `config/portfolios.json`. The batch size comes from the skill (`skills[watchlist_to_shortlist]`). Only names whose `Status` is `RESEARCH_REQUIRED` or `PENDING_RESEARCH` are eligible. Select them by header name.

## 1. Session date and run directory

As in `market_intelligence.md` §1–2. Date technical facts and dossier as-of statements to the latest completed session with a verified benchmark close, not automatically to the run date.

## 2. Batch

Start the run session (`run_session.py start --workflow watchlist_to_shortlist --market <MKT>`), then claim the batch from inside the worktree: `.venv/bin/python scripts/run_claims.py batch --workflow watchlist_to_shortlist --market <MKT> --run-id <run_id> --size <skill batch size>`. It returns the next eligible names in watchlist order, read from freshly fetched `origin/main`, skipping names completed on origin and names claimed by any other live run, so two runs never work on the same company. Work on exactly the returned `symbols`; if `short_batch` is true, process those and disclose the short batch in the summary report; never widen eligibility to fill it. Record the batch, the claim output and `base_commit` in `manifest.json`. Do not process a name twice in the same run. Rerunning the command for the same run id returns the same names.

## 3. Ledger and research

Build the ledger, as in the market intelligence workflow, so every name has its price and stage history from the same session. Research each name through the duck-duck-go MCP, following the underwriting skill, and record it in the research file.

## 4. Underwrite and write dossiers

Apply the underwriting skill to each name. Each name gets one dossier written in sections (`skills/_shared/SECTION_DRAFTING.md`). The output path for each dossier is `output.watchlist_to_shortlist` in `markets.json`, with `{symbol}` filled in. Each dossier must pass the full validator and complete up to two reviewer rounds. If round 2 is still REVISE or BLOCK, make the remaining evidence-backed fixes best-effort, rerun the validator, and record unresolved findings; do not start a third review. Gates the existing evidence cannot satisfy (above all the 60-day `as_of` check when the latest quarterly filing is older than 60 days) are exceptions under `_COMMON.md`, "Gate exceptions and mandatory publication": run `citation_check.py` with `--allow-stale-asof`, put a `gate-exceptions` section in every dossier and in the batch summary report, and publish. A dossier is never withheld for an excepted gate.

## 5. Workbook updates

Update the watchlist and shortlist JSON record files with each name's verdict. Use header names, never column positions. A name that fails underwriting moves to the rejected list only as the skill describes.

## 6. Delivery and cleanup

Publish every validated batch and its dossier updates to GitHub Pages, refreshing the catalog and committing/pushing as `_COMMON.md` requires. Before committing, apply the "Overriding earlier publications" rules in `_COMMON.md`: a dossier or record from an earlier run is replaced only by a fresher or equal-session run that was generated later, and the superseded commit is recorded. Re-read origin's record files and rebuild the record edits on them before the push. Do not send routine batch emails. Compare final validated decisions against the frozen starting watchlist/shortlist: send one short digest only if at least one company newly qualifies for the shortlist or a shortlisted candidate newly passes the displacement gates against an actual current holding. Use `--report-type watchlist`, `--shortlisted SYMBOL` for each new qualification, and `--displacement "CANDIDATE replaces HOLDING: gate evidence"` for each newly eligible replacement. Unchanged shortlist members, tentative candidates and failed gates are not alert events. Email only after successful publication, with a summary, highlights and the published full-report link. Record sent/skipped status and evidence in the manifest. Clean up as `_COMMON.md` specifies.
