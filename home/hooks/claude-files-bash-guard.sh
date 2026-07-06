#!/usr/bin/env bash
# PreToolUse Bash — hard-deny Bash commands that LAND a file at a Claude-specific
# name inside a non-allowed location. Mirror of claude-files-guard.sh for
# rename/copy/symlink vectors.
#
# Closes the bypass: `Write /repo/x.tmp` (allowed) followed by `mv /repo/x.tmp /repo/CLAUDE.md`
# (would land at the forbidden name, but claude-files-guard fires on Write/Edit only).
#
# Allowed destinations (no block):
#   ~/.claude/**, ~/Documents/claude/**

INPUT=$(cat)
CMD=$(printf '%s' "$INPUT" | jq -r '.tool_input.command // empty')
[ -z "$CMD" ] && exit 0

H="$HOME"

# Is this path a Claude-specific landing site we want to forbid (outside allowed roots)?
matches_claude_file() {
  local p="$1"
  # Allow legitimate roots
  case "$p" in
    "$H"/.claude/*) return 1 ;;
    "$H"/Documents/claude/*) return 1 ;;
  esac
  # Forbidden patterns
  case "$p" in
    */CLAUDE.md) return 0 ;;
    */memory/MEMORY.md) return 0 ;;
    */memory/workflow_pending_cleanup.md) return 0 ;;
    */memory/*.md) return 0 ;;
    */.claude/*) return 0 ;;
  esac
  return 1
}

# Normalize a token
clean_tok() {
  local t="$1"
  t=$(printf '%s' "$t" | sed 's/^[`("\x27]*//; s/[;|&)`"\x27]*$//')
  case "$t" in
    "~/"*) t="$H${t#\~}" ;;
    "~") t="$H" ;;
  esac
  printf '%s' "$t"
}

# Only inspect cp/mv/ln/install commands — these are the rename/copy vectors.
case "$CMD" in
  cp\ *|mv\ *|ln\ *|install\ *|cp|mv|ln|install) ;;
  *) exit 0 ;;
esac

read -r -a TOKENS <<< "$CMD"

# Check for -t / --target-directory: every positional arg lands UNDER target dir
# with its source basename. Approximate: flag the target dir + a synthesized name.
TARGET_DIR=""
i=0
n=${#TOKENS[@]}
while [ $i -lt $n ]; do
  case "${TOKENS[$i]}" in
    -t)
      j=$((i+1))
      [ $j -lt $n ] && TARGET_DIR=$(clean_tok "${TOKENS[$j]}")
      ;;
    --target-directory=*)
      TARGET_DIR=$(clean_tok "${TOKENS[$i]#--target-directory=}")
      ;;
    -t*)
      TARGET_DIR=$(clean_tok "${TOKENS[$i]#-t}")
      ;;
  esac
  i=$((i+1))
done

CANDIDATES=()

if [ -n "$TARGET_DIR" ]; then
  # Walk non-flag, non-meta args; synthesize target as TARGET_DIR/basename(src)
  for tok in "${TOKENS[@]}"; do
    case "$tok" in
      -*|"<"|"|"|"&"|";"|"cp"|"mv"|"ln"|"install") continue ;;
    esac
    c=$(clean_tok "$tok")
    [ -z "$c" ] && continue
    [ "$c" = "$TARGET_DIR" ] && continue
    CANDIDATES+=("${TARGET_DIR%/}/$(basename "$c")")
  done
else
  # Destination is the last non-flag positional arg
  LAST=""
  for tok in "${TOKENS[@]}"; do
    case "$tok" in
      -*|"<"|"|"|"&"|";"|"cp"|"mv"|"ln"|"install") continue ;;
    esac
    LAST=$(clean_tok "$tok")
  done
  [ -n "$LAST" ] && CANDIDATES+=("$LAST")
fi

for c in "${CANDIDATES[@]}"; do
  if matches_claude_file "$c"; then
    jq -nc --arg path "$c" \
      '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":("Bash command would land a Claude-specific file at \($path) — that path is inside a repo (would pollute git, get accidentally committed, leak on push). Place Claude memory/config under ~/.claude/projects/<sanitized>/ instead, or do this rename yourself in a terminal.")}}'
    exit 0
  fi
done

exit 0
