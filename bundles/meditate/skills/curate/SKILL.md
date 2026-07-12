---
name: curate
description: >-
  Dispatch the meditate:curator Opus agent to sweep the memory store + CLAUDE.md (+ serena if active),
  then write the proposed-disposition manifest to a timestamped path for human review and /meditate:apply.
---

# meditate:curate — the plan step

Run the full memory-curation sweep: pre-flight serena → dispatch the read-only curator agent →
extract the fenced-yaml manifest → write it to a timestamped file → tell the human where to review
and how to apply.

## Pre-flight: check serena availability

Attempt `mcp__plugin_serena_serena__get_current_config`:
- **Success** → set `serena_available: true`.
- **Tool-not-found / any error** → set `serena_available: false`.

## Read curate targets

Read `${CLAUDE_PLUGIN_ROOT}/config/targets.yaml` (use Read tool or Bash `cat`). If a user override at
`~/.claude/meditate/targets.yaml` exists, prefer it. Parse the `targets:` list. If neither file is
readable → abort with:
`Error: targets.yaml not found. Copy config/targets.example.yaml to config/targets.yaml (opt-in, home key only) before running /meditate:curate.`

Each entry has: `key` (an **absolute path**), `rulebook` (a list of paths, possibly tilde-prefixed),
and `serena_project` (string or null).

Define the key-resolution helpers once, up front, so the guard and the memdir resolver match the
abs-path `key` form (self-contained — no external lib to source):

```bash
# slug resolution delegates to the shared helper (single source of truth for the slug rule):
memkey_slug()       { "${CLAUDE_PLUGIN_ROOT}/bin/meditate-slug" "$1"; }
memkey_memdir()     { printf '%s\n' "${HOME}/.claude/projects/$(memkey_slug "$1")/memory"; }
memkey_is_worktree(){ case "$1" in */.worktrees/*) return 0 ;; *) return 1 ;; esac; }
```

For each entry in `targets:`, resolve its memory dir and apply the **worktree/tmp guard** before
adding it to the active scope. Note `key` is an absolute path, so `memkey_is_worktree` (which matches
`*/.worktrees/*`) lines up with the key form — a slug-form key would never match and the guard would
silently fail:

```bash
key="<entry.key>"                       # absolute path, e.g. $HOME or a repo dir
# Worktree/tmp guard (DG-P3-2) — backstop to the opt-in list. memkey_is_worktree matches the
# abs-path key form (*/.worktrees/*); add the /tmp check inline since the helper above only covers worktrees.
case "$key" in /tmp/*|/private/tmp/*|/var/tmp/*|/var/folders/*) is_tmp=1 ;; *) is_tmp=0 ;; esac
if memkey_is_worktree "$key" || [ "$is_tmp" = 1 ]; then
  echo "WARNING: skipping worktree/tmp key '$key' (targets.yaml should never list these)."
  continue
fi
memdir="$(memkey_memdir "$key")"        # -> $HOME/.claude/projects/<slug>/memory
```

`memkey_memdir` slugifies the abs-path `key` via `bin/meditate-slug` and returns
`$HOME/.claude/projects/<slug>/memory` — so the memory dir is **derived from `key`**, not stored
separately. The canonical slug rule (decisions log, verified live at Claude Code v2.1.195) is
`sed 's|[/.]|-|g'`: `/` and `.` become `-`, and **`_` is preserved** (e.g.
`/home/user/projects/foo_bar` → `-home-user-projects-foo_bar`). `meditate-slug` also self-verifies
against `~/.claude/projects/` and falls back to a legacy underscore-replacing slug when a store
predates this rule, so an underscore-bearing key resolves to the right memdir on any vintage of the
store. (Primary safety is the opt-in list itself; the worktree/tmp guard is the belt-and-suspenders
backstop.)

The active sweep scope = the resolved `memdir`s + the rulebooks from the surviving (non-skipped) entries.

## Dispatch the curator agent

Dispatch `meditate:curator` with:
- Mode: `sweep` (store-wide periodic sweep, not a harvest manifest).
- Scope: the targets list from `targets.yaml` (after guard). For each surviving target, pass:
  - The resolved memory directory `memdir` (from `memkey_memdir "$key"`).
  - The rulebook files listed in `rulebook:` — **expand any leading `~` to `$HOME`** before testing
    existence or reading (a literal `~` is not expanded by Bash inside a variable, so an existing
    file would look missing and be silently skipped). Use either form:
    ```bash
    rb="${rb/#\~/$HOME}"          # expand a leading ~ to $HOME
    [ -f "$rb" ] && pass_to_curator "$rb"   # skip a rulebook path that does not exist
    ```
  - The `serena_project:` value (pass as-is; null = no serena audit for this target).
