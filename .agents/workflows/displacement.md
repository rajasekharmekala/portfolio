# Displacement memo workflow (W8)

One-page, advisory-only memo comparing **one current holding** against **one
candidate** name, produced by `scripts/displacement.py` from a stored input
JSON. It never generates orders. The user makes the decision and records it in
the decision log (`data/decisions/`, W10).

## When to run

- A portfolio-audit verdict (`TRIM_PROFIT_BOOKING`, `PENDING`, `EXIT`) names a
  holding that might be better spent elsewhere.
- A watchlist/shortlist name (`QUALIFIED`, `QUALIFIED_DEFERRED`) looks like a
  better use of capital than a current position.
- The user asks "should I swap X for Y?".

## Inputs (stored JSON, one file per pair)

Location: `data/displacement/<HOLDING>_vs_<CANDIDATE>_<as_of>.json`.
The agent fills this from the research stage; every number in the memo is
computed from it, so the memo is reproducible.

```json
{
  "schema_version": 1,
  "as_of": "YYYY-MM-DD",
  "market": "US | IN",
  "holding":   { name block },
  "candidate": { name block },
  "costs": {
    "sell_bps": 2, "buy_bps": 2, "slippage_bps": 5,
    "notional_usd": <market value of the holding>,
    "tax_note": "one line on the sell-leg tax treatment"
  },
  "params": { "reversal_threshold_pp": 5.0 }
}
```

Name block (identical shape for holding and candidate — the "same scorecard"):

| key | source |
|---|---|
| `symbol`, `name` | account file / shortlist |
| `bucket` | `CORE_ALPHA` or `TACTICAL_MOMENTUM` (scoring.json) |
| `theme` | one-line theme tag (used for theme-exposure deltas) |
| `price` | frozen facts ledger for `as_of` |
| `weight_pct` | holding: position value / known market portfolio value; candidate: 0 |
| `proposed_weight_pct` | candidate only; a tier size from `scoring.json` tier table |
| `gate_verdict` | `scripts/momentum_gate.py` on the frozen ledger (`IN_MOMENTUM`, `ENTERING_MOMENTUM`, `NO_MOMENTUM`) |
| `support_distance_atr` | `base_pivot_atr` from the gate output |
| `expected_return_pct_12m` | `{low, base, high}`; base from the dossier scenario table or analyst average target, low/high from the worst/best case |
| `scorecard` | `{quality, valuation, momentum}` 0–100 research-stage sub-scores |
| `source_note` | one line naming the sources and retrieval date |

Rules for filling inputs:

- Price, gate verdict and support distance MUST come from the frozen facts
  ledger + `momentum_gate.py` for the same `as_of`. Never mix dates.
- Expected-return ranges must be the same kind of estimate for both names
  (scenario-based or analyst-target-based), stated in the source notes.
- The 15% hard cap and the 50–65% tactical band are read by the script from
  `.agents/config/scoring.json` — do not copy them into the input.

## Recommendation logic (deterministic, in `compute()`)

Round-trip cost = `sell_bps + buy_bps + 2 × slippage_bps`; drag in pp = that
figure / 100. `edge = candidate.base − holding.base`;
`net_edge = edge − cost drag`.

1. **Cap violation** → `HOLD` with a resize-and-rerun note (never propose a
   size above the hard cap).
2. Candidate **gate-eligible** (`IN_MOMENTUM` or `ENTERING_MOMENTUM`) and
   `net_edge ≥ reversal_threshold_pp` (default 5.0) → **DISPLACE**.
3. Candidate **not gate-eligible** but `edge ≥ threshold` → **WATCH**
   (strong business/valuation, the gate is the only blocker).
4. Everything else → **HOLD**.

A holding that itself fails the momentum gate is not, by itself, a reason to
displace: a failed gate means "no new allocation", not "sell". The memo notes
each name's gate verdict so the user can see both.

## Memo content (the six elements from plan section 7)

1. Recommendation line: **DISPLACE / HOLD / WATCH** + one-paragraph rationale.
2. Side-by-side scorecard table (price, bucket, theme, weight, gate verdict,
   support distance, sub-scores, expected-return range).
3. Expected return of each with its range, plus the source note.
4. Transaction costs: round-trip bps, dollar cost on notional, drag in pp,
   tax note.
5. Portfolio caps and theme exposure: hard-cap compliance, tactical band,
   theme deltas, post-trade weights.
6. The single condition that would reverse the advice (one sentence, with the
   concrete numbers and the gate verdicts that would flip it).

Footer: stored-input path, `--verify` instruction, and the reminder that the
user decides and logs the outcome in `data/decisions/`.

## Run

```bash
.venv/bin/python scripts/displacement.py \
  --input data/displacement/ORCL_vs_ADBE_2026-10-08.json \
  --out docs/reports/displacement/ORCL_vs_ADBE_2026-10-08.md

# pass criterion: the memo is reproduced from the stored inputs
.venv/bin/python scripts/displacement.py \
  --input data/displacement/ORCL_vs_ADBE_2026-10-08.json \
  --out docs/reports/displacement/ORCL_vs_ADBE_2026-10-08.md --verify
```

`--verify` regenerates the memo from the input and exits non-zero unless the
file is byte-identical. Output is deterministic (no timestamps other than the
input's `as_of`), so an unchanged input always reproduces the memo.
