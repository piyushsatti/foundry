#!/usr/bin/env bash
# Publish wiki/ to the GitHub wiki repo (github.com/piyushsatti/foundry.wiki).
#
# The wiki content is authored under wiki/ in this repo (PR-reviewable) and
# mirrored to the GitHub wiki, whose files live at the wiki root. This script
# does that mirror. Run it from a machine/session with wiki write access —
# the CI/agent environment is scoped to the main repo and cannot push here.
#
# Usage:  scripts/publish_wiki.sh ["commit message"]
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$REPO_ROOT/wiki"
WIKI_URL="${FOUNDRY_WIKI_URL:-https://github.com/piyushsatti/foundry.wiki.git}"
MSG="${1:-Publish wiki from foundry/wiki}"

[ -d "$SRC" ] || { echo "no wiki/ dir at $SRC" >&2; exit 1; }

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "Cloning $WIKI_URL"
git clone --depth 1 "$WIKI_URL" "$TMP"

# Replace all tracked content (keep .git), then flatten the folder tree into
# GitHub-wiki-flat pages (unique slugs + rewritten links) — see flatten_wiki.py.
( cd "$TMP" && git rm -rq . >/dev/null 2>&1 || true )
python3 "$REPO_ROOT/scripts/flatten_wiki.py" "$SRC" "$TMP"

cd "$TMP"
git add -A
if git diff --cached --quiet; then
  echo "No changes to publish."
else
  git commit -m "$MSG"
  git push
  echo "Published to $WIKI_URL"
fi
