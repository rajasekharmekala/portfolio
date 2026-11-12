---
name: dossier_refresh
description: >-
  Companion dossier refresh, blind-spot brainstorm, and re-underwriting skill for
  companies that already have a published monograph (IN or US). Strips prior verdicts,
  targets, and stops to challenge baseline Chapters 1–6 assumptions against new
  filings/concalls, actively brainstorms omitted risks/competitors/unit-economics
  blind spots and patches the owning chapters, re-evaluates live Valuation, Stage 2
  technicals, and upward-only held stop-loss ratchets, recompiles synchronized Web
  HTML + PDF, and updates Watchlist/Shortlist/Discard deterministically.
---

# Skill: dossier_refresh (Companion Assumption Audit, Blind-Spot Brainstorm & Tape Re-Underwriting)

> **Purpose:** Avoid rewriting 15,000 words of slow-moving corporate history from scratch while **preventing status-quo confirmation bias and omission blindness**. Every refresh strips the prior verdict, re-tests existing Chapters 1–6 assumptions against fresh disclosures, actively brainstorms what the original monograph missed, patches only the affected structural chapters, and then re-underwrites Valuation (`ch-7`), Stage 2 technicals (`ch-8`), Synthesis (`ch-9`), Stop-Loss Ratchets (`spine.json`), and `ch-0` (`_dossier.html` + `_book.pdf` + `data/dossiers/<MARKET>/<SYMBOL>/`).

---

## Binding Anti-Bias & Stop-Ratchet Rules

1. **Verdict-Stripped Pass 1 Barrier (`prepare` -> `validate-audit`):**
   - Start with `scripts/dossier_refresh.py prepare --market <MARKET> --symbol <SYMBOL> --out-dir "<RUN_DIR>/work/<SYMBOL>"`. It copies *only* `ch01..ch06` + `business_quality.json` and writes `blind_refresh_packet.md` (stripping `spine.json`, `ch-0`, `ch-7..ch-9`, prices, multiples, targets, and stops).
   - Spawn an isolated Pass 1 subagent that reads **only** `blind_refresh_packet.md`, `--blind-only` fundamentals (`stock_snapshot.py --blind-only`), new filings/concalls since `prior_as_of`, and skeptic web searches — **never** `prior_anchor_locked.json`, `docs/blogs/`, `watchlist`, `shortlist`, or `positions`.
2. **Mandatory Blind-Spot & Omission Brainstorm (`>= 2` distinct vectors):**
   - Pass 1 must actively ask *"What did the original dossier fail to consider?"* across the 6 vectors in `blind_refresh_packet.md` (`CUSTOMER_SUPPLIER_CONCENTRATION`, `FOOTNOTE_BALANCE_SHEET_FORENSICS`, `UNIT_ECONOMICS_HIDDEN_FRICTION`, `UNLISTED_OR_ADJACENT_COMPETITION`, `REGULATORY_TARIFF_FX_EXPOSURE`, `GOVERNANCE_INCENTIVES_CAPITAL_ALLOCATION`), research primary sources, and **directly update the owning `chapters/ch01..ch06.json` (`web_blocks` + `book_paragraphs`) and `business_quality.json`** whenever a blind spot is `MATERIAL_PATCHED` or an assumption is `WEAKENED` / `BROKEN`.
   - `scripts/dossier_refresh.py validate-audit` checks SHA-256 diffs against `baseline_hashes.json` and fails if any `MATERIAL_PATCHED` / `WEAKENED` / `BROKEN` finding did not actually update its target chapter JSON.
3. **3-Tier Selective Chapter Effort:**
   - `TIER_1_TAPE_VALUATION`: No new quarterly filing/event and blind-spot checks are `IMMATERIAL_VERIFIED` -> keep `ch01..ch06` (with any minor clarifications), re-author `ch07..ch09`, `spine.json`, and `ch00.json`.
   - `TIER_2_QUARTERLY_OR_BLINDSPOT`: New earnings/concall or `MATERIAL_PATCHED` blind spots -> patch the affected `ch01..ch06` chapters + `business_quality.json`, then re-author `ch07..ch09`, `spine.json`, and `ch00.json`.
   - `TIER_3_THESIS_BREAK`: Core business/moat pillar `BROKEN` (fraud, major pivot/M&A, structural impairment) -> rewrite affected fundamental chapters, set `business_quality_verdict` accordingly, and re-underwrite `ch07..ch09`, `spine.json`, and `ch00.json`.
