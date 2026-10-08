# Bucket-Aware Portfolio Action Requirements

## Purpose

Create a practical, repeatable workflow for reviewing holdings and deciding
whether to add, hold, take profits, reduce, or exit. The workflow must use
different decision rules for each strategy book instead of applying one generic
score to the whole portfolio.

This is a decision-support checklist. It should recommend and document actions;
it should not place broker orders automatically.

## Common Support-Aware Entry Gate

`ADD` is valid only when the candidate or holding has a verified support/MA
confluence, a documented conditional entry zone (preferably within
approximately `0.5 × ATR(14)` of support), a stop below that structure, a
supported target, and acceptable reward-to-risk. An extended setup becomes
`WATCH` or `DEFER / WAIT_FOR_SUPPORT`; missing or broken support is not a buy
signal. This gate applies to Core, Tactical, Leveraged, and the underlying of
an Options thesis. It governs new or increased exposure and does not force an
exit from an otherwise valid existing Core thesis.

## Priority order

### P0 - Daily and regular action workflow

- [ ] Build a bucket-aware action queue showing the holdings that need attention
      today, this week, this month, or this quarter.
- [ ] Show one current action for every position:
      `ADD`, `HOLD`, `WATCH`, `TRIM`, `REDUCE`, or `EXIT`.
- [ ] Show the reason for the action, the evidence date, the next review date,
      and the confidence level.
- [ ] Show the last review, report age, thesis status, current weight, target
      weight, gain/loss, and whether a catalyst is approaching.
- [ ] Show entry posture, support anchor/type, distance from support in ATR,
      entry zone, stop, target, and reward-to-risk for every `ADD` or
      `WATCH` decision.
- [ ] Support explicit human overrides with a required reason and an audit
      record.
- [ ] Keep comparisons within the same strategy book by default.

### P0 - Common holding health check

- [ ] Compare the current position with its thesis, target, stop or
      invalidation level, and planned holding horizon.
- [ ] Flag material changes since the previous review:
      earnings, guidance, KPI trajectory, valuation, price trend, catalyst,
      or risk.
- [ ] Flag stale theses and missing decision fields instead of treating missing
      data as a positive signal.
- [ ] Show portfolio weight, bucket capacity, cash available, and overlapping
      exposure before recommending an action.
- [ ] Provide a concise "What changed?" summary for each flagged position.

## Bucket-specific requirements

### Core Alpha

Review cadence: weekly awareness and quarterly deep review.

- [ ] Track revenue growth, margins, free cash flow, balance sheet, moat,
      management, valuation, and company-specific KPIs.
- [ ] Separate normal price volatility from fundamental thesis deterioration.
- [ ] Trigger a review when growth decelerates, KPIs break, valuation becomes
      excessive, or a superior capital use is identified.
- [ ] Support profit booking through partial trims when valuation or position
      weight becomes excessive while the thesis remains intact.
- [ ] Support exit when the moat, growth engine, balance sheet, management case,
      or core thesis is materially broken.
- [ ] Avoid automatic exits based only on a short-term moving-average break.

### Tactical Momentum

Review cadence: several times per week and daily around major catalysts.

- [ ] Record the catalyst, expected catalyst window, entry zone, target, stop,
      and maximum time allowed for the thesis to work.
- [ ] Prefer a pullback, pivot, or breakout-retest entry near verified support;
      do not chase a vertical move.
- [ ] Track relative strength, 20/50-day trend, breakout quality, volume,
      momentum, and catalyst progress.
- [ ] Trigger a review when the catalyst is delayed, fails, or becomes less
      attractive.
- [ ] Recommend profit protection after a strong move when momentum weakens,
      the target is reached, or the position becomes oversized.
- [ ] Recommend exit when the setup fails, relative strength breaks, the stop
      is hit, or the catalyst window expires without progress.
- [ ] Prevent a failed tactical trade from silently becoming a Core holding.

### Leveraged Book

Review cadence: daily or near-daily.

- [ ] Track the underlying instrument, leverage multiplier, daily target
      exposure, market regime, trend, volatility, drawdown, and holding duration.
- [ ] Show both market value and leveraged or notional exposure.
- [ ] Flag volatility drag, sideways markets, sharp drawdowns, and overlapping
      exposures to the same underlying theme.
- [ ] Support profit booking using staged trims, trailing protection, and
      exposure reduction after a large move or trend deterioration.
- [ ] Recommend rapid reduction or exit after a trend breakdown, regime change,
      stop breach, or unacceptable drawdown.
- [ ] Never use the Core book's long-term hold logic for a leveraged product.

### Dual-Market Options Book (NSE F&O & US CBOE/OPRA)

Review cadence: daily or near-daily, with event-, Greeks-, and expiration-driven reviews.

- [ ] Track the underlying equity thesis separately from the option contract Greeks & volatility profile.
- [ ] Enforce the **4-Layer Quantitative Underwriting Radar** on all new entries:
      Underlying Stage 2 & Support $\le 0.5\times\text{ATR}(14)$, Volatility Squeeze ($IV_{30} \le RV_{30}\times 1.10$, IV Pct $<40\%$), Smart Money Footprint (NSE Long Build-up / CBOE GEX), and Contract Structuring (Bull Call Vertical Spreads Delta $0.50/0.25$ vs LEAPS Delta $0.65\text{–}0.75$).
