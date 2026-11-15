---
name: portfolio_audit
description: >-
  Deterministic portfolio forensic audit, risk-heat & sector-rotation allocation, hysteresis convergence,
  and dual-edition storytelling (Web Research Desk + Masterclass Audiobook/PDF Companion) for one market
  (IN = Zerodha account; US = consolidated Charles Schwab, Robinhood & Options book). Market-specific
  blocks are marked.
---

> **Market blocks (binding):** this skill covers both markets. Read `.agents/config/markets.json` for the market in this run (`IN` or `US`). Follow the text outside a market block, and inside a market block follow only the block matching this run's market. Never mix figures, currencies, exchanges, or sources across markets.

> **Single Source of Truth & Zero LLM Math (binding):** read `.agents/config/scoring.json` (schema v4). Never invent share counts, target weights, open portfolio heat, stop ratchets, or cash bridges in prose. Run `scripts/portfolio_allocator.py` first to produce `<RUN_DIR>/cache/allocation_<MKT>_<date>.json` (and update `data/allocations/<MKT>.json`), then compile **both** synchronized deliverables through `scripts/portfolio_audit_builder.py`:
> 1. `docs/reports/<MKT>_Portfolio_Audit.html` — `research-desk-v1` Web Research Desk Edition with built-in interactive Audiobook narrator (`.book-audio-bar`), `.edition-switcher`, reconciled tables, and per-holding case notes.
> 2. `docs/reports/<MKT>_Portfolio_Audit_book.pdf` — Masterclass Narrative Companion PDF ("The Portfolio Architect"), walking through every keep, ratchet, trim, exit, starter buy, option hold, and cash reserve as one cohesive second-person story.

> **Reviewer-cycle limit & Publication (binding):** use `../_shared/REVIEWER_OPERATIONS.md` and `.agents/config/reviewer.json` (strict maximum of two rounds). After validation and review, publish both `<MKT>_Portfolio_Audit.html` and `<MKT>_Portfolio_Audit_book.pdf` plus `data/allocations/<MKT>.json` to GitHub Pages via `scripts/publish_run.py` per `../_shared/RUN_PROTOCOL.md` §6 & §8, then send the short decision digest via `scripts/send_email.py`.

> **Holdings source & Tracking Isolation (binding):** for `IN`, positions replay from `data/accounts/IN/zerodha.transactions.jsonl`. For `US`, positions replay from `data/accounts/US/schwab.transactions.jsonl` and `data/accounts/US/robinhood.transactions.jsonl` plus `data/options/US.json`, consolidated in `<RUN_DIR>/cache/positions_US_<date>.json` (`net_worth` = equities + cash + options MV). Always pass `--allow-stale-holdings` to `market_facts.py` and disclose any freshness warning. Tiny tracking stubs (`< 0.35%` of Net Worth per `scoring.json`) are isolated automatically: they are reconciled in total Net Worth, excluded from the `12–15` active risk-slot count, and exempted from individual 80-word case notes.

<!-- MARKET IN -->
# Master India (Zerodha) Portfolio Audit, Deterministic Allocation & Narrative Companion Skill
<!-- /MARKET -->
<!-- MARKET US -->
# Master US (Schwab, Robinhood & Options) Portfolio Audit, Deterministic Allocation & Narrative Companion Skill
<!-- /MARKET -->

> **Voice & Cohesive Audiobook Storytelling (binding):** read `../_shared/REPORT_VOICE.md` and `../_shared/REPORT_EDITORIAL_STANDARD.md`. Write the narrative chapters and case notes in clear second-person mentor voice (`"you and I"` sitting across the desk), telling one cohesive start-to-finish story explaining *why* the macro tide sets our risk budget, *why* each holding earns or loses its slot, *how* challengers compete fairly, and *why* our recommendations stay stable across short reruns. Use `verdict-*` classes from `../_shared/REPORT_PALETTE.md` only—no inline off-palette hex colors and no emoji.

