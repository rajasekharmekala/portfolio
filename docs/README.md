# Published Research & Intelligence Portal (GitHub Pages)

This directory (`docs/`) is the root of the published research portal hosted via GitHub Pages.

## Directory Structure
- `docs/index.html`: Master Institutional Research Portal and Command Deck (GitHub Pages landing page with full-text search, multi-factor filtering, and direct links to reports and dossiers).
- `docs/reports/`: Institutional daily briefings, portfolio forensic audits, and options underwriting reports:
  - `Daily_Market_Intelligence_<YYYY-MM-DD>.html` (Indian Equities)
  - `Daily_US_Market_Intelligence_<YYYY-MM-DD>.html` (US Equities)
  - `Portfolio_Audit_<YYYY-MM-DD>.html` (Zerodha Demat Portfolio Audit)
  - `US_Portfolio_Audit_<YYYY-MM-DD>.html` (US Brokerage Portfolio Audit)
  - `Options_Underwriting_NSE_<YYYY-MM-DD>.html` / `Options_Underwriting_US_<YYYY-MM-DD>.html`
- `docs/blogs/`: Standalone Wikipedia-style equity research dossiers (`<SYMBOL>_dossier.html`), shared navigator (`dossier_nav.js`), registry (`dossiers.json`), and blogs index (`index.html`).

## Automated Publishing Workflow
All `.agents/workflows` and skills persist deliverables directly into `docs/`:
1. Market intelligence and portfolio audits write validated HTML briefings directly to `docs/reports/`.
2. Watchlist underwriting deep dives write company dossiers directly to `docs/blogs/<SYMBOL>_dossier.html`.
3. `scripts/build_dossier_portal.py` regenerates `docs/index.html`, `docs/blogs/index.html`, and `docs/blogs/dossiers.json`.
4. Committing and pushing to `main` auto-deploys all research to GitHub Pages.
