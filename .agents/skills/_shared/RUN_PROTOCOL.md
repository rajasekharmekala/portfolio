# Run Protocol (binding for every workflow and skill)

## Report Design (Binding)

Read REPORT_DESIGN.md for every new report and dossier. Assemble the full research body through scripts/assemble_report.py with --market, --kind, --workflow and --as-of. Older Wikipedia HTML head/style examples in skills are obsolete presentation templates; preserve their analysis requirements, not their page shell. Generation time belongs in the Pacific header, separate from the verified session cutoff. New workflow output filenames are stable as specified in REPORT_DESIGN.md; this supersedes dated published-output naming instructions only. Evidence files and freshness checks remain session-dated. Newly completed publication rejects old-style output. All citations, references and quality gates remain mandatory.

This protocol exists because earlier runs leaked state into later ones: prior-day ledgers, prior-day research,
and hardcoded dates produced reports that looked current but were not. These rules apply to every run.

## 7. Python environment (binding for every script invocation)

- Every Python command in this repository runs through the repository's own virtual environment: use `.venv/bin/python` from the repo root. Never use bare `python3`, `pip`, or a system/conda Python. Any command written as `python3 scripts/...` in a skill or shared document means `.venv/bin/python scripts/...`.
- If `.venv` is missing (e.g., after a fresh clone), recreate it before any other step: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`, then rerun the command.
- Do not add packages outside `requirements.txt` silently. If a script needs a new dependency, add it to `requirements.txt` and install it into `.venv`, and tell the user.

## 8. Concurrent runs (binding)

Several runs, of the same or different workflows, may be active at once and all publish to `main`. Four mechanisms keep them apart:

1. **One worktree per run.** `scripts/run_session.py start --workflow <w> --market <MKT>` creates `.worktrees/<run_id>` on branch `run/<run_id>` from freshly fetched `origin/main`. Every command and file edit of the run happens there. Never edit, merge, pull or check out in the shared main checkout, and never touch another run's worktree or untracked files.
2. **Singleton claim.** `market_intelligence`, `portfolio_audit`, `options_audit` and `displacement` allow one live run per market. If `start` is refused (exit 3), stop and tell the user which run holds it; do not wait, retry in a loop or bypass the claim.
3. **Name claims.** `watchlist_to_shortlist`, `reject_to_watchlist` and `company_report` take their companies with `scripts/run_claims.py batch --workflow <w> --market <MKT> --run-id <id> --size <N> [--pool archive]` (or `names SYMBOL...`) from inside the worktree. A company held by another live run is skipped, whichever workflow holds it; a short batch is processed and disclosed, never widened. Work only on the printed symbols, and record them with the claim output in the manifest. For runs longer than the claim TTL (6 hours) renew with `run_claims.py heartbeat --run-id <id>`.
4. **Merge-aware publish.** `scripts/publish_run.py` (see §6) is the only way a run reaches `origin/main`.

Failure handling: a run that stops keeps its worktree, branch and claims; the claims expire by TTL or are released with `run_session.py finish --run-id <id> --keep-worktree`. `run_claims.py list` shows what is held.

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
- **Holdings accuracy assumption:** The user's holdings transaction log is the authoritative record and is assumed accurate. Always pass `--allow-stale-holdings` to `market_facts.py`; a `HOLDINGS NOT CURRENT` freshness-metadata warning is not a run blocker. Record the warning and assumption in the manifest and disclose them in the report. This does not waive input readability/schema checks or the market-price ledger freshness requirements above.
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
- Publish only after the validator and reviewer process are complete. `RESULT: PASS` and reviewer `APPROVE` are preferred. The strict maximum is two complete review rounds; after round 2, apply all evidence-backed fixes best-effort, rerun the validator, and record any remaining findings and the `BEST_EFFORT_AFTER_REVIEW_LIMIT` status in the manifest. Never launch a third round or call best-effort status APPROVE. A gate that the existing evidence cannot satisfy (for example a stale `as_of` with no newer filing, or an unavailable reviewer model) does not block publication: record it, disclose it in the report's `gate-exceptions` section, and publish with status `PUBLISHED_WITH_GATE_EXCEPTIONS` under `../../workflows/_COMMON.md`, "Gate exceptions and mandatory publication".
- Copy the final HTML into `docs/reports/` only after this gate. Keep exactly one latest report for each report type and market; remove the superseded page for that same type/market. Regenerate the indexes with `.venv/bin/python scripts/build_dossier_portal.py` and verify the published links are relative and point to existing files.
- Commit and push the publication automatically through `scripts/publish_run.py` from the run's worktree (§8); never commit or push by hand and never from the shared checkout. It stages only `docs/`, `data/`, `.agents/` and `scripts/` changes, uses your descriptive commit message, pushes as a fast-forward and never forces. A rejected push is retried automatically on the newer `origin/main`; if it still fails or conflicts, the run branch stays intact and you report the exact blocker.
- A later run may replace an earlier published output only under the override rules in `.agents/workflows/_COMMON.md` ("Overriding earlier publications"): same or later session date and later `generated-at`. `publish_run.py` enforces this and merges record files symbol by symbol on the freshly fetched files; never copy an older record file over a newer one.
- Record the commit hash, the push result and any superseded commit hash in the manifest (`--manifest` does it). The run is complete only after the push succeeds; then remove the run directory and finish the run session as specified above.
- `docs/` contains published reports, the stable homepage and its JavaScript/CSS assets, and only two public metadata JSON files: `portal-data.json` and `portal-updates.json`. These contain published paths, titles, timestamps, short decision summaries and highlights. Never copy private JSON record files, ledgers, research files, fact packs, or `.env` into `docs/`.
- After the publication gates, `publish_run.py` runs the equivalent of `.venv/bin/python scripts/build_dossier_portal.py --completed "<published HTML paths>" --workflow "<stable workflow name>" --market "<IN or US>" --summary "<decision overview>" --highlight "<key change>" --repair-links` to stamp completion and refresh public metadata. Pass multiple paths as separate arguments to `--completed`; stage both catalog JSON files with the report. Routine rebuilds preserve prior completion times. Failed runs must not be marked completed.
- All links inside published pages must be relative. Do not embed absolute local paths such as `/Users/...` or `file://`. Email delivery converts valid local links to absolute URLs under `https://rajasekharmekala.github.io/portfolio/`; missing or unpublished destinations are made non-clickable rather than inventing URLs.

## Email Notification Policy

Apply `_COMMON.md` email policy after successful GitHub Pages publication/push. Market intelligence and portfolio audits always receive short digest emails. Watchlist-to-shortlist, archive resurrection and displacement runs receive email only for a newly verified shortlist qualification or newly eligible displacement of an actual holding, compared with frozen starting state. Archive-to-watchlist moves, existing shortlist members, unchanged displacement eligibility and failed gates remain silent. Skipping email does not skip report publication. Pass verified `--shortlisted` / `--displacement` events plus `--report-type`, `--summary`, and `--highlight` to `scripts/send_email.py`; never email the full report. Record sent/skipped/failed status and eligibility evidence in the manifest. Emails link to the published HTML report, not a local draft or Markdown memo.
