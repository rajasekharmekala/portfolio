# Portfolio Research System

A research and reporting system for two portfolios:

- **India (IN):** one Zerodha account, benchmarked to the Nifty 50 and the NSE 500.
- **United States (US):** two brokerage accounts (Charles Schwab and Robinhood) combined into one portfolio, benchmarked to the S&P 500 and the S&P 1500.

The system does four things. It records holdings as transactions. It builds a daily market facts ledger from public price data. It turns the ledger and the research into reports that a validator and an independent reviewer must approve. It publishes the approved reports as a static site.

Read this file first. Each section tells you what to do and where the detail lives.

---

## 1. Setup

You need Python 3.10 or later, and these packages:

```bash
pip install pandas yfinance openpyxl beautifulsoup4
```

`openpyxl` is only needed by the one-time migration script. `beautifulsoup4` is needed by the dossier portal builder.

Create a `.env` file in the repository root. It is gitignored. Never commit it.

```
GMAIL_USER=you@gmail.com
GMAIL_APP_PASSWORD=your-16-character-app-password
GMAIL_RECIPIENT=where-reports-are-sent@example.com
```

`GMAIL_APP_PASSWORD` is a Gmail app password, not your normal password. Create one in your Google account security settings.

Check that the setup works:

```bash
python3 scripts/data_layer.py --market US --validate
python3 scripts/data_layer.py --market IN --validate
```

Both should print `RESULT: PASS`.

---

## 2. Repository layout

```
.
├── README.md                   This file
├── data/                       The portfolio data. JSON only. Private.
│   ├── accounts/IN/            Zerodha transaction log (zerodha.transactions.jsonl)
│   ├── accounts/US/            Schwab and Robinhood transaction logs
│   ├── metadata/symbols.json   Company name, strategy bucket and mandate per symbol, by market
│   ├── watchlist/IN.json, US.json     Active candidates and archived (rejected) names
│   ├── shortlist/IN.json, US.json     Shortlist sheets, one array per sheet
│   ├── options/IN.json, US.json       Open option contracts
│   └── views/                  Generated readable tables (do not edit)
├── scripts/                    Python tools
│   ├── market_facts.py         Builds the daily facts ledger and fact pack for one market
│   ├── data_layer.py           Validates the data, replays positions, writes the holdings views
│   ├── validate_report.py      Pre-send gate for every report (structure, language, data)
│   ├── send_email.py           Sends a report by email
│   ├── build_dossier_portal.py Rebuilds the company dossier index
│   ├── serve_blogs.py          Serves the reports and dossiers on localhost:9050
│   ├── migrate_to_json.py      One-time migration from the Excel workbooks (historical)
│   └── config/aliases.json     Symbol aliases (version-controlled)
├── .agents/
│   ├── config/
│   │   ├── markets.json        Per-market parameters: screen, skills, output file names, email subjects
│   │   ├── portfolios.json     Which data files each market reads
│   │   └── reviewer.json       Reviewer model, passes and round limit
│   ├── workflows/             Step-by-step runs. Start here for a daily run.
│   │   ├── _COMMON.md          Rules that apply to every workflow
│   │   ├── market_intelligence.md, portfolio_audit.md, options_audit.md,
│   │   │   watchlist_to_shortlist.md, reject_to_watchlist.md
│   └── skills/                Analysis and writing rules, one folder per skill
│       ├── _shared/           Shared standards: run protocol, voice, palette, data layer,
│       │                      section drafting, holdings update, editorial standard
│       ├── report_reviewer/   The independent reviewer's rubric
│       └── market_intelligence, portfolio_audit, options_underwriting, company_report,
│           watchlist_shortlist_underwriting, archive_resurrection_review,
│           shortlist_capital_allocator   (each covers both markets)
├── googledrive/                Generated reports and dossiers, plus your research notes (gitignored)
│   ├── newsletters/            Daily reports and audits
│   ├── blogs/                  Company dossiers
│   └── transcripts/            Research transcripts
├── docs/                       The published site (GitHub Pages). See section 6.
└── Portfolio Research System/  Your investment rules and reference documents
```

---

## 3. Keeping the holdings current

Holdings are recorded as transactions. The system replays each account's log to work out quantities and average cost. You don't edit positions directly.

