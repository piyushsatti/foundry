#!/usr/bin/env bash
# cwd-drift-guard.sh — block bare `cd` as the leading command in a bash tool call.
# Allows: (cd ...), bash -c 'cd ...', subshell patterns.
# Blocks: `cd /foo`, `cd /foo && cmd` (top-level cd that persists session CWD).

input=$(cat)
cmd=$(printf '%s' "$input" | jq -r '.tool_input.command // empty' 2>/dev/null)

if [[ -z "$cmd" ]]; then exit 0; fi

trimmed="${cmd#"${cmd%%[![:space:]]*}"}"
if [[ "$trimmed" =~ ^cd[[:space:]] && ! "$trimmed" =~ ^\(cd ]]; then
    printf '{"decision":"block","reason":"Bare `cd` persists session CWD (cwd-drift-guard). Use absolute paths or subshell: (cd /path && cmd)."}\n'
    exit 0
fi
exit 0
