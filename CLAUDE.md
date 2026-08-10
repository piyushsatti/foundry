# foundry

**Foundry is a compiler for agent plugins.** It holds that compiler, which turns a plugin
repository into one finished folder per agent harness that plugin asked for, and the template a new
plugin repository starts from. Nothing else.

The category was decided on 2026-08-10 against alternatives, and it earns its keep in this file
because it says where a change belongs. A front end validates the manifest, one intermediate tree
carries the content, one back end per target writes a folder. **Bundler is wrong by definition**, a
bundler merges many files into few and nothing here merges. **Transpiler is wrong**, nothing here is
a language until Stencil. Converter fits Pandoc's shape and is rejected because a converter is
expected to lose quietly. Stencil does not weaken the word: staging a build so that part of it is
deferred, leaving a residual the runtime finishes, is textbook multi-stage compilation, and a
compiler that ships a runtime is the norm rather than the exception.

## Foundry is atomic. Do not split it.

**One repository. Never broken into a marketplace, a bundle, a template repo, or a package.** Build
tool, manifest format, Stencil, the template, the release process: one inheritance. Take all of it or
none.

Pi's decision, not an open question. Written here because the code does not say it: the repo looks
separable, and a defect will eventually make splitting look obvious. It is not.

| Never | Instead |
|---|---|
| Move `template/` to its own repository | Report the problem, ask |
| Publish any part of Foundry separately | Nothing here ships on its own |
| Let a plugin depend on a piece of Foundry | It declares `foundry:` and takes the whole tool |

Written 2026-08-09 after a session proposed that split and created a public `foundry-template` repo
before Pi saw the decision. The defect behind it is real and is under known problems below.

No plugins live here. No skills, agents, shared library, MCP servers or web app live here. All of
that left the repo in the split and now sits in a holding folder outside it. Where each piece lands
is a later session's decision and is not this repo's concern.

## The test for whether something belongs here

**Would someone building a completely unrelated plugin need this? If no, it is not Foundry.**

| Belongs | Does not belong |
|---|---|
| The build tool and the resolver | Any actual plugin, skill, agent or command |
| The manifest format the build tool reads | A library one plugin happens to import |
| The template a plugin repository starts from | Anything specific to Pi's own plugins |
| Conventions and checks that define a valid plugin | Anything that names a particular consumer |
| Foundry's own version and release process | A list of who uses Foundry |

If two parties want to share code between their plugins, they make their own repository and point
at it. Foundry has no opinion and no involvement.

## Layout

| Path | Holds |
|---|---|
| `scripts/resolve.py` | Reads a plugin's manifest, walks its dependencies, settles which Foundry version applies and fingerprints everything. Runs inside a plugin repository, not inside Foundry |
| `scripts/build.py` | Copies the plugin's own content, copies what it takes from each dependency, catches collisions, checks `provides`. Then hands that staged tree to one emitter per harness named in `targets` and writes `foundry.lock.json` inside each folder. Knows nothing about any harness itself |
| `scripts/emitters/__init__.py` | The registry of which module emits which harness, the loss policy, the pruning that takes out every kind a harness cannot read, and the skill depth check. Everything about loss lives here and in no emitter |
| `scripts/emitters/contract.py` | What every emitter module declares, and the file helpers every emitter shares: `write_json`, `metadata`, `skill_dirs`, `frontmatter`, `mcp_servers`, `hook_rules`, `remove`, `read_json`. Also the moment vocabulary and the validation of a neutral hook rule, checked once before any harness folder is written |
| `scripts/emitters/<harness>.py` | One harness's folder, and nothing else. `claude_code.py`, `agent_plugins.py` which also serves Codex, `skills_tree.py` which serves OpenCode and Pi, `instructions.py` |
| `template/` | The starting shape of a plugin repository: manifest, empty content directories, CI workflow, its own README and CLAUDE.md |
| `template/scripts/foundry.py` | The bootstrap stub. The one file genuinely copied into a plugin repo rather than fetched |
| `VERSION` | Foundry's own version. The release is a git tag `v<version>` and nothing else, and `release.yml` refuses a tag that disagrees with this file |
| `ruff.toml` | The lint and format gate, pinned so it means the same thing on any machine. Development tooling only: nothing under `scripts/` imports it |
| `tests/` | Fixture plumbing in `repos.py` that writes throwaway plugin repos, plus the rule tests under `tests/scripts/`. Run with `python3 -m unittest discover -s tests` |
| the wiki | Every decision, and the architecture they add up to. `Decisions` indexes them and says which are built. `D1-Foundry-holds-no-plugins` says what Foundry is, `D2-One-source-one-release-one-folder-per-harness` says what it emits, `D3-Six-hook-moments-and-a-waiver-on-the-rule` says why a per-harness override lives on a rule and not on a kind, and `D4-Stencil-binds-at-build-time-and-on-the-users-machine` narrows two invariants below. `docs/adr/` held these and is gone |
| `docs/plans/` | The order of work for something not built yet, and its blast radius. A plan is deleted once its work has landed, unlike an ADR |
| `.github/workflows/` | Foundry's own CI. `ci.yml` is callable only, and two workflows call it: `gate.yml` on a tag named `gate-*`, and `release.yml` on `v*` after checking the tag against `VERSION` |

