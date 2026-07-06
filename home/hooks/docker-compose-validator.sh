#!/usr/bin/env bash
# PostToolUse Edit|Write — validate docker-compose files after edits
source ~/.claude/hooks/stats.sh
INPUT=$(cat)
FILE=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
if echo "$FILE" | grep -qE '(docker-)?compose.*\.ya?ml$'; then
  result=$(docker compose -f "$FILE" config 2>&1)
  code=$?
  if [ $code -ne 0 ]; then
    log_stat "docker-compose-validator" "PostToolUse" "warn" "$(basename "$FILE")"
    jq -n --arg ctx "docker compose config validation failed for $FILE:\n$result" \
      '{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":$ctx}}'
  fi
fi
