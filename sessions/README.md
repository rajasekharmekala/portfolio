# Session folders

OpenCode sessions for this project are grouped by workflow and market.
These folders are session working directories only — session content lives
in the OpenCode database (`~/.local/share/opencode/opencode.db`), not here.

| Folder | Contents |
|---|---|
| `watchlist-in/` | IN Watchlist to Shortlist runs and their sub-agent sessions |
| `watchlist-us/` | US Watchlist to Shortlist runs and their sub-agent sessions |
| `market-intelligence-in/` | IN Market Intelligence runs |
| `market-intelligence-us/` | US Market Intelligence runs |
| `portfolio-audit-in/` | IN Portfolio Audit runs |
| `portfolio-audit-us/` | US Portfolio Audit runs |
| `misc/` | One-off / admin sessions |

Grouped 2026-10-13. A resumed session works from its folder, which is still
inside this repo (same git root and config discovery). New scheduled runs
still start at the repo root; move them here afterwards if needed.

Exception: `New session - 2026-10-11T17:54:32.068Z` (automation setup / US
audit attempt) stays at the repo root — its pre-existing message-sequence
counter is inconsistent, so the server rejects a move for it.
