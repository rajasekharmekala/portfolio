---
name: company_report
description: >-
  Unified single-company underwriting, portfolio action, and multi-horizon Stage 2 investment dossier
  for one listed company (IN or US), delivered in 2 synchronized formats
  (Web Research Dossier HTML and a narrative PDF companion) at book-length
  depth (12,000–18,000 words). Explains what the company does, every business
  segment with revenue/profit mix and concrete real-world examples,
  distribution and unit economics, 5–10 year financial forensics, Why the
  Price Is What It Is, and unbiased Two-Sided (Bull vs. Bear) investment
  judgment across Short-Term Trading/Momentum, Medium-Term Inflection, and
  Long-Term Compounding (or Stay Away).
---

> **Design & Two-Format Compiler (binding):** read `../_shared/REPORT_DESIGN.md`. Author the monograph chapter-by-chapter in `<RUN_DIR>/work/<SYMBOL>/` (`spine.json` + `chapters/ch00.json` .. `ch09.json`) and compile both synchronized formats with `scripts/dossier_builder_template.py --spec <RUN_DIR>/work/<SYMBOL> --snapshot <snapshots.json> --facts <facts.json> --positions <positions.json> --shortlist data/shortlist/<MARKET>.json --out docs/blogs/<MARKET>/<SYMBOL>_dossier.html`:
> 1. `docs/blogs/<MARKET>/<SYMBOL>_dossier.html` — Web Research Desk Edition (`research-desk-v1`: 10-year tables, unit-economics matrices, interactive TradingView chart, External Learning Hub, inline `[N]` citations).
> 2. `docs/blogs/<MARKET>/<SYMBOL>_book.pdf` — narrative PDF companion, printed by WeasyPrint from the same chapter data. There is **no** standalone `_book.html`, `.epub`, or `.md`; the narrative HTML is an internal build intermediate that the compiler writes and removes.

