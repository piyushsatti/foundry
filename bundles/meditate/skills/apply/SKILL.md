---
name: apply
description: Execute a human-approved memory-curation manifest against the live stores — promote/merge/keep/drop/promote-to-rule/demote-rule/generalize/specialize/deprecate/retire/link/amend/combine/split. Archives (never deletes); reports an optional-cleanup rm-block + CLAUDE.md additions/removals. Run manually on a /meditate:review-approved manifest (the human gate is deliberate — nothing auto-chains curate→apply); also the future target of a wt reap harvest.
---

# meditate:apply — the dumb executor

You apply an ALREADY-APPROVED manifest. Make NO semantic decisions — execute exactly what each
candidate's `proposed` block says. Authority: `${CLAUDE_PLUGIN_ROOT}/docs/mem-arch-applier-design.md`
(a pre-horizontal-verb snapshot — where it and THIS skill disagree, this skill wins).

## Input

A path to an approved manifest — a `curate-<ts>.md` from `/meditate:curate` (the live sweep path) or a
`.reap-manifest.md` from a future `wt reap` (harvest). Both are the interface-contract §3 shape: YAML
frontmatter (`schema_version: 2`, `curated`, `curator`, `serena_available`) + a fenced ```yaml``` block
whose SINGLE top-level key is `candidates:` (a list). Use `${CLAUDE_PLUGIN_ROOT}/bin/meditate-manifest
extract <manifest>` to pull that block and `… validate <manifest>` to check it (see Flow step 1).

Optional `--sandbox <ROOT>`: root every read AND write at `<ROOT>` instead of the live store (for
tests — never touch the live store). In sandbox mode a candidate's absolute `source_path` is used
verbatim (reads are NOT re-rooted), so sandbox manifests must carry sandbox-absolute paths.

Resolve the memory-store root once — `ROOT` IS the store root; NO `.claude` appears in any path formula below:
- live (no `--sandbox`): `ROOT = $HOME/.claude`
- sandbox: `ROOT = <given dir>`

Paths (single formula, relative to ROOT — live and sandbox both resolve from it):
- memory store (per candidate): `ROOT/projects/<slug>/memory/` — for same-key ops, `<slug>` is already
  embedded in the candidate's `source_path` (its containing directory); no re-derivation needed. For a
  cross-key destination — a cross-key `promote`, or a `split` child whose proposed cell lands outside the
  source's key — `<slug>` is derived from `proposed.dest.key` (an absolute project-dir path the curator
  emits for any cross-key dest; for a `split` child, its optional per-child `key`, else the candidate
  `dest.key`) via the shared helper `${CLAUDE_PLUGIN_ROOT}/bin/meditate-slug <key>` — canonical rule
  `sed 's|[/.]|-|g'` (`/` and `.` → `-`, `_` PRESERVED; verified live at Claude Code v2.1.195, and it
  self-verifies against `~/.claude/projects/`). The manifest's `dest.scope` is `{depth,role}`
  (machine-independent) — it resolves to a memdir for the home key (`{depth:0,role:home}` →
  `meditate-slug "$HOME"`) or, for any other key, via `dest.key` as above.
