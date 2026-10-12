# Reviewer Operations (how the reviewer gate runs)

This file explains how the reviewer gate is run. The rubric (what to judge) lives in `skills/report_reviewer/SKILL.md`; the red team's method lives in `skills/red_team/SKILL.md`. The model, red-team scope and limits live in `config/reviewer.json`. Read both before running a review.

The design in one paragraph: code does the mechanical review once, in `scripts/review_packet.py`. One reviewer agent reads the small packet it produces and does only the judgment. A red team runs only for decision-driving reports and reads a short conclusions digest. Round 2 reviews only what changed. Nobody re-reads the raw report, ledger and research record to re-derive what code already checked.

## 1. Choosing the model

- The model is a setting, not part of the workflow. Set `"model"` in `.agents/config/reviewer.json` (default `ao-claude-lc/claude-sonnet-5-5`). Any model id the runner supports works.
- Workflows never name a model. If a workflow text names one, that text is wrong: fix the workflow, not the config.
- The red team uses the same model unless `red_team.model` is set.
- Calibrate a new model before trusting it: run the reviewer on a report already known to be good (APPROVE expected) and on one with a planted error (REVISE or BLOCK expected).

## 2. Building the packet (code, before any agent)

After the full validator prints `RESULT: PASS`, build the round's packet:

```
.venv/bin/python scripts/review_packet.py build --report <report.html> --kind <market_intel|portfolio_audit|dossier> \
  --facts <RUN_DIR>/cache/facts_<MKT>_<date>.json --research <RUN_DIR>/cache/research_<MKT>_<date>.json \
  --out-dir <RUN_DIR>/review/round_<N> --round <N> [--sibling <sibling report>] [--inputs-dir <RUN_DIR>/inputs] \
  [--allow-stale-asof] [--symbol <TICKER>]
```

Use `--kind portfolio_audit` for audits, options reviews, the capital allocation and archive/watchlist batches that are not single-company dossiers; use `--kind dossier` for a single-company dossier. Pass `--sibling` when a sibling report for the same session exists. Pass `--allow-stale-asof` exactly when the citation check was run with it.

It writes `review_packet.md`, `conclusions_digest.md`, `report_text.md` and `packet.json` (item ids, the SHA-256 of the report, ledger, research record and sibling, and section hashes for round 2). A review whose report hash does not match the current report is stale and must be re-run.

What it does in code, so no agent does it: traces every number to the ledger, the research record, the positions replay from `data/accounts/` and simple arithmetic on them; checks Stage, RSI and close claims, session date, table totals, asymmetry ratios, verdict conflicts and sibling differences; and runs the validator, citation check and readability check. It lists only what code could not settle.

The reviewer is independent only if it has not seen the writer's reasoning. Do not put the story brief, drafts, earlier reviews or the writer's notes in the run's `review/` folder.

## 3. Running the review

1. Start one reviewer agent with the configured model. Its prompt names the pass (`review`), points it at `<RUN_DIR>/review/round_<N>/`, and says to follow `report_reviewer/SKILL.md`. It writes `round_<N>/round_<N>_review.json`.
2. If the workflow is not in `red_team.skip_for`, start the red team at the same time, pointing it at the same folder and `red_team/SKILL.md`. It reads `conclusions_digest.md` and writes `round_<N>/round_<N>_red_team.json`.
3. Check each output before acting on it:
   `.venv/bin/python scripts/review_packet.py check --review <round_<N>_review.json> --packet <packet.json> --report <report.html>`
   It verifies JSON shape, verdict words, that every BLOCK/REVISE finding has `location`, `quote`, `fix` and `kind`, that every quote is really in the report, that every packet item has a disposition, that the verdict rows were all reviewed, and that the report has not changed since the packet. The red team output is checked by reading it: it must contain the `bear_case` block.
4. If the output is malformed, rerun that agent once (`on_malformed_output`). If it is still malformed, treat it as REVISE and say so in the report notes. Never treat a malformed output as APPROVE.
5. If a reviewer is unavailable (the model is not reachable, or the runner fails), try the configured model once, then run the same pass with the runner's default agent and record the substitution (configured model, substitute, reason) in the manifest and in the report's `gate-exceptions` section. An unavailable reviewer never blocks publication.

## 4. Rounds: a strict cap of two, round 2 is a delta

- `max_rounds` is a strict hard cap of **2 complete rounds** for every skill and workflow. Never increase it, split a round into extra reviews, or launch a third round.
- Round 1 is APPROVE when the reviewer returns APPROVE (NOTE findings only) and the red team, if run, is `verdict_holds` with NOTE findings only.
- On REVISE or BLOCK, consolidate the findings, fix them in the sections that own the quoted text (`SECTION_DRAFTING.md`), re-assemble, rerun the validator until `RESULT: PASS`, then build the **round 2 packet as a delta**:

  ```
  .venv/bin/python scripts/review_packet.py build ... --round 2 \
    --prev-packet <RUN_DIR>/review/round_1/packet.json --prev-review <RUN_DIR>/review/round_1/round_1_review.json
  ```

  It lists only items in sections that changed, marks each previous finding as fixed (its quote is gone) or still present, and carries the sections' prose. It prints `AGENT NEEDED: True|False`.
- **Skip the agent** when it prints `False`: every open round-1 finding was `mechanical`, every quote is gone, and the code checks show no items. The fixes are verified by code. Count round 2 as APPROVE and record `round_2: code_verified` in the manifest.
- Otherwise run the round 2 reviewer on the delta packet. Continue the round-1 reviewer's session when the runner can (`continue_round_1_session`); it already holds the context. If it cannot, start a fresh agent with the delta packet.
- The red team runs in round 2 only if its round-1 assessment was `verdict_should_be_stricter` or `verdict_unsupported`, or it had a BLOCK/REVISE finding. It checks only that the writer's answer is present, cites bundle evidence and shows its arithmetic.
- Round 2 is the final independent review. If it returns REVISE or BLOCK, apply every fix the approved evidence supports; remove or clearly qualify unsupported claims; rerun the validator and the writer's pre-delivery checklist. Do not launch another round.
- After round 2, finish best-effort when the validator passes. Record `BEST_EFFORT_AFTER_REVIEW_LIMIT` in the manifest, list unresolved findings and any edits made after the final review, and disclose that the report did not receive reviewer APPROVE. Do not describe that state as APPROVE.
- A BLOCK finding means the quoted claim or section must not be carried forward unchanged. Correct it, omit it, or state the evidence gap.

## 5. Writer rules

- The writer fixes findings. The writer does not argue with them in the report. If a finding is wrong, record why in `<RUN_DIR>/review/disputes.md`, fix what is right, and let the next round judge the rest.
- The writer never edits the reviewer's output files.
- Record in `manifest.json`: the reviewer model, each agent's verdict per round, the validator result per round, whether round 2 was an agent, a delta review or `code_verified`, and the final decision.

## 6. Cost and limits

- The reviewer does not fetch data and does not search the web. Live web research belongs to the research stage (`RESEARCH_CONTRACT.md`) and is recorded in the research record; the reviewer judges claims against that record. Anything it cannot verify from the packet and the files the packet points to is a finding, not a silent pass.
- Do not ask any agent to count table rows or words, recompute totals, re-run the validators or re-trace numbers. That is code.
- If the packet itself is too large for the chosen model (a long batch of dossiers), build one packet per dossier or per H2 group and merge the findings by location.
