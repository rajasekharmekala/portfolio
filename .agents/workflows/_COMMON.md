# Common Workflow Rules (read by every workflow)

Every workflow takes a market (`IN` or `US`) and reads its parameters from `../config/markets.json` and its sources from `../config/portfolios.json`. Nothing market-specific is written into a workflow.

## Governing documents (binding)

- `../skills/_shared/RUN_PROTOCOL.md`: run directory, freshness, what may carry over, cleanup, publication.
- `../skills/_shared/REPORT_VOICE.md`: how every heading is explained.
- `../skills/_shared/REPORT_PALETTE.md`: the only colours allowed.
- `../skills/_shared/REPORT_EDITORIAL_STANDARD.md`: structure, data completeness, floors.
- `../skills/_shared/SECTION_DRAFTING.md`: how long reports are drafted in sections.
- `../skills/_shared/REVIEWER_OPERATIONS.md` and `../skills/report_reviewer/SKILL.md`: the reviewer gate.
- `../config/reviewer.json`: the reviewer model and strict maximum of four rounds. Do not raise the cap or name a model in a workflow.

## Run directory

Create it first, as RUN_PROTOCOL §1 says. Every file this run creates lives there. The only things that leave the run are the final report, the updated JSON record files, the email, and the published copy in `docs/`.

## Preflight (every run)

1. Resolve the **latest completed market session** under `../skills/_shared/RUN_PROTOCOL.md` §0. Do not default to the calendar date of the run. Check exchange holidays and close time, then confirm the benchmark's final daily bar; if today's session is incomplete or its final bar is not available, date the report to the most recent earlier completed session with a verified close. Record `run_date` and `session_date` separately when they differ.
2. Check inputs: `.venv/bin/python scripts/market_facts.py --market <MKT> --check-inputs --run-dir "<RUN_DIR>"`. A missing or mis-shaped source stops the run. The manifest records the SHA-256 of every input.
3. Read `.env` for the email settings: `GMAIL_USER`, `GMAIL_APP_PASSWORD`, and `GMAIL_RECIPIENT`. The recipient comes from `.env`, not from this document.

## The ledger

`.venv/bin/python scripts/market_facts.py --market <MKT> --date <session> --screen <ledger_screen from markets.json> --allow-stale-holdings --run-dir "<RUN_DIR>"`

It writes the ledger and the fact pack into `<RUN_DIR>/cache/` and records per-symbol freshness and input hashes in `<RUN_DIR>/manifest.json`. The date argument is the resolved latest completed session, not necessarily the run date. If the newest completed session's final benchmark bar is unavailable, retry once, then resolve the most recent earlier completed session with a verified bar and build for that exact date; do not relabel, copy, or rename a ledger. Stop only when no recent completed benchmark session can be verified or the selected-date build fails. The user's holdings transaction log is the authoritative position record and is assumed accurate; a `HOLDINGS NOT CURRENT` warning reflects freshness metadata, not a reason to stop. Always pass `--allow-stale-holdings`, record the warning and assumption in the manifest, and disclose it in the report without claiming independent reconciliation. This exception does not relax market-price ledger freshness or input/schema validation. The report filename, title and as-of label all use the ledger session date.

A symbol listed in `failures` must be resolved before any N/A cell is allowed. Aliases live in `scripts/config/aliases.json`, which is version-controlled.

## Research

Use the `duck-duck-go` MCP server (`search` and `fetch_content`), as the market intelligence skill describes. Record every result in `<RUN_DIR>/cache/research_<MKT>_<date>.json` with its `source_url`, `as_of`, and `retrieved_at`. Quote only recorded values.

## Reviewer gate (mandatory before any delivery)

1. Read `../config/reviewer.json`. Run each pass it lists (`source`, `consistency`, `tone`) as a separate fresh agent, using the model it names, following `../skills/_shared/REVIEWER_OPERATIONS.md`.
2. Give each pass only the review bundle described in REVIEWER_OPERATIONS §2. Do not pass drafts, the story brief, or reasoning.
3. On REVISE or BLOCK in rounds 1–3, consolidate and fix all findings, rerun the validator until `RESULT: PASS`, then rerun all configured passes. Four rounds is a strict cap; never run a fifth round or increase `max_rounds`.
4. If round 4 is not APPROVE, fix all evidence-backed findings best-effort, remove or qualify unsupported claims, rerun the validator and pre-delivery checklist, then continue with status `BEST_EFFORT_AFTER_REVIEW_LIMIT`. Record unresolved findings and post-round-4 edits; do not label the report APPROVE.
5. Record each pass's verdict per round in `manifest.json`. If a pass is malformed or unavailable after the configured handling, record that status and disclose it; do not exceed four rounds.
6. If the configured reviewer model cannot be run, try it once, then run the same passes with the runner's default agent, record the substitution in the manifest and in the report's gate-exceptions section, and continue. An unavailable model is an exception, never a reason to skip the gate or to stop.

## Gate exceptions and mandatory publication (binding)

Every run that completes its research publishes its reports. A gate that the existing evidence cannot satisfy is a recorded and disclosed **exception**, not a stop. The user has pre-approved this; never ask again.