> **Report date (binding):** resolve the latest completed exchange session with a verified benchmark close per `../_shared/RUN_PROTOCOL.md` §0, and use that exact `<date>` across `market_facts.py`, `stock_snapshot.py`, `options_snapshot.py`, `portfolio_allocator.py`, research queries, and validation.

---

## STEP-BY-STEP EXECUTION PROTOCOL (MANDATORY)

### Step 1 — Start Isolated Run Session & Build Deterministic Evidence Ledgers

1. Start an isolated worktree & singleton claim per `RUN_PROTOCOL.md` §8:
   ```bash
   .venv/bin/python scripts/run_session.py start --workflow portfolio_audit --market <MKT>
   ```
2. Create `<RUN_DIR>` (`cache/`, `inputs/`, `work/`, `review/`), copy input JSONs (`shortlist`, `watchlist`, `options`, `allocations` if present), and build the session ledger + Stage 2 sector breadth + live multi-source snapshots:
<!-- MARKET IN -->
   ```bash
   .venv/bin/python scripts/market_facts.py --market IN --date <session> --screen nifty500 --allow-stale-holdings --run-dir "<RUN_DIR>"
   .venv/bin/python scripts/stage2_scanner.py --market IN --min-mcap 1000 --out "<RUN_DIR>/cache/stage2_IN_<session>.json"
   .venv/bin/python scripts/stock_snapshot.py --market IN --from-holdings --from-shortlist --stage2-file "<RUN_DIR>/cache/stage2_IN_<session>.json" --out "<RUN_DIR>/cache/snapshots_IN_<session>.json"
   ```
<!-- /MARKET -->
<!-- MARKET US -->
   ```bash
   .venv/bin/python scripts/market_facts.py --market US --date <session> --screen sp1500 --allow-stale-holdings --run-dir "<RUN_DIR>"
   .venv/bin/python scripts/stage2_scanner.py --market US --min-mcap 1.0 --out "<RUN_DIR>/cache/stage2_US_<session>.json"
   .venv/bin/python scripts/stock_snapshot.py --market US --from-holdings --from-shortlist --stage2-file "<RUN_DIR>/cache/stage2_US_<session>.json" --out "<RUN_DIR>/cache/snapshots_US_<session>.json"
   .venv/bin/python scripts/options_snapshot.py --market US --from-options --from-shortlist --out "<RUN_DIR>/cache/options_snapshot_US_<session>.json"
   ```
<!-- /MARKET -->
3. Run the mandatory `duck-duck-go` MCP web research pass (`search` + `fetch_content` per `REPORT_EDITORIAL_STANDARD.md` §6) for every item in `facts.research_needs` (earnings dates, catalysts behind any `EXIT`/`TRIM`, FII/DII or Treasury/VIX context, promoter pledges / Form 4s) and write `<RUN_DIR>/cache/research_<MKT>_<session>.json` (`>= 12` distinct verified URLs).

### Step 2 — Run the Deterministic CIO Portfolio Allocator (`scripts/portfolio_allocator.py`)

Compute exact open portfolio heat, correlated cluster caps (`<= 25%` NAV / `<= 3.5%` heat), unified 100-point tournament scores, regime-adaptive 50/50 starter/scale-up tranches, 2x/3x & LEAPS decay guardrails, 5-day hysteresis locks, and `±1.25%` convergence deadbands:

```bash
.venv/bin/python scripts/portfolio_allocator.py \
  --market <MKT> \
  --facts "<RUN_DIR>/cache/facts_<MKT>_<session>.json" \
  --positions "<RUN_DIR>/cache/positions_<MKT>_<session>.json" \
  --snapshots "<RUN_DIR>/cache/snapshots_<MKT>_<session>.json" \
  --shortlist "data/shortlist/<MKT>.json" \
  --watchlist "data/watchlist/<MKT>.json" \
  --options-snapshot "<RUN_DIR>/cache/options_snapshot_<MKT>_<session>.json" \
  --prior-state "data/allocations/<MKT>.json" \
  --persist-state "data/allocations/<MKT>.json" \
  --out "<RUN_DIR>/cache/allocation_<MKT>_<session>.json"
```

