# Reviewer Operations (how the reviewer gate runs)

This file explains how the reviewer gate is run. The rubric (what to check) lives in `skills/report_reviewer/SKILL.md`. The model and limits live in `config/reviewer.json`. Read both before running a review.

## 1. Choosing the model

- The model is a setting, not part of the workflow. Set `"model"` in `.agents/config/reviewer.json`. It can be any model id your runner supports, including small and cheap models such as `haiku or luna-high, or gemini-flash 3.8 e.t.c`.
- Workflows never name a model. If a workflow text names one, that text is wrong: fix the workflow, not the config.
- A smaller model needs narrower work, not different work. That is why the review is split into passes (section 3). Keep the same rubric for every model. If a model cannot pass a spot-check on a known-good report, do not use it as the reviewer.
- Calibrate a new model before trusting it: run the reviewer on a report already known to be good (APPROVE expected) and on one with a planted error (REVISE or BLOCK expected). Record both results in `<RUN_DIR>/manifest.json`.

## 2. Preparing the review bundle

The reviewer must see only what it needs. Before the first pass, the writer copies these into `<RUN_DIR>/review/`:

- the report HTML, under its original file name
- `cache/facts_<MKT>_<date>.json` and `cache/research_<MKT>_<date>.json`
- the snapshots in `inputs/`
- the sibling report for the same session, if one exists
- the standards `REPORT_EDITORIAL_STANDARD.md`, `REPORT_VOICE.md`, `REPORT_PALETTE.md`
- the validator output, saved as `validator.txt`

Write `<RUN_DIR>/review/bundle.json` listing each file with its SHA-256. The reviewer records the hashes it read. A review whose hashes do not match the current report is stale and must be re-run.

Do not include the story brief, drafts, earlier reviews, or the writer's notes. The reviewer is independent only if it has not seen the writer's reasoning.

## 3. Running the passes

Run the passes listed in `config/reviewer.json`, one fresh agent per pass. Each pass gets:

- the bundle
- its own section of the rubric (source, consistency, or tone) from `report_reviewer/SKILL.md`
- the instruction to write `<RUN_DIR>/review/round_<N>_<pass>.json` and nothing else

Why split the passes: a small model that checks sourcing, consistency, and tone in one pass tends to skim all three. One focused pass per concern gets a real read.

Presentation and completeness checks are covered by `validate_report.py` and by the writer's own pre-send checklist. Do not ask a reviewer pass to count table rows or words; ask it to judge what the counts cannot show.

## 4. Output contract

Each pass must return JSON matching the shape in `report_reviewer/SKILL.md`. Check it before acting on it:

- It parses as JSON.
- It has `verdict`, `round`, `pass`, and `findings`.
- Every BLOCK or REVISE finding has a `location`, a `quote`, and a `fix`.
- The source pass lists at least 10 numbers it spot-checked against the ledger, with the result of each. A source pass with no spot-checks is malformed.

If the output is malformed, rerun that pass once (`on_malformed_output`). If it is still malformed, treat the pass as REVISE and say so in the report notes. Never treat a malformed pass as APPROVE.

If the reviewer is unavailable (the model is not reachable, or the runner fails), do not deliver. Set the gate to block delivery (`on_unavailable_reviewer`), keep the run directory, and tell the user.

## 5. Combining the passes

- The round is APPROVE only when every pass returns APPROVE, or returns NOTE findings only.
- Any BLOCK from any pass blocks delivery.
- Otherwise the round is REVISE. Fix every BLOCK and REVISE finding from every pass, re-run the validator until it shows `RESULT: PASS`, and start the next round with all passes again.
- Stop after `max_rounds`. If still not APPROVE, do not deliver.

## 6. Writer rules

- The writer fixes findings. The writer does not argue with them in the report. If a finding is wrong, record why in `<RUN_DIR>/review/disputes.md`, fix what is right, and let the next round judge the rest.
- The writer never edits the reviewer's output files.
- Record in `manifest.json`: the reviewer model, each pass's verdict per round, the validator result per round, and the final decision.

## 7. Cost and limits

- A review reads the whole report, so it is the largest input in a run. Keep reports within the size the chosen model handles. If the source pass cannot fit the report, split the source pass by section (one agent per H2) and merge the findings by location.
- The reviewer does not fetch data. Anything it cannot verify from the bundle is a finding, not a silent pass.