## Invariants, and what breaking each one costs

| Invariant | Cost of breaking it |
|---|---|
| The bootstrap stub stays tiny and almost never changes | It is the only file that ever needs re-copying by hand across every plugin repository. Anything that might need fixing later belongs in `scripts/`, where one fix reaches everyone |
| Nothing on a user's machine fetches, and nothing assembles a folder | This is the narrowed form, accepted with the templating decision. The conflict-free property comes from a plugin arriving as one finished folder, and that survives: rendering text already inside a folder creates no conflict between two installed plugins, while fetching or assembling one does. So Stencil may render a plugin's own files in place, and nothing may reach outside the installed folder or pull anything down. The wider sentence this replaces read "nothing resolves on a user's machine" |
| The build never picks a winner | Every ambiguity stops the build and names both sides. Choosing silently means nobody finds out a substitution happened |
| There is no silent drop | A declared kind a harness cannot represent stops the build, naming the kind, the harness, the manifest line and both ways forward. Or the author wrote that loss down under `degrade.<harness>.drop`, and then it is printed at build time, recorded in that folder's `foundry.lock.json`, and recorded again in `foundry.release.json` when the build wrote more than one folder. `write_release` is called only when more than one harness is named, so a single-target build records the drop in the folder's own lock file and writes no release record at all. A single hook rule follows the same two outcomes at its own smaller grain: a rule naming a moment a harness has no event for stops the build, or the rule already names `only` and the harness it excludes is a recorded, printed drop, and a rule excluded from every harness that carries hooks in this build stops the build too, because a rule dropped everywhere is a guard that runs nowhere no matter how many of those drops are on the record. There is no third outcome, at either grain. This is the winner rule applied to harnesses: a diminished folder is always a line somebody wrote, never something the tool concluded |
| A recorded drop actually happened | Refuse or record was never the whole rule: a record has to be true. `strip_allowed_tools` in `emitters/__init__.py` used to match a YAML key by reading lines while `declared_kinds` decided the same fact with a real parser, so quoting the key, which is ordinary valid YAML, made them disagree: the lock file recorded the drop and the field still shipped. That is worse than a silent drop, because the record actively lies and the folder lands where nobody ran the build. Both that function and the Pi `arguments` rename in `skills_tree.py` now share `frontmatter_key` in `contract.py` and cross-check against the parser afterward, refusing by name if it still sees the key. **Wherever a parser and a hand-rolled matcher both decide one fact, they compare and the build stops on disagreement** |
| A symlink stops the build, and is never followed | Nothing here ever considered one: `fingerprint` walked with `rglob`, which steps over a symlinked directory, while `shutil.copytree` dereferenced it. So a dependency shipped files from outside its own repository and its pin stayed byte-identical even after those files changed, which breaks what a pin means. `find_symlink` in `resolve.py` refuses instead, from `fingerprint` and again from `copy_dependency_content`, honouring the same three skip lists so a link inside `.venv` is not a build error. **This is a named failure, not a resolution policy.** Deciding which links are safe to follow needs two functions to agree about resolution forever, which is the shape of the bug being fixed, and no repository has one |
| A release Foundry already wrote is not source | A previous output directory left in a checkout was ordinary content: hashed into the pin, so the same source fingerprinted differently once it had been built, and copied into every shipped folder, so `claude-code/dist/` held a whole earlier release, seven lock files deep, and `shipped.py` passed it. `find_release` in `resolve.py` refuses instead, from `fingerprint` and again from `copy_own_content`, pruned by the same `SKIP_DIRS` so a cached release under `.foundry` is not a build error. **Recognised by content, never by name.** `--out` takes any path, so `dist` is a convention and a guess, while `foundry.lock.json` and `foundry.release.json` are written by nothing else. `built_by_this_tool` decides it and lives in `resolve.py` now, because that module has to recognise a release on sight and cannot import upward. `exclude` is deliberately not a way out and the refusal says so: it governs what ships and never reaches the fingerprint, so it would leave the pin wrong while looking like a fix |
| A Claude Code folder moves only on purpose, with a before-and-after diff run first | Every `contents` fingerprint already sitting in a shipped lock file was measured on those bytes, and every pin written against one stops matching the moment they move, silently, on somebody else's machine. `emitters/claude_code.py` still writes the manifest exactly as the old `write_metadata` did: same `METADATA_KEYS` tuple, same order, same path. A manifest that names no `targets` still gets a lock file with no `target` and no `dropped` field, because a lock file is part of the folder that ships. The folder has moved twice, both before `v0.1.0` and both with the before-and-after listing read. Once when `mcp.json` and `hooks/hooks.yaml` started being translated rather than shipped unread, which moved it only for plugins declaring an MCP server or a hook. Once when a `.gitkeep` at the top of a content directory stopped shipping, which moved it only for plugins carrying one |
| A capability answers for every kind | `carries` and `cannot` in one `Capability` together name all six kinds in `KINDS`, and the framework refuses to dispatch otherwise, calling it a Foundry defect. When a seventh kind is added, no harness can carry it silently on the grounds that nobody re-read that module |
| No folder holds a neutral file whose translated twin it also holds | This is the narrowed form, and it is narrower than it used to read. Once `mcp.json` becomes `.mcp.json`, or `hooks/hooks.yaml` becomes `hooks/hooks.json`, the neutral one is removed: two files saying one thing, one of which the harness ignores, is a record that cannot explain itself. **Everything else the repository ships, ships.** The wider sentence this replaces read "no harness folder holds a file that harness does not read", which every packaged folder already breaks by carrying `README.md`, and enforcing it literally would strip loose files from five folders and move the `claude-code` fingerprint that six repositories are pinned against. `drop_placeholders` in `build.py` still sweeps a dot file out of the top of each content directory before any emitter runs, dropping the directory if that leaves it empty. See `Emitters` in the wiki |
| Error messages are the product | Each refusal states what is wrong, where it was declared, and what to do about it. A refusal with no next step is a bug |
| Foundry keeps no list of consumers and never reaches into another repository | The dependency direction only runs one way. A list here inverts it |
| Only pyyaml beyond the standard library | The build tool runs in strangers' CI. Every added dependency is a new way for someone else's build to fail |
| What gets skipped during fingerprinting is frozen | `SKIP_DIRS`, `SKIP_SUFFIXES` and `SKIP_NAMES` in `resolve.py` alone decide what a fingerprint covers, both the pin and the lock file's `contents`. Changing any of the three changes every fingerprint, which invalidates every pin anyone has written. A test asserts all three lists by hand for exactly this reason, and it is what caught `.foundry` being added rather than letting it through. `NEVER_SHIP` in `build.py` is a separate list deciding only what gets copied, and changing it moves no fingerprint at all. `fingerprint` also takes an `exempt` argument, and that is not a fourth list: it is per-call, matched by resolved path, empty for every caller but `build()`, which passes its own destination so that `--out dist` twice does not fingerprint differently from a clean checkout. The three lists stay frozen and the hand-written test still calls `fingerprint` with no exemption |
| Nothing skipped by `resolve.py` may be missing from `NEVER_SHIP` | A path outside the fingerprint that still gets copied ships without the lock file's `contents` changing, so the record cannot show it happened. That is how `.claude`, the author's local settings, was reaching people who installed a plugin, and how `.foundry`, the cache the bootstrap stub writes, was putting 170 files of Foundry's own source inside every shipped folder |
| A build never reads its own output or its own scratch | `--out dist` puts both inside the plugin being read. The staging directory is created beside the destination, so copying the plugin root copies the staging directory into itself until the path is too long for the filesystem, and that fails on the first build rather than the second. `copy_own_content` is handed both paths and matches them resolved, because `dist` is a convention in a README and the flag takes anything |
| A pin names the fingerprint of the dependency's source checkout | `resolve()` fingerprints each manifest's `root` and `check_pins` compares every pin against that. The lock file's `contents` is a separate record of what shipped and no pin is ever checked against it. State it the other way round and people copy `contents` into a pin, which always disagrees |
| A dependency hands over skills, agents, commands and hooks only | `CONTENT_DIRS` in `build.py` is what stops a dependency writing anywhere it likes in the output |

