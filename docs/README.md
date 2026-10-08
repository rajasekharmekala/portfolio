# Published reports (GitHub Pages)

This folder is the only thing GitHub Pages serves. Nothing here is generated automatically.

Rules:
1. Publish only a report that has passed `scripts/validate_report.py` in its run. Copy the HTML into `docs/reports/`. Do not copy workbooks, ledgers, research files, transcripts, or `.env`.
2. All links inside a page must be relative. No `/Users/...` paths and no `file://` URLs.
3. `docs/.nojekyll` must stay, so Pages serves the files as-is.
4. Personal holdings and position sizes are in these reports. Publish only to a private repository (Pages from a private repo is limited to GitHub paid plans and to repository members), or only after the user has explicitly approved public publication. Confirm the repo's visibility before the first publish.
5. Regenerate `docs/index.html` only from the files currently in `docs/reports/`.
