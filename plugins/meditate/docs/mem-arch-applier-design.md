> **Vendored into the meditate plugin 2026-07-05** from
> `pslap:~/Documents/personal/notes/infrastructure/mem-arch-applier-design.md`.
> This copy is canonical from now on; the pslap original is historical. Plugin prose
> (`agents/curator.md`, `skills/*`) still cites the old path — repointing is a pending repair item.

---
title: "Memory Architecture — /apply-curation (the ②-applier) — Design Spec"
date: 2026-06-27
status: design (approved 2026-06-27) — pending implementation plan
related:
  - mem-arch-interface-contract.md            # §2 verbs, §3 manifest, §5 curator — the authority
  - mem-arch-00-orchestrator.md               # Phase 4 / ② curation
  - mem-arch-worktree-skill-handoff-2026-06-25.md   # the reap feed path (A)
  - memory: reference_agent_cannot_delete_memory_files
---

# `/apply-curation` — the ②-applier

## 1. Purpose & pipeline position

The **dumb executor** of the curation pipeline. The memory-curator agent *proposes* dispositions; a
human *gates*; `/apply-curation` *executes* the approved proposals against the live stores and reports.

```
curator (agent, built) → fills `proposed` blocks in a manifest
        ↓
human edits the manifest (cut/tweak = approval)
        ↓
/apply-curation <manifest> → plan summary → confirm once → execute → report + optional-cleanup block
        ↑                                    ↑
   /curate-memory (sweep)               wt reap (worktree)      ← the two feed paths
```

Smart-propose / **dumb-apply (this)** / human-gate. The applier makes **no semantic decisions** — it
executes exactly what the (human-approved) manifest says.

## 2. Scope

**In scope:** execute the 9 verbs (contract §2) against the live stores; **cold-archive + tombstone**
for deletes (recoverable); final-confirm gate; a report + an optional-cleanup block + a CLAUDE.md-changes-to-review list.