A shipped folder can never itself be a dependency `path`. `MANIFEST_NAME` is in `NEVER_SHIP`, so
nothing that ships carries a manifest and `read_manifest` refuses it. A dependency is always a
source checkout.

## What a neutral hook rule is

`hooks/hooks.yaml` is a list of blocks. It never ships: every harness with a hook surface has its
own event vocabulary, so an emitter that carries hooks translates this file and removes it.

| Key | Is |
|---|---|
| `at` | one of `session-start`, `before-tool`, `after-tool`, `turn-end`, `before-compact`, `session-end`. `session-start`, `before-tool`, `after-tool` and `session-end` are universal: every hook-carrying harness expresses all four. `turn-end` and `before-compact` are not: only Claude Code has an event for either today |
| `run` | a path to a file inside the plugin. Not a shell line, so the build can check the hook has something to run. Shell work goes inside that file |
| `match` | optional, one pattern, passed to whatever the harness calls a matcher |
| `only` | optional, a list of harness names. The rule is carried by the harnesses it names and is a recorded, printed drop everywhere else. Refused if it names a harness outside `targets`, and refused again if no harness carrying hooks in this build is left to run the rule |
| `timeout` | optional, a whole number of seconds greater than zero, carried into the Claude Code hook entry |

Any other key is refused rather than ignored, because an ignored key in a guard is a guard that does
less than it appears to.

