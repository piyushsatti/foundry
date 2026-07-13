> **Vendored into the meditate plugin 2026-07-05** from
> `pslap:~/Documents/personal/notes/infrastructure/mem-arch-planner-handoff-2026-06-25.md`.
> This copy is canonical from now on; the pslap original is historical. Plugin prose
> (`agents/curator.md`, `skills/*`) still cites the old path — repointing is a pending repair item.

---
title: "Memory Architecture — Planner Handoff (tools / MCP / agents / contracts)"
date: 2026-06-25
status: handoff
audience: "planner session — implementation design for tooling/MCP/agents"
related:
  - 2026-06-24-memory-architecture-spec.md      # authority spec
  - mem-arch-00-orchestrator.md                 # root/hub
  - mem-arch-session-handoff-2026-06-25.md       # worktree / Plan B
  - project_memory_architecture_design.md        # Claude memory — live thread
  - reference_memory_architecture_map.md         # Claude memory — digest
---

# Memory Architecture — Planner Handoff (2026-06-25)

## 1. Purpose & audience

For the **planner session** that will design/build the **tools, MCP servers, agents, and contracts** around the memory architecture. The high-level memory design is **DECISION-COMPLETE** as of 2026-06-25 — every architectural choice is locked. This doc is the consolidated, self-contained picture: you should not need to re-read the whole design thread to start.

**The form factor of each capability — skill / CLI / MCP server / agent — is YOUR call.** This handoff hands you the *contracts* (the stable interfaces) and the *build agenda* (the capabilities), not the implementation shape.

## 2. Status snapshot

| State | Items |
|---|---|
| ✅ **Locked (design)** | 2-axis model · 3 stores · routing test · ownership · hard rule · worktree nesting · serena-global · + 2026-06-25: #2/#3/#4, ① frontmatter finalized, ③ archival, ④ serena cross-worktree |
| ⏳ **Execution (near-term)** | **① ADOPT** = retag ~20 memories to the finalized schema + a CLAUDE.md memory-writing rule (user-applied) |
| 🔨 **Build (yours)** | **②** curation tooling · **Plan B** (`/worktree` lifecycle) · memory-management skill · export-fence operation |
| ⛔ **Parked** | Company-tier gap (not blocking) |

## 3. The locked architecture

**2-axis model.**
- **Scope tiers:** `Universal ⊃ Machine ⊃ Workspace ⊃ Project ⊃ Work-unit` (applicability + lifecycle).
- **Genericity:** every tier = `generic base + specific overlay`. The genericity seam is a **vertical export fence through every tier**. **Company-switch = detach `specific`, keep `generic`.**

**3 stores, differentiated by LOADING MODEL (not redundant):**
- **CLAUDE.md / `.local`** = always-on **rulebook**; full body injected every session in scope; composes by **filesystem walk-up** (location = scope). Keep lean + behavioral.
- **Claude memory** (`MEMORY.md` index + `*.md`) = on-demand **knowledge base**; index always loaded, bodies recalled on relevance. Stored at `~/.claude/projects/<cwd-key>/memory/` (off-tree, **cwd-keyed** — does NOT compose up tiers).
- **serena** = **code-coupled** intelligence; stored **GLOBALLY** at `~/.serena/` (git-safe).

**Routing test:** proactive (fires every time) → CLAUDE.md · recalled (looked up) → memory · code-coupled → serena. Behavioral prefs ("run ruff", "prefer tables") are **RULES → CLAUDE.md, never memory.**

**Ownership:** generic → human 1° / agent 2°; specific → agent 1° / human 2°.