- [ ] Record and audit: Ticket ID, Strike, Expiration Date, DTE, Delta ($\Delta$), IV Percentile, Theta Burn Rate (%/day), Premium Paid, Current Value, Underlying Support Anchor, and Invalidation Level.
- [ ] Enforce the non-discretionary **4-Action Position Health Audit**:
      - **`HOLD`**: Position healthy, Delta $0.40\text{–}0.70$, DTE $>20$ (Tactical) or $>60$ (LEAPS), underlying $>20/50\text{-DMA}$.
      - **`ROLL_UP_OUT`**: Option gain $\ge +80\%$ to $+150\%$ or Delta $\ge 0.75\text{–}0.85$; monetize deep ITM option and reset delta to $0.50$ in next cycle.
      - **`CONVERT_SPREAD`**: Underlying reaches Resistance 1 with gain $+30\%\text{ to }+60\%$; sell OTM Call ($\Delta 0.25$) to freeze delta and eliminate theta decay.
      - **`KILL`**: Immediate stop if option loses $\ge 40\text{–}50\%$, underlying breaks 50-DMA / swing low on daily close, or DTE $<20$ without breakout.
- [ ] Enforce Pre-Catalyst Volatility Rules: Close all event-driven options 24–48 hours BEFORE the scheduled announcement to avoid IV crush.
- [ ] Never treat an attractive long-term underlying thesis as justification to hold a decaying, low-delta option.

## Profit-booking and exit decision requirements

The action workflow is sufficient only if it answers these questions for every
position:

- [ ] What was the original thesis and what has changed?
- [ ] Is the position profitable, and is the gain large relative to its original
      risk?
- [ ] Has the position reached its target, become oversized, or exceeded its
      bucket capacity?
- [ ] Is the upside from today still attractive compared with the downside?
- [ ] Is there a better use of the capital?
- [ ] What specific event, price, KPI, trend, or contract condition requires a
      trim, reduction, or exit?
- [ ] Is the recommended action a full exit or a partial profit-protection
      action?
- [ ] What would invalidate the recommendation, and when should it be reviewed
      again?
- [ ] Was the human decision recorded, including the reason for accepting or
      overriding the recommendation?

The system must distinguish these outcomes:

- **Take profits:** Thesis remains valid, but valuation, weight, momentum, or
  realized gain justifies a partial trim.
- **Reduce risk:** Thesis may remain valid, but exposure, leverage, correlation,
  drawdown, or contract risk is too high.
- **Exit:** The thesis is broken, the catalyst failed or expired, the stop was
  breached, or the capital has a clearly superior use.
- **Hold:** The thesis remains valid and the current risk/reward still justifies
  the position.
- **Defer:** Evidence is incomplete or stale; no action should be taken until a
  specified review is completed.

## Suggested delivery sequence

1. [ ] Implement the common action model and action queue.
2. [ ] Implement Core and Tactical health checks, including profit-taking and
       invalidation rules.
3. [ ] Add Leveraged monitoring for notional exposure, regime, drawdown, and
       fast exit signals.
4. [ ] Add Options contract health and contract-specific actions.
5. [ ] Add human decision logging, overrides, reminders, and review history.
6. [ ] Add one-click comparison of an existing position against same-book
       candidates before reallocating capital.

## Acceptance criteria

- [ ] A daily review can be completed from one screen without opening every
      research report.
- [ ] Every action includes a bucket-specific reason and supporting evidence.
- [ ] Profit booking and exit recommendations are visibly different.
- [ ] The same position can receive different actions as its thesis, risk,
      weight, or bucket conditions change.
- [ ] Missing or stale data results in `DEFER` or `RESEARCH_REQUIRED`, not a
      confident buy, hold, or exit recommendation.
- [ ] Every human decision and override is recorded for later review.

## First production slice

The first production slice is implemented at `/portfolio-actions` as a separate
left-navigation page outside `/research`.

Implemented:

- Deterministic, visible precedence:
  `EXIT -> REDUCE -> TRIM -> ADD -> HOLD -> WATCH -> DEFER`.
- Core Alpha and Tactical Momentum actions use the latest usable structured
  candidate scorecard or research report, holding price/weight, target/stop
  data, and evidence freshness. Existing holdings do not require a shortlist
  candidate when a current structured report is available.
- Leveraged and Options holdings appear in the queue, but conservatively show
  `DEFER` until leverage/notional or live options risk metrics are available.
- Queue filters cover action, strategy book, urgency, and search. Expanded rows
  show the reason, metrics, evidence age, missing inputs, and links back to
  research reports or scorecards.
- Action computation is a pure frontend evaluator for this slice and is ready to
  move behind persisted action records when the backend model is introduced.

Current limitation: live event/catalyst feeds, Greeks, liquidity, leverage
notional, and drawdown/regime data are not fabricated; rows requiring them stay
in `DEFER / RESEARCH_REQUIRED`.
