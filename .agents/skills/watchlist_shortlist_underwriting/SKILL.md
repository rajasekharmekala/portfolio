---
name: watchlist_shortlist_underwriting
description: >-
  Underwrites the next batch of watchlist names for one market (IN or US) using the Stage 2 Sector Momentum + TradingView/Screener/Finviz Snapshot + No-FOMO Entry Timing framework, writes a deep business-monograph dossier per company, prunes broken Stage 4 / rejected names from the watchlist, and updates the watchlist and shortlist JSON files.
---

> **Design (binding):** read `../_shared/REPORT_DESIGN.md`. Every new dossier must be assembled using `scripts/assemble_report.py --market <MKT> --kind dossier --workflow "Company research" --as-of <session-date>`. Summary reports use `--kind report --workflow "Watchlist underwriting"` and stable `docs/reports/<MKT>_Watchlist_to_Shortlist.html`.

> **Market blocks (binding):** this skill covers both markets (`IN` and `US`). Read `.agents/config/markets.json` and `.agents/config/scoring.json` for the market in this run.

> **Zero LLM Math (binding):** never compute moving averages, RSI, volume multiples, or financial ratios in your head. All technical and valuation figures must come from `scripts/stock_snapshot.py` (TradingView + Screener.in / Finviz + TheWrap Stage 2 snapshot) and verified primary filings.

> **Reviewer-cycle limit (binding):** use the shared reviewer process in `../_shared/REVIEWER_OPERATIONS.md` and `.agents/config/reviewer.json`. Two complete rounds is a strict maximum.

# Stage 2 & Deep Business-Monograph Watchlist-to-Shortlist Underwriting Engine (`IN` & `US`)

## 1. Philosophy & Architecture

The Watchlist-to-Shortlist pipeline bridges **idea discovery** (`market_intelligence` and `stage2_sector_momentum` adding leads to `data/watchlist/<MKT>.json`) and **capital deployment** (`data/shortlist/<MKT>.json` and `portfolio_audit`).

Instead of rigid, mechanical accounting pass/fail gates that miss turnaround inflections and early Stage 2 momentum leaders, this workflow evaluates every candidate through three practical institutional lenses:

1. **Deep Business Monograph Understanding (`company_report` skill):**
   - What the company actually does and how its day-to-day operational processes work across each business vertical.
   - Curated external links (official product sites, YouTube factory tours, management interviews, investor presentations, concalls) to learn more.
   - The true operational KPIs and story of the business (what drives unit economics, margins, and order flow).
   - **Management "Walk the Talk" & Potential Audit:** Did leadership deliver on past guidance and capital allocation promises? Is the company reaching its structural potential?
2. **Stage 2 Sector & Stock Momentum (`scripts/stage2_scanner.py` + `scripts/stock_snapshot.py`):**
   - Is the stock's sector/industry experiencing institutional Stage 2 breadth inflows on TheWrap (`https://thewrap.in/data-tools/stage2` for `IN`; `https://thewrap.in/data-tools/ustocks` for `US`)?
   - What is the exact TradingView technical posture (30-week SMA, 10-week EMA, 20/50/200-day SMAs/EMAs, RSI-14, 10d/30d relative volume, pivot levels, and TradingView technical rating)?
3. **Valuation Sanity & No-FOMO Entry Timing (`.agents/config/scoring.json`):**
   - How does current valuation (Screener.in for `IN`; Finviz for `US`) compare against the company's earnings growth trajectory and history?
   - **Should we buy immediately at CMP or wait for support?**
     - **`IMMEDIATE_BUY`**: Strong business & sector tailwinds + Early Stage 2 / fresh base breakout / constructive pullback within $10\%$ of the 10-week EMA ($12\%$ of 50D SMA) with $\text{RSI}(14) \le 73$ and reasonable valuation.
     - **`WAIT_FOR_SUPPORT` / `ACCUMULATE_ON_DIP`**: Strong business and confirmed Stage 2 uptrend, **but** price is extended ($>10\%$ above 10-week EMA, $>12\%$ above 50-day SMA, or $\text{RSI}(14) > 73$) or valuation needs a margin-of-safety pullback. Promote to `data/shortlist/<MKT>.json` with an explicit limit-order support buy zone (`20D EMA` / `10W EMA` / `50D SMA`) so we never chase FOMO spikes.
     - **`REJECTED`**: Confirmed Stage 4 breakdown (price below falling 30-week SMA and falling 50-day SMA), broken business thesis, or management failing to walk the talk with deteriorating fundamentals. Prune from `watchlist.active` to `watchlist.archive`.

---

## 2. Step-by-Step Execution Protocol

