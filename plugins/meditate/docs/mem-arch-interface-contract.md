> **Vendored into the meditate plugin 2026-07-05** from
> `pslap:~/Documents/personal/notes/infrastructure/mem-arch-interface-contract.md`.
> This copy is canonical from now on; the pslap original is historical. Plugin prose
> (`agents/curator.md`, `skills/*`) still cites the old path — repointing is a pending repair item.

---
title: "Memory Architecture — Interface Contract (planner / build boundary)"
date: 2026-06-25
status: FROZEN v3 — state-vocab FINAL v2 (scope=mapping, schema_version added 2026-06-28); action-lexicon FINAL v2 (horizontal verbs split/combine/link/amend added 2026-07-03); manifest FINAL v3 (claude.local.md store added 2026-06-28; source_path/content_hash/mtime candidate fields + manifest schema_version frontmatter added 2026-06-28 P3; horizontal-verb fields — combine_sources/link_target_*/children/severed_dependency/patch/dest.key — added 2026-07-03); hook-points STUB (worktree-skill session)
related:
  - mem-arch-planner-handoff-2026-06-25.md      # §1 state-vocab authority (B, closed)
  - 2026-06-24-memory-architecture-spec.md       # authority spec
  - mem-arch-00-orchestrator.md                  # root/hub + surfaced-issues
  - mem-arch-session-handoff-2026-06-25.md        # worktree / Plan B (F1 now superseded — see §6)
  - meditate-problem-domain-formalization.md      # the WHY / theory — model + research record (2026-06-29)
  - 2026-07-03-meditate-horizontal-implementation-plan.md   # v2→v3 change-control log entry (horizontal verbs)
---

# Memory Architecture — Interface Contract

The **frozen boundary** between the three concurrent workstreams, so each builds in parallel
against a fixed shape instead of each other's internals (header-file / API-schema discipline).

| § | Section | Owner | State |
|---|---|---|---|
| 1 | State vocabulary (frontmatter) | **B** (conceptual, closed) | FINAL v2 (scope=mapping, schema_version — 2026-06-28) |
| 2 | Action lexicon (verbs + action-nouns) | **this session** (lifecycle/how) | FINAL v2 (horizontal verbs split/combine/link/amend added 2026-07-03) |
| 3 | Manifest schema | **this session** | FINAL v3 (scope mapping, claude.local.md store — 2026-06-28; source_path/content_hash/mtime + schema_version frontmatter added 2026-06-28 P3; horizontal-verb fields added 2026-07-03) |
| 4 | Skill hook-points | **A** (worktree skill) | STUB — A implements |
| 5 | Consumer — memory-curator agent | this session | spec'd |

**Freeze discipline:** changes go through the orchestrator surfaced-issues protocol, never ad-hoc.
A *shape* change (new field, new verb, new store) must be logged there before any session adopts it.

**Changelog:**
- 2026-07-03: horizontal verbs added — split/combine/link/amend; preserve-before-destroy;
  per-source locks. (§2, §3 bumped; full spec: `2026-07-03-meditate-horizontal-implementation-plan.md`)

---

## §1 — State vocabulary (FINAL v2 — owner: B planner-handoff §4.1; scope+schema_version amended 2026-06-28)

The nouns of *state*: what a memory IS. Authority is the planner-handoff; restated compactly:

