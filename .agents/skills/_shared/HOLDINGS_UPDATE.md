# Keeping the holdings current

Holdings are recorded as transactions, one JSON line per trade. The run replays the log to get quantities and cost. Broker snapshots are no longer the source; they are only a cross-check if you want one.

## When you trade

1. Append one line to the account's log: `data/accounts/US/schwab.transactions.jsonl`, `data/accounts/US/robinhood.transactions.jsonl`, or `data/accounts/IN/zerodha.transactions.jsonl`. Use the format in `DATA_LAYER.md`. A buy's `amount` is the total cost including fees; a sell's `amount` is the proceeds net of fees.
2. If the symbol is new, add it to `data/metadata/symbols.json` under its market, with its company name and strategy bucket.
3. Run `.venv/bin/python scripts/data_layer.py --market US --validate` (or `IN`). It must print `RESULT: PASS`.
4. Commit the log with the trade. The git history is the audit trail.

## Positions with unknown cost

A position with `"amount": null` in its opening line has no known cost. The report shows its cost as unknown and does not estimate it. To fix this, find the purchase in the broker's history and append a `buy` record with its amount. Do not edit the opening line.

The current US openings for GOOGL, BE, and ANET have no cost, and the Schwab snapshot showed "—" for them. The Robinhood openings for BE and ANET carry costs derived from gain and loss, and those derivations are recorded in the `note` field.

## Checking

- `.venv/bin/python scripts/data_layer.py --market <MKT> --positions` prints each account's replayed positions and cash.
- `.venv/bin/python scripts/data_layer.py --market <MKT> --view` writes `data/views/holdings_<MKT>.md`, a readable table for GitHub.
- `.venv/bin/python scripts/market_facts.py --market <MKT> --check-inputs --run-dir "<RUN_DIR>"` confirms every declared source is readable.

## Options

The options file `data/options/<MKT>.json` is a state file for now: one record per open contract with its current value. Add a record when you open a position, and remove or mark it closed when you close one. Option transactions will move to a log when the options workflow is next revised.
