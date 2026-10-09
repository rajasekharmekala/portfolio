# Portfolio Research System: Improvement Plan (v2)

Prepared 2026-10-08. Supersedes v1. This is a plan only. No file in the system has been changed by it. The work is split into work packages in section 8 for smaller agents to carry out.

## 0. Decisions already made

1. **Citations are mandatory and machine-checked.** Every number and every factual claim in a report links to a source that was fetched during the run. A value with no fetched source is written as "not verified" and is never guessed. No hallucinated figure reaches a published report.
2. **Displacement is advisory.** The system recommends a swap and gives the reasons. You place the trade.
3. **The constitution is brought into line with the skills.** Where the constitution and the skills disagree, the skills' numbers are copied into the constitution, after the conflicts inside the skills are resolved (section 3).
4. **Investment philosophy is momentum-first.** You want to own stocks that are already in momentum, or are about to enter it. Holding periods vary: some positions are short-term (roughly 3 to 12 months), some long-term (3 to 5 years), and each must still be in momentum or entering it.
5. **Company reports must be readable by a beginner.** They should read like a book, not a spreadsheet. Each report explains reasons, consequences, estimates, and the reasoning behind each estimate. Each company gets a report shaped to its own business.

## 1. The momentum-first investment rule

The constitution already puts price momentum at the top of the decision order (§9), but the skills do not apply it as a gate. A stock with weak momentum can pass the fundamental gates and still be allocated. This plan changes that.

Every candidate for any bucket must pass one of two momentum tests, both computed in code from the frozen price data.

**Test A: In momentum now.** The stock is in a confirmed Stage 2 uptrend (Weinstein terms: price above a rising 50-day and 200-day average, with the 50-day above the 200-day), with relative strength against the benchmark at or above a set rank, and the price is within the support band defined in section 3.

**Test B: Entering momentum.** The stock is in a Stage 1 base that is turning up. Required: the 50-day average has stopped falling and is flattening or rising; relative strength is rising over the last 4 to 8 weeks; the price is within about 1 ATR of the base pivot (the high of the base); volume is drying up during the base and expanding on the approach to the pivot. A stock that passes Test B gets a conditional entry: it is allocated only on a confirmed breakout or a retest of the pivot, not before.

A stock that fails both tests is not allocated, however good its business. The company report still gets written, and it records what would have to happen for the stock to pass.

Horizon is a separate tag, not a different rule. Each name is tagged `SHORT` (expected 3 to 12 months) or `LONG` (3 to 5 years). A `LONG` name must still pass Test A or B on every review. If a long-term name leaves momentum for a sustained period, the review flags it, and the thesis must be re-confirmed before it is held.

The exact thresholds for "relative strength rank", "flattening", and "within 1 ATR" are placeholders. They are set once in the scoring config (work package W4) and must be written into the constitution.

## 2. Diagnosis (unchanged from v1)

- **Numbers do not reconcile.** In the US shortlist, 23 of 37 rows store an asymmetry ratio that cannot be recomputed from the same row's CMP, stop and target. CRWD is stored at 3.6 and recomputes to 0.36. ORCL is stored at 3.2 and recomputes to 1.11.
- **Verdicts break the allocator's rules.** Thirteen US rows say accumulate or buy while 1.4 to 1.9 ATR above support. The allocator gives 0% to anything above 1.2 ATR.
- **Schema drift.** US and IN use different field names (`cmp_usd` vs `cmp`, `roic_pct` vs `roce_pct`). Stage labels appear in at least eight forms. IN verdicts include emoji. Two IN asymmetry values are not numbers. Some rows have no as-of date, and some are dated February 2025.
- **Dossier links are broken.** 35 of 37 US rows point to `googledrive/blogs/`, but the files are in `docs/blogs/`.
- **Dossiers are thin.** ADBE's has 5 citations against a required 25 to 40. NVDA's has 30. ADBE's has no readable as-of date. The shortlist records ADBE at a P/E of 8.6, which looks implausible for Adobe and must be source-checked before anyone acts on it.
- **Thresholds conflict** (section 3).
- **Displacement has no pipeline** in this repository. The Compare tab that does it is not in this folder.
- **Research is not traceable.** The workflow asks for a research cache with a source URL and as-of date per value, but none is in the repository.

