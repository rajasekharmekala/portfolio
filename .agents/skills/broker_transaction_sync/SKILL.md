---
name: broker_transaction_sync
description: >-
  Rebuild a broker's transaction log (Zerodha IN; Schwab and Robinhood US) from downloaded trade history and statements, reconcile it against the live holdings and cash, validate it, and commit it. Use when the user says the holdings are out of date, asks to sync or import broker transactions, or supplies new Tradebook, activity or statement files.
---

> **Scope.** Writes only `data/accounts/<MKT>/<account>.transactions.jsonl` and, when a held symbol is missing, `data/metadata/symbols.json`. It never edits the holdings view, reports or options state. Format rules are in `../_shared/DATA_LAYER.md`; the routine for a single trade is in `../_shared/HOLDINGS_UPDATE.md`. This skill is for rebuilding a whole account from history.

## 0. Rules that override everything else

- Never read `.env` or any credentials file. Never copy cookies, session data or passwords out of a browser profile.
- Never log in on the user's behalf. Browser automation is allowed only in a separate, automation-only Chromium profile that the user logs into themselves (for example, `--remote-debugging-port` with a temp `--user-data-dir`). Stop that browser when finished and delete its profile directory.
- Do not invent cost, quantity, strategy bucket or exchange. Ask the user for anything missing.
- Do not commit or push without explicit user approval.

## 1. Inputs

| Broker | Preferred source | Notes |
|---|---|---|
| Zerodha (IN) | Console → Reports → Tradebook, one CSV per financial year | Export each FY separately. Full history requires the earliest FY. Holdings snapshot: Console → Holdings. Funds: Console → Funds → Overview (withdrawable balance). |
| Schwab (US) | Transactions CSV (`Date, Action, Symbol, Description, Quantity, Price, Fees & Comm, Amount`) | Covers the full history in one file when the export starts at the account opening. |
| Robinhood (US) | Activity CSV (`Activity Date ... Trans Code, Quantity, Price, Amount`) plus monthly statement PDFs | The CSV may stop before the latest month. Use the statements for the gap. Options (`BTO`/`STC`) are not stock transactions. |

Ask the user to place every file in one folder (for example `~/Downloads/<broker>/`). Check for duplicates first: Robinhood's dividend-only CSV was a subset of the activity CSV.

## 2. Parse and normalise

Sort by date, then by execution time or line order. Use the trade date for `as of` rows.

- **Zerodha:** Map `symbol` to the repo symbol used in `symbols.json`. Quantities are decimals with `.000000`; convert to int when whole. Amount = quantity × price (Tradebook has no fees; say so in the report). Watch for symbol renames (for example `ORIANA` → `ORIANA-SM`) and bonus, split or demerger legs that are absent from the export. Infer them only when live holdings confirm the quantities, and label the line as inferred.
- **Schwab:** Buy `amount` = −`Amount` (includes fees). Sell `amount` = `Amount` (net proceeds). Reverse split and stock split rows carry quantity only. Journals, dividends and interest → `cash`. ADR fees and foreign tax → `fee` with a positive amount.
- **Robinhood:** Parse `(…)` as negative. Buy `amount` = −`Amount`. Sell `amount` = `Amount`. `ACH`, `RTP`, `CDIV`, `INT`, `SLIP` → `cash`. `GOLD` → `fee`. Ignore `SXCH` symbol-change pairs for closed names. Statement `Buy`/`Sell` lines look like `CUSIP: … SYM Margin Buy MM/DD/YYYY qty $price $amount`.

Every line needs the fields the schema requires, plus `source` and `note`. Keep the field order of the existing file.

## 3. Scope rule

Only trades for symbols that have an entry in `data/metadata/symbols.json` are itemised. Each other closed position becomes one `cash` line with the net cash of its trades, dated on its last trade, and a note saying the trades were not recorded. Ask the user for a strategy bucket before adding metadata for a symbol that is still held. Options contracts stay in `data/options/<MKT>.json`; their net premiums go into one aggregated cash line.

## 4. Reconcile before writing

1. **Cash:** Cumulative cash through each month-end must match the statement balance, plus any constant offset. A constant offset is an opening balance. Record it on the first date as `cash` with the note `implied opening balance`. Do not hide it in a balancing entry.
2. **Holdings:** Replayed quantities must match the latest live holdings or statement positions. Lent shares count as held. Fractional shares must match to the decimal.
3. **Costs:** Compare the replayed cost basis with the live cost column. Differences from fees alone should be small. Report any larger gap rather than forcing a match.
4. **Snapshot conflicts:** If the existing log lists a symbol that no transaction supports, ask the user which source to trust. Do not keep an unsupported position.

Use the newest statement for the end date. State any activity after the last file as a gap.

## 5. Write, validate, check

1. Write the new log in date order, one JSON object per line.
2. `.venv/bin/python scripts/data_layer.py --market <MKT> --validate` must print `RESULT: PASS`.
3. `.venv/bin/python scripts/data_layer.py --market <MKT> --positions` must match step 4.
4. `git status` must show only the transaction logs and, if changed, `symbols.json`.

## 6. Clean up

- Delete scratch files you created: `/tmp` text dumps, backups, temporary scripts, browser profiles and logs.
- Keep the user's downloaded exports unless the user asks you to remove them.
- Do not touch unrelated untracked files in the repository.

## 7. Commit (only with approval)

Stage only the transaction logs and `symbols.json`. Name the market and the date range in the commit message, and include the Co-authored-by trailer.

```text
Rebuild <broker> transactions through <YYYY-MM-DD>

Source: <broker export names>. Reconciled quantities and cash to <statement or snapshot>.

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
```

## 8. Report to the user

Give these in plain terms:

- Positions that match, and any that do not.
- Cost differences by symbol, in currency.
- Cash result and any constant offset.
- Closed names summarised, options summarised, and assumptions (fees, exchange codes, inferred splits).
- What still needs the user: missing files, strategy buckets, or which source to trust.
