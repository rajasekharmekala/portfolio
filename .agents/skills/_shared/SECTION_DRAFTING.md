# Section Drafting (how long reports are written at lower cost)

Long reports are drafted in pieces, each by a fresh agent with a small, fixed input. This keeps each agent's context small, makes each section cheap to redo, and stops one section's errors from spreading into the others. The numbers come only from the fact pack. The prose comes only from the section plan and the section brief.

## 1. Inputs

- The fact pack: `<RUN_DIR>/cache/factpack_<MKT>_<date>.json`, written by `market_facts.py`. It is roughly an order of magnitude smaller than the full ledger, which is why sections use it and not the ledger.
- The research record: `<RUN_DIR>/cache/research_<MKT>_<date>.json`.
- The standards: `REPORT_EDITORIAL_STANDARD.md` (structure and floors), `REPORT_VOICE.md` (how to write), `REPORT_PALETTE.md` (colours).
- The report skill for this market (its blueprint table, for example 7A or 7B).

## 2. The plan

The writer creates `<RUN_DIR>/work/plan.json` before drafting. The plan has one entry per section:

Every `<date>` placeholder in ledger, research, validation, and dated output paths means the latest completed session resolved under `RUN_PROTOCOL.md` §0; it never means the run's calendar date by default.

```json
{"sections": [
  {"id": "00_head", "title": "Title, infobox, primer, lede", "blueprint": "7A Title/infobox + Primer + lede", "names": [], "targets": {"prose_words": 1200}},
  {"id": "01_big_picture", "title": "1 Big Picture", "blueprint": "7A row 1", "names": [], "targets": {"prose_words": 1400, "tables": 2}},
  {"id": "03_bull_list", "title": "3 Bull list", "blueprint": "7A row 3", "names": ["ZYDUSLIFE", "..."], "targets": {"prose_words": 1500, "casenotes": 3}}
]}
```

`names` lists the symbols the section may discuss. A section agent may quote only those symbols and only the fact-pack entries for them. Keep the list tight: a section that covers the Bull List does not need the Bear List's names.

## 3. Drafting each section

For each section, in order, run one fresh agent with exactly these inputs:

1. Its plan entry.
2. The fact-pack entries for its `names`, plus the parts of `regime`, `macro`, `benchmarks_and_sectors`, `bull_pick`, and `bear_pick` that its blueprint row uses. Do not pass the rest of the fact pack.
3. The research entries that its blueprint row needs, with their URLs and as-of dates.
4. The last paragraph of the previous section, so the bridge is written against what was actually said.
5. The story-brief bullets relevant to this section (not the whole brief).
6. The three standards.

Its output is one file: `<RUN_DIR>/work/sections/<id>.html`, containing only that section's HTML, with no `<html>` or `<style>` tags. It must follow the section's blueprint row and the voice guide. Every H2 and H3 gets its own explanation, and the section ends with a bridge.

## 4. Checking each section as it lands

Run the partial validator on the fragment before starting the next section:

```
.venv/bin/python scripts/validate_report.py --report <RUN_DIR>/work/sections/<id>.html --kind <market_intel|portfolio_audit> --facts <RUN_DIR>/cache/facts_<MKT>_<date>.json --partial
```

Fix any FAIL and re-run that section only. Partial mode checks banned phrases, thin subsections, repeated openings, price mismatches against the ledger, palette, emoji, and table intros and takeaways. Whole-report floors are not checked yet.

## 5. Assembly and the full gate

1. Concatenate `00_head` and the section files in plan order into `<RUN_DIR>/work/body.html`. Do not write a `<head>` or `<style>` block. Then run `.venv/bin/python scripts/assemble_report.py --body <RUN_DIR>/work/body.html --out docs/reports/<Name>_<date>.html --market <IN|US> --facts <RUN_DIR>/cache/facts_<MKT>_<date>.json --research <RUN_DIR>/cache/research_<MKT>_<date>.json`. The script builds the head from the palette `:root` block in `REPORT_PALETTE.md`, then `report_base.css`, then `book_components.css`, wraps the body in `<div class="report">`, wraps each bare `wikitable` in `<div class="table-wrap">`, adds the missing TradingView and Screener (IN) or Finviz (US) links next to every bold ticker, and appends a References list built from every link in the body plus every `source_url` in the research record.
2. Run the full validator on `<RUN_DIR>/report.html`. This is the gate that matters. It must print `RESULT: PASS`.
3. Run the reviewer gate on `report.html` (see the workflow's reviewer section). The reviewer reads the assembled report, not the fragments.

Findings from the reviewer go back to the section that owns the quoted text. Re-draft that section only, re-run its partial check, re-assemble, and re-run the full gate. Apply the strict four-round cap in `REVIEWER_OPERATIONS.md`: after round 4, fix findings best-effort, rerun the full validator and pre-delivery checklist, record any remaining findings, and do not start another review.

## 6. Cost rules

- Pass only the fact-pack entries a section names. Never pass the full ledger or the full fact pack to a section agent.
- Re-draft a section, not the report, when a single finding is local.
- Keep section outputs as files in `<RUN_DIR>/work/`. Agents pass paths, not contents, between steps.
- Use the smallest model the reviewer calibration has accepted for drafting checks, and the chosen writer model for the head and the lede.
