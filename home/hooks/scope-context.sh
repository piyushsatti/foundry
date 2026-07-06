#!/usr/bin/env bash
# SessionStart — inject scope context for current project
# Reads session-scopes.json and lists available scopes so Claude asks which one the user is working in.

SCOPES_FILE="$HOME/.cache/cc/session-scopes.json"
SCOPES_DIR="$HOME/.claude/scopes"
[[ -f "$SCOPES_FILE" ]] || exit 0

CWD=$(pwd)
# Encode the CWD into its cwd-key the same way Claude Code does: replace / AND . with -
# (was "${CWD//\//-}" which only handled slashes — wrong for .worktrees paths; see meditate P0/T3).
ENCODED=$(printf '%s' "$CWD" | sed 's|[/.]|-|g')

# Get unique scopes — try v2 real_path matching first, fall back to encoded matching
SCOPES=$(jq -r --arg p "$ENCODED" --arg rp "$CWD" '
  [to_entries[]
   | select(.key != "__meta")
   | select(.value.project == $p or .value.real_path == $rp)
   | .value.scope] | unique | .[]
' "$SCOPES_FILE" 2>/dev/null)

[[ -z "$SCOPES" ]] && exit 0

# Build context message (using real newlines so jq --arg escapes them correctly)
PROJECT_NAME=$(basename "$CWD")
PRIMER_DIR="$SCOPES_DIR/$PROJECT_NAME"
NL=$'\n'
MSG="Active scopes for $PROJECT_NAME:"
while IFS= read -r scope; do
    [[ -z "$scope" ]] && continue
    if [[ -f "$PRIMER_DIR/$scope.md" ]]; then
        MSG+="${NL}  - $scope (has primer at $PRIMER_DIR/$scope.md)"
    else
        MSG+="${NL}  - $scope"
    fi
done <<< "$SCOPES"
MSG+="${NL}Ask which scope the user is working in, or if this is a new scope."

jq -n --arg ctx "$MSG" '{
    "additionalContext": $ctx
}'