```yaml
metadata:
  schema_version: 2                                       # REQUIRED integer. Current = 2. Files without it are implicitly v1 (pre-migration).
  created: YYYY-MM-DD                                     # chronological anchor
  type: user | feedback | project | reference | decision  # NOTE: `kind` axis DROPPED; decision folds in; no rule/fact
  scope:
    depth: 0          # int — hops below $HOME (0 = home). Machine-independent ordinal.
    role: home        # home | repo | worktree | sub | dir
  genericity: generic | specific                          # the export fence (the one bespoke field)
  last_updated: YYYY-MM-DD
```
- All fields REQUIRED (untagged memory = a hole in the export fence). Filename `<created>-<type>_<slug>.md` (date-prefixed; date = the `created` field).
- **`schema_version`** — integer schema version. Current = `2`. The curator/applier rejects unknown versions. Files without it are implicitly v1 (pre-migration).
- **`scope`** — a **derived relative descriptor**, a mapping (NOT a scalar, NOT an absolute path, NOT a fixed named tier):
  - `depth`: integer, hops below `$HOME` (0 = home). Machine-independent ordinal.
  - `role`: `home | repo | worktree | sub | dir`. Auto-derived (`home` when cwd == `$HOME`, `worktree` when `*/.worktrees/*`); best-effort (`repo`, `sub`); else `dir`. Refinable via a `KNOWN_ROLES` config.

  Computed by `derive_scope()`; see `migrate_frontmatter.py`.
- **Rules never live in memory** — proactive/always-apply → CLAUDE.md (no `rule` value in `type`).
- **decision splits by code-coupling** (#2): code-coupled (why *code* is shaped so) → **serena**,
  tagged `kind=decision` (serena convention); code-agnostic (why a *workflow/tool/arch*) →
  **Claude memory**, `type=decision`.
- Retention vocab `{importance, status, usage, TTL?, confidence?}` is **deferred to ② curation**
  (designed with the tool; `usage` derived from recall logs, never hand-stamped). Not in v1.

## §2 — Action lexicon (FINAL v2 — owner: this session; horizontal verbs split/combine/link/amend added 2026-07-03)

The verbs that *act* on §1's nouns, and the nouns naming the action-artifacts. The lexicon is
**directive**: the manifest's `verb` field (§3) is a command the applier dispatches on.
Verbs are **axis-separated** — the 2-axis model (scope × genericity) demands it; a single "demote"
conflated two distinct moves, now split.

### Disposition verbs — per harvest candidate (the manifest `verb`)
| verb | axis / target | effect |
|---|---|---|
| **promote** | scope (up) | relocate the candidate to a broader scope (lower `depth` / more-shared `role`; exact ordering over `{depth, role}` defined by the curator, P2) |
| **merge** | collision | land into an existing destination item; reconcile bodies. **2-way** (candidate vs dest-now), adjudicated against **live code via LSP** for serena — no 3-way base (see §6) |
| **keep** | — | leave at its current scope; only meaningful on `archive`, irrelevant on `reap` |
| **drop** | — | discard ephemeral noise |
| **promote-to-rule** | store→rulebook | the item is actually a *rule* (proactive/always-apply) → flag for **CLAUDE.md** (USER-applied); NEVER writes a memory store. Replaces the old drop+flag workaround. Coupled-safety: rule lands in CLAUDE.md *before* the memory is dropped. |
| **demote-rule** | rulebook→store | a CLAUDE.md rule that belongs better as a recalled memory → write the memory FIRST, then remove the rule line (marker-anchored if present, else exact-match; no match → PARTIAL: memory kept, line stays, NO data lost). Reverse of `promote-to-rule`. Coupled-safety: memory write must succeed before the CLAUDE.md edit. |

> `demote-rule` added 2026-06-27 (meditate plugin §A).
> **Reserved for the store axis only (2026-07-03)** — the scope-axis move (global→project
> rulebook) is named `narrow-rule` (reserved, not implemented in v1). See "Horizontal verbs"
> below.

### Rule-marker standard (v1 — locked 2026-06-28, P4)

Both `promote-to-rule` (write) and `demote-rule` (remove) depend on a shared marker convention.
The marker is embedded in the rulebook file (CLAUDE.md or CLAUDE.local.md) immediately after each managed rule.

**Format:**
```
<rule text — one line>
<!-- meditate:rule id=<slug> src=<memory-filename> -->
```

**Convention:** the rule text appears on one line; the marker appears on the IMMEDIATELY FOLLOWING line (no blank line between them). This two-line block is the write/remove unit.

- `id=<slug>` — the candidate's slug (unique within the rulebook).
- `src=<memory-filename>` — the source memory file basename (e.g. `2026-06-01-reference_some_fact.md`).
- Both `promote-to-rule` and `demote-rule` use this exact format; neither supports same-line placement.
- Removal (demote-rule): match the two-line block (rule + marker); if no marker present, fall back to exact-match on the rule text alone; no fuzzy matching.

### Curation verbs — ongoing maintenance (② tooling; not harvest-bound)
| verb | axis / target | effect |
|---|---|---|
| **generalize** | genericity | flip `specific`→`generic` (export-fence promotion; "emergent rule") |
| **specialize** | genericity | flip `generic`→`specific` (narrow an over-broad item) |
| **deprecate** | lifecycle | mark stale / no longer true (bumps `last_updated` — v3, 2026-07-03) |
| **retire** | lifecycle | remove |

> Reconciliation with B handoff §4.5: B's "promote (specific→generic)" = our **generalize**
> (genericity axis); B's "demote/deprecate" = our **specialize** + **deprecate**. B's "harvest"
> = the process noun below; B's "retire/archive" = **retire** + the archive *endpoint* (§4).

### Horizontal verbs — layer restructuring (NEW v3, added 2026-07-03)

Verbs that restructure item boundaries **within** one layer (store × scope × genericity × type)
without moving atoms across cells — the boundary verbs (`split`/`combine`/`link`) conserve the
layer's content; `amend` is the one deliberate exception (corrects content in place, pre-image
archived). Full mechanics: `2026-07-03-meditate-horizontal-implementation-plan.md` §2.2–§2.5.