- Pass `serena_available: <true|false>` explicitly so the curator knows whether to attempt serena tools.
- The curator reads the authority docs itself from `${CLAUDE_PLUGIN_ROOT}/docs/` (the interface
  contract + planner-handoff + decisions log).

## Extract the manifest

The curator returns its output ending with ONE fenced ```yaml``` block whose top-level key is
`candidates:` (a list — the interface-contract §3 manifest shape). Write the curator's raw output to
a temp file and extract that block with the shared helper (it prints the block verbatim to stdout,
uv/parse noise to stderr):

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/meditate-manifest" extract "$curator_output_file"
```

If it exits non-zero (no fenced block found) → report the error, print the curator's raw output,
and stop (do not write an empty manifest).

The curator's output also carries prose **outside** the fenced yaml block — don't let it be
silently dropped the way it used to be (the manifest template had no slot for it, and
`/meditate:review` reads a hole where its needs-human step expects content). Scan the raw output
for whichever of these sections the curator emitted, each introduced by its own heading: `Summary
table`, `Rules-for-human`, `Contradictions` / `Contradictions/demotions`, `needs-human`, `Clusters`.
Extract each one verbatim — from its heading through to the next heading or the yaml fence,
whichever comes first. A section the curator didn't emit this run is simply absent; do not
fabricate an empty one.

## Post-attach content_hash + mtime (per candidate)

After extracting the fenced yaml block, iterate each candidate block in the proposals list. For
each candidate that carries a `source_path:` field, run the following Bash to compute and inject
`content_hash` and `mtime`:

```bash
source_path="<candidate.source_path>"
if [ -f "$source_path" ]; then
  # meditate-lock prints two YAML-ready lines: `content_hash: <hex>` and `mtime: <epoch>`,
  # portably (sha256sum||shasum, GNU||BSD stat). Inject both as siblings of source_path.
  "${CLAUDE_PLUGIN_ROOT}/bin/meditate-lock" "$source_path"
else
  echo "WARNING: source_path not found for candidate '<id>': $source_path — skipping hash."