**Decisions locked 2026-06-25:**
- **#2 Decisions/rationale → SPLIT by code-coupling:** code-coupled (why code is shaped this way) → **serena** `kind=decision`; code-agnostic (why a workflow/tool/architecture) → **Claude memory** `type=decision`.
- **#3 Machine-generic recipes** (GNOME-RDP, NVIDIA-VGL) → **Claude memory, Machine-scope, generic-tagged**; vault = human mirror only.
- **#4 C-1 composition asymmetry → ACCEPTED:** rulebook walks up; memory is cwd-keyed/off-tree and does NOT compose — fine because cross-scope knowledge is a RULE (rulebook composes up). **Consequence:** a worktree's cwd-key ≠ its repo's key → a worktree session won't auto-load the Project memory (project *rules* still reach it via walk-up; project *facts* don't) → folded into ② curation.
- **① Frontmatter primitives FINALIZED** (see §4.1; retag/adopt deferred to user go).
- **③ Work-unit archival → BOTH** (see §5).
- **④ serena cross-worktree → `global/` tier, never copy** (see §4.4).
- **Write-time enforcement → RULE-FIRST** (sharpened routing rule sufficed; Phase-3 hooks SKIP unless drift recurs).
- **`.remember` → DROPPED** (bespoke rebuild deferred).

## 4. Contracts — the stable interfaces every tool MUST honor

### 4.1 Frontmatter schema (FINALIZED)

