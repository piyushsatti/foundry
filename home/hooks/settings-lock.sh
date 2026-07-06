#!/usr/bin/env bash
# PreToolUse Edit|Write|Bash — lock ~/.claude/settings*.json against edits by Claude.
#
# Rationale: settings.json holds permission deny rules and defaultMode. If Claude
# can edit it, Claude can also lift its own restrictions (e.g. flip to bypassPermissions
# mode, remove the Atlassian write-tool denies). User must modify these files
# manually with a text editor outside Claude.

source ~/.claude/hooks/stats.sh

INPUT=$(cat)
TOOL=$(echo "$INPUT" | jq -r '.tool_name // empty')

# Files we lock: settings.json, settings.local.json, managed-settings.json under any .claude/
settings_pattern='\.claude/(settings|settings\.local|managed-settings)\.json'

if [[ "$TOOL" == "Edit" || "$TOOL" == "Write" || "$TOOL" == "MultiEdit" ]]; then
  FILE=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
  if echo "$FILE" | grep -qE "$settings_pattern"; then
    log_stat "settings-lock" "PreToolUse" "deny" "$(basename "$FILE")"
    deny_hook "Editing ~/.claude/settings*.json is locked. Modify it manually with a text editor if you need to change permissions or modes."
    exit 0
  fi
elif [[ "$TOOL" == "Bash" ]]; then
  CMD=$(echo "$INPUT" | jq -r '.tool_input.command // empty')
  if echo "$CMD" | grep -qE "$settings_pattern"; then
    # Block if the command pairs the settings path with any write-capable operator.
    # Includes interpreters (python/node/perl/ruby) and ln/install: now that inline
    # interpreter code is permitted, `python3 -c 'open(settings,"w")...'` must not be
    # able to rewrite the permission file. (Kernel `chattr +i` is the hard backstop;
    # this is defense-in-depth.) Pure reads (cat/jq/grep/less/diff) are not matched.
    if echo "$CMD" | grep -qE '(>>?[[:space:]]|(^|[[:space:]])(tee|mv|cp|rm|ln|install|truncate|sponge|chmod|python3?|node|perl|ruby)[[:space:]]|sed[[:space:]]+-i|sed[[:space:]]+--in-place|dd[[:space:]]+of=|sponge)'; then
      log_stat "settings-lock" "PreToolUse" "deny" "bash-write"
      deny_hook "Bash command would modify ~/.claude/settings*.json. Locked by settings-lock hook — edit manually outside Claude."
      exit 0
    fi
  fi
fi

exit 0
