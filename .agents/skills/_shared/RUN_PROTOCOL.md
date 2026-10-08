# Run Protocol (binding for every workflow and skill)

This protocol exists because earlier runs leaked state into later ones: prior-day ledgers, prior-day research,
and hardcoded dates produced reports that looked current but were not. These rules apply to every run.

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
- Publish only a report that has passed both the validator (`RESULT: PASS`) and the reviewer gate (`APPROVE`). Copy the HTML into `docs/reports/` under its report name, and regenerate `docs/index.html` from the files that are present.
- Publication is committed by the user. The run stages the files and reports the commit command; it does not commit or push.
- Reports contain personal holdings. Publish only to a private repository, or only after the user has explicitly approved public publication for that repository.
- `docs/` must contain only published reports and their index. Never copy JSON record files, ledgers, research files, fact packs, or `.env` into `docs/`.
- All links inside published pages must be relative. Do not embed absolute local paths such as `/Users/...` or `file://`.