| verb | arity | effect | coupled-safety ordering |
|---|---|---|---|
| **split** | 1→N | decompose an item into N cohesive children + reify severed cohesion edges as links | archive-copy original → write N children → update index → tombstone original |
| **combine** | N→1 | merge N same-cell items into one strictly-richer result | archive-copy every source → write result (new path) → update index → tombstone each source |
| **link** | 1↔1 | reify a cohesion edge crossing an item boundary — non-destructive | append `Related: [[slug]] — <invariant>` to both files, bump `last_updated` (no archive; nothing destroyed) |
| **amend** | 1→1 | correct a stale/wrong claim in place without changing the item's cell or boundaries | pre-scan ALL patch anchors (zero edits on any miss) → archive pre-image → apply all patches → bump `last_updated` |

**Store scoping (v1):** `split` / `combine` / `link` / `amend` are **claude-store only**. A
serena horizontal candidate routes to needs-human; serena extension is future work.

**Existing-verb amendments (v3):**
- **`merge`** now also archives the **destination's pre-image** before reconciling (uniform
  recoverability across all mutating verbs — former open question resolved).
- **`deprecate`** now **bumps `last_updated`** on the banner edit (previously missed).

**Naming reservation:** **`demote-rule` is reserved for the store axis (R→M) only** (unchanged
meaning). The scope-axis move on a rule (global rulebook → project rulebook) is reserved as
**`narrow-rule`** — named now, **not implemented** in v1.

### Action-nouns (glossary)
- **harvest** — the batch process at worktree-close that emits a manifest of candidates.
- **manifest** (`.reap-manifest.md`) — the harvest output (§3).
- **candidate** — one harvested memory under triage.
- **disposition** — the curator's proposed `{verb, dest, genericity_op, rationale}` for a candidate.
- **collision** — a candidate whose destination already holds a related item → triggers `merge`.

## §3 — Manifest schema (FINAL v3 — owner: this session; source_path/content_hash/mtime + schema_version frontmatter added 2026-06-28 P3; horizontal-verb fields added 2026-07-03)

`<repo>/.worktrees/<branch>/.reap-manifest.md` — front-matter list, one entry per candidate.
**No `base` field** — F1 is no-copy (§6), so a worktree's memories are genuine new authorship →
harvest is **pure-add**; the only reconciliation is a `collision` against the destination.