**Hard stops (the only reasons not to publish):** a missing or mis-shaped input file; no completed session with a verified benchmark close, or a failed ledger build for the selected date; a figure that would have to be invented; a failed Research Desk layout check (fix the assembly, never bypass it); a secret that would be published. Everything else is an exception.

**Exception classes and how each is handled:**

| Class | Handling |
|---|---|
| Stale `as_of` (the latest periodic filing, results release or guidance is more than 60 days old and no newer one exists) | Run `citation_check.py ... --allow-stale-asof`. Keep every `as_of` true; never edit one to dodge the gate. The result `PASS WITH EXCEPTIONS` is acceptable. Every other citation failure (URL not in cache, value not in cached text, source floor) is still fixed, not excepted. |
| Reviewer model unavailable | Section Reviewer gate, item 6. Still at most four rounds. |
| Reviewer round 4 not APPROVE | `BEST_EFFORT_AFTER_REVIEW_LIMIT` as above. |
| Short batch (fewer eligible names than the batch size) | Process the eligible names and say so. Do not widen eligibility to fill the batch. |
| Source blocked or unfetchable (403, paywall, bot wall) | Show N/A with the reason; never fill from memory. |
| Residual readability or validator finding after best-effort fixes | Fix what can be fixed, list the rest. |

**Disclosure (mandatory):** every affected report and dossier carries a `<section class="chapter" id="gate-exceptions"><h2>Run notes and gate exceptions</h2>` immediately before its notes/sources, in plain English: what failed, the checker's own line, why it cannot be cured now, how it lowers confidence, and what would cure it and when. The batch or run summary report repeats the list. The first screen of each report (primer or key figures) states the status `PUBLISHED_WITH_GATE_EXCEPTIONS`. The manifest records a `gate_exceptions` list and the status. Never describe an excepted gate as passed, and never describe the report as APPROVE unless every reviewer pass approved. Status words may combine, for example `BEST_EFFORT_AFTER_REVIEW_LIMIT` with `PUBLISHED_WITH_GATE_EXCEPTIONS`.

## Delivery

Only after the validator and reviewer process are complete, with every unmet gate recorded under **Gate exceptions** (`RESULT: PASS` plus reviewer APPROVE is preferred; `BEST_EFFORT_AFTER_REVIEW_LIMIT` and `PUBLISHED_WITH_GATE_EXCEPTIONS` are both acceptable final states):

1. Save the final report under the published `docs/` output path and remove superseded reports for the same market/type. Continue publishing every report, even when email is skipped.
2. Record completion and refresh the catalog with `.venv/bin/python scripts/build_dossier_portal.py --completed "<published HTML path>" --workflow "<stable workflow name>" --market "<IN or US>" --summary "<one-sentence decision overview>" --highlight "<key change or risk>" --repair-links`. Include updated dossiers as separate `--completed` arguments. Never mark failed runs completed.
3. Verify published destinations and stage only this run's reports, deletions, public catalog JSON files and relevant workflow changes. Never stage unrelated work or private research records.
4. Commit and push publication to the configured origin branch, without force-pushing or asking for per-run approval. If rejected, fetch/integrate safely and retry once. Record the commit and push result in the manifest. Do not email links when publication fails.
5. After successful publication, apply the email policy below. All emails are short digests: one decision summary, up to five highlights, qualifying events when present, and an absolute GitHub Pages link to the full report. Never email the complete HTML report.
6. Send with `.venv/bin/python scripts/send_email.py --html-file "<published HTML path>" --subject "<configured subject>" --report-type "<type>" --summary "<decision overview>" --highlight "<key change>"`, adding event flags only when verified. Repeat `--highlight`, `--shortlisted`, and `--displacement` as needed. Record sent/skipped/failed status and qualifying evidence in the manifest. An email failure must retain the run for retry; an intentional skip is successful delivery.

### Email Policy

- `market-intelligence` and `portfolio-audit`: always send a summary email after successful publication.
- `watchlist`, `archive`, and `displacement`: no routine emails. Send only when a company newly becomes eligible for the shortlist (`--shortlisted SYMBOL`) or a shortlisted candidate newly becomes eligible to replace an actual current holding (`--displacement "CANDIDATE replaces HOLDING: passed gate and reason"`).
- Compare validated results with the frozen starting state. Already-shortlisted companies, unchanged previously eligible replacements, archive-to-watchlist promotions, tentative ideas and failed gates do not qualify. Do not fabricate events to bypass the sender. Displacement must pass the deterministic displacement gates, including bucket, transaction costs, return hurdle and portfolio caps; this is an eligibility alert, not an executed trade.
- Archive resurrection alone remains silent. If that workflow also completes full shortlist underwriting and newly qualifies a company, send the shortlist event; otherwise only publish the report.
- Preserve existing email eligibility for other report types, but send only a digest and the published report link.
- Use `--dry-run` to preview the policy/digest without accessing credentials or sending mail. The sender centrally skips conditional types without qualifying event flags.

Publication, including portfolio holdings, remains pre-authorized after the validation gates.

## Cleanup

When delivery is complete, delete the run directory: `rm -rf "<RUN_DIR>"`. On any failure, keep it and report its path. Do not delete any file in the repository as cleanup. The only repository changes a run makes are the deliverables listed above.
