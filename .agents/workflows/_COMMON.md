# Common Workflow Rules (read by every workflow)

Every workflow takes a market (`IN` or `US`) and reads its parameters from `../config/markets.json` and its sources from `../config/portfolios.json`. Nothing market-specific is written into a workflow.

## Governing documents (binding)

- `../skills/_shared/RUN_PROTOCOL.md`: run directory, freshness, what may carry over, cleanup, publication.
- `../skills/_shared/REPORT_VOICE.md`: how every heading is explained.
- `../skills/_shared/REPORT_PALETTE.md`: the only colours allowed.
- `../skills/_shared/REPORT_EDITORIAL_STANDARD.md`: structure, data completeness, floors.
- `../skills/_shared/SECTION_DRAFTING.md`: how long reports are drafted in sections.
- `../skills/_shared/REVIEWER_OPERATIONS.md` and `../skills/report_reviewer/SKILL.md`: the reviewer gate.
- `../config/reviewer.json`: the reviewer model, the red-team scope and the strict maximum of two rounds. Do not raise the cap or name a model in a workflow.
- `../../scripts/review_packet.py`: builds the review packet (the mechanical review, in code) and checks reviewer output.

## Run session (isolated worktree, claims) — do this before anything else

Runs may overlap, so no run works in the shared checkout. RUN_PROTOCOL §8 is binding. Start the session from the main checkout:

`.venv/bin/python scripts/run_session.py start --workflow <workflow> --market <MKT>`

Workflow names: `market_intelligence`, `portfolio_audit`, `options_audit`, `displacement` (one live run per workflow and market; a second is **refused**, exit code 3, so stop and report who holds it), and `watchlist_to_shortlist`, `reject_to_watchlist`, `company_report` (per-company; take names with `scripts/run_claims.py batch` or `names`). The command prints `run_id` and `worktree`. From then on, every command of the run (scripts, ledger, validators, file edits) uses that worktree as its working directory, and `.venv/bin/python` resolves there. Record `run_id`, the worktree path and `base_commit` in the manifest.

## Run directory

Create it as RUN_PROTOCOL §1 says. Every file this run creates lives there. The only things that leave the run are the final report, the updated JSON record files, the email, and the published copy in `docs/`.

## Preflight (every run)

1. Resolve the **latest completed market session** under `../skills/_shared/RUN_PROTOCOL.md` §0. Do not default to the calendar date of the run. Check exchange holidays and close time, then confirm the benchmark's final daily bar; if today's session is incomplete or its final bar is not available, date the report to the most recent earlier completed session with a verified close. Record `run_date` and `session_date` separately when they differ.
2. Check inputs: `.venv/bin/python scripts/market_facts.py --market <MKT> --check-inputs --run-dir "<RUN_DIR>"`. A missing or mis-shaped source stops the run. The manifest records the SHA-256 of every input.
3. Read `.env` for the email settings: `GMAIL_USER`, `GMAIL_APP_PASSWORD`, and `GMAIL_RECIPIENT`. The recipient comes from `.env`, not from this document.
4. Sync is part of the run session: `run_session.py start` fetches origin and cuts the worktree from `origin/main`, so the worktree is already synced and unrelated changes in the main checkout never reach it. Never `merge`, `pull` or `checkout` in the main checkout. Read every JSON record file (watchlist, shortlist, holdings) from the worktree, and record `base_commit` in the manifest. Batch eligibility comes from freshly fetched `origin/main` through `run_claims.py batch`, so a name that origin already holds as `COMPLETED`, or that another live run has claimed, is not offered.

## The ledger

`.venv/bin/python scripts/market_facts.py --market <MKT> --date <session> --screen <ledger_screen from markets.json> --allow-stale-holdings --run-dir "<RUN_DIR>"`

It writes the ledger and the fact pack into `<RUN_DIR>/cache/` and records per-symbol freshness and input hashes in `<RUN_DIR>/manifest.json`. The date argument is the resolved latest completed session, not necessarily the run date. If the newest completed session's final benchmark bar is unavailable, retry once, then resolve the most recent earlier completed session with a verified bar and build for that exact date; do not relabel, copy, or rename a ledger. Stop only when no recent completed benchmark session can be verified or the selected-date build fails. The user's holdings transaction log is the authoritative position record and is assumed accurate; a `HOLDINGS NOT CURRENT` warning reflects freshness metadata, not a reason to stop. Always pass `--allow-stale-holdings`, record the warning and assumption in the manifest, and disclose it in the report without claiming independent reconciliation. This exception does not relax market-price ledger freshness or input/schema validation. The report filename, title and as-of label all use the ledger session date.

A symbol listed in `failures` must be resolved before any N/A cell is allowed. Aliases live in `scripts/config/aliases.json`, which is version-controlled.

## Research

Use the `duck-duck-go` MCP server (`search` and `fetch_content`), as the market intelligence skill describes. Record every result in `<RUN_DIR>/cache/research_<MKT>_<date>.json` with its `source_url`, `as_of`, and `retrieved_at`. Quote only recorded values.

## Reviewer gate (mandatory before any delivery)