> **Blind-First, Judge-Second Decision Order (binding):** prevent price/valuation anchoring by separating business underwriting from market pricing:
> 1. **Pass 1 — Price-Blind Business & Forensic Audit (`ch-1`..`ch-6` + `business_quality.json`):** run an isolated subagent given *only* `--blind-only` fundamentals, primary filings, concalls, and two-sided Bull/Skeptic web research — **never** stock prices, P/E multiples, `stage2_evaluation` postures, watchlist verdict notes, or portfolio holdings. Chapters 1–6 must contain zero portfolio verdict, tier, or support-zone tokens and end with `business_quality.json` (`business_quality_verdict`: `COMPOUNDER_PASS`, `CYCLICAL_CONDITIONAL`, or `FUNDAMENTAL_FAIL`; `kpi_health`: `PASS`, `PASS_WITH_WATCH`, or `FAIL`). Gate Pass 1 with `scripts/dossier_schema.py --check-blind-pass <RUN_DIR>/work/<SYMBOL>` before pulling live prices.
> 2. **Pass 2 — Valuation, Tape & Synthesis (`ch-7`..`ch-9` -> `spine.json` -> `ch-0`):** only after Pass 1 passes, run `market_facts.py`, `stage2_scanner.py`, and full `stock_snapshot.py` to test the locked business reality against Reverse DCF (`ch-7`), Weinstein Stage 2 structure (`ch-8`), and Bull vs. Bear probability-weighted outcomes (`ch-9`). Derive `spine.json` and `ch-0` (`id: "ch-0"`) last.
> 3. **Anti-Hedging Rules (enforced by `dossier_schema.py`):** `FUNDAMENTAL_FAIL` must map to `REJECTED` (never hedged as `WAIT_FOR_SUPPORT`). Every non-rejected call (`IMMEDIATE_BUY`, `ACCUMULATE_ON_DIP`, `WAIT_FOR_SUPPORT`) requires `target_base > entry_zone_high` with `>= 1.5:1` support-zone asymmetry; if even the support zone lacks asymmetric upside, assign `REJECTED`. Conversely, when `business_quality_verdict == "COMPOUNDER_PASS"`, `technical_timing_gate == "CLEAR_FOR_CONSIDERATION"`, and CMP asymmetry clears hurdles, assign an earned `IMMEDIATE_BUY` rather than defaulting timidly to `WAIT_FOR_SUPPORT`.
>
> **Evidence-First Dual Verdict (binding):** derive both the new-capital verdict and the current-holding action after the evidence and Chapter 9 are complete. `spine.json` must include `new_capital_verdict`, `holding_action`, `holding_shares_to_sell`, `holding_rationale`, `holding_alerts`, and `redeployment_plan`. The holding action must use `KEEP_COMPOUNDING`, `HOLD_WITH_HARD_STOP`, `TRIM_INTO_STRENGTH`, `TRIM_OVERWEIGHT`, `EXIT_IMMEDIATELY`, `EXIT_ON_BOUNCE`, `NOT_HELD`, or `DEFER`. Use the same-session positions ledger for actual shares, account split, cost, market value, gain/loss and portfolio weight; never infer that the analyzed company is held. Every alert row includes its trigger, instruction, and exact shares affected (zero if no shares are to be sold). The redeployment plan must compare active shortlist names, researched outside candidates, and cash; allocate 100% of the capital under review, and retain cash when neither equity choice clears the current evidence and entry hurdles. These are advisory alerts, not broker orders.
>
> **Structured spine contract (binding):** `new_capital_verdict` must exactly match the existing `verdict`. `holding_shares_to_sell` is the total shares recommended for sale now or on the named triggers and cannot exceed the positions ledger quantity. When `new_capital_verdict` is `REJECTED`, `spine.json` must also include `rejection_reasons`: a non-empty list drawn from `VALUATION` (base value below price or valuation cited), `CASH_FLOW` (negative or thin free/operating cash flow), `TREND` (broken price trend), and `BUSINESS` (`FUNDAMENTAL_FAIL`). Use every class the dossier's evidence supports. Each `holding_alerts` row has `trigger`, optional numeric `trigger_price`, `shares`, and `instruction`. `redeployment_plan` has a plain-language `capital_source` plus `destinations`: each row has `destination_type` (`CASH`, `SHORTLIST`, or `OUTSIDE`), optional `symbol`, `allocation_pct`, `recommendation`, `rationale`, and `entry_condition`. Named equity destinations also include an analyst-derived `target_base` and `asymmetry_ratio`; live CMP, support zone and invalidation stop are drawn from the same-session snapshot. Include all three destination types, even when their allocation is 0%; allocations sum to 100%. Funded shortlist symbols must exist in the active shortlist and fresh snapshot; funded outside symbols must be in the fresh snapshot. If no specific pool of money is being freed, define the reviewed capital as the next marginal cash unit and allocate 100% to cash until a current equity setup clears the gates.

> **Narrative Companion Narrative Rules (binding for `book_paragraphs`, `epigraph`, and `book_callouts`):**
> - **Second-Person Mentor Voice:** Write the narrative chapters as a seasoned institutional analyst sitting across the desk from the reader (`"you and I"`), using engaging rhetorical questions, vivid factory/customer walkthroughs, and clear transitions.
> - **3 Layers of Quotations:** (1) Every chapter opens with a framed `epigraph` quote (`{"quote": "...", "author": "..."}`); (2) weave verbatim CEO/CFO concall quotes and investor maxims into the prose; (3) include `NARRATOR'S REFLECTION` callout boxes (`"kind": "reflection"`).
> - **Dynamic, Situational Mechanism Twins (NO Regional Quota):** Do **not** force repetitive US/India/Europe analogies into every chapter or recycle mega-cap clichés (*Apple, Berkshire, Danaher, Constellation Software, Bajaj Finance, Titan*). Instead, include **2–4 researched Situational Parallels per dossier** (`{"type": "parallel", "role": "MOAT_SCALING" | "FAILURE_BASE_RATE" | "CYCLE_VALUATION", "company": "...", "region_era": "...", "mechanism": "...", "outcome_numbers": "...", "lesson_for_symbol": "..."}` in `web_blocks`, automatically synced to the PDF) from **any** global market or era where that exact mechanism played out — including **at least one `FAILURE_BASE_RATE` twin** that had the same working-capital, concentration, or valuation vulnerability and de-rated or failed.
> - **Beginner-Clear Options & Multi-Timeframe Chart Lens (`options_snapshot.py` + `macos-browser-automation`):** In Pass 2, run `scripts/options_snapshot.py` (which inspects Weekly `1W` / Daily `1D` / 4-Hour `4H` TradingView structure, checks NSE F&O / US chain liquidity and IV-vs-HV20, and performs a graceful read-only check of any logged-in Chrome Robinhood / TradingView session — continuing cleanly on public data if not logged in) and pass `--options-snapshot` to `dossier_builder_template.py` so `#options-overlay` explains in plain beginner dollars what any Call Spread or LEAPS Call costs, its worst-case loss, breakeven, and scenario payoffs (or stamps `NOT_OPTIONABLE_OR_ILLIQUID` / `NO_OPTIONS_EDGE`).

