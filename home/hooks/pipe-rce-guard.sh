#!/usr/bin/env bash
# PreToolUse Bash — deny pipe-to-shell / process-substitution / command-substitution RCE patterns.
#
# Claude Code's permission system matches each piped subcommand independently, so
# Bash() deny rules can't catch composite RCE patterns. This hook regexes the full
# command string before the tool runs.
#
# Catches:
#   1. <downloader> ... | [sudo|nohup|env [flags|values...]] <shell-or-interpreter>
#   2. <shell> <(<downloader> ...)            -- process substitution
#   3. source/.<space><(<downloader> ...)
#   4. <interpreter> -c|-e|-Command "$(<downloader> ...)"   -- command substitution
#
# Misses (out of scope by design):
#   - File-then-exec: curl -o /tmp/x && sh /tmp/x  (two distinct bash invocations)
#   - Base64 / intermediate filters: curl | base64 -d | sh
#   - Obfuscated interpreter names: curl | $(echo bash)
#   - Determined attackers — this is a tripwire for accidents/canonical attacks.

INPUT=$(cat)
CMD=$(printf '%s' "$INPUT" | jq -r '.tool_input.command // empty')

[ -z "$CMD" ] && exit 0

# Downloader / interpreter alternations (kept short for regex readability)
DL='(curl|wget|fetch|http|aria2c|axel|curlie|xh|gh|nc|ncat|socat|scp|rsync)'
SH='(s?h|bash|zsh|ksh|dash|python3?|node|ruby|perl|pwsh)'

# Optional command prefix: sudo/nohup/env with any flags or env-var assignments
# Matches: "", "sudo ", "sudo -E ", "sudo -u root ", "sudo --preserve-env=ALL ", "env FOO=bar "
WRAP='((sudo|nohup|env)([[:space:]]+[-=._/[:alnum:]]+)*[[:space:]]+)?'

DENY_REASON=""

# Pattern 1: pipe-to-shell (with optional sudo/nohup/env wrap before the shell)
if printf '%s' "$CMD" | grep -qE "(^|[^[:alnum:]_])${DL}[[:space:]]+[^|&;]*\|[[:space:]]*${WRAP}${SH}([[:space:]]|$)"; then
    DENY_REASON="Pipe-to-shell pattern detected (download command piped to shell/interpreter)."

# Pattern 2 & 3: process substitution — bash <(curl ...), source <(curl ...), . <(curl ...)
elif printf '%s' "$CMD" | grep -qE "(^|[[:space:]])(${SH}|source|\\.)[[:space:]]+(-[^[:space:]]+[[:space:]]+)*<\\(${DL}[[:space:]]"; then
    DENY_REASON="Process-substitution shell pattern detected (e.g. bash/source/. <(curl ...))."

# Pattern 4: command substitution into interpreter — bash -c "$(curl ...)", eval "$(curl ...)"
elif printf '%s' "$CMD" | grep -qE "(${SH}|eval)[[:space:]]+(-c|-e|-Command)?[[:space:]]*[\"'\`]?\\\$\\(${DL}[[:space:]]"; then
    DENY_REASON="Command-substitution shell pattern detected (e.g. bash -c \"\$(curl ...)\")."
fi

if [ -n "$DENY_REASON" ]; then
    jq -n --arg reason "$DENY_REASON Download to a file and review before executing." \
       '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":$reason}}'
fi
