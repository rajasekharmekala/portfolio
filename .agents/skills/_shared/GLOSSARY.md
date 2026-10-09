# Glossary: first-use definitions for company reports

The machine-readable list is `.agents/config/glossary.json`; the checker
(`scripts/readability_check.py`) enforces it. Every term that appears in a
report must, at its **first occurrence**, be wrapped in `<dfn>`, and the same
paragraph must carry the plain-English definition.

Write the first use like this:

> The **<dfn>relative strength index (RSI)</dfn>** — a meter from 0 to 100 of
> how fast the price has been rising — is at 61, which is strong but not
> overheated.

Acronyms: the paragraph must contain the spelled-out expansion (checked
verbatim, case-insensitive). Phrase terms: the paragraph must contain a
defining sentence — the word followed by "is", "are", "means", "stands for",
or a dash definition.

## Acronyms (spelled out on first use)

| term | expansion | one-line plain meaning |
|---|---|---|
| RSI | relative strength index | how fast the price has been moving, on a 0–100 meter |
| ATR | average true range | the average daily price swing, in currency units |
| EBITDA | earnings before interest, taxes, depreciation and amortization | profit before the accounting and finance adjustments |
| ROCE | return on capital employed | profit earned on each rupee/dollar of capital the business uses |
| ROIC | return on invested capital | profit earned on each dollar invested in the business |
| EPS | earnings per share | the company's profit divided across all shares |
| FCF | free cash flow | cash left after running the business and buying assets |
| SBC | stock-based compensation | the cost of paying employees in shares |
| NIM | net interest margin | a bank's interest income after paying depositors |
| GNPA | gross non-performing assets | loans a bank expects it will not get back, before provisions |
| NNPA | net non-performing assets | the same, after the safety provisions |
| CASA | current and savings account | cheap deposits: money a bank barely pays interest on |
| ARR | annual recurring revenue | the yearly value of subscriptions that renew |
| NRR | net revenue retention | the share of last year's customer revenue still with you this year |
| RPO | remaining performance obligations | signed contracts not yet recognised as revenue |
| TAM | total addressable market | the full market the company could ever sell into |
| PUE | power usage effectiveness | how much of a data centre's power goes to computing |
| PPA | power purchase agreement | a contract to buy electricity at a fixed price |
| EIR | inspection report | a USFDA inspection of a manufacturing plant |
| PEG | price-to-earnings-to-growth | the P/E adjusted for how fast earnings grow |
| SSSG | same-store sales growth | sales growth at stores open for a full year |
| BCF | billion cubic feet | a unit of natural gas volume |
| BESS | battery energy storage system | a large battery farm that stores electricity |
| CoWoS | chip-on-wafer-on-substrate | the advanced packaging that joins logic chips to memory |
| GMV | gross merchandise value | the total value of goods sold through a platform |

## Phrase terms (defined sentence on first use)

- **20/50/200-day moving average** — the average closing price over the last
  20/50/200 trading days; a slowly moving line the price tends to bounce off.
- **Stage 2 / Stage 4** — the Weinstein stage scale: Stage 2 is the confirmed
  uptrend, Stage 4 the confirmed downtrend.
- **base** — a sideways consolidation the price builds before a move; the
  platform a breakout starts from.
- **pivot** — the top of a base; the price level a breakout must clear.
- **breakout** — the move that takes the price above a base or pivot on volume.
- **retest** — the pullback after a breakout that tests the level from above.
- **stop loss** — the price at which the thesis is wrong and the position is cut.
- **limit order** — an order that only fills at your price or better; it does
  not chase.
- **entry zone** — the band of prices where buying is planned.
- **asymmetry / reward-to-risk** — the ratio of potential gain to potential
  loss from the entry: (target − price) / (price − stop).
- **gross / operating / net margin** — revenue minus cost of goods / minus all
  running costs / minus everything, as a share of revenue.
- **debt-to-equity** — total debt divided by shareholders' money.
- **net debt** — interest-bearing debt minus the cash held.
- **price-to-earnings** — the price paid for each rupee/dollar of earnings.
- **free cash flow** — see FCF.
- **cash flow from operations** — the cash the business itself generates before
  financing.
- **guidance** — the company's own published forecast for the coming period.
- **measured move** — the height of a base projected as a target above it.
- **book-to-bill** — new orders divided by revenue; above 1 means the order
  book is growing.
- **take rate** — the share of transaction value a platform keeps.
- **dilution** — the rise in share count from issuing new shares.
- **capital expenditure** — spending on plants, equipment and infrastructure.
- **buyback** — the company buying its own shares back, shrinking the count.
- **working capital** — current assets minus current liabilities; the cash tied
  up in day-to-day operations.
- **consensus estimate** — the average of analysts' forecasts for a number.

If a term you need is missing from the list, add it to
`.agents/config/glossary.json` and to this table in the same run.
