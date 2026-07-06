# Global Workflow Discipline

These rules apply to ALL projects. Project-specific context lives in each project's own CLAUDE.md.

## About the User
- Piyush Satti (piyushsatti@gmail.com)
- Reviews every diff before committing — do not auto-commit
- Uses conventional commits: feat:/fix:/chore:/docs:/refactor:/test: etc.

## End-of-Task Discipline
Before declaring any task complete, ALWAYS:
1. Check if the work created follow-up needs (stale docs, TODOs, config drift, missing tests)
2. If yes — append each item to `memory/workflow_pending_cleanup.md` with today's date
3. If config files, docs, or build scripts reference files/paths that changed — flag immediately
4. When writing or updating any memory file, set `last_updated: YYYY-MM-DD` in its YAML frontmatter (new files include it from the start)

### Docs & Config Staleness
When editing files, check the project's CLAUDE.md for its staleness check list. Every project defines which files to scan for ripple effects.

## Project Bootstrap
If the SessionStart hook reports `PROJECT_BOOTSTRAP_NEEDED`, list the missing items and ask the user if they want to set them up now. For each missing piece:
- **CLAUDE.md**: Explore the project (README, structure, build system) and draft a project context file with architecture, key paths, build commands, and a staleness check list
- **Memory index + cleanup tracker**: Create `memory/MEMORY.md` and `memory/workflow_pending_cleanup.md` from templates
- **Serena**: Run `activate_project` + `onboarding` if the user wants semantic code tools

## Implementation Gate
Never write code, create files, or edit config unless I explicitly say "do it", "build it", "implement", or similar. Research, proposals, and plans are NOT permission to execute. When in doubt, present the approach and ask before touching files.

## Behavioral Rules
- **When blocked or changing approach** — STOP and present 2-3 options to the user. Never silently pivot.
- Use `git merge --no-edit` for merges
- **Never add Co-Authored-By trailers to commits**
- **Never bump a version number unless I explicitly ask** — no `plugin.json` / `package.json` / any package or changelog version change on your own initiative, even after a release-worthy change. Propose it and wait for my go-ahead.
- **Always prefer Sonnet for subagents** — dispatch Agent/Task subagents with `model: sonnet` by default; reserve Opus for the main orchestrating thread and `advisor` review. Only override to Opus when a delegated task genuinely needs it.
- **Offload heavy file work to a planned subagent** — for any task with substantial exploration or many file reads/writes/rewrites: plan the work in the main thread first, then dispatch a Sonnet subagent to execute it and return a concise report. Raw file contents and edit churn stay in the subagent, keeping the main thread's context lean. (Extends the Sonnet-subagent rule above.) **This rule applies to the MAIN orchestrating thread only — if you ARE a subagent, do the delegated work yourself; NEVER re-delegate to another subagent.** (Added 2026-07-02 after a 4-deep delegation chain: each Sonnet subagent read this rule and re-dispatched a near-identical prompt instead of executing.)

