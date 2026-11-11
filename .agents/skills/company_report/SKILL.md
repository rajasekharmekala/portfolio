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

> **Evidence-First Decision Order (binding):** the verdict is a *conclusion*, never an input. Author **Chapters 1–8 first** — business & history (ch-1)–(ch-2), distribution/unit economics (ch-3), moat (ch-4), management walk-the-talk (ch-5), 10-year financial forensics (ch-6), valuation & Reverse DCF (ch-7), and the Stage 2 technical structure (ch-8) — then author **Chapter 9** (Bull vs. Bear steelman + probability-weighted outcomes). Only once Chapter 9 is written do you **derive** the `verdict`, `archetype`, `conviction_tier`, `entry_zone_low/high`, `stop_loss`, `target_base/bull/bear`, and `strategy_bucket` into `spine.json` and write the `ch-0` Prologue. Do not open a spine with a pre-committed verdict and then write chapters to fit it. The technical snapshot (`scripts/stock_snapshot.py`) outputs a `technical_timing_gate` — a ceiling that can cap the call at `WAIT_FOR_SUPPORT`/`REJECTED` but never grants `IMMEDIATE_BUY` on its own; the business, valuation and management evidence must earn the call.
> **Evidence-First Dual Verdict (binding):** derive both the new-capital verdict and the current-holding action after the evidence and Chapter 9 are complete. `spine.json` must include `new_capital_verdict`, `holding_action`, `holding_shares_to_sell`, `holding_rationale`, `holding_alerts`, and `redeployment_plan`. The holding action must use `KEEP_COMPOUNDING`, `HOLD_WITH_HARD_STOP`, `TRIM_INTO_STRENGTH`, `TRIM_OVERWEIGHT`, `EXIT_IMMEDIATELY`, `EXIT_ON_BOUNCE`, `NOT_HELD`, or `DEFER`. Use the same-session positions ledger for actual shares, account split, cost, market value, gain/loss and portfolio weight; never infer that the analyzed company is held. Every alert row includes its trigger, instruction, and exact shares affected (zero if no shares are to be sold). The redeployment plan must compare active shortlist names, researched outside candidates, and cash; allocate 100% of the capital under review, and retain cash when neither equity choice clears the current evidence and entry hurdles. These are advisory alerts, not broker orders.
>
> **Structured spine contract (binding):** `new_capital_verdict` must exactly match the existing `verdict`. `holding_shares_to_sell` is the total shares recommended for sale now or on the named triggers and cannot exceed the positions ledger quantity. Each `holding_alerts` row has `trigger`, optional numeric `trigger_price`, `shares`, and `instruction`. `redeployment_plan` has a plain-language `capital_source` plus `destinations`: each row has `destination_type` (`CASH`, `SHORTLIST`, or `OUTSIDE`), optional `symbol`, `allocation_pct`, `recommendation`, `rationale`, and `entry_condition`. Named equity destinations also include an analyst-derived `target_base` and `asymmetry_ratio`; live CMP, support zone and invalidation stop are drawn from the same-session snapshot. Include all three destination types, even when their allocation is 0%; allocations sum to 100%. Funded shortlist symbols must exist in the active shortlist and fresh snapshot; funded outside symbols must be in the fresh snapshot. If no specific pool of money is being freed, define the reviewed capital as the next marginal cash unit and allocate 100% to cash until a current equity setup clears the gates.
> **Evidence-First Decision Order (binding):** the verdict is a *conclusion*, never an input. Author **Chapters 1–8 first** — business & history (ch-1)–(ch-2), distribution/unit economics (ch-3), moat (ch-4), management walk-the-talk (ch-5), 10-year financial forensics (ch-6), valuation & Reverse DCF (ch-7), and the Stage 2 technical structure (ch-8) — then author **Chapter 9** (Bull vs. Bear steelman + probability-weighted outcomes + holding action + redeployment). Only after Chapter 9 derive all decision fields into `spine.json` and write the `ch-0` Prologue. The technical snapshot (`scripts/stock_snapshot.py`) outputs a `technical_timing_gate` — a ceiling that can cap the call at `WAIT_FOR_SUPPORT`/`REJECTED` but never grants `IMMEDIATE_BUY` on its own; the business, valuation and management evidence must earn the call.

> **Narrative Companion Narrative Rules (binding for `book_paragraphs`, `epigraph`, and `book_callouts`):**
> - **Second-Person Mentor Voice:** Write the narrative chapters as a seasoned institutional analyst sitting across the desk from the reader (`"you and I"`), using engaging rhetorical questions, vivid factory/customer walkthroughs, and clear transitions.
> - **3 Layers of Quotations:** (1) Every chapter opens with a framed `epigraph` quote (`{"quote": "...", "author": "..."}`); (2) weave verbatim CEO/CFO concall quotes and investor maxims into the prose; (3) include `NARRATOR'S REFLECTION` callout boxes (`"kind": "reflection"`).
> - **Global Parallel Company Examples (US, India, and Europe):** Every chapter must connect the company's economics, moat, working-capital cycle, or valuation to concrete historical parallels across the US, India, or Europe (via prose and `"kind": "parallel"` callout boxes) so the reader grasps how similar business models and stock setups have played out globally.

