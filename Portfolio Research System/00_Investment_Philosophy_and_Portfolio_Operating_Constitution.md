Investment Philosophy & Portfolio Operating Constitution

Version 1.0  |  August 2026

| Aggressive growth. Active alpha. Deliberate risk. Disciplined execution. |
| --- |


Purpose: to preserve consistency in portfolio decisions through changing markets, strong emotions, and shifting narratives.

# 1. Purpose

This document defines the principles under which I will manage my investment portfolio. Its purpose is to prevent short-term market noise, emotion, recent performance, or attractive new narratives from causing me to drift away from my intended strategy.

My portfolio is designed to pursue aggressive capital growth and significant outperformance of the S&P 500, while accepting substantially more volatility than a conventional diversified portfolio.

I am an active investor. I am willing to spend significant time researching, monitoring, and managing positions. My portfolio therefore does not need to be optimized for passivity; it should be optimized for risk-adjusted alpha, capital efficiency, and disciplined execution.

# 2. Investment Objective

| Primary objective: generate approximately 20%+ annualized returns over time and materially outperform the S&P 500. |
| --- |


This objective will not be pursued by simply taking indiscriminate risk. The strategy is to combine concentrated high-conviction growth companies, short-term momentum and catalyst opportunities, leveraged instruments, and options with asymmetric payoff potential.

A temporary portfolio drawdown of approximately 20-30% is acceptable when the underlying investment theses remain intact. Drawdowns beyond this level should trigger a portfolio-level risk review rather than automatic liquidation.

# 3. Investor Identity

Investor style: Aggressive Growth / Active Alpha Investor.

Fundamental analysis

Valuation

Technical analysis

Momentum

Catalysts

Macroeconomic conditions

Market positioning and sentiment

Options activity where relevant

Relative capital allocation opportunities

I am neither a passive buy-and-hold investor nor a pure short-term trader. I want to own quality businesses when the long-term opportunity is attractive, but capital should remain productive.

| Core does not mean passive. Even a Core holding should have a credible path toward meaningful thesis progress within roughly 6-12 months. |
| --- |


# 4. Portfolio Architecture

The portfolio is divided into four distinct investment engines. These categories remain separate because they have different purposes, time horizons, analytical frameworks, and risk-management rules.

| Portfolio Engine | Target Allocation | Primary Role |
| --- | --- | --- |
| Core Alpha | 35-40% (US); 30-40% (IN) | 3-5 year high-conviction wealth compounding |
| Short-Term / Momentum / Tactical | 50-65% (US and IN) | 3-12 month catalyst and momentum opportunities |
| Leveraged Holdings | 20-25%, hard max 30% | Amplified exposure to strong trends/themes |
| Options / Asymmetric Bets (LEAPS) | 5-10%, hard max 10% (LEAPS only) | Defined-risk, high-upside time-bound hypotheses |

The machine-readable twin of every number in this architecture lives in `.agents/config/scoring.json`; that file is the single source of truth and the skills reference it.


These are target ranges rather than rigid requirements. Capital may temporarily move between buckets when unusually attractive opportunities emerge.

# 5. Core Alpha Portfolio

## Purpose

Core Alpha positions are my highest-conviction businesses. Expected holding period: approximately 3-5 years. However, Core does not mean permanent or passive.

Strong long-term growth potential

Durable competitive advantages

Attractive or improving fundamentals

Credible earnings growth

A favorable valuation/risk-reward relationship (Core requires at least 2.0:1 target-vs-stop asymmetry at CMP or at the planned limit-order Entry Zone, per `.agents/config/scoring.json`)

Identifiable catalysts or business developments capable of producing meaningful progress within roughly 6-12 months

The 3-5 year horizon carries a 6-12 month thesis checkpoint: if a Core name leaves momentum for a sustained period, the review flags it and the thesis must be re-confirmed before it is held

## Concentration & Risk-Unit Sizing

The Core portfolio holds 5-10 companies; the total portfolio holds 6-12 names. Initial position sizing is governed by **Risk-Unit Sizing (Portfolio Heat)** per `.agents/config/scoring.json`: new positions risk 35–100 bps of portfolio net worth between entry price and invalidation stop (`weight_pct = min(tier_max_pct, risk_budget_bps / stop_distance_pct)`), with an initial cost-basis cap of 10% and a standard single-name cap of 15%. Total portfolio heat across all open stops is capped at 12% of net worth.

