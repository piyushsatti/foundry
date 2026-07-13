# devtools

Dev-environment tooling bundle.

## Structure

| Skill | Job |
|-------|-----|
| `worktree` | Worktree-native lifecycle for any repo — add/check/archive/revive/reap, with memory + serena wiring and per-stack env setup |

## Why

Workspace tooling is its own domain — it fits neither review (crucible), spec (manifold), orchestration (plan-orchestrator), nor memory (meditate). One bundle, room to grow with future dev-workflow skills.

## Operate

Install via the foundry marketplace. The skill triggers on `/worktree`, "new worktree", "reap a worktree", etc. Helper functions live in `skills/worktree/helpers.sh`; the manual recipe and gotchas in `skills/worktree/references/worktree-recipe.md`.
