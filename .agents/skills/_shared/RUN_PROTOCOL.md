# Run Protocol (binding for every workflow and skill)

This protocol exists because earlier runs leaked state into later ones: prior-day ledgers, prior-day research,
and hardcoded dates produced reports that looked current but were not. These rules apply to every run.

## 7. Python environment (binding for every script invocation)

- Every Python command in this repository runs through the repository's own virtual environment: use `.venv/bin/python` from the repo root. Never use bare `python3`, `pip`, or a system/conda Python. Any command written as `python3 scripts/...` in a skill or shared document means `.venv/bin/python scripts/...`.
- If `.venv` is missing (e.g., after a fresh clone), recreate it before any other step: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`, then rerun the command.
- Do not add packages outside `requirements.txt` silently. If a script needs a new dependency, add it to `requirements.txt` and install it into `.venv`, and tell the user.

## 0. Report session date (binding for every skill and workflow)

Date every report and its data to the **latest completed market session**, not automatically to the calendar date on which the run starts. Resolve the session separately for the target exchange:

1. Check the exchange calendar and session hours for holidays, weekends, and whether today's session has actually closed (NSE/BSE: 15:30 IST; US exchanges: 16:00 ET, with a 30-minute data-publication allowance).
2. Use a session date only when the benchmark's final daily close for that date is present in the fresh data source. If today's session is not complete, use the previous completed session. After today's close, wait through the publication window in step 1 before deciding its bar is missing. Do not stamp a report with today's date merely because the run is happening today.
3. Build the ledger with that exact selected date and make it the report's date, filename date, research query date, and validator date. Never rename or relabel data to fit a desired date. Record both `run_date` and `session_date` in the manifest when they differ, and state the report's as-of session prominently.
4. If the latest exchange session has closed, its publication window has elapsed, and its final bar is still missing, retry once, then step back to the most recent earlier completed session whose benchmark close is verified and use that exact date. This is a data-availability fallback, not permission to relabel prices. Disclose the as-of date and delay in the report. Stop only if no recent completed session can be verified or the selected date fails the ledger freshness check.

## 1. Run directory (isolation)

Create a fresh, private directory at the start of every run. Never reuse one.

```bash
RUN_DIR="$(mktemp -d "${TMPDIR:-/tmp}/portfolio-<MKT>-<YYYY-MM-DD>-XXXX")"
mkdir -p "$RUN_DIR/cache" "$RUN_DIR/inputs" "$RUN_DIR/work"
```

- `<RUN_DIR>` is outside the repository. It is the only place for ledgers, research records, drafts, and scratch code.
- A run must never read from, or write derived output to, any other run directory.
- Pass `--run-dir "<RUN_DIR>"` to every `scripts/market_facts.py` build.

## 2. Inputs and manifest

- Copy the portfolio JSON record files needed for this run (holdings, watchlist, shortlist) into `<RUN_DIR>/inputs/` and record their SHA-256 in the manifest. Work from the copies, not the originals.
- Write `<RUN_DIR>/manifest.json` at start with: market, session date, start time (ISO 8601 with timezone), input file hashes, and the ledger and research paths. Update it with output paths and the validation result at the end.

## 3. What may carry over between runs

Only the user's own state may carry over: holdings, watchlist, shortlist, and option positions. These are read from the JSON record files in `sheets/`, `watchlist/`, and `shortlist/`.

These may NOT carry over: ledgers (`facts_*.json`), research records, prior report HTML, prior screen results, or any cached web result. Prior reports may be cited as history in a report, but never used as a data source for the current run.

## 4. Freshness

- The ledger's `asof` must equal the resolved latest completed session date under §0. `market_facts.py` exits non-zero if the benchmark's last bar is on another date. Do not rename, copy, or relabel a ledger. If the current calendar day's session is incomplete, resolve the prior session. If its completed close is missing, retry once, then use the most recent earlier completed session with a verified benchmark close. If that exact-date build fails, stop and report.
- Every web-sourced value needs `source_url`, `as_of` (the date the value describes), and `retrieved_at` (ISO 8601 time of retrieval). A value whose `as_of` is not the session date must be labeled as prior-session in the report.
- Never fall back to "latest file" lookup. Every file path is explicit.
- Never use the system date as a stand-in for the session date. Use the latest completed, data-verified market session (ET for US, IST for India), even when it is earlier than the run date.

## 5. Outputs and cleanup

- Only final artifacts leave the run: the report HTML, the updated watchlist/shortlist/holdings JSON record files, and the email. Everything else stays in `<RUN_DIR>`.
- After the validation gate passes and artifacts are saved, delete the run directory: `rm -rf "$RUN_DIR"`.
- If the run fails, keep `<RUN_DIR>` and report its path so the failure can be inspected. Do not delete it.

## 6. Publication (GitHub Pages)

- `docs/` holds only the latest published report for each report type and market, plus the index that links them. Publishing a new report overwrites the old file in `docs/reports/`. History is kept by git commits, not by files in the folder.
- Publication to this repository's GitHub Pages is mandatory for every completed report run. Do not ask for separate permission to publish, commit, or push; the user has authorized this repository's reports, including personal holdings, to be published publicly as part of the normal workflow.
- Publish only after the validator prints `RESULT: PASS` and the reviewer process is complete. Reviewer `APPROVE` is preferred. The strict maximum is four complete review rounds; after round 4, apply all evidence-backed fixes best-effort, rerun the validator, and record any remaining findings and the `BEST_EFFORT_AFTER_REVIEW_LIMIT` status in the manifest. Never launch a fifth round or call best-effort status APPROVE.
- Copy the final HTML into `docs/reports/` only after this gate. Keep exactly one latest report for each report type and market; remove the superseded page for that same type/market. Regenerate the indexes with `.venv/bin/python scripts/build_dossier_portal.py` and verify the published links are relative and point to existing files.
- Commit and push the publication automatically. Stage only the report files, superseded report deletion, generated indexes, and skill/workflow/config changes made for this run; never include unrelated working-tree changes. Use a descriptive commit message. Push to the configured `origin` branch. Never force-push. If the push is rejected, fetch and integrate the remote update safely, then retry once; if it still fails or conflicts, leave the local commit intact and report the exact blocker.
- Record the commit hash and push result in the manifest. The run is complete only after the push succeeds; then remove the run directory as specified above.
- `docs/` must contain only published reports and their index. Never copy JSON record files, ledgers, research files, fact packs, or `.env` into `docs/`.
- All links inside published pages must be relative. Do not embed absolute local paths such as `/Users/...` or `file://`.
