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

## `exclude` cannot name a nested path, and it made five repos move their own files

`build.py:135` walks the plugin root one level deep and `exclude` matches a name in that listing.
A plugin cannot keep `skills/*/evals/` or `packages/<name>/tests/` out of the build.

That broke Foundry's promise. Converting the plugins moved their files to fit the tool:

| Repo | Moved |
|---|---|
| manifold | `packages/manifold/tests/` to `tests/`, 28 files. `skills/manifold/evals/` to `evals/` |
| crucible | `skills/consult/evals/` to `evals/consult/` |
| review-library | `skills/hats/evals/` and `skills/red-vs-blue/evals/` to `evals/` |
| meditate | `skills/apply/tests/` to `tests/apply/` |
| plan-orchestrator | `scripts/progress` to `bin/progress`, because `scripts` is excluded wholesale |

A plugin brings what it has and Foundry builds it. Teach `exclude` to name a nested path, then put
all five layouts back.

## Pull request 14 is the templating language and it does not merge

It adds `docs/adr/0004-templating-binds-at-build-time-and-at-runtime.md`. Merging pull request 16
put a different `0004` on main, so two decisions claim the number, and both pull requests edit
`CLAUDE.md`. Renumber and resolve, then integrate the branch.

Two things block every line of templating code and both are Pi's alone:

- the real name of the language. `Pattern` is a placeholder. It sets the module name, the manifest
  key, and every message the resolver prints
- the two file extensions. `SKILL.pattern.md` and `SKILL.md` are placeholders, and changing them
  renames a file in every plugin that adopts this

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
lists are frozen, and `tests/scripts/test_resolve.py:61` asserts them by hand. So reversing it needs
its own decision record and moves every pin that exists. The workaround holds meanwhile: never build
into the tree.

## Six plugin repositories have no remote

review-library, crucible, plan-orchestrator, devtools, meditate and manifold are converted, clean,
and local only. None has CI. Foundry still carries their wiki pages and their issues.
