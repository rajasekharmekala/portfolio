# Research Desk Design (Binding)

All new reports and dossiers match the homepage: IBM Plex Sans body, Newsreader headings, IBM Plex Mono figures and timestamps, pale neutral background and restrained green links. The assembler embeds REPORT_PALETTE.md, report_base.css, book_components.css, report_desk.css and report_desk.js. Older skill HTML heads, Wikipedia styling, encyclopedia subtitles and daily output naming do not apply to new presentation.

Write the complete body, not a competing head, stylesheet or script. Retain all fixed research chapters, financial tables, calculations and inputs, bull/base/bear cases and probabilities, sector and options analysis, underwriting layers, uncertainties, monitoring triggers, source URLs, citation anchors and numbered end references. Book-style analysis means readable, comprehensive research, not a Wikipedia page design. No analysis may be hidden in tabs, collapsed panels, tooltips or script-loaded content. JavaScript only enhances navigation, table access, reading progress and printing. Research must remain readable without it.

## Assemble Before Validation and Publication

```bash
.venv/bin/python scripts/assemble_report.py \
  --body "<RUN_DIR>/work/body.html" \
  --out docs/reports/US_Market_Intelligence.html \
  --market US --kind report --workflow "Market intelligence" \
  --as-of "<verified market-session date>" \
  --facts "<RUN_DIR>/facts_US_<session-date>.json" \
  --research "<RUN_DIR>/research_US_<session-date>.json"
```

Dossiers use --kind dossier --workflow "Company research" and docs/blogs/SYMBOL_dossier.html. Use the correct market. Reassemble after final editorial changes, then run the existing factual, citation, recomputation, readability, structural and independent-review gates without weakening them. Newly completed publication checks require the research-desk-v1 marker, shared interactions and timezone-aware header.

Generation time is the actual assembly time in America/Los_Angeles: PDT during daylight saving, PST during standard time, with an ISO offset. Never substitute session dates or hard-code a time. --as-of separately identifies the verified research cutoff. Metadata provides report market, kind, workflow and dates independently of filename parsing.

For future workflow reports, use one stable filename per market and type, such as IN_Market_Intelligence.html, US_Market_Intelligence.html, IN_Portfolio_Audit.html, US_Portfolio_Audit.html, IN_Options_Audit.html, US_Options_Audit.html, IN_Watchlist_to_Shortlist.html and US_Watchlist_to_Shortlist.html. Evidence files remain session-dated. Do not delete or rename old published reports solely for styling.

## Explicit Existing-Research Updates

Use --layout-only only when asked to restyle an existing report. It preserves original body text, links, IDs and tables, suppresses new ticker-link/research additions, and labels the header timestamp "Layout updated". Original generation time is unknown unless recorded; do not invent it. This is not new research, must not refresh workflow completion timestamps, and must not trigger an email.

## Checks

Run scripts/test_portal.py, JavaScript syntax checks and desktop/mobile browser checks. Check no overflow, working section and citation navigation, all references retained, print output and no-JavaScript reading. The named-report preservation test compares actual content before and after layout-only rendering. Never bypass failed checks by reverting the renderer to an old shell.