**Letting Winners Run:** Never mechanically trim a Stage 2 winner with intact fundamentals and stable/rising earnings revisions solely because RSI exceeds 70 or its weight grows past 15%. Appreciated winners may run up to the `runaway_winner_cap_pct` (22% of net worth) in `.agents/config/scoring.json` while trailing the stop to the rising 21-day EMA or 50-day SMA.

## Core Decision Standard

1.  Why this business can materially outperform.

2.  What the market may currently be misunderstanding.

3.  Which company-specific KPIs will prove or disprove the thesis.

4.  What should happen during the next 6-12 months.

5.  What would invalidate the thesis.

6.  Whether the expected upside still justifies tying up the capital.

# 6. Short-Term / Momentum / Tactical Portfolio

This bucket seeks opportunities expected to materialize primarily within approximately 3-12 months, with ~6 months as the normal working horizon. Typical number of positions: approximately 5-10.

Turnarounds

Earnings inflections

Sector rotations

Cyclical recoveries

Valuation reratings

Macro-driven opportunities

Momentum trades

Event-driven setups

## Required Thesis

Catalyst

Expected timeline

Technical condition

Fundamental support

Valuation/risk-reward

Failure condition

| A failed short-term trade must not become a long-term investment simply because it is losing money. |
| --- |


# 7. Leveraged Portfolio

Leveraged products are an important return engine within my strategy. They are not substitutes for ordinary stock holdings and should not be analyzed using the same framework. Typical number of positions: approximately 10-15.

Underlying asset

Trend

Momentum

Technical structure

Market breadth

Macro regime

Liquidity

Volatility

Correlation with other portfolio exposures

Drawdown characteristics

Profit protection

Monitoring: leveraged positions should normally be reviewed almost daily. Because these products magnify both returns and losses, deterioration in trend should be taken more seriously than in Core holdings.

# 8. Options Portfolio

Options are an essential component of the strategy and should be treated as time-bound asymmetric investment hypotheses. Typical number of option theses: approximately 10-15.

Underlying company thesis

Strike

Expiration

Premium at risk

Delta / effective exposure

Implied volatility

Time decay

Required underlying move

Catalyst timing

Technical trajectory

Expected exit conditions

Multiple strikes or contracts on the same underlying should generally be treated as one underlying investment thesis when assessing portfolio concentration.

| A correct long-term company thesis does not necessarily mean an option position is correct. Timing is part of the options thesis. |
| --- |


# 9. Decision Hierarchy & Archetype Underwriting

Almost any non-fraudulent, solvent business is ownable if the price is cheap enough (high valuation asymmetry / low Reverse-DCF implied growth) and the fundamental and technical trajectory is inflecting in the right direction. Every company on the watchlist or in the portfolio is evaluated across all three underwriting layers (`Layer 1: Levels vs. Trajectory & Red Lines`, `Layer 2: Company-Specific KPIs & Management Walk-the-Talk`, `Layer 3: Support-Aware Entry & Risk-Unit Sizing`) — Layers 2 and 3 are never skipped.

Candidates qualify under one of three archetypes defined in `.agents/config/scoring.json` (`underwriting_philosophy`):

1. **Compounder (`CORE_ALPHA`):** High static return on capital (`ROIC >= 12%` US, `ROCE >= 15%` IN; or adjusted ex-goodwill/intangibles amortization), strong cash conversion (`FCF margin >= 12%` US; `3Y CFO/PAT >= 0.70` IN, or `>= 0.50` for high-growth Capital Goods/Defense/Infra/Manufacturing with `D/E < 0.50` and `ROCE >= 18%`), disciplined dilution (`SBC < 8%` US, or `< 15%` when Owner FCF margin `>= 10%` and share dilution `<= 3%`), and reasonable valuation (`asymmetry >= 2.0:1`).
2. **Turnaround / Value Inflection (`TURNAROUND_VALUE_INFLECTION`):** A company that misses a static compounder floor (e.g., depressed trailing margin/ROIC or elevated SBC) still qualifies when: (a) all solvency/governance `hard_red_lines` pass, (b) at least two rate-of-change trajectory indicators are improving (QoQ/YoY margins, cash conversion/working capital days, consensus EPS revisions, or debt reduction), (c) Reverse-DCF implied 10-year growth at today's price is below realistic forward growth (or valuation is at a `>20%` discount to 3Y median multiple), and (d) reward-to-risk asymmetry clears `2.5:1` (at CMP or at the planned limit-order Entry Zone).
3. **Tactical Breakout (`TACTICAL_MOMENTUM`):** Confirmed Stage 2 trend leader or Stage 1 base breakout with earnings/revenue acceleration and `asymmetry >= 2.5:1`.