**The moment is `at` and never `on`.** YAML 1.1 resolves a bare `on` to the boolean true, in every
YAML 1.1 reader, so `on: session-start` arrives keyed `true` and the rule names no moment. It was
written as `on` and nothing noticed for as long as nothing read a rule. A rule still written that
way is refused by name, so the author is told this rather than told they have a key called True.

## Adding a harness is one module and one registry line

Everything to the left of the seam is the build tool that already existed: resolution,
fingerprinting, collisions, the `provides` check. Everything to the right is one harness's folder.
A module in `scripts/emitters/` declares three names and nothing else.

| Name | Is |
|---|---|
| `TARGETS` | the harness names this module emits, as a tuple. One module may serve several harnesses that share a package shape |
| `CAPABILITIES` | one `Capability` per name in `TARGETS`, each naming what that harness carries and, for everything else, the sentence saying why it cannot |
| `emit(target, manifest, tree)` | writes that harness's folder, in place, in the private copy of the staged tree it is handed. Returns nothing |

Adding a harness is that module, one line in `REGISTRY` in `emitters/__init__.py`, and one row in
`HARNESS` in `.github/checks/harnesses.py`, whose `row` exits for a target with no entry. Nothing
under `scripts/` changes, and that is the evidence the seam is in the right place. **Not the size of
a module**: this sentence used to offer `claude_code.py` as under forty lines, which was wrong by
several times over on the day it was written and is wrong by more now. An emitter is as long as its
harness's file shapes demand. What makes the seam right is that adding one touches nothing to the
left of it.

