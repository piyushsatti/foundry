#!/usr/bin/env bash
# Shared helpers for ~/.claude/hooks/*.sh — sourced, not executed.
#
# Provides:
#   deny_hook <reason>           → emits PreToolUse deny JSON to stdout (caller exits)
#   log_stat <hook> <event> <result> [ctx]  → appends one JSONL line to ~/.claude/hook-stats.jsonl
#   project_dir <path>           → maps /home/piyush/foo → /home/piyush/.claude/projects/-home-piyush-foo
#
# If this file is missing, every hook that sources it will print stderr noise
# and silently allow operations the hook was supposed to deny. Do NOT delete.

deny_hook() {
  local reason="$1"
  jq -n --arg reason "$reason" \
    '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":$reason}}'
}

log_stat() {
  local hook="$1" event="$2" result="$3" ctx="${4:-}"
  local ts
  ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  jq -nc \
    --arg ts "$ts" \
    --arg hook "$hook" \
    --arg event "$event" \
    --arg result "$result" \
    --arg ctx "$ctx" \
    '{ts:$ts, hook:$hook, event:$event, result:$result, ctx:$ctx}' \
    >> "$HOME/.claude/hook-stats.jsonl" 2>/dev/null
}

project_dir() {
  local path="$1"
  printf '%s/.claude/projects/%s\n' "$HOME" "$(printf '%s' "$path" | sed 's|[/.]|-|g')"
}

# is_sandboxed → return 0 (true) ONLY if the effective sandbox.enabled for this
# session is positively true; return 1 otherwise. FAIL-CLOSED: missing jq, parse
# errors, absent keys, or any uncertainty all yield 1 (treat as unsandboxed = strict).
#
# Detection mirrors the harness's own resolution: walk up from $CLAUDE_PROJECT_DIR
# (fallback $PWD) to the nearest .claude/settings.local.json, then fall back to the
# global local file, then global settings.json. The first file that sets
# sandbox.enabled wins (scalar override semantics). Hooks run OUTSIDE the sandbox,
# so we cannot probe Seccomp/namespaces — the settings files are the ground truth.
is_sandboxed() {
  command -v jq >/dev/null 2>&1 || return 1
  local dir f val
  dir="${CLAUDE_PROJECT_DIR:-$PWD}"
  while :; do
    f="$dir/.claude/settings.local.json"
    if [ -f "$f" ]; then
      val=$(jq -r '.sandbox.enabled' "$f" 2>/dev/null) || return 1
      case "$val" in
        true)  return 0 ;;
        false) return 1 ;;
      esac
    fi
    [ "$dir" = "/" ] && break
    [ "$dir" = "$HOME" ] && break
    dir=$(dirname "$dir")
  done
  f="$HOME/.claude/settings.local.json"
  if [ -f "$f" ]; then
    val=$(jq -r '.sandbox.enabled' "$f" 2>/dev/null)
    case "$val" in true) return 0 ;; false) return 1 ;; esac
  fi
  f="$HOME/.claude/settings.json"
  if [ -f "$f" ]; then
    val=$(jq -r '.sandbox.enabled' "$f" 2>/dev/null)
    case "$val" in true) return 0 ;; esac
  fi
  return 1
}