One reviewer agent, a conditional red team, at most two rounds. Details are in `../skills/_shared/REVIEWER_OPERATIONS.md`.

1. After the validator prints `RESULT: PASS`, build the packet: `.venv/bin/python scripts/review_packet.py build ... --out-dir "<RUN_DIR>/review/round_1" --round 1`. Code has then already traced numbers, checked tickers, dates, totals and verdict conflicts, and run the validator, citation and readability checks.
2. Read `../config/reviewer.json`. Run the single reviewer (`passes`: `review`) as a fresh agent with the model it names, pointing it at the packet folder and `../skills/report_reviewer/SKILL.md`. Unless this workflow is in `red_team.skip_for`, run the red team on the same folder, using `../skills/red_team/SKILL.md`. Do not pass drafts, the story brief or reasoning.
3. Check the reviewer's output with `review_packet.py check`. Malformed output is rerun once, then treated as REVISE.
4. On REVISE or BLOCK in round 1, fix the findings in the sections that own the quoted text, rerun the validator until `RESULT: PASS`, then build the round 2 packet as a delta (`--round 2 --prev-packet ... --prev-review ...`). If it prints `AGENT NEEDED: False`, the fixes are verified by code: record `round_2: code_verified` and continue. Otherwise run the round 2 reviewer on the delta packet (continue the round-1 session where the runner can), and the red team only if round 1 asked for changes. Two rounds is a strict cap; never run a third or increase `max_rounds`.
5. If round 2 is not APPROVE, fix all evidence-backed findings best-effort, remove or qualify unsupported claims, rerun the validator and pre-delivery checklist, then continue with status `BEST_EFFORT_AFTER_REVIEW_LIMIT`. Record unresolved findings and post-round-2 edits; do not label the report APPROVE.
6. Record each agent's verdict per round in `manifest.json`. If an output is malformed or the agent unavailable after the configured handling, record that status and disclose it; do not exceed two rounds.
7. If the configured reviewer model cannot be run, try it once, then run the same review with the runner's default agent, record the substitution in the manifest and in the report's gate-exceptions section, and continue. An unavailable model is an exception, never a reason to skip the gate or to stop.

## Gate exceptions and mandatory publication (binding)

Every run that completes its research publishes its reports. A gate that the existing evidence cannot satisfy is a recorded and disclosed **exception**, not a stop. The user has pre-approved this; never ask again.

**Hard stops (the only reasons not to publish):** a missing or mis-shaped input file; no completed session with a verified benchmark close, or a failed ledger build for the selected date; a figure that would have to be invented; a failed Research Desk layout check (fix the assembly, never bypass it); a secret that would be published. Everything else is an exception.

**Exception classes and how each is handled:**

| Class | Handling |
|---|---|
| Stale `as_of` (the latest periodic filing, results release or guidance is more than 60 days old and no newer one exists) | Run `citation_check.py ... --allow-stale-asof`. Keep every `as_of` true; never edit one to dodge the gate. The result `PASS WITH EXCEPTIONS` is acceptable. Every other citation failure (URL not in cache, value not in cached text, source floor) is still fixed, not excepted. |
| Reviewer model unavailable | Section Reviewer gate, item 7. Still at most two rounds. |
| Reviewer round 2 not APPROVE | `BEST_EFFORT_AFTER_REVIEW_LIMIT` as above. |
| Short batch (fewer eligible names than the batch size) | Process the eligible names and say so. Do not widen eligibility to fill the batch. |
| Source blocked or unfetchable (403, paywall, bot wall) | Show N/A with the reason; never fill from memory. |
| Residual readability or validator finding after best-effort fixes | Fix what can be fixed, list the rest. |

**Disclosure (mandatory):** every affected report and dossier carries a `<section class="chapter" id="gate-exceptions"><h2>Run notes and gate exceptions</h2>` immediately before its notes/sources, in plain English: what failed, the checker's own line, why it cannot be cured now, how it lowers confidence, and what would cure it and when. The batch or run summary report repeats the list. The first screen of each report (primer or key figures) states the status `PUBLISHED_WITH_GATE_EXCEPTIONS`. The manifest records a `gate_exceptions` list and the status. Never describe an excepted gate as passed, and never describe the report as APPROVE unless every reviewer pass approved. Status words may combine, for example `BEST_EFFORT_AFTER_REVIEW_LIMIT` with `PUBLISHED_WITH_GATE_EXCEPTIONS`.

## Delivery

Only after the validator and reviewer process are complete, with every unmet gate recorded under **Gate exceptions** (`RESULT: PASS` plus reviewer APPROVE is preferred; `BEST_EFFORT_AFTER_REVIEW_LIMIT` and `PUBLISHED_WITH_GATE_EXCEPTIONS` are both acceptable final states):

