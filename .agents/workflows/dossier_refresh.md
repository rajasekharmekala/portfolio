---
description: Companion dossier refresh, assumption audit, blind-spot brainstorm, and Stage 2 stop/verdict update for a named ticker or the stalest published monograph.
---

# Companion Dossier Refresh Workflow (Market: `<MKT>`)

Read `_COMMON.md` first and follow `.agents/skills/dossier_refresh/SKILL.md`.

**Input:** market `<MKT>` and optionally a specific ticker that already has a published dossier (if none exists yet, delegate to `company_report.md`). With no ticker, claims the stalest published dossier across active holdings, shortlist, and watchlist.

## 1. Start an isolated worktree, claim one company & prepare the blind packet

```bash
.venv/bin/python scripts/run_session.py start --workflow dossier_refresh --market <MKT>
.venv/bin/python scripts/run_claims.py batch --workflow dossier_refresh --market <MKT> --run-id <run_id> --size 1
.venv/bin/python scripts/dossier_refresh.py prepare --market <MKT> --symbol <SYMBOL> --out-dir "<RUN_DIR>/work/<SYMBOL>"
.venv/bin/python scripts/stock_snapshot.py --market <MKT> --symbols <SYMBOL> --blind-only --out "<RUN_DIR>/cache/blind_<MKT>_<SYMBOL>.json"
```

(For an explicitly requested symbol, use `run_claims.py names --workflow dossier_refresh --market <MKT> --run-id <run_id> <SYMBOL>`.)

## 2. Pass 1 — Verdict-stripped assumption audit & blind-spot brainstorm (`ch01..ch06`)

Spawn an isolated Pass 1 subagent reading only `<RUN_DIR>/work/<SYMBOL>/blind_refresh_packet.md` and `blind_<MKT>_<SYMBOL>.json`:
1. Re-test baseline Chapters 1–6 claims/KPIs against all filings, concalls, insider trades, and competitor news since `prior_as_of`.
2. Brainstorm and verify `>= 2` omitted blind-spot vectors (concentration, footnote forensics, unit-economics friction, unlisted/global rivals, regulatory/FX, governance incentives) and directly patch the owning `chapters/ch01..ch06.json` + `business_quality.json`.
3. Write `refresh_audit.json` and gate before unlocking live prices:

```bash
.venv/bin/python scripts/dossier_refresh.py validate-audit --work-dir "<RUN_DIR>/work/<SYMBOL>"
```

## 3. Pass 2 — Valuation, Stage 2 technicals, stop-loss ratchet & compilation

1. Build same-session `market_facts.py`, `stage2_scanner.py`, and full `stock_snapshot.py` (target + peers + shortlist + holdings).
2. Author fresh `ch07.json`, `ch08.json`, `ch09.json`, `spine.json` (enforcing upward-only stop ratchet on held shares via `dossier_refresh.py check-ratchet`), and `ch00.json`.
3. Compile `docs/blogs/<MKT>/<SYMBOL>_dossier.html`, `<SYMBOL>_book.pdf`, and canonical `data/dossiers/<MKT>/<SYMBOL>/` via `scripts/dossier_builder_template.py`.

## 4. Review, sync pipeline (`Watchlist <-> Shortlist` / `Discard`) & publish

Run `readability_check.py`, `citation_check.py`, Stage 9 `review_packet.py` + `report_reviewer` + `red_team`, `scripts/sync_dossier_pipeline.py`, `data_layer.py --validate`, `validate_data.py`, and publish via `scripts/publish_run.py`. Company dossiers are not emailed.
