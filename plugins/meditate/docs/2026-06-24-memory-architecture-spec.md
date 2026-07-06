> **Vendored into the meditate plugin 2026-07-05** from
> `pslap:~/Documents/personal/notes/infrastructure/2026-06-24-memory-architecture-spec.md`.
> This copy is canonical from now on; the pslap original is historical. Plugin prose
> (`agents/curator.md`, `skills/*`) still cites the old path — repointing is a pending repair item.

---
title: "Memory & Instruction Architecture — Specification + Decision Appendix"
date: 2026-06-24
status: SPEC (confirmed parts) + APPENDIX (reasoning) — open cells flagged as TBD
related:
  - 2026-06-22-tool-integration-architecture-plan.md
  - remember-plugin-analysis-and-decision.md
  - memory: project_memory_architecture_design
  - memory: feedback_no_agent_files_in_git
  - memory: reference_serena_worktree_projects
---

# Memory & Instruction Architecture

How the agent's knowledge is organized across scopes, what file lives where, how it loads, who owns it, and what stays out of git. **Part I** is the spec (the confirmed "how it will be"). **Part II** is the appendix (every decision + alternatives + why). **Part III** is the conflict check.

Convention in this doc: **generic** = portable/company-safe (left of the export fence); **specific** = bound/sensitive (right of the fence, gitignored or machine-local).

---

# Part I — Specification

## 1. Problem this solves

Three pains drove the design:
1. **Write-time mis-routing / cross-contamination** — facts saved to the wrong tier (a global pref lands in a project store, or a project quirk leaks global), degrading other work.
2. **Recompute** — derived decisions (the *why* behind a pattern) have no home, so they're re-derived from code each time.
3. **No ownership methodology, no file discipline, not portable** — `notes` / memory / CLAUDE.md / serena with no contract, and no clean way to carry the setup to a new machine or company.

## 2. The model — two axes

- **Scope tier** (applicability; lifecycle is implied by scope):
  `Universal ⊃ Machine ⊃ Workspace ⊃ Project ⊃ Work-unit`
- **Genericity** (portability + confidentiality): every tier (except Work-unit) splits into a **generic base** + a **specific overlay**. The **generic|specific seam is a vertical export fence** running through *every* tier — not a horizontal line below Universal.
- **Scope assignment** (clarified 2026-06-25): `scope` = breadth of applicability. A `generic` item that is OS-independent (a tool/method fact) sits at **Universal**; a `generic` item bound to a machine class (e.g. an Ubuntu setup recipe — portable to a like box, not a Mac) sits at **Machine**. Genericity captures *portability*; scope captures *reach*.

**Overlay primitive** (docker-compose `-f` style): a session's effective context = generic bases + specific overlays, stacked by scope. **Company-switch = detach the specific overlays, keep the generic bases.** This is the portability mechanism.

## 3. Stores and their roles

Two stores only — **claude** and **serena**. (`.remember` dropped — see `remember-plugin-analysis-and-decision.md`.) They are differentiated by **loading model**, and are *not* redundant:

| Store | Role | Loading model | Holds |
|---|---|---|---|
| **CLAUDE.md / CLAUDE.local.md** | **Rulebook** (always-on) | full body injected every session in scope → keep **lean**, behavioral | "how to act here" — rules, conventions, stack prefs |
| **Claude memory** (`MEMORY.md` + files) | **Knowledge base** (on-demand) | index always loaded; **bodies recalled when relevant** → scales | "what's true / decided / learned" — facts, references |
| **serena** (`~/.serena/projects/<name>/`, `~/.serena/memories/`, `~/.serena/memories/global/`) | **Code intelligence** (code-coupled) | pulled via tools during code work; stored globally in `~/.serena/` (no in-repo `.serena/` dir) — inherently git-safe | symbols + prose *about the codebase*; reusable code patterns (global tier) |

**Routing heuristic:** behavior / always-apply → CLAUDE.md · recalled fact → memory · code-coupled knowledge → serena.