> **Zero LLM Math & Deterministic Blocks (binding):** never compute moving averages, RSI, volume multiples, per-100 waterfall percentages, or peer multiples in your head. All technical and valuation figures must come from `scripts/stock_snapshot.py` (TradingView + Screener.in / Finviz + TheWrap Stage 2 snapshot) and verified primary filings:
> - Use `{"type": "waterfall", "period": "<FY>", "unit": "<Cr|M>", "revenue": ..., "cogs": ..., "employee_cost": ..., "other_opex": ..., "da": ..., "interest": ..., "other_income": ..., "tax": ..., "cfo": ..., "capex": ...}` in `ch-3` so Python scales every row to $100 / ₹100 of a **single period-matched** audited fiscal year (never mix `TTM` P&L with annual Cash Flow).
> - Use `{"type": "snapshot_financials", "statement": "profit_loss" | "balance_sheet" | "cash_flow" | "ratios"}` in `ch-6` when Screener multi-year tables are present in the snapshot, and `{"type": "peer_snapshot_table", "peers": [...]}` in `ch-7` after snapshotting listed peers.
> - `ch-8` and `ch-9` automatically render the interactive TradingView chart + deterministic technical ledger (`tradingview_chart`) and No-FOMO risk-unit sizing table (`sizing_table`).
>
> **JSON & Prose Integrity (binding):**
> - Write `spine.json` and `chapters/ch00.json`..`ch09.json` via direct file-write tools or Python `json.dump(..., ensure_ascii=False)` — **never** via unquoted shell heredocs (`cat <<EOF`), which strip `$digits` and `$M`/`$B` as bash variables.
> - **Never** run regex sentence-splitting scripts (`. In addition,`, `. :`, `. However, <verb>`); write clear, natural institutional prose directly.
> - `spine.json["citations"]` requires `>= 25` primary sources including `>= 15` distinct `https://` URLs, and Chapter 4's External Learning Hub requires `>= 3` clickable `https://` links. Inline `[N]` markers in `web_blocks` are automatically linked to `#cite_note-N` by the compiler.

> **Unbiased Two-Sided Research & Independent Judgment (binding):**
> - Actively search **both sides of the aisle**: (1) the Bull narrative (management guidance, secular tailwinds, operating leverage, order book) and (2) the Bear / Skeptic narrative (working-capital/DSO stretch, cash-flow gaps, cyclicality, customer/platform concentration, competitive threats, valuation stretch).
> - Never cheerlead management and never pad paragraphs with robotic defensive disclaimers ("This is a company claim, not verified"). Instead, attribute claims cleanly, weigh both sides against the financial record, and state **our own independent judgment** based on the probability-weighted likely outcomes.

> **Concrete Segment & Distribution Walkthroughs (binding):**
> - Every business segment in Chapter 2 must include its share of revenue/profit AND **at least one concrete, end-to-end real-world example** (who the customer is, what problem they face, what exact product/service they buy, how it is engineered/built/delivered, and how it is priced).
> - Chapter 3 must explain **distribution and go-to-market mechanics** (direct sales, channel/MSP partners, dealer networks, OEM qualification, geographical delivery) and trace a worked **$100 / ₹100 revenue-to-free-cash-flow waterfall**.

# 10-Chapter Institutional Monograph & Narrative Companion Blueprint (12,000–18,000 Words)

Both the Web Dossier (`_dossier.html`) and the narrative PDF companion (`_book.pdf`) follow the same 10-chapter structure and share **100% identical numbers, verdicts, and Short / Medium / Long-Term outlooks**:

