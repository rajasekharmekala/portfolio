#!/usr/bin/env bash
# cleanup_retired.sh : removes folders and files made obsolete by the JSON data layer.
# Default is a DRY RUN that only prints what it would do. Run with DRY_RUN=0 to delete.
set -euo pipefail

REPO="/Users/mereddy/Desktop/github/portfolio"
DRY_RUN="${DRY_RUN:-1}"
cd "$REPO"

run() {
  if [ "$DRY_RUN" = "1" ]; then echo "would: $*"; else echo "run:   $*"; "$@"; fi
}

echo "== Repo: $REPO  (DRY_RUN=$DRY_RUN)"

# 1. Generated caches and scratch from the old pipeline (gitignored, rebuilt by runs)
[ -d scratch ]             && run rm -rf scratch
[ -d scripts/.cache ]      && run rm -rf scripts/.cache
[ -d scripts/__pycache__ ] && run rm -rf scripts/__pycache__

# 2. Old logs (gitignored)
[ -f mcp-server.log ]      && run rm -f mcp-server.log

# 3. Old git worktree that held a copy of the retired workflows
if [ -d .worktrees/mereddy-adobe-friendly-doodle ]; then
  run git worktree remove --force .worktrees/mereddy-adobe-friendly-doodle || run rm -rf .worktrees/mereddy-adobe-friendly-doodle
  run git worktree prune
fi
[ -d .worktrees ] && [ -z "$(ls -A .worktrees 2>/dev/null)" ] && run rmdir .worktrees

# 4. Root symlinks that pointed at the workbook folders. shortlist and watchlist are only workbooks,
#    so they go. sheets is kept if it still holds markdown files you want (see the note below).
for link in shortlist watchlist; do
  [ -L "$link" ] && run rm "$link"
done
for dir in googledrive/shortlist googledrive/watchlist; do
  [ -d "$dir" ] && [ -z "$(ls -A "$dir" 2>/dev/null)" ] && run rmdir "$dir"
done

echo "== Done. Not touched: googledrive/blogs, googledrive/newsletters, googledrive/transcripts,"
echo "   googledrive/sheets (may hold markdown snapshots), docs/, data/, scripts/*.py, Portfolio Research System/."