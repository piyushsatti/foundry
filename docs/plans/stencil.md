# Plan: templating in Foundry

The decision and its reasoning are in the wiki, at `D4-Stencil-binds-at-build-time-and-on-the-users-machine`,
and the whole shape is on the `Stencil` page beside it. This file is the order of work and the blast
radius. Nothing here restates the argument.

## What is being built

| Piece | Lands in | Shape |
|---|---|---|
| The resolver | `scripts/` | One module, standard library only, two entry points: one per stage |
| The build stage call | `scripts/build.py` | One call, between `copy_dependency_content` and `check_provides` |
| The runtime stage script | `template/` and the plugin's own folder | A file the plugin ships and its own hooks run |
| Rule tests | `tests/scripts/` | Refusals checked by message text, as every other rule in this repository is |
| Template wiring | `template/` | The two hook rules, and whatever the manifest needs to say a plugin uses this |

It does not land in a new repository. It is base tooling by the test in `CLAUDE.md`: someone
building a completely unrelated plugin needs it. It is part of Foundry 0.1.0.

## Named, so the work can start

Both decisions that gated every file are answered. Pi named them on 2026-08-09.

| Was blocked on | Answer |
|---|---|
| The real name of the language | **Stencil.** It sets the module filename, the manifest key, and every message the resolver prints |
| What the two files are called | The source a plugin author writes is **`SKILL.stencil.md`**. The file the harness reads stays **`SKILL.md`**, written beside it. `.stencil` sits before `.md` so the source is still markdown to every editor, linter and diff |

Both files live in the installed folder. The source is never consumed, so the resolver can run again
on every session and a changed environment re-renders correctly.

## Order of work

Each phase has a gate. A phase does not start until the gate above it is green.

| # | Phase | Gate |
|---|---|---|
| 1 | Port the lab resolver into `scripts/`, build stage only, with its tests | `python3 -m unittest discover -s tests` green, `uvx ruff check` clean |
| 2 | Attach the build stage in `build.py` at the one position the wiki's `Stencil` page fixes, after `copy_dependency_content` and before `check_provides` | `python3 scripts/build.py template --check` prints the same five fingerprints it prints today, because the template holds no templates |
| 3 | Prove a template that resolves at build time and a plain file produce the same bytes when the template has no constructs | A test asserting byte-identity, so adopting the source extension on a file with no holes moves no fingerprint |
| 4 | Runtime stage: the resolver's second entry point, and the script a plugin ships | Tested against a fixture plugin repo written by `tests/repos.py` |
| 5 | The two hook rules in `template/`, and the loss policy for the five harnesses with no `hooks` entry | The build refuses, or degrades, and says which. Test by message text |
| 6 | Documentation: `CLAUDE.md` invariant narrowed, `README.md` given the two-stage story | Both read correctly to someone who has not read the wiki's decision page |

Phase 3 is the one worth not skipping. If adopting the source extension moves a `contents`
fingerprint on a file that has no template constructs in it, every existing plugin's pin breaks for
a rename.

## Blast radius

| Artifact | Scope of change | Reversible |
|---|---|---|
| `scripts/<resolver>.py` | New file | Yes, delete it |
| `scripts/build.py` | One call added inside `build()` | Yes, remove the line |
| `tests/scripts/` | New test file, plus fixture additions | Yes |
| `template/` | Two hook rules, one shipped script, possibly two renamed placeholder files | Yes, but a plugin repository already created from the template does not receive the change. That is the starting-shape rule and it is why anything fixable belongs in `scripts/` |
| `CLAUDE.md` | One invariant narrowed, one row added to the layout table | Yes |
| `D1-Foundry-holds-no-plugins` in the wiki | Untouched. The Stencil decision amends it by reference rather than editing it | n/a |
| A plugin adopting this | Every templated file renamed, its `contents` fingerprint moves, its dependents' pins break | Yes for that plugin, at the cost of a version bump |
| A plugin not adopting this | Nothing | n/a |

**Untouched by every phase:** the resolver in `scripts/resolve.py`, all fingerprint skip lists, the
emitter contract, every existing emitter, the manifest schema apart from whatever one key the
runtime stage needs, and the shipped shape of any folder built from a plugin that does not use a
template.

**The irreversible edge:** a Foundry release that has shipped. Until `v0.1.0` is something people
have built against, every phase above is a rewrite away from nothing. After that, the source
extension is a public fact and changing it is a first-number bump.

## Not in this plan

| Item | Where it goes |
|---|---|
| Fixing the 18 dangling cross-references in the parked plugins | The repository that ends up owning each plugin, after the split lands them |
| Availability-filtered inline enumerations | Not expressible in version one. A version two question, if it is ever a question |
| Proposing the runtime stage as a harness feature so the hooks become unnecessary | A separate document to a separate audience |