### Step 3 — Author Bespoke Cohesive Narrative & Case Notes (`audit_narrative_<MKT>.json`)

Read `<RUN_DIR>/cache/allocation_<MKT>_<session>.json`, `<RUN_DIR>/cache/research_<MKT>_<session>.json`, and any same-date `<MKT>_Market_Intelligence.html` sibling report. Write `<RUN_DIR>/work/audit_narrative_<MKT>.json` via direct file-write tools or `json.dump` (never unquoted shell heredocs) supplying:
- `"primer"`: 150–250 word executive thesis opening with portfolio condition, net worth, open heat vs ceiling, convergence score, what changed since the prior plan, and the decision summary.
- `"chapters"` (`"chapter1"` .. `"chapter7"`): cohesive mentor-voice `"book_paragraphs"`, `"epigraph"` (`quote` + `author`), and `"book_callouts"` (`mental_model`, `reflection`, `parallel`, `execution`) weaving our macro regime, asymmetric sector rotation, holding verdicts, 2x/3x & options decay rules, challenger tournament, money bridge, execution routing, and hysteresis stability into one compelling audiobook story.
- `"casenotes"`: one rich `90–160` word story per active non-tracking holding (`holding_decisions`) with varied sentence openings, explaining what the business does, why we own it, exact ledger close/weight/P&L/stop/heat from `allocation_<MKT>_<session>.json`, the rule behind its verdict, and the concrete `if / unless / below` invalidation trigger (citing research URLs where catalysts/earnings apply).
- `"citations"`: numbered primary filing, exchange, and research source strings.

**Strict Non-Contradiction Rule:** Every share count, dollar/rupee value, weight, stop, tournament score, convergence percentage, and verdict in your narrative MUST match `allocation_<MKT>_<session>.json` verbatim.

### Step 4 — Compile Both Synchronized Editions (`scripts/portfolio_audit_builder.py`)

```bash
.venv/bin/python scripts/portfolio_audit_builder.py \
  --allocation "<RUN_DIR>/cache/allocation_<MKT>_<session>.json" \
  --facts "<RUN_DIR>/cache/facts_<MKT>_<session>.json" \
  --research "<RUN_DIR>/cache/research_<MKT>_<session>.json" \
  --narrative "<RUN_DIR>/work/audit_narrative_<MKT>.json" \
  --out "docs/reports/<MKT>_Portfolio_Audit.html"
```

This writes both `docs/reports/<MKT>_Portfolio_Audit.html` (with interactive Web Speech Audiobook bar + Research Desk tables) and `docs/reports/<MKT>_Portfolio_Audit_book.pdf` ("The Portfolio Architect").

### Step 5 — Mechanical Validation, Reviewer Gate, Publication & Digest

1. Run the deterministic report validator:
   ```bash
   .venv/bin/python scripts/validate_report.py \
     --report "docs/reports/<MKT>_Portfolio_Audit.html" \
     --kind portfolio_audit \
     --facts "<RUN_DIR>/cache/facts_<MKT>_<session>.json" \
     --research "<RUN_DIR>/cache/research_<MKT>_<session>.json" \
     --allocation "<RUN_DIR>/cache/allocation_<MKT>_<session>.json"
   ```
2. Build the Stage 9 review packet (`--allocation` traces all allocator numbers automatically) and run `report_reviewer` + `red_team` (max 2 rounds):
   ```bash
   .venv/bin/python scripts/review_packet.py build \
     --report "docs/reports/<MKT>_Portfolio_Audit.html" \
     --kind portfolio_audit \
     --facts "<RUN_DIR>/cache/facts_<MKT>_<session>.json" \
     --research "<RUN_DIR>/cache/research_<MKT>_<session>.json" \
     --snapshots "<RUN_DIR>/cache/snapshots_<MKT>_<session>.json" \
     --stage2-file "<RUN_DIR>/cache/stage2_<MKT>_<session>.json" \
     --allocation "<RUN_DIR>/cache/allocation_<MKT>_<session>.json" \
     --out-dir "<RUN_DIR>/review/round_1" --round 1
   ```
