# meditate:apply — sandbox test suite

`seed.sh` builds a self-consistent sandbox store **and** a fixture manifest whose locks are REAL
(computed from the seeded files via `bin/meditate-lock`), targeting the current `meditate:apply`
(schema_version 2, `candidates:` container, `{depth, role}` scopes, optimistic hash locks).

## Run

```bash
# 1. build the sandbox + fixture (defaults to ${TMPDIR:-/tmp}/meditate-apply-test)
bash seed.sh /path/to/sandbox

# 2. static check — schema + law-1 (runnable in CI; must exit 0)
../../../bin/meditate-manifest validate /path/to/sandbox/fixture.md

# 3. execution — agent-driven (apply is a prose skill, not a script):
#    /meditate:apply --sandbox /path/to/sandbox /path/to/sandbox/fixture.md
#    then assert the store per "Expected outcomes" below. Reads AND writes are rooted at the
#    sandbox; the live store / ~/.claude is never touched.
```

## Verb coverage

Fixtured (8 of 14): `keep`, `drop`, `deprecate`, `generalize`, `amend`, `promote-to-rule`,
`demote-rule`, `merge` — a no-op, a destructive archive+tombstone, an in-place banner, a fence
flip, a horizontal exact-anchor patch, both rulebook directions, and a 2-way fold. `merge` carries
`proposed.dest.path` + `proposed.result_body` and BOTH locks (`content_hash` on the source,
`dest_content_hash` on the dest).

The remaining verbs — `split`, `combine`, `link`, cross-key `promote` — are execution-proven by
their own scratch drivers (same seed pattern), and `specialize`/`retire` run the shared
generalize/drop handlers. All 14 verbs are execution-verified.

## Expected outcomes (assert after apply --sandbox)

- `keep_me` — unchanged (recorded "kept (no-op)").
- `drop_me` — overwritten to a `type: tombstone` stub; a copy under `backups/memory-archive/`;
  its `MEMORY.md` line removed; path added to the optional-cleanup `rm` block.
- `deprecate_me` — a `> ⚠ DEPRECATED …` banner after the frontmatter; `metadata.deprecated` set;
  body preserved.
- `generalize_me` — `metadata.genericity` flipped `specific → generic`.
- `amend_me` — `Deploy command: make deploy-old` → `make deploy`; pre-image archived; `last_updated`
  bumped.
- `rule_shaped` — rule text appended under `## Behavioral Rules` in the sandbox `CLAUDE.md` with a
  `<!-- meditate:rule … -->` marker, THEN the memory tombstoned (rule lands first — law 3).
- `demote_prefer_ripgrep` — a new memory written first, THEN the `prefer ripgrep …` rule + its
  marker removed from `CLAUDE.md`.
- Archives never clobber; every destructive op is recoverable from `backups/memory-archive/`.

## History

Replaces the legacy fixtures salvaged from the retired standalone `apply-curation` skill (removed
2026-07-05). Those predated `schema_version: 2`, the `candidates:` container, the optimistic
content-hash lock, and the horizontal verbs, and could not run against `meditate:apply`.
