# Data Layer (how the portfolio is stored and written)

Holdings, watchlists, shortlists, options, and metadata live in JSON under `data/`. Excel workbooks are retired. Nothing is read or written by cell position.

## Where things are

| What | Where | Written by |
|---|---|---|
| Holdings (per account) | `data/accounts/<MKT>/<account>.transactions.jsonl` | the user, when a trade happens (one JSON line per transaction) |
| Strategy bucket and name per symbol | `data/metadata/symbols.json` | the user, when a new name is bought |
| Watchlist (active and archive) | `data/watchlist/<MKT>.json` | the watchlist workflows |
| Shortlist (one array per sheet) | `data/shortlist/<MKT>.json` | the shortlist workflows |
| Options positions | `data/options/<MKT>.json` | the options workflow, and the user for new trades |
| Generated holdings view | `data/views/holdings_<MKT>.md` | `scripts/data_layer.py --view` (never edit) |

## Transactions

Each line of a transaction log is one JSON object:

```json
{"date": "2026-10-05", "type": "buy", "market": "US", "account": "Schwab", "symbol": "BE", "quantity": 2, "amount": 573.30, "source": "trade confirmation", "note": null}
```

Types: `opening` (position already held at the start of the log; amount may be null if the cost is unknown), `buy` (amount is total cost including fees), `sell` (amount is proceeds net of fees), `split` (quantity change, amount 0), `cash` (cash in or out; positive means in), `fee` (a charge that is not a trade).

Holdings are replayed with the average-cost method. A position whose cost is unknown keeps `cost_known: false`. Never fill an unknown cost with a guess; record the purchase when you have it.

## Editing records (watchlist, shortlist, options)

- Find the record by its `symbol` (or `underlying` for US options), then change only the fields you need. Never change field order or add fields that the schema does not use.
- Column names in older text map to JSON keys: lowercase the name and replace spaces and punctuation with underscores. For example, "Action Verdict" is `action_verdict`, "Deep Research Status" is `deep_research_stat`, and "Strategy Bucket" is `strategy_bucket`.
- The watchlist file has two arrays: `active` (names being researched or held as candidates) and `archive` (rejected names). Moving a name between them means moving the whole record.
- The shortlist file has one array per former sheet under `sheets`. The workflows read `sheets.Master_Shortlist` unless the skill says otherwise.
- After any edit, run `python3 scripts/data_layer.py --market <MKT> --validate`. It must print `RESULT: PASS` before the run continues.

## Where the workflows read from

The ledger reads all of these in one step, and the manifest records the hash of every file it read. Checks: `python3 scripts/market_facts.py --market <MKT> --check-inputs --run-dir "<RUN_DIR>"`.