**Out of scope (YAGNI):** the curator (built); the `/curate-memory` sweep wrapper (separate, thin —
dispatches curator, hands the manifest here); physical file deletion (impossible in-session — §6);
conflict-resolution intelligence (the curator already decided; merges carry the curator's instruction).

## 3. I/O contract

- **Input:** a path to an *approved* manifest — the contract-§3 `.reap-manifest.md` shape, with each
  candidate's `proposed { verb, dest{scope,store}, genericity_op, rationale }` filled, after the human
  has edited it (deleted rejected candidates, tweaked any field). "Approved" = whatever remains in the file.
- **Output (to the chat):**
  1. a **plan summary** before applying (counts per verb + every destructive op), then a single confirm;
  2. an **execution report** — per candidate: done / skipped / failed (+ why);
  3. a copy-paste **optional-cleanup block** (tombstoned sources to `rm` whenever — content is already archived, so non-urgent — §6);
  4. a **CLAUDE.md-review list** — the rule additions written by `promote-to-rule` (the user re-reads the diff).

## 4. Per-verb execution

| verb | store | action |
|---|---|---|
| `promote` | claude | Write a new file `<created>-<type>_<slug>.md` at the dest scope's key, §4.1 frontmatter; add its `MEMORY.md` index line |
| `promote` | serena | activate the dest project → `write_memory(name, body)` |
| `merge` | claude | Edit the existing dest file — reconcile per the curator's rationale (supersede stale lines, keep the rest); bump `last_updated` |
| `merge` | serena | `write_memory` over the existing memory name (supersede) |
| `generalize` / `specialize` | claude | Edit the file's `genericity:` field; if the dest scope differs, relocate (Write at new key + archive + tombstone old) |
| `deprecate` | claude | Edit: prepend a deprecation banner + set a frontmatter note; keep the body |
| `keep` | — | no-op (record "kept" in the report) |
| `drop` / `retire` | claude | **cold-archive** (Write the full memory to `~/.claude/backups/memory-archive/<archived-date>-<orig-filename>`, frontmatter preserved) → **tombstone** the source (§7) → add to the optional-cleanup list. **Recoverable** (copy back from the archive). |
| `promote-to-rule` | claude.md | Edit `~/.claude/CLAUDE.md` — append the curator's rule text under the right section; then **archive + tombstone** the source memory. **Coupled order:** CLAUDE.md write succeeds *first*, then the source is archived+tombstoned. |

Notes:
- **serena writes** require the dest serena project active; the skill activates it, writes, and reports if activation fails (then skips that item, continues the rest).
- **scope relocation** (a `promote` up a scope, or a genericity flip that changes the home key) = Write-at-new + archive + tombstone-old (can't move in-session).

## 5. Execution flow

1. **Read & parse** the manifest. Unparseable → abort with the parse error, change nothing.
2. **Validate** each candidate: known `verb`, resolvable `dest`. Invalid → mark "skip (reason)", don't abort the batch.
3. **Plan summary**: print counts per verb + an itemized list of every destructive op (tombstone+rm, CLAUDE.md edit, relocation). **One confirm** to proceed.
4. **Execute** in a safe order: non-destructive first (promote/merge/generalize/specialize/deprecate/keep), then the archive+tombstone set, then the `promote-to-rule` CLAUDE.md edits (each followed by its source archive+tombstone).
5. **Report** (§3 output 2–4).

## 6. Hard constraints (baked in — see `reference_agent_cannot_delete_memory_files`)

- `~/.claude/projects/<key>/memory/` is **read-only to every shell** (Bash + `!` both EROFS). All writes go through the **Write/Edit tool**; there is **no delete**. → `drop`/`retire`/relocation **cold-archive** the memory (Write to `~/.claude/backups/memory-archive/` — agent-writable via the Write tool, **verified 2026-06-27**; not captured by `capture-claude.sh`) + **tombstone** the source. Physical source-removal is then **optional cleanup** (content is safe in the archive) — a batched `! rm` from the user's real terminal, not a do-or-lose step.
- `~/.claude/CLAUDE.md` **is** editable by the Edit tool → `promote-to-rule` writes there (user reviews the diff).
- `~/.claude/skills/` is agent-read-only → the **SKILL.md is user-installed** (this design supplies it; the user copies it in).
- serena store lives globally at `~/.serena/` (git-safe); writes via serena MCP tools.

## 7. Tombstone format

A dropped/retired memory is overwritten (not deleted) to an inert stub the loader ignores and the user can `rm`:

```yaml
---
name: <original-slug>
metadata:
  type: tombstone
  dropped: YYYY-MM-DD
  archived: "~/.claude/backups/memory-archive/<archived-name>"
  reason: "<verb> — <one-line from the curator rationale>"
---
DROPPED <date> — archived → `~/.claude/backups/memory-archive/<archived-name>` (recover by copying back).
Optional cleanup: `rm <abs-path>` in a normal OS terminal.
```
The optional-cleanup block aggregates every tombstoned path so the user can clear them in one paste — **non-urgent**, since each is already preserved in the archive.

## 8. Error handling

- **Parse failure** → abort, zero changes.
- **Per-item failure** (bad dest, serena activation fails, Edit anchor not found for a merge) → mark that item failed (+ reason), continue the rest, surface all failures in the report. Never half-apply silently.
- **Idempotency** → re-running a manifest is safe-ish: tombstones overwrite identically; a `promote` whose dest file already exists is reported as "exists — skipped" (no clobber) rather than duplicated.
- **Coupled-safety** for `promote-to-rule`: if the CLAUDE.md edit fails, do NOT tombstone the source (the rule must land first).

## 9. Testing

- **Fixture manifest** — a synthetic `.reap-manifest.md` carrying one candidate per verb (incl. one serena, one claude, one promote-to-rule, one drop). Run `/apply-curation` on it against a scratch memory dir; assert each store mutation + the `! rm` block + the CLAUDE.md additions.
- **Realistic fixture** — the curator's smoke-test sweep output (already produced) as an approved manifest.
- **Dry-run** — the plan-summary step IS the dry-run preview (printed before the confirm); no separate flag needed.
- **Archive test** — `drop` a memory → assert the archive copy exists in `~/.claude/backups/memory-archive/`, the source is a tombstone pointing to it (`archived:` field), and no in-session `rm` is attempted (only the optional-cleanup list). Then assert recoverability (copy the archive file back).

## 10. Delivery & callers

- Form: a **skill** at `~/.claude/skills/apply-curation/SKILL.md` — agent-driven instructions (the agent reads the manifest + executes via Write/Edit/serena tools). **User-installed** (skills dir is agent-read-only).
- Callers: you directly (`/apply-curation <manifest>`); the future `meditate:curate` flow; `wt reap` (after its manifest is approved).

## Naming (decided 2026-06-27 — build/rename DEFERRED)

Project = a Claude Code plugin **`meditate`** (reflective memory curation: pause → review → consolidate → release). Terraform `plan → show → apply`, named for reflection:
- **`meditate:curate`** (= plan) — dispatch the read-only curator agent → emit the manifest.
- **`meditate:review`** (= show) — render the pending manifest readably + flag every destructive op; read-only; **re-inspectable anytime** (supports `reap` leaving a manifest for later review+apply).
- **`meditate:apply`** (= apply) — execute the reviewed manifest (this doc's `apply-curation`).

The curator agent stays the internal engine behind `curate` (keeps its enforced read-only / Opus-xhigh safety).

**DEFERRED:** the rename + plugin-packaging wait until the `wt reap` integration is exercised (it'll clarify the real invocation / whether all three commands are wanted). Until then the built pieces — the `apply-curation` skill + `memory-curator` agent — stay installed + **hand-invocable** as-is.