## 3. Constitution changes: aligning with the skills

The table lists each rule the constitution states, the value the skills use, and the change to make. Where the two skills (US and IN) disagree, the row is marked **Conflict** and needs one value chosen. I recommend the value in the last column; you can override any of them.

| Constitution section | Current constitution | Skill value | Proposed constitution text | Status |
|---|---|---|---|---|
| §4 Core target | ~40% | US 35–40%; IN 30–40% | 35–40% (US); 30–40% (IN) | Per market |
| §4 Short-term/momentum target | ~25% | US 25–35%; IN 50–65% | Conflict. Recommend US 25–35%, IN 50–65%, reflecting the momentum-first rule | Conflict: IN and US differ widely |
| §4 Leveraged target | ~20% | US 20–25%, max 30% | 20–25%, hard max 30% | Match |
| §4 Options target | ~15% | US LEAPS 5–10%, max 10% | 5–10%, hard max 10% (LEAPS only; short-dated options are outside this cap) | Match |
| §4/§15 Cash | 0–5% normal, 5–10% when opportunities are scarce | US and IN 5–10%, scaled to VIX (<15: 5%; 15–22: 7.5%; >22: 10%+) | 5–10% with the VIX ladder | Match |
| §5 Core concentration | 5–10 companies | IN 6–12 names total | Core 5–10 names; total portfolio 6–12 names | Match |
| §5 Max position | ~10% of total | US Tier 1: 7–10%, cap $10,000; IN Tier 1: 8–12.5%, max 15% | 10% hard cap for any single name, all markets. IN "max 15%" removed | Conflict: IN skill exceeds the constitution |
| Position size, tiers | none | US: Tier 1 7–10%, Tier 2 4–6.5%, Tier 3 2–3.5%, Tier 4 1–2% | Adopt the US tier table for both markets, with the cap in dollars removed in favour of the % cap | Recommended |
| Asymmetry floor | none stated | Core ≥3.0:1; Tactical ≥3.5:1; IN Tier 3 ≥4.0:1 | Core ≥3.0:1; Tactical ≥3.5:1 for both markets | Conflict: IN Tier 3 ≥4.0 |
| Support proximity | "≤0.5 × ATR" for buying near support | US has two ladders: 0.5/1.2 ATR, and 0.5/1.0/1.5 ATR. IN uses 0.5/1.0/1.5 | Single ladder: ≤0.5 ATR full size; 0.5–1.0 ATR standard size; 1.0–1.2 ATR limit order at reduced size; >1.2 ATR no buy | Conflict: the US skill contradicts itself |
| Stop placement | not stated | Core: below the lower of swing low and 50/200-day minus 1 ATR; Tactical: lower of swing low and 20/50-day minus 0.5 ATR | Copy these as written | Match |
| Core horizon | 3–5 years | Core as described | 3–5 years, with a 6–12 month thesis checkpoint | Match |
| Catalyst window | "6–12 months" | not stated | Keep | No change |

Two further points for the constitution. First, the "Core does not mean passive" principle stays. Second, §9 is rewritten so that the momentum test in section 1 comes before fundamentals as a gate, not just as a priority. Fundamentals still have to pass their own floors.

## 4. The pipeline (revised)

**Stage 0: Universe.** The existing ledger screen (`market_facts.py`) produces the candidate list. This stage already works.

**Stage 1: Frozen snapshot.** One record per candidate with prices, technicals, and as-of dates, all from the same verified session. Every technical value is computed in code. The record is hashed.

**Stage 2: Momentum gate.** Tests A and B from section 1 are applied in code. Names that fail both stop here. The company report is still written, in a shorter form, to record why.

**Stage 3: Deep research.** One independent agent per company, run in parallel. It fetches filings and pages in full, not search snippets, and returns a fixed JSON record in which every value carries a source (section 5). Coverage: at least three years of revenue, margins, cash flow and net debt, and the latest quarter.

