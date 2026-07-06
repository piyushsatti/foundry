#!/usr/bin/env bash
# plan-review-nudge.sh — PreToolUse hook keyed on ExitPlanMode (EXPERIMENTAL,
# first plugin hook in this repo; autoloading via hooks.json is unverified —
# see plugins/crucible/README.md).
#
# Heuristic, NEVER-BLOCKING nudge: if the plan being finalized looks
# high-stakes, remind the user to consider running red-vs-blue before
# proceeding. Always allows the tool call (exit 0 in every path) and emits at
# most one nudge. Must not crash on a missing/malformed/oddly-shaped payload —
# on any doubt, stay silent and allow.
#
# Threshold is tunable via CRUCIBLE_PLAN_NUDGE_THRESHOLD (chars); default is a
# rough "this plan is long enough to be non-trivial" heuristic, not tuned data.

set -u

THRESHOLD="${CRUCIBLE_PLAN_NUDGE_THRESHOLD:-1200}"
KEYWORDS='migration|auth|security|launch|delete|production|payment|schema'

# Read the hook payload from stdin. A missing/empty/unreadable payload is not
# an error here — just nothing to nudge about.
input="$(cat 2>/dev/null)" || exit 0
[ -z "${input:-}" ] && exit 0

# jq missing, payload not valid JSON, tool_input not an object, or plan absent
# → jq exits non-zero / prints nothing; captured with stderr suppressed, so a
# malformed payload degrades to an empty $plan and we exit quietly below.
plan="$(printf '%s' "$input" | jq -r '.tool_input.plan // empty' 2>/dev/null)"
[ -z "${plan:-}" ] && exit 0

high_stakes=""

# Stage 1: length heuristic (a long plan is worth a second look regardless of
# keywords). ${#plan} is safe even if $plan contains odd bytes.
if [ "${#plan}" -gt "$THRESHOLD" ]; then
  high_stakes=1
fi

# Stage 2: keyword heuristic, case-insensitive.
if printf '%s' "$plan" | grep -qiE "$KEYWORDS" 2>/dev/null; then
  high_stakes=1
fi

[ -z "$high_stakes" ] && exit 0

msg='This plan looks high-stakes (long, or touches migration/auth/security/launch/delete/production/payment/schema). Before finalizing, consider running the crucible red-vs-blue skill to stress-test it — or say no and proceed as-is.'

jq -n --arg ctx "$msg" \
  '{"hookSpecificOutput":{"hookEventName":"PreToolUse","additionalContext":$ctx}}' 2>/dev/null

exit 0