| Ch # | ID | Target Words | Web Dossier Section (`_dossier.html`) | PDF Companion Section (`_book.pdf`) | Core Content, Examples & Investment Judgment |
|---|---|---|---|---|---|
| 0 | `ch-0` | 700–1,000 | **0. Executive Thesis, Dual Verdict & Opportunity Matrix** | **Prologue: The Business, The Price & Our Independent Verdict** | What the company does; new-capital verdict; current holding action with shares/value/weight when held; cash/shortlist/outside redeployment summary; Bull vs. Bear debate; 3-horizon judgment and exact alert/entry levels. |
| 1 | `ch-1` | 1,400–2,000 | **1. Origin, Corporate Evolution & Past Stock Cycles** | **Chapter 1: How the Business & Stock Got Here — Past Cycles & Pivots** | How the company was built, major strategic pivots and acquisitions, and how its revenue, margins, and stock price performed across prior boom-bust cycles to arrive at today's market cap. |
| 2 | `ch-2` | 1,800–2,500 | **2. What the Company Does: Segments, Revenue Mix & Concrete Examples** | **Chapter 2: Inside Every Segment — Products, Customers & Real-World Examples** | Deep segment-by-segment breakdown: exact share of revenue/profit by vertical and geography; plain-English explanation of each segment; and **at least one concrete, end-to-end real-world example per segment** showing who buys, why they buy, and how the product/service works in practice. |
| 3 | `ch-3` | 1,400–2,000 | **3. Distribution, Supply Chain & Unit Economics** | **Chapter 3: How It Is Sold & Delivered — Distribution & Unit Economics** | Distribution & Go-To-Market anatomy: direct sales vs. dealers/distributors/channel partners, supply-chain/manufacturing footprint, customer qualification, pricing model, billing/DSO cycle, and a worked **$100 / ₹100 revenue-to-free-cash-flow waterfall**. |
| 4 | `ch-4` | 1,300–1,800 | **4. Industry Structure, Competitive Moat & External Learning Hub** | **Chapter 4: The Battlefield — Rivals, Switching Costs & Moat Reality** | Unbiased assessment of competitive advantages vs. vulnerabilities: market share shifts, customer lock-in, pricing power vs. competitor pushback, and the curated **External Learning Hub** (product demos, factory tours, interviews, filings). |
| 5 | `ch-5` | 1,300–1,800 | **5. Leading KPIs, Structural Potential & CEO Walk-the-Talk Audit** | **Chapter 5: Management on Trial — Leading KPIs & Walking the Talk** | The 5–6 operational KPIs that lead financial results; capacity utilization & TAM runway; and an unbiased 3–5 year audit comparing what the CEO/CFO promised against what was actually delivered. |
| 6 | `ch-6` | 1,500–2,100 | **6. 10-Year Financial Forensics, Cash Conversion & Balance Sheet** | **Chapter 6: Following the Cash — 10-Year Financials & Earnings Quality** | Full 5–10 year P&L, margin bridge, balance sheet & debt/lease forensics, working capital & DSO trends, CFO-to-PAT conversion, ROIC/ROCE vs. WACC, and share dilution—separating genuine cash compounding from accounting optics. |
| 7 | `ch-7` | 1,300–1,800 | **7. Why the Price Is What It Is: Valuation, Reverse DCF & Peer Comps** | **Chapter 7: Why the Stock Trades Here — Market Expectations vs. Peers** | Deconstructs today's stock price: historical valuation multiple bands, Reverse DCF (what growth/margin today's price already assumes), and quantitative head-to-head comparison against 3–5 listed peers. |
| 8 | `ch-8` | 1,100–1,500 | **8. Stage 2 Technical Structure, Institutional Flow & Momentum Setup** | **Chapter 8: Reading the Tape — Trend, Volume & Momentum Opportunity** | Stan Weinstein Stage (1, 2, 3, or 4), 30-week SMA / 10-week EMA / 50 & 200-DMA structure, volume accumulation vs. distribution, relative strength, and whether there is an actionable short-term trading/momentum edge right now. |
| 9 | `ch-9` | 1,600–2,200 | **9. Bull vs. Bear, Portfolio Action & Redeployment Plan** | **Chapter 9: Bull vs. Bear, Likely Outcomes & Our Action Plan** | Bull/Bear steelman; probability-weighted outcomes; 3-horizon new-capital verdict; explicit current holding verdict, shares to hold/trim/exit, sell/stop alerts; and a 100%-reconciled table comparing Shortlist, Outside, and Cash destinations. |

