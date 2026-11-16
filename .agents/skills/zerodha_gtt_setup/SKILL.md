---
name: zerodha-gtt-setup
description: >-
  Reads a portfolio audit PDF (e.g. docs/reports/IN_Portfolio_Audit_book.pdf)
  and sets up, modifies, or replaces Good-Till-Triggered (GTT) buy or stop
  alerts in the user's live, signed-in Google Chrome Zerodha Kite session
  (https://kite.zerodha.com/orders/gtt) using macos-browser-automation.
---

# Zerodha GTT Setup

## Overview

Extracts sequenced execution alerts (Phase 2B support buy bands and/or protective stops) from a portfolio audit PDF and stages them as real **CNC Limit GTT** orders in Zerodha Kite using the user's already-authenticated Chrome session on macOS. Handles ₹0.05 tick rounding, modifying or replacing existing `ACTIVE` GTTs for the same symbol and side, exchange SME minimum lot-size constraints, and post-placement verification against the live GTT table.

## Security & Authorization Rules

- Never read `.env` or any credentials file; never copy cookies, session data, or passwords out of a browser profile.
- Never log in on the user's behalf. The user must already be signed into `https://kite.zerodha.com/orders/gtt` in their normal Chrome profile.
- Always confirm candidate selection, price-band rule (upper bound, midpoint, or lower bound), and any SME lot-size upsizing with the user before submitting real GTT orders.

## Dependencies

- **`macos-browser-automation`** (`~/.agents/skills/macos-browser-automation/SKILL.md`): Provides `chrome_ctl.py` to execute JavaScript in the user's live Chrome tab via macOS Apple Events (`View > Developer > Allow JavaScript from Apple Events` must be enabled).

## Quick Start

```bash
# 1. Verify Chrome Apple Events and Kite GTT tab
uv run .agents/skills/zerodha_gtt_setup/scripts/kite_gtt.py check

# 2. Snapshot current ACTIVE GTTs
uv run .agents/skills/zerodha_gtt_setup/scripts/kite_gtt.py list --output /tmp/gtt_before.json

# 3. Place or modify/replace a batch of GTTs from a spec JSON
uv run .agents/skills/zerodha_gtt_setup/scripts/kite_gtt.py batch \
  --spec /tmp/gtt_specs.json \
  --on-existing modify \
  --output /tmp/gtt_after.json
```

## Utility Scripts

All commands in `.agents/skills/zerodha_gtt_setup/scripts/kite_gtt.py` write structured JSON to `--output`:

- **`check [--output <file>]`**: Verifies Chrome is running, Apple Events JS is enabled, and `https://kite.zerodha.com/orders/gtt` is open (navigating to it if needed).
- **`list --output <file>`**: Reads the live Kite GTT table (`row_index`, `created_on`, `instrument`, `type`, `trigger`, `ltp`, `qty`, `status`).
- **`place --symbol <SYM> --qty <N> --trigger <P> --price <P> [--exchange NSE|BSE] [--side BUY|SELL] [--on-existing modify|replace|skip] [--sme-one-lot] --output <file>`**:
  - Rounds `trigger` and `price` to the nearest `₹0.05` tick.
  - Checks for an existing `ACTIVE` GTT matching `(symbol, side)` (normalizing `-SM`/`-BE`/`-BZ` suffixes) and modifies/replaces it per `--on-existing` (default `modify`, falling back to `replace` if edit is unavailable).
  - Detects HTML5 `:invalid` constraints (e.g. SME lot minimums) before submitting; unless `--sme-one-lot` is passed, cancels cleanly and returns `"status": "sme_lot_required"` with `min_qty` and `adjusted_notional`.
- **`batch --spec <orders.json> [--on-existing modify|replace|skip] [--sme-one-lot] --output <file>`**: Runs `place` sequentially with 1.0s pacing between orders, then re-reads the live GTT table into `verified_table`.

## Workflow

1. **Read the Portfolio Audit PDF:** Read the target PDF (default `docs/reports/IN_Portfolio_Audit_book.pdf`), focusing on the *Execution Playbook* table (symbol, advisory size, support/alert band, protective stop, and routing/validity).
2. **Confirm Parameters with the User:**
   - Which candidates to stage (e.g., all Phase 2B challengers vs. top Tier-2 picks, and whether to include protective stops).
   - Which price within each support band to use for `Trigger price` and `Limit price` (recommended: upper bound of the band, rounded to `₹0.05`, matching the playbook checklist).
3. **Check Chrome & Existing GTTs:** Run `kite_gtt.py check` and `kite_gtt.py list`. Flag any existing `ACTIVE` GTTs that will be modified or replaced.
4. **Stage & Handle SME Lot Constraints:** Write a spec JSON and run `kite_gtt.py batch --on-existing modify`. If any ticker returns `"status": "sme_lot_required"` (e.g., `YASHHV` min `125` sh on BSE, `PROV-SM` min `80` sh on NSE), present the minimum lot size and adjusted notional to the user and ask whether to place 1 SME lot (`--sme-one-lot`) or skip.
5. **Verify & Report:** Inspect `verified_table` in the output JSON and report every `ACTIVE` GTT (instrument, type, trigger/limit price, qty, notional, and status), noting Kite's 1-year GTT expiry vs. the audit's 14-day review window.

## Common Mistakes & Kite UI Gotchas

- **Clicking the hidden `.instrument-search-modal`:** Kite keeps `.instrument-search-modal` in the DOM with `display: none`. Clicking `New GTT` actually opens `.market-depth-widget` — search inside `.market-depth-widget input[type=text]`, select the matching `li.results-item`, then click `Create GTT` to open `.gtt-window`.
- **Forgetting to switch `Market` → `Limit`:** `.gtt-window` defaults to `Market` (disabling the `Price` input). Click `input[value=LIMIT]` and wait ~0.4s for Vue to enable `Price` before setting it.
- **Silent HTML5 validation blocks on `Place`:** `button.place` is `type="submit"`, so an SME lot-size violation (`qty < min`) silently blocks submission with no Kite toast. Always inspect `input:invalid` in `.gtt-window`.
- **Sub-tick prices:** NSE/BSE reject prices not divisible by `₹0.05` (e.g. `₹211.26` → `₹211.25`).
