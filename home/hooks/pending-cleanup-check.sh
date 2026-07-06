#!/usr/bin/env bash
# SessionStart — remind about pending cleanup items for the current project
source ~/.claude/hooks/stats.sh
CWD=$(pwd)
[ -e "$CWD/.git" ] || exit 0   # -e not -d: in a worktree .git is a FILE (gitdir pointer), not a dir
CLEANUP_FILE="$(project_dir "$CWD")/memory/workflow_pending_cleanup.md"

if [ -f "$CLEANUP_FILE" ]; then
  PENDING=$(grep -c '^\- \[ \]' "$CLEANUP_FILE" 2>/dev/null || echo "0")
  if [ "$PENDING" -gt 0 ]; then
    log_stat "pending-cleanup-check" "SessionStart" "found" "$PENDING"
    jq -n --arg ctx "PENDING_CLEANUP_CHECK: Found $PENDING open item(s) in workflow_pending_cleanup.md. Review and surface to user before starting new work." \
      '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":$ctx}}'
  fi
fi
