#!/usr/bin/env bash
# PreToolUse Write|Edit|MultiEdit — block Claude-specific files inside project repos.
#
# Claude-specific files (CLAUDE.md, memory/*.md, .claude/**) must live under
# ~/.claude/projects/<sanitized-path>/ — never inside the repo itself, where
# they'd pollute git, get accidentally committed, and leak to teammates on push.
#
# Hard deny: the deny message includes the correct project-scoped path. If you
# genuinely want a CLAUDE.md / memory file inside a repo, write it yourself in
# a terminal outside Claude.
#
# Allowed locations (no block):
#   ~/.claude/**, ~/Documents/claude/**

source ~/.claude/hooks/stats.sh

INPUT=$(cat)
FILE=$(printf '%s' "$INPUT" | jq -r '.tool_input.file_path // empty')
[ -z "$FILE" ] && exit 0

H="$HOME"

# Allow legitimate Claude storage locations
case "$FILE" in
  "$H"/.claude/*) exit 0 ;;
  "$H"/Documents/claude/*) exit 0 ;;
esac

PATTERN_TYPE=""
case "$FILE" in
  */CLAUDE.md)                                PATTERN_TYPE="CLAUDE.md" ;;
  */memory/MEMORY.md)                         PATTERN_TYPE="memory/MEMORY.md" ;;
  */memory/workflow_pending_cleanup.md)       PATTERN_TYPE="memory/workflow_pending_cleanup.md" ;;
  */memory/*.md)                              PATTERN_TYPE="memory/*.md" ;;
  */.claude/*)                                PATTERN_TYPE=".claude/" ;;
esac

[ -z "$PATTERN_TYPE" ] && exit 0

# Compute the correct project-scoped path for the deny message
case "$FILE" in
  */CLAUDE.md)
    REPO_DIR=$(printf '%s' "$FILE" | sed 's|/CLAUDE\.md$||')
    CORRECT="$(project_dir "$REPO_DIR")/CLAUDE.md"
    ;;
  */memory/*.md)
    REPO_DIR=$(printf '%s' "$FILE" | sed 's|/memory/[^/]*$||')
    FNAME=$(basename "$FILE")
    CORRECT="$(project_dir "$REPO_DIR")/memory/$FNAME"
    ;;
  */.claude/*)
    REPO_DIR=$(printf '%s' "$FILE" | sed 's|/\.claude/.*$||')
    REL=$(printf '%s' "$FILE" | sed 's|.*/\.claude/||')
    CORRECT="$(project_dir "$REPO_DIR")/.claude/$REL"
    ;;
esac

log_stat "claude-files-guard" "PreToolUse" "deny" "$PATTERN_TYPE"
deny_hook "Claude-specific files (${PATTERN_TYPE}) must NOT be written inside a repo — they pollute git, get accidentally committed, and leak to teammates on push. Correct project-scoped location: ${CORRECT}. If you really mean to put this file in the repo, do it yourself in a terminal."

exit 0