3. Rebuild catalog (`scripts/build_dossier_portal.py --completed "docs/reports/<MKT>_Portfolio_Audit.html" --workflow "Portfolio audit" --market <MKT> ...`), publish via `scripts/publish_run.py`, and dispatch the short decision digest via `scripts/send_email.py`.

---

## SUMMARY OF BINDING v4 PORTFOLIO RULES (`scoring.json`)

<!-- MARKET IN -->
- **Sleeves & Slots (IN — Zerodha):** `12–15` active equity positions (`<0.35%` tracking stubs excluded). **Core Alpha `35%–45%`** (ROCE > 18%, secular moat; ignores short-term sector dips unless 30W structure or KPIs break), **Tactical Momentum `40%–55%`** (gated on Leading/Improving 3M RS + TheWrap Stage 2 breadth), **Cash Buffer `5%–22%`** (regime-driven floor).
<!-- /MARKET -->
<!-- MARKET US -->
- **Sleeves & Slots (US — Schwab + Robinhood + Options):** `12–15` total unique active risk underlyings across Equities, 2x/3x ETFs, and Options (`<0.35%` tracking stubs and `NBIL` T-bill ETF excluded). **Core Alpha `35%–45%`**, **Tactical Momentum Equities `25%–40%`**, **2x/3x Sector Rotation ETFs `0%–12%`** (max 2 sector/index ETFs `<=6%` each; single-stock 2x ETFs phased out; `0%` new buys in sideways/downtrend regimes; 20D EMA stop + 15-session time stop + `+15%` half-trim), **Drawdown Calls / LEAPS `0%–10%`** at `max(cost, MV)` (`0.60–0.80` delta or Bull Call Debit Spreads when `IV > 1.15x HV20`; `<=2%` cost per underlying; grandfather legacy contracts above shelf stops), with a **15.0% Combined Decay Ceiling** across `(2x/3x ETFs + Options)`. Route equities to **Charles Schwab** (selling Robinhood duplicate lots first on trims) and Options / 2x/3x swings to **Robinhood**.
<!-- /MARKET -->
- **Cluster & Heat Caps:** Max **25.0% NAV** and **3.5% open heat** in any correlated/thematic cluster (`1Y r >= 0.65`); max total Open Portfolio Heat **12.0%** in Broad Uptrends, **7.5%–8.5%** in Narrow/Sideways tapes, **4.0%** in Downtrends.
- **Regime-Adaptive 50/50 Tranches:** Deploy a **50% Starter** inside non-extended support/breakout rules (`<=4.0%` from support in sideways tapes; `<=8.5%` from 10W EMA in broad uptrends); deploy the **50% Proof Add** only on pullback or after `>= +1R` profit cushion; harvest `35%` into `+2R` strength on tactical swings during sideways regimes while letting Stage 2 winners run up to `22%` in broad uptrends.
- **Day-1 Provisional Rule & Dossier Debt Queue:** Pre-dossier holdings are grandfathered on ratcheted chart stops, frozen from fresh `ADD`s, and ranked by capital exposure in Chapter 6.1 for upcoming `company_report` runs.
- **Convergence & Short-Rerun Stability:** `data/allocations/<MKT>.json` enforces an upward-only stop ratchet, a **5-day `±2.5%` price hysteresis lock**, a **`+15 pt` slot displacement hurdle**, and a **`±1.25%` NAV rebalance deadband** so recommendations never flip-flop on 1-day reruns and converge monotonically toward zero trades as edits are executed.
