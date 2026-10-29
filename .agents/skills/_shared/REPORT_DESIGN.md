# Research Desk Report Design (Techmeme / Morning Brief Unified Theme)

Every newly generated report or dossier in `docs/reports/` and `docs/blogs/` must match the Techmeme-inspired Research Desk visual language used by `docs/index.html`, `/Users/mereddy/Desktop/github/personal-wiki`, and `/Users/mereddy/Desktop/github/rajasekharmekala.github.io`.

This file defines presentation and assembly rules only. Do **not** drop, shorten, rewrite or omit any analysis, table, citation, source link, reviewer check or methodology rule to fit the layout.

## Single Assembly Path

Write only the report body HTML (`<h1>` through references) to a scratch file, then assemble the published page with:

```bash
.venv/bin/python scripts/assemble_report.py \
  --body <RUN_DIR>/work/body.html \
  --out docs/reports/<Stable_Report_Name>.html \
  --market <IN|US> \
  --kind <report|dossier> \
  --workflow "<Workflow Name>" \
  --as-of "<Verified market-session cutoff>" \
  --facts <RUN_DIR>/facts_<MKT>_<date>.json \
  --research <RUN_DIR>/research_<MKT>_<date>.json
```

For company monographs / dossiers, use `--kind dossier` and `--out docs/blogs/<MKT>/<SYMBOL>_dossier.html`.

Never hand-write `<head>`, `<style>` or `<html>` in a report skill. Never copy an old report or dossier file as a shell.

## Header & Timestamp Contract

`scripts/assemble_report.py` injects:

- `<meta name="report-design" content="research-desk-v1">`
- `<meta name="generated-at" content="...">` in `America/Los_Angeles` time (`PDT`/`PST`)
- The top pre-navigation bar (`.desk-prenav`) with cross-repo links (`Home`, `Portfolio Desk`, `The Morning Brief`, `Travel Research`), logo banner (`.desk-logotab`), and `#174a61` Techmeme navy `.desk-masthead` bar
- `<header class="report-header">` (styled as the gold-accented executive synthesis banner) containing the `<h1>` and `Generated Date: <time datetime="...">DD Mon YYYY, HH:MM AM/PM PDT|PST</time>`
- An optional `Research as of ...` line when `--as-of` is passed

Do not put a fake generation timestamp in the body. Keep the market-session cutoff (`as of ...`) separate from the Pacific generation timestamp.

## Visual Rules

- **Palette**: `.agents/skills/_shared/REPORT_PALETTE.md` (`#ffffff` page, `#111111` ink, `#174a61` Techmeme navy brand/headers, `#002848` links with `#d0e8f4` hover highlight, `#fdfbe8` gold-bordered primer/synthesis banner, `#fcfdfe` deep-dive case cards, and WCAG-checked verdict pills).
- **Typography**: `Optima, "Century Gothic", "Trebuchet MS", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif` across body and headings; `tabular-nums` on every figure, price, date, delta, ratio and table cell.
- **Layout**: Centered Techmeme container with main reading column (`940px`) and sticky right-hand section contents rail (`250px`) on wide screens; responsive mobile section jumper on narrow screens.
- **Components**: Keep using `.infobox`, `.key-figures`, `table.wikitable`, `.callout`, `.callout-rule`, `.callout-warn`, `.case-note`, `.section-summary`, `.verdict` and `ol.reflist` as documented in `.agents/skills/_shared/BOOK_REPORT_TEMPLATE.md`. Tables are automatically wrapped in `<div class="table-wrap" tabindex="0" role="region">` with sticky `<th>` headers.

## Publish Enforcement

`scripts/portal_publish.py` refuses to complete a workflow if any target HTML page lacks the `research-desk-v1` design marker, masthead, Pacific `<time datetime>` header, or generated-at metadata. Use `--layout-only` only when restyling an existing historical file at the user's explicit request; `--layout-only` pages are marked `Layout updated` and are not accepted as newly completed workflow outputs.
