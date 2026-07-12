> **Vendored into the meditate plugin 2026-07-05** from
> `pslap:~/Documents/personal/notes/infrastructure/meditate-decisions-and-findings.md`.
> This copy is canonical from now on; the pslap original is historical. Plugin prose
> (`agents/curator.md`, `skills/*`) still cites the old path — repointing is a pending repair item.

---
title: "meditate — decisions and findings log"
date: 2026-06-28
last_updated: 2026-07-03
status: LIVE — canonical append-only log; new findings go here first
related:
  - meditate-HANDOFF-2026-06-28.md
  - meditate-implementation-plan.md
  - meditate-gap-AB-plan-2026-06-27.md
  - mem-arch-STATE-2026-06-27.md
  - meditate-problem-domain-formalization.md   # the WHY / theory — model + research record (2026-06-29)
---

# meditate — decisions and findings log

Append-only. New empirical results and design decisions go here first, then get cross-referenced in
handoffs/specs. Do NOT restructure the ~19 surrounding `mem-arch-*` / `meditate-*` docs (that cleanup
is an open item below).

---

## Empirical findings

### 2026-06-27 (verified at Claude Code v2.1.195; DO NOT re-derive)

- **Memory keying — cwd-path-keyed, NOT git-repo-keyed.** Key = `sed 's|[/.]|-|g'` of the absolute
  cwd. Subdirs generate their own isolated key (orphaned, empty). This **contradicts the official docs**
  (which claim git-repo-keyed / subdirs share). Proven live: launching from a repo subdir created its
  own empty memory key.

- **Worktree memory sharing** is via a keystore symlink, not native Claude behavior: the worktree key's
  `memory/` dir is a symlink to the repo-root key's `memory/` (same realpath/inode). The `/worktree`
  skill creates this. Auto-sharing does NOT happen for arbitrary subdirs.

- **Compaction: SessionStart hooks re-fire on `source:compact`** — proven 8/8 across compaction
  boundaries in a real 23 MB / 11-compaction transcript. This is the load-bearing durability primitive.
  Native MEMORY.md index does NOT survive compaction (appeared ~3 times in that transcript, never
  re-injected after a boundary → it decays). No native memory-tool retrieval calls observed (0 calls).

### 2026-06-28 (verified at Claude Code v2.1.195; DO NOT re-derive)

- **Hook output cap = 10,000 characters PER HOOK** (documented: code.claude.com/docs/en/hooks.md).
  Output exceeding the cap is **archived to a file and replaced with a path + preview** (same as large
  tool results) — graceful, NO data loss. It is NOT a silent dead pointer.

- **Multiple SessionStart hooks:** their `additionalContext` values are **concatenated**; each is capped
  at 10k individually; if the combined output is oversized, the same file-archive behavior applies.

- **PostCompact does NOT support `additionalContext`** — only `systemMessage` (user-facing),
  `suppressOutput`, `terminalSequence`. "PostCompact hooks have no decision control." Durability
  therefore rests entirely on the **SessionStart hook firing with `source=compact` + `additionalContext`**
  (proven 8/8). PostCompact cannot serve as a context-injection backup.

- **Real-data volume (this machine, 2026-06-28):**
  - A home-dir key index: 28 entries / ~7,900 chars — fits within the 10k cap.
  - A large project-repo key index: 44 entries / ~10,800 chars — **exceeds the 10k cap alone**.
  - 40 of 50 keys have a non-empty MEMORY.md; intermediate dirs (e.g. `~/Documents`) have no memory key.

- **Environment guards (deployed):**
  - `xattr-guard.sh` blocks agent Bash from executing `bash <a-Claude-authored-file>` (but `source` is
    allowed).
  - `hooks-lock.sh` + `hooks-lock-bash.sh` HARD-DENY any write (Write tool AND Bash) under
    `~/.claude/hooks/**` unless sentinel `~/.claude/.hooks-unlocked` exists.
  - Deployed hooks run fine — Claude Code's hook engine runs them, not the agent's sandboxed Bash.

---

## Decisions

### 2026-06-27 (architecture — locked)

- **Substrate = native markdown files + curator** (MemPalace and other external stores evaluated and
  rejected). Two native stores only: Claude memory + serena. `.remember` dropped.

