---
name: review
description: >-
  Render a pending curate manifest readably — disposition table, destructive-op flags, the
  ⚠ CLAUDE.md-changes line, and the needs-human decisions. Read-only + re-runnable. Defaults to the
  latest manifest if no path is given. Run it between /meditate:curate and /meditate:apply.
---

# meditate:review — the show step (terraform `show`)

Render an already-written curate manifest for human inspection before `/meditate:apply`.
**Read-only: never edit the manifest or any store — this step only displays.**

## Resolve the manifest
- Invoked with a path argument → use it.
- No argument → the **latest** `curate-*.md` (highest `YYYY-MM-DD-HHMM` timestamp in the filename)
  under the home key's `.meditate/` dir. Derive that dir at runtime — never hardcode the slug:
  ```bash
  manifest_dir="${HOME}/.claude/projects/$("${CLAUDE_PLUGIN_ROOT}/bin/meditate-slug" "$HOME")/.meditate"
  ```
- None found → print `No pending manifest. Run /meditate:curate first.` and stop.

Read the file. Parse: frontmatter (`curated`, `curator`, `serena_available`), the fenced ```yaml```
proposals block (top-level `candidates:` list), and — if present — the prose sections the curator
emits: `Summary table`, `Rules-for-human`, `Contradictions/demotions`, `needs-human`, `Clusters`.
(These five are the canonical set shared by curator output → curate persistence → this parser.)

## Render (in this order)

1. **Header** — manifest path · `curated` date · `serena: active | skipped`.

2. **Dispositions** — one row per yaml candidate:

   | id | verb | dest (scope/store) | genericity | conf | rationale |

   Pull `verb`, `dest.scope`/`dest.store`, `genericity` (append `→generic`/`→specific` when
   `genericity_op` is not `none`), confidence **from the candidate's own yaml `confidence` field —
   this is the single source of truth** (fall back to `—` only if the field is absent from that
   candidate), and the one-line `rationale`.

   The four new verbs render differently:
   - **`split`** — one parent row for the candidate itself (`id`, verb `split`, its dest/genericity/
     conf/rationale), plus one **indented** row per entry in `proposed.children`: that child's `id`
     and its dest cell (`scope`/`genericity`/`type`) — no separate conf/rationale, they inherit the
     parent's.
   - **`combine`** — one row for the result (`id` = `proposed.result.id`, dest/genericity from
     `proposed.result`, conf/rationale from the candidate), followed by a compact source list:
     `sources: <path1>, <path2>, … (N)` drawn from `combine_sources[].source_path`.
   - **`link`** — a normal single row; append `→ <link_to>` (from `proposed.link_to`) to the row.
   - **`amend`** — a normal single row; append the patch count, e.g. `(3 patches)`, from the length
     of `proposed.patch`.

3. **Destructive-op flags** — scan every candidate's verb; list each destructive op explicitly:
   - `drop` / `retire` → `🗑  archive + tombstone <id>` (recoverable from the archive).
   - `demote-rule` → `✂  CLAUDE.md rule REMOVED → memory <id>`.
   - `promote-to-rule` → `➕ CLAUDE.md rule ADDED ← memory <id>`.
   - `generalize`/`specialize` whose `dest.scope` ≠ the candidate's current `scope` → `↦  relocate <id> → <scope>`.
   - `split` → `✂→N  split <id> — original archived+tombstoned, N children written` (N = length of
     `proposed.children`).
   - `combine` → `⊕→1  combine <id> — N sources archived+tombstoned` (N = length of
     `combine_sources`).
   - `amend` → `✎  amend <id> — pre-image archived, in-place patch`.
   - `merge` → `⊕  merge <id> → <dest.path> — dest pre-image archived, source folded in + tombstoned`.
   - If none of the above → `Destructive ops: 0 — fully non-destructive (promote/keep/link only)`.

   `link` is **non-destructive** — never list it under destructive-op flags. Instead render it as
   its own informational line below the flag list (or in place of it, if it's the only op present):
   `🔗  link <id> ↔ <link_to>` — informational, does not count toward the "Destructive ops: N" total.

4. **CLAUDE.md change line** — always print:
   `⚠ CLAUDE.md changes: N (promote-to-rule M, demote-rule K)` (count from verbs).
   If N = 0 → `CLAUDE.md changes: 0`.

5. **needs-human** — echo the manifest's `needs-human` section verbatim. These are **decisions, not
   apply-able verbs** — the human acts on them separately (the applier will not touch them).

6. **Persisted prose sections** — echo each of the following, verbatim under its own heading, in
   this order, exactly like `needs-human` above; omit any that the manifest doesn't carry (curate
   only persists the sections the curator actually emitted):
   - `Rules-for-human`
   - `Contradictions/demotions`
   - `Clusters`

7. **Summary** — `<N> candidates: <per-verb breakdown>`, plus the `⚠ CLAUDE.md changes` count from
   step 4 (there is no separate "CLAUDE.md audit" section — the curator does not emit one).

## Close — how to proceed
```
To approve: leave the candidate's block as-is.
To reject:  delete the candidate's block from the manifest.
To modify:  edit any `proposed:` field.
Then:       /meditate:apply <manifest-path>

(review is read-only + re-runnable — safe to re-run after editing the manifest.)
```

**Do NOT edit the manifest or any store. Display only.** If the manifest has zero apply-able verbs
(all `keep`), say so plainly: `/meditate:apply` would be a no-op; the value is in needs-human.
