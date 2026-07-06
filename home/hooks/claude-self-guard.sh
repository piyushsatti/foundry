#!/usr/bin/env bash
# PreToolUse Write|Edit|MultiEdit — surface "ask" prompt when Claude tries to
# modify its own enforcement layer.
#
# Protected paths:
#   ~/.claude/settings.json, ~/.claude/settings.local.json — permission rules + hook wiring
#   ~/.claude/hooks/* — the hook scripts that enforce everything else
#   ~/.claude/bin/* — user-facing helpers (e.g., bless)
#
# Rationale: settings-lock.sh is intentionally disabled to allow iteration.
# Until the proper hooks-lock work lands, this hook keeps the user in the loop
# for self-modification attempts so a prompt-injected Claude can't silently
# disable the rest of the defense layer.

INPUT=$(cat)
FILE=$(printf '%s' "$INPUT" | jq -r '.tool_input.file_path // empty')
[ -z "$FILE" ] && exit 0

H="$HOME"

case "$FILE" in
  "$H"/.claude/settings.json|"$H"/.claude/settings.local.json|"$H"/.claude/hooks/*|"$H"/.claude/bin/*)
    jq -nc --arg path "$FILE" \
      '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"ask","permissionDecisionReason":("Self-modification request: \($path) is part of Claude'\''s enforcement layer (permissions, hooks, or helper). Approve ONLY if you explicitly asked Claude to change this in the current session. Denying preserves the defense layer.")}}'
    exit 0 ;;
esac

exit 0