**Decisions routing (locked 2026-06-25 — D1):** apply the same code-coupling test. A decision that explains *why code is shaped a certain way* → serena, `kind=decision`. A decision about *workflow / tool / architecture / process* (code-agnostic) → Claude memory, `kind=decision`, at the right scope. The earlier "decisions/rationale → serena" proposal is refined: most decisions this user generates are process/architecture; routing them all to serena would orphan them away from where they are recalled. Serena earns only the code-level ones.

## 4. Directory layout (root → branch)

**Working tree** (what sits in the filesystem where you work):

```
~/.claude/                                   [Universal + Machine]
  CLAUDE.md                                  Universal GENERIC rulebook            (you 1°)
  CLAUDE.local.md                            Machine SPECIFIC rulebook             (agent 1°)
                                               └ mounts, mount→data, SSH paths, IPs
  skills/worktree/                           the /worktree method (Workspace-generic tooling)

~/Documents/projects/                        [Workspace]  — NOT a git repo
  CLAUDE.md                                  Workspace GENERIC rulebook
  CLAUDE.local.md                            Workspace SPECIFIC (repo inventory / sync — thin)
  _remember-to-process/                      legacy .remember holding (harvest, then delete)

  <repo>/                                    [Project]  — a git repo
    CLAUDE.md                                Project GENERIC rulebook (stack prefs)   [gitignored]
    CLAUDE.local.md                          Project SPECIFIC rulebook/facts          [gitignored]
    <source files…>
    .worktrees/<branch>/                     [Work-unit]  — nested, dot-prefixed       [gitignored]
      CLAUDE.local.md                        Work-unit SPECIFIC (ephemeral)            [gitignored]
      <source files…>

~/.serena/                                   serena GLOBAL store — entirely outside repos, inherently git-safe
  projects/<name>/project.yml              project registration + config (one entry per registered project/worktree)
  memories/                                all project and global memories (keyed by project name)
  memories/global/                         reusable cross-project code patterns (always injected)
```