```yaml
---
name: <slug>
description: <one-line recall hook>
metadata:
  created: YYYY-MM-DD                                    # FIRST — chronological anchor (sort/glance)
  type: user | feedback | project | reference | decision
  scope: universal | machine | workspace | project | work-unit
  genericity: generic | specific                         # the export fence — bespoke, self-enforced
  last_updated: YYYY-MM-DD
  # node_type, originSessionId — auto, keep
---
```
- **All 5 fields REQUIRED** (an untagged memory is unpeelable → a hole in the fence).
- **Filename:** `<created>-<type>_<slug>.md` — date-prefixed (date = the `created` field); prefix after the date **== `type`** (single prefix, not stacked).
- **Naming principles:** (a) **verb/noun cut** — nouns = what it IS (`type`/`scope`/`genericity`), past-participle verbs = what HAPPENED (`created`/`last_updated`); governs *naming*, not order. (b) **filename ⟺ frontmatter coherence** — any filename token must have a backing field (filename ⊆ frontmatter).
- **`created` back-fill** (existing memories): `originSessionId` date → file mtime → `= last_updated`.
- **Dropped:** a separate `kind` axis (no arisen need; rules→CLAUDE.md). `decision` folds into `type`; `scope` absorbs tier.
- **Deferred to ② — the "retention vocabulary":** `{ importance, status, usage, TTL?, confidence? }`, designed as one set with the curation tool. `usage` = **derived from recall logs**, never hand-stamped.
- Survey-validated core (matches Obsidian + Mem0/Letta/Zep + Claude Code's own MEMORY.md `type` enum); `genericity` is the one bespoke field.

### 4.2 Store roles + routing test
Per-store loading model in §3. The routing test is the write-time contract: proactive→CLAUDE.md, recalled→memory, code-coupled→serena. Decisions split by code-coupling (#2).

### 4.3 Genericity export-fence
`generic` = portable/company-safe; `specific` = bound/gitignored. **Company-switch operation = filter out everything `genericity: specific`, keep `generic`.** This is the whole reason ① is load-bearing — the operation is driven entirely by the frontmatter tag.

### 4.4 serena model (cross-worktree)
- `~/.serena/memories/global/` = **native shared tier** (auto-surfaces across all projects; holds cross-project patterns). Cross-project knowledge goes here — **zero copying**.
- `~/.serena/projects/<name>/memories/` = per-project.
- A **worktree registers as its OWN serena project** (own code index) and is **NOT** given the parent's project-memories (avoids N-way drift) — it onboards fresh or uses live symbol tools.
- Durable worktree memories **harvest UP** to the parent on reap (ties to §5).
- **NEVER copy-down.** (This **revises Plan B F1** — drop the copy step, keep register-as-own-project.) Residual check at adopt: confirm `global/` auto-surfaces via `list_memories`.

### 4.5 Lifecycle semantics (what the curation layer must implement)
- **promote** (specific→generic): move the memory up a scope-key + flip its `genericity` tag (an "emergent rule").
- **demote / deprecate**: a generic pref no longer true → retire or mark.
- **retire / archive**: stale → out.
- **harvest** (worktree→project): on worktree close, distillate graduates up (§5).

### 4.6 Memory store location + C-1
`~/.claude/projects/<cwd-key>/memory/` (cwd-key = path with `/ . _` → `-`). home-key carries Universal+Machine; repo-key = Project; worktree-key = Work-unit. Memory does **not** compose up tiers (C-1 accepted). The worktree↛project-memory gap (§3 #4 consequence) is the curation layer's to close (fallback or harvest).

### 4.7 The hard rule
**No agent-facing file (CLAUDE.md, Claude memory, serena, .remember) is ever committed or travels via git.** serena is inherently safe (lives at `~/.serena/`). Everything else is gitignored/local.

## 5. Build agenda (capabilities — form factor is the planner's call)

| Capability | What it must do | Contract |
|---|---|---|
| **① ADOPT** (execution, near-term) | retag ~20 existing memories to §4.1 (set `created`/`scope`/`genericity`; `type: decision` + `decision_` renames; `genericity` tags per #3) + draft+apply a CLAUDE.md memory-writing rule (**user-applied** — `~/.claude` is read-only to agent Bash) | §4.1 |
| **② Curation tooling** (working name `/curate-memory`) | promote / demote-deprecate / retire-archive / harvest-on-worktree-close; + the worktree↛project-memory fallback; + derive `usage` from recall logs; + design the retention vocabulary | §4.5, §4.6 |
| **Plan B** (`/worktree` lifecycle) | modes `add` / `remove`=archive / `revive` / `reap`; `.reap-manifest.md` (work-unit notes + serena-memory diff vs main); **F1 REVISED (no copy)**; F2 `artifacts/` rename; F3 context capture; F4 modes. Doc: `~/.claude/plans/dreamy-meandering-dusk.md` (DRAFTED, not approved) | §4.4 |
| **Memory-management skill** | consumes the reap-manifest; merges worktree memories/serena/CLAUDE **up to main** (the harvest mechanism). May be the same effort as ② | §4.5 |
| **③ Work-unit archival** (policy locked, build rides ②/Plan B) | **BOTH**: harvest distillate UP to Project (via routing test) + snapshot full work-unit to timestamped cold store `<repo>/.worktrees/_archive/<branch>/`. Archive = lifecycle ENDPOINT, **not a scope tier**. Trigger = `/worktree remove`(revivable)/`reap`(harvest→archive→delete) | §4.5 |
| **Export-fence operation** | company/machine switch: filter by `genericity: specific` to detach specific overlays + machine/company-bound memories, keep the generic base | §4.3 |
| **Enforcement** | rule-first now; escalate to hooks only if drift recurs | §4.2 |

## 6. Deferred / parked
- **Company-tier gap:** the Machine tier conflates *this-box* + *this-company*. `genericity` peels company-switch cleanly, but NOT new-machine-same-company (keep company-specific, drop box-specific — both are `specific@machine`). Revisit if it bites. **Not blocking.**
- Retention vocabulary (with ②) · `.remember` bespoke rebuild · retire 8 stale out-of-tree brains · 24+ items in `workflow_pending_cleanup.md`.

## 7. Constraints & guardrails
- **HARD RULE** (§4.7) — no agent files in git.
- **Implementation Gate** — no writes/build without an explicit user "do it / build it".
- **`~/.claude` is read-only to agent Bash** → CLAUDE.md / settings / hooks changes are **USER-APPLIED**; supply exact commands.
- **serena lives globally** at `~/.serena` — never in-repo.
- User reviews every diff; conventional commits; **never add Co-Authored-By**.

## 8. Pointers (canonical docs)
- **Authority spec:** `2026-06-24-memory-architecture-spec.md` (§5 frontmatter, §12 cells, Part II appendix A–T, Part III conflict check incl. C-1 + R-1).
- **Root/hub:** `mem-arch-00-orchestrator.md`.
- **Live design thread:** `project_memory_architecture_design.md` (Claude memory).
- **Digest:** `reference_memory_architecture_map.md` (Claude memory).
- **Worktree / Plan B:** `mem-arch-session-handoff-2026-06-25.md`.
