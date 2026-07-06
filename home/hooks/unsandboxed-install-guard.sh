#!/usr/bin/env bash
# PreToolUse Bash — re-deny project-local package installs WHEN UNSANDBOXED.
#
# These install patterns are removed from settings.json deny so they can run in a
# verified sandbox (BUILD mode, where network is limited to official registries and
# the filesystem is confined). This hook restores the deny for INVESTIGATION mode
# (unsandboxed primary clones), where install-time scripts run with full host access.
#
# Scope: project-local installs only (uv add / uv pip install / uvx / pip install /
# npm install|i|add|ci / pnpm / yarn / cargo add). GLOBAL/system installs
# (cargo install, pipx, poetry, gem, brew, apt, go install, pre-commit install, …)
# remain denied in BOTH tiers via settings.json — this hook does not touch them.
source ~/.claude/hooks/stats.sh
source ~/.claude/hooks/patterns.sh
INPUT=$(cat)
CMD=$(echo "$INPUT" | jq -r '.tool_input.command // empty')
[ -z "$CMD" ] && exit 0

# BUILD mode (verified sandbox) → installs allowed.
is_sandboxed && exit 0

# INVESTIGATION mode (unsandboxed / uncertain) → deny project-local installs.
if printf '%s' "$CMD" | grep -qE "(^|[[:space:]&|;])(${CC_INSTALL_ALT})([[:space:]]|$)"; then
  log_stat "unsandboxed-install-guard" "PreToolUse" "deny" "${CMD:0:50}"
  deny_hook "Package installs are blocked in unsandboxed (investigation) sessions — install-time scripts would run with full host access. Run this inside a sandboxed worktree (BUILD mode), or install it yourself."
fi
exit 0
