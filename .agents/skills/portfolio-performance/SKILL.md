---
name: portfolio-performance
description: Calculate and visualize broker portfolio profit/loss for overall, one-year, and six-month periods; use when the user asks how their accounts performed or wants an S&P 500 reference.
---

# Portfolio performance

Use this skill to explain whether each brokerage profile gained or lost money, show realized and unrealized components, and compare the same periods with an S&P 500 total-return proxy.

## Workflow

1. Identify each account separately and its base currency. In this portfolio, the canonical logs are Zerodha (INR), Robinhood (USD), and Schwab (USD). Include only accounts the user asks about.
2. Use the newest reconciled transaction logs and the latest broker holdings/cash snapshots available. A current holdings table must include its as-of date, price source, and currency. If a same-day mark is missing, use the latest available close and say which date it represents.
3. Calculate account P&L in currency, never by combining INR and USD. Follow the formulas and coverage rules in [performance-methodology.md](references/performance-methodology.md).
4. Run `scripts/compute_performance.py` with `.venv/bin/python` to replay transactions, calculate the period components, and fetch SPY adjusted-price returns. Provide a JSON snapshot describing current per-symbol values; schema and invocation are in [performance-methodology.md](references/performance-methodology.md).
5. Build the requested canvas as an interactive, accessible visualization. Show each account separately, the selected period, the P&L components, current account value, and the S&P 500 return for that same period. Keep benchmark percentage returns visually distinct from currency P&L.
6. State material limits beside the affected profile: incomplete history, missing costs, fees embedded in cash adjustments, stale prices, unreconciled cash, or options whose marks/history are unavailable. Do not present an unflow-adjusted comparison as alpha or as a fully comparable investment return.

## Guardrails

- Do not invent missing transaction amounts, prices, or external cash flows. Use the user's logs as the transaction record and reconcile quantities with the broker snapshot.
- Use live brokerage data only when the user authorized browser access and an already authenticated session is available. Never log in or handle credentials.
- Treat open options as a separate component unless both current and period-start marks reconcile. If they do not, show their available P&L separately and exclude them from the stock-period totals.
- The S&P 500 line is a benchmark reference unless a flow-adjusted portfolio return can be calculated from complete external cash flows and valuations. Use SPY adjusted close as a dividend-inclusive proxy; label it as a proxy.
- Preserve the user's requested windows. “Overall” means the period covered by complete, usable transaction records, not necessarily account lifetime.
- Do not commit, publish, or change the underlying transaction logs as part of a performance analysis unless the user separately asks for those actions.
