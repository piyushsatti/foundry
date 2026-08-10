# TODO

Open work on Foundry. Each item says what is wrong and what the fix is, not how to do it.

## Rewrite every document once the shape is settled

`CLAUDE.md`, `README.md`, the wiki, `template/README.md` and `template/CLAUDE.md` are all long,
and length is the problem. They read as summaries of everything true about Foundry rather than as
something a person wrote for another person.

Rewrite each to fifteen or twenty lines: what it does, why it exists, how you install and use it.
Nothing else. Delete rather than condense. Do this after the items below settle, because the shape
they leave behind is what the documents describe.

Not the code. Only the prose.

## Five repositories are still holding a layout they only adopted to fit the old `exclude`

The tool half is done. `exclude` takes globs with negation, anchored to the top level unless the
pattern carries a slash, so `**/evals` and `packages/*/tests` are now one line each. What has not
happened is the five repositories undoing the moves they made when it could not.

| Order | Repo | Reverses | Writes |
|---|---|---|---|
| 1 | review-library | `evals/` back under `skills/hats/` and `skills/red-vs-blue/` | `**/evals` |
| 2 | crucible | `evals/consult/` back to `skills/consult/evals/` | `**/evals`, and repins review-library |
| 3 | plan-orchestrator | `bin/progress` back to `scripts/progress` | `scripts/*`, `!scripts/progress`, and repins review-library |
| 4 | manifold | 28 files back to `packages/manifold/tests/`, `evals/` back under `skills/manifold/` | `packages/*/tests`, `**/evals` |
| 5 | meditate | `tests/apply/` back to `skills/apply/tests/` | `**/tests` |

**Order is not a preference.** `crucible` and `plan-orchestrator` both pin `review-library`, so
moving its files moves its fingerprint and both refuse to build until they repin.

**`scripts/*` rather than `scripts`**, because gitignore cannot re-include a path whose parent
directory is excluded. Excluding the directory's children instead is expressible and does what
plan-orchestrator wants.

Each of these moves that plugin's own fingerprint, on purpose, and each takes a version bump its own
repository owns. None of it happens before Foundry is tagged, because a repository writing the new
patterns and then building against the old Foundry ships the directories it just restored, silently.

## Build Stencil, which is what 0.2.0 is for

**Targeted at 0.2.0**, ruled by Pi on 2026-08-09. Nothing here ships before that release, and that
release is named by it.

The decision landed and is accepted: `D4-Stencil-binds-at-build-time-and-on-the-users-machine` in
the wiki, and `Stencil` there carries the whole shape. The order of work is `docs/plans/stencil.md`.
Nothing is blocked any more, and six questions on that page are still open: a target names when it
ships, not what it decides.

- the language is **Stencil**
- a plugin author writes **`SKILL.stencil.md`**, and **`SKILL.md`** is rendered beside it. Both live
  in the installed folder, and the harness only ever reads the second
- it binds twice. `{{build.*}}` and `{{use skill.x}}` at build time. `{{env.*}}`, `has()` and
  `{{arg.*}}` on the machine the plugin is installed on, through two hooks the plugin ships
- the runtime half exists for one reason: whether a skill in another plugin is installed can only be
  known where both are installed, and a plugin's build may not look outside its own repository

## "Use this template" hands out the build tool

This repository is marked as a GitHub template, and GitHub copies a repository root. A generated
repo therefore has no `foundry.plugin.yaml` at its top, because the only one is in `template/`, and
it cannot build until someone lifts that directory up by hand.

Foundry is atomic, so the answer is not a second repository. It is unanswered. Until it is answered,
make a new plugin by copying `template/`.

## Delete the `foundry-template` repository

`piyushsatti/foundry-template` was created on 2026-08-09 in error, pushed and marked as a template.
It should not exist. Deleting it needs the `delete_repo` scope, which the local `gh` token does not
have: `gh auth refresh -h github.com -s delete_repo`.

## A build's own output sits inside the fingerprint

`SKIP_DIRS` in `resolve.py` has no `dist`, so a checkout that has been built into fingerprints
differently from a clean one, and a consumer pinning it then refuses on a pin that was correct when
written. Reproduced: review-library is `26ecf1ddadc0` clean, and both consumers pin that number.

Commit `0e8cbe0` considered this and deliberately went the other way, `CLAUDE.md` says the skip
lists are frozen, and `FingerprintIsFrozen` in `tests/scripts/test_resolve.py` asserts them by hand,
in `test_a_known_tree_still_hashes_to_the_digest_it_has_always_hashed_to`. So reversing it needs
its own decision record and moves every pin that exists. The workaround holds meanwhile: never build
into the tree.

## Six plugin repositories have no remote

review-library, crucible, plan-orchestrator, devtools, meditate and manifold are converted, clean,
and local only. None has CI. Foundry still carries their wiki pages and their issues.

## `docs/migrations/` does not exist, and a live refusal already names a file inside it

`check_foundry_major` in `resolve.py` refuses a build across a change to Foundry's first number and
sends the reader to `docs/migrations/foundry-<older>-to-<newer>.md`. That directory has never been
written, so the one refusal that cannot be worked around is also the one whose next step points at
nothing. A refusal with no next step is a bug by Foundry's own rule.

The first change to the first number creates the directory and that document, in the same change
that moves the number.

## Two hand-written JSON refusals are now unreachable

`translate_mcp` in `emitters/claude_code.py` and `check_mcp` in `emitters/agent_plugins.py` each
catch a JSON decode error on `mcp.json` and raise a proper refusal. Neither can run any more.
`declared_kinds` calls `mcp_servers` in `emitters/contract.py` before any emitter is reached, and
that now refuses an unreadable file itself, so the build always stops earlier.

They were unreachable before this too, by crashing rather than by refusing. Either delete both, or
give one of them a reason to exist that the earlier check does not already cover. Dead code in a
refusal path reads as a guard that is running.

## The pinned action majors are running on borrowed time

Every CI run now annotates itself:

    Node.js 20 is deprecated. The following actions target Node.js 20 but are
    being forced to run on Node.js 24: actions/checkout@v4, actions/setup-python@v5

Both lines are in `.github/workflows/ci.yml` and in the workflow copied by hand into every plugin
repository, so the day GitHub stops forcing is the day every one of those repositories goes red at
once, with nothing having changed in any of them. This is the most likely way Foundry breaks while
nobody is touching Foundry.

Moving to the next majors is one line each, but it is a change every plugin repository has to be
told about, which is the same cost the bootstrap stub carries. Do it deliberately, in one pass,
rather than one repository at a time.
