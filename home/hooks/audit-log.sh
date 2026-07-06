#!/usr/bin/env bash
# Audit log — JSONL trail of Bash / Write / Edit / MultiEdit events.
#
# Wired to:
#   PreToolUse  Bash | Write | Edit | MultiEdit
#   PostToolUse Bash | Write | Edit | MultiEdit
#
# Output: ~/.claude/audit.jsonl (forever retention).
# Old ~/.claude/audit.log (plain text) is frozen as historical record — not touched.
#
# Schema:
#   PreToolUse  Bash     → {ts, event, tool, session_id, cwd, command}
#   PostToolUse Bash     → {ts, event, tool, session_id, cwd, command, exit_code, interrupted}
#   PreToolUse  W/E/ME   → {ts, event, tool, session_id, cwd, file_path}
#   PostToolUse W/E/ME   → {ts, event, tool, session_id, cwd, file_path, sha256, bytes}
#
# Secret redaction: known kv patterns (password=, token=, secret=, api_key=, apikey=, auth=)
# in Bash command strings are redacted before logging.
# sha256: skipped (logged as "skipped-too-large") for files >10MB.

set -u

LOG="$HOME/.claude/audit.jsonl"
MAX_HASH_BYTES=$((10 * 1024 * 1024))

INPUT=$(cat)
TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)
CWD=$(pwd)

TOOL=$(printf '%s' "$INPUT" | jq -r '.tool_name // empty')
SESSION_ID=$(printf '%s' "$INPUT" | jq -r '.session_id // ""')

if printf '%s' "$INPUT" | jq -e 'has("tool_response")' >/dev/null 2>&1; then
  EVENT="PostToolUse"
else
  EVENT="PreToolUse"
fi

case "$TOOL" in
  Bash)
    CMD=$(printf '%s' "$INPUT" | jq -r '.tool_input.command // empty')
    # Redact common credential shapes before logging. Belt-and-braces; the
    # bash-cred-read-guard.sh hook already denies many of these patterns, but
    # logs from denied commands still hit this file.
    CMD=$(printf '%s' "$CMD" | sed -E '
      s/(password|passwd|token|secret|api_key|apikey|auth|access_key|access[-_]?token|refresh_token|client_secret|bearer)=[^ ]*/\1=REDACTED/gi
      s/--(password|token|secret|api-key|api_key|apikey)[= ]+[^ ]+/--\1 REDACTED/gi
      s/-p[ ]+[^ -][^ ]*/-p REDACTED/g
      s/(Authorization|X-API-Key|X-Auth-Token|X-Access-Token)[ ]*:[ ]*[^"\x27 ]+[^"\x27]*/\1: REDACTED/gi
      s/(Bearer|Basic|Token)[ ]+[A-Za-z0-9._\/+\-]+={0,2}/\1 REDACTED/g
      s/AKIA[0-9A-Z]{16}/AKIA_REDACTED/g
      s/ASIA[0-9A-Z]{16}/ASIA_REDACTED/g
      s/ghp_[A-Za-z0-9]{20,}/ghp_REDACTED/g
      s/gho_[A-Za-z0-9]{20,}/gho_REDACTED/g
      s/ghs_[A-Za-z0-9]{20,}/ghs_REDACTED/g
      s/xox[bpars]-[A-Za-z0-9-]{10,}/xoxX-REDACTED/g
      s/sk-[A-Za-z0-9]{20,}/sk-REDACTED/g
    ')
    if [ "$EVENT" = "PreToolUse" ]; then
      jq -nc \
        --arg ts "$TS" --arg event "$EVENT" --arg tool "$TOOL" \
        --arg session_id "$SESSION_ID" --arg cwd "$CWD" --arg command "$CMD" \
        '{ts:$ts, event:$event, tool:$tool, session_id:$session_id, cwd:$cwd, command:$command}' \
        >> "$LOG"
    else
      # Claude Code 2.1.133 tool_response for Bash lacks exit_code.
      # Available: stdout, stderr, interrupted, isImage, noOutputExpected.
      # We log lengths (not content — could be huge/sensitive) plus the booleans.
      printf '%s' "$INPUT" | jq -c \
        --arg ts "$TS" --arg event "$EVENT" --arg tool "$TOOL" \
        --arg session_id "$SESSION_ID" --arg cwd "$CWD" --arg command "$CMD" \
        '{
           ts:$ts, event:$event, tool:$tool, session_id:$session_id, cwd:$cwd,
           command:$command,
           interrupted: (.tool_response.interrupted // false),
           stdout_bytes: ((.tool_response.stdout // "") | length),
           stderr_bytes: ((.tool_response.stderr // "") | length),
           had_stderr: (((.tool_response.stderr // "") | length) > 0)
         }' >> "$LOG"
    fi
    ;;
  Write|Edit|MultiEdit)
    FILE_PATH=$(printf '%s' "$INPUT" | jq -r '.tool_input.file_path // empty')
    if [ "$EVENT" = "PreToolUse" ]; then
      jq -nc \
        --arg ts "$TS" --arg event "$EVENT" --arg tool "$TOOL" \
        --arg session_id "$SESSION_ID" --arg cwd "$CWD" --arg file_path "$FILE_PATH" \
        '{ts:$ts, event:$event, tool:$tool, session_id:$session_id, cwd:$cwd, file_path:$file_path}' \
        >> "$LOG"
    else
      SHA256="missing"
      BYTES_ARG="null"
      if [ -n "$FILE_PATH" ] && [ -f "$FILE_PATH" ]; then
        BYTES=$(stat -c%s "$FILE_PATH" 2>/dev/null)
        if [ -n "$BYTES" ]; then
          BYTES_ARG="$BYTES"
          if [ "$BYTES" -le "$MAX_HASH_BYTES" ]; then
            SHA256=$(sha256sum "$FILE_PATH" 2>/dev/null | awk '{print $1}')
          else
            SHA256="skipped-too-large"
          fi
        fi
      fi
      jq -nc \
        --arg ts "$TS" --arg event "$EVENT" --arg tool "$TOOL" \
        --arg session_id "$SESSION_ID" --arg cwd "$CWD" --arg file_path "$FILE_PATH" \
        --arg sha256 "$SHA256" --argjson bytes "$BYTES_ARG" \
        '{ts:$ts, event:$event, tool:$tool, session_id:$session_id, cwd:$cwd, file_path:$file_path, sha256:$sha256, bytes:$bytes}' \
        >> "$LOG"
    fi
    ;;
  *)
    exit 0
    ;;
esac

if [ $(( RANDOM % 50 )) -eq 0 ]; then
  chmod 600 "$LOG" 2>/dev/null
fi

exit 0
