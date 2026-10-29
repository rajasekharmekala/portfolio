---
name: company_report
description: >-
  Deep-research company monograph and multi-horizon Stage 2 investment dossier
  for one listed company (IN or US), written like a small book on the company:
  what they do and how each vertical operates day-to-day, curated links to
  external websites/videos/presentations to learn more, the true operational
  KPIs and story of the business, whether the company is reaching its potential
  and the CEOs are walking the talk, Screener.in/Finviz financials & valuation,
  TheWrap Stage 2 & TradingView technical readout, and a No-FOMO execution plan
  (Immediate Buy vs. Wait for Support).
---

> **Design (binding):** read `../_shared/REPORT_DESIGN.md`. Build the dossier via `scripts/dossier_builder_template.py --spec <spec.json> --snapshot <snapshots.json> --out docs/blogs/<MARKET>/<SYMBOL>_dossier.html` (which calls `scripts/assemble_report.py --market <MARKET> --kind dossier --workflow "Company research" --as-of <verified-session-date>`). Never copy an old dossier shell.

> **Zero LLM Math (binding):** never compute moving averages, RSI, volume multiples, or financial ratios in your head. All technical and valuation figures must come from `scripts/stock_snapshot.py` (TradingView + Screener.in / Finviz + TheWrap Stage 2 snapshot) and verified primary filings.

> **Voice & Readability (binding):** read `../_shared/REPORT_VOICE.md`. Write like an investigative business biographer and institutional investor explaining the company to a smart, curious reader. Define technical terms at first use per `.agents/config/glossary.json`, avoid banned filler phrases, and ensure `scripts/readability_check.py` and `scripts/citation_check.py` pass.

# Deep Business-Monograph & Multi-Horizon Company Dossier (`IN` & `US`)

Your deliverable is a standalone, self-contained HTML monograph saved directly in:
`docs/blogs/<MARKET>/<SYMBOL>_dossier.html` (e.g. `docs/blogs/IN/FSL_dossier.html`, `docs/blogs/US/AVPT_dossier.html`).

---

## 1. Monograph Book Structure (Binding)

Each dossier is a complete deep-research monograph ("like a small book on the company itself") combined with a multi-horizon Stage 2 & valuation view:

| Order | ID | Chapter Title | Core Questions Answered |
|---|---|---|---|
| 0 | `primer` | **Before you read** | 3–5 sentences: what the company does, our multi-horizon conclusion, and what would invalidate it. |
| 1 | `ch-1` | **1. What the company does & day-to-day vertical operations** | What products/services do they sell? Who pays and why? How does each business vertical actually work day-to-day (raw materials/sourcing, manufacturing/engineering workflows, distribution, customer onboarding, billing & working-capital cycle)? Ends with a plain-English glossary. |
| 2 | `ch-2` | **2. Competitive moat, industry structure & external learning hub** | Why does this company win or lose against competitors? Includes the **External Learning Hub** table with clickable links to official product pages, YouTube factory tours / CEO interviews / product explainers, investor presentations, and concall transcripts so the reader can explore further. |
| 2B | `ch-2b` | **2B. Operational business KPIs, structural potential & CEO walk-the-talk** | What are the 4–6 real operational KPIs that drive this business? **Is the company reaching its structural potential?** (Capacity utilization, TAM capture, margin ceiling). **Are the CEOs walking the talk?** Forensic audit comparing past management guidance/promises over the last 2–3 years against actual delivered results. |
| 3 | `ch-3` | **3. Financial trajectory & valuation sanity check** | Multi-year revenue, operating profit, margins, PAT/EPS, cash flow, and balance-sheet tables grounded in Screener.in (`IN`) or Finviz / SEC filings (`US`), peer comparison matrix (3–5 direct peers), and whether the current valuation multiple is cheap, fair, or rich relative to growth. |
| 4 | `ch-4` | **4. Stage 2 trend & TradingView technical structure** | Auto-populated by `dossier_builder_template.py` from `stock_snapshot.py`: TheWrap Stage 2 sector/stock breadth, TradingView 30-week SMA, 10-week EMA, 20/50/200-day SMAs, RSI(14), relative volume, classic pivots, and deterministic No-FOMO support distance. |
| 5 | `ch-5` | **5. Multi-horizon investment view: short-term momentum, medium-term catalysts & scenarios** | **Short-term view (1–12 weeks):** momentum, volume, extension from support. **Medium-term view (3–18 months):** order book / product cycle catalysts, earnings inflection. **Long-term view (2–5 years):** structural compounding potential. Plus Bull / Base / Bear scenarios. |
| 6 | `ch-6` | **6. Key risks, thesis breakers & bear case** | The strongest honest bear arguments (demand, execution, margin compression, balance sheet, technical breakdown) and the single hinge claim the thesis rests on. |
| 7 | `ch-7` | **7. What we would do, and when (No-FOMO action plan)** | Clear decision (`IMMEDIATE_BUY` at CMP vs. `WAIT_FOR_SUPPORT` / `ACCUMULATE_ON_DIP` limit zone vs. `REJECTED`), exact TradingView support buy zone (`20D EMA` / `10W EMA` / `50D SMA`), invalidation stop, risk-unit sizing, let-winners-run rule, and `<p class="trigger">` conditions. |
| 8 | `notes` | **Notes and sources** | 25–40+ numbered primary filings, concalls, Screener/Finviz/TradingView snapshots, and external web/video references. |