The manifest file carries a top-level `schema_version: 2` in its frontmatter (alongside `curated`,
`curator`, `serena_available`). The applier rejects manifests with unknown versions.

```yaml
candidates:
  - id: <slug>
    store: serena | claude
    source: <worktree memory path/key>
    type: <user|feedback|project|reference|decision>   # candidate's §1 type
    scope:                                              # candidate's CURRENT scope (§1 v2 mapping)
      depth: <int>    # hops below $HOME
      role: <home|repo|worktree|sub|dir>
    genericity: <generic|specific>                          # candidate's CURRENT genericity (the BASE; proposed.genericity_op flips it)
    body: <the memory content>
    source_path: <absolute path to the candidate's memory file>
                                                        # curator-emitted (DG-P3-1=A); the curate skill uses
                                                        # it to compute content_hash + mtime post-attach.
    content_hash: <sha256 hex>                          # skill-post-attached via sha256sum on source_path;
                                                        # feeds the apply skill's optimistic lock (re-hash
                                                        # before write; mismatch → abort that item).
    mtime: <epoch seconds>                              # skill-post-attached via stat --format=%Y on source_path;
                                                        # feeds the apply skill's optimistic lock alongside hash.
    file_schema_version: <int>                          # curator-emitted; applier skips candidate if value > 2 (unknown schema)
    collision: <ref to existing dest item> | none       # if present → 2-way merge vs dest (LSP-adjudicated for serena)
    proposed:                                           # the curator fills this block
      verb: promote | merge | keep | drop | promote-to-rule | demote-rule
      dest: { scope: { depth: <int>, role: <home|repo|worktree|sub|dir> }, store: serena | claude | claude.md | claude.local.md }
      source_file: CLAUDE.md | CLAUDE.local.md | ~       # demote-rule only — the rule's removal anchor for the applier
      genericity_op: generalize | specialize | none      # fence-axis op applied on landing, if any
      rationale: <curator reasoning>
```
**Apply-time routing by `genericity`:** `generic` → committed file (`CLAUDE.md` / `*.md`);
`specific` → gitignored local file (`CLAUDE.local.md` / `*.local.md`). The export fence decides the store.

The harvester (skill, §4) fills everything except `proposed`. The **curator agent** (§5) fills
`proposed`. A human approves. A **mechanical applier** then executes the verbs (smart-propose /
dumb-apply / human-gate).

### §3a — Horizontal-verb candidate fields (NEW v3, 2026-07-03)

Extends a candidate block when `proposed.verb` is one of the four horizontal verbs. All other
fields per the schema above are unchanged.

```yaml
confidence: high | medium | low        # NEW, ALL verbs — single source of truth (review reads
                                        # this yaml field, not curator prose)
combine_sources:                       # NEW, combine only — per-source lock + cell data
  - { source_path: <abs>, content_hash: <sha256>, mtime: <epoch>,
      scope: {depth: <d>, role: <r>}, genericity: <g>, type: <t>, store: claude }
link_target_path: <abs>                 # NEW, link only — curate-attached (endpoint 2)
link_target_hash: <sha256>              # NEW, link only
link_target_mtime: <epoch>              # NEW, link only
proposed:
  verb: promote | merge | keep | drop | promote-to-rule | demote-rule | split | combine | link | amend   # extended enum
  # NOTE (2026-07-05, foundry repair): the shipped curator emits a codified 14-verb enum that ALSO
  # includes generalize | specialize | deprecate | retire as first-class verbs (matching the
  # applier), rather than only via `genericity_op` / "② tooling". See meditate-decisions-and-findings.md
  # 2026-07-05. generalize/specialize stay ALSO valid as a `genericity_op` modifier.
  dest:
    scope: { depth: <int>, role: <home|repo|worktree|sub|dir> }
    store: serena | claude | claude.md | claude.local.md
    key: <abs project-dir path>          # NEW, REQUIRED for any cross-key destination — lets the
                                          # applier resolve the destination memdir
  children:                              # NEW, split only — each written with created=today,
    - { id: <slug>, type: <t>, scope: {depth: <d>, role: <r>},    # last_updated=today,
        genericity: <g>, body: <content>, links: [<sibling-ids>] } # schema_version: 2
  severed_dependency: <one line> | none  # NEW, REQUIRED on split
  result:                                # NEW, combine only — must land on a NEW path
    { id: <slug>, type: <t>, scope: {...}, genericity: <g>, body: <content> }
  link_to: <slug>                        # NEW, link only — the target's frontmatter `name:` slug
                                         # (store [[...]] convention); resolver = filename-slug
                                         # glob, then name:-field match, same memdir (v1). The
                                         # Related-line display slug is the name: slug too.
  link_note: <one-line invariant>        # NEW, link only
  patch:                                 # NEW, amend only
    - { anchor: <exact existing text>, replacement: <corrected text> }
  rationale: <curator reasoning>
```

