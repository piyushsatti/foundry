#!/usr/bin/env bash
# PostToolUse Bash (async) — after a package install, tag freshly-created
# .venv/bin and node_modules/.bin entries with user.claude.authored, so that
# xattr-guard.sh re-gates them (bless required) if they are executed in an
# UNSANDBOXED session later. Closes the install-time-persistence gap: a binary
# planted by a malicious package in a sandboxed BUILD session cannot then run
# silently in an investigation/primary-clone session or by the user/CI.
#
# Best-effort: silent on failure (no xattr support, no install command, etc.).
source ~/.claude/hooks/patterns.sh
INPUT=$(cat)
CMD=$(printf '%s' "$INPUT" | jq -r '.tool_input.command // empty')
[ -z "$CMD" ] && exit 0

printf '%s' "$CMD" | grep -qE "(${CC_INSTALL_ALT})" || exit 0

proj="${CLAUDE_PROJECT_DIR:-$PWD}"
TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)

for d in "$proj"/.venv/bin "$proj"/node_modules/.bin; do
  [ -d "$d" ] || continue
  # Tag regular files created/modified in the last 2 minutes (the just-installed set).
  find "$d" -maxdepth 1 -type f -mmin -2 2>/dev/null | while read -r f; do
    setfattr -n user.claude.authored -v "${TS}|install" "$f" 2>/dev/null
  done
  # node_modules/.bin entries are usually symlinks — tag the resolved target too.
  find "$d" -maxdepth 1 -type l -mmin -2 2>/dev/null | while read -r f; do
    t=$(readlink -f "$f" 2>/dev/null)
    [ -n "$t" ] && [ -f "$t" ] && setfattr -n user.claude.authored -v "${TS}|install" "$t" 2>/dev/null
  done
done
exit 0
