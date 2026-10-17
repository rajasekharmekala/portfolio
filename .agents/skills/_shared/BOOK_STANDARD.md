# Book Standard: how every company report is written and checked

A company report is a short book, not a dossier. It is read by a capable adult
with no finance training. Plain English comes first, technical terms come second,
and every technical term is defined the first time it appears. Target reading
level: roughly a good popular-science book. Short sentences. One idea per
paragraph.

This standard is binding. The code checks in section 5 are run by
`scripts/readability_check.py`; the citation checks are run by
`scripts/citation_check.py`. A report that fails either gate is not finished,
whatever the reviewer thinks.

## 1. Structure: the chapters

Each report reads as chapters, and each chapter answers one question the reader
would ask. The chapters are fixed in order; the content inside them is written
for that company's business.

| order | id | title | the question it answers |
|---|---|---|---|
| 0 | `primer` | Before you read | what is this company, what does this report conclude, and what would make the conclusion wrong? |
| 1 | `ch-1` | What the company does | who pays it, for what, and how does it make money? |
| 2 | `ch-2` | Why the business is strong or weak | what is the competitive position, and what is the evidence? |
| 2B | `ch-2b` | Company specifics, operating KPIs, and management walk-the-talk | which 3–5 company-specific KPIs run this business (Layer 2), and did management deliver on what it promised 1–2 years ago? |
| 3 | `ch-3` | The numbers, in plain words | what do revenue, profit, cash and debt do over five years, and how do static levels compare with trajectory (Layer 1)? |
| 4 | `ch-4` | What the price is doing | does the stock pass the momentum/turnaround test, and what would confirm or reject the idea? |
| 5 | `ch-5` | What could happen next | what growth rate is today's price already assuming (Reverse DCF), how are analyst estimates moving, what is our variant view, and what are the bull, base and bear cases? |
| 6 | `ch-6` | Why these estimates might be wrong | which assumption is weakest, what is the red-team bear case, and when will we know? |
| 7 | `ch-7` | What we would do, and when | what is the decision, the risk-unit position size, the let-winners-run rule, and the trigger that changes it? |
| 8 | `notes` | Notes and sources | where does every number come from? |

Rules per chapter:

- **Before you read.** Three to five sentences only: what the company is, what
  the report concludes, and what would make the conclusion wrong.
- **Chapter 1** is explained as if to a friend, and ends with a short glossary
  of the terms the report uses (the terms from `GLOSSARY.md` that appear).
- **Chapter 2** states the competitive position with reasons and evidence. Each
  claim cites a source.
- **Chapter 3** shows revenue, profit, cash and debt over five years. Every
  table is followed by a paragraph explaining what the table means and what it
  does not show.
- **Chapter 4** states the momentum test result in plain words, for example
  "the price is above its 50-day average, which has been rising for eight
  weeks". Each technical term is defined. The consequence is stated: what the
  chart would need to do to confirm or reject the idea. The test result is the
  frozen-snapshot output of `scripts/momentum_gate.py`, not a re-derivation.
- **Chapter 5** gives bull, base and bear. For each: the story in plain words,
  the driver, the number, the probability, and the reason for that probability.
  Then the expected outcome in dollars or rupees.
- **Chapter 6** takes each estimate and states its weakest assumption, what
  evidence would show it is wrong, and when that evidence will be known (for
  example, the next earnings date).
- **Chapter 7** gives the decision (buy, wait, hold, trim, exit, or displace),
  the price or event that would change it, the entry zone, stop and targets,
  each with the reason.
- **Notes and sources** are numbered, with the page or section for each filing.

## 2. Every estimate shows its working

Each estimate in the report includes five things, in this order:

1. The number, in plain words.
2. How it was calculated, in one or two sentences.
3. The inputs, each cited.
4. The range: what the number would be in the bull and bear case, and why.
5. The consequence: what changes for the reader if the number is off.

Pattern (not real data): "We estimate next year's profit per share at $X. We
got this by taking this year's profit (cited), adding the growth the company
guided to (cited), and assuming the margin stays where it was last year
(cited). If margins fall by two points, profit would be about $Y, and the case
for buying would weaken."

## 3. Company-specific layout

The chapter structure stays; the content follows the business. A bank is judged
on loan quality and net interest margin. A chip company on order backlog and
gross margin. A software company on recurring revenue and free cash flow. A
leveraged ETF is not analysed as a company at all: its report covers the
index, the trend, and the decay risk.

Key metrics for each major sector (the writer picks the three to five that
matter for this company and says why):

- **Cloud / Software / AI:** ARR growth, net revenue retention, RPO backlog,
  free cash flow margin, Rule of 40 (growth plus FCF margin), SBC as % of
  revenue.
- **Semiconductors / Hardware:** gross margin, book-to-bill, fab utilisation,
  data-centre revenue share, inventory weeks.
- **Data-centre / Power Infrastructure:** power under contract, capex backlog,
  PUE, order book.
- **Consumer Tech / Platforms:** take rate, GMV growth, active users, monetisation.
- **Healthcare / Biotech / MedTech:** pipeline phases, regulatory milestones,
  royalty or recurring revenue share.
- **Banks / NBFCs:** net interest margin, asset quality (GNPA/NNPA in India,
  charge-offs in the US), capital ratio, CASA ratio.
- **Industrials / Aerospace / Defence:** firm backlog to sales, book-to-bill,
  operating margin, order wins.
- **Consumer / Retail:** same-store sales, unit economics, inventory turns.
- **Pharma / CDMO:** gross margin, pipeline, USFDA compliance, patent cliffs.
- **Capital Goods / EPC / Energy:** order book to billings, working capital days,
  capacity utilisation.

## 4. Voice and colour

- Voice: `REPORT_VOICE.md` (binding). No banned filler phrases.
- Colour: `REPORT_PALETTE.md` (binding). Verdicts are `<span class="verdict verdict-keep">KEEP</span>`
  style, never emoji.

## 5. Readability checks (enforced by `scripts/readability_check.py`)

The verifier runs these in code and flags failures:

1. **Reading level.** Flesch–Kincaid grade of each chapter at or below the
   agreed threshold (default 13, `--max-grade`). Failing chapter is listed.
2. **Glossary terms defined on first use.** Every term in
   `.agents/config/glossary.json` that appears in the report must, at its first
   occurrence, be wrapped in `<dfn>`, and the same paragraph must contain the
   plain-English expansion (for acronyms) or a defining sentence (for phrase
   terms).
3. **No bare tables.** Every `<table>` is followed by at least one explanatory
   paragraph (80+ characters) before the next table or heading.
4. **Estimates show their working.** Every `<section class="estimate">`
   contains the five labelled parts: `The number`, `How it was calculated`,
   `The inputs`, `The range`, `If the number is off`.
5. **Decisions name their trigger.** Chapter 7 contains at least one
   `<p class="trigger">`, and each decision paragraph names the price or event
   that would change the decision.
6. **Banned filler absent**, per `REPORT_VOICE.md`; the primer is three to five
   sentences; Notes and sources exist and are numbered.

HTML conventions the checker relies on:

- chapters are `<section class="chapter" id="ch-N">` with the exact table titles above in `<h2>`;
- the primer is `<section class="primer" id="primer">`;
- notes are `<section id="notes">` with an `<ol class="sources">`;
- estimates are `<section class="estimate">` with the five `<h4>` labels;
- glossary terms at first use: `<dfn>relative strength index (RSI)</dfn>`;
- every table sits in `<div class="table-wrap">`.

Readability is checked by code and then by the tone reviewer. A report does
not pass on the reviewer's opinion alone.