---

## Step-by-Step Execution Protocol

1. **Claim a Company and Pull Price-Blind Fundamentals Only:**
   - Claim one eligible active-watchlist name with `run_claims.py batch --workflow company_report --market <MARKET> --run-id <RUN_ID> --size 1`, or claim a specifically requested symbol with `run_claims.py names --workflow company_report --market <MARKET> --run-id <RUN_ID> <SYMBOL>`.
   - Do **not** read watchlist verdict blurbs, shortlist targets, or portfolio holdings yet. Pull only price-blind operating and financial statement data:
     ```bash
     .venv/bin/python scripts/stock_snapshot.py \
       --market <MARKET> --symbols <SYMBOL> --blind-only \
       --out "<RUN_DIR>/cache/blind_<MARKET>_<SYMBOL>.json"
     ```
2. **Pass 1 — Isolated Price-Blind Fundamental Audit (`ch01`..`ch06` + `business_quality.json`):**
   - Spawn an isolated subagent supplied *only* with `<SYMBOL>`, `<MARKET>`, `blind_<MARKET>_<SYMBOL>.json`, primary filings (annual reports / 10-K / 10-Q / investor presentations / latest concall transcripts), and two-sided Bull + Bear/Skeptic web searches.
   - Author `chapters/ch01.json` .. `ch06.json` (`ch-1` history, `ch-2` segments & concrete customer examples, `ch-3` distribution & deterministic `waterfall` block, `ch-4` moat & clickable External Learning Hub, `ch-5` leading KPIs & CEO walk-the-talk audit, `ch-6` 10-year financial forensics) plus `<RUN_DIR>/work/<SYMBOL>/business_quality.json` (`business_quality_verdict`, `kpi_health`, `summary_rationale`).
   - Run the mandatory blind-pass checkpoint before unlocking prices or technicals:
     ```bash
     .venv/bin/python scripts/dossier_schema.py --check-blind-pass "<RUN_DIR>/work/<SYMBOL>"
     ```
3. **Pass 2 — Unlock Market Ledger, Stage 2 Tape & Peer Valuation (`ch07`..`ch09` -> `spine.json` -> `ch00`):**
   - Build a fresh same-session `market_facts.py` ledger (`facts_<MARKET>_<date>.json` and `positions_<MARKET>_<date>.json`), run `stage2_scanner.py` into `<RUN_DIR>/cache/stage2_<MARKET>_<date>.json` (`IN --min-mcap 1000`; `US --min-mcap 1.0`), snapshot the target company, listed peers from Chapters 4/7, active shortlist names, and current holdings, AND pull the multi-timeframe chart + beginner-clear options setup (with graceful Chrome Robinhood/TradingView check; inspect live TradingView `1W`/`1D` charts via `macos-browser-automation` when Chrome is available):
     ```bash
     .venv/bin/python scripts/stock_snapshot.py \
       --market <MARKET> \
       --symbols <SYMBOL> <PEER_1> <PEER_2> <PEER_3> \
       --from-shortlist --from-holdings \
       --stage2-file "<RUN_DIR>/cache/stage2_<MARKET>_<date>.json" \
       --out "<RUN_DIR>/cache/snapshots_<MARKET>_<date>.json"
     .venv/bin/python scripts/options_snapshot.py \
       --market <MARKET> --symbols <SYMBOL> \
       --out "<RUN_DIR>/cache/options_<MARKET>_<SYMBOL>.json"
     ```
   - Author `chapters/ch07.json` (Reverse DCF & `peer_snapshot_table` weighed against `business_quality.json`), `ch08.json` (Stage 2 + multi-timeframe `1W/1D/4H` shelves, gaps, and VCP structure), and `ch09.json` (Bull vs. Bear steelman, probability-weighted outcomes, explicit 3-horizon verdict, current position action, alert plan, and capital redeployment).
   - **Derive** `spine.json` from Chapter 9 (including `sector`, `business_quality_verdict`, `kpi_health`, dual verdicts, and structured alert/redeployment fields), then write `chapters/ch00.json` (`id: "ch-0"`) last. Minimum floors: `8,500+` Web words + dense tables, `10,000+` narrative PDF words.
