#!/usr/bin/env bash
# PostToolUse Write|Edit|MultiEdit (async) — tag Claude-written files with xattr.
#
# Tags every Claude-authored file with: user.claude.authored = "<UTC-ts>|<session_id>"
# The companion hook xattr-guard.sh then blocks exec/copy of tagged files until
# the user runs `~/.claude/bin/bless <file>` in their terminal.
#
# Skipped paths:
#   - ~/.claude/hooks/* — defer to future hooks-lock work (workflow_pending_cleanup.md 2026-05-01)
#
# Best-effort: silent on failure (filesystems lacking xattr support).

INPUT=$(cat)
FILE=$(printf '%s' "$INPUT" | jq -r '.tool_input.file_path // empty')
[ -z "$FILE" ] && exit 0

# Skip hook files — hook protection belongs to the future hooks-lock hook.
case "$FILE" in
  "$HOME"/.claude/hooks/*) exit 0 ;;
  "$HOME"/.claude/bin/*) exit 0 ;;
esac

# Only tag if the file actually exists on disk (Write/Edit may have been blocked by another hook)
[ -e "$FILE" ] || exit 0

SESSION_ID=$(printf '%s' "$INPUT" | jq -r '.session_id // ""')
TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)

setfattr -n user.claude.authored -v "${TS}|${SESSION_ID}" "$FILE" 2>/dev/null

exit 0
