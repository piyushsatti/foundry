#!/usr/bin/env bash
# SessionStart — detect missing project workflow infrastructure and prompt setup
source ~/.claude/hooks/stats.sh
CWD=$(pwd)

[ -e "$CWD/.git" ] || exit 0   # -e not -d: in a worktree .git is a FILE (gitdir pointer), not a dir

PROJECT_DIR=$(project_dir "$CWD")

MISSING=""
NL=$'\n'

[ -f "$PROJECT_DIR/CLAUDE.md" ]                          || MISSING="${MISSING}- Project-scoped CLAUDE.md (project context, architecture, staleness check list)${NL}"
[ -f "$PROJECT_DIR/memory/MEMORY.md" ]                   || MISSING="${MISSING}- Memory index (memory/MEMORY.md)${NL}"
[ -f "$PROJECT_DIR/memory/workflow_pending_cleanup.md" ] || MISSING="${MISSING}- Pending cleanup tracker (memory/workflow_pending_cleanup.md)${NL}"
# Serena stores project config out-of-tree at ~/.serena/projects/<name>/, NOT in the repo.
# Resolve the project name from the MAIN clone's basename (first `git worktree list` entry),
# so this also reports correctly from inside a linked worktree. If MAIN can't be resolved
# (git error / stale gitdir pointer), SKIP the check rather than guess a wrong path from
# $CWD — in a worktree $CWD's basename is the branch, which would false-flag "Serena missing".
SERENA_MAIN=$(git -C "$CWD" worktree list --porcelain 2>/dev/null | awk '/^worktree /{print $2; exit}')
if [ -n "$SERENA_MAIN" ]; then
  SERENA_NAME=$(basename "$SERENA_MAIN")
  [ -f "$HOME/.serena/projects/$SERENA_NAME/project.yml" ] || MISSING="${MISSING}- Serena project config (~/.serena/projects/$SERENA_NAME/project.yml) — recommended for semantic code navigation${NL}"
fi

if [ -n "$MISSING" ]; then
  MISSING_COUNT=$(echo "$MISSING" | grep -c '^-')
  log_stat "project-bootstrap-check" "SessionStart" "missing" "$MISSING_COUNT"
  MSG="PROJECT_BOOTSTRAP_NEEDED: This project is missing workflow infrastructure:
${MISSING}Ask the user if they'd like to set these up before starting work. Offer to scaffold the missing pieces."
  jq -n --arg ctx "$MSG" \
    '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":$ctx}}'
else
  log_stat "project-bootstrap-check" "SessionStart" "ok"
fi