4. **Upward-Only Stop-Loss Ratchet on Active Holdings (enforced by `dossier_schema.py`):**
   - For held positions (`quantity > 0`), `stop_loss` may **ratchet UP** behind rising Stage 2 support (`50D SMA` / `30W SMA`), or stay at the prior structural floor — **never** lower `stop_loss` below `prior_anchor_locked.json["stop_loss"]` to accommodate a falling stock. If live price or Stage 4 breakdown breaches the prior structural stop, set `holding_action` to `EXIT_IMMEDIATELY` or `EXIT_ON_BOUNCE`.

---

## Step-by-Step Execution Protocol

1. **Start Isolated Worktree, Claim Stalest Published Dossier & Prepare Blind Workspace:**
   ```bash
   .venv/bin/python scripts/run_session.py start --workflow dossier_refresh --market <MARKET>
   # Inside the worktree:
   .venv/bin/python scripts/run_claims.py batch --workflow dossier_refresh --market <MARKET> --run-id <RUN_ID> --size 1
   # (Or claim a requested symbol with: run_claims.py names --workflow dossier_refresh --market <MARKET> --run-id <RUN_ID> <SYMBOL>)
   .venv/bin/python scripts/dossier_refresh.py prepare --market <MARKET> --symbol <SYMBOL> --out-dir "<RUN_DIR>/work/<SYMBOL>"
   .venv/bin/python scripts/stock_snapshot.py --market <MARKET> --symbols <SYMBOL> --blind-only --out "<RUN_DIR>/cache/blind_<MARKET>_<SYMBOL>.json"
   ```
2. **Pass 1 — Isolated Assumption Audit & Blind-Spot Brainstorm (`ch01..ch06` + `refresh_audit.json`):**
   - Spawn an isolated subagent with `blind_refresh_packet.md` and `blind_<MARKET>_<SYMBOL>.json`.
   - Research all disclosures since `prior_as_of` AND brainstorm/verify `>= 2` blind-spot vectors; patch affected `chapters/ch01..ch06.json` + `business_quality.json`; write `<RUN_DIR>/work/<SYMBOL>/refresh_audit.json`.
   - Enforce the mechanical checkpoint before unlocking live prices:
     ```bash
     .venv/bin/python scripts/dossier_refresh.py validate-audit --work-dir "<RUN_DIR>/work/<SYMBOL>"
     ```
3. **Pass 2 — Live Valuation, Stage 2 Tape, Stop Ratchet & Compilation (`ch07..ch09` -> `spine.json` -> `ch00`):**
   - Run `market_facts.py`, `stage2_scanner.py`, and full `stock_snapshot.py --market <MARKET> --symbols <SYMBOL> <PEERS...> --from-shortlist --from-holdings --stage2-file ... --out "<RUN_DIR>/cache/snapshots_<MARKET>_<date>.json"`.
   - Author fresh `ch07.json` (Reverse DCF & `peer_snapshot_table`), `ch08.json` (Stage 2 tape), `ch09.json` (Bull vs. Bear + holding/redeployment), derive `spine.json` (honoring `prior_anchor_locked.json` stop-ratchet and anti-hedging gates) and `ch00.json` (`id: "ch-0"`), and append new sources to `prior_anchor_locked.json["citations"]`.
   - Verify stop ratchet and compile synchronized Web HTML + PDF + canonical `data/dossiers/<MARKET>/<SYMBOL>/` spec:
     ```bash
     .venv/bin/python scripts/dossier_refresh.py check-ratchet \
       --work-dir "<RUN_DIR>/work/<SYMBOL>" \
       --positions "<RUN_DIR>/cache/positions_<MARKET>_<date>.json" \
       --snapshot "<RUN_DIR>/cache/snapshots_<MARKET>_<date>.json"
     .venv/bin/python scripts/dossier_builder_template.py \
       --spec "<RUN_DIR>/work/<SYMBOL>" \
       --snapshot "<RUN_DIR>/cache/snapshots_<MARKET>_<date>.json" \
       --facts "<RUN_DIR>/cache/facts_<MARKET>_<date>.json" \
       --positions "<RUN_DIR>/cache/positions_<MARKET>_<date>.json" \
       --shortlist "data/shortlist/<MARKET>.json" \
       --out "docs/blogs/<MARKET>/<SYMBOL>_dossier.html"
     ```
4. **Reviewer, Red-Team & Deterministic Pipeline Sync (`Watchlist <-> Shortlist` / `Discard`):**
   - Run `readability_check.py`, `citation_check.py --min-sources 25 --allow-stale-asof`, and Stage 9 `review_packet.py build --kind dossier` -> `report_reviewer` + `red_team` -> `review_packet.py check`.
   - Run `scripts/sync_dossier_pipeline.py` (with `--review-dir "<RUN_DIR>/review"`), `scripts/data_layer.py --market <MARKET> --validate`, `scripts/validate_data.py`, `scripts/build_dossier_portal.py --completed ...`, and `scripts/publish_run.py`.