**Layer 2 KPI Qualification (`PASS_WITH_WATCH`):** Company-specific KPIs (3–5 metrics) are scored `PASS` (`1.0`), `WATCH` (`0.5`), or `FAIL` (`0.0`). A candidate qualifies when its weighted score is `>= 3.0/5.0` (or `>= 2.5/4.0`) and at most 1 KPI is `FAIL` (e.g., `3 PASS + 2 WATCH + 0 FAIL = 4.0/5.0` qualifies as `PASS_WITH_WATCH`).

**Technical Routing (Selection vs. Entry Timing):** Only a `Stage 4` breakdown (`Close < falling SMA50 < falling SMA200` with `Test C` failing) is a Layer 1 technical disqualifier (`REJECTED`). If a candidate passes `hard_red_lines`, qualifies under an archetype + Layer 2 KPIs, and clears the asymmetry floor at CMP or at its support Entry Zone, but is currently in a Stage 3 pullback / Stage 1 base above a rising/flat 200-DMA or extended in Stage 2 (`> 1.6 ATR` above support), it is routed to `WAIT_FOR_SUPPORT` (or limit-order `ACCUMULATE_ON_DIP`) rather than rejected.

Technical momentum and inflection are measured from the frozen price snapshot (`scripts/momentum_gate.py`) across three tests in `.agents/config/scoring.json`:

- **Test A — in momentum now (`STAGE2_LEADER`):** Confirmed Stage 2 uptrend (`price > SMA50 > SMA200`, rising 50-day, non-falling 200-day), positive 63-day relative strength vs. benchmark, and price within `1.6 ATR` of nearest verified support.
- **Test B — entering momentum (`BASE_PIVOT`):** Tight 63-day base with flattening 50-day average (`<= 0.8%` decline over 21d), rising 28-day relative strength, within `1.5 ATR` of base low, volume dry-up in the base (`<= 0.92x`), and volume expansion (`>= 0.95x`) on the turn.
- **Test C — turnaround inflection (`TURNAROUND_INFLECTION`):** Price holding a higher-low floor above its 63-day low (`swing_low_20d >= base_low_63d` within `2.0%` tolerance), reclaiming its 20-day moving average with positive 28-day relative strength or 2-week gain, within `2.0 ATR` of support, and RSI stabilizing (`>= 32`).

# 10. Capital Efficiency

| Every position should periodically answer: Is this still one of the best uses of my capital? |
| --- |


The catalyst is too distant

Earnings growth is unlikely to accelerate

The stock lacks momentum

Valuation offers insufficient upside

Superior opportunities exist elsewhere

Long-term investing does not mean tolerating indefinite dead money.

# 11. Buying and Adding to Positions

I am comfortable holding through volatility when the investment thesis remains intact. I am also willing to add when conviction remains high and price returns to verified support with a defined invalidation level.

| I will not average down solely because a stock has become cheaper. |
| --- |

### Support-aware entry and capital-preservation standard

Stock selection and entry timing are separate decisions. A company can be one of
the best research candidates and still be a **no-buy today** if its current
price is extended from a verified support area. For every new position or
additional capital, prefer a conditional entry at a documented confluence of
prior breakout/base support, a rising 20/50/200-day moving average appropriate
to the strategy bucket, and/or a recent swing low. The entry zone, support
anchor, distance from support, and data-as-of timestamp must be recorded.

