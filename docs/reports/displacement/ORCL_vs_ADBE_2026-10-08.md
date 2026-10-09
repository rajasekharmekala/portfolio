# Displacement memo - ORCL vs ADBE

**As of:** 2026-10-08  |  **Market:** US  |  **Advisory only - no orders are generated.**

## Recommendation: **HOLD**

ADBE's base return of +12.0% is 63.4pp below ORCL's +75.4% (net of the +0.14% cost drag the edge is -63.5%), and its momentum gate is NO_MOMENTUM. There is no edge in selling ORCL to buy ADBE.

## Side by side on the same scorecard

| | ORCL (holding) | ADBE (candidate) |
|---|---|---|
| Name | Oracle Corporation | Adobe Inc. |
| Price (2026-10-08) | $135.69 | $241.05 |
| Bucket | CORE_ALPHA | TACTICAL_MOMENTUM |
| Theme | Enterprise software & cloud | Creative & document software |
| Weight in market portfolio | 6.62% | 0% (proposed 4.0%) |
| Momentum gate (frozen snapshot) | NO_MOMENTUM | NO_MOMENTUM |
| Distance to support | 3.27 ATR | 3.41 ATR |
| Scorecard (quality / valuation / momentum) | 70 / 65 / 20 | 85 / 78 / 20 |
| Expected 12-mo return (low / base / high) | -18.93% / +75.38% / +194.79% | -19.10% / +11.98% / +36.94% |

## Expected return of each, with its range

- **ORCL (holding):** base +75.38% over 12 months
  (range -18.93% to +194.79%).
  Source: price and gate: frozen facts ledger scripts/.cache/facts_US_2026-10-08.json, momentum_gate run 2026-10-08; expected return: analyst target low $110 / average $237.97 / high $400 vs $135.69 from stockanalysis.com/stocks/ORCL/forecast/ (retrieved 2026-10-08); weight: 35 shares, $4,858.62 of $73,423.49 known US market value
- **ADBE (candidate):** base +11.98% over 12 months
  (range -19.10% to +36.94%).
  Source: docs/blogs/ADBE_dossier.html (2026-10-08): scenario prices bear $195 / base $270 / bull $330 vs $241.05; gate: momentum_gate run on the same frozen ledger; proposed 4.0% = TIER_2 of .agents/config/scoring.json

## Transaction costs

Round trip of 14 bps (sell 2 + buy
2 + slippage 5 on each leg) on
the $4,858.62 notional = **$6.80**, a
+0.14% drag. Tax note: US accounts: the sell leg is subject to capital-gains tax if the lot is long-term; tax is not included in the bps figure

## Portfolio caps and theme exposure

- 15% single-name hard cap: no trade, so no cap is touched (proposed ADBE size +4.0% is within the 15% cap).
- Tactical band 50-65%: unchanged (no trade).
- Theme exposure: unchanged (no trade).

## The single condition that would reverse this advice

Re-run this memo when ADBE's momentum gate verdict becomes IN_MOMENTUM or ENTERING_MOMENTUM and its 12-month base expected return is at least 5.0pp above ORCL's current base of +75.4%.

---
Stored inputs: `/Users/mereddy/Desktop/github/portfolio/data/displacement/ORCL_vs_ADBE_2026-10-08.json`. Numbers above are
computed from those inputs by `scripts/displacement.py`; re-run with `--verify`
to reproduce. You make the decision and record it in the decision log
(`data/decisions/`).