- **Scope = the folder tree (dynamic depth).** `scope` frontmatter = a derived relative descriptor
  (machine-independent; NOT an absolute path, NOT a fixed `universal|machine|…` enum). Vocabulary to be
  picked before any frontmatter migration (see Open items).

- **Genericity = the export fence**: rulebook = 2 files (`.md` generic / `.local` specific); memory =
  a `genericity` tag. Machine-generic content → memory, not rulebook. The fence governs what is safe to
  git / cross-machine-export, NOT what gets injected in a single-machine session.

- **Durable memory + inherit-down = a SessionStart-on-compact hook** (read-through: reads parent
  MEMORY.md index from disk + injects; NO copy, NO symlink). Proven durable (8/8).

- **Selection method = judgment-first v1**: Opus curator — scope = least-common-ancestor of relevance +
  rubric + decision biases; human gates every promotion. No metrics; quantitative signals
  (usage/recency/dedup) deferred to v2.

- **promote-UP committed; CLAUDE.md↔memory cross-store movement SKIPPED; serena DEFERRED.**

- **Curator = sole promotion authority** (read-only agent). Work-sessions only flag candidates; they do
  not write to the store directly.

- **Archive-not-destroy**: drop/retire cold-archives (recoverable) + tombstones; no in-session delete.
  Archive path: `~/.claude/backups/memory-archive/`.

- **Hard rule: no agent file ever committed to git.** CLAUDE.md / Claude memory / serena / .remember
  never committed or travel via git; agent artifacts stay gitignored/local or outside the repo.

### 2026-06-28 (hook design — post-experiment)

