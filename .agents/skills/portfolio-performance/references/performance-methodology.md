# Method and input format

## P&L definitions

Use the repository's average-cost replay for stock transactions.

- **Overall realized P&L:** net proceeds from sells minus the average cost of the shares sold, accumulated through the as-of date.
- **Current unrealized P&L:** current market value of open shares minus their remaining recorded cost basis.
- **Window realized P&L:** sale proceeds minus the carrying value of sold shares. Shares held at the start are carried at their start-date close; shares bought inside the window are carried at purchase cost.
- **Window unrealized change:** ending market value minus the remaining carried value. This pairs with window realized P&L so price gains that existed before the window are not counted again when shares are sold.
- **Income and fees:** add identified dividends, interest, and stock-lending income; subtract explicit fee records. Do not count cash transfers, journals, opening balances, or balancing entries as investment profit.
- **Net P&L:** realized P&L + unrealized P&L/change + identified income − explicit fees.

This is a transaction-based P&L, not a tax report or a time-weighted return. If trade amounts are gross of charges, fee rows are incomplete, closed names are summarized as net cash, or a transaction range is missing, state the effect and do not imply exact lifetime account return.

## Benchmark

Use SPY's Yahoo Finance adjusted close as a dividend-inclusive S&P 500 total-return proxy. Compute the proxy return from the last available adjusted close on or before each window start to the last adjusted close on or before the as-of date. For “overall,” use the earliest complete transaction date for that account.

Show the S&P 500 return as a separate percentage reference. It is not a valid excess-return comparison when external contributions/withdrawals are incomplete, option valuations are absent, account cash is unreconciled, or the account value series is not flow-adjusted. Do not subtract it from account P&L or label the difference “alpha” in those cases.

## Snapshot JSON

Pass a JSON file with current broker snapshot values. `positions_mv` holds per-symbol market values in the account currency, not prices. `cash` is the broker's cash balance. Optional option fields are separate.

```json
{
  "as_of": "2026-11-06",
  "accounts": {
    "Zerodha": {
      "market": "IN",
      "currency": "INR",
      "transaction_log": "data/accounts/IN/zerodha.transactions.jsonl",
      "cash": 0,
      "positions_mv": {"ABC": 12500.0},
      "source": "Broker holdings page, 2026-11-06"
    },
    "Robinhood": {
      "market": "US",
      "currency": "USD",
      "transaction_log": "data/accounts/US/robinhood.transactions.jsonl",
      "cash": 0,
      "positions_mv": {"XYZ": 500.0},
      "options_mv": null,
      "options_cost_basis": null,
      "source": "Broker investing page, 2026-11-06"
    }
  }
}
```

An absolute transaction-log path is also accepted when the logs are in isolated worktrees. If the broker snapshot gives only position quantities and live prices, calculate market values before building this file. Record unavailable prices in a `notes` field rather than filling them with a guessed value.

## Run the helper

From the portfolio repository:

```bash
.venv/bin/python .agents/skills/portfolio-performance/scripts/compute_performance.py \
  --root . --snapshot /path/to/current-snapshot.json
```

The helper prints JSON with account P&L components, 1-year and 6-month P&L, benchmark reference returns, current values, and missing-price/record warnings. It fetches daily historical closes with `yfinance`; NSE symbols try `.NS`, then `.BO`. Window components are incomplete when any starting holding lacks a historical mark; the output lists missing marks. Add exact historical overrides to `historical_price_overrides` in the snapshot when a reliable source has a price missing from Yahoo:

```json
"historical_price_overrides": {
  "RNITAI": {"2026-05-06": 74.83}
}
```

Keep source attribution for overrides in the visualization's source note. Do not store credentials, cookies, or broker session data in the snapshot.

Split rows in the portfolio transaction logs may encode bonus shares as `quantity`, and a note may state that the old ticker became a new ticker. The replay treats quantity as added shares and transfers the old ticker's shares and basis when that rename is explicitly recorded. Inspect warnings for any transaction history that does not replay cleanly.