1. Save the final report under the published `docs/` output path and remove superseded reports for the same market/type. Continue publishing every report, even when email is skipped.
2. Edit the reports, dossiers and record files inside the run's worktree only. Do not run `build_dossier_portal.py` and do not commit or push by hand: `publish_run.py` stamps completion and regenerates the catalog on top of the newest origin copy (the catalog files are never merged).
3. Publish from the worktree: `.venv/bin/python scripts/publish_run.py --run-id "<run_id>" --market "<IN or US>" --message "<descriptive commit message>" --workflow "<stable workflow name>" --completed "<published HTML path>" [more paths] --summary "<one-sentence decision overview>" --highlight "<key change or risk>" --manifest "<RUN_DIR>/manifest.json"`. Include updated dossiers as separate `--completed` paths; never list a failed run's output. It commits only `docs/`, `data/`, `.agents/` and `scripts/` changes, replays them onto the newest `origin/main` (records merge symbol by symbol; the "Overriding earlier publications" rules decide a page both runs changed), validates the data, pushes as a fast-forward, releases the run's claims, and automatically removes the run's worktree and branch after a successful push (pass `--keep-worktree` to preserve them). Exit 5 means refused (a conflict or a newer page on origin): nothing was pushed, so report it. Never force-push.
4. Verify the published destinations on origin. Do not email links when publication fails. `publish_run.py` removes the worktree automatically upon successful push; if `--keep-worktree` was passed, clean it up manually with `.venv/bin/python scripts/run_session.py finish --run-id "<run_id>"`.
5. After successful publication, apply the email policy below. All emails are short digests: one decision summary, up to five highlights, qualifying events when present, and an absolute GitHub Pages link to the full report. Never email the complete HTML report.
6. Send with `.venv/bin/python scripts/send_email.py --html-file "<published HTML path>" --subject "<configured subject>" --report-type "<type>" --summary "<decision overview>" --highlight "<key change>"`, adding event flags only when verified. Repeat `--highlight`, `--shortlisted`, and `--displacement` as needed. Record sent/skipped/failed status and qualifying evidence in the manifest. An email failure must retain the run for retry; an intentional skip is successful delivery.

### Email Policy

- `market-intelligence` and `portfolio-audit`: always send a summary email after successful publication.
- `watchlist`: do not send emails. Watchlist-to-shortlist reports and dossiers are published to GitHub Pages only; email delivery is permanently disabled and intentionally skipped.
- `archive` and `displacement`: no routine emails. Send only when a company newly becomes eligible for the shortlist (`--shortlisted SYMBOL`) or a shortlisted candidate newly becomes eligible to replace an actual current holding (`--displacement "CANDIDATE replaces HOLDING: passed gate and reason"`).
- Compare validated results with the frozen starting state. Already-shortlisted companies, unchanged previously eligible replacements, archive-to-watchlist promotions, tentative ideas and failed gates do not qualify. Do not fabricate events to bypass the sender. Displacement must pass the deterministic displacement gates, including bucket, transaction costs, return hurdle and portfolio caps; this is an eligibility alert, not an executed trade.
- Archive resurrection alone remains silent. If that workflow also completes full shortlist underwriting and newly qualifies a company, send the shortlist event; otherwise only publish the report.
- Preserve existing email eligibility for other report types, but send only a digest and the published report link.
- Use `--dry-run` to preview the policy/digest without accessing credentials or sending mail. The sender centrally skips conditional types without qualifying event flags.

Publication, including portfolio holdings, remains pre-authorized after the validation gates.

## Overriding earlier publications (binding)

A later run may replace a published dossier, report or record written by an earlier run. Fresher evidence is the normal way the catalog moves forward, and it is not a failure. The rule compares freshness with the metadata every published page carries (`research-as-of` and `generated-at` in its `<meta>` tags) and with the record's own dates.

1. **Allowed override.** A run may overwrite an earlier output for the same symbol or report when its own `research-as-of` (ledger session date) is the same as or later than the earlier output's, and its `generated-at` time is later. The run may then overwrite the file in place and update the records in place.
2. **Refused override.** Never overwrite an output whose `research-as-of` is later than this run's, or whose `generated-at` is later than this run's, even when the session dates match. Stop, report both commits and both dates, and leave the existing output alone.
3. **Concurrent runs.** `publish_run.py` does this in code: it fetches `origin/main` again, and for every file both runs changed it applies rules 1 and 2 (HTML) or merges the record by symbol (JSON; the same field changed differently by both runs is a conflict). An allowed override records the superseded commit in the commit message and manifest. A refused override or conflict stops before any push, keeps the run's branch, worktree, claims and run directory, and is reported with both commits and dates.
4. **Eligibility after an override.** A name whose newer output is already on origin is not re-selected for a new batch. Its next underwriting waits for a later round-robin cycle, as the workflow's selection rule states.
5. **Push.** Always fast-forward. Never force-push. If the push is rejected, repeat step 3 once and then report the blocker.

## Cleanup

When delivery is complete, delete the run directory: `rm -rf "<RUN_DIR>"`. The run's worktree and branch are pruned automatically by `publish_run.py` upon successful publish (or manually with `run_session.py finish --run-id <run_id>`). On any failure, keep both and report the run directory, the worktree path and the run id; a failed run's claims stay held until its TTL expires or you release them with `run_session.py finish --run-id <id> --keep-worktree`. Do not delete any file in the repository as cleanup. The only repository changes a run makes are the deliverables listed above.
