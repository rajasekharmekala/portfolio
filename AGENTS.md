# Portfolio Repository Agent Instructions

This file defines binding repo-wide rules, workflow routing, and mandatory derived-artifact chains so that data updates, research reports, and the public GitHub Pages portal (`docs/index.html`) never fall out of sync.

---

## 1. Environment, Safety & Concurrency (Binding)

- **Python environment:** Always run Python commands through `.venv/bin/python` from the repo root. Never use bare `python3`, `pip`, or a system Python.
- **Credentials & browser safety:** Never read `.env` or any credentials file. Never copy cookies, session data, or passwords out of a browser profile, and never log in on the user's behalf. Live browser inspection/automation (via `macos-browser-automation`) is permitted in the user's signed-in Chrome profile **strictly for authenticated broker account state** (Zerodha/Schwab/Robinhood transaction syncs, open options book checks, and Zerodha GTT alerts) — never use Robinhood Chrome or PowerBI scraping for general market data or multi-stock scanning.
- **Market data source split:** Use TradingView's headless batch scanner (`scripts/stage2_scanner.py --source tradingview`, `scripts/stock_snapshot.py`, `scripts/options_snapshot.py`) for live/same-day prices, volume, technicals, and Sector Stage 2 breadth. Keep `yfinance` for multi-year historical OHLCV bar series (`scripts/build_performance.py`, `scripts/market_facts.py`), with TradingView latest-close overlay in `build_performance.py` so XIRR/NAV stays current on the latest session.
- **No fabrication:** Never invent costs, quantities, strategy buckets, exchanges, prices, or timestamps. Ask the user for missing inputs (or use verified shortlist metadata where already defined).
- **Concurrent workflow runs (`RUN_PROTOCOL.md` §8):** Multi-step research workflows (`company_report`, `dossier_refresh`, `portfolio_audit`, `options_desk`) may overlap:
  1. Start every workflow run with `.venv/bin/python scripts/run_session.py start --workflow <w> --market <MKT>` to create an isolated git worktree + branch.
  2. Claim companies with `scripts/run_claims.py` before researching.
  3. Reach `main` only through `scripts/publish_run.py`. Never edit, pull, or merge in the shared checkout during a workflow run, and never touch another run's worktree or files. Report a refused singleton run or publish conflict; never bypass it.
- **Publication authorization:**
  - Newly completed **research workflow** outputs (`company_report`, `dossier_refresh`, `portfolio_audit`, `options_desk`) are pre-authorized to commit and push to `main` via `scripts/publish_run.py` once all quality gates pass, letting the worktree and branch clean up automatically after push.
  - **Broker transaction syncs** and manual ledger edits require explicit user approval before committing and pushing.
- **Sector & universe policy — ETF-only trend-following sectors (IN & US, Binding):** Never screen, shortlist, underwrite (`company_report` / `dossier_refresh`), or recommend buying individual stocks in **Banking, Insurance & Pure Financials** (banks, insurers, reinsurers, NBFCs, rating agencies), **Energy (Oil & Gas) & Metals/Mining**, or **Utilities & REITs** in either India or the US. *(Individual stock picking remains explicitly allowed in Pharma, Biotech, Healthcare, Airlines, Tech/Semis, Industrials, and Consumer/Retail.)* **Do not avoid these ETF-only sectors**—actively evaluate their **broad index or sector ETFs** (US: `XLF`, `KIE`, `XLE`, `XME`/`GDX`, `XLU`, `XLRE`; IN: `BANKBEES`, Nifty Financial Services, Nifty Energy/Metals such as `METALIETF`, Nifty Infra/REITs) for portfolio reallocation and buys during every `portfolio_audit` whenever both the broad market index and the sector ETF are aligned in a confirmed Stage 2 uptrend, and exit systematically when the trend breaks.

---

## 2. User Intent → Workflow & Skill Routing

When a user request matches one of the intents below, read and follow the corresponding skill/workflow **and** execute its downstream derived-artifact chain (§3):

| User intent / trigger | Skill / Workflow to follow | Primary files modified |
|---|---|---|
| Sync or update broker trades, cash, dividends, splits, or balances across accounts (Zerodha IN, Charles Schwab US, Robinhood US) | `.agents/skills/broker_transaction_sync/SKILL.md` (single ad-hoc trade: `.agents/skills/_shared/HOLDINGS_UPDATE.md`) | `data/accounts/<MKT>/*.transactions.jsonl`, `data/metadata/symbols.json` + **§3 Transaction Sync Chain** |
| Run a full portfolio audit & allocation review (IN or US) | `.agents/workflows/portfolio_audit.md` & `.agents/skills/portfolio_audit/SKILL.md` | `docs/reports/<MKT>_Portfolio_Audit.html` (+ PDF) + **§3 Report & Performance Chain** |
| Write a new single-company deep-dive dossier (or next shortlist candidate) | `.agents/workflows/company_report.md` & `.agents/skills/company_report/SKILL.md` | `docs/blogs/<MKT>/<SYMBOL>_dossier.html` (+ PDF), `data/dossiers/<MKT>/<SYMBOL>/`, `data/shortlist/<MKT>.json`, `data/discarded/<MKT>.json` + **§3 Report Chain** |
| Refresh / re-underwrite an existing published dossier | `.agents/workflows/dossier_refresh.md` & `.agents/skills/dossier_refresh/SKILL.md` | `docs/blogs/<MKT>/<SYMBOL>_dossier.html` (+ PDF), `data/dossiers/<MKT>/<SYMBOL>/`, `data/shortlist/<MKT>.json`, `data/discarded/<MKT>.json` + **§3 Report Chain** |
| Audit open options, scan call-convexity/LEAPS, or update `data/options/<MKT>.json` | `.agents/workflows/options_desk.md` & `.agents/skills/options_desk/SKILL.md` | `data/options/<MKT>.json`, `docs/reports/<MKT>_Options_Desk.html` + **§3 Options / Performance Chain** |
| Set up, modify, or replace Zerodha Kite GTT buy/stop alerts | `.agents/skills/zerodha_gtt_setup/SKILL.md` | Live Chrome Kite GTT session (read-only on repo files) |
| Refresh homepage performance, P&L timelines, or XIRR (`index.html#performance`) | Direct script run (see §3) | `docs/portal-performance.json` |
| Refresh homepage catalog, held badges, or shortlist/discarded queues (`index.html`) | Direct script run (see §3) | `docs/portal-data.json`, `docs/portal-updates.json` |

