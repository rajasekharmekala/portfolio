---
description: Fast standalone Options & Call-Convexity Desk workflow (US listed options/LEAPS & IN NSE F&O) with beginner-clear payoff math, graceful Robinhood browser check, and optional surgical dossier overlay updates.
---

# Options & Call-Convexity Desk Workflow (Market: `<MKT>`)

Read `_COMMON.md` first and follow `.agents/skills/options_desk/SKILL.md`.

**Input:** market `<MKT>` (`US` or `IN`) and optional specific symbol(s). With no symbols, screens all open contracts in `data/options/<MKT>.json` plus active `data/shortlist/<MKT>.json` candidates.

## 1. Start isolated worktree

```bash
.venv/bin/python scripts/run_session.py start --workflow options_desk --market <MKT>
```

## 2. Run multi-timeframe chart + options chain + graceful Robinhood probe

```bash
.venv/bin/python scripts/options_snapshot.py \
  --market <MKT> \
  --from-options --from-shortlist \
  --patch-dossier-specs \
  --out "<RUN_DIR>/cache/options_snapshot_<MKT>_<date>.json"
```

(Pass `--symbols <SYM...>` when targeting specific names. If Robinhood is not logged in on Chrome, the script automatically records that live broker access was unavailable and uses public chain data.)

## 3. Build `docs/reports/<MKT>_Options_Desk.html` & refresh dossier overlays

```bash
.venv/bin/python scripts/options_desk_builder.py \
  --snapshot "<RUN_DIR>/cache/options_snapshot_<MKT>_<date>.json" \
  --as-of "<YYYY-MM-DD>" \
  --out "docs/reports/<MKT>_Options_Desk.html" \
  --patch-published-dossiers
```

## 4. Validate & publish

Verify modern Research Desk layout (`portal_publish.py`), validate data (`data_layer.py --market <MKT> --validate`), and publish via `scripts/publish_run.py`.
