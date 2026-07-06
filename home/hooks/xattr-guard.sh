#!/usr/bin/env bash
# PreToolUse Bash (sync) — block exec/copy/redirect-out of Claude-tagged files.
#
# Companion to xattr-tagger.sh. Reads the planned Bash command and denies it
# if any referenced file path carries the user.claude.authored xattr AND the
# command is in a "danger pattern":
#
#   1. Interpreter exec:  bash <path>, python <path>, etc.
#   2. cp without preserve flag (-p/-a/--preserve)
#   3. Output redirect: <cmd> <src> > <dst>  or  >> <dst>
#
# To bless a tagged file (user only, must be in a terminal):
#   ~/.claude/bin/bless <path>
#
# Known limitations:
#   - Naive tokenization (read -a) doesn't fully handle quoted paths with spaces
#   - Exotic laundering (rsync, dd, tee, install) not covered by design
#   - Only checks paths that look path-like (contain / or have an extension)

set -u

source ~/.claude/hooks/stats.sh

INPUT=$(cat)
CMD=$(printf '%s' "$INPUT" | jq -r '.tool_input.command // empty')
[ -z "$CMD" ] && exit 0

# Is a path inside the current sandboxed project tree? Used to waive the *exec*
# gate in BUILD mode: a verifiably-sandboxed worktree confines what the script can
# do, and the tag is left in place so the gate re-fires if the file is ever run
# unsandboxed (primary clone / CI / human). Fail-closed: no project dir → not under.
proj="${CLAUDE_PROJECT_DIR:-}"
is_under_project() {
  [ -n "$proj" ] || return 1
  local rp rproj
  rp=$(realpath -m "$1" 2>/dev/null) || return 1
  rproj=$(realpath -m "$proj" 2>/dev/null) || return 1
  case "$rp/" in "$rproj"/*) return 0 ;; esac
  return 1
}

INT='(bash|s?h|zsh|ksh|dash|python3?|node|ruby|perl|pwsh)'

DANGER_TYPE=""

# Pattern 1: interpreter <path>  (exempt shell parse-only `-n`, which does NOT execute the file)
if printf '%s' "$CMD" | grep -qE "(^|[^[:alnum:]_])(bash|s?h|zsh|ksh|dash)([[:space:]]+--[a-z-]+)*[[:space:]]+-[a-zA-Z]*n([[:space:]]|$)"; then
  :  # syntax-check only (e.g. `bash -n foo.sh`) — allow it
elif printf '%s' "$CMD" | grep -qE "(^|[^[:alnum:]_/.-])${INT}[[:space:]]+(-[^[:space:]]+[[:space:]]+)*[^[:space:]-]"; then
  DANGER_TYPE="exec"
fi

# Pattern 2: cp without an xattr-preserving flag.
# Only `cp -a` (archive, includes xattrs) and `cp --preserve=xattr|all|...,xattr,...`
# actually preserve xattrs. `cp -p` does NOT (it preserves mode/owner/timestamps).
if [ -z "$DANGER_TYPE" ] && printf '%s' "$CMD" | grep -qE "(^|[^[:alnum:]_/.-])cp[[:space:]]"; then
  if ! printf '%s' "$CMD" | grep -qE "(^|[^[:alnum:]_/.-])cp[[:space:]]+([^[:space:]]+[[:space:]]+)*(-[a-zA-Z]*a[a-zA-Z]*|--archive|--preserve=([a-z]+,)*(all|xattr))"; then
    DANGER_TYPE="cp-without-preserve"
  fi
fi

# Pattern 3: output redirect — narrowed to script-extension targets or
# scratch / PATH-shadow destinations where laundered content could be executed.
# Broad rule ("any redirect") had too many false positives (e.g. `cat doc.md > out.txt`).
if [ -z "$DANGER_TYPE" ] && printf '%s' "$CMD" | grep -qE "[[:space:]]>>?[[:space:]][^[:space:]]*(\.(sh|py|js|rb|pl|pm|lua|tcl|fish|zsh|bash|ksh|mjs|cjs|ts)([[:space:]]|;|&|\||\)|$)|/tmp/|/var/tmp/|/dev/shm/|/\.local/bin/|/bin/[^/[:space:]]+([[:space:]]|;|&|\||\)|$))"; then
  DANGER_TYPE="redirect-to-exec-target"
fi

# No danger pattern matched — exit clean
[ -z "$DANGER_TYPE" ] && exit 0

# Tokenize and check each candidate path for the xattr tag
read -r -a TOKENS <<< "$CMD"

for tok in "${TOKENS[@]}"; do
  # Strip leading/trailing shell metacharacters
  clean=$(printf '%s' "$tok" | sed 's/^[`("\x27]*//; s/[;|&)`"\x27]*$//')
  [ -z "$clean" ] && continue
  # Skip flags
  [[ "$clean" == -* ]] && continue
  # Only consider path-like tokens
  case "$clean" in
    /*|./*|../*|*/*) ;;
    *.*) ;;
    *) continue ;;
  esac
  # Tilde expansion (manual — read -a doesn't expand)
  case "$clean" in
    "~/"*) clean="$HOME${clean#\~}" ;;
    "~") clean="$HOME" ;;
  esac
  # Check tag — only if file exists
  if [ -e "$clean" ] && getfattr -n user.claude.authored "$clean" >/dev/null 2>&1; then
    # BUILD mode: waive the exec gate for in-tree scripts in a verified sandbox.
    # Tag is left intact; cp-without-preserve / redirect-to-exec-target are NOT waived.
    if [ "$DANGER_TYPE" = "exec" ] && is_sandboxed && is_under_project "$clean"; then
      continue
    fi
    jq -nc --arg path "$clean" --arg type "$DANGER_TYPE" \
      '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":("Path \($path) is tagged as Claude-authored (operation=\($type)). Review the file, then bless it manually in your terminal: ~/.claude/bin/bless \($path)")}}'
    exit 0
  fi
done

exit 0
