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

`.venv/bin/python scripts/market_facts.py --market <MKT> --date <session> --screen <ledger_screen from markets.json> --run-dir "<RUN_DIR>"`

It writes the ledger and the fact pack into `<RUN_DIR>/cache/` and records per-symbol freshness and input hashes in `<RUN_DIR>/manifest.json`. The date argument is the resolved latest completed session, not necessarily the run date. If the newest completed session's final benchmark bar is unavailable, retry once, then resolve the most recent earlier completed session with a verified bar and build for that exact date; do not relabel, copy, or rename a ledger. Stop only when no recent completed benchmark session can be verified or the selected-date build fails. If it exits with `HOLDINGS NOT CURRENT`, stop. Use `--allow-stale-holdings` only if the user has said so, and state the reason in the report. The report filename, title and as-of label all use the ledger session date.

A symbol listed in `failures` must be resolved before any N/A cell is allowed. Aliases live in `scripts/config/aliases.json`, which is version-controlled.

## Research

Use the `duck-duck-go` MCP server (`search` and `fetch_content`), as the market intelligence skill describes. Record every result in `<RUN_DIR>/cache/research_<MKT>_<date>.json` with its `source_url`, `as_of`, and `retrieved_at`. Quote only recorded values.

## Reviewer gate (mandatory before any delivery)

1. Read `../config/reviewer.json`. Run each pass it lists (`source`, `consistency`, `tone`) as a separate fresh agent, using the model it names, following `../skills/_shared/REVIEWER_OPERATIONS.md`.
2. Give each pass only the review bundle described in REVIEWER_OPERATIONS §2. Do not pass drafts, the story brief, or reasoning.
3. On REVISE or BLOCK in rounds 1–3, consolidate and fix all findings, rerun the validator until `RESULT: PASS`, then rerun all configured passes. Four rounds is a strict cap; never run a fifth round or increase `max_rounds`.
4. If round 4 is not APPROVE, fix all evidence-backed findings best-effort, remove or qualify unsupported claims, rerun the validator and pre-delivery checklist, then continue with status `BEST_EFFORT_AFTER_REVIEW_LIMIT`. Record unresolved findings and post-round-4 edits; do not label the report APPROVE.
5. Record each pass's verdict per round in `manifest.json`. If a pass is malformed or unavailable after the configured handling, record that status and disclose it; do not exceed four rounds.

## Delivery

Only after the validator shows `RESULT: PASS` and either the reviewer returns APPROVE within four rounds or the writer records `BEST_EFFORT_AFTER_REVIEW_LIMIT` following the round-4 procedure:

1. Save the final report to the path named in `markets.json` under `output` (e.g. `docs/reports/`), replacing and removing any superseded report for the same market and report type (historical versions remain in git history).
2. Send the email with `.venv/bin/python scripts/send_email.py --html-file "<report path>" --subject "<email_subject from markets.json, filled in>"`. The recipient is read from `.env`.
3. Run `.venv/bin/python scripts/build_dossier_portal.py` to update `docs/index.html` and `docs/blogs/index.html` with links to the latest reports.
4. Verify that each index link resolves to an existing report and that published HTML uses relative links only.
5. Automatically commit and push the publication to the configured `origin` branch. Do not ask the user to commit, push, or approve publication. Stage only this run's report additions/deletions, generated indexes, and skill/workflow/config changes made for this run; leave unrelated working-tree changes unstaged. Never force-push. If a push is rejected, fetch and integrate safely and retry once; if that still fails, report the blocker and keep the local commit.
6. Record the commit hash and push result in `manifest.json`. Delivery is incomplete until the push succeeds.

Publication to this repository's GitHub Pages, including portfolio holdings, is pre-authorized by the user and mandatory after the gates above. Do not add per-run approval prompts.

## Cleanup

When delivery is complete, delete the run directory: `rm -rf "<RUN_DIR>"`. On any failure, keep it and report its path. Do not delete any file in the repository as cleanup. The only repository changes a run makes are the deliverables listed above.
