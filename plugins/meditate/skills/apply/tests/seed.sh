#!/usr/bin/env bash
# Build a scratch sandbox store + a self-consistent fixture manifest for meditate:apply tests.
# Nothing here touches the live store / CLAUDE.md — everything lives under ROOT.
#
# Usage:   seed.sh [ROOT]          (default: ${TMPDIR:-/tmp}/meditate-apply-test)
# Produces:
#   $ROOT/projects/<slug>/memory/...   seeded v2 memory files + MEMORY.md
#   $ROOT/CLAUDE.md                    rulebook (a marked rule for demote-rule + a section for promote-to-rule)
#   $ROOT/backups/memory-archive/      archive dir
#   $ROOT/fixture.md                   the approved manifest (schema_version 2, candidates:, REAL hashes)
#
# Then:    bin/meditate-manifest validate "$ROOT/fixture.md"      # must exit 0
#          /meditate:apply --sandbox "$ROOT" "$ROOT/fixture.md"   # agent-driven; assert per NOTE.md
#
# Verb coverage: keep, drop, deprecate, generalize, amend, promote-to-rule, demote-rule (7 of 14).
# NOT yet fixtured (need distinct seeds / an under-specified path resolved first): merge (2-way dest,
# finding M4), split, combine, link, promote (cross-key), specialize, retire. See NOTE.md.
set -euo pipefail

ROOT="${1:-${TMPDIR:-/tmp}/meditate-apply-test}"
BIN="$(cd "$(dirname "$0")/../../../bin" && pwd)"     # plugins/meditate/bin
SLUG="-sandbox-home"
M="$ROOT/projects/$SLUG/memory"

rm -rf "$ROOT"
mkdir -p "$M" "$ROOT/backups/memory-archive"

ch() { "$BIN/meditate-lock" "$1" | awk '/^content_hash:/{print $2}'; }
mt() { "$BIN/meditate-lock" "$1" | awk '/^mtime:/{print $2}'; }

mem() {  # mem <filename> <genericity> <body-line>
  cat > "$M/$1" <<EOF
---
name: ${1%.md}
metadata:
  created: 2026-06-01
  type: reference
  scope:
    depth: 1
    role: repo
  genericity: $2
  schema_version: 2
  last_updated: 2026-06-01
---
$3
EOF
}

# ── seed one memory file per verb under test ─────────────────────────────────
mem "2026-06-01-reference_keep_me.md"       generic  "A fact worth keeping as-is."
mem "2026-06-02-reference_drop_me.md"        generic  "Ephemeral note to be dropped."
mem "2026-06-03-reference_deprecate_me.md"   generic  "A fact that is now stale."
mem "2026-06-04-reference_generalize_me.md"  specific "A pattern that is actually portable."
mem "2026-06-05-reference_rule_shaped.md"    generic  "always run tests before pushing"
# merge: two same-cell items — the source (loser) folds INTO the dest (winner)
mem "2026-06-08-reference_merge_from.md"     generic  "Deploy uses 'make ship'."
mem "2026-06-09-reference_merge_into.md"     generic  "Deploy is done by the release owner."

# amend target — carries a verbatim stale line we patch by exact anchor
cat > "$M/2026-06-06-reference_amend_me.md" <<'EOF'
---
name: amend_me
metadata:
  created: 2026-06-06
  type: reference
  scope:
    depth: 1
    role: repo
  genericity: generic
  schema_version: 2
  last_updated: 2026-06-06
---
Deploy command: make deploy-old
EOF

# MEMORY.md index
cat > "$M/MEMORY.md" <<'EOF'
# Memory Index
- [Keep me](2026-06-01-reference_keep_me.md) — kept as-is
- [Drop me](2026-06-02-reference_drop_me.md) — ephemeral
- [Deprecate me](2026-06-03-reference_deprecate_me.md) — stale
- [Generalize me](2026-06-04-reference_generalize_me.md) — portable
- [Rule shaped](2026-06-05-reference_rule_shaped.md) — promote to rule
- [Amend me](2026-06-06-reference_amend_me.md) — deploy cmd
- [Merge from](2026-06-08-reference_merge_from.md) — folds into merge_into
- [Merge into](2026-06-09-reference_merge_into.md) — merge winner
EOF

# rulebook: a section header for promote-to-rule + an existing MARKED rule for demote-rule
cat > "$ROOT/CLAUDE.md" <<'EOF'
# Sandbox CLAUDE.md

## Behavioral Rules
- always review the diff before committing
- prefer ripgrep over grep for code search
<!-- meditate:rule id=prefer-ripgrep src=reference_ripgrep_rule -->
EOF

