# Portfolio Research Generation

Every newly generated report or dossier must use the Research Desk design matching docs/index.html. Read .agents/skills/_shared/REPORT_DESIGN.md. Assemble the complete research body with scripts/assemble_report.py; never copy an old published HTML shell or follow an older Wikipedia head/style template in a skill. This rule supersedes old presentation instructions only, not analysis, sourcing, methodology or quality gates.

Use --market IN/US, --kind report/dossier, --workflow and --as-of. The actual generation timestamp is embedded in the header in America/Los_Angeles time (PDT/PST); the verified market-session cutoff is separate. New workflow outputs use stable filenames; dossier names remain SYMBOL_dossier.html. Do not remove or truncate any research, table, citation or reference for the design.

Newly completed workflows must pass the modern-layout check in scripts/portal_publish.py in addition to all existing research-quality checks. Never bypass the check. Catalog rebuilds may still include historical reports unchanged. Use --layout-only solely for explicitly requested presentation updates to existing research; never call those new research or invent their original generation timestamp.

Use .venv/bin/python for Python commands. Do not change unrelated user work, publish fresh research without its quality gates, or commit/push without user authorization.