> **Zero LLM Math (binding):** never compute moving averages, RSI, volume multiples, or financial ratios in your head. All technical and valuation figures must come from `scripts/stock_snapshot.py` (TradingView + Screener.in / Finviz + TheWrap Stage 2 snapshot) and verified primary filings.

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

1. **Claim a Company and Build Fresh Portfolio / Market Inputs:**
   - Claim one eligible active-watchlist name with `run_claims.py batch --workflow company_report --market <MARKET> --run-id <RUN_ID> --size 1`, or claim a specifically requested symbol with `run_claims.py names --workflow company_report --market <MARKET> --run-id <RUN_ID> <SYMBOL>`.
   - Build a fresh same-session `market_facts.py` ledger. Use its `positions_<MARKET>_<date>.json` for actual shares, account split, cost basis, market value, P&L, cash and NAV. Read the active shortlist from `data/shortlist/<MARKET>.json`; do not infer holdings from shortlist membership.
    - Run `stage2_scanner.py` into `<RUN_DIR>/cache/stage2_<MARKET>_<date>.json` (`IN --min-mcap 1000`; `US --min-mcap 1.0`), then snapshot the target company, all current holdings and active shortlist candidates. After identifying outside peers in Chapters 4 and 7, add them to a fresh `stock_snapshot.py` pass before assigning technical levels.
2. **Pull Live Consumer-Tool & 10-Year Financial Snapshot (`scripts/stock_snapshot.py`):**
   ```bash
   .venv/bin/python scripts/stock_snapshot.py \
     --market <MARKET> \
     --symbols <SYMBOL> \
      --from-shortlist --from-holdings \
      --stage2-file "<RUN_DIR>/cache/stage2_<MARKET>_<date>.json" \
     --out "<RUN_DIR>/cache/snapshots_<MARKET>_<date>.json"
   ```
3. **Two-Sided Multi-Source Research:**
   - Pull primary filings (Screener.in 10-year tables, BSE/NSE or SEC EDGAR 10-K/10-Q, investor presentations, latest concall transcripts) AND run dedicated web searches for both the **Bull thesis** and the **Bear/Skeptic thesis** (short-seller critiques, working-capital/cash conversion debates, competitive threats, analyst downgrades).
4. **Evidence-First Chapter Authoring (`<RUN_DIR>/work/<SYMBOL>/`):**
   - Author **Chapters 1–8 first** (`chapters/ch01.json` .. `chapters/ch08.json`) so the research and technicals are complete before any decision exists. Write the narrative fields (`epigraph`, `book_paragraphs`, `book_callouts`, `book_subsections`) for each as you go.
    - Author **Chapter 9** (`chapters/ch09.json`): the Bull vs. Bear steelman, probability-weighted outcomes, explicit 3-horizon verdict, current position action, alert plan, and capital opportunity-cost discussion. The compiler appends the validated position and allocation tables to this chapter and the same decision summary to the PDF.
    - **Derive** `spine.json` from Chapter 9, including the two verdicts and structured alert/redeployment fields, then write `chapters/ch00.json` (the Prologue) last from that spine.
5. **Compile Both Synchronized Formats (`scripts/dossier_builder_template.py`):**
   ```bash
   .venv/bin/python scripts/dossier_builder_template.py \
      --spec "<RUN_DIR>/work/<SYMBOL>" \
      --snapshot "<RUN_DIR>/cache/snapshots_<MARKET>_<date>.json" \
      --facts "<RUN_DIR>/cache/facts_<MARKET>_<date>.json" \
      --positions "<RUN_DIR>/cache/positions_<MARKET>_<date>.json" \
      --shortlist "data/shortlist/<MARKET>.json" \
      --out "docs/blogs/<MARKET>/<SYMBOL>_dossier.html"
   ```
   This writes the Web Dossier and the `_book.pdf` companion. It does not emit `_book.html`, `.epub`, or `.md`.
6. **Update Records and Run Quality Gates:**
    - `.venv/bin/python scripts/readability_check.py docs/blogs/<MARKET>/<SYMBOL>_dossier.html`
    - `.venv/bin/python scripts/citation_check.py docs/blogs/<MARKET>/<SYMBOL>_dossier.html --research <RUN_DIR>/cache/research_<MARKET>_<date>.json --allow-stale-asof --min-sources 25`
    - Run `scripts/portal_publish.py`'s modern-layout check before marking the dossier complete.
    - Update the matching watchlist row when one exists; add or update an active-watchlist row for an outside name only when it merits future monitoring. Add to the shortlist only after full underwriting qualifies it. A rejected name should not be left in the active queue. Validate with `scripts/data_layer.py --market <MARKET> --validate` and `scripts/validate_data.py`.