The checks row is deliberate duplication and its own docstring says so: a check that asked the
emitters what they write would agree with every change including a wrong one. **The place that does
not refuse is `tests/scripts/test_emitters.py`**, where `ALL_TARGETS` and the expected-files map
beside it are written out by hand, so a seventh harness added without touching them ships untested
and nothing reports it.

`KINDS` in `resolve.py` is the six things a capability answers for. The first four are
`CONTENT_KINDS`, directories, and the only things a dependency may hand over.

| Kind | Where it lives in the neutral tree |
|---|---|
| `skills`, `agents`, `commands`, `hooks` | a directory at the tree root |
| `mcp` | the plugin's own `mcp.json` at the tree root, never taken from a dependency |
| `allowed-tools` | a frontmatter field inside a skill, not a thing on disk of its own |

Carrying a kind is not the same as copying it through. `claude_code.py` translates two neutral
files into the names Claude Code opens, and removes the neutral one each time.

| Neutral | Claude Code reads | Also changed |
|---|---|---|
| `mcp.json` | `.mcp.json` | only `mcpServers` crosses over. `$schema` names the portable specification the source was written against, and Claude Code's format does not name it |
| `hooks/hooks.yaml` | `hooks/hooks.json` | the six moments become `SessionStart`, `PreToolUse`, `PostToolUse`, `Stop`, `PreCompact`, `SessionEnd`. Only the file goes: `hooks/` is a content directory and the scripts the rules run live in it |
| both | | `${PLUGIN_ROOT}` and `${PLUGIN_DATA}` become `${CLAUDE_PLUGIN_ROOT}` and `${CLAUDE_PLUGIN_DATA}`. Claude Code knows nothing of the shorter pair, which would reach a user as literal text inside a path |

Transports need no translation: Claude Code takes `streamable-http` as an alias for its own `http`,
and takes `stdio` and `sse` under those names.

| Harness | Module | Carries | Cannot carry |
|---|---|---|---|
| `agent-plugins` | `agent_plugins.py` | skills, mcp | agents, commands, hooks, allowed-tools |
| `claude-code` | `claude_code.py` | all six | nothing |
| `codex` | `agent_plugins.py` | skills, mcp | agents, commands, hooks, allowed-tools |
| `instructions` | `instructions.py` | skills, commands | agents, hooks, mcp, allowed-tools |
| `opencode` | `skills_tree.py` | skills, agents | commands, hooks, mcp, allowed-tools |
| `pi` | `skills_tree.py` | skills, commands, allowed-tools | agents, hooks, mcp |

Those numbers belong to the module and each is argued in that module's docstring against the
harness's own documentation. The policy that turns them into a refusal or a recorded drop belongs to
the framework. Change a capability in the module; never work around one in the framework.

**Before `emit` runs, the framework has already deleted every kind in that harness's `cannot`**: the
directory, or `mcp.json`, or the `allowed-tools` line out of each `SKILL.md`. So no emitter contains
loss logic, and none can: an emitter cannot see what its harness cannot carry.

| An emitter may | An emitter may not |
|---|---|
| Add files, write its harness's manifest, translate a neutral file into the shape that harness reads, delete a neutral file that harness does not read | Resolve, fetch, reorder, reach outside the tree it was given, or touch a fingerprint |

Every manifest goes through `write_json` in `contract.py`, and every other shared piece of file work
has a helper there. An emitter that formats its own JSON drifts one release at a time, and the drift
lands in a `contents` fingerprint looking like a content change.

