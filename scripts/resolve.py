#!/usr/bin/env python3
"""Work out everything a plugin needs, and refuse to guess when it is unclear.

Runs inside a plugin repository, not inside Foundry. Reads that repo's
`foundry.plugin.yaml`, walks whatever it depends on, and returns one settled
answer: which Foundry version applies, which dependencies are in play, and the
fingerprint of each. `build.py` turns that answer into a shipped folder.

Why this exists: once plugins live in separate repositories, "which version of
the shared thing am I getting" stops being answerable by looking at the
directory layout. This answers it once, when the plugin is published, and
writes the answer down. Nothing is resolved on a user's machine.

The three rules it enforces, and why each one:

  Foundry version      A plugin declares the OLDEST Foundry it works with. The
                       answer is the newest version anyone actually asked for,
                       never newer. So a build can never quietly land on a
                       version nobody requested.

  Foundry major        A major version bump is the only signal that something
                       breaks. If a plugin needs a major this tooling is not,
                       the build stops and says which migration to read.

  Dependency pins      Two dependencies wanting different builds of the same
                       third thing is a real disagreement with no correct
                       answer. It stops and names both sides. It never picks
                       the newer one, because nobody is watching to catch it.

Operate:
    python3 resolve.py [PLUGIN_DIR] [--out lock.json] [--print]

Exit 0 when everything resolves, 1 on any unresolvable disagreement.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

import yaml

FOUNDRY_ROOT = Path(__file__).resolve().parents[1]
VERSION_FILE = FOUNDRY_ROOT / "VERSION"
MIGRATIONS_DIR = "docs/migrations"

MANIFEST_NAME = "foundry.plugin.yaml"

# The two files Foundry writes into a finished folder, and nothing else writes
# anywhere. They live here rather than in `build.py`, which is where they used
# to sit, because this module has to recognise a release on sight and cannot
# import upward to ask. `build.py` imports both from here.
#
# One folder carries a lock file. A release of several folders carries the
# record at its top and a lock file inside each folder, so a directory holding
# either name is a release, and checking both is what names a multi-harness
# release at `dist/` rather than at `dist/agent-plugins`. The record is also
# the one place a person can see that the Pi folder at 1.4.2 has no MCP server
# while the Claude Code folder at the same version does.
LOCK_NAME = "foundry.lock.json"
RELEASE_NAME = "foundry.release.json"

# Manifest fields that describe the plugin to whoever installs it. They are
# carried through untouched and land in the plugin metadata the build writes.
METADATA_KEYS = ("description", "author", "homepage", "license", "keywords")

# Every top-level key any consumer of this manifest reads. `read_manifest`
# below reads all but one of them itself; the exception is `foundry_source`,
# read only by `template/scripts/foundry.py`'s own regex, before this module
# or anything else under `scripts/` has run, because it names where to fetch
# the very tool this module belongs to. It stays recognised here so the
# documented way to build against a local Foundry checkout, commented out in
# the template's own manifest, is not refused by a rule that has never read
# it. A key belongs on this list because something in the repository reads
# it, never because `read_manifest` happens to be the thing that does.
RECOGNIZED_KEYS = frozenset(
    {
        "id",
        "version",
        "foundry",
        "foundry_source",
        "requires",
        "targets",
        "degrade",
        "provides",
        "exclude",
    }
    | set(METADATA_KEYS)
)

# The four content directories a plugin repository holds, and the four a
# dependency may hand over. Named here rather than in `build.py` because both
# halves of the tool need the same list from the same place: the build fences a
# dependency to them, and every emitter declares which of them its target can
# represent. `build.py` still exports it as `CONTENT_DIRS`.
CONTENT_KINDS = ("skills", "agents", "commands", "hooks")

# Everything an emitter can be asked to carry, and the whole vocabulary a
# `degrade` block may name. The two beyond the content directories are not
# directories at all: `mcp` is the plugin's own `mcp.json`, and `allowed-tools`
# is a field inside a skill file that one harness reads and the rest discard.
KINDS = CONTENT_KINDS + ("mcp", "allowed-tools")

# What a manifest that never mentions `targets` gets. This is exactly what
# Foundry built before targets existed, so an existing plugin keeps building
# the same folder in the same place without its owner touching anything.
DEFAULT_TARGETS = ("claude-code",)

SEMVER_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")

# What `name_fault` in `scripts/emitters/agent_plugins.py` already demands of a
# name Agent Plugins 1.0.0 will accept: the same character set with the
# underscore taken out, no leading or trailing character outside it, no
# doubled hyphen or dot, and a 64 character cap. `id` used to have its own,
# looser rule, so `id: my_plugin` passed here, a claude-code folder got built,
# and only then did the whole release stop, the moment `agent-plugins` or
# `codex` was named in `targets`, deep inside that harness's own emitter,
# refusing a name Foundry itself had already accepted. One vocabulary, the
# strictest one, checked once, here, before any folder is built: every `id`
# Foundry accepts is an `id` every harness it can build for accepts too.
NAME_RE = re.compile(r"^(?!.*(?:--|\.\.))[a-z0-9](?:[a-z0-9.-]{0,62}[a-z0-9])?$")
MOVING_TARGETS = {"latest", "current", "head", "*", "main", "master"}

# Never part of what a plugin ships, so never part of its fingerprint.
#
# `.foundry` is the cache the bootstrap stub writes when it fetches a Foundry
# release, and it is here because a pin has to mean the same thing on two
# machines. Without it the fingerprint of a plugin's checkout depends on whether
# that checkout has ever been built and which Foundry versions it happens to
# have cached, so the same source pins differently everywhere and the advice to
# pin against a clean checkout describes a state no built repository can return
# to. It is in `NEVER_SHIP` for the separate reason that it was being copied
# into every folder, eight megabytes of Foundry's own source inside each one.
SKIP_DIRS = {".git", "__pycache__", ".venv", "node_modules", ".claude", ".github", ".foundry"}
SKIP_SUFFIXES = {".pyc", ".pyo"}
SKIP_NAMES = {".DS_Store", MANIFEST_NAME}


class ResolveError(Exception):
    """Something could not be settled. The message is the whole report."""


# ------------------------------------------------------------ version numbers
def parse_version(value: str, where: str) -> tuple[int, int, int]:
    match = SEMVER_RE.match(str(value).strip())
    if not match:
        raise ResolveError(
            f"{where}: '{value}' is not a version number.\n"
            f"  Expected three numbers separated by dots, like 1.4.2."
        )
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def foundry_version() -> str:
    """The version of the Foundry this tooling came from."""
    if not VERSION_FILE.is_file():
        raise ResolveError(
            f"missing {VERSION_FILE}.\n"
            f"  The build tool ships as part of Foundry, so it should always know\n"
            f"  which Foundry it is. This copy does not, which means it was moved\n"
            f"  out of a Foundry release instead of fetched as one."
        )
    return VERSION_FILE.read_text().strip()


# ---------------------------------------------------------------- fingerprint
def find_symlink(root: Path) -> Path | None:
    """The first symlink under `root`, outside what fingerprinting already skips.

    Walked by hand rather than through `rglob`, which gets this wrong two ways
    at once: it never descends into a symlinked directory, so nothing beneath
    one is ever visited, and `is_file()` on a symlinked file returns True, so a
    symlinked file already reads as an ordinary one and its target's current
    bytes get hashed under the link's own name. Presence is what has to be
    caught here, not content, so this asks `is_symlink()` directly instead of
    asking what kind of thing sits on the other end.

    Pruned at the directory level rather than filtered afterward: a directory
    named in `SKIP_DIRS` is never entered, the same exemption `fingerprint`
    already gives it, so a symlink inside `.venv` or `node_modules` is
    invisible here exactly as it is invisible to the hash below.
    """
    for entry in sorted(root.iterdir()):
        relative = entry.relative_to(root)
        if any(part in SKIP_DIRS for part in relative.parts):
            continue
        if entry.is_symlink():
            if entry.suffix in SKIP_SUFFIXES or entry.name in SKIP_NAMES:
                continue
            return entry
        if entry.is_dir():
            found = find_symlink(entry)
            if found is not None:
                return found
    return None


def built_by_this_tool(directory: Path) -> bool:
    """One folder carries a lock file; a release of several carries a record."""
    return (directory / LOCK_NAME).exists() or (directory / RELEASE_NAME).exists()


def find_release(root: Path, exempt: frozenset[Path] = frozenset()) -> Path | None:
    """The topmost directory under `root` that Foundry already wrote, if any.

    A release is recognised by what is inside it and never by what it is
    called. `--out` takes any path, so `dist` is a convention in a README and
    nothing more, while `foundry.lock.json` and `foundry.release.json` are
    files only this tool writes. Naming a directory would also mean guessing
    about somebody else's repository, which is the argument that rejected
    exempting an output directory by name and which this does not need.

    The topmost one is returned, not the deepest and not the lock file itself:
    a release of six folders holds its record at the top and a lock file in
    each folder, so naming a child would send an author to delete one sixth of
    the thing. It is also what makes "delete it" a complete instruction.

    `exempt` holds resolved paths this build already accounts for, which is its
    own destination. A directory named there is stepped over **and the walk
    continues**, rather than the walk stopping at the first release it meets:
    stopping would let the build's own `dist` shadow a genuinely stale
    directory sorting after it, which is a hole in exactly the place the bug
    this rule exists for was found.

    Pruned by `SKIP_DIRS` the same way `find_symlink` and `fingerprint` prune,
    so a cached release under `.foundry` or a sample one inside a virtualenv is
    not a build error. `SKIP_SUFFIXES` and `SKIP_NAMES` say nothing here:
    both describe a file, and this only ever asks the question of a directory.
    """
    for entry in sorted(root.iterdir()):
        relative = entry.relative_to(root)
        if any(part in SKIP_DIRS for part in relative.parts):
            continue
        if entry.is_symlink() or not entry.is_dir():
            continue
        if entry.resolve() in exempt:
            continue
        if built_by_this_tool(entry):
            return entry
        found = find_release(entry, exempt)
        if found is not None:
            return found
    return None


def fingerprint(root: Path, exempt: tuple[Path, ...] = ()) -> str:
    """A short, stable name for the exact contents of a folder.

    Sorted file paths and their bytes, hashed together, so a rename counts as a
    change and file order never does. Same method Go uses for module contents.

    The path goes in as `as_posix()` rather than `str()`, so the separator
    hashed is always `/`, never whatever the local platform happens to use.
    On macOS and Linux `Path` already prints with `/`, so the two expressions
    produce identical bytes and no fingerprint anyone has already published
    moves. Foundry makes no promise about building on Windows, and this line
    does not manufacture one: a checkout with different line endings still
    hashes different bytes, because the bytes really did change and no path
    encoding can paper over that. `.gitattributes` is the plugin author's fix
    for that, not this function's.

    A symlink anywhere under `root`, outside `SKIP_DIRS`, `SKIP_SUFFIXES` and
    `SKIP_NAMES`, stops this rather than being hashed either way. A symlinked
    directory is invisible to the walk below and a symlinked file already
    reads as an ordinary one, so a pin computed here can stay byte-identical
    while what a copy of this same root actually copies changes underneath
    it: `shutil.copytree` dereferences a symlink instead of copying it. This
    is a refusal rather than a rule about which links are safe to follow, and
    `find_symlink` is what finds one; see its own docstring for why the walk
    below cannot be trusted to notice one on its own.

    A directory Foundry already wrote stops this the same way, and `exempt`
    names the ones this caller accounts for: its own destination, and nothing
    else. Those are left out of the digest rather than merely allowed past the
    refusal, which is the whole point. Hashing an exempt directory would leave
    `--out dist` twice fingerprinting differently from a clean checkout, which
    is the bug being closed, reintroduced one line further down.

    This changes nothing about what a fingerprint covers for anybody who does
    not pass `exempt`, and every caller outside `build()` passes none. The
    three skip lists above stay frozen and hand-asserted; this is a per-call,
    path-matched exemption, the shape `copy_own_content`'s `skip` already has.
    """
    link = find_symlink(root)
    if link is not None:
        raise ResolveError(
            f"{link}: this is a symlink.\n\n"
            f"  A pin is the fingerprint of a source checkout, and copying a plugin's\n"
            f"  content copies through a symlink rather than copying it: a symlinked\n"
            f"  directory is invisible to this walk and to the tool that reads a\n"
            f"  finished pin the same way, while whatever ships dereferences the link\n"
            f"  and copies what it currently points to. So the fingerprint can stay\n"
            f"  put while what ships moves underneath it, with nothing to notice.\n\n"
            f"  Remove the symlink, or replace it with a real copy of what it points to."
        )
    accounted = frozenset(path.resolve() for path in exempt)
    release = find_release(root, accounted)
    if release is not None:
        raise ResolveError(
            f"{release}: this is a release, not source.\n\n"
            f"  It holds {LOCK_NAME}, a file only Foundry writes, so it is a folder\n"
            f"  an earlier build left behind rather than anything this plugin is\n"
            f"  made of. Hashing it in means this checkout's fingerprint depends on\n"
            f"  whether it has ever been built and on what happened to be sitting\n"
            f"  there at the time, so the same source pins differently on two\n"
            f"  machines. Copying it in puts a whole previous release inside the\n"
            f"  folder people install.\n\n"
            f"  It is recognised by what is inside it, never by its name: --out\n"
            f"  takes any path, so 'dist' is only a convention.\n\n"
            f"  Delete {release}, or point --out somewhere outside this plugin.\n"
            f"  Adding it to 'exclude' is not a way out: that decides what ships\n"
            f"  and never reaches this fingerprint."
        )
    digest = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        relative = path.relative_to(root)
        if any(part in SKIP_DIRS for part in relative.parts):
            continue
        if path.suffix in SKIP_SUFFIXES or path.name in SKIP_NAMES:
            continue
        if any(directory in path.parents for directory in accounted):
            continue
        digest.update(relative.as_posix().encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()[:12]


# ------------------------------------------------------------------- manifest
def read_targets(raw: dict, path: Path) -> tuple[list[str], bool]:
    """Which harnesses this plugin is built for, and whether it said so.

    Whether a name is one Foundry can emit is not decided here. This module
    sits below the emitters and must not import them, so the shape is checked
    here and the name is checked where the emitter is looked up.

    The second return value is whether the key was written at all, because a
    manifest that never mentions targets has to keep producing the exact bytes
    it produced before the key existed, lock file included.
    """
    raw_targets = raw.get("targets")
    if raw_targets is None:
        return list(DEFAULT_TARGETS), False

    if not isinstance(raw_targets, list):
        raise ResolveError(
            f"{path}: 'targets' should be a list of harness names.\n  targets:\n    - {DEFAULT_TARGETS[0]}"
        )
    if not raw_targets:
        raise ResolveError(
            f"{path}: 'targets' is empty, so this build would write nothing.\n"
            f"  Either name at least one harness, or delete the key and get\n"
            f"  {DEFAULT_TARGETS[0]}, which is what Foundry built before targets existed."
        )

    targets: list[str] = []
    for index, entry in enumerate(raw_targets):
        name = str(entry).strip()
        if not name:
            raise ResolveError(f"{path}: targets[{index}] is empty. Name a harness or remove the line.")
        if name not in targets:
            targets.append(name)
    return targets, True


def read_degrade(raw: dict, targets: list[str], path: Path) -> dict[str, list[str]]:
    """Losses the author pre-authorised, as a map of target to a list of kinds.

    A kind that a target cannot represent stops the build unless it is named
    here. Writing it down is deliberately more work than deleting the target,
    because a diminished package should be a decision somebody made.
    """
    raw_degrade = raw.get("degrade") or {}
    if not isinstance(raw_degrade, dict):
        raise ResolveError(
            f"{path}: 'degrade' should be a map of harness name to a 'drop' list.\n"
            f"  degrade:\n    {targets[0]}:\n      drop: [hooks]"
        )

    degrade: dict[str, list[str]] = {}
    for raw_target, block in raw_degrade.items():
        target = str(raw_target).strip()
        if target not in targets:
            raise ResolveError(
                f"{path}: 'degrade.{target}' waives a loss on a harness that is not built.\n"
                f"  targets: {', '.join(targets)}\n\n"
                f"  A waiver nobody reads does nothing, and a misspelled name here reads\n"
                f"  as a waiver that was written. Fix the name, or add {target} to 'targets',\n"
                f"  or delete the block."
            )
        if not isinstance(block, dict) or "drop" not in block:
            raise ResolveError(
                f"{path}: 'degrade.{target}' should be a block holding a 'drop' list.\n"
                f"  degrade:\n    {target}:\n      drop: [hooks]"
            )
        dropped = block["drop"] or []
        if not isinstance(dropped, list):
            raise ResolveError(f"{path}: 'degrade.{target}.drop' should be a list of kinds.")
        kinds: list[str] = []
        for entry in dropped:
            kind = str(entry).strip()
            if kind not in KINDS:
                raise ResolveError(
                    f"{path}: 'degrade.{target}.drop' names '{kind}', which is not a kind.\n"
                    f"  A kind is one of: {', '.join(KINDS)}."
                )
            if kind not in kinds:
                kinds.append(kind)
        degrade[target] = kinds
    return degrade


def check_unknown_keys(raw: dict, path: Path) -> None:
    """A key nothing reads is a rule that looks written and does nothing.

    Checked before anything else in the manifest, because it is a fact about
    the whole file rather than about any one field: `target:` for `targets:`
    used to build the default folder in total silence, and the author had no
    way to find out the harness they named was never read. An ignored key
    always costs exactly this, whatever its name, so it is refused by the
    same rule rather than caught one typo at a time.
    """
    unknown = sorted(key for key in raw if key not in RECOGNIZED_KEYS)
    if not unknown:
        return
    listed = ", ".join(repr(key) for key in unknown)
    plural = len(unknown) > 1
    verb = "are" if plural else "is"
    noun = "keys" if plural else "a key"
    raise ResolveError(
        f"{path}: {listed} {verb} not {noun} this manifest reads.\n\n"
        f"  An unrecognised key used to be silently ignored, which read to whoever\n"
        f"  wrote it as a line that took effect. 'target:' for 'targets:' was\n"
        f"  exactly this mistake: the default folder got built, the harness that\n"
        f"  was actually named never did, and nothing said why.\n\n"
        f"  Recognised keys: {', '.join(sorted(RECOGNIZED_KEYS))}.\n\n"
        f"  Fix the name, or remove the line."
    )


def read_take(raw_take: object, where: str) -> dict:
    """What one dependency hands over: a map of content kind to a list of names.

    A value written as a plain string is the shape this exists to catch, and
    it is worth catching here rather than downstream because of what happens
    if it is not: Python treats a string exactly like any other sequence, so
    `take: {skills: audit}`, meant as one skill, is read one character at a
    time by anything that iterates it expecting a list of names. The build
    then refuses the first of those one-letter names, sending the author to
    fix a skill that was never the problem. Refusing the shape itself, before
    a single item is looked up, means the refusal names the actual mistake.
    """
    if not raw_take:
        return {}
    if not isinstance(raw_take, dict):
        raise ResolveError(
            f"{where}: 'take' should be a map of content kind to a list of names.\n"
            f"  take:\n    skills: [audit]"
        )
    for kind, items in raw_take.items():
        if isinstance(items, str):
            raise ResolveError(
                f"{where}: 'take.{kind}' is '{items}', a single line of text where a list\n"
                f"  belongs.\n\n"
                f"  A string is read one character at a time, so this would be taken as\n"
                f"  {len(items)} one-letter names rather than the one meant, and the build\n"
                f"  would refuse the first of them and send you to fix a name that was\n"
                f"  never the problem.\n\n"
                f"  Wrap it in brackets, even for one entry:\n"
                f"    take:\n      {kind}: [{items}]"
            )
        if not isinstance(items, list):
            raise ResolveError(
                f"{where}: 'take.{kind}' should be a list of names.\n  take:\n    {kind}: [audit]"
            )
    return raw_take


def read_manifest(plugin_dir: Path) -> dict:
    path = plugin_dir / MANIFEST_NAME
    if not path.is_file():
        raise ResolveError(
            f"{plugin_dir}: no {MANIFEST_NAME} here.\n"
            f"  Every plugin repository has one at its root. Start from the\n"
            f"  Foundry template if this repository does not."
        )
    raw = yaml.safe_load(path.read_text()) or {}
    check_unknown_keys(raw, path)

    name = str(raw.get("id", "")).strip()
    if not name:
        raise ResolveError(f"{path}: needs an 'id'.")
    if not NAME_RE.match(name):
        raise ResolveError(
            f"{path}: id '{name}' is not a name every harness Foundry can build for\n"
            f"  will accept.\n"
            f"  Use lowercase letters, numbers, dots and hyphens, 1 to 64 characters,\n"
            f"  starting and ending on a letter or a digit, with no doubled hyphen\n"
            f"  and no doubled dot."
        )

    if "foundry" not in raw:
        raise ResolveError(
            f"{path}: needs a 'foundry' version.\n"
            f"  This is the oldest Foundry the plugin works with. A plugin takes\n"
            f"  all of Foundry or none of it, so one version is the whole answer."
        )

    if raw.get("version") is None:
        raise ResolveError(
            f"{path}: needs a 'version'.\n"
            f"  This is the plugin's own version, owned by this repository. It used\n"
            f"  to default to 0.0.0 and ship that into every harness manifest and\n"
            f"  lock file without saying so, which is not a version anyone chose."
        )

    requires = raw.get("requires") or {}
    dependencies = []
    for index, entry in enumerate(requires.get("plugins") or []):
        where = f"{path}: requires.plugins[{index}]"
        if not isinstance(entry, dict):
            raise ResolveError(f"{where} should be a block with 'id', 'pin' and 'path'.")
        for key in ("id", "pin", "path"):
            if key not in entry:
                raise ResolveError(f"{where} is missing '{key}'.")
        pin = str(entry["pin"]).strip()
        if pin.lower() in MOVING_TARGETS:
            raise ResolveError(
                f"{where}: pin is '{pin}', which moves.\n"
                f"  A pin names one exact build and never changes meaning. Use a\n"
                f"  fingerprint. Following a moving target is how a plugin ends up\n"
                f"  shipping against something it was never built with."
            )
        dependencies.append(
            {
                "id": str(entry["id"]),
                "pin": pin,
                "path": (plugin_dir / str(entry["path"])).resolve(),
                "take": read_take(entry.get("take"), where),
            }
        )

    targets, targets_declared = read_targets(raw, path)
    degrade = read_degrade(raw, targets, path)

    manifest = {
        "id": name,
        "version": str(raw["version"]),
        "foundry_minimum": str(raw["foundry"]).strip(),
        "dependencies": dependencies,
        "provides": raw.get("provides") or {},
        "exclude": raw.get("exclude") or [],
        "targets": targets,
        "targets_declared": targets_declared,
        "degrade": degrade,
        "root": plugin_dir,
        "manifest_path": path,
    }
    for key in METADATA_KEYS:
        if raw.get(key):
            manifest[key] = raw[key]
    return manifest


def collect(plugin_dir: Path) -> list[dict]:
    """The plugin plus everything it depends on, each manifest read once.

    Depth-first, tracking the path taken, so a cycle is reported as the actual
    loop rather than as a stack overflow.

    A second visit to the same directory is ordinary rather than exceptional:
    a diamond reaches one dependency down two branches, and a cycle arrives
    back at a manifest already on the trail. Both have to be answered from
    what was already read, and neither can be recognised before the read,
    because `found` and `trail` are keyed by the plugin id and the id is
    inside the file. `parsed` is keyed by the resolved directory, which is
    known beforehand, so the file is opened once and the decision is taken
    after. The trail is still consulted before `found`, so a cycle served from
    `parsed` is refused exactly as one read from disk would be.
    """
    parsed: dict[Path, dict] = {}
    found: dict[str, dict] = {}
    order: list[dict] = []

    def read_once(directory: Path) -> dict:
        key = directory.resolve()
        if key not in parsed:
            parsed[key] = read_manifest(directory)
        return parsed[key]

    def walk(directory: Path, trail: list[str]) -> None:
        manifest = read_once(directory)
        name = manifest["id"]
        if name in trail:
            loop = " needs ".join(trail[trail.index(name) :] + [name])
            raise ResolveError(
                f"DEPENDENCY LOOP.\n\n  {loop}\n\n  Break the loop; nothing can be built through it."
            )
        if name in found:
            return
        found[name] = manifest
        order.append(manifest)
        for dependency in manifest["dependencies"]:
            if not dependency["path"].is_dir():
                raise ResolveError(
                    f"{manifest['manifest_path']}: cannot find {dependency['id']} at "
                    f"{dependency['path']}.\n"
                    f"  Check the path, or fetch the dependency before building."
                )
            walk(dependency["path"], trail + [name])

    walk(plugin_dir, [])
    return order


# ---------------------------------------------------------------------- rules
def check_foundry_major(manifests: list[dict], running: str) -> None:
    running_major, _, _ = parse_version(running, str(VERSION_FILE))
    mismatched = []
    for manifest in manifests:
        major, _, _ = parse_version(manifest["foundry_minimum"], f"{manifest['manifest_path']} foundry:")
        if major != running_major:
            mismatched.append((manifest, major))
    if not mismatched:
        return

    report = [
        f"WRONG FOUNDRY GENERATION. This build tool is Foundry {running}.",
        "",
        "A change to the first number means something that used to work no longer",
        "does. It cannot be worked around, only migrated.",
        "",
    ]
    for manifest, major in mismatched:
        # A migration document is named oldest generation first, because it
        # describes what changed going forward and only one of those is ever
        # written. Naming it in the order the two numbers happened to appear
        # would, whenever the plugin is ahead of this tool, point at a document
        # that will never exist, and a refusal with no next step is a bug.
        older, newer = sorted((major, running_major))
        report.append(f"  {manifest['id']} needs Foundry {manifest['foundry_minimum']}")
        report.append(f"    declared in: {manifest['manifest_path']}")
        report.append(f"    read:        {MIGRATIONS_DIR}/foundry-{older}-to-{newer}.md")
    return_error = "\n".join(report)
    raise ResolveError(return_error)


def choose_foundry(manifests: list[dict], running: str) -> str:
    """Newest version anyone asked for. Never newer, never older."""
    running_parsed = parse_version(running, str(VERSION_FILE))
    asked = [(parse_version(m["foundry_minimum"], f"{m['manifest_path']} foundry:"), m) for m in manifests]
    highest, asker = max(asked, key=lambda pair: pair[0])
    chosen = ".".join(str(number) for number in highest)

    if highest > running_parsed:
        raise ResolveError(
            f"FOUNDRY TOO OLD. This build tool is Foundry {running}, but "
            f"{asker['id']} needs at least {chosen}.\n"
            f"  declared in: {asker['manifest_path']}\n\n"
            f"  Build with a newer Foundry, or lower that plugin's requirement.\n"
            f"  Nothing is downgraded automatically."
        )
    return chosen


def check_pins(manifests: list[dict], actual: dict[str, str]) -> None:
    """Nobody may disagree about which build of a dependency is in use."""
    claimed: dict[str, dict[str, list[str]]] = {}
    for manifest in manifests:
        for dependency in manifest["dependencies"]:
            claimed.setdefault(dependency["id"], {}).setdefault(dependency["pin"], []).append(manifest["id"])

    problems = []
    for target in sorted(claimed):
        pins = claimed[target]
        if len(pins) > 1:
            lines = [f"Two different builds of {target} are being asked for:"]
            for pin in sorted(pins):
                lines.append(f"      {pin}  wanted by {', '.join(sorted(pins[pin]))}")
            lines.append("    Only one can ship. Decide which, and update the other.")
            problems.append("\n    ".join(lines))
            continue
        pin = next(iter(pins))
        present = actual.get(target)
        if present is None:
            problems.append(f"{target} is required by {', '.join(sorted(pins[pin]))} but was not found.")
        elif present != pin:
            problems.append(
                f"{', '.join(sorted(pins[pin]))} expects {target} build {pin},\n"
                f"    but the copy here is build {present}.\n"
                f"    Either fetch the expected build, or update the requirement on purpose."
            )
    if problems:
        raise ResolveError(
            "DEPENDENCIES DISAGREE.\n\n    "
            + "\n\n    ".join(problems)
            + "\n\n  Nothing is picked automatically. A disagreement means someone has to\n"
            "  choose, and that choice should be deliberate."
        )


# -------------------------------------------------------------------- resolve
def resolve(plugin_dir: Path, exempt: tuple[Path, ...] = ()) -> dict:
    """Settle the version, fingerprint every checkout, check every pin.

    `exempt` is this build's own destination, and it reaches the plugin being
    built and nothing else. `manifests[0]` is that plugin, which the code just
    below already relies on. A dependency's checkout is exactly what its pin is
    the fingerprint of, so a release left sitting in one is the case worth
    refusing hardest, and there is no path through which `exempt` could reach
    it.
    """
    running = foundry_version()
    manifests = collect(plugin_dir)

    check_foundry_major(manifests, running)
    foundry = choose_foundry(manifests, running)

    actual = {
        m["id"]: fingerprint(m["root"], exempt if index == 0 else ()) for index, m in enumerate(manifests)
    }
    check_pins(manifests, actual)

    root = manifests[0]
    return {
        "plugin": root["id"],
        "version": root["version"],
        "foundry": foundry,
        "foundry_chosen_by": "newest version any dependency asked for",
        "built_with_foundry": running,
        "dependencies": [
            {
                "id": m["id"],
                "version": m["version"],
                "build": actual[m["id"]],
                "foundry_needs_at_least": m["foundry_minimum"],
            }
            for m in sorted(manifests[1:], key=lambda m: m["id"])
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Work out everything a plugin needs.")
    parser.add_argument(
        "plugin", nargs="?", type=Path, default=Path.cwd(), help="the plugin repo (default: here)"
    )
    parser.add_argument("--out", type=Path, help="write the answer to this file")
    parser.add_argument("--print", dest="show", action="store_true", help="print the answer")
    args = parser.parse_args()

    try:
        answer = resolve(args.plugin.resolve())
    except ResolveError as problem:
        print(f"\n{problem}\n", file=sys.stderr)
        return 1

    text = json.dumps(answer, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
        print(f"wrote {args.out}")
    if args.show:
        print(text, end="")
    if not args.out and not args.show:
        count = len(answer["dependencies"])
        print(f"{answer['plugin']} resolves against Foundry {answer['foundry']}, {count} dependencies")
    return 0


if __name__ == "__main__":
    sys.exit(main())