# ── compute REAL locks and emit the fixture manifest ─────────────────────────
keep="$M/2026-06-01-reference_keep_me.md"
drop="$M/2026-06-02-reference_drop_me.md"
depr="$M/2026-06-03-reference_deprecate_me.md"
genz="$M/2026-06-04-reference_generalize_me.md"
rule="$M/2026-06-05-reference_rule_shaped.md"
amnd="$M/2026-06-06-reference_amend_me.md"
mfrom="$M/2026-06-08-reference_merge_from.md"
minto="$M/2026-06-09-reference_merge_into.md"

cat > "$ROOT/fixture.md" <<EOF
---
schema_version: 2
curated: 2026-07-05
curator: meditate:curator
serena_available: false
---

# Meditate Apply Fixture (sandbox)

Approve = leave; reject = delete block; then: /meditate:apply --sandbox $ROOT $ROOT/fixture.md

\`\`\`yaml
candidates:
  - id: keep_me
    scope: {depth: 1, role: repo}
    genericity: generic
    store: claude
    type: reference
    source_path: $keep
    content_hash: $(ch "$keep")
    mtime: $(mt "$keep")
    file_schema_version: 2
    proposed:
      verb: keep
      rationale: still true and correctly placed

  - id: drop_me
    scope: {depth: 1, role: repo}
    genericity: generic
    store: claude
    type: reference
    source_path: $drop
    content_hash: $(ch "$drop")
    mtime: $(mt "$drop")
    file_schema_version: 2
    proposed:
      verb: drop
      rationale: ephemeral, recoverable from context

  - id: deprecate_me
    scope: {depth: 1, role: repo}
    genericity: generic
    store: claude
    type: reference
    source_path: $depr
    content_hash: $(ch "$depr")
    mtime: $(mt "$depr")
    file_schema_version: 2
    proposed:
      verb: deprecate
      rationale: superseded, keep the trail

  - id: generalize_me
    scope: {depth: 1, role: repo}
    genericity: specific
    store: claude
    type: reference
    source_path: $genz
    content_hash: $(ch "$genz")
    mtime: $(mt "$genz")
    file_schema_version: 2
    proposed:
      verb: generalize
      genericity_op: generalize
      dest: {scope: {depth: 1, role: repo}, store: claude}
      rationale: pattern is company-portable

  - id: amend_me
    scope: {depth: 1, role: repo}
    genericity: generic
    store: claude
    type: reference
    source_path: $amnd
    content_hash: $(ch "$amnd")
    mtime: $(mt "$amnd")
    file_schema_version: 2
    proposed:
      verb: amend
      patch:
        - anchor: "Deploy command: make deploy-old"
          replacement: "Deploy command: make deploy"
      rationale: deploy target renamed

  - id: rule_shaped
    scope: {depth: 1, role: repo}
    genericity: generic
    store: claude
    type: reference
    body: "always run tests before pushing"
    source_path: $rule
    content_hash: $(ch "$rule")
    mtime: $(mt "$rule")
    file_schema_version: 2
    proposed:
      verb: promote-to-rule
      dest: {scope: {depth: 0, role: home}, store: claude.md}
      rationale: "## Behavioral Rules"

  - id: demote_prefer_ripgrep
    scope: {depth: 0, role: home}
    genericity: generic
    store: claude.md
    type: reference
    body: "prefer ripgrep over grep for code search"
    file_schema_version: 2
    proposed:
      verb: demote-rule
      source_file: CLAUDE.md
      dest: {scope: {depth: 1, role: repo}, store: claude}
      rationale: situational, better recalled than always-on

  - id: merge_from
    scope: {depth: 1, role: repo}
    genericity: generic
    store: claude
    type: reference
    source_path: $mfrom
    content_hash: $(ch "$mfrom")
    mtime: $(mt "$mfrom")
    dest_content_hash: $(ch "$minto")
    dest_mtime: $(mt "$minto")
    file_schema_version: 2
    proposed:
      verb: merge
      dest: {path: $minto, scope: {depth: 1, role: repo}, store: claude}
      result_body: "Deploy: the release owner runs 'make ship'."
      rationale: fold the command detail from merge_from into merge_into (the owner note)
\`\`\`

## needs-human
(none this run)
EOF

echo "sandbox + fixture ready:"
echo "  store:    $M"
echo "  rulebook: $ROOT/CLAUDE.md"
echo "  manifest: $ROOT/fixture.md"
echo
echo "validate with: $BIN/meditate-manifest validate $ROOT/fixture.md"