### Step 1: Refresh Stage 2 & Consumer-Tool Snapshots + Prune Watchlist
Before claiming or underwriting the batch, run `scripts/stock_snapshot.py` across the active watchlist (and optionally refresh `data/views/stage2_<MKT>_latest.json` if stale):
```bash
.venv/bin/python scripts/stock_snapshot.py \
  --market <MKT> \
  --from-watchlist --from-shortlist \
  --stage2-file data/views/stage2_<MKT>_latest.json \
  --prune-watchlist \
  --out "<RUN_DIR>/cache/snapshots_<MKT>_<date>.json"
```
- **Automatic Watchlist Pruning:** `--prune-watchlist` automatically moves any active watchlist entry that has fallen into a confirmed `STAGE_4` breakdown or carries a `REJECTED` verdict from `watchlist.active` to `watchlist.archive`, keeping the active watchlist focused on viable setups.

### Step 2: Claim the Batch of 4 Candidates
Claim up to **4 eligible securities** from `watchlist.active`:
```bash
.venv/bin/python scripts/run_claims.py batch --workflow watchlist_to_shortlist --market <MKT> --run-id <RUN_ID> --size 4
```

### Step 3: Spawn 1 Dedicated Subagent Per Company
- **Strict Single-Company Subagent Rule:** Never write multiple company dossiers in a single agent loop. Launch **1 dedicated subagent per company** (`invoke_subagent`).
- Pass each subagent:
  1. Its symbol's exact JSON block from `<RUN_DIR>/cache/snapshots_<MKT>_<date>.json` (TradingView moving averages, RSI, volume, pivots, Screener.in/Finviz valuation, TheWrap Stage 2 data, and `stage2_evaluation`).
  2. Instructions to follow `.agents/skills/company_report/SKILL.md` to research and write the complete **Deep Business-Monograph Dossier** (`docs/blogs/<MKT>/<SYMBOL>_dossier.html`, $\ge 35\text{ KB}$, 25–40+ citations, including external website/video links, day-to-day vertical operations, business KPIs, management walk-the-talk audit, and multi-horizon Stage 2 + valuation view).
  3. Instructions to return the structured shortlist/watchlist decision payload (`action_verdict`, `entry_posture`, `entry_zone_low`, `entry_zone_high`, `stop_loss`, `target_base`, `target_bull`, `weinstein_stage`, `primary_catalyst`, `primary_kpi_summary`, `moat_description`, `invalidation_condition`).

### Step 4: Update `data/shortlist/<MKT>.json` & `data/watchlist/<MKT>.json`
1. **Dossier-First Gate:** Verify `docs/blogs/<MKT>/<SYMBOL>_dossier.html` exists on disk, is $\ge 30\text{ KB}$, and passes `scripts/portal_publish.py` modern-layout checks before marking any candidate `COMPLETED`.
2. **Shortlist Promotion (`IMMEDIATE_BUY`, `ACCUMULATE_ON_DIP`, `WAIT_FOR_SUPPORT`):**
   - Insert or update qualified candidates in `data/shortlist/<MKT>.json` (`CORE_ALPHA` max 10 autowritten slots; `TACTICAL_MOMENTUM` max 10 autowritten slots; plus `LEVERAGED_SATELLITE` max 5 for `US`).
   - Populate exact figures from `stock_snapshot.py` (`cmp`, `pe`, `roce_pct`/`roe_pct`, `rsi_14`, `weinstein_stage`, `entry_zone_low`, `entry_zone_high`, `stop_loss`, `research_dossier_path`: `"blogs/<MKT>/<SYMBOL>_dossier.html"`).
   - If a shortlist book is at capacity (10 slots), displace the weakest incumbent (e.g., an incumbent whose Stage 2 trend has stalled into Stage 3/4 or whose valuation/momentum is inferior to an `IMMEDIATE_BUY` early Stage 2 challenger).
3. **Watchlist Pruning & Status Update (`data/watchlist/<MKT>.json`):**
   - For candidates with `action_verdict = REJECTED`, move their row from `watchlist.active` into `watchlist.archive` with the full rejection rationale and dossier link.
   - For qualified candidates (`IMMEDIATE_BUY`, `ACCUMULATE_ON_DIP`, `WAIT_FOR_SUPPORT`), update their row in `watchlist.active` (`status = "COMPLETED"`, `deep_research_status = "COMPLETED"`, `research_cycle = target_research_cycle`, `action_verdict`, `entry_posture`, `last_researched_date`).
4. Run `.venv/bin/python scripts/data_layer.py --market <MKT> --validate` to verify schema compliance.

### Step 5: Write Batch Summary Report & Run Reviewer Gate
1. Assemble the batch underwriting report at `docs/reports/<MKT>_Watchlist_to_Shortlist.html` summarizing:
   - Watchlist hygiene & Stage 4 names pruned to archive.
   - Side-by-side comparison table of the 4 underwritten companies (Stage 2 status, TradingView MAs/RSI, Screener/Finviz valuation, Management Walk-the-Talk verdict, and No-FOMO Entry Zone).
   - Deep-dive summary and direct link to each company's new monograph dossier (`blogs/<MKT>/<SYMBOL>_dossier.html`).
2. Run `scripts/review_packet.py`, `report_reviewer`, and `red_team` per `../_shared/REVIEWER_OPERATIONS.md`.
3. Rebuild the portal catalog (`.venv/bin/python scripts/portal_publish.py`) and publish via `scripts/publish_run.py`.
