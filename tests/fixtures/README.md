# tests/fixtures/

Small, real plugin repositories that `.github/checks/repos.py` builds and checks against a recorded
baseline, the same way it builds the plugin repositories that live beside Foundry on this machine.
They exist so that check has cases that do not depend on this machine having those repositories, and
so the `exclude` work landing next has something concrete to be proved against.

| Fixture | Carries |
|---|---|
| `nested-skill-tests` | A `skills/<name>/SKILL.md` plus a `skills/<name>/tests/` directory, and a top-level `tests/` directory. Today's `exclude: [tests]` matches the top-level one only |
| `package-tests` | A `packages/<name>/tests/` directory, plus a top-level `tests/`. `packages/` is not one of Foundry's four content directories, so it ships as an ordinary top-level directory |
| `negation` | A `scripts/` directory holding two entries, excluded whole today. A future `!` pattern would re-include one of them on its own |
| `precedence` | A path two future exclude patterns would both match, so the order they are applied becomes observable once that syntax exists |

Every fixture builds clean against today's code and is baselined like any other repository
`repos.py` builds. None of them assert anything about a glob or a negation, because that syntax does
not exist yet: `exclude` today matches a flat top-level name and nothing else. Each fixture's job
right now is to be a recorded starting point, so that the day glob and negation land, the change in
what these four repositories build is visible instead of silent.

Do not add an assertion here about behavior `exclude` cannot perform yet. Add the fixture, let
`repos.py --record` capture what it builds today, and leave the assertion to whoever builds the
feature.