**Applier validation (v3 additions):** law-1 clause (b) cross-candidate references (a candidate
referencing a path another candidate in the same manifest creates or destroys) → **manifest-level**
fail of the involved candidates · split without `severed_dependency` → fail · any child/result path
collision → fail (no clobber, no `exists — skipped` for horizontal verbs) · combine with >4 sources,
any cross-cell source, or any `combine_sources` hash mismatch (dedicated lock loop — separate from
the existing top-level `source_path` re-hash) → fail · serena-store horizontal verb → needs-human ·
missing or tombstoned endpoint (link both, amend target) → fail · amend pre-scan anchor miss → fail
with zero edits.

**Hash attachment (curate skill, v3 additions):** split → the **original** only (children don't
exist yet) · combine → **every** `combine_sources` entry · link → `source_path` (endpoint 1) +
`link_target_*` (endpoint 2) · amend → `source_path` as usual.

**Tombstone formats (NEW v3, 2026-07-03):**
- **split-original tombstone** — frontmatter `type: tombstone / split: <date> / archived:
  <archive-path> / children: [<child-paths>] / reason: <rationale>`; body lists each child path.
- **combine-source tombstone** — frontmatter `type: tombstone / combined: <date> / into:
  <result-path> / archived: <own-archive-path> / reason: <rationale, naming the sibling sources>`
  (written once per source).

**Archive naming (v3, key-qualified):** every archived copy (split original, combine sources,
amend/merge pre-images) lands at
`~/.claude/backups/memory-archive/<date>-<keyslug>-<orig-filename>.md` with `archived_from` /
`archive_reason` metadata. The key qualifier prevents same-basename collisions when multiple
sources from different memory keys archive on the same day.

## §4 — Skill hook-points (STUB — owner: worktree-skill session "A")

What `/worktree` must provide. Consistent with Plan B (`dreamy-meandering-dusk.md`) **minus the F1
copy step, which is DROPPED** (§6).

```
wt add     → register the worktree as its OWN serena project (own code index).
             NO copy-down of parent memories. (F1 FINAL — see §6)
wt reap    → 1. collect the worktree's NEW memories:
                  serena  ~/.serena/projects/<wt-name>/memories/
                  claude  ~/.claude/projects/<wt-cwd-key>/memory/
                2. detect collisions vs the parent destination
                3. write <wt>/.reap-manifest.md  (§3 shape; no base)
                4. invoke the memory-curator agent (§5) → fills `proposed`
                5. human approves → mechanical applier executes the verbs
wt remove  → archive (revivable): freeze the worktree buckets; NO harvest (work unfinished)
```
- A worktree's claude memory starts **empty** (its cwd-key ≠ the repo key — C-1 accepted), so the
  claude harvest is also pure-add. The read-side gap (a worktree session can't *see* project
  memory while working) is **②'s fallback to design**, not this contract's job (B handoff §4.6).