- **Cross-key resolution (D2)**: if the resolved dest memdir does not exist, create it. If it has no
  `MEMORY.md`, create one first (header + empty list) — use the Write tool for both (never Bash `mkdir`;
  `~/.claude` is EROFS to Bash) — before appending the first index line or writing the destination file. A
  cross-key candidate (cross-key `promote`, or a `split` child landing outside the source's key) with no
  `proposed.dest.key` → `fail(no dest key)`.
- **keyslug** (for archive naming, law 2): the `<slug>` path segment of a file's OWN memdir — i.e. if a file
  lives at `ROOT/projects/<slug>/memory/<file>.md`, its keyslug is `<slug>`. Used to key-qualify every
  archive filename (see Archive naming under `## Verb execution`).
- archive (store-global): `ROOT/backups/memory-archive/`
- rulebooks (store-global): `ROOT/CLAUDE.md`, `ROOT/CLAUDE.local.md`

**Sandbox / write caveat:** live rulebook + memory writes use the **Write/Edit tool**, NOT Bash — `~/.claude`
is EROFS to agent Bash, and the claude-files-guard blocks CLAUDE.md/memory filenames even outside `~/.claude`
(incl. a `/tmp` sandbox). When a Bash snippet builds the `<!-- meditate:rule -->` marker, run `set +H` first
(shell history-expansion corrupts the `!`).

## Flow

1. **Read + parse** the manifest. Pull the fenced block with `${CLAUDE_PLUGIN_ROOT}/bin/meditate-manifest extract <manifest>` and parse its top-level `candidates:` list. If extract fails, or the block has no `candidates:` key (a bare list is rejected) → STOP, print the error, change nothing.
1b. **Schema guard** — after parse, read the manifest frontmatter `schema_version`. If `schema_version` is absent or not `2` (and not a known-supported value) → STOP with: `unknown or missing manifest schema_version (found: <value or "absent">) — cannot apply safely`. A missing `schema_version` means the manifest is pre-v2 (unknown migration state) → STOP the same way. Per candidate: if `file_schema_version` is present and > 2 → mark `skip(unknown file schema_version: <N>)`, continue. If `file_schema_version` is absent → treat as v1, warn `⚠ <id>: no file_schema_version — treating as v1, migration may be incomplete`, proceed.
2. **Validate** each candidate: known `verb` (the 14-verb set), resolvable `dest`. For `promote` / `promote-to-rule` / `demote-rule`, also require `body` and `type` (the curator fills these in sweep mode, the harvester in harvest mode) — absent → `skip(missing body/type)`. Invalid → mark `skip(reason)`, keep going.
2b. **Serena pre-flight** — if any candidates have `dest.store: serena`, attempt `mcp__plugin_serena_serena__get_current_config`. If serena is inactive/unavailable → surface `⚠ N serena items will be SKIPPED — serena inactive` in the plan-summary so the human can choose whether to proceed before confirming. Do NOT silently skip mid-batch.
2c. **Optimistic lock** — every candidate whose verb writes a MEMORY FILE identified by `source_path` MUST carry a `content_hash` (and `combine` MUST carry a per-source `content_hash` on every `combine_sources[]`). Such a candidate with no lock → `fail(no lock — refusing to write unlocked)`; do NOT execute it. This closes the hole where a hashing failure at curate time (e.g. a `stat`/`sha256` that silently produced nothing) would otherwise execute unlocked. **Exempt** (no memory `source_path` to lock): `keep` (a no-op) and `demote-rule` (its source is a CLAUDE.md rule line, not a memory file — its safety is the exact rule-text anchor match + the memory-first coupled ordering).
   When the lock is present, recompute with `${CLAUDE_PLUGIN_ROOT}/bin/meditate-lock <source_path>` (read-only; EROFS-safe) and compare `content_hash`. On MISMATCH → first check whether `<source_path>` is already a `type: tombstone` whose `archived:` points at the archive path THIS candidate would produce; if so it was ALREADY APPLIED → report `already applied (tombstone verified)` and skip cleanly (this is what makes a re-run after a completed `drop`/`combine`/`split` report correctly instead of a misleading "hash mismatch"). Otherwise → `skip(hash mismatch — file changed since curation)`, record it in the plan-summary, continue. Never abort the whole run (per-item skip). `mtime` may be a cheap pre-filter, but `content_hash` is authoritative.
2d. **Step 0 — manifest validation (law 1, whole-manifest)** — run
   `${CLAUDE_PLUGIN_ROOT}/bin/meditate-manifest validate <manifest>`. It enforces the manifest schema
   plus the statically-checkable half of law 1 (clause (a) in full; clause (b) for paths another
   candidate DESTROYS). If it exits non-zero → STOP and print its diagnostics — the manifest is not
   safe to apply. The clause-(b) CREATED-side (a reference to a `split` child or `combine` result path,
   which is only resolvable at apply time) is deferred to the split/combine pre-flights below
   (`fail(path collision)`). For reference, the full law-1 statement the validator + pre-flights
   jointly enforce: (a) **one verb per item** — no path that is the subject of one candidate (its
   `source_path`, any
   `combine_sources[].source_path`, a `split`'s original, a `link`/`amend` target, or a `merge`'s
   `source_path`/`dest.path`) is ALSO the subject
   of another candidate in this manifest; (b) **no cross-candidate references** — no candidate's
   `combine_sources[].source_path`, `link_to`/`link_target_path`, `amend` target, or `merge` `dest.path`
   may name a path that
   ANOTHER candidate in this same manifest creates (a `split` child, a `combine` result) or destroys (a
   `split` original, any `combine_sources` source, a `merge` source, a `drop`/`retire`/cross-key-`promote` source). On a
   violation of either clause → mark BOTH the violating candidate and the candidate that owns the
   referenced/duplicated path `fail(cross-candidate reference)`; every OTHER candidate proceeds
   unaffected. (A chain like split-then-combine-the-child defers to the next sweep — this manifest does
   not resolve it.)
3. **Plan summary** — print counts per verb + an itemized list of every destructive op (archive+tombstone, CLAUDE.md edit, relocation). Include every hash-mismatch skip in the summary (tagged `⚠ SKIPPED — hash mismatch`). Ask ONE confirm: "Apply these N changes? (yes/no)". On no → stop, change nothing.
   The plan-summary MUST include a distinct `⚠ CLAUDE.md changes: N (promote-to-rule M [.md X / .local Y], demote-rule K)` line if N > 0, so the human sees rulebook edits — split by target file — even without running `review`.
4. **Execute** in order (see `## Verb execution`). **Re-verify the lock at execute time:** immediately
   before each writing candidate's FIRST write, recompute `content_hash` via `meditate-lock` and confirm
   it still matches — the step-3 human-confirm pause is an open TOCTOU window, so a lock checked at 2c
   may be stale by now. Mismatch at execute → `skip(hash mismatch at execute)`, change nothing for that
   candidate. (`amend`/`combine`/`split`/`merge` already re-verify in their own pre-flights; this makes
   it uniform for `drop`/`retire`/cross-key `promote`/`generalize`/`specialize`/`deprecate`/
   `promote-to-rule`/`demote-rule` as well.)
   1. `keep` / `generalize` / `specialize` / `deprecate` / `promote` / `link` (non-destructive)
   2. `merge` (pre-flight both locks → archive dest pre-image → write `result_body` → archive+tombstone source)
   3. `amend` (pre-scan ALL anchors → archive pre-image → apply patches → bump `last_updated`)
   4. `combine` (pre-flight + dedicated lock loop → archive every source → write result → index → tombstone sources)
   5. `split` (pre-flight all children → archive original → write children → index → tombstone original)
   6. `drop` / `retire` (archive → tombstone)
   7. `promote-to-rule` (rule line first, then tombstone — law 3)
   8. `demote-rule` (memory first, then rulebook line — law 3)
5. **Report** (see `## Report`).

## Verb execution

**Archive naming (law 2, all verbs)** — every archive copy is written to
`<archive>/<today>-<keyslug>-<orig-filename>` (never the bare `<archive>/<today>-<orig-filename>`), where
`<keyslug>` is defined in `## Input` / Paths above — this key-qualifies every archived filename so that
same-basename files from different keys archiving on the same day never collide. Every archive copy also
carries `metadata.archived_from: <orig-abs-path>` and `metadata.archive_reason: "<verb-specific reason>"`.

**Archives never overwrite (law 2, non-clobber).** Before writing any archive copy, check whether its
path already exists; if it does (a same-key, same-basename file archived earlier the same day — law 1
only forbids collisions WITHIN one manifest, so two manifests on one day can collide), append `-HHMMSS`
(UTC) to the archived filename and, if that still exists, `-HHMMSS-<n>`. An archive-never-delete store
must never let a second pre-image clobber a first — the recovery copy IS the preservation.

### keep
No-op. Record "kept (no-op)" in the report.

### promote (store=claude)
Write a NEW file at the DESTINATION key's memory dir — `<dest-memory>/<created>-<type>_<slug>.md` — using: `created`=today (if the candidate lacks one); `type`=candidate.type; `scope`=`proposed.dest.scope`; `genericity`=`candidate.genericity` (flipped iff `proposed.genericity_op` is generalize/specialize); `last_updated`=today; body = candidate `body`. Then append a `MEMORY.md` line `- [<Title>](<filename>) — <one-line>` in the dest MEMORY.md. If the dest file already exists → report `exists — skipped` (no clobber, no merge — surface for human to re-run as `merge`).

**Cross-key MOVE** — when `proposed.dest.scope.depth < candidate.scope.depth` (the curator signals a cross-key promote), the source must be removed from its old scope after landing at the destination. Steps in order:
1. Write the new file at the dest key memory dir (as above).
2. Append to the dest MEMORY.md.
3. Archive the SOURCE — Write a COPY to `<archive>/<today>-<keyslug>-<source-filename>` with `metadata.archived_from: <source-abs-path>` and `metadata.archive_reason: "promote (cross-key) — <rationale>"`.
4. Overwrite the SOURCE in place with the tombstone (same format as `drop`): `type: tombstone`, `dropped: <today>`, `archived: "<archive-path>"`, `reason: "promoted to <dest-key> — <rationale>"`; body = `PROMOTED <today> — moved to <dest-key>, archived → <archive-path> (recover by copying back). Optional cleanup: rm <source-path>.`
5. Remove the source's MEMORY.md line from the source MEMORY.md (Edit).
6. Add `<source-path>` to the optional-cleanup block.
On dest collision at step 1 → `skip + surface` (no clobber); do NOT archive/tombstone the source.
NEVER attempt `rm`/unlink in-session (EROFS). The archive copy IS the preservation.

### promote (store=serena)
`activate_project(<dest>)` → `write_memory(memory_name=<slug>, content=<body>)`. Activation fails → `skip(reason)`, continue.

**Common preconditions for the horizontal verbs (`link`, `amend`, `combine`, `split`)** — claude-store
only: if a candidate's `store` (or, for `combine`, any `combine_sources[].store`) is `serena`, mark
`needs-human(serena-store horizontal)` and do NOT execute — horizontal verbs are v1 claude-store-only; a
serena horizontal candidate must never be auto-applied. Every path a horizontal candidate REFERENCES (both
`link` endpoints, the `amend` target, every `combine_sources[].source_path`, the `split` original) must
exist and have `type != tombstone` in its frontmatter — missing or tombstoned → `fail(endpoint missing or
tombstoned)`. These checks are IN ADDITION to, not a replacement for, the per-candidate hash lock at step 2c.

### link (1↔1, non-destructive)
Manifest: `link_target_path` / `link_target_hash` / `link_target_mtime` (endpoint 2, curate-attached) +
`proposed.link_to` (a slug) + `proposed.link_note` (a one-line invariant).
- **Same-key only (v1)**: endpoint 1 (`source_path`) and endpoint 2 (`link_target_path`) must resolve to
  the SAME memdir — `link_to` is a slug resolved against that shared memdir. If the two endpoints are in
  different memdirs → `needs-human(cross-key link)`, do not execute.
- **Display slugs for the two `Related:` lines**: use each endpoint's frontmatter `name:` slug (the
  store's `[[...]]` convention); fall back to the filename slug (`<created>-<type>_<slug>.md`) only when
  `name:` is absent. Endpoint 1's line points at endpoint 2's slug and vice versa. Never re-derive a
  PATH from a slug — endpoint paths come only from `source_path` / `link_target_path`.
- **Both endpoints hash-verified**: endpoint 1 = the candidate's top-level `source_path`/`content_hash`
  (already checked at step 2c); endpoint 2 = `link_target_path`/`link_target_hash` — recompute with
  `${CLAUDE_PLUGIN_ROOT}/bin/meditate-lock <link_target_path>` (read-only) and compare; mismatch →
  `skip(hash mismatch — file changed since curation)`, same handling as step 2c.
- Both endpoints must exist and be non-tombstone (common precondition above).

Execute: Edit BOTH files — append a body line `Related: [[<other-slug>]] — <link_note>` to each (endpoint
1's line points at endpoint 2's slug and carries `link_note`; endpoint 2's line points back at endpoint
1's slug with the same `link_note`); bump `last_updated`=today in both frontmatters. Non-destructive — no
archive, no tombstone, no MEMORY.md index change (item count in each memdir is unchanged).

### merge (2-way fold, claude-store only)
A 2-way fold of the candidate's `source_path` (the LOSING item) INTO an existing dest named by
`proposed.dest.path` (the WINNER). The curator supplies the reconciled body in `proposed.result_body`;
the applier writes it verbatim and does NOT reconcile at apply time — this keeps the executor dumb and
the merge human-reviewable, exactly like `combine`.
Manifest: `source_path` + `content_hash`/`mtime` (source lock) + `proposed.dest.path` +
`dest_content_hash`/`dest_mtime` (curate-attached dest lock) + `proposed.result_body` + `rationale`.

**Pre-flight (all-or-nothing; write NOTHING until every check passes):**
1. Both endpoints `store: claude` — a serena merge → `needs-human(serena merge)` (v1 is claude-only).
   `source_path` and `dest.path` in different memdirs → `needs-human(cross-key merge)` (v1 same-key).
2. Both `source_path` and `dest.path` exist and are non-tombstone → else `fail(endpoint missing or tombstoned)`.
3. Both locks present and re-verified: `source_path` vs `content_hash` (step 2c) AND `dest.path` vs
   `dest_content_hash` (recompute with `${CLAUDE_PLUGIN_ROOT}/bin/meditate-lock`). Missing either lock →
   `fail(no lock)`; either mismatch → `skip(hash mismatch — file changed since curation)`.

**Execute (only once every check above passes):**
1. Archive the DEST pre-image — Write an unmodified COPY of the current dest to
   `<archive>/<today>-<keyslug>-<dest-filename>` (keyslug of the DEST) with `metadata.archived_from:
   <dest-abs-path>` and `metadata.archive_reason: "merge pre-image — <rationale>"`.
2. Write `proposed.result_body` to `dest.path` (replace its body; keep the dest's frontmatter identity);
   bump `last_updated`=today.
3. Archive the SOURCE — Write a COPY to `<archive>/<today>-<keyslug>-<source-filename>` with
   `metadata.archived_from: <source-abs-path>` and `metadata.archive_reason: "merge — folded into <dest.path>"`.
4. Tombstone the SOURCE in place — **merge-tombstone format**: frontmatter `type: tombstone`,
   `merged: <today>`, `into: <dest.path>`, `archived: "<source archive-path>"`, `reason: "<rationale>"`;
   body = `MERGED <today> → <dest.path> (folded in; archived → <source archive-path>).`
5. Remove the source's line from `MEMORY.md`; add `<source-path>` to the optional-cleanup block.

### amend (1→1, claude-store only)
In-place content correction — the item is correctly bounded and placed, but a specific claim inside it (a
status line, a moved path, a superseded fact) is stale. Never used to change an item's cell (that's
`promote`/`generalize`/`specialize`) or its boundaries (that's `split`/`combine`).
Manifest: `proposed.patch: [{anchor: <exact existing text>, replacement: <corrected text>}]` + `rationale`.

**Two-phase, atomic — Phase 1 (pre-scan, read-only, zero writes):**
1. Re-verify the hash lock (already checked at step 2c) still holds.
2. Read the target file. For EVERY entry in `proposed.patch`, confirm its `anchor` exact-matches text
   currently in the file — byte-for-byte, never fuzzy.
3. If ANY anchor is missing → `fail(anchor pre-scan)` for the WHOLE candidate. Make ZERO edits — do not
   apply the patches that DID match. This is what makes "fail = untouched" mechanically true (there is no
   rollback once an Edit lands — the agent cannot delete files).

**Phase 2 (only if every anchor in Phase 1 matched):**
1. Archive the pre-image — Write an unmodified COPY of the current file to
   `<archive>/<today>-<keyslug>-<orig-filename>` with `metadata.archived_from: <target-abs-path>` and
   `metadata.archive_reason: "amend pre-image"`.
2. Apply all patches by exact match — for each `proposed.patch[i]` in list order, Edit the target file
   replacing `anchor` with `replacement` (exact string match).
3. Bump `last_updated`=today in the target's frontmatter.

No index change — same path, same identity; only its content and `last_updated` change.

### combine (N→1, claude-store only)
Manifest: `combine_sources: [{source_path, content_hash, mtime, scope, genericity, type, store: claude},
...]` (per-source lock + cell data) + `proposed.result: {id, type, scope, genericity, body}` + `rationale`.

**Pre-flight (all-or-nothing; NOTHING is written until every check below passes):**
1. **Dedicated lock loop** — re-hash EVERY `combine_sources[i].source_path` with
   `${CLAUDE_PLUGIN_ROOT}/bin/meditate-lock` (read-only) and compare to that entry's own `content_hash`.
   This is IN ADDITION to step 2c — step 2c's optimistic lock only checks the candidate's top-level
   `source_path` and does NOT reach into this nested list; this loop is required and separate. ANY one
   mismatch → `fail(source hash mismatch)` for the whole candidate.
2. Assert every source is claude-store, exists, and is non-tombstone (common preconditions above).
3. Assert all N per-source cells — `scope`, `genericity`, `type`, `store` — are pairwise equal across
   every entry in `combine_sources`. Any cross-cell mismatch → `fail(cross-cell combine — sources occupy
   different cells)` for the whole candidate.
4. Count sources: more than 4 → `fail(cap exceeded)` — do not combine; surface for human review same as
   any other fail.
5. Resolve the result path (`proposed.result`, same memdir as the sources). It must be a NEW path —
   colliding with ANY existing file, source or not, → `fail(path collision)` for the WHOLE candidate. Never
   clobber; never report `exists — skipped` for a horizontal verb.

**Execute (only once every pre-flight check above has passed):**
1. Archive-copy EVERY source — for each `combine_sources[i]`, Write an unmodified COPY to
   `<archive>/<today>-<keyslug>-<its-filename>` (each source's OWN keyslug — sources may come from
   different memdirs) with `metadata.archived_from: <its-abs-path>` and `metadata.archive_reason: "combine
   — <rationale>"`.
2. Write the result — a new file at the resolved result path, using `proposed.result`: `created`=today,
   `last_updated`=today, `schema_version: 2`, `type`/`scope`/`genericity` from `proposed.result`, body =
   `proposed.result.body`.
3. Index — in the shared MEMORY.md: add ONE line for the result; remove all N source lines (Edit). If the
   memdir has no MEMORY.md, create it first (header + empty list).
4. Tombstone EACH source — overwrite it in place with the **combine-tombstone format**: frontmatter
   `type: tombstone`, `combined: <today>`, `into: <result-path>`, `archived: "<that source's own
   archive-path>"`, `reason: "<rationale, naming the sibling sources>"`; body = one line pointing at the
   result path and that source's own archive path.
Add every source's original path to the optional-cleanup block.

### split (1→N, claude-store only)
Manifest: `proposed.children: [{id, type, scope, genericity, body, links: [<sibling-ids>]}]` (one entry
per child) + `severed_dependency: <one line> | none` (REQUIRED — `none` must be explicit, never simply
absent) + `rationale`.

**Pre-flight (all-or-nothing; there is no rollback — the agent cannot delete files — so this is the ONLY
safety net and must run to completion, for every child, before any write):**
1. Verify the original's hash lock (already checked at step 2c) still holds.
2. Resolve EVERY child's destination memdir from its proposed `scope`/`genericity`/`type` cell — same-key
   if the child's cell stays in the original's key; otherwise cross-key resolution via the child's own
   optional `key` (a per-child cross-key dest), falling back to the candidate `proposed.dest.key` (see
   `## Input` / Paths, "Cross-key resolution (D2)"). This lets one split fan children into DIFFERENT keys
   (one `dest.key` alone cannot). A cross-key child with neither its own `key` nor a candidate `dest.key`
   → `fail(no dest key)`.
3. Check every child's filename for collision against: (a) any existing file in its dest memdir, (b) the
   ORIGINAL's own filename (a child may NEVER reuse the original's path), and (c) every sibling child's
   filename. ANY collision, in any of these three, → `fail(path collision)` for the WHOLE candidate — a
   hard fail, never `exists — skipped`.
4. Confirm `proposed.severed_dependency` is present (`none` counts as present; a genuinely absent field
   does not) → missing → `fail(missing severed_dependency)`.
5. If ANY of steps 1–4 failed → fail the WHOLE candidate and write NOTHING.

**Execute (only once every pre-flight check above has passed, for every child):**
1. Archive-copy the original — Write an unmodified COPY to `<archive>/<today>-<keyslug>-<orig-filename>`
   with `metadata.archived_from: <original-abs-path>` and `metadata.archive_reason: "split — <rationale>"`.
2. Write N children — for each entry in `proposed.children`, create
   `<dest-memory>/<created>-<type>_<slug>.md` with `created`=today, `last_updated`=today, `schema_version:
   2`, its proposed `type`/`scope`/`genericity`, body = child `body` followed by one
   `Related: [[<sibling-slug>]]` line per entry in that child's `links`.
3. Index — remove the original's MEMORY.md line; add one line per child to ITS OWN dest MEMORY.md
   (children may land in different memdirs). If a dest memdir has no MEMORY.md, create it first (header +
   empty list) before appending.
4. Tombstone the original — overwrite it in place with the **split-tombstone format**: frontmatter
   `type: tombstone`, `split: <today>`, `archived: "<archive-path>"`, `children: [<child-path-1>,
   <child-path-2>, ...]`, `reason: "<rationale>"`; body lists each child's path, one per line.
Add the original's path to the optional-cleanup block.

### generalize / specialize
Edit the target file's frontmatter `genericity:` — generalize→`generic`, specialize→`specific`. If `dest.scope` differs from the file's current `scope`, RELOCATE (Write at the new scope key + archive + tombstone old — see drop).

### deprecate
Edit the target file: insert `> ⚠ DEPRECATED <today> — <rationale>` right after the frontmatter; add `deprecated: <today>` under `metadata:`; bump `last_updated`=today in the frontmatter. Keep the body.

### drop / retire
1. Read the source file. Write a COPY to `<archive>/<today>-<keyslug>-<source-filename>` — full frontmatter preserved + add `metadata.archived_from: <source-abs-path>` and `metadata.archive_reason: "<verb> — <rationale>"`.
2. Overwrite the SOURCE in place with the §7 tombstone: frontmatter `type: tombstone`, `dropped: <today>`, `archived: "<archive-path>"`, `reason: "<verb> — <rationale>"`; body = `DROPPED <today> — archived → <archive-path> (recover by copying back). Optional cleanup: rm <source-path>.`
3. Remove the source's line from `MEMORY.md` (Edit).
4. Add `<source-path>` to the optional-cleanup block.
NEVER attempt `rm`/unlink in-session (EROFS). The archive copy IS the preservation; the `rm` is the user's optional cleanup.

### promote-to-rule
Route by `proposed.dest.store` — this determines WHICH rulebook file receives the rule:
- `dest.store == claude.md` → edit `<ROOT>/CLAUDE.md`
- `dest.store == claude.local.md` → edit `<ROOT>/CLAUDE.local.md`

1. Edit the routed rulebook file: append the candidate `body` (the rule text) as a single line under the section named in `proposed.rationale` (default `## Behavioral Rules`), then append `<!-- meditate:rule id=<slug> src=<memory-name> -->` on the IMMEDIATELY FOLLOWING line (the line right after the rule text — no blank line between them). This two-line block (rule + marker) is the write unit. Dedup: if an equivalent rule line already exists, SKIP the append + note it. If the target section is absent → the edit FAILS (do not invent placement).
2. ONLY IF the rulebook edit succeeded → archive + tombstone the source (as in `drop`). If the edit FAILED → do NOT tombstone (the rule must land first); mark `failed(rulebook edit)`.
3. Add the appended rule text to the CLAUDE.md-review list in the report, noting which file was edited (`.md` or `.local.md`).

### demote-rule
Move a rulebook rule to a memory file (reverse of `promote-to-rule`). **Memory-first coupling:**

**Routing:** use `proposed.source_file` as the removal target — `CLAUDE.md` or `CLAUDE.local.md`. Do NOT hardcode `~/.claude/CLAUDE.md`. Resolve to `<ROOT>/CLAUDE.md` or `<ROOT>/CLAUDE.local.md` depending on `proposed.source_file`.

1. Write the memory `<created>-<type>_<slug>.md` (§4.1 frontmatter; body = `candidate.body` (the rule text) + "Demoted from <source_file> <today>"; `created`=today, `last_updated`=today). Append the `MEMORY.md` index line.
2. **Only if (1) succeeded** → Edit the file indicated by `proposed.source_file` to remove the rule block:
   - The removal unit is the two-line block: the rule text line + the `<!-- meditate:rule id=<slug> src=… -->` marker on the immediately following line. Remove both lines as a unit.
   - If the marker `<!-- meditate:rule id=<slug> … -->` is present on the line IMMEDIATELY following the rule text → use marker as the anchor (exact marker match; remove the rule line + the marker line).
   - Else → exact-match `candidate.body` (the rule text for a demote-rule candidate); remove that line only.
   - **No match found (neither marker+rule block nor exact rule text) → SKIP the rulebook edit.** Report:
     `demote-rule PARTIAL: memory written, <source_file> line not found — rule still present, NO data lost, resolve manually`.
   - **NEVER fuzzy-match. NEVER guess-remove.**
3. The safe-partial state (rule in both memory + rulebook) is intentional and auditable. The forbidden state (removed-but-not-saved) is impossible by this ordering.

Add to optional-cleanup block if memory written. Add rule text to `CLAUDE.md review` list in report (so the human can verify the removal), noting which file (`CLAUDE.md` or `CLAUDE.local.md`) was the target.

## Error handling
- Manifest unparseable → STOP, report the error, zero changes.
- Unknown manifest `schema_version` → STOP, report, zero changes.
- Hash mismatch on optimistic lock → `skip(hash mismatch)` that candidate; continue the rest (per-item, not abort-all).
- Per-candidate failure (unknown verb, bad dest, serena activation fails, merge Edit anchor not found) → mark `skip/failed(reason)`, continue the rest, surface all in the report. Never half-apply silently.
- Idempotency: re-running an already-applied manifest is safe. A completed `drop`/`retire`/`combine`/`split`/cross-key-`promote` leaves the source as a tombstone, so step 2c's lock recompute mismatches — but the tombstone-aware branch (2c) recognizes it via the matching `archived:` path and reports `already applied (tombstone verified)` rather than a misleading hash mismatch. A `promote` whose dest exists is reported `exists — skipped` (no clobber).
- Mid-verb crash recovery (`split`/`combine`): if a crash lands AFTER children/result are written but BEFORE the original is tombstoned, a re-run's split/combine pre-flight will hit `fail(path collision)` on the already-written children/result — this is a SAFE stop (nothing is lost; the original is still live and indexed). Resolve by hand: delete the orphaned children/result (they are re-derivable) and re-run, or finish the tombstone+index manually. Do NOT auto-resume — a dumb applier must not guess which half completed.
- promote-to-rule coupled-safety: the rulebook edit must succeed before its source is tombstoned.
- demote-rule coupled-safety: the memory write must succeed before the rulebook edit is attempted.
- New horizontal-verb failure modes (all per-item — a per-item failure never aborts the rest of the
  manifest — except the law-1 step-0 case, which fails only the specific candidates involved, not the
  whole manifest either):
  - `fail(cross-candidate reference)` — step 0 finds a candidate whose `combine_sources`, `link_to`, or
    amend target references a path another candidate creates or destroys (law 1 clause b), or a path that
    is the subject of more than one candidate (law 1 clause a). Fails BOTH the referencing/duplicate
    candidate and the candidate it collides with; every other candidate proceeds. The only failure mode
    that spans more than one candidate.
  - `fail(path collision)` — a `split` child or `combine` result path collides with an existing file (or,
    for `split`, with the original's own path or a sibling child's path). Hard fail, no clobber, never
    `exists — skipped`.
  - `needs-human(serena-store horizontal)` — a `link`/`amend`/`combine`/`split` candidate targets
    `store: serena`. Horizontal verbs are claude-store only in v1; route to needs-human, do not execute.
  - `fail(endpoint missing or tombstoned)` — any referenced path (a `link` endpoint, the `amend` target,
    any `combine_sources` entry, the `split` original, or a `merge` `source_path`/`dest.path`) does not
    exist or has `type: tombstone`.
  - `needs-human(serena merge)` / `needs-human(cross-key merge)` — a `merge` whose endpoints are
    serena-store, or whose `source_path` and `dest.path` live in different memdirs. v1 merge is
    claude-store, same-key only; route to needs-human, do not execute.
  - `fail(anchor pre-scan)` — an `amend` candidate has at least one `patch.anchor` that does not
    exact-match the current file. Zero edits are made — the whole candidate is left untouched.
  - `fail(source hash mismatch)` — the `combine` dedicated lock loop finds any ONE `combine_sources[i]`
    whose live hash no longer matches its recorded `content_hash`. Fails the whole candidate.
  - `fail(cap exceeded)` — a `combine` candidate lists more than 4 sources.
  - `fail(missing severed_dependency)` — a `split` candidate's `proposed.severed_dependency` field is
    absent (not even an explicit `none`).
  - `fail(no dest key)` — a cross-key `promote`, or a `split` child landing outside the source's key, has
    no `proposed.dest.key`.

## Report (always, at the end)

- **Done / Skipped / Failed** — one line per candidate (+ reason for skip/fail).
- **Per-verb counts** — alongside Done/Skipped/Failed, report per-verb totals: children written (`split`),
  sources archived + tombstoned (`combine`), bidirectional link pairs added (`link`), and pre-images
  archived (`merge`, `amend`).
- **Optional cleanup** — a ```bash``` block of `rm <abs-path>` for every tombstoned source (run in a normal OS terminal; non-urgent — all content is archived).
- **CLAUDE.md review** — the rule text appended by any `promote-to-rule`, and rule text removed (or attempted) by any `demote-rule` (re-read the diff).
