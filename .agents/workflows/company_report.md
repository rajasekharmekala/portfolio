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

## 2. Build fresh market and portfolio evidence

1. Build the same-session facts ledger with `market_facts.py`; it writes the consolidated positions ledger including shares, broker/account split, cost basis, current market value, P&L, cash, options value, and NAV.
2. Run `stage2_scanner.py` into `<RUN_DIR>/cache/stage2_<MKT>_<date>.json` (IN `--min-mcap 1000`; US `--min-mcap 1.0`).
3. Run `stock_snapshot.py` for the target company, all current holdings, and all active shortlist candidates against that fresh dashboard. Research any outside peers found during the dossier and run a fresh snapshot for them before recommending a price or entry condition.
4. Use current broker records only for holdings and the active shortlist only for shortlisted candidates. Keep cash as an explicit candidate destination.

## 3. Underwrite, decide, and author the dossier

Follow the evidence-first sequence in `company_report/SKILL.md`: Chapters 1–8, then Chapter 9, then derive the spine and Prologue. Chapter 9 must include:

- a distinct new-capital verdict and current-holding action (or `NOT_HELD`);
- actual holdings/cost/value/weight from the positions ledger when held;
- exact trim/exit/stop/entry alerts and conditions, clearly labeled advisory;
- a capital allocation plan that totals 100% across active shortlist candidates, researched outside candidates, and cash. Cash may receive the entire amount when no equity entry clears the gates.

Compile `docs/blogs/<MKT>/<SYMBOL>_dossier.html` and `<SYMBOL>_book.pdf` with the positions ledger, facts ledger, stock snapshots, and active shortlist inputs. There is no separate watchlist-summary report.

## 4. Update records, validate, review, and publish

Update the claimed watchlist record and the active shortlist only when supported by the final dossier verdict. Run data validation, dossier schema/compiler validation, readability and citation checks, modern-layout validation, and the dossier reviewer + conditional red-team process per `_COMMON.md` and `REVIEWER_OPERATIONS.md`.

Publish only the dossier HTML and PDF plus the relevant watchlist/shortlist record changes through `scripts/publish_run.py`. Do not create a second batch report or run a second review cycle on a wrapper. Company dossiers are not emailed.
