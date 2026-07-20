# Session Hooks

**Session hooks run at SessionStart to inject the context a fresh session needs — durable memory, active scope, pending work, and project state — so a new or resumed session doesn't start blank.**

> **Status:** draft — authored, mostly unwired (roadmap, Issue #3).

## The problem

A new or resumed session has no memory of what came before. Without re-injection it forgets durable notes, doesn't know which scope or epic it's in, and misses pending cleanup — so it re-asks, re-derives, or drifts off task. Session hooks rehydrate that context at the start boundary.

## How it works

Each fires at SessionStart, reads local state, and emits `additionalContext`:

- **`memory-durability`** — re-injects the durable memory index (a nearest-directory-first `MEMORY.md` walk up to `$HOME`). Also the intended compaction rehydrator — see [compaction hooks](compaction-hooks).
- **`scope-context`** — reads `session-scopes.json`, lists the scopes active for the current directory and their primers, and asks which one you're in.
- **`project-bootstrap-check`** — detects missing workflow infrastructure (project `CLAUDE.md`, `MEMORY.md`, cleanup tracker, Serena) and offers to scaffold it.
- **`pending-cleanup-check`** — surfaces open `- [ ]` items from the workflow cleanup tracker.
- **`todo-detector`** — greps the repo for TODO/FIXME/HACK and injects up to 20.

## Why SessionStart, not per-turn

Context that must hold for the whole session — memory, scope — belongs at the boundary, injected once, not recomputed every turn. SessionStart is also the reliable rehydration point after compaction, which is why the memory hook lives here.

## Open questions

- `scope-context` emits a bare `additionalContext` payload rather than the `hookSpecificOutput` wrapper the other session hooks use — a schema inconsistency that may not inject on some Claude Code versions.

## See also

- [Lifecycle](../lifecycle) · [Compaction hooks](compaction-hooks) · [meditate](../../../plugins/meditate/overview)
