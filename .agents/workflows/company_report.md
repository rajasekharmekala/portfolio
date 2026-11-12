---
description: Single-company underwriting for a named ticker or the next active-watchlist candidate. Produces a dossier and PDF with a current holding action, alerts, and cash/shortlist/outside redeployment analysis.
---

# Company Report Workflow (Market: `<MKT>`)

Read `_COMMON.md` first and follow `.agents/skills/company_report/SKILL.md`.

**Input:** market `<MKT>` and optionally a specific ticker. With no ticker, claim the next eligible active-watchlist candidate. A named ticker may be held, shortlisted, active-watchlisted, or a researched outside opportunity.

## 1. Start an isolated run and claim one company

```bash
.venv/bin/python scripts/run_session.py start --workflow company_report --market <MKT>
```

Work only in the printed worktree. Create the private `RUN_DIR`, resolve the latest completed verified session, check inputs, and copy/hash the holdings, watchlist, shortlist, and options inputs per `_COMMON.md`.

Claim exactly one name:

```bash
.venv/bin/python scripts/run_claims.py batch --workflow company_report --market <MKT> --run-id <run_id> --size 1
```

For an explicitly requested symbol, use `run_claims.py names --workflow company_report --market <MKT> --run-id <run_id> <SYMBOL>` instead. Record the claim output and work only on the claimed name.

## 2. Pass 1 — Price-blind fundamental audit (`ch01..ch06` + `business_quality.json`)

1. Pull only price-blind operating and financial statement data with `stock_snapshot.py --market <MKT> --symbols <SYMBOL> --blind-only --out "<RUN_DIR>/cache/blind_<MKT>_<SYMBOL>.json"`. Do **not** read watchlist verdict notes, shortlist targets, or portfolio holdings yet.
2. Spawn an isolated Pass 1 subagent to research primary filings, concalls, and two-sided Bull + Skeptic evidence, author `chapters/ch01.json..ch06.json` + `business_quality.json`, and pass `scripts/dossier_schema.py --check-blind-pass "<RUN_DIR>/work/<SYMBOL>"`.

## 3. Pass 2 — Market ledger, valuation, tape & synthesis (`ch07..ch09` -> `spine.json` -> `ch00`)

1. Build the same-session facts ledger (`market_facts.py`), `stage2_scanner.py`, and full `stock_snapshot.py` for the target company, listed peers from Chapters 4/7, active shortlist candidates, and current holdings.
2. Author `ch07.json` (Reverse DCF & `peer_snapshot_table`), `ch08.json` (Stage 2 technicals), and `ch09.json` (Bull vs. Bear steelman, probability-weighted outcomes, distinct new-capital verdict and current-holding action, share-exact advisory alerts, and 100%-reconciled allocation across `SHORTLIST`, `OUTSIDE`, and `CASH`), then derive `spine.json` and `ch00.json` (`id: "ch-0"`).
3. Compile `docs/blogs/<MKT>/<SYMBOL>_dossier.html`, `<SYMBOL>_book.pdf`, and persistent canonical spec `data/dossiers/<MKT>/<SYMBOL>/` via `scripts/dossier_builder_template.py`.

## 4. Review, deterministic pipeline sync (`Watchlist <-> Shortlist` / `Discard`) & publish

Run `readability_check.py`, `citation_check.py`, and Stage 9 `review_packet.py build --kind dossier` + `report_reviewer` + `red_team` per `_COMMON.md` and `REVIEWER_OPERATIONS.md`. Then run `scripts/sync_dossier_pipeline.py` (never touching `data/accounts/` holdings), `scripts/data_layer.py --market <MKT> --validate`, and `scripts/validate_data.py`, and publish through `scripts/publish_run.py`. Company dossiers are not emailed.