## Working & communication discipline
- **Diagnose before fixing** — verify the assumption with evidence (diagnostic / log / repro) before writing fix code; don't present conditional Scenario-A/B/C fixes.
- **Proactive data quality** — surface and prompt fixes for data-quality issues (duplicate / stale / unnamed) with severity; never silently work around them.
- **Memory save gate** — before saving a memory: (1) is it worth documenting? (2) will it recur? Propose the save with that evaluation.
- **Incremental walkthroughs** — interactive / multi-step procedures: one step at a time, then wait; no walls of steps.
- **Separate conflating topics** — when two related-but-distinct topics tangle, stop and ask to split them; don't reason about both at once.
- **Plan blast-radius** — every plan file includes a blast-radius section (artifacts × scope, what's untouched, reversibility).
- **Long output to a file** — write long runbooks / reference output to a markdown file, not just chat.

## Worktree-First Workflow
All non-trivial work happens in a git worktree, never the main checkout; the primary clone stays clean on the default branch. Layout: primary `~/Documents/projects/<repo>/`, worktrees nested in-repo at `<repo>/.worktrees/<branch>/` (gitignored via `~/.gitignore_global`), shared content `~/Documents/projects/artifacts/<repo>/`.

- **Use the `/worktree` skill** to create/validate/bootstrap — it does the worktree create + brain/memory/`.claude` wiring + artifacts symlinks + per-stack env, and `/worktree check` validates or repairs one. The manual fallback recipe, gotchas (real-dir `.claude`, per-worktree `.venv`, `.gitignored` exclude, new-branch-off-remote tracking), and editor integration live in the skill's `references/worktree-recipe.md`.
- **Branch naming**: `<TICKET-ID>[-<short-slug>]` or `<descriptive-kebab>`. Slashes are fine (e.g. `hotfix/x`) — artifacts symlinks are absolute (`ln -sfn`; survives `git worktree move` on archive/revive, portable to BSD/macOS ln).
- **Always confirm the base branch with the user before creating a worktree.** Emit commands directly, no shell wrapper.

## Test File Layout
Tests live in the top-level `tests/` directory, mirroring the source path of what they test: source `path/to/foo` → `tests/path/to/test_foo`. Never colocate tests beside the source under a nested `tests/` subdir. Project-specific conventions (framework, exact naming) live in that project's CLAUDE.md.

## Bash Safety

- **Never use bare `cd` in Bash tool calls** — persists session CWD silently. Use absolute paths directly, or subshell: `(cd /abs/path && cmd)`.
- On multi-host setups where the same `/mnt/` path maps to different data per host, resolve a mount to its (host, export) before any bulk/recursive write — path alone is not a safe identifier. Host-specific mount policy belongs in machine-local config, never this generic file.

## Memory routing (where does this go?)

**The test:** does it fire PROACTIVELY every time, or get RECALLED only when relevant?

- **Proactive → CLAUDE.md** (generic) / `CLAUDE.local.md` (specific). Rules, gates, standing prefs that apply automatically — INCLUDING behavioral prefs like "run ruff before commit", "prefer tables", "uv pins .python-version". These are RULES, not facts. **Never put an always-apply rule in memory.**
- **Recalled → Claude memory** (`memory/*.md`). Facts / references / past context you look UP when relevant.
- **Code-coupled → serena.** Symbols, architecture, code decisions.

generic = portable, you-owned; specific = bound, agent-owned, gitignored. Location = scope. NEVER commit agent files.

- **Memory frontmatter (required):** every memory file carries `created`, `type`, `scope`, `genericity`, `last_updated`, `schema_version`. `scope` is a derived `{depth, role}` mapping (the home key = `{depth: 0, role: home}`), not the old `universal|machine|…` enum; `schema_version` is currently `2`. `genericity` is the export fence — unsure → `specific`. Rules (proactive / always-apply) never go in memory; they belong here as rules. Filename = `<created>-<type>_<slug>.md` (the created date prefixed).

## Coding & output preferences
- Run `ruff` (format + check) before committing Python.
- uv projects: pin the interpreter in `.python-version`.
- Prefer markdown tables over bullet lists for options, tradeoffs, and comparisons.
- **Pasteable command blocks = pure commands only — NO inline `#` comments, NO backticks inside the block.** This TUI line-wraps multi-line pastes; a wrapped inline comment (or a backticked word) lands on its own line and executes as a stray command. Put all explanation in prose before/after the block; if a step needs a note, use a separate prose line, not an inline comment.

## Tool Routing

### context7 — external library/API docs (use BEFORE answering from memory)
Before answering ANY question about an external library, framework, SDK, API, CLI
tool, or cloud service — even one you think you know — first call context7:
`resolve-library-id` then `query-docs`. Do NOT answer library/API questions from
training memory; it may be stale or version-wrong. Applies to: API signatures,
config options, version/migration questions, library-specific debugging,
setup/CLI usage. Skip context7 ONLY for: the user's own code/business logic,
general programming concepts, or when the user explicitly says answer from memory.

### scrutineer — rigor audit of a research notebook / analysis doc
Dispatch the `scrutineer` subagent (user-level, `~/.claude/agents/scrutineer.md`) when asked to
audit / sanity-check / verify the internal consistency or evidential rigor of a research notebook,
report, or findings doc — or before treating one as trustworthy. It builds a claim ledger with
evidence tiers (T0 proven-live → T3 assumed), checks macro order + per-heading coherence, and demands
a discriminating data-backed proof for every doubtful claim. Report-only (never edits the target).
NOT for code-correctness of a diff (use `/code-review`) nor for building/fixing (dispatch a builder).
