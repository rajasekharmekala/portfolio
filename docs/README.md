# Published reports (GitHub Pages)

This folder is the only thing GitHub Pages serves.

- `docs/reports/` holds only the latest published report for each report type and market. Publishing overwrites the file of the same name. Earlier versions are in git history.
- `docs/index.html` lists the files in `docs/reports/`. It is regenerated from that folder, never edited by hand.
- `docs/.nojekyll` must stay, so Pages serves the files as they are.
- Publish only a report that passed `validate_report.py` (`RESULT: PASS`) and the reviewer gate (`APPROVE`).
- Reports contain personal holdings. Use a private repository, or publish publicly only after an explicit decision for that repository.
- Commit and push are done by the user.