- **Genericity filter DROPPED from the durability hook.** Rationale: genericity is an export fence
  (what's safe to git / cross-machine), NOT an injection fence. On a single machine, reading your own
  local memory into your own session leaks nothing. (User decision.)

- **Import model:** the durability hook imports ALL levels from cwd up to `$HOME` (inclusive), ALL
  entries (specific + generic), **nearest-first**, **dedup by the memory dir's realpath** (auto-handles
  the worktree→repo-root symlink so the repo's memory is injected once, not twice).

- **Fit strategy under the 10k cap = "let it overflow" (v1).** The hook emits all full index lines;
  when the total exceeds 10k, Claude Code's documented graceful archive-to-file handles it without data
  loss. Revisit if real usage / the `/compact` verification shows overflow is common — that degrades
  inline durability to a file reference. (User decision; see Open items.)

- **`memkey_entry_genericity` nested-metadata parser bug is DE-SCOPED from P0.** The genericity filter
  was dropped, so the hook no longer calls this function. Fix deferred to P1, where the
  curator/applier genericity-routing needs it. Note: real memory frontmatter nests `genericity:` indented
  under a `metadata:` block (not as a top-level field) — any parser must match `genericity:` at any
  indentation inside the frontmatter.

- **T2 (PostCompact backup channel) reconsidered:** since PostCompact cannot inject context, its
  original "belt-and-suspenders re-injection" purpose is infeasible. Likely drop T2 or repurpose as a
  user-facing `systemMessage` tripwire. To be finalized when T2 is reached. (See Open items.)

### 2026-06-28 (curate flow — P2-DG1 + P3 decisions)

- **P2-DG1:** the curator stays READ-ONLY (Bash-less). `content_hash` + `mtime` are post-attached
  by the curate skill, NOT the curator. The curator emits `source_path` + `file_schema_version`
  only — a path string is not a write, so read-only is intact.

- **DG-P3-1 = A:** the curate skill resolves candidate → file via the curator's emitted
  `source_path` (not by re-globbing). The curator reads each memory file during its sweep and
  emits the absolute path; the skill then runs `sha256sum` + `stat` on that path to compute
  `content_hash` + `mtime`, injecting both into the candidate block before writing the manifest.

- **DG-P3-2 = guard:** the curate skill applies a runtime worktree/tmp guard (backstop to the
  opt-in `targets.yaml`). For each key read from `targets.yaml`, if it matches `*/.worktrees/*`
  or a `/tmp/` prefix (via inline grep or `memkey_is_worktree` from `lib/memkey.sh`), the skill
  skips it with a printed warning. Opt-in is the primary defense; this guard is belt-and-suspenders.

### 2026-06-28 (scope vocabulary — locked, closes OI-4)

- **`scope` descriptor vocabulary = B-subblock `{depth, role}` (a mapping).** Chosen over the
  role-by-depth enum (re-introduces the fixed-enum leak ARTICLE §3 rejects — sibling dirs at equal
  depth collapse to one label) and over the scalar `"depth:role"` string (chose explicit queryable
  sub-fields, accepting manifest/parser weight). `derive_scope()` returns a dict; CONTRACT §3
  manifest models `scope` as a mapping. Unblocks the frontmatter migration.

- **`schema_version: 2` required alongside the scope change** — integer version field added to the
  `metadata:` block. The curator/applier rejects unknown versions; files without `schema_version` are
  implicitly v1 (pre-migration). CONTRACT §1 updated.

### 2026-07-03 (horizontal layer — locked, implementation plan approved)

- **Horizontal lexicon locked**: `split` (1→N) / `combine` (N→1) / `link` (1↔1, non-destructive)
  / `amend` (1→1, in-place correction) — the full verb set for within-layer restructuring.
- **`demote-rule` disambiguation settled**: reserved for the store axis (R→M) only; the
  scope-axis move (global→project rulebook) is named `narrow-rule` (reserved, not built).
- **`amend` designed** — a novel verb with no theory prior (absent from the DB-normalization /
  agent-memory research base). Two-phase exact-anchor patch: pre-scan ALL anchors, zero edits on
  any miss, then archive pre-image → apply patches → bump `last_updated`.
- **`link` format locked**: body line `Related: [[<slug>]] — <one-line invariant>` on both
  endpoints (bidirectional); no frontmatter `links:` field in v1; same-key only (cross-key link →
  needs-human).
- **Law 3 generalized**: write-before-destroy → **preserve-before-destroy** — archive copies of
  ALL to-be-mutated/destroyed files precede any write; no rollback exists (agent can't delete), so
  pre-flight is the only safety.
- **`merge` archives the destination's pre-image** before reconciling (uniform recoverability
  across all mutating verbs — former open question resolved).
- **Red-team review adopted in full**: verdict REWORK on v1.0 of the implementation plan — 4
  CRITICAL / 7 MAJOR / 5 MINOR findings, all adopted into v1.1 (adjudication table in
  `2026-07-03-meditate-horizontal-implementation-plan.md` §8).
- **Resolve stage stubbed as FUTURE** — a verdict-verification stage between curate and review
  (fresh-context, refute-framed skeptic on intrinsic-judgment failures); deferred until after the
  horizontal layer lands (design sketch in the implementation plan §9).

## 2026-07-05 (foundry-repo repair pass — decisions)

Recorded during the P0/P1 repair of the plugin after its import into the `foundry` monorepo (full
review 2026-07-05; reports in `.gitignored/audits/meditate-full-review-2026-07-05/`).

- **Authority docs vendored into the plugin.** The six contract docs (this file + interface
  contract, problem-domain formalization, planner-handoff, architecture spec, applier design) now
  live at `${CLAUDE_PLUGIN_ROOT}/docs/` and are canonical; the pslap `~/Documents/...` originals are
  historical. Curator/apply/curate cite the plugin path; a missing doc degrades (in-file summary +
  flag), never aborts.
- **Manifest verb enum codified at 14 (the applier's superset).** Contract §3's manifest `verb` enum
  was 10 (6 disposition + 4 horizontal), modeling generalize/specialize as `genericity_op` and
  leaving deprecate/retire without a manifest slot; the applier implements all 14 as executable
  verbs. DECISION: the curator output template now emits the full 14-verb enum to match the applier —
  the lower-risk reconciliation in a repair pass. `generalize`/`specialize` remain ALSO expressible
  as `genericity_op` (a fence flip paired with a promote/keep); either serialization is valid. A
  future cleanup may narrow to the pure contract model (fence flip = modifier only).
- **Manifest container = top-level `candidates:` key** (contract §3, confirmed). curate + curator now
  emit it; a bare list is rejected by `bin/meditate-manifest validate`.
- **Slug rule reaffirmed: `sed 's|[/.]|-|g'`, underscore PRESERVED** (verified live at v2.1.195; see
  the 2026-06-27 memory-keying finding). The skills' contradicting "underscore-replaced live-fire"
  narrative was stale (traced to the 2026-06-25 handoff) and was corrected. `bin/meditate-slug` is now
  the single source, with a legacy-underscore fallback for pre-fix stores.
- **Deterministic helpers extracted to `bin/`:** `meditate-lock` (portable sha256+mtime),
  `meditate-slug` (canonical slug), `meditate-manifest extract|validate` (fenced block + schema +
  law-1). Skills call these instead of inline GNU-only recipes.
- **Safety holes closed (P1):** missing lock on a writing verb → `fail(no lock)`; execute-time lock
  re-verify for all writing verbs (TOCTOU); tombstone-aware re-run reporting; non-clobbering archive
  filenames; migrate-frontmatter fence split line-anchored (fixes a reproduced silent-corruption path).
- **Per-child `key` on `split`** — a split may now fan children into different keys (one `dest.key`
  could not address N keys).
- **`config/targets.yaml` is per-machine + gitignored**; `config/targets.example.yaml` is the tracked
  template; curate reads `${CLAUDE_PLUGIN_ROOT}/config/targets.yaml` and derives the home key from `$HOME`.
- **Harvest / `wt reap`** stays FINAL-shape / stub-producer (unchanged) — the repair made only the
  sweep path runnable; harvest scaffolding was left intact, not built.
- **`merge` resolved as a 2-way "fold source into dest" (the M4 ambiguity, closed).** Sweep `merge`
  was under-specified: the dest wasn't identified (the `collision` field is harvester-only, absent
  in sweep), the dest wasn't locked, and reconciliation happened at apply time. DECISION: model it
  like `combine` — the curator emits `proposed.dest.path` (the existing winner) + `proposed.result_body`
  (the reconciled body it produces); the curate skill locks the dest too (`dest_content_hash`/
  `dest_mtime`); the applier re-verifies BOTH locks, archives the dest pre-image, writes `result_body`
  verbatim to the dest (frontmatter identity kept), then archives+tombstones+de-indexes the source
  (merge-tombstone: `merged`/`into`). Deterministic, human-reviewable, dumb applier. v1 is
  claude-store + same-key; serena/cross-key merge → `needs-human`. Execution-proven in sandbox —
  **all 14 verbs now verified end-to-end.**

---

## Open items / revisit

| # | Item | Priority | Context |
|---|------|----------|---------|
| OI-1 | **Overflow → compression revisit** — if live usage shows a large project key (44 entries / 10.8k) regularly overflows, switch hook to compressed entries (title + path + short hook) to preserve inline delivery. | P1 | empirical section 2026-06-28; decision "let it overflow" |
| OI-2 | ~~**Finalize T2 (PostCompact) fate** — drop T2 or repurpose as `systemMessage` tripwire; PostCompact cannot inject `additionalContext`.~~ **CLOSED 2026-06-28** — PostCompact cannot inject `additionalContext` (only `systemMessage`); durability rests on SessionStart `source=compact`, proven live 8/8. T2 dropped. No code required. | P1 | decision 2026-06-28 "T2 reconsidered" |
| OI-3 | ~~**P1: fix `memkey_entry_genericity` parser** — must match `genericity:` at any indentation inside frontmatter YAML block (it's nested under `metadata:`).~~ **RESOLVED 2026-06-28** — P1·T4: `/^genericity:/` → `/^[[:space:]]*genericity:/` (+ matching `sub`); matches indented real frontmatter, column-0 regression-safe; vault `hooks/lib/memkey.sh` updated (live deploy = optional user bang-shell). | P1 | P1·T4, TDD RED 2/4 → GREEN 4/4 |
| OI-4 | ~~**Pick `scope` descriptor vocabulary** before any frontmatter migration — role-by-depth enum vs depth+role pair.~~ **RESOLVED 2026-06-28** — `scope` = `{depth, role}` mapping (B-subblock). See decision entry below. | P0 gate | decision 2026-06-28; CONTRACT §1/§3 updated |
| OI-5 | **Doc-sprawl cleanup** — ~19 `mem-arch-*` / `meditate-*` docs should eventually be consolidated into fewer surfaces; this log is the new single surface for decisions/findings going forward. | low | open item; do NOT do in this session |