fi
```

Inject `content_hash: <hex>` and `mtime: <epoch>` as sibling fields of `source_path` in the
candidate's yaml block (not inside `proposed:`). These feed the apply skill's optimistic lock:
before any write, the applier re-hashes the source and aborts that item if the hash has changed.

This default loop covers `keep`/`promote`/`generalize`/`specialize`/`deprecate`/`drop`/`retire`/
`promote-to-rule`/`demote-rule` as-is, and two of the four horizontal verbs need nothing extra:

- **`split`** — hash the candidate's top-level `source_path` only (the **original**). The
  `proposed.children` don't exist as files yet — never attempt to hash them.
- **`amend`** — hash the top-level `source_path` as usual; no extra fields.

The other two new verbs need hashing beyond the default loop:

- **`combine`** — has no single top-level `source_path`. Instead, for every `source_path` you read
  from the candidate's `combine_sources` list (these come from the parsed YAML — there is no bash
  array), run `meditate-lock` and inject its two lines into that `combine_sources[i]` entry,
  alongside its existing `source_path`/`scope`/`genericity`/`type`/`store` fields:

  ```bash
  # for each combine_sources[i].source_path read from the extracted YAML:
  if [ -f "$source_path" ]; then
    "${CLAUDE_PLUGIN_ROOT}/bin/meditate-lock" "$source_path"   # -> content_hash + mtime
  else
    echo "WARNING: combine_sources source not found for candidate '<id>': $source_path — skipping hash for this source."
  fi
  ```

- **`link`** — hash the top-level `source_path` (endpoint 1) via the default case, **and** resolve
  `proposed.link_to` (a slug, same-key v1 — resolved against the same memdir as `source_path`) to
  its file, then inject three sibling fields at the **candidate's top level** (not inside
  `proposed:`): `link_target_path`, `link_target_hash`, `link_target_mtime`.

  ```bash
  memdir="$(dirname "$source_path")"
  # Resolve link_to (a name-slug) to a file. Prefer a frontmatter `name:` match (the store's
  # [[...]] convention; the name-slug often differs from the filename slug — live-fire finding
  # 2026-07-03), handling quoted and unquoted values; fall back to the filename slug. Fail loudly
  # on ambiguity instead of silently taking the first match.
  link_target_path="$(grep -lE "^name: \"?${link_to}\"?\$" "$memdir"/*.md 2>/dev/null)"
  if [ "$(printf '%s\n' "$link_target_path" | grep -c .)" -gt 1 ]; then
    echo "WARNING: link_to slug '$link_to' is ambiguous in $memdir (multiple matches) — skipping link_target_* hash."
    link_target_path=""
  elif [ -z "$link_target_path" ]; then
    link_target_path="$(find "$memdir" -maxdepth 1 -name "*_${link_to}.md" | head -n1)"
  fi
  if [ -n "$link_target_path" ] && [ -f "$link_target_path" ]; then
    # meditate-lock prints content_hash/mtime — relabel them link_target_hash/link_target_mtime
    "${CLAUDE_PLUGIN_ROOT}/bin/meditate-lock" "$link_target_path"
  else
    echo "WARNING: link_to slug '$link_to' not found in $memdir for candidate '<id>' — skipping link_target_* hash."
  fi
  ```

- **`merge`** — hash the top-level `source_path` (the losing item) via the default case, **and** lock
  the dest: read `proposed.dest.path` (the absolute path of the existing winner), run `meditate-lock`
  on it, and inject its two lines at the **candidate's top level** relabelled as `dest_content_hash`
  and `dest_mtime` (siblings of `content_hash`/`mtime`, not inside `proposed:`). Apply re-verifies
  BOTH locks before it writes anything.

  ```bash
  dest_path="<candidate.proposed.dest.path>"
  if [ -f "$dest_path" ]; then
    # meditate-lock prints content_hash/mtime — relabel them dest_content_hash/dest_mtime
    "${CLAUDE_PLUGIN_ROOT}/bin/meditate-lock" "$dest_path"
  else
    echo "WARNING: merge dest.path not found for candidate '<id>': $dest_path — skipping dest lock."
  fi
  ```

If `source_path` is absent from a candidate (e.g. it was omitted by the curator), emit a warning
line in the report and leave `content_hash` / `mtime` absent for that candidate — do not abort
the whole run. The same applies to every hash target above: a missing original, a missing
`combine_sources[i]` file, or an unresolved `link_to` target each get a warning and are left with
their hash fields absent for that candidate — the applier will fail that candidate at apply time
over the missing lock, but a bad hash never aborts the curate run itself.

## Write the manifest file

Determine the manifest path — derive the home slug at runtime (never hardcode it):
```bash
home_slug="$("${CLAUDE_PLUGIN_ROOT}/bin/meditate-slug" "$HOME")"
manifest_dir="${HOME}/.claude/projects/${home_slug}/.meditate"
manifest_path="${manifest_dir}/curate-<YYYY-MM-DD-HHMM>.md"
```
Where `<YYYY-MM-DD-HHMM>` is the current timestamp (UTC). Create the `.meditate/` directory if it
does not exist (it is under `~/.claude/projects/`, which is agent-writable via the Write tool).

Write the manifest file with this structure:
```markdown
---
schema_version: 2
curated: <YYYY-MM-DD>
curator: meditate:curator
serena_available: <true|false>
---

# Meditate Manifest — <YYYY-MM-DD-HHMM>

Review each proposed disposition below. To approve: leave as-is. To reject: delete the candidate's
block. To modify: edit any `proposed:` field. When satisfied, run:

  /meditate:apply <this-file-path>

` ` `yaml
<extracted yaml block — the top-level `candidates:` mapping, verbatim from meditate-manifest extract>
` ` `

## Summary table
<verbatim — only if the curator emitted one>

## Rules-for-human
<verbatim — only if the curator emitted one>

## Contradictions/demotions
<verbatim — only if the curator emitted one>

## needs-human
<verbatim — only if the curator emitted one>

## Clusters
<verbatim — only if the curator emitted one>
```

Append the sections extracted in the previous step after the closing yaml fence, in the order
shown above, each verbatim under its own `## <heading>`. Omit any section the curator did not
emit for this run — never write an empty heading with no body underneath it.

## Report to the human

Print:
```
Curation complete.

Manifest written to:
  <manifest_path>

Review it (open the file, edit to approve/reject/modify), then run:
  /meditate:apply <manifest_path>

Summary: <N> candidates proposed (<M> promote, <K> merge, <J> drop, <L> demote-rule, <S> split,
  <C> combine, <Li> link, <Am> amend, ...).
Serena: <active — audited | skipped (inactive)>.
```
