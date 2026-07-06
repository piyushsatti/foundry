#!/usr/bin/env bash
# PreToolUse Bash — block commits/pushes directly to main/master
source ~/.claude/hooks/stats.sh
INPUT=$(cat)
CMD=$(echo "$INPUT" | jq -r '.tool_input.command // empty')
if echo "$CMD" | grep -qE '^git (commit|push|merge)'; then
  BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
  [ -z "$BRANCH" ] && exit 0  # not in a git repo — can't determine branch, allow
  if echo "$BRANCH" | grep -qE '^(main|master)$'; then
    log_stat "main-branch-guard" "PreToolUse" "deny" "$BRANCH"
    deny_hook "Direct commit/push to $BRANCH blocked. Use a feature branch and PR."
  fi
fi