---

## 3. Mandatory Derived-Artifact Chains (Never Leave the Portal Stale)

This repository deploys `docs/` directly to GitHub Pages (`https://rajasekharmekala.github.io/portfolio/`). There are **no GitHub Actions** that auto-rebuild derived files on push; every derived artifact must be rebuilt locally before committing. This section supersedes any older narrow-scope note in individual skills (such as `broker_transaction_sync` stating not to update holdings views or portal JSON).

### A. After ANY change to `data/accounts/<MKT>/*.transactions.jsonl` or `data/metadata/symbols.json`
Run **all** of these steps for each modified market `<MKT>` before committing:
1. **Validate ledger & inspect positions:**
   ```bash
   .venv/bin/python scripts/data_layer.py --market <MKT> --validate
   .venv/bin/python scripts/data_layer.py --market <MKT> --positions
   ```
   (`--validate` must print `RESULT: PASS`.)
2. **Rebuild readable holdings views (`data/views/holdings_<MKT>.md`):**
   ```bash
   .venv/bin/python scripts/data_layer.py --market <MKT> --view
   ```
3. **Rebuild public homepage catalog (`docs/portal-data.json`, `docs/portal-updates.json`):**
   ```bash
   .venv/bin/python scripts/portal_publish.py
   ```
   *(Updates held-ticker badges/filters and queues on `docs/index.html`; quantities and cash are never published in `portal-data.json`.)*
4. **Rebuild performance, P&L timelines & XIRR (`docs/portal-performance.json`):**
   ```bash
   .venv/bin/python scripts/build_performance.py --refresh
   ```
   *(Powers `docs/index.html#performance` across all profiles.)*
5. **Stage and commit together** (after explicit user approval for broker syncs): transaction logs, `data/metadata/symbols.json` (if changed), `data/views/holdings_<MKT>.md`, `docs/portal-data.json`, `docs/portal-updates.json`, and `docs/portal-performance.json`.

### B. After ANY change to `data/options/<MKT>.json`
1. `.venv/bin/python scripts/data_layer.py --market <MKT> --validate`
2. `.venv/bin/python scripts/build_performance.py --refresh` *(open US options mark-to-market is included in `docs/portal-performance.json`)*
3. `.venv/bin/python scripts/portal_publish.py`

### C. After ANY change to `data/shortlist/<MKT>.json` or `data/discarded/<MKT>.json`
1. `.venv/bin/python scripts/data_layer.py --market <MKT> --validate`
2. `.venv/bin/python scripts/validate_data.py`
3. `.venv/bin/python scripts/portal_publish.py` *(refreshes homepage queues in `docs/portal-data.json`)*

### D. After completing a `portfolio_audit` workflow
In addition to the standard report publication steps in §4 and `scripts/publish_run.py`, run:
```bash
.venv/bin/python scripts/build_performance.py --refresh
```
so `docs/portal-performance.json` (`index.html#performance`) reflects the same session and holdings as the newly published audit.

---

## 4. Portfolio Research Generation & Report Design (Binding)

- Every newly generated report or dossier must use the Research Desk design matching `docs/index.html`. Read `.agents/skills/_shared/REPORT_DESIGN.md`. Assemble the complete research body with `scripts/assemble_report.py`; never copy an old published HTML shell or follow an older Wikipedia head/style template in a skill. This rule supersedes old presentation instructions only, not analysis, sourcing, methodology, or quality gates.
- Pass `--market IN/US`, `--kind report/dossier`, `--workflow`, and `--as-of`. The actual generation timestamp is embedded in the header in `America/Los_Angeles` time (PDT/PST); the verified market-session cutoff is separate. New workflow outputs use stable filenames; dossier names remain `SYMBOL_dossier.html`. Do not remove or truncate any research, table, citation, or reference for the design.
- Newly completed workflows must pass the modern-layout check in `scripts/portal_publish.py` in addition to all existing research-quality checks (`readability_check.py`, `citation_check.py`, `review_packet.py` + `report_reviewer`, and `red_team` for dossiers/audits). Never bypass the check. Catalog rebuilds may still include historical reports unchanged. Use `--layout-only` solely for explicitly requested presentation updates to existing research; never call those new research or invent their original generation timestamp.
- Do not change unrelated user work or publish fresh research without its quality gates.