**State tree** (Claude Code's own per-key store, OUT of the working tree):

```
~/.claude/projects/<cwd-key>/
  memory/
    MEMORY.md                                knowledge-base index (always loaded)
    *.md                                     fact files (recalled on demand)
```
`<cwd-key>` = the cwd path with `/` and `.` → `-`. *(Knowledge-base physical location is partly TBD — see §12 / open cell.)*

## 5. File conventions

- **Pair per scope:** `CLAUDE.md` (generic) + `CLAUDE.local.md` (specific). **Location encodes scope; the `.md` vs `.local` suffix encodes genericity.**
- **`.local` kept** as the specific-file name — it is natively recognized and auto-gitignored by Claude Code. (Trade-off in appendix D.)
- **Rulebook stays lean** (always-on). Bulk/recall-heavy knowledge goes to memory or serena, not CLAUDE.md.
- **Frontmatter schema (locked 2026-06-25 — R):** all generated memory files carry these five fields, in this order, all required:

  ```yaml
  created: YYYY-MM-DD          # first (chronological sort/glance)
  type: user|feedback|project|reference|decision
  scope: universal|machine|workspace|project|work-unit
  genericity: generic|specific
  last_updated: YYYY-MM-DD
  ```

  **Filename convention:** `<created>-<type>_<slug>.md` — date-prefixed (date = the `created` field); the prefix after the date equals `type` (single prefix; filename ⊆ frontmatter coherence: every filename token has a backing field).

  **Naming principles:** (a) *verb/noun cut* — nouns = identity fields (`type`/`scope`/`genericity`); past-participle verbs = event fields (`created`/`last_updated`); governs field naming, not order. (b) *filename ⟺ frontmatter coherence* — any token encoded in the filename must have a corresponding frontmatter field.

  **Fields dropped vs earlier proposals:** a separate `kind` axis (rule|fact|decision|reference) was considered and dropped — rules belong in CLAUDE.md not memory; `decision` folds cleanly into `type`; `scope` absorbs tier. A retention/ranking cluster (`importance`, `status`, `usage`, TTL, `confidence`) is **deferred** to curation tooling.

  **Adoption:** retag of ~20 existing memories + a CLAUDE.md memory-writing rule is **deferred** to user go — see §12.

## 6. Native composition (zero `@import`)

Claude Code loads `CLAUDE.md` then `CLAUDE.local.md` by **walking up the directory tree** from cwd, concatenating root→cwd, plus the user-level `~/.claude/`. Because worktrees **nest** inside the repo and the Workspace file sits at `~/Documents/projects/`, the **entire ladder composes by location alone — no `@import` bridge anywhere:**

```
~/.claude/CLAUDE.md                              Universal generic   ┐ user-level, always
~/.claude/CLAUDE.local.md                        Machine specific    ┘
~/Documents/projects/CLAUDE.md  + .local         Workspace           ┐
~/Documents/projects/<repo>/CLAUDE.md + .local   Project             │ native walk-up
<repo>/.worktrees/<branch>/CLAUDE.local.md       Work-unit           ┘ (nested)
```

## 7. The global gitignore gate (`~/.gitignore_global`)

**Hard rule:** no agent-facing file is ever committed / travels via git. Enforced **once, globally** (one definition, every repo, no per-session drift). The gate ignores **agent-generated files only** (not all `.md` — README etc. are normal):

```
# agent artifacts — never committed (see feedback_no_agent_files_in_git)
CLAUDE.md
CLAUDE.local.md
.worktrees/
.remember/            # legacy — plugin dropped, holding dirs being harvested
```

Notes: (a) gitignore only blocks *adding* new files; a repo that already tracks a committed `CLAUDE.md` is unaffected locally (the rule still says never add ours). (b) `~/.serena/` (global) and `~/.claude/` live outside repos — already safe; serena is inherently git-safe because it stores everything globally under `~/.serena/`, never inside a repo. (c) `~/Documents/projects/CLAUDE.md` (Workspace) is in a non-repo dir → not committed regardless.

> **Correction 2026-06-25:** `.serena/` removed from the gitignore block. Serena stores all project configs and memories globally at `~/.serena/projects/<name>/` and `~/.serena/memories/` — there is no in-repo `.serena/` directory to ignore.

## 8. Workspace structure

`~/Documents/projects/` is the **Workspace** scope — the projects+worktrees collection. It is **not** a git repo. It holds:
- `CLAUDE.md` / `CLAUDE.local.md` — the Workspace rulebook pair (same pattern as every tier).
- repos as children (`<repo>/`), each a git repo with its own Project pair + nested worktrees.
- `_remember-to-process/` — legacy holding for the dropped `.remember` data.
- Worktree management (create/fix/prune/sync) is the Workspace's job; the `/worktree` skill is its generic tooling.

## 9. Ownership rule

By **genericity**:
- **Generic** content → **human primary, agent secondary** (you define prefs/rules).
- **Specific** content → **agent primary, human secondary** (agent discovers facts about this box/repo/work).

## 10. The ownership matrix

| Scope | Rulebook — `CLAUDE.md`/`.local` (always-on) | Knowledge base — memory (on-demand) | Code — serena | Owner |
|---|---|---|---|---|
| **Universal** | `~/.claude/CLAUDE.md` | universal memory | `~/.serena/memories/global/` (reusable patterns) | generic → **you** 1°, agent 2° |
| **Machine** | `~/.claude/CLAUDE.local.md` | machine memory (mounts/SSH/IPs) | — | specific → **agent** 1°, you 2° |
| **Workspace** | `~/Documents/projects/CLAUDE.md` + `.local` | workspace memory (thin — inventory/sync mostly derivable) | — | rules → you · specifics → agent |
| **Project** | G: `<repo>/CLAUDE.md` · S: `<repo>/CLAUDE.local.md` | project memory | `~/.serena/projects/<name>/` + `~/.serena/memories/` (global, keyed by project name — no in-repo `.serena/`) | rules → **you** · facts/code → **agent** |
| **Work-unit** | `<repo>/.worktrees/<br>/CLAUDE.local.md` | (ephemeral) | its own global serena project at `~/.serena/projects/<name>/` | specific → **agent** 1° |

## 11. Lifecycle & tooling (NEEDED — future build)

Neither claude nor serena provides cross-tier lifecycle. A **curation tooling layer** is required to maintain boundaries and move knowledge as it matures/decays:
- **Emergent rules** — a recurring *specific* observation → **promote** to a *generic* rule.
- **Deprecation** — a *generic* pref no longer true → **demote / retire**.
- **Harvest-on-close** — on PR merge/abandon, promote the worktree's durable signal **up to project** (serena project memory / decisions), then discard the ephemeral remainder. serena harvests worktree→project (optionally →global); journals are harvested, not pushed wholesale.

## 12. Open cells (explicit TBD — not yet decided)

### Resolved / Locked 2026-06-25

- **D1 — Decisions/rationale home:** SPLIT by code-coupling. Code-coupled decisions (why code is shaped this way) → serena, `kind=decision`. Code-agnostic decisions (workflow / tool / architecture / process) → Claude memory, `kind=decision`, at the right scope. See §3 routing heuristic update and appendix O.
- **D2 — Machine-generic recipes:** Confirmed in Claude memory, Machine-scope, generic-tagged. Portable methods (e.g. GNOME headless RDP, NVIDIA VGL device perms) already live there; this decision confirms that placement. Vault = human mirror only; no duplication. **Tagging (genericity=generic on Machine memories) is BLOCKED until the frontmatter schema is adopted** — see the frontmatter open cell below. See appendix P.
- **D3 — C-1 composition asymmetry:** ACCEPTED + closed. The rulebook composes by walk-up (location=scope); memory is off-tree, keyed by cwd, and does not compose up the tiers. Accepted because anything that must apply across scopes is a rule → lives in the rulebook (which does compose up); memory holds scope-local recalled facts, so each cwd seeing only its own store is correct. **Known consequence folded into curation-tooling cell below:** a worktree's cwd-key ≠ its repo's key, so a worktree session won't auto-load the project memory (project rules still reach it via CLAUDE.md walk-up; only project facts don't). The fix (a memory-key fallback or harvest) belongs to the future curation tooling. See appendix Q and C-1.
- **① Frontmatter schema finalized (locked 2026-06-25 — R):** five-field YAML schema in order (created · type · scope · genericity · last_updated), all required; filename = `<created>-<type>_<slug>.md` (date-prefixed). `kind` axis dropped. Retention/ranking cluster deferred to curation tooling. **Adoption (retag of ~20 existing memories + CLAUDE.md memory-writing rule) DEFERRED to user go.** See §5 and appendix R.
- **③ Work-unit archival: BOTH (locked 2026-06-25 — S):** on worktree close, (a) harvest the distillate (decisions/patterns/gotchas) up to the Project store, and (b) snapshot the full work-unit context to a timestamped cold store `<repo>/.worktrees/_archive/<branch>/`. The archive is a lifecycle endpoint — never loaded/recalled, carries no live frontmatter. Trigger = `/worktree remove` (archive/revivable) or `reap` (harvest→archive→delete). See appendix S.
- **④ serena cross-worktree: global/ tier, never copy (locked 2026-06-25 — T):** cross-project patterns → `~/.serena/memories/global/` (auto-shared, zero wiring); a worktree registers as its own serena project and is NOT given the parent's project-memories; durable worktree memories harvest up to the parent on reap (ties to ③). **Revises Plan B F1** (drop the "copy main's memories" step; keep register-as-own-project). Residual: confirm `global/` auto-surfaces via `list_memories`. See appendix T.

