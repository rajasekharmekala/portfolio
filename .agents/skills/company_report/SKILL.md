---
name: company_report
description: >-
  Deep-research company monograph and multi-horizon Stage 2 investment dossier
  for one listed company (IN or US), delivered in 4 synchronized formats
  (Web Research Dossier HTML, Audiobook/Book Reader HTML, EPUB 3 e-book, and
  Narrative Markdown) at book-length depth (12,000–18,000 words, ~75–90 min
  audiobook). Explains what the company does, every business segment with
  revenue/profit mix and concrete real-world examples, distribution and unit
  economics, 5–10 year financial forensics, Why the Price Is What It Is, and
  unbiased Two-Sided (Bull vs. Bear) investment judgment across Short-Term
  Trading/Momentum, Medium-Term Inflection, and Long-Term Compounding (or Stay Away).
---

> **Design & 5-Edition Compiler (binding):** read `../_shared/REPORT_DESIGN.md`. Author the monograph chapter-by-chapter in `<RUN_DIR>/work/<SYMBOL>/` (`spine.json` + `chapters/ch00.json` .. `ch09.json`) and compile all five synchronized editions with `scripts/dossier_builder_template.py --spec <RUN_DIR>/work/<SYMBOL> --snapshot <snapshots.json> --out docs/blogs/<MARKET>/<SYMBOL>_dossier.html`:
> 1. `docs/blogs/<MARKET>/<SYMBOL>_dossier.html` — Web Research Desk Edition (`research-desk-v1`: 10-year tables, unit-economics matrices, interactive TradingView chart, External Learning Hub, inline `[N]` citations).
> 2. `docs/blogs/<MARKET>/<SYMBOL>_book.html` — Masterclass Companion Book & Audiobook Web Reader (`masterclass-book-v1`: warm cream `#fdfbf7` paper, `Cinzel` / `Newsreader` literary serif typography, full Book Cover page, Roman-numeral TOC with 5-stat strip, chapter Epigraph Quotes, Drop-Caps, `NARRATOR'S REFLECTION`, `GLOBAL PARALLEL (US/INDIA/EUROPE)`, and `MENTAL MODEL` boxes, plus interactive Web Speech audio player).
> 3. `docs/blogs/<MARKET>/<SYMBOL>_book.pdf` — WeasyPrint Masterclass Companion PDF Book.
> 4. `docs/blogs/<MARKET>/<SYMBOL>_book.epub` — Standalone Masterclass EPUB 3 e-book.
> 5. `docs/blogs/<MARKET>/<SYMBOL>_book.md` — Narrative Masterclass Markdown book for `book-companion` / `live-companion`.

> **Lively Audiobook & Masterclass Book Narrative Rules (binding for `book_paragraphs`, `epigraph`, and `book_callouts`):**
> - **Second-Person Mentor Voice:** Write the Book chapters as a seasoned institutional analyst sitting across the desk from the listener (`"you and I"`), using engaging rhetorical questions, vivid factory/customer walkthroughs, and clear spoken transitions.
> - **3 Layers of Quotations:** (1) Every chapter opens with a framed `epigraph` quote (`{"quote": "...", "author": "..."}`); (2) weave verbatim CEO/CFO concall quotes and investor maxims into the prose; (3) include `NARRATOR'S REFLECTION` callout boxes (`"kind": "reflection"`).
> - **Global Parallel Company Examples (US, India, and Europe):** Every chapter must connect the company's economics, moat, working-capital cycle, or valuation to concrete historical parallels across the US, India, or Europe (via prose and `"kind": "parallel"` callout boxes) so the listener grasps how similar business models and stock setups have played out globally.

> **Zero LLM Math (binding):** never compute moving averages, RSI, volume multiples, or financial ratios in your head. All technical and valuation figures must come from `scripts/stock_snapshot.py` (TradingView + Screener.in / Finviz + TheWrap Stage 2 snapshot) and verified primary filings.

