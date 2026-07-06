#!/usr/bin/env bash
# Stop (async) — append session summary to running log
source ~/.claude/hooks/stats.sh
LOG=~/.claude/session-log.md

CWD=$(pwd)
BRANCH=$(git -C "$CWD" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "no-git")
LAST=$(git -C "$CWD" log --oneline -1 2>/dev/null || echo "no commits")
ENTRY="- [$(date '+%Y-%m-%d %H:%M')] $CWD ($BRANCH) — $LAST"

# Dedup check first — Stop fires on every tool-use stop, not just true session end
LAST_ENTRY=$(tail -1 "$LOG" 2>/dev/null)
if [ "$ENTRY" = "$LAST_ENTRY" ]; then
  log_stat "session-log" "Stop" "skipped"
  exit 0
fi

# Rotate only when we're actually going to write (keep last 1000 of 2000)
if [ -f "$LOG" ] && [ "$(wc -l < "$LOG")" -gt 2000 ]; then
  tail -1000 "$LOG" > "$LOG.tmp" && mv "$LOG.tmp" "$LOG"
fi

echo "$ENTRY" >> "$LOG"
log_stat "session-log" "Stop" "fired" "$BRANCH"