### Open

1. **Execution — ① adopt frontmatter schema:** retag ~20 existing memories (`type=`, `scope=`, `genericity=`); add memory-writing rule to CLAUDE.md. Unblocks D1 (`type=decision` routing) and D2 (`genericity=generic` on Machine memories).
2. **Build — curation tooling / Plan B / memory-skill** (§11): promote/demote/harvest tooling. Includes the worktree memory-key fallback or harvest surfaced by D3; the `/worktree reap` workflow for ③; the `list_memories` residual check for ④.
3. **Write-time routing enforcement** — nudge vs gate (session lesson: nudge ≠ compel).
4. **PARKED — Company-tier gap:** Machine tier conflates *this-box* + *this-company*; genericity peels the company-switch but not a new-machine-same-company scenario. Not blocking current design; revisit if multi-company portability becomes concrete.

---

# Part II — Appendix: decisions, alternatives, reasoning

Every choice in Part I, with what else was considered and why we landed here. Ordered roughly as they arose.

### A. Build a memory architecture at all
- **Decision:** treat memory/instruction storage as a designed system with a contract per store.
- **Alternatives:** keep ad-hoc (status quo).
- **Why:** the three pains (§1) are structural, not incidental — they recur and worsen as scope grows.

### B. Two axes (scope × genericity)
- **Decision:** organize by scope tier × generic/specific.
- **Alternatives:** (i) lifecycle-primary (organize by how long knowledge lives); (ii) full 2-D grid (scope × lifecycle, every cell named).
- **Why:** lifecycle correlates so tightly with scope (Universal=permanent, Work-unit=days) that a separate lifecycle axis is redundant; the confidentiality fence is a *scope/genericity* property, not a time one. Full grid = over-engineering (YAGNI).