**The one refusal that belongs to an emitter is about content, not about kinds.** A transport the
harness rejects, a matcher it ignores, a blocking hook it cannot express: those depend on what is
inside a file rather than on which kind it is, so the emitter raises `EmitError` itself while it is
looking at the file. Kind-level loss is never an emitter's to decide.

## Version discipline

`VERSION` is Foundry's public promise, and consumers who are strangers pin against it.

| Number | Meaning | Who bumps it |
|---|---|---|
| First | Something that used to work no longer does. The only breaking-change signal there is | Pi, on his explicit ask only |
| Second | New capability, nothing broken | Pi, on his explicit ask only |
| Third | A fix | Claude, when shipping one |

A first-number bump needs a migration document at `docs/migrations/foundry-<old>-to-<new>.md`,
because `resolve.py` names that exact path when it refuses to build across one. That directory does
not exist yet and must be created with the first such bump.

A careless second-number bump that actually breaks a consumer destroys the only break signal that
exists.

## Running the checks

There is no dependency install beyond pyyaml. The suite under `tests/` is the gate on the rules;
building the template is the end-to-end check.

```
python3 -m unittest discover -s tests
python3 scripts/build.py template --check
python3 scripts/resolve.py template --print
```

`--check` builds into a temporary directory and throws it away. All three exit 0 today. Run them
after any change to `scripts/` or `template/`.

**No count of the suite is written here on purpose.** A number in prose is right on the day it is
typed and wrong on the next commit, and this file said 73 for long enough that it was out by nearly
eighty. The command prints the real number, and `.github/checks/discovery.py` proves every test file
on disk is one the run found, which is the thing a count was standing in for.

Python style is `ruff`, over the same four paths for both commands, before committing:

```
uvx ruff check scripts tests .github/checks template
uvx ruff format scripts tests .github/checks template
```

`ruff.toml` pins the rule set and says which two rules are left out and why. `template` is in the
list because the bootstrap stub is the one file copied by hand into every plugin repository, so it
was formatted before any repository copied it rather than after.

The four checks under `.github/checks/` each take different arguments and CI is where those
arguments are written down. Running one with the wrong path fails with a message about the path, not
about the repository, so read `.github/workflows/ci.yml` rather than guessing:

```
python3 .github/checks/discovery.py tests
python3 .github/checks/defaults.py template
python3 .github/checks/shipped.py <built> <source>
python3 .github/checks/conformance.py <built> <source>
```

The last two want a built release and the source it was built from, which CI makes by copying
`template/` to a temporary directory first so the build cannot be helped by anything sitting around
it.

The template names five harnesses, so `--check` prints five lines, one per folder, each with that
folder's own `contents` fingerprint. The version names the source and the resolution answer, never
the capability set, so a folder's fingerprint is a fact about that folder alone.

Two of the five are the same number today, and that is right rather than a bug. The template holds
no content, and OpenCode and Pi both take a loose tree with no manifest, so with nothing to lay out
there is nothing to tell the two folders apart. They separate the moment the plugin has anything:
Pi ships commands as `prompts/` and OpenCode drops them, OpenCode ships `agents/` and Pi drops them.
The one previous reason these two differed was that each carried a different set of `.gitkeep`
placeholders, which is a difference in git bookkeeping and not in what anybody installs.

The suite covers each refusal by its message text. Resolution: a pin that moves, two dependencies
wanting different builds, a Foundry too old, a different first number in either direction, a
dependency loop, two sources for one name, and a `provides` claim absent from the output. Emitting:
a kind a harness cannot carry, hooks on OpenCode and on Pi, an MCP server on Pi, a harness name
Foundry does not know, a `degrade` block naming a harness not in `targets`, an empty `targets` list,
a skill nested more than one level deep, a manifest the author already wrote being overwritten, and
the case where every named harness would drop everything the plugin holds. Hooks have their own on
top of that: a rule written with `on`, a moment outside the six, a key a rule does not name, a `run`
naming a file the plugin does not hold, a `match` that is not a line of text, a `timeout` that is not
a whole number greater than zero, an `only` naming a harness the plugin does not build, and an
`only` naming only harnesses that carry no hooks in this build, which leaves the rule absent from
every folder written.

