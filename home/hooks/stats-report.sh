#!/usr/bin/env bash
# Hook stats report — run manually to see aggregate data
# Usage: bash ~/.claude/hooks/stats-report.sh [days]
#        bash ~/.claude/hooks/stats-report.sh 30   # last 30 days (default)
#        bash ~/.claude/hooks/stats-report.sh 7    # last 7 days

STATS="${HOME}/.claude/hook-stats.jsonl"
DAYS="${1:-30}"

if [ ! -f "$STATS" ]; then
  echo "No stats yet at $STATS"
  echo "Stats are written as hooks fire. Try again after a few sessions."
  exit 0
fi

TOTAL=$(wc -l < "$STATS")
SORTED_TS=$(jq -r '.ts' "$STATS" | sort)
FIRST=$(echo "$SORTED_TS" | head -1)
LAST=$(echo "$SORTED_TS" | tail -1)

# Date cutoff (GNU date / macOS date compatible)
CUTOFF=$(date -u -d "${DAYS} days ago" '+%Y-%m-%d' 2>/dev/null \
      || date -u -v"-${DAYS}d"        '+%Y-%m-%d' 2>/dev/null \
      || echo "1970-01-01")

echo "╔══════════════════════════════════════════════════════╗"
echo "║           Claude Hook Stats Report                   ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""
echo "  All-time total events : $TOTAL"
echo "  Date range            : $FIRST → $LAST"
echo "  Report window         : last ${DAYS} days (since $CUTOFF)"
echo ""

# Filter to window
WINDOW=$(jq -r --arg d "$CUTOFF" 'select(.ts[:10] >= $d)' "$STATS")
WINDOW_COUNT=$(echo "$WINDOW" | grep -c '^{' || echo 0)

echo "  Events in window      : $WINDOW_COUNT"
echo ""

echo "──────────────────────────────────────────────────────"
echo "  By hook + result"
echo "──────────────────────────────────────────────────────"
echo "$WINDOW" | jq -r '[.hook, .result] | @tsv' \
  | sort | uniq -c | sort -rn \
  | awk '{printf "  %5s  %-30s %s\n", $1, $2, $3}'
echo ""

echo "──────────────────────────────────────────────────────"
echo "  Deny events (with context)"
echo "──────────────────────────────────────────────────────"
DENIES=$(echo "$WINDOW" | jq -r 'select(.result=="deny") | [.ts[:10], .hook, (.ctx // "-")] | @tsv')
if [ -n "$DENIES" ]; then
  echo "$DENIES" | awk '{printf "  %s  %-28s %s\n", $1, $2, $3}'
else
  echo "  (none in window)"
fi
echo ""

echo "──────────────────────────────────────────────────────"
echo "  Session log: fired vs skipped"
echo "──────────────────────────────────────────────────────"
FIRED=$(echo "$WINDOW"   | jq -r 'select(.hook=="session-log" and .result=="fired")'   | grep -c '^{' || echo 0)
SKIPPED=$(echo "$WINDOW" | jq -r 'select(.hook=="session-log" and .result=="skipped")' | grep -c '^{' || echo 0)
TOTAL_SL=$(( FIRED + SKIPPED ))
if [ "$TOTAL_SL" -gt 0 ]; then
  DEDUP_PCT=$(( SKIPPED * 100 / TOTAL_SL ))
  echo "  Fired  : $FIRED"
  echo "  Skipped: $SKIPPED  (${DEDUP_PCT}% deduped)"
else
  echo "  (no session-log events in window)"
fi
echo ""

echo "──────────────────────────────────────────────────────"
echo "  Daily activity (events per day)"
echo "──────────────────────────────────────────────────────"
echo "$WINDOW" | jq -r '.ts[:10]' | sort | uniq -c \
  | awk '{printf "  %s  %s events\n", $2, $1}'
echo ""