When you trade:

1. Append one JSON line to the account's log. Example for a US buy:

   ```json
   {"date": "2026-10-09", "type": "buy", "market": "US", "account": "Schwab", "symbol": "BE", "quantity": 2, "amount": 573.30, "source": "trade confirmation", "note": null}
   ```

   - `buy`: `amount` is the total cost including fees.
   - `sell`: `amount` is the proceeds after fees.
   - `split`: `quantity` is the change in shares, and `amount` is 0.
   - `cash`: positive for money in, negative for money out. `symbol` is `null`.
   - `fee`: a charge that isn't part of a trade. `symbol` may be `null`.

2. If the symbol is new, add it to `data/metadata/symbols.json` under its market, with its company name and strategy bucket.
3. Validate: `python3 scripts/data_layer.py --market US --validate`
4. Commit the change.

The full format is in `.agents/skills/_shared/DATA_LAYER.md`. The update routine is in `.agents/skills/_shared/HOLDINGS_UPDATE.md`.

**Unknown cost.** An opening position with `"amount": null` has no known cost. Reports show the cost as unknown and never estimate it. To fix it, find the original purchase and append a `buy` line. Don't edit the opening line.

**Watchlist, shortlist and options** are JSON records keyed by symbol. The workflows update them. You can edit them by hand too, but run the validator afterwards.

---

## 4. Running a daily report

Each report is a workflow file in `.agents/workflows/`. Give the workflow to your agent, with the market and the session date. For example:

> Run `.agents/workflows/market_intelligence.md` for market US on session date 2026-10-08.

The workflow sets the steps. The rules it refers to are in `_COMMON.md`. Every run follows the same pattern:

1. **Session date.** Use the market's last completed session, not today's system date. US: the last session before the 16:30 ET close. IN: the last session before the 15:30 IST close.
2. **Run directory.** Each run creates a private temporary directory. Nothing from an earlier run is read. Cleanup happens at the end.
3. **Input check.**
   ```bash
   python3 scripts/market_facts.py --market US --check-inputs --run-dir "$RUN_DIR"
   ```
4. **Facts ledger.** This is the only source for prices, averages, RSI, ATR and stages.
   ```bash
   python3 scripts/market_facts.py --market US --date 2026-10-08 --screen sp1500 --run-dir "$RUN_DIR"
   ```
   For IN, use `--market IN --screen nifty500`. If the output says `STALE DATA` or `HOLDINGS NOT CURRENT`, stop. Don't rename or copy an old ledger. Re-run once the source has updated. You can override a stale holding with `--allow-stale-holdings`, but the report must say why.
5. **Research.** Facts the ledger can't provide (flows, option walls, insider buying, company catalysts) come from web research through the `duck-duck-go` tools. Each result is recorded with its source URL and as-of date.
6. **Writing.** Reports are drafted section by section from the fact pack (`factpack_<MKT>_<date>.json`). Each section agent sees only the names it needs. The voice and layout rules are in `.agents/skills/_shared/REPORT_VOICE.md`, `REPORT_PALETTE.md` and `REPORT_EDITORIAL_STANDARD.md`.
7. **Partial check.** After each section:
   ```bash
   python3 scripts/validate_report.py --report "$RUN_DIR/work/sections/<id>.html" --kind market_intel --facts "$RUN_DIR/cache/facts_US_2026-10-08.json" --partial
   ```
8. **Full gate.** After assembling `report.html`:
   ```bash
   python3 scripts/validate_report.py --report "$RUN_DIR/report.html" --kind market_intel --facts "$RUN_DIR/cache/facts_US_2026-10-08.json"
   ```
   Use `--kind portfolio_audit` for audits and option reviews. The result must be `RESULT: PASS`. Don't lower a threshold to pass a report.
9. **Reviewer gate.** An independent agent reviews the report for source support, consistency and plain language. The reviewer's model is set in `.agents/config/reviewer.json`. A report can only be delivered with `APPROVE` from the reviewer and `RESULT: PASS` from the validator. At most two review rounds. If the report still isn't approved, nothing is delivered, and the run directory is kept for inspection.
10. **Delivery.**
    ```bash
    python3 scripts/send_email.py --report "googledrive/newsletters/US_Market_Intelligence_2026-10-08.html" --subject "Daily US Market Pulse | 2026-10-08 | S&P Uptrend"
    ```
    The recipient comes from `GMAIL_RECIPIENT`. The filename and subject for each market and report type are in `.agents/config/markets.json`.
