#!/usr/bin/env bash
# SessionStart — inject existing TODOs/FIXMEs into context
source ~/.claude/hooks/stats.sh
CWD=$(pwd)
if [ -d "$CWD/.git" ]; then
  TODOS=$(grep -r \
    --exclude-dir=node_modules \
    --exclude-dir=.venv \
    --exclude-dir=__pycache__ \
    --exclude-dir=.git \
    --exclude-dir=target \
    --exclude-dir=build \
    --exclude-dir=dist \
    --exclude-dir=install \
    --exclude-dir=log \
    --exclude-dir=.serena \
    --exclude-dir=venv \
    --exclude-dir=ubunto20simulate \
    --include="*.py" --include="*.js" --include="*.ts" --include="*.cpp" --include="*.h" \
    -n "TODO\|FIXME\|HACK" "$CWD" 2>/dev/null | head -20)
  if [ -n "$TODOS" ]; then
    TODO_COUNT=$(echo "$TODOS" | wc -l)
    log_stat "todo-detector" "SessionStart" "found" "$TODO_COUNT"
    jq -n --arg ctx "Existing TODOs/FIXMEs in this project:\n$TODOS" \
      '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":$ctx}}'
  fi
fi