> **Unbiased Two-Sided Research & Independent Judgment (binding):**
> - Actively search **both sides of the aisle**: (1) the Bull narrative (management guidance, secular tailwinds, operating leverage, order book) and (2) the Bear / Skeptic narrative (working-capital/DSO stretch, cash-flow gaps, cyclicality, customer/platform concentration, competitive threats, valuation stretch).
> - Never cheerlead management and never pad paragraphs with robotic defensive disclaimers ("This is a company claim, not verified"). Instead, attribute claims cleanly, weigh both sides against the financial record, and state **our own independent judgment** based on the probability-weighted likely outcomes.

> **Concrete Segment & Distribution Walkthroughs (binding):**
> - Every business segment in Chapter 2 must include its share of revenue/profit AND **at least one concrete, end-to-end real-world example** (who the customer is, what problem they face, what exact product/service they buy, how it is engineered/built/delivered, and how it is priced).
> - Chapter 3 must explain **distribution and go-to-market mechanics** (direct sales, channel/MSP partners, dealer networks, OEM qualification, geographical delivery) and trace a worked **$100 / ₹100 revenue-to-free-cash-flow waterfall**.

# 10-Chapter Institutional Monograph & Audiobook Blueprint (12,000–18,000 Words)

Both the Web Dossier (`_dossier.html`) and the Book/Audiobook Edition (`_book.html`, `.epub`, `.md`) follow the same 10-chapter structure and share **100% identical numbers, verdicts, and Short / Medium / Long-Term outlooks**:

| Ch # | ID | Target Words | Web Dossier Section (`_dossier.html`) | Book / Audiobook Chapter (`_book.html`, `.epub`, `.md`) | Core Content, Examples & Investment Judgment |
|---|---|---|---|---|---|
| 0 | `ch-0` | 700–1,000 | **0. Executive Thesis, Price Verdict & Opportunity Matrix** | **Prologue: The Business, The Price & Our Independent Verdict** | What the company does, why the stock trades at today's price, the core Bull vs. Bear debate, our independent judgment across **Short-Term Trade**, **Medium-Term Inflection**, and **Long-Term Compounding** (or **Stay Away**), and exact No-FOMO levels. |
| 1 | `ch-1` | 1,400–2,000 | **1. Origin, Corporate Evolution & Past Stock Cycles** | **Chapter 1: How the Business & Stock Got Here — Past Cycles & Pivots** | How the company was built, major strategic pivots and acquisitions, and how its revenue, margins, and stock price performed across prior boom-bust cycles to arrive at today's market cap. |
| 2 | `ch-2` | 1,800–2,500 | **2. What the Company Does: Segments, Revenue Mix & Concrete Examples** | **Chapter 2: Inside Every Segment — Products, Customers & Real-World Examples** | Deep segment-by-segment breakdown: exact share of revenue/profit by vertical and geography; plain-English explanation of each segment; and **at least one concrete, end-to-end real-world example per segment** showing who buys, why they buy, and how the product/service works in practice. |
| 3 | `ch-3` | 1,400–2,000 | **3. Distribution, Supply Chain & Unit Economics** | **Chapter 3: How It Is Sold & Delivered — Distribution & Unit Economics** | Distribution & Go-To-Market anatomy: direct sales vs. dealers/distributors/channel partners, supply-chain/manufacturing footprint, customer qualification, pricing model, billing/DSO cycle, and a worked **$100 / ₹100 revenue-to-free-cash-flow waterfall**. |
| 4 | `ch-4` | 1,300–1,800 | **4. Industry Structure, Competitive Moat & External Learning Hub** | **Chapter 4: The Battlefield — Rivals, Switching Costs & Moat Reality** | Unbiased assessment of competitive advantages vs. vulnerabilities: market share shifts, customer lock-in, pricing power vs. competitor pushback, and the curated **External Learning Hub** (product demos, factory tours, interviews, filings). |
| 5 | `ch-5` | 1,300–1,800 | **5. Leading KPIs, Structural Potential & CEO Walk-the-Talk Audit** | **Chapter 5: Management on Trial — Leading KPIs & Walking the Talk** | The 5–6 operational KPIs that lead financial results; capacity utilization & TAM runway; and an unbiased 3–5 year audit comparing what the CEO/CFO promised against what was actually delivered. |
| 6 | `ch-6` | 1,500–2,100 | **6. 10-Year Financial Forensics, Cash Conversion & Balance Sheet** | **Chapter 6: Following the Cash — 10-Year Financials & Earnings Quality** | Full 5–10 year P&L, margin bridge, balance sheet & debt/lease forensics, working capital & DSO trends, CFO-to-PAT conversion, ROIC/ROCE vs. WACC, and share dilution—separating genuine cash compounding from accounting optics. |
| 7 | `ch-7` | 1,300–1,800 | **7. Why the Price Is What It Is: Valuation, Reverse DCF & Peer Comps** | **Chapter 7: Why the Stock Trades Here — Market Expectations vs. Peers** | Deconstructs today's stock price: historical valuation multiple bands, Reverse DCF (what growth/margin today's price already assumes), and quantitative head-to-head comparison against 3–5 listed peers. |
| 8 | `ch-8` | 1,100–1,500 | **8. Stage 2 Technical Structure, Institutional Flow & Momentum Setup** | **Chapter 8: Reading the Tape — Trend, Volume & Momentum Opportunity** | Stan Weinstein Stage (1, 2, 3, or 4), 30-week SMA / 10-week EMA / 50 & 200-DMA structure, volume accumulation vs. distribution, relative strength, and whether there is an actionable short-term trading/momentum edge right now. |
| 9 | `ch-9` | 1,600–2,200 | **9. Both Sides of the Aisle, Likely Outcomes & No-FOMO Action Plan** | **Chapter 9: Bull vs. Bear, Likely Outcomes & Our Action Plan** | Side-by-side steelman of Bull vs. Bear narratives + **Our Independent Judgment**; probability-weighted Bull / Base / Bear outcomes; explicit verdict across **Short-Term Trading (1–12w)**, **Medium-Term Inflection (3–18m)**, and **Long-Term Compounding (3–10y)** (or **Stay Away**); and exact No-FOMO execution levels & triggers. |