4. **Compile Both Synchronized Formats (`scripts/dossier_builder_template.py`):**
   ```bash
   .venv/bin/python scripts/dossier_builder_template.py \
      --spec "<RUN_DIR>/work/<SYMBOL>" \
      --snapshot "<RUN_DIR>/cache/snapshots_<MARKET>_<date>.json" \
      --options-snapshot "<RUN_DIR>/cache/options_<MARKET>_<SYMBOL>.json" \
      --facts "<RUN_DIR>/cache/facts_<MARKET>_<date>.json" \
      --positions "<RUN_DIR>/cache/positions_<MARKET>_<date>.json" \
      --shortlist "data/shortlist/<MARKET>.json" \
      --out "docs/blogs/<MARKET>/<SYMBOL>_dossier.html"
   ```
   This writes the Web Dossier and the `_book.pdf` companion. It does not emit `_book.html`, `.epub`, or `.md`.
5. **Run Mechanical, Reviewer & Adversarial Red-Team Gates:**
   - `.venv/bin/python scripts/readability_check.py docs/blogs/<MARKET>/<SYMBOL>_dossier.html`
   - `.venv/bin/python scripts/citation_check.py docs/blogs/<MARKET>/<SYMBOL>_dossier.html --research <RUN_DIR>/cache/research_<MARKET>_<date>.json --allow-stale-asof --min-sources 25`
   - Build the Stage 9 review packet and run both the independent `report_reviewer` and adversarial `red_team` passes (strict cap of 2 rounds per `../_shared/REVIEWER_OPERATIONS.md`):
     ```bash
     .venv/bin/python scripts/review_packet.py build \
       --report "docs/blogs/<MARKET>/<SYMBOL>_dossier.html" \
       --kind dossier --symbol <SYMBOL> \
       --facts "<RUN_DIR>/cache/facts_<MARKET>_<date>.json" \
       --research "<RUN_DIR>/cache/research_<MARKET>_<date>.json" \
       --out-dir "<RUN_DIR>/review/round_1" --round 1 --allow-stale-asof
     ```
     Verify reviewer JSON with `scripts/review_packet.py check`. If `red_team` or `report_reviewer` flags a hedged verdict or unsupported assumption (`BLOCK` / `REVISE`), update `ch09.json`, `spine.json`, and `ch00.json`, recompile, and complete Round 2 delta verification.
6. **Deterministic Pipeline Sync (`Watchlist <-> Shortlist` / `Discard`) & Validation:**
   - Never touch brokerage `Holdings` (`data/accounts/<MARKET>/*.transactions.jsonl`); holdings reflect executed broker trades only.
   - Sync `data/watchlist/<MARKET>.json` and `data/shortlist/<MARKET>.json` deterministically from the reviewed monograph:
     ```bash
     .venv/bin/python scripts/sync_dossier_pipeline.py \
       --spec "<RUN_DIR>/work/<SYMBOL>" \
       --snapshot "<RUN_DIR>/cache/snapshots_<MARKET>_<date>.json" \
       --dossier "docs/blogs/<MARKET>/<SYMBOL>_dossier.html" \
       --review-dir "<RUN_DIR>/review" \
       --research "<RUN_DIR>/cache/research_<MARKET>_<date>.json"
     ```
     (`REJECTED` / `FUNDAMENTAL_FAIL` discards the symbol from both active queues; qualified `TIER_1`/`TIER_2` setups promote/upsert into `shortlist.active` and mark `watchlist.active` `COMPLETED`; conditional `TIER_3` setups remain on `watchlist.active` as `COMPLETED`.)
   - Validate with `scripts/data_layer.py --market <MARKET> --validate` and `scripts/validate_data.py`, rebuild the catalog via `scripts/build_dossier_portal.py --completed ...`, and publish via `scripts/publish_run.py`.
