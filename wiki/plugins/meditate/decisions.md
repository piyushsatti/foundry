# Decisions & Findings

**The empirical findings and locked decisions that meditate's design rests on** — verified at Claude Code v2.1.195; do not re-derive.

> **Status:** stable

## Verified environment findings

| Finding | Detail |
|---------|--------|
| **Memory is cwd-path-keyed, not git-repo-keyed** | Key = `sed 's|[/.]|-|g'` of the absolute cwd (underscore preserved). Subdirs generate their own isolated, empty key — contradicting the official docs. Proven live. |
| **SessionStart-on-compact = the durability primitive** | SessionStart hooks re-fire on `source:compact` (proven 8/8 across an 11-compaction transcript). The native MEMORY.md index does *not* survive compaction. This is the load-bearing durability mechanism. |
| **PostCompact cannot inject context** | It supports only `systemMessage`, not `additionalContext`. So durability rests entirely on SessionStart with `source=compact`; PostCompact is no backup channel. |
| **Hook output cap = 10,000 chars per hook** | Overflow is archived to a file and replaced with a path + preview (graceful, no data loss). Multiple SessionStart hooks concatenate their `additionalContext`, each capped individually. |
| **Worktree memory sharing is a symlink** | The worktree key's `memory/` dir is symlinked to the repo-root key's (same inode), created by the `/worktree` skill — not native behavior. |

## Locked decisions

| Decision | Substance |
|----------|-----------|
| **Native markdown + curator** | Substrate is native markdown files, not an external store (MemPalace etc. rejected). Two stores: Claude memory + serena; `.remember` dropped. |
| **Scope = the folder tree** | `scope` is a derived `{depth, role}` mapping — machine-independent, not an absolute path or fixed `universal\|machine` enum. `schema_version: 2` required alongside. |
| **Genericity = the export fence** | Rulebook = `.md` generic / `.local` specific; memory = a `genericity` tag. Governs what is git/export-safe, *not* what a single-machine session injects. |
| **Curator = sole promotion authority** | A read-only Opus agent proposes; work-sessions only flag candidates; a human gates every promotion. |
| **Archive-not-destroy** | drop/retire cold-archive (recoverable) + tombstone; no in-session delete. Archive at `~/.claude/backups/memory-archive/`. |
| **No agent file in git** | CLAUDE.md / memory / serena / .remember never committed; agent artifacts stay gitignored or outside the repo. |
| **Horizontal lexicon locked** | `split` / `combine` / `link` / `amend` for within-layer restructuring. `demote-rule` reserved for the store axis; the scope move is `narrow-rule` (reserved, unbuilt). |
| **preserve-before-destroy** | Archive copies of ALL to-be-mutated files precede any write; no rollback exists (the agent can't delete), so pre-flight is the only safety. `merge` archives the destination's pre-image too. |

## Open items

- **OI-1** — overflow → compression revisit if a large project key regularly exceeds the 10k cap (P1).
- **OI-5** — doc-sprawl cleanup: consolidate the ~19 `mem-arch-*` / `meditate-*` docs eventually (low).

## See also

- [Execution contract](execution-contract) — the applier built on these findings.
- [Overview](overview) — the pipeline these decisions shaped.
