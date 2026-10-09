# Decision log

Every decision the system makes (buy, sell, hold, watch, no-action) is recorded
here in `decisions.json` with its thesis, expected return, invalidation, and
date, so that results can be compared with the benchmark at 3, 6 and 12
months.

## Record shape

```json
{
  "id": "YYYY-MM-DD_SYMBOL_SLUG",
  "date": "YYYY-MM-DD",
  "market": "US",
  "symbol": "ADBE",
  "benchmark": "SPY",
  "action": "WAIT_FOR_SUPPORT",
  "price_at_decision": 241.05,
  "benchmark_price_at_decision": 773.93,
  "thesis": "one paragraph, the reason for the decision",
  "expected_return_pct_12m": {"low": -19.1, "base": 11.98, "high": 36.94},
  "invalidation": "the condition that makes the decision wrong",
  "invalidation_price": 210.88,
  "status": "open",
  "prices": {"ADBE": {"YYYY-MM-DD": px}, "SPY": {"YYYY-MM-DD": px}}
}
```

## Commands

```
scripts/outcomes.py --init                 create the ledger
scripts/outcomes.py --add <file.json>      validate and append one record
scripts/outcomes.py --refresh <id>         store price bars (yfinance); the only network command
scripts/outcomes.py --report [id]          3/6/12-month rows vs benchmark, from stored prices only
```

Rules:

- `--report` never touches the network. It computes only from the bars stored
  in the record. A horizon whose target date has no stored bar yet is
  reported as `not reached`, not fetched.
- The stored bars are the audit trail: do not edit them after the fact. If a
  bar was stored wrong, add a corrected record and mark the old one
  `status: superseded`.
- Today's close may be seeded from the session's facts ledger when the price
  feed has not published the day's bar yet; say so in the run log.
