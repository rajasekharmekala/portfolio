# Published reports (GitHub Pages)

This folder is the only thing GitHub Pages serves.

- `docs/reports/` holds only the latest published report for each report type and market. Publishing overwrites the file of the same name. Earlier versions are in git history.
- `docs/index.html` lists the files in `docs/reports/`. It is regenerated from that folder, never edited by hand.
- `docs/.nojekyll` must stay, so Pages serves the files as they are.
- Publish only after `validate_report.py` returns `RESULT: PASS` and the reviewer process is complete: APPROVE within four rounds, or best-effort fixes and a passing validator after the strict fourth-round limit.
- Publishing reports, including personal holdings, to this repository's public GitHub Pages is pre-authorized and mandatory after those gates. Keep one latest report per report type and market; older versions remain in git history.
- Regenerate the indexes, then commit and push the reports and indexes automatically to the configured `origin` branch. Never force-push or stage unrelated working-tree changes.