Operationally, entry sizing follows the single support-distance ladder in
`.agents/config/scoring.json`, measured from the selected verified support
anchor: within `0.6 × ATR(14)` (`FULL_SIZE`) → full risk-adjusted tier size;
`0.6–1.2 × ATR(14)` (`STANDARD`) → standard risk-adjusted size;
`1.2–1.6 × ATR(14)` (`LIMIT_ORDER_REDUCE`) → starter / limit order only, at
reduced size; beyond `1.6 × ATR(14)` (`NO_BUY`) → no chase at market (place a
limit order in the entry zone or wait for a pullback/consolidation). Do not
chase a sharp extension, convert a breakout into an automatic market buy, or
catch a falling knife. If price is extended, wait for a controlled pullback, a
valid breakout retest, or a new base (`WAIT_FOR_SUPPORT`); if structural
Stage 4 support has failed, mark the setup `REJECTED`.

Asymmetry floor: a Core position must offer at least 2.0:1 and a Tactical or
Turnaround position at least 2.5:1 target-vs-stop asymmetry (at CMP for
immediate entries, or at `entry_zone_high` for limit-order / `WAIT_FOR_SUPPORT`
setups; formula: `(target_base − entry_ref) / (entry_ref − stop_loss)`).
Stops: Core below the nearest structural invalidation support — `min(swing_low_20d, SMA50) − 1.0 × ATR(14)` in Stage 2 uptrends (or `base_low_63d − 1.0 × ATR(14)` in Stage 1 / turnaround bases; do not mechanically use a distant 200-day MA in a multi-month advance); Tactical below `min(swing_low_20d, SMA20 or SMA50) − 0.5 × ATR(14)`.

The stop must sit below the support structure with the applicable volatility
buffer, and the target must be independently supported by resistance,
valuation, a measured move, or a dated catalyst. No new or increased position
is eligible without verified price, support, stop, target, liquidity, and
positive reward-to-risk. This timing rule protects capital; it does not
override a valid long-term thesis for an existing Core holding.

Has the thesis improved, remained intact, or deteriorated?

Is the valuation more attractive?

Is the expected catalyst still valid?

Has the technical setup stabilized?

Am I increasing exposure to an already concentrated portfolio theme?

Additional capital requires renewed conviction, not merely a lower price.

# 12. Profit Taking and Sell Discipline

My sell framework should remain flexible rather than mechanically tied to fixed percentage gains or losses. I want to allow exceptional winners to compound while also booking substantial profits when evidence suggests momentum or trajectory is changing.

Large gains combined with deteriorating technical momentum

Break of an established trend

Failure after a major breakout

Fundamental growth deceleration

Excessive valuation

Thesis completion

Catalyst realization followed by weakening price action

Better alternative opportunities

Position becoming excessively large

Possible actions: Add -> Hold -> Hold/Watch -> Trim -> Reduce -> Exit. The appropriate decision depends on the bucket and circumstances.

# 13. Thesis Invalidation

Every significant investment should eventually define specific conditions that would prove the thesis wrong. These should primarily be based on business performance, industry structure, competitive position, expected catalysts, technical deterioration, and macro conditions when relevant.

A declining stock price alone does not invalidate a Core thesis. Repeated evidence contradicting the original assumptions does. I should avoid defending an investment simply because I already own it.

# 14. Theme Concentration

I am intentionally willing to concentrate capital in a small number of themes when the opportunity is compelling. Diversification is not an objective by itself, but I must understand my actual economic exposure.

Artificial intelligence

Cloud / software

Semiconductors

Cybersecurity

Fintech

China recovery

Consumer growth

Housing / rate-sensitive recovery

Other emerging high-conviction themes

| Multiple securities may represent the same underlying thesis. Concentration should be intentional, not accidental. |
| --- |


The portfolio should track: Position -> Bucket -> Sector -> Theme -> Underlying macro exposure.

# 15. Cash

Cash allocation: 5-10% of total portfolio, scaled to the VIX ladder in `.agents/config/scoring.json` (VIX < 15 → 5%; VIX 15-22 → 7.5%; VIX > 22 → 10%+). Cash rises toward the top of the band when attractive opportunities are scarce, market risk/reward becomes unfavorable, significant profits have recently been harvested, or I am intentionally waiting for better entries.

Cash is tactical ammunition, not a permanent investment allocation.