**Stage 4: Trend assessment.** The agent records sector trend, relative strength, estimate revisions and the next earnings date, each with its evidence.

**Stage 5: Rally potential.** Bull, base and bear cases, each with a named driver (for example, forward EPS times a multiple taken from the company's own five-year history, or a measured move from the base). Each case has a probability. Expected return and downside are calculated in code. The six Core questions in constitution §5 each have a fixed field.

**Stage 6: Gates and score.** Hard gates (ROIC, cash conversion, leverage, momentum, support distance, asymmetry) and a weighted score. Gates and weights live in one config file used by both markets.

**Stage 7: Shortlist.** Ranked by score, with the gate results for each name. A row shows the momentum test it passed (A or B), its horizon tag, and whether it is a full-size, reduced-size, or conditional entry.

**Stage 8: Displacement (advisory).** Each holding goes through Stages 3 to 6, so incumbent and candidate are scored on the same rubric. A swap is recommended only if: the candidate's score beats the incumbent's by a set margin; the candidate passes its momentum test; the candidate is at support; the position caps in section 3 still hold after the swap; and the expected-return gain exceeds the costs, including tax and slippage. Output is DISPLACE, HOLD or WATCH, with the numbers behind it.

**Stage 9: Verification.** Four checks before publication: (a) a recomputation of every ratio, distance, weight, and target, within a stated tolerance; (b) a citation check (section 5); (c) three reviewer passes, source, consistency and tone, as today; (d) a red-team agent whose only job is to find the strongest reason the thesis is wrong. Any failure blocks publication.

**Stage 10: Decision log.** Each shortlist entry or swap records thesis, expected return, invalidation level and date. Outcomes are compared with the benchmark at 3, 6 and 12 months.

## 5. Citation and anti-hallucination rules

These rules apply to every report, dossier and shortlist row.

1. **Fetch before you cite.** A source must be fetched during the run and stored in the run directory with its URL, retrieval time and a content hash. A URL seen only in search results cannot be cited.
2. **Quote, then compute.** Each number in a report is traced to a stored source and the exact passage it came from. Derived numbers (ratios, growth rates, averages) show the formula and the inputs, and each input has its own citation.
3. **No value, no guess.** If a value cannot be found in a fetched source, the report says "not verified" and gives the reason. It does not estimate it silently. An estimate, such as a future EPS, is labelled as an estimate, names its method, and cites the inputs.
4. **Machine check.** A script confirms that every cited URL is in the cache and that the cited value appears in the stored text. A failure blocks the report.
5. **Citation floor.** A full company report needs at least 25 distinct primary sources. For US names: SEC filings (10-K, 10-Q, 8-K, proxy), earnings releases, investor presentations, and transcripts. For IN names: BSE/NSE filings, annual reports, quarterly results, investor presentations, and credit-rating releases. Aggregator pages can support a number but cannot be the only source for it.
6. **Dates on everything.** Every price and every fact carries an as-of date. Reports state the as-of session at the top.
7. **Structured fundamentals where possible.** For US names, SEC EDGAR XBRL data is the preferred source for financial statements. For IN names, the BSE/NSE filings. Search-and-fetch of aggregator pages is the fallback, not the first choice.

## 6. Company report redesign: a readable book

### 6.1 The reader

The reader is a capable adult with no finance training. Each report must work for that person. Plain English comes first, technical terms come second, and every technical term is defined the first time it appears. Target reading level: roughly the level of a good popular-science book. Short sentences. One idea per paragraph.

### 6.2 Structure: the book

Each report reads as chapters, and each chapter answers one question the reader would ask. The chapters are fixed in order, but each company's content inside them is written for that business.

- **Before you read.** Three to five sentences: what the company is, what the report concludes, and what would make the conclusion wrong.
- **Chapter 1: What the company does.** Explained as if to a friend. Who pays it, for what, and how it makes money. Include a short glossary of the terms used.
- **Chapter 2: Why the business is strong or weak.** The competitive position, explained with the reasons and the evidence. Each claim cites a source.
- **Chapter 3: The numbers, in plain words.** Revenue, profit, cash and debt over five years. Each table is followed by a paragraph explaining what it means and what it does not show.
- **Chapter 4: What the price is doing.** The momentum test result in plain words (for example, "the price is above its 50-day average, which has been rising for 8 weeks"). Each technical term is defined. The consequence is stated: what the chart would need to do to confirm or reject the idea.
- **Chapter 5: What could happen next.** Bull, base and bear cases. For each: the story in plain words, the driver, the number, the probability, and the reason for that probability. Then the expected outcome in dollars or rupees.
- **Chapter 6: Why these estimates might be wrong.** Each estimate's weakest assumption, what evidence would show it is wrong, and when that evidence will be known (for example, the next earnings date).
- **Chapter 7: What we would do, and when.** The decision (buy, wait, hold, trim, exit, or displace), the price or event that would change it, the entry zone, stop, and targets, each with the reason.
- **Notes and sources.** Numbered, with the page or section for each filing.

### 6.3 Every estimate shows its working

Each estimate in the report must include five things, in this order:

1. The number, in plain words.
2. How it was calculated, in one or two sentences.
3. The inputs, each cited.
4. The range: what the number would be in the bull and bear case, and why.
5. The consequence: what changes for the reader if the number is off.

Example pattern, not real data: "We estimate next year's profit per share at $X. We got this by taking this year's profit (cited), adding the growth the company guided to (cited), and assuming the margin stays where it was last year (cited). If margins fall by 2 points, profit would be about $Y, and the case for buying would weaken."

### 6.4 Company-specific layout

Companies differ, so the report adapts. The chapter structure stays, but the content inside each chapter follows the business. A bank is judged on loan quality and net interest margin. A chip company is judged on order backlog and gross margin. A software company is judged on recurring revenue and free cash flow. A leveraged ETF is not analysed as a company at all, and its report covers the index, the trend, and the decay risk. The skill file should hold a short list of the key metrics for each major sector. The writer chooses from that list and explains why the metrics it picked matter for this company.

### 6.5 Readability checks

The verifier (Stage 9) runs these checks in code and flags failures:

- Reading level of each chapter is below an agreed threshold, using a standard readability formula.
- Each technical term in a fixed glossary list is defined on first use.
- No chapter is a bare table. Each table is followed by at least one explanatory paragraph.
- Each estimate contains the five items in 6.3.
- Each decision in Chapter 7 names the event or price that would change it.
- Banned filler phrases from REPORT_VOICE are absent, and the emoji and status colours follow the palette.

Readability is checked by code and then by the tone reviewer. A report does not pass on the reviewer's opinion alone.

## 7. Displacement, advisory form

The output is a one-page memo. It states the recommendation (DISPLACE, HOLD, or WATCH), the holding and candidate side by side on the same scorecard, the expected return of each with its range, the transaction costs, the change in portfolio caps and theme exposure, and the single condition that would reverse the advice. You make the decision and record it in the decision log.

## 8. Work packages for smaller agents

Each package has a clear target and a pass test. They are ordered by dependency.

**W1. Schema and data cleanup (no behaviour change).**
Files: `data/shortlist/US.json`, `data/shortlist/IN.json`, `data/watchlist/US.json`, `data/watchlist/IN.json`, and new `scripts/schemas/`.
Do: define one JSON schema per record type shared by both markets. Map field names to one set. Normalise `action_verdict`, `weinstein_stage` and `kpi_health` to fixed enums. Remove emoji. Convert non-numeric asymmetry values. Add missing as-of dates, or mark them unknown.
Pass: schema validation passes for every row; no row has an as-of date older than the latest session without a flag.

**W2. Recompute checker.**
File: new `scripts/recompute_check.py`.
Do: recompute asymmetry, ATR distance, weights and targets from stored fields; report every mismatch beyond tolerance.
Pass: runs on current data and lists the 23 known US mismatches plus any IN mismatches; fixes are then applied and the checker reports zero.

**W3. Dossier path and citation validator.**
Files: `scripts/build_dossier_portal.py`, `scripts/validate_report.py`, and the dossier record paths in shortlist JSON.
Do: point dossier links to `docs/blogs/`. Add a citation checker: counts distinct primary sources, confirms each cited URL is in the run cache, and checks that the cited value appears in the cached text. Add the as-of check.
Pass: 35 broken links fixed; ADBE, UNH and any other dossier below 25 citations fails validation.

**W4. Constitution alignment and scoring config.**
Files: `Portfolio Research System/00_Investment_Philosophy_and_Portfolio_Operating_Constitution.md`, new `.agents/config/scoring.json`, and the skills named below.
Do: apply the constitution changes in section 3, after you choose the Conflict values. Add the momentum tests from section 1 with their thresholds to the constitution and to `scoring.json`. Replace the duplicated threshold tables in `shortlist_capital_allocator/SKILL.md` and `watchlist_shortlist_underwriting/SKILL.md` with references to `scoring.json`. Remove the internal conflict in the US allocator (two ATR ladders).
Pass: each threshold appears in exactly one place in the constitution and in `scoring.json`; both skills cite it by reference; no skill holds a number that differs from the config.

**W5. Momentum gate in code.**
File: `scripts/market_facts.py` (extend), new `scripts/momentum_gate.py`.
Do: compute Test A and Test B for every candidate and holding from the frozen snapshot. Output pass or fail with the measured values.
Pass: unit tests on known price series for each condition; the gate output is written into the ledger for every name.

**W6. Research contract.**
Files: new `.agents/skills/_shared/RESEARCH_CONTRACT.md`, new `scripts/fetch_cache.py`.
Do: define the JSON record each research agent returns (value, unit, period, source URL, retrieved-at, quoted passage, or null with reason). Build the fetch cache that stores each fetched page with its hash.
Pass: a sample company produces a complete record; the citation validator (W3) accepts it and rejects a record with a deliberately altered value.

**W7. Company report rewrite.**
Files: `.agents/skills/company_report/SKILL.md` and a new `.agents/skills/_shared/BOOK_STANDARD.md`, plus a new glossary file.
Do: rewrite the skill around the book structure in section 6.2, the estimate format in 6.3, the sector metric lists in 6.4, and the readability checks in 6.5. Remove the fixed "Wikipedia" framing. Keep the palette and voice rules.
Pass: one test company (suggest a holding, such as ADBE) is regenerated; it passes the W3 citation check and the 6.5 readability checks; you read it and confirm it is clear.

**W8. Displacement memo.**
Files: new `scripts/displacement.py` and `.agents/workflows/displacement.md`.
Do: produce the one-page memo in section 7 from the shared scorecard. Advisory only; no order generation.
Pass: runs for one holding against one candidate and reproduces the numbers in the memo from the stored inputs.

**W9. Reviewer and red team.**
Files: `.agents/skills/report_reviewer/SKILL.md`, new `.agents/skills/red_team/SKILL.md`, `.agents/config/reviewer.json`.
Do: add the red-team pass (Stage 9d). Update the reviewer rubric to check citations and readability.
Pass: the red team returns a reasoned bear case for every full report.

**W10. Decision log and outcome tracking.**
Files: new `data/decisions/` and `scripts/outcomes.py`.
Do: record each decision with thesis, expected return, invalidation and date. Compare results with the benchmark at 3, 6 and 12 months.
Pass: a test entry is logged and its 3-month row computes from stored prices.

Recommended order: W1, then W2 and W3 in parallel, then W4 once you choose the Conflict values, then W5 and W6 in parallel, then W7, then W8, W9, W10.

## 9. Open items for you

1. Choose the value for each row marked **Conflict** in section 3 (short-term target for US vs IN; IN Tier 3 asymmetry; the ATR ladder). I recommend the values shown.
2. Set the momentum thresholds in section 1 (relative strength rank, flattening, pivot distance). I can propose defaults from your past trades if you share them.
3. Confirm whether the Compare tab web app is still in use. If it is, its code should come into this repository before W8.
4. Confirm the sector list for the metric library in section 6.4. Start with the sectors that already appear in your holdings.