### C. Export fence = vertical generic|specific seam
- **Decision:** the portability/confidentiality boundary runs through every tier (generic vs specific), not as a horizontal line below Universal.
- **Alternatives:** "Universal is the only safe tier, everything below is bound."
- **Why:** the user observed every tier has a generic part + a specific part (e.g. Machine: reusable "RDP-on-Ubuntu" recipe vs this box's IPs). So the fence is vertical. Company-switch = peel the specific column, keep the generic column.

### D. CLAUDE.md pair per level; kept `.local` name
- **Decision:** `CLAUDE.md` (generic) + `CLAUDE.local.md` (specific) at each scope; location=scope, suffix=genericity.
- **Alternatives:** (i) a custom legible name for the specific file (e.g. `CLAUDE.specific.md`); (ii) `@import` chains pointing at off-tree canonical files.
- **Why:** Claude Code natively loads only `CLAUDE.md` + `CLAUDE.local.md` and auto-gitignores `.local`. A custom name would need an `@import` and lose native loading. The `@import` chain (my first draft) was **noise** — native directory walk-up already composes the hierarchy. Verified via context7 (`code.claude.com/docs/memory`).

### E. Hard rule — no agent files in git
- **Decision:** no `CLAUDE.md` / memory / serena / `.remember` ever committed; enforced by one global gitignore gate.
- **Alternatives:** commit project-level rules (the industry default — verified: all 8 surveyed harnesses, e.g. Cursor/Cline/Copilot, commit project rules for team-sharing).
- **Why:** confidentiality (agent files carry infra topology, prefs, decisions that must never enter a company repo's history) + portability (knowledge rides the user's own layered setup, not the repo). **Contrarian on purpose.** Cost accepted: no team-sharing of agent rules via the repo; portable guidance must ride the user's own sync, not clone.

### F. Worktree placement — NEST in-repo (not siblings)
- **Decision:** worktrees live at `<repo>/.worktrees/<branch>/`.
- **Alternatives:** siblings at `~/Documents/projects/.worktrees/<repo>/<branch>/` (the prior layout) + one `@import` bridge.
- **Why / the twist:** I first claimed nesting causes a "fight every tool forever" tooling tax (ripgrep dup matches, pytest double-collect, etc.). The user pushed back; two Sonnet subagents + web verified the claim was **OVERSTATED** — `.gitignore` fixes git/rg/ruff/VSCode, and pytest skips dot-prefixed `.worktrees/` via `norecursedirs`. The user then noted `.worktrees/` is a fixed convention → one entry in the **global** gitignore neutralizes it everywhere. The last tilt to siblings (serena LSP double-indexing the nested copies) was cleared when context7 confirmed serena has a native ignore system (`is_ignored_path` / `ignored_paths`). With all blockers gone, **nest** wins because it makes the CLAUDE.md ladder compose **natively end-to-end (zero `@import`)**. Cost accepted: one-time `/worktree` skill migration (worktree path, drop the bridge, recompute artifacts symlink depth).

### G. Stores reduced to claude + serena; `.remember` dropped
- **Decision:** keep claude + serena; drop the `.remember` plugin.
- **Alternatives:** keep `.remember`; build a propagation layer on it.
- **Why:** validated (RE-559 + RE-499 cross-check) that the official plugin is ~80%+ redundant with Jira+commits+plan docs; its value is **inverse to Jira discipline** (a thin backstop). Ephemeral by design; ~90% raw-log cruft. Unique slice (bugs/gotchas) real but small. Full reasoning + "hopes for a bespoke replacement" in `remember-plugin-analysis-and-decision.md`. Deferred Task #7.

### H. Three store-roles (corrects the "fold facts into CLAUDE.md" overreach)
- **Decision:** CLAUDE.md = always-on rulebook; memory = on-demand knowledge base; serena = code-coupled. They are distinct by **loading model**.
- **Alternatives:** (A) fold all facts into the CLAUDE.md overlay (one store); (C) hybrid (universal/machine facts in CLAUDE.md, rest in memory).
- **Why:** (A) was **wrong** — it would cram lazy-recall facts into always-on context and bloat every session. CLAUDE.md injects its **full body** every session; memory loads an **index** + recalls bodies on demand. Different loading models → not redundant → both kept.

### I. serena vs claude division
- **Decision:** serena = code-coupled knowledge (symbols + prose about the codebase, queried during code work, lives with the project); claude = code-agnostic knowledge (behavioral rules + user/env facts, injected as context).
- **Why:** different consumption (navigating/editing code vs deciding behavior) and different coupling (serena goes stale with code; claude doesn't). Fuzzy overlap = decisions/rationale → resolved as D1 / appendix O (2026-06-25).

### J. Ownership by genericity
- **Decision:** generic → human 1°/agent 2°; specific → agent 1°/human 2°.
- **Why:** humans define prefs/rules (generic); agents discover environment/repo/work facts (specific). Maps ownership to the axis that already governs portability.

### K. serena has a global tier (corrected belief)
- **Decision:** treat serena as project + global (`~/.serena/memories/global/`).
- **Was believed:** serena is project-ceilinged.
- **Why corrected:** subagent + source confirmed serena writes global memories via the `global/` prefix, always injected. So reusable code patterns have a home above the project. serena still has **no worktree awareness and no native lifecycle** → harvest is ours (§11).

### L. Workspace follows the same pair pattern
- **Decision:** `~/Documents/projects/CLAUDE.md` + `.local`.
- **Why:** consistency (every tier has the pair) **and** a payoff — `~/Documents/projects/` is an ancestor of every repo, so its rulebook loads natively for all projects via walk-up. Completes the zero-`@import` ladder.

### M. Notes/vault = manual human interface, out of automation scope
- **Decision:** `~/Documents/notes` is the human-readable interface the user curates by hand; it is **not** the canonical agent store and is **not** auto-written.
- **Alternatives:** make the vault the canonical home for portable/generic content (my earlier map).
- **Why:** the user built notes for themselves, to read and to write into deliberately. The agent's layers live in their own stores; notes is a separate, manual mirror.

### N. Promote/demote/harvest tooling needed
- **Decision:** a curation layer is required (not provided by either store).
- **Why:** knowledge matures (specific→generic = emergent rules) and decays (deprecated prefs), and worktree learnings must be harvested at close. Without tooling, the tiers drift.

### O. Decisions/rationale routing — split by code-coupling (locked 2026-06-25)
- **Decision:** apply the existing code-coupling test to decisions. Code-coupled decision (why code is shaped a certain way) → serena, `kind=decision`. Code-agnostic decision (why a workflow / tool / architecture / process) → Claude memory, `kind=decision`, at the right scope.
- **Alternatives:** (i) all decisions → serena (the earlier proposal from appendix I); (ii) all decisions → a dedicated decisions doc in the vault.
- **Why:** the earlier "all → serena" proposal conflated code-level decisions with process/architecture decisions. Most decisions this user generates are the latter — workflow, tooling, infrastructure choices — which would be orphaned in serena (a code-intelligence store, not recalled during non-code sessions). A dedicated vault doc duplicates the same routing problem. The code-coupling test already governs everything else in §3; applying it to decisions is the minimal, consistent resolution. Refines appendix I without contradicting it.

### P. Machine-generic recipes stay in Claude memory (locked 2026-06-25)
- **Decision:** portable machine methods (e.g. GNOME headless RDP setup, NVIDIA VGL device perms) stay in Claude memory at Machine scope, with `genericity: generic` tagging. Vault = human-readable mirror only; no duplication between stores.
- **Alternatives:** (i) vault/notes as canonical home (human maintains it, agent reads it); (ii) both stores maintained in parallel.
- **Why:** these recipes were already accumulating in Claude memory (see `reference_gnome_headless_rdp`, `reference_nvidia_vgl_device_perms_ubuntu`). The vault is the manual human interface (appendix M); making it canonical for recalled facts contradicts the stores model. Parallel maintenance creates drift. The memory holds the recalled essence + a pointer to the vault doc for the full write-up — vault is the detail store, memory is the retrieval surface. **Dependency:** `genericity: generic` tagging is blocked until the frontmatter schema (§12 open cell) is adopted.

### Q. C-1 composition asymmetry — accepted + closed (locked 2026-06-25)
- **Decision:** accept the asymmetry. The rulebook composes by walk-up (location=scope); the knowledge base (memory) is off-tree, keyed by cwd, and does not compose up the tiers. This is correct behavior, not a bug.
- **Alternatives:** (a) accept the asymmetry — status quo, zero migration (chosen); (b) relocate memory to follow the in-tree location=scope pattern — uniform but fights a native Claude Code feature (`~/.claude/projects/<cwd-key>/`).
- **Why:** anything that must apply across scopes is a **rule** — it belongs in the rulebook, which composes via walk-up. Memory holds scope-local recalled facts; each cwd seeing only its own store is the right semantics. The asymmetry that C-1 flagged is therefore not a design flaw but a correct differentiation between the two loading models (§3). **Known consequence:** a worktree's cwd-key differs from its repo's cwd-key, so a worktree session won't auto-load the Project memory store (project rules still reach it via CLAUDE.md walk-up; only project facts don't). This gap is real but belongs to the curation-tooling open cell (§12), not to this architectural question.

### R. Frontmatter primitives finalized (locked 2026-06-25)
- **Decision:** five fields, in order, all required: `created` (YYYY-MM-DD) · `type` {user|feedback|project|reference|decision} · `scope` {universal|machine|workspace|project|work-unit} · `genericity` {generic|specific} · `last_updated` (YYYY-MM-DD). Filename convention: `<created>-<type>_<slug>.md` (date-prefixed; date = the `created` field; prefix after the date = `type`; single prefix).
- **Alternatives considered:** (i) a separate `kind` axis {rule|fact|decision|reference} — dropped, no arisen need; rules belong in CLAUDE.md not memory, and `decision` folds cleanly into `type` while `scope` absorbs tier; (ii) a retention/ranking cluster {importance, status, usage, TTL, confidence} — deferred to curation tooling; `usage` is derived from recall logs, not hand-stamped.
- **Naming principles:** (a) *verb/noun cut* — nouns = identity (`type`/`scope`/`genericity`); past-participle verbs = events (`created`/`last_updated`); governs naming not order. (b) *filename ⟺ frontmatter coherence* — every filename token has a backing field (filename ⊆ frontmatter). `created` is first for chronological sort/glance.
- **Back-fill order** for existing memories: originSessionId date → file mtime → `= last_updated`.
- **External validation:** survey of Obsidian + agent-memory frameworks (Mem0/Letta/Zep) + Claude Code's own MEMORY.md spec validated the core fields; `genericity` is bespoke — no framework has a generic/specific export axis, so it is self-enforced.
- **Adoption deferred:** retag of ~20 existing memories + a CLAUDE.md memory-writing rule is deferred to user go (see §12 execution cell).

### S. Work-unit archival: both harvest + cold snapshot (locked 2026-06-25)
- **Decision:** on worktree close, do both: (a) harvest the distillate (decisions, patterns, gotchas) **up** to the Project store via the standard routing test; (b) snapshot the full work-unit context to a timestamped cold store at `<repo>/.worktrees/_archive/<branch>/`.
- **Key point:** the archive is a lifecycle **endpoint** — it is never loaded, never recalled, and carries no live frontmatter. It is not a sixth scope tier.
- **Trigger:** `/worktree remove` (archives, leaves revivable snapshot) or `/worktree reap` (harvest → archive → delete). Corresponds to Plan B F4.
- **Alternatives:** (i) dedicated-archive-only (no harvest) — loses the distillate in the cold store, unrecallable; (ii) roll-up-only (no archive) — loses the full context, nothing to revive from. **Chose both**: distillate stays useful and nothing is permanently lost.

### T. serena cross-worktree: global/ tier, never copy (locked 2026-06-25)
- **Decision:** share-up + harvest-up, never copy-down. Cross-project patterns → `~/.serena/memories/global/` (auto-shared, zero wiring). A worktree registers as its **own** serena project (own code index) and is **not** given the parent repo's project-memories. Durable worktree memories harvest **up** to the parent on reap (ties to S/③).
- **Evidence from live install:** `~/.serena/memories/global/` is a real native shared tier — already holds cross-project feedback memories; serena_config `read_only_memory_patterns` example `global/.*` treats it as cross-project. Per-project memories live at `~/.serena/projects/<name>/memories/`.
- **Revises Plan B F1:** drop the "copy main's memories" step from worktree setup; keep register-as-own-project.
- **Alternative rejected:** copy-per-worktree (Plan B F1 original) — redundant with the `global/` tier and drift-prone (N copies diverge).
- **Residual check:** confirm `global/` auto-surfaces via `list_memories` (not yet verified).

---

# Part III — Conflict check (spec ↔ appendix)

Surfaced for resolution **before** proceeding (per the goal):

- **C-1 RESOLVED 2026-06-25 (accepted — see D3 / appendix Q): rulebook is in-tree, knowledge base is not.** §4–6 say "location encodes scope; files at each level compose by walk-up" — but that is true only for the **rulebook** (`CLAUDE.md`/`.local`). The **knowledge base** (memory) lives under `~/.claude/projects/<cwd-key>/memory/`, **off-tree**, keyed by cwd — it does *not* sit "at each level" and does *not* compose by walk-up. So the elegant "location=scope, native composition" property (§6) applies to rulebook only, not to memory. **Resolution:** asymmetry accepted — option (a). Anything that must apply across scopes is a rule → rulebook (which composes up); memory holds scope-local recalled facts, so each cwd seeing only its own store is correct, not a bug. Known consequence (worktree cwd-key ≠ repo cwd-key → project facts don't auto-load in worktrees) is folded into the curation-tooling open cell.

- **C-2 (caveat, not a contradiction): gitignoring `CLAUDE.md` globally.** §7 ignores `CLAUDE.md` in every repo. Repos that *already* track a committed `CLAUDE.md` (e.g. a teammate's) keep it tracked — gitignore only blocks new adds. No conflict with the hard rule (we still never add ours), but worth knowing the global ignore won't *hide* a pre-existing tracked one.

- **R-1 RECONCILED 2026-06-25 (R / appendix R): §5 frontmatter placeholder replaced by finalized schema.** §5 previously read "Frontmatter + naming discipline: TBD (§12)". Appendix O and §12 (D1) referenced a `kind=decision` tag that was never formally defined. Decision R (2026-06-25) finalized the five-field schema, dropped the `kind` axis entirely (rules belong in CLAUDE.md; `decision` folds into `type`), and replaced the TBD line in §5 with the full schema block. The `kind=decision` references in §3 (D1 paragraph) and appendix O remain accurate in intent — they now map to `type=decision` in the finalized schema. No residual contradiction; the wording in those sections uses `kind=decision` as a label coined before R was locked; it is correct to read it as `type=decision` going forward.

- No other spec↔appendix contradictions found. Everything else in Part I has a matching rationale in Part II.