## §5 — Consumer: the memory-curator agent

| Property | Decision |
|---|---|
| Form | dedicated agent type — `~/.claude/agents/memory-curator` (user-applied; `~/.claude` is read-only to agent Bash) |
| Model + effort | **Opus**, **`effort: xhigh`** (semantic, high-stakes, low-volume — promotion is rare; the per-subagent `effort` field overrides the session level). Justified override of the default-Sonnet-subagent rule (advisor-class). |
| Authority | **SOLE promoter.** Work-sessions may only *flag candidates* into the manifest — never promote/merge directly. |
| Output | **proposes** `proposed` blocks + rationale; **never auto-writes.** Human gates; a dumb applier executes. |
| Input | a `.reap-manifest.md` (§3) **or** a periodic store-wide sweep (`/curate-memory`) for drift/contradiction. |
| Context | the spec + routing test + §1 vocabulary + the *current* state of every target scope (to detect collision / merge / contradiction). |

The curator is the single chokepoint for the **export fence** (the `genericity` call at promotion)
and the single authority enforcing the routing test at harvest — which is *why* it can't be left to
individual work-sessions (tunnel vision → re-imports the original cross-contamination problem).

## §6 — Decision log / cross-session reconciliations

- **F1 REVERSED → NO copy-down (2026-06-25).** Supersedes this session's earlier "copy-at-fork
  (merge base)" lock; aligns B planner-handoff §4.4 + revises Plan B F1 (drop the copy step, keep
  register-as-own-serena-project). **Why:** the copy was *self-inflicted* — copying parent memories
  into the worktree is what creates the divergence that then *needs* a base to resolve. No copy →
  worktree bucket is pure-new → harvest is pure-add, no 3-way merge. And serena is **code-coupled**:
  the ground truth (code) is always live via LSP, so a collision is better adjudicated against live
  code than against a stale copied base (which also drifts — B's "N-way drift"). **Consequence:**
  drop the merge-base machinery; **Task #3 re-closed** (no per-worktree serena copy wiring needed).
- **Single "demote" split → `specialize` (genericity) + `deprecate` (lifecycle)**, per the 2-axis
  model. Our originally-locked 5 verbs (promote/merge/keep/drop/demote) become 4 disposition +
  4 curation verbs (§2).
- **`kind` axis dropped → `type`** (B §4.1); no `rule`/`fact` values in memory.
- **`promote-to-rule` verb added (2026-06-25)** — when an audited/harvested memory is actually a CLAUDE.md rule, name it explicitly (dest=CLAUDE.md, USER-applied) rather than overloading `drop`. Coupled-safety: promote the rule to CLAUDE.md *before* dropping the memory.
- **Scope assignment rule (2026-06-25, superseded 2026-06-28)** — original enum-based rule (`generic`+OS-independent → universal; `generic`+OS/machine-bound → machine) is superseded by the v2 mapping below. The genericity/portability distinction it captured is preserved; scope now encodes *position* (depth+role) rather than an applicability tier.
- **`scope` vocabulary locked → `{depth, role}` mapping (2026-06-28, OI-4 RESOLVED)** — `scope` becomes a derived mapping (`depth`: int hops below `$HOME`; `role`: `home|repo|worktree|sub|dir`) instead of the old named-enum. Computed by `derive_scope()`; v1 files without this shape are pre-migration. See `meditate-decisions-and-findings.md` 2026-06-28 decision entry.
- **`schema_version: 2` required (2026-06-28)** — added alongside the scope shape change. The curator/applier rejects unknown versions; files without `schema_version` are implicitly v1 (pre-migration).
- **`claude.local.md` added as `dest.store` value (2026-06-28)** — genericity-routing at apply time: `generic` → committed file (`CLAUDE.md`/`*.md`); `specific` → gitignored local file (`CLAUDE.local.md`/`*.local.md`). The export fence decides the store.