11. **Publish (optional).** Copy the approved report into `docs/reports/` and regenerate `docs/index.html`. Then commit it yourself.
12. **Cleanup.** Delete the run directory once delivery is complete: `rm -rf "$RUN_DIR"`.

**Report types:**

| Workflow | What it produces |
|---|---|
| `market_intelligence.md` | Daily market briefing for one market: regime, sectors, Stage 2 and Stage 4 lists, tactical playbook |
| `portfolio_audit.md` | Audit of every holding, with actions and the reasons for them |
| `options_audit.md` | Review of open option contracts and setup ideas |
| `watchlist_to_shortlist.md` | Underwrites the next batch of watchlist names, writes a dossier for each |
| `reject_to_watchlist.md` | Re-examines the next batch of archived names for resurrection |

---

## 5. Reports for the US portfolio

The US portfolio is the combined total of the Schwab and Robinhood logs, plus the US options book. The audit reports:

- the total net worth across both accounts,
- the account split for each holding that is held in both,
- the cash in each account,
- the options value,
- any holding with no known cost, listed separately.

Net worth is the market value of the stocks and ETFs at the ledger close, plus cash, plus the options value.

---

## 6. Publishing to GitHub Pages

The `docs/` folder is the only folder GitHub Pages serves.

- `docs/reports/` holds only the latest version of each report. Publishing overwrites the file with the same name. Earlier versions are kept in git history.
- `docs/index.html` lists the files in `docs/reports/`. Regenerate it from the folder. Don't edit it by hand.
- `docs/.nojekyll` must stay, so Pages serves the files as they are.
- Only publish a report that passed the validator and the reviewer.

**Privacy.** The reports contain your holdings, position sizes and cash. Use a private repository, and enable Pages for it only if your plan allows private Pages. Before publishing anything to a public repository, make an explicit decision for that repository.

**Commit only what you intend.** `data/` contains your full financial history. It belongs in the private repository only. `.env`, `googledrive/` and the Excel workbooks are gitignored.

---

## 7. Viewing locally

```bash
python3 scripts/serve_blogs.py
```

Then open `http://localhost:9050/`. It serves the reports and dossiers from `googledrive/`.

---

## 8. Troubleshooting

| Message | Meaning and fix |
|---|---|
| `INPUT MISSING` | A data file named in `.agents/config/portfolios.json` is missing. Restore it or fix the path. |
| `INPUT SCHEMA` | A records file no longer has the expected structure. Check the JSON keys against `DATA_LAYER.md`. |
| `STALE DATA` | The benchmark has no bar for the session date yet. Wait and re-run. Don't relabel the ledger. |
| `HOLDINGS NOT CURRENT` | A held name has no price for the session date. Wait, or use `--allow-stale-holdings` and say why in the report. |
| `RESULT: FAIL` from `data_layer.py` | A transaction line is malformed or a sell has no position. Fix the line named in the error. |
| `PRICE MISMATCH` | A price in a report differs from the ledger close. Use the ledger value. |
| A position shows `cost unknown` | The opening line has no cost. Append a `buy` line once you have the purchase record. |
| `unclassified` symbol | A held symbol has no entry in `metadata/symbols.json`. Add one. |

---

## 9. Known limits and open items

- The daily build needs internet access for price data. The reports are only as current as the data source.
- Option positions are a state file, not a transaction log. Option history is not recorded yet.
- Some cost bases are not known yet. Current gaps are listed by `data_layer.py --positions` as `cost unknown`.
- The opening date for the Zerodha positions (2026-10-05) and the broker snapshots came from the source files, not from transactions. Add the real trade history when you have it.
- The reviewer gate depends on the model chosen in `reviewer.json`. Calibrate a model on a known-good report before relying on it.

---

## 10. History

Before the JSON data layer, holdings lived in Excel workbooks and broker markdown snapshots. Those files were migrated once by `scripts/migrate_to_json.py` and are now archived outside the repository. The old workflow files and skill folders for each market were merged into the current ones. Git history keeps the old versions.
