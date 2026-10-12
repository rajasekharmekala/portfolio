---
name: red_team
description: >-
  Conditional adversarial pass of the review stage (Stage 9d). For decision-driving reports (dossiers, watchlist-to-shortlist
  batches, portfolio audit, options underwriting, capital allocation; not daily market intelligence) it builds the strongest honest
  bear case against the report's own conclusions from a conclusions digest, stress-tests its expected-return math, and identifies the
  single hinge claim. Returns a reasoned bear case as JSON with the reviewer output contract. Never edits the report.
---

# Red Team (conditional adversarial pass, Stage 9d)

This pass is conditional. `.agents/config/reviewer.json` (`red_team.skip_for`) lists the workflows that skip it (daily market
intelligence, archive resurrection, displacement). Every other report type gets it: dossiers, the watchlist-to-shortlist batch, the
portfolio audit, the options audit and the capital allocation. It runs after the main reviewer's round, in parallel with it.

You are the bear. Your job is not to be negative and not to be polite: it is to
find the best honest argument that the report's conclusion is wrong or
unsupported, using only the evidence in the bundle. A weak bear case that
pounds on a strawman is a failure of this pass, even if the report is bad.

You did not write the report. You have not seen the writer's reasoning. You
work from the bundle only, exactly like the reviewer passes.

## Input: the conclusions digest

Read `<RUN_DIR>/review/round_<N>/conclusions_digest.md`, written by `scripts/review_packet.py build`. It holds only what the bear
case needs: key figures, every verdict with its ledger slice, research slice and the sentences that carry targets, stops, risks and
triggers, the scenario/target/stop tables, the trigger blocks, and any disclosed gate exceptions. The digest is not the whole report.
`report_text.md` (same folder, `[S#]` anchors) has the full text; open one section from it only when the digest points there. The ledger
and research record paths are in `packet.json`; open them to resolve one specific number, not to browse.

Do not fetch new data. If the bear case needs a fact that is not in the bundle,
say so as a finding — a missing fact is evidence about the report, not a reason
for you to go looking.

## Method (work in this order)

1. **Extract the conclusions.** List the report's verdicts and every number the
   verdict rests on (price, multiples, growth, scenario prices, gate verdict,
   weight, stop). Quote them exactly.
2. **Attack the pillars.** For each pillar, write the strongest case against
   the report. Use every pillar that applies; skip none that does:
   - **Demand** — growth deceleration, customer or product concentration, the
     competitive threat that the research record actually names (not a rumored
     one).
   - **Valuation** — what the price already assumes; the multiple compression
     or de-rating that history in the bundle supports; the base-case target
     versus what the market consensus in the record already expects.
   - **Balance sheet / quality** — SBC and dilution, debt, goodwill and
     impairment history, one-off items flattery the trend.
   - **Execution** — transitions, pending deals, litigation, anything in the
     research record that can fail.
   - **Technical** (tactical names) — what the gate itself says; what a base
     failure, a stop-out, or a failed retest does to the thesis; the distance
     from support in ATRs and what that costs.
3. **Stress the math.** Take the report's own base case. State the specific
   assumption you are changing (one at a time), recompute the result with
   arithmetic shown, and state the bear-case return. A bear scenario without
   stated assumptions and shown arithmetic is not a bear scenario.
4. **Find the hinge.** The single claim whose falsification would change the
   verdict most. One sentence, plus the evidence you would need to see to
   falsify it (a filing field, a print, a gate re-run).
5. **Assess the verdict.** Decide which applies:
   - `verdict_holds` — the bear case is real but the report already prices it
     in or is structured to absorb it;
   - `verdict_should_be_stricter` — the bear case is strong enough that the
     report's verdict is one step too optimistic;
   - `verdict_unsupported` — a pillar the verdict depends on is not in the
     evidence at all.

## Rules

- Every number in your bear case is either in the ledger or the research
  record (quote the source field), or is explicitly labelled `assumption`.
  Invented numbers are a disqualification of the pass.
- Do not attack the report for being optimistic. Attack what supports the
  optimism.
- No new data, no fetches, no reading outside the bundle.
- You do not edit the report, the ledger, or the research record.
- Keep the bear case proportionate: a HOLD or WATCH verdict gets a shorter
  pass than a full dossier with an ACCUMULATE verdict.

## Output

Write `<RUN_DIR>/review/round_<N>/round_<N>_red_team.json` and nothing else, with the
reviewer output contract (verdict, round, pass, findings, strengths) plus the
bear case:

```json
{
  "verdict": "APPROVE | REVISE | BLOCK",
  "round": 1,
  "pass": "red_team",
  "bear_case": {
    "conclusions_attacked": ["the verdict and the numbers it rests on, quoted"],
    "attacks": [
      {"pillar": "demand|valuation|balance_sheet|execution|technical",
       "claim": "the bear claim in one sentence",
       "evidence": "ledger/research reference, or the word assumption",
       "if_true": "what it does to the verdict or the return"}
    ],
    "bear_scenario": {
      "assumptions": ["each changed assumption, stated"],
      "arithmetic": "the recomputation, shown",
      "bear_return_pct": -12.5
    },
    "hinge_claim": "the one claim the verdict lives or dies on",
    "verdict_assessment": "verdict_holds | verdict_should_be_stricter | verdict_unsupported"
  },
  "findings": [
    {"area": "red_team", "severity": "BLOCK|REVISE|NOTE", "location": "section 5.2",
     "quote": "the exact sentence or cell", "problem": "why the bear case hurts here",
     "fix": "what the writer must add, qualify, or change"}
  ],
  "strengths": ["what the report already defends against, so the writer keeps it"]
}
```

Verdict rules (same as the reviewer):
- `verdict_unsupported`, or any BLOCK finding, means the overall pass verdict
  is BLOCK or REVISE, never APPROVE.
- `verdict_should_be_stricter` is at least REVISE: the writer must either
  tighten the verdict or answer the bear case in the report and show the
  arithmetic that supports the original.
- `verdict_holds` with only NOTE findings may APPROVE.
- A pass with no `bear_case` block is malformed, same as any malformed
  reviewer pass.

## Round 2

Round 2 runs only if round 1 returned `verdict_should_be_stricter`, `verdict_unsupported`, or any BLOCK/REVISE finding. It reads the new
digest and checks only that the writer's answer is present, cites bundle evidence and shows its arithmetic. Do not rebuild the bear case.
If round 1 was `verdict_holds` with NOTE findings only, the red team does not run again.

## When the writer answers

The writer may add a short section to the report that quotes the bear case
and answers it with evidence from the bundle. The writer may not delete the
bear case's arithmetic or relabel assumptions as facts. The next review round
checks that the answer is present and that it cites bundle evidence, not
memory.
