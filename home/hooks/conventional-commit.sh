#!/usr/bin/env bash
# PreToolUse Bash — enforce conventional commit format.
#
# Parses the commit message from `git commit` and denies non-conventional messages.
# Handles: -m "msg", -m heredoc ($(cat <<EOF ...)), -F <file>/--file=<file>,
# bare --amend (reuses prior, already-validated message), and --allow-empty-message.
source ~/.claude/hooks/stats.sh
INPUT=$(cat)
CMD=$(echo "$INPUT" | jq -r '.tool_input.command // empty')
printf '%s' "$CMD" | grep -qE '(^|[[:space:]])git[[:space:]]+commit($|[[:space:]])' || exit 0

# Explicit empty message is allowed if the user asked for it.
if printf '%s' "$CMD" | grep -qE '(^|[[:space:]])--allow-empty-message($|[[:space:]])'; then
  log_stat "conventional-commit" "PreToolUse" "pass" "allow-empty-message"
  exit 0
fi

# Tokenize for flag scanning (naive split on whitespace — matches other hooks).
read -r -a TOK <<< "$CMD"
n=${#TOK[@]}

# Does the command supply a (new) message via any message-bearing flag?
has_msg_flag=0
FFILE=""
for ((i=0; i<n; i++)); do
  case "${TOK[i]}" in
    -m|--message|-c|--reedit-message|-C|--reuse-message) has_msg_flag=1 ;;
    -m*|--message=*) has_msg_flag=1 ;;
    -F|--file)       has_msg_flag=1; j=$((i+1)); [ $j -lt $n ] && FFILE="${TOK[j]}" ;;
    -F*)             has_msg_flag=1; FFILE="${TOK[i]#-F}" ;;
    --file=*)        has_msg_flag=1; FFILE="${TOK[i]#--file=}" ;;
  esac
done

# --amend with no new message reuses the previous (already-validated) message → allow.
if printf '%s' "$CMD" | grep -qE '(^|[[:space:]])--amend($|[[:space:]])' && [ "$has_msg_flag" -eq 0 ]; then
  log_stat "conventional-commit" "PreToolUse" "pass" "amend-reuse"
  exit 0
fi

MSG=""

# -F / --file: validate the file's first non-empty line.
if [ -n "$FFILE" ]; then
  case "$FFILE" in "~/"*) FFILE="$HOME${FFILE#\~}" ;; esac
  FFILE=$(printf '%s' "$FFILE" | sed 's/^["'\'']//; s/["'\'']$//')
  if [ -r "$FFILE" ]; then
    MSG=$(grep -vE '^[[:space:]]*(#|$)' "$FFILE" 2>/dev/null | head -1 | sed 's/^[[:space:]]*//')
  fi
fi

# -m "msg" (simple quoted form; preserve multi-line content with printf).
if [ -z "$MSG" ]; then
  MSG=$(printf '%s' "$CMD" | sed -nE "s/.*-m[[:space:]]*[\"']([^\"']*)[\"'].*/\1/p" | head -1)
  if printf '%s' "$MSG" | grep -q '^\$('; then MSG=""; fi
fi

# HEREDOC: first content line between the << marker and the closing EOF.
if [ -z "$MSG" ]; then
  MSG=$(printf '%s\n' "$CMD" | sed -n '/<<.*EOF/,/EOF/{/EOF/d;p;}' | grep -vE '^[[:space:]]*$' | head -1 | sed 's/^[[:space:]]*//')
fi

if [ -z "$MSG" ]; then
  log_stat "conventional-commit" "PreToolUse" "deny" "unparseable"
  deny_hook 'Could not parse commit message. Use: git commit -m "type: description" (conventional commits required).'
elif ! printf '%s' "$MSG" | grep -qE '^(feat|fix|chore|docs|refactor|test|style|perf|ci|build|revert)(\(.+\))?!?:'; then
  log_stat "conventional-commit" "PreToolUse" "deny" "${MSG:0:40}"
  deny_hook "Commit message must follow conventional commits: feat:/fix:/chore:/docs:/refactor:/test:/style:/perf:/ci:/build:/revert:"
else
  log_stat "conventional-commit" "PreToolUse" "pass" "${MSG:0:40}"
fi