It also covers the nine things that fail silently or crash rather than refusing: the author's local
`.claude` settings reaching the shipped folder, a refusal on one harness leaving a half-written
release behind, the neutral files shipping into a Claude Code folder untranslated, a `.gitkeep`
shipping into every folder and holding an empty content directory open, the sweep that removes it
reaching one level too far into a skill somebody wrote, the `.foundry` cache shipping inside every
folder, that same cache moving a plugin's pin the moment it is built once, a previous release being
copied into the next one when both go to the same path, and the same release being copied in and
hashed in when the next build goes anywhere else. Add a test there rather than checking a refusal by
hand.

The last two are one bug read at two grains and the second one is the one that got out. The guard
against the first matches this build's own destination by resolved path, which is exactly right and
sees nothing left over from a run that pointed somewhere else. Both tests, and the CI step beside
them, only ever built to one path twice.

Two guards are worth knowing before changing anything under `scripts/emitters/`. One asserts a
Claude Code folder holds exactly the files it should, and one asserts its `contents` fingerprint is
a string written out by hand from the specification of the folder rather than read back from the
build. If either goes red and the change did not mean to move that folder, it breaks pins on
machines Foundry cannot see.

## Known problems, open

**"Use this template" hands out the build tool, not a plugin.** GitHub copies a repository root, and
this root is Foundry. The only `foundry.plugin.yaml` is in `template/`, one floor down, so a
generated repo cannot build:

```
no foundry.plugin.yaml here.
```

The size is not the problem, the layout is. Fix is Pi's, and it is not a split: read the atomic rule
at the top. Meanwhile, make a new plugin by copying `template/`.

## Known stale, do not trust these until they are rewritten

| File | What is wrong |
|---|---|
| `.claude-plugin/marketplace.json` | Lists five plugins served from this repository. None of them are here. Kept on purpose, and `.claude-plugin/README.md` says why: the entries resolve from the untouched `release` branch, so deleting them would break people who already installed one. Whether a catalog of consumers belongs in the base at all is still open |
| the superseded monorepo decision | Described `bundles/`, `library/`, `packages/` and `scripts/check_boundaries.py`, none of which exist. It has no wiki page: `Decisions` records it as superseded history and says what survived of it |

Five files were on this list and are no longer. `template/foundry.plugin.yaml`'s pin comment now
says the pin is the fingerprint of the dependency's source checkout. `.github/workflows/ci.yml` and
`.github/workflows/release.yml` were rewritten for a base rather than a monorepo. `.gitignore` was
rewritten so every fence names something this repository can produce, which took out `/plugins/`,
`/local/`, and a per-machine path under `bundles/meditate/`. `.gitignored/` was deleted: its README
described a scratch layout naming `docs/<product>/` and `research/`, both of which left in the
split.

`v0.1.0` is tagged and pushed. A fresh plugin repository needs no `foundry_source:` line and no
`FOUNDRY_SOURCE` override: the bootstrap stub clones the tag from GitHub and builds. Proven end to
end from a copy of `template/` with neither set, to the same five fingerprints the in-repo `--check`
prints.

That paragraph said the opposite until 2026-08-09, and it stayed wrong for the few minutes between
the push and this edit. In those minutes twelve agents converting the plugin repositories read it,
believed it, and each one worked around a problem that no longer existed. A note about the state of
the world is a claim with a shelf life, and this file is read by things that cannot check it.

## Working rules for this repo

- Documentation is structure, why, and how to operate it. No preamble, no restating the obvious.
- Never refer to a decision by a shorthand code. State the decision in a sentence every time.
- No em dashes. Use a colon, a comma, a period, or a middle dot.
- Never compare Foundry to an operating system or to any Unix-like system.
- Prefer a table to a bullet list for anything enumerable. Headings state their conclusion.
