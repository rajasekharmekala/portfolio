# Run Protocol (binding for every workflow and skill)

This protocol exists because earlier runs leaked state into later ones: prior-day ledgers, prior-day research,
and hardcoded dates produced reports that looked current but were not. These rules apply to every run.

## 1. Run directory (isolation)

Create a fresh, private directory at the start of every run. Never reuse one.

```bash
RUN_DIR="$(mktemp -d "${TMPDIR:-/tmp}/portfolio-<MKT>-<YYYY-MM-DD>-XXXX")"
mkdir -p "$RUN_DIR/cache" "$RUN_DIR/inputs" "$RUN_DIR/work"
```

- `<RUN_DIR>` is outside the repository. It is the only place for ledgers, research records, drafts, and scratch code.
- A run must never read from, or write derived output to, any other run directory.
- Pass `--run-dir "<RUN_DIR>"` to every `scripts/market_facts.py` build.

## 2. Inputs and manifest

- Copy the portfolio workbooks needed for this run (holdings, watchlist, shortlist) into `<RUN_DIR>/inputs/` and record their SHA-256 in the manifest. Work from the copies, not the originals.
- Write `<RUN_DIR>/manifest.json` at start with: market, session date, start time (ISO 8601 with timezone), input file hashes, and the ledger and research paths. Update it with output paths and the validation result at the end.

## 3. What may carry over between runs

Only the user's own state may carry over: holdings, watchlist, shortlist, and option positions. These are read from the workbooks in `sheets/`, `watchlist/`, and `shortlist/`.

These may NOT carry over: ledgers (`facts_*.json`), research records, prior report HTML, prior screen results, or any cached web result. Prior reports may be cited as history in a report, but never used as a data source for the current run.

## 4. Freshness

- The ledger's `asof` must equal the session date. `market_facts.py` exits non-zero if the benchmark's last bar is on another date. Do not rename, copy, or relabel a ledger. If the build fails for staleness, wait and retry; if it still fails, stop and report.
- Every web-sourced value needs `source_url`, `as_of` (the date the value describes), and `retrieved_at` (ISO 8601 time of retrieval). A value whose `as_of` is not the session date must be labeled as prior-session in the report.
- Never fall back to "latest file" lookup. Every file path is explicit.
- Never use the system date as a stand-in for the session date. Use the market's session date (ET for US, IST for India).

## 5. Outputs and cleanup

- Only final artifacts leave the run: the report HTML, the updated watchlist/shortlist/holdings workbooks, and the email. Everything else stays in `<RUN_DIR>`.
- After the validation gate passes and artifacts are saved, delete the run directory: `rm -rf "$RUN_DIR"`.
- If the run fails, keep `<RUN_DIR>` and report its path so the failure can be inspected. Do not delete it.

## 6. Publication (GitHub Pages)

- Reports are published only by copying a validated report into `docs/reports/` and regenerating `docs/index.html`.
- Publication is an explicit user decision per repository. Reports contain personal holdings. Do not publish to a public repository or Pages site without the user's explicit approval.
- `docs/` must contain only published reports and their index. Never copy workbooks, ledgers, research files, or `.env` into `docs/`.
- All links inside published pages must be relative. Do not embed absolute local paths such as `/Users/...` or `file://`.
