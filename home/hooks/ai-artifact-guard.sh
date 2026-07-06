#!/usr/bin/env bash
# PreToolUse Write|Edit — redirect AI-generated artifacts out of the project tree
source ~/.claude/hooks/stats.sh
INPUT=$(cat)
FILE=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

[ -z "$FILE" ] && exit 0

# Already outside the project tree — allow unconditionally
if echo "$FILE" | grep -qE "^$HOME/\.claude/"; then
  exit 0
fi

# Detect docs/superpowers/ paths (plans, specs, any subdirectory)
if echo "$FILE" | grep -qE '/docs/superpowers/'; then
  PROJECT_ROOT=$(echo "$FILE" | sed 's|/docs/superpowers/.*||')
  REL_PATH=$(echo "$FILE" | sed 's|.*/docs/superpowers/||')
  DEST="$(project_dir "$PROJECT_ROOT")/docs/superpowers/$REL_PATH"
  log_stat "ai-artifact-guard" "PreToolUse" "deny" "docs/superpowers"
  deny_hook "AI artifacts must not be written inside the project tree. Write to: $DEST"
  exit 0
fi

# Detect .superpowers/ paths inside project directories
if echo "$FILE" | grep -qE '/\.superpowers/'; then
  log_stat "ai-artifact-guard" "PreToolUse" "deny" ".superpowers"
  deny_hook "Do not write to .superpowers/ inside the project tree. Use the brainstorm server with /tmp or redirect output externally."
  exit 0
fi