# 16. Monitoring Frequency

| Bucket | Monitoring Standard |
| --- | --- |
| Core Alpha | Regular price/news monitoring; monthly thesis awareness; quarterly deep fundamental review; immediate review after major developments. |
| Short-Term / Momentum | Several times per week; more frequently during major technical or catalyst periods. |
| Leveraged Holdings | Almost daily. |
| Options | Daily or near-daily. |


# 17. Quarterly Company Reviews

Every Core company should receive a structured quarterly review. The review should preserve historical thinking rather than overwrite it.

Thesis Status: Stronger / Intact / Weakening / Broken

Company-Specific KPIs: only metrics that materially influence the investment thesis

What Changed: focus on changes since the previous review

Valuation: Bull / Base / Bear framework

Catalysts: expected developments over the next 6-12 months

Risks / Invalidation: evidence that would materially alter the thesis

Technical Condition: momentum and trajectory

Decision: Add / Hold / Watch / Trim / Reduce / Exit

# 18. Research Database Philosophy

The purpose of this project is to become my investment decision database, not simply a collection of research. The system should preserve:

Why I bought

What I expected

What KPIs mattered

What catalysts I expected

What could prove me wrong

What actually happened

What decision I made

Whether that decision was correct

Information should remain organized into a small number of portfolio-level databases rather than dozens of disconnected files.

1.  Investment Philosophy / Portfolio Constitution

2.  Master Portfolio Dashboard

3.  Core Holdings Database

4.  Short-Term / Momentum Database

5.  Leveraged Holdings Database

6.  Options Book

7.  Quarterly Portfolio Reviews

8.  Research & KPI Library

Individual companies should generally exist as clearly structured sections within these databases rather than separate files.

# 19. Decision Dashboard Philosophy

Detailed research should support decisions, not obscure them. Every portfolio review should begin with a concise decision layer showing:

Position

Bucket

Theme

Conviction

Thesis status

Technical status

Catalyst

Current action

Last review

Next required review

Detailed research should remain available underneath the dashboard for deeper examination.

# 20. Watchlist and Opportunity Ranking

The research system should contain both a broad watchlist and a ranked opportunity list. Existing holdings should continually compete with new opportunities.

| Recurring question: If I had fresh capital today, where would I put it? |
| --- |


Ownership should not create entitlement to continued capital.

# 21. Behavioral Rules

## I will not

Panic-sell high-quality Core holdings solely because they decline.

Blindly average down because something is cheaper.

Convert failed trades into long-term investments without a new thesis.

Hold dead money indefinitely because a company is "good."

Confuse multiple securities representing the same thesis with diversification.

Ignore technical deterioration in leveraged or options positions.

Refuse to take profits when a large gain and deteriorating trajectory occur together.

Become attached to a stock because of previous research or past gains.

Chase a new narrative without understanding the risk/reward.

Chase an extended price when a better support-based entry is reasonably
available.

## I will

Concentrate when conviction and opportunity justify it.

Respect momentum and market signals.

Research deeply enough to understand what I own.

Define the metrics that would prove me right or wrong.

Protect large gains when conditions materially deteriorate.

Reallocate capital toward superior opportunities.

Accept volatility when expected reward remains attractive.

Distinguish normal volatility from genuine thesis impairment.

Prefer conditional, support-aware entries and retain cash when the setup is
extended or the downside cannot be defined.

Maintain a written historical record of major portfolio decisions.

# 22. Five Questions Before Any Major Portfolio Decision

1.  What has actually changed?

2.  Is the underlying thesis stronger or weaker?

3.  What does the technical trajectory say?

4.  What is the upside versus realistic downside from today's price?

5.  Is the price at or near verified support, or should I wait for a better
    entry?

6.  Is there a materially better use for this capital?

If these questions cannot be answered clearly, more research is required before materially changing the position.

# 23. Governing Principle

| Take substantial risk when the expected payoff is asymmetric. Reduce risk when the evidence no longer supports the expected payoff. |
| --- |


The objective is not to avoid drawdowns. The objective is to ensure that the risks I take are intentional, researched, monitored, and worth taking.

This document should evolve as my investing experience develops, but major changes should be deliberate and documented rather than made impulsively in response to market conditions.