---

## 2. Step-by-Step Execution Protocol

### Step 1: Pull Live Browser & Consumer-Tool Snapshot (`scripts/stock_snapshot.py`)
Ensure you have the live TradingView + Screener.in/Finviz + TheWrap Stage 2 snapshot for `<SYMBOL>`:
```bash
.venv/bin/python scripts/stock_snapshot.py \
  --market <MARKET> \
  --symbols <SYMBOL> \
  --stage2-file data/views/stage2_<MARKET>_latest.json \
  --out "<RUN_DIR>/cache/snapshots_<MARKET>_<date>.json"
```

### Step 2: Deep Multi-Source Research & External Link Discovery
1. **Financials & Filings:**
   - **IN:** Fetch Screener.in (`https://www.screener.in/company/<SYMBOL>/consolidated/` or standalone), BSE/NSE investor presentations, annual reports, and concall transcripts.
   - **US:** Fetch Finviz (`https://finviz.com/quote.ashx?t=<SYMBOL>`), SEC EDGAR 10-K/10-Q filings, investor day presentations, and earnings call transcripts.
2. **Day-to-Day Vertical Processes & External Learning Hub (`search_web`):**
   - Search for the company's official product/vertical pages, YouTube factory tours, management interviews, industry conference talks, and customer case studies.
   - Cache fetched pages with `scripts/fetch_cache.py` and log research records in `<RUN_DIR>/cache/research_<MARKET>_<date>.json` using `scripts/research_log.py`.

### Step 3: Build the Dossier via `scripts/dossier_builder_template.py`
Write `<RUN_DIR>/work/<SYMBOL>_spec.json` and render the HTML dossier:
```bash
.venv/bin/python scripts/dossier_builder_template.py \
  --spec "<RUN_DIR>/work/<SYMBOL>_spec.json" \
  --snapshot "<RUN_DIR>/cache/snapshots_<MARKET>_<date>.json" \
  --out "docs/blogs/<MARKET>/<SYMBOL>_dossier.html"
```

### Step 4: Run Quality Gates & Reviewer
1. `.venv/bin/python scripts/readability_check.py docs/blogs/<MARKET>/<SYMBOL>_dossier.html`
2. `.venv/bin/python scripts/citation_check.py docs/blogs/<MARKET>/<SYMBOL>_dossier.html --research <RUN_DIR>/cache/research_<MARKET>_<date>.json --allow-stale-asof`
3. `.venv/bin/python scripts/review_packet.py build --report docs/blogs/<MARKET>/<SYMBOL>_dossier.html --kind dossier --snapshots <RUN_DIR>/cache/snapshots_<MARKET>_<date>.json --research <RUN_DIR>/cache/research_<MARKET>_<date>.json --out-dir <RUN_DIR>/review/round_1 --round 1 --symbol <SYMBOL>`
4. Run `report_reviewer` and `red_team` per `../_shared/REVIEWER_OPERATIONS.md`.
