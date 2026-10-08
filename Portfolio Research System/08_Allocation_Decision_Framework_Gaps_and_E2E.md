# Allocation Decision Framework: Gaps and UI Walkthrough

## Current status

The Compare tab is usable as an **advisory capital-allocation framework**. It compares candidates against holdings, evaluates displacement economics, correlation, concentration, compliance, stress impact, sizing, and funding sources, and produces a persisted decision memo.

It is not an automated trade-authorisation system. A `DO_NOT_SWAP` or `RESEARCH_REQUIRED` outcome is deliberately fail-closed. A user may still review the memo, accept the stated uncertainty, and place a trade manually through the broker.

## Support-Aware Allocation Gate

The Compare tab must treat entry location as a separate allocation gate. A
candidate can win the fundamental comparison and still be `RESEARCH_REQUIRED`
or `WAIT_FOR_SUPPORT` when its price is extended from verified support or a
retest zone. Any proposed new allocation must show the support anchor, entry
zone, distance in `ATR(14)`, stop below support, target, and reward-to-risk
from the same frozen snapshot. Existing holdings are not automatically exited
because they are extended; this gate controls new or increased exposure.

## Evidence gaps and consequences

| Gap | Why it matters | Current behavior |
| --- | --- | --- |
| Live option Greeks (delta, IV, and contract inputs) | Option exposure, stress loss, and sizing cannot be calculated precisely without them. | Advisory reports can use bounded estimates; option execution is blocked. |
| Beta-adjusted gross exposure and theme look-through | Capital weight alone understates correlated and leveraged exposure. | Theme-cap compliance is not certified; execution is blocked while this input is unavailable. |
| Complete tax-lot coverage | The funding leg's realized tax drag depends on actual lots, holding period, basis, and currency. | Reports may show economics excluding unavailable tax drag; execution is blocked. Lots are aggregated across all matching holdings in the selected account scope. |
| Confirmed portfolio policy | Book bands, single-name caps, and theme caps must reflect the user's approved policy rather than proposed defaults. | Proposed defaults are shown for analysis; execution is blocked until policy is confirmed. |
| Execution-time controls | Holdings, prices, cash, and compliance can change after analysis; an order must be revalidated immediately before submission. | No automatic order placement is provided. Manual broker execution remains possible. |
| Broker/order integration | The application currently generates analysis, not authenticated orders with idempotency, permissions, and audit controls. | Manual execution only. |
| Allocation-specific browser E2E coverage | Existing browser tests do not yet provide a dedicated, stable four-book allocation flow; provider/addon tests have unrelated failures. | Use the manual walkthrough below and treat the memo/evidence blockers as the acceptance checks. |

These are not reasons to discard the framework. They define the boundary between a high-quality decision aid and a system that could safely submit orders without human review.

## Reproducing the feature in the UI

1. Start the web application using the repository's normal web-dev command (`pnpm run dev:web`) with the web database configured.
2. Open the Research page and select the **Compare** tab:
   `http://localhost:1420/research?tab=compare`
3. Select the target account or account scope. Confirm that the holdings shown in the selector belong to that scope.
4. Select instruments manually. There are no default selections. For a replacement analysis, select the candidate and the incumbent funding holding; for a fresh-capital analysis, select the candidate without a funding holding. Keep the selection within the displayed maximum.
5. Choose **Generate Allocation Analysis**.
6. Choose the strategy book when the UI offers it: **Core**, **Tactical**, **Leveraged**, or **Options**. Use the book-specific candidate and incumbent scenarios, then confirm the bull/base/bear probabilities and timestamp.
7. Review the generated memo from top to bottom:
   - decision, action, size, funding leg, confidence, and as-of timestamp;
   - blockers versus limitations/estimates;
   - expected-return and hurdle economics, including bear-case sensitivity;
   - before/after book and theme exposure;
   - correlation, compliance, stress, tax-lot, and option-risk details;
   - reviewer pass, evidence hash, source versions, and review date.
8. Treat `DO_NOT_SWAP` as a recommendation to retain or defer, and `RESEARCH_REQUIRED` as an explicit request for missing evidence. Do not interpret an LLM narrative as permission to override a deterministic blocker.
9. If the memo supports a manual action after reviewing the limitations, place or adjust the order directly in the broker. Recheck price, cash, lots, sizing, and policy immediately before doing so.
10. Record the human decision and rationale in the application's decision-record flow when available so the outcome can be reviewed later.

## Acceptance criteria for future execution support

Before enabling any automated order path, all of the following must be true:

- live option-chain/Greeks data is sourced, timestamped, and stale-data gated;
- beta-adjusted gross exposure and ETF/index look-through are computed for the selected scope;
- all funding lots are available or explicitly selected;
- the user has confirmed the active compliance policy;
- broker authentication, permissions, idempotency, order-preview, and execution-time revalidation are implemented;
- allocation-specific E2E tests cover Core, Tactical, Leveraged, and Options paths;
- a fresh Sonnet and Terra review certifies both the implementation and generated evidence.
