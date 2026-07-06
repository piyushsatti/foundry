#!/usr/bin/env bash
# PreToolUse Write|Edit — block edits to test files unless explicitly approved
source ~/.claude/hooks/stats.sh
INPUT=$(cat)
FILE=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

if echo "$FILE" | grep -qE '(^|/)tests?/|test_[^/]*\.py$|_test\.py$|conftest\.py$'; then
  log_stat "test-file-guard" "PreToolUse" "deny" "$(basename "$FILE")"
  deny_hook "Test file edit blocked: $(basename "$FILE"). Tests are the source of truth — fix the code, not the tests. Only edit tests when the user explicitly asks."
  exit 0
fi