---

## Step-by-Step Execution Protocol

1. **Pull Live Consumer-Tool & 10-Year Financial Snapshot (`scripts/stock_snapshot.py`):**
   ```bash
   .venv/bin/python scripts/stock_snapshot.py \
     --market <MARKET> \
     --symbols <SYMBOL> \
     --stage2-file data/views/stage2_<MARKET>_latest.json \
     --out "<RUN_DIR>/cache/snapshots_<MARKET>_<date>.json"
   ```
2. **Two-Sided Multi-Source Research:**
   - Pull primary filings (Screener.in 10-year tables, BSE/NSE or SEC EDGAR 10-K/10-Q, investor presentations, latest concall transcripts) AND run dedicated web searches for both the **Bull thesis** and the **Bear/Skeptic thesis** (short-seller critiques, working-capital/cash conversion debates, competitive threats, analyst downgrades).
3. **Multi-Stage Chapter Authoring (`<RUN_DIR>/work/<SYMBOL>/`):**
   - Write `spine.json` and author `chapters/ch00.json` through `chapters/ch09.json` individually so each chapter achieves full 1,200–2,500 word analytical and narrative depth.
4. **Compile All 4 Synchronized Formats (`scripts/dossier_builder_template.py`):**
   ```bash
   .venv/bin/python scripts/dossier_builder_template.py \
     --spec "<RUN_DIR>/work/<SYMBOL>" \
     --snapshot "<RUN_DIR>/cache/snapshots_<MARKET>_<date>.json" \
     --out "docs/blogs/<MARKET>/<SYMBOL>_dossier.html"
   ```
5. **Run Quality Gates:**
   - `.venv/bin/python scripts/readability_check.py docs/blogs/<MARKET>/<SYMBOL>_dossier.html`
   - `.venv/bin/python scripts/readability_check.py docs/blogs/<MARKET>/<SYMBOL>_book.html --book --min-words 11000`
   - `.venv/bin/python scripts/citation_check.py docs/blogs/<MARKET>/<SYMBOL>_dossier.html --research <RUN_DIR>/cache/research_<MARKET>_<date>.json --allow-stale-asof`
