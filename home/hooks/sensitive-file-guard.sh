#!/usr/bin/env bash
# PreToolUse Write|Edit — block edits to sensitive files
source ~/.claude/hooks/stats.sh
INPUT=$(cat)
FILE=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

# NOTE: edits to ~/.claude/hooks/* are gated by claude-self-guard (ask) — no bypass here,
# so the sensitive-name check below still applies to hook files (F2 fix, 2026-06-11).

if echo "$FILE" | grep -qiE '(^|/)([^/]*\.(pem|key|p12|pfx|crt)|[^/]*(credentials?|secrets?)[^/]*)$'; then
  log_stat "sensitive-file-guard" "PreToolUse" "deny" "$(basename "$FILE")"
  deny_hook "Sensitive file detected (key, credentials). Approve manually if this edit is intentional."
  exit 0
fi
