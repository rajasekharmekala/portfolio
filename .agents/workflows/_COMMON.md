# Common Workflow Rules (read by every workflow)

Every workflow takes a market (`IN` or `US`) and reads its parameters from `../config/markets.json` and its sources from `../config/portfolios.json`. Nothing market-specific is written into a workflow.

## Governing documents (binding)

- `../skills/_shared/RUN_PROTOCOL.md`: run directory, freshness, what may carry over, cleanup, publication.
- `../skills/_shared/REPORT_VOICE.md`: how every heading is explained.
- `../skills/_shared/REPORT_PALETTE.md`: the only colours allowed.
- `../skills/_shared/REPORT_EDITORIAL_STANDARD.md`: structure, data completeness, floors.
- `../skills/_shared/SECTION_DRAFTING.md`: how long reports are drafted in sections.
- `../skills/_shared/REVIEWER_OPERATIONS.md` and `../skills/report_reviewer/SKILL.md`: the reviewer gate.
- `../config/reviewer.json`: the reviewer model and rounds. Do not name a model in a workflow.

## Run directory

Create it first, as RUN_PROTOCOL §1 says. Every file this run creates lives there. The only things that leave the run are the final report, the updated workbooks, the email, and the published copy in `docs/`.

## Preflight (every run)

1. Resolve the session date for the market (see the market workflow). Use the market's session date, not the system date.
2. Check inputs: `python3 scripts/market_facts.py --market <MKT> --check-inputs --run-dir "<RUN_DIR>"`. A missing or mis-shaped source stops the run. The manifest records the SHA-256 of every input.
3. Read `.env` for the email settings: `GMAIL_USER`, `GMAIL_APP_PASSWORD`, and `GMAIL_RECIPIENT`. The recipient comes from `.env`, not from this document.

## The ledger

`python3 scripts/market_facts.py --market <MKT> --date <session> --screen <ledger_screen from markets.json> --run-dir "<RUN_DIR>"`

It writes the ledger and the fact pack into `<RUN_DIR>/cache/` and records per-symbol freshness and input hashes in `<RUN_DIR>/manifest.json`. If it exits with `STALE DATA` or `HOLDINGS NOT CURRENT`, stop. Do not relabel, copy, or rename a ledger. Re-run after the source updates. Use `--allow-stale-holdings` only if the user has said so, and state the reason in the report.

A symbol listed in `failures` must be resolved before any N/A cell is allowed. Aliases live in `scripts/config/aliases.json`, which is version-controlled.

## Research

Use the `duck-duck-go` MCP server (`search` and `fetch_content`), as the market intelligence skill describes. Record every result in `<RUN_DIR>/cache/research_<MKT>_<date>.json` with its `source_url`, `as_of`, and `retrieved_at`. Quote only recorded values.

## Reviewer gate (mandatory before any delivery)

1. Read `../config/reviewer.json`. Run each pass it lists (`source`, `consistency`, `tone`) as a separate fresh agent, using the model it names, following `../skills/_shared/REVIEWER_OPERATIONS.md`.
2. Give each pass only the review bundle described in REVIEWER_OPERATIONS §2. Do not pass drafts, the story brief, or reasoning.
3. On REVISE or BLOCK, fix every BLOCK and REVISE finding, re-run the validator until `RESULT: PASS`, and re-run the passes. At most `max_rounds` rounds. If still not APPROVE, do not deliver: keep the run directory and report the open findings.
4. Record each pass's verdict per round in `manifest.json`.

## Delivery

Only after the validator shows `RESULT: PASS` and the reviewer returns APPROVE:

1. Save the final report to the path named in `markets.json` under `output` (e.g. `docs/reports/`), replacing the previous file in the working tree (historical versions are preserved in git commit history).
2. Send the email with `python3 scripts/send_email.py --html-file "<report path>" --subject "<email_subject from markets.json, filled in>"`. The recipient is read from `.env`.
3. Run `python3 scripts/build_dossier_portal.py` to update `docs/index.html` and `docs/blogs/index.html` with links to the latest reports.
4. Record delivery results in `manifest.json`.

## Cleanup

When delivery is complete, delete the run directory: `rm -rf "<RUN_DIR>"`. On any failure, keep it and report its path. Do not delete any file in the repository as cleanup. The only repository changes a run makes are the deliverables listed above.
