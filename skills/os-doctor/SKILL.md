---
name: os-doctor
description: Read-only health check for Pi's LifeOS vault at ~/LifeOS. Scans for PARA violations, missing frontmatter, broken cross-references, max-3-active-projects rule, naming inconsistencies. Outputs a dated report to 02-Areas/tool-stack/os-doctor-YYYY-MM-DD.md. Trigger on "check the vault", "vault health check", "audit the vault", /os-doctor, or as part of the weekly review ritual.
---

<!-- foundry:dependencies:start -->
## Dependencies

Registry: [`manifest.yaml`](../manifest.yaml) · refresh: `python3 scripts/skills_manifest.py sync-docs`

| Kind | Skills | Role |
|------|--------|------|
| — | — | No manifest dependencies |

<!-- foundry:dependencies:end -->

# OS Doctor

Pure read-only audit of `~/LifeOS`. Never modifies the vault. Outputs a single dated report. Pi runs this during weekly review or on demand.

## Hard rules

1. **Read only.** Never edit, move, or delete anything in `~/LifeOS`. The only thing this skill writes is the report file at `~/LifeOS/02-Areas/tool-stack/os-doctor-YYYY-MM-DD.md`.
2. **Fast.** Should complete in under 30 seconds for a vault of this size. Use Glob and Grep heavily; only Read files you need to inspect (frontmatter, link content).
3. **Report, don't fix.** Every violation gets a "suggested action" line, but Pi decides.
4. **Skip `00-Inbox/apple-notes-raw/`.** That folder has its own processing project; don't audit it for naming.

## Process

### 1. Inventory

Use Glob to enumerate:
- All `_PROJECT.md` files under `01-Projects/`
- All `_AREA.md` files under `02-Areas/`
- All folders under `01-Projects/`, `02-Areas/`, `03-Resources/`, `04-Archive/`
- All files at `00-Inbox/` root (excluding `apple-notes-raw/` subfolder)

### 2. Run checks

Use Read to extract YAML frontmatter from each `_PROJECT.md` / `_AREA.md`. Parse the block between leading `---` markers.

#### Flow checks
- **Active project count** — count `status: active` across all `_PROJECT.md`. Flag if > 3, list the active set.
- **Closed projects in 01-Projects** — any `status: closed` project still in `01-Projects/`. Suggest move to `04-Archive/projects/<name>/`.
- **Stale inbox** — files in `00-Inbox/` (root only) older than 14 days. Use file mtime. Suggest review.
- **Empty PARA folders** — any folder under `01-Projects/`, `02-Areas/`, `03-Resources/` with no `.md` files.

#### Structure checks
- **Project without `_PROJECT.md`** — folder under `01-Projects/` lacking `_PROJECT.md`.
- **Loose project `.md` at `01-Projects/` root** — any `.md` at root that doesn't start with `_` (the always-folders rule). `_PARKED.md`, `_TEMPLATE.md` are exempt.
- **Area without `_AREA.md`** — folder under `02-Areas/` lacking `_AREA.md`.

#### Metadata checks
- **Missing frontmatter** — `_PROJECT.md` without YAML frontmatter, or missing required fields: `status`, `created`, `updated`, `done_definition`, `sensitivity`. For `_AREA.md`: `type`, `last_tended`.
- **Invalid status value** — `status` not in [`active`, `scoping`, `parked`, `paused`, `closed`].
- **Stale `updated` field** — `updated` more than 30 days behind today AND `status: active`. Suggests project may not actually be active.
- **Parked without `why_parked`** — `status: parked` but `why_parked` field empty or missing.
- **Last-tended drift on areas** — `last_tended` more than 30 days behind today.

#### Reference checks
- **Broken vault-relative links** — markdown links of shape `01-Projects/...`, `02-Areas/...`, `03-Resources/...`, `04-Archive/...` that point to nonexistent paths. Use Grep to find link patterns. Skip files in `00-Inbox/` (historical).
- **References to archived files in active files** — non-inbox file references a path under `04-Archive/`. Suggest review.

#### Naming checks
- **Non-conforming inbox names** — files in `00-Inbox/` (root) not matching `YYYY-MM-DD-*.md` or `_*.md`.

### 3. Write report

Write to `~/LifeOS/02-Areas/tool-stack/os-doctor-YYYY-MM-DD.md`. If a report for today already exists, overwrite it.

Format:

```markdown
# OS Doctor Report — YYYY-MM-DD

## Summary
- Total violations: N
- Categories with issues: M / 5
- Top 3 most-urgent: ...

## Flow
| Check | Result | Suggested action |
|---|---|---|
| Active project count | N (limit 3) | ... |
| Closed in 01-Projects | N | ... |
| Stale inbox (>14d) | N files | ... |
| Empty PARA folders | N | ... |

## Structure
| Check | Result | Suggested action |
|---|---|---|

## Metadata
| Check | Result | Suggested action |
|---|---|---|

## References
| Check | Result | Suggested action |
|---|---|---|

## Naming
| Check | Result | Suggested action |
|---|---|---|

## Suggestions in execution order
1. ...
2. ...
```

When a check has zero violations, still include the row with `result: ✓ clean` for confidence. Don't omit.

### 4. Surface to Pi

After writing the report, summarize in chat:
- Top 3 most-urgent items
- Total violation count
- Path to the full report

Do not propose execution. The weekly review ritual handles that.

## What's out of scope (v1)

- Auto-fixing anything
- Tracking trends across runs
- Apple Notes raw folder analysis
- Resources taxonomy (too thin to bother)
- Cross-vault analysis (only `~/LifeOS`)

## Conventions reference

The full convention spec lives at `~/LifeOS/04-Archive/projects/vault-cleanup/01-conventions.md`. If a check here disagrees with that file, that file wins — update this skill.
