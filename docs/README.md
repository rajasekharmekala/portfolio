# Published reports (GitHub Pages)

This folder is the only thing GitHub Pages serves.

- `docs/reports/` holds only the latest published report for each report type and market. Publishing overwrites the file of the same name. Earlier versions are in git history.
- `docs/index.html` is the stable vanilla-JavaScript homepage. `portal.js` fetches `portal-data.json` to render recent activity, latest workflow reports, and a searchable dossier library. `portal.css` owns its responsive layout. Rebuild commands regenerate data, not the homepage HTML.
- Run `.venv/bin/python scripts/build_dossier_portal.py` to rebuild the catalog from existing published files. All generated destinations must exist under `docs/`. Older reports use last Git commit timestamps, labeled as such; unknown timestamps stay unknown. Read status is local to each browser and resets for a report when its update timestamp changes.
- After a successful workflow, run `.venv/bin/python scripts/build_dossier_portal.py --completed docs/reports/<report>.html --workflow "Portfolio audit" --market US --summary "One-sentence decision overview" --highlight "Key change or risk" --repair-links`. `--completed` accepts multiple report/dossier paths; repeat `--highlight` as needed. Use stable workflow names. Include `portal-data.json` and `portal-updates.json` in publication commits. Do not stamp existing reports as newly completed merely to seed the homepage.
- `--repair-links` repairs resolvable local report links while preserving HTML formatting. Unpublished or missing local destinations become non-clickable; external links are preserved. Email sending converts valid local links to absolute URLs under `https://git.corp.adobe.com/pages/mereddy/ai-automations/`.
- Preview with `.venv/bin/python -m http.server 8765 --directory docs` and open `http://localhost:8765/`. JSON fetching requires HTTP rather than opening the page with `file://`.
- Verify with `.venv/bin/python -m unittest discover -s scripts -p test_portal.py` and `node --check docs/portal.js`.
- `docs/.nojekyll` must stay, so Pages serves the files as they are.
- Publish only after `validate_report.py` returns `RESULT: PASS` and the reviewer process is complete: APPROVE within four rounds, or best-effort fixes and a passing validator after the strict fourth-round limit.
- Publishing reports, including personal holdings, to this repository's public GitHub Pages is pre-authorized and mandatory after those gates. Keep one latest report per report type and market; older versions remain in git history.
- Regenerate the indexes, then commit and push the reports and indexes automatically to the configured `origin` branch. Never force-push or stage unrelated working-tree changes.

## Email Delivery

Emails contain only a short summary, up to five highlights, qualifying events and an absolute link to the complete published report. Publish and push before emailing. Existing received emails are unchanged.

Market intelligence and portfolio audits always receive digest emails. Watchlist underwriting, archive resurrection and displacement runs are silent unless a company newly qualifies for the shortlist or a shortlisted candidate newly passes displacement gates against a current holding. Archive-to-watchlist moves and unchanged eligibility do not qualify. Workflows record evidence and sent/skipped status in the run manifest.

Use `scripts/send_email.py --html-file <published-report.html> --subject <subject> --report-type <type> --summary <overview> --highlight <highlight>`. Repeat `--shortlisted SYMBOL` or `--displacement "CANDIDATE replaces HOLDING: gate evidence"` only for verified new events. `--dry-run` previews the decision and digest without loading credentials or sending mail. Direct Python callers must supply `source_path` for reports that will be emailed.
