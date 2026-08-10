#!/usr/bin/env python3
"""Turn a plugin repository into one self-contained folder that can be shipped.

Runs inside a plugin repository, in that repository's own CI, once per release.
The folder it writes is complete: everything the plugin needs is already inside
it. A user downloads that folder and it works. Nothing is resolved, fetched or
assembled on a user's machine, and so nothing can conflict there.

What it does, in order:

  1. Ask resolve.py what this plugin needs and which Foundry version applies.
  2. Copy the plugin's own content into one neutral tree.
  3. Copy in the exact pieces it asked for from each dependency.
  4. Check every claim in `provides`, and that no skill is nested too deep.
  5. Decide, for each harness named in `targets`, what it cannot carry.
  6. Write one folder per harness, each with its own lock file.

Steps 1 to 4 know nothing about any harness. Step 6 is `scripts/emitters/`, one
module per harness, and no other part of this file knows what a harness is.

All of that happens in a scratch folder beside the destination, which is moved
into place only once the build finished. A refused build leaves nothing behind,
so running it again after fixing the cause works.

It refuses to guess. Two dependencies handing over a skill of the same name is
a collision with no correct answer, so it stops and names both. A plugin that
claims to provide something it does not have is a lie in the metadata, so it
stops and says which claim is empty. A kind that a named harness cannot carry
stops the build unless the manifest already wrote that loss down.

Operate:
    python3 build.py [PLUGIN_DIR] --out DIR
    python3 build.py [PLUGIN_DIR] --check     # build to a temp dir, discard it

Exit 0 when the folder is written, 1 on anything unresolvable.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import emitters  # noqa: E402
from emitters import EmitError  # noqa: E402
from resolve import (  # noqa: E402
    CONTENT_KINDS,
    MANIFEST_NAME,
    ResolveError,
    find_symlink,
    fingerprint,
    read_manifest,
    resolve,
)

# Content directories a plugin can hold. A dependency hands over items from
# these and nowhere else, so a dependency can never write outside them. The
# list itself lives in `resolve.py`, because every emitter needs the same one
# to declare which of them its harness can represent, and two copies of a list
# that must agree is one copy too many.
CONTENT_DIRS = CONTENT_KINDS

# Never copied into a shipped folder, from the plugin or from any dependency.
#
# `.claude` is here because `resolve.py` already leaves it outside every
# fingerprint. Without it, a plugin author's local settings file is copied into
# the folder strangers download, and the `contents` recorded in the lock file is
# the same number whether it was copied or not, so the record cannot show that
# it happened. Adding it changes no fingerprint anywhere: what a fingerprint
# covers is decided entirely by the skip lists in `resolve.py`.
#
# `.foundry` is the same failure with a bigger payload. It is the cache the
# bootstrap stub writes when it fetches a Foundry release, so it exists in every
# plugin repository from its first build, and it was being copied whole into
# every folder: 170 files and eight megabytes of Foundry's own source inside
# each one, in a folder whose whole point is that nothing resolves where it is
# installed.
NEVER_SHIP = {
    ".git",
    ".github",
    ".claude",
    ".foundry",
    ".venv",
    "__pycache__",
    "node_modules",
    ".pytest_cache",
    ".DS_Store",
    MANIFEST_NAME,
}

LOCK_NAME = "foundry.lock.json"

# Written at the root of a release that holds more than one harness folder. It
# is the one place a person can see that the Pi folder at 1.4.2 has no MCP
# server while the Claude Code folder at the same version does.
RELEASE_NAME = "foundry.release.json"

# A private handoff from an emitter to write_lock below, naming a file-level
# loss the kind-level Loss object has no branch for. instructions.py is the
# only emitter that writes one today: it prunes what its own generated index
# does not name, one path at a time, decided only once the tree has been
# read, so the framework's kind-level plan cannot know about it in advance
# the way it knows a whole kind will be dropped. write_lock reads this file
# back and deletes it the moment it gets to it, so it never ships and never
# sits inside the `contents` fingerprint measured right after.
LEFT_BEHIND_NAME = ".foundry-left-behind.json"


class BuildError(Exception):
    """The folder could not be written. The message is the whole report."""


def ignored(_directory: str, names: list[str]) -> set[str]:
    return {name for name in names if name in NEVER_SHIP or name.endswith((".pyc", ".pyo"))}


def _segment_glob(segment: str) -> str:
    """One path segment's glob, translated so '*' and '?' can never reach across a '/'.

    This is the syntax `.gitignore` already uses, minus the anchoring rule
    `Excludes` documents on itself. An unterminated '[' is read as a literal
    character rather than refused: a directory named with a stray bracket in
    it should not stop a build over punctuation nobody meant as a pattern.

    A bracket class is glob syntax, not regex syntax, and the two disagree on
    what negates it: glob writes a negated class '[!t]', where '!' means
    "not this", while regex writes the same idea '[^t]' and reads a leading
    '!' as the literal character. Copying a class straight through kept it a
    valid regex while flipping its meaning, so a leading '!' or '^' is
    translated to the regex negation marker here, and any other '^' inside
    the class is escaped so it stays the literal character the author wrote.
    """
    out: list[str] = []
    index = 0
    while index < len(segment):
        char = segment[index]
        if char == "*":
            out.append("[^/]*")
        elif char == "?":
            out.append("[^/]")
        elif char == "[":
            end = segment.find("]", index + 1)
            if end == -1:
                out.append(re.escape(char))
            else:
                body = segment[index + 1 : end]
                if body[:1] in ("!", "^"):
                    body = "^" + body[1:].replace("^", "\\^")
                else:
                    body = body.replace("^", "\\^")
                out.append(f"[{body}]")
                index = end
        else:
            out.append(re.escape(char))
        index += 1
    return "".join(out)


# A placeholder swapped in for a '**' segment while a pattern is being
# stitched back together, then swapped back out for the connector that
# segment's position needs. Never appears in a real path, so it can never be
# confused with one.
_DOUBLE_STAR = "\0**\0"


def _compile_pattern(text: str) -> re.Pattern[str]:
    """One 'exclude' entry, its leading '!' already stripped, as a regex
    matched against a full relative POSIX path from the plugin root.

    A trailing '/' is how `.gitignore` says "this name is a directory", not
    an empty final segment to match against, so it is stripped before the
    pattern is split. Left in, 'scripts/' splits into ['scripts', ''] and the
    empty piece compiles to a pattern that can never match anything at all,
    which is worse than matching too much: the entry silently protects
    nothing while the build reports it as merely unused today.

    A pattern with no '/' in it never had a directory to cross into, so it is
    read as one literal segment and can only ever match a top-level entry:
    that is the anchoring rule `Excludes` documents, applied here rather than
    argued here. Every other pattern is split on '/' and stitched back
    together, and a run of '**' stands for zero or more whole segments, so
    '**/tests' matches 'tests' itself and not only something below it, and
    'skills/**/tests' matches 'skills/tests' and 'skills/a/b/tests' but not
    'skillset/tests': the slash bounding '**' on the literal-segment side is
    kept as a mandatory literal in the stitched regex rather than folded into
    the optional middle group, so a name that merely starts with 'skills' can
    never stand in for the segment boundary a '/' would have to cross.

    Either way, the compiled pattern also matches everything below whatever
    it matches: the trailing `(?:/.*)?` is what makes excluding a directory
    take its contents with it, the same as `.gitignore`.
    """
    if text.endswith("/"):
        text = text[:-1]
    segments = text.split("/")
    if len(segments) == 1:
        return re.compile(f"^{_segment_glob(text)}(?:/.*)?$")

    pieces = [_DOUBLE_STAR if segment == "**" else _segment_glob(segment) for segment in segments]
    body = "/".join(pieces)
    body = body.replace(f"/{_DOUBLE_STAR}/", "/(?:.*/)?")
    body = body.replace(f"{_DOUBLE_STAR}/", "(?:.*/)?")
    body = body.replace(f"/{_DOUBLE_STAR}", "(?:/.*)?")
    body = body.replace(_DOUBLE_STAR, ".*")
    return re.compile(f"^{body}(?:/.*)?$")


class Excludes:
    """Every 'exclude' entry, in the order the manifest wrote them, checked
    against a relative POSIX path from the plugin root.

    Entries are globs. Matching a path also matches everything below it, the
    same way naming a directory in `.gitignore` takes its whole contents with
    it: 'scripts' excludes 'scripts/anything', not only the literal name
    'scripts'. A leading '!' re-includes something an earlier entry excluded,
    and the last entry to match one path decides that path's fate, the same
    order-of-application rule `.gitignore` already uses. That is the whole of
    what negation costs: two entries can name the same path, and whichever
    one is written second wins.

    The one place this diverges from `.gitignore` on purpose: an entry with
    no '/' in it is anchored to the top level and reaches nowhere else. Under
    real `.gitignore` semantics a bare name matches at any depth, which would
    silently reach past every plugin repository already shipping something
    with that name one level deeper than whoever wrote the entry meant, and
    move that folder's `contents` fingerprint on upgrade rather than on
    purpose. Reaching deeper is written down explicitly instead, as
    '**/tests' rather than 'tests'.
    """

    def __init__(self, patterns: list[str]) -> None:
        self._entries: list[tuple[bool, re.Pattern[str], str]] = []
        for raw in patterns:
            negated = raw.startswith("!")
            text = raw[1:] if negated else raw
            self._entries.append((negated, _compile_pattern(text), raw))
        self._used: set[int] = set()

    def matches(self, relative: str) -> bool:
        """Whether `relative` is excluded, once every entry has had its say.

        Every entry is checked, never just the first one that matches,
        because a later entry might still reverse an earlier one. An entry
        that matches is marked used either way: a negation that only ever
        fires to be overridden by something written after it still counts as
        having fired, because it did exactly what its author wrote.
        """
        excluded = False
        for index, (negated, pattern, _raw) in enumerate(self._entries):
            if pattern.match(relative):
                self._used.add(index)
                excluded = not negated
        return excluded

    def unused(self) -> list[str]:
        """Entries that never matched one path, in the order they were written."""
        return [
            raw for index, (_negated, _pattern, raw) in enumerate(self._entries) if index not in self._used
        ]


def unused_exclude(manifest_path: Path, pattern: str) -> str:
    """One 'exclude' entry that matched nothing over this build.

    Not a fault: the template's own manifest excludes 'notes', which the
    template does not have, and refusing that would refuse Foundry's own
    starting shape. Printed rather than silent for the same reason a drop
    already agreed to is still printed on every build: a line an author
    cannot see is a line they cannot check. It takes effect on its own the
    day this plugin's content grows to hold something it matches.
    """
    return (
        f"{manifest_path}: 'exclude' names '{pattern}', which matched nothing in this build.\n"
        f"  Unused today. It takes effect the day this plugin holds something it matches."
    )


def skipping(forbidden: frozenset[Path], excludes: Excludes, root: Path):
    """`ignored`, the two directories this build owns, and every excluded file.

    `shutil.copytree` asks this before it descends into anything, and it asks
    at each level rather than once at the top. That is the only place the
    destination and the staging directory can be caught when either sits
    deeper than a direct child of the plugin root, and it is also what lets
    `exclude` reach a nested path rather than only a top-level name.

    `--out build/dist` is the case the destination/staging half exists for.
    `build` is an ordinary top-level directory, so it is copied entire, and
    the staging directory sitting inside it would be copied into itself until
    the path is too long for the filesystem: a `shutil.Error` with no next
    step in it, on the first build rather than the second.

    A directory is never added to what this returns. Only a file is decided
    here, once and for all: a directory that one entry excludes might still
    hold a path a later, more specific entry reincludes, and `copytree` can
    only see what is inside a directory it was allowed to descend into. So
    every directory is walked regardless of what excludes it, every file
    inside is checked on its own full relative path against every entry, and
    whatever a walk like that leaves without a single file inside it is not a
    directory anyone asked to keep: `_prune_empty_directories` sweeps it once
    the top-level entry it came from is done, rather than shipping it empty.
    """

    def ignore(directory: str, names: list[str]) -> set[str]:
        here = Path(directory)
        skipped = ignored(directory, names)
        excluded_names = set(skipped)
        relative_dir = here.resolve().relative_to(root)
        for name in names:
            if name in skipped:
                continue
            candidate = here / name
            if candidate.resolve() in forbidden:
                excluded_names.add(name)
                continue
            relative = (relative_dir / name).as_posix()
            matched = excludes.matches(relative)
            if matched and candidate.is_file():
                excluded_names.add(name)
        return excluded_names

    return ignore


def _prune_empty_directories(directory: Path) -> None:
    """Remove `directory`, and everything under it, that ended up holding nothing.

    A directory that an 'exclude' entry matches is never skipped outright by
    `skipping`'s `ignore` callback: a later, more specific entry might still
    reinclude one path inside it, which a directory-level skip could never
    let happen. So every directory is walked and every file inside it is
    decided on its own, and what that walk leaves picked clean afterward is
    not a directory anyone asked to keep. It is bookkeeping the copy is left
    holding, swept here rather than shipped as an empty folder no harness
    reads.
    """
    if not directory.is_dir():
        return
    for child in sorted(directory.iterdir()):
        if child.is_dir():
            _prune_empty_directories(child)
    if not any(directory.iterdir()):
        directory.rmdir()


def copy_own_content(manifest: dict, out: Path, skip: tuple[Path, ...] = ()) -> dict[str, str]:
    """Everything in the plugin repo except what never ships.

    Returns every item it wrote under a content directory, credited to this
    plugin, so that a dependency later handing over the same name is caught.
    The plugin's own content goes down first, and without this the dependency
    would quietly overwrite it. Every direct child of a content directory is
    credited, dot names included: a path nobody is credited with is a path a
    dependency can write over, and an uncredited directory is worse than an
    uncredited file because `copytree` raises `FileExistsError` on it rather
    than overwriting quietly. `drop_placeholders` gives back the credit for
    anything it removes, so this map stays the set of paths actually in the
    tree and never refuses on behalf of a file that is no longer there.

    `skip` names this build's own two directories, and both have to be named
    because `--out dist` puts both of them inside the plugin being read.

    | Path | What it does if it is not skipped |
    |---|---|
    | the destination | the second `--out dist` copies the whole of the first run's release into the new one, and the third copies the second's copy of the first |
    | the staging directory | it is created beside the destination, so `--out dist` puts it in the plugin root, and copying the plugin root copies the staging directory into itself until the path is too long for the filesystem |

    The second one fails on the first build, not the second, and `--out dist` is
    the command the template's README gives everybody. Both are matched by
    resolved path rather than by name: `dist` is a convention in a README and
    the flag takes anything. Both are matched at every level rather than only
    at the top, because the flag takes a path as well as a name and `--out
    build/dist` puts them under a directory that is itself copied whole.

    `exclude` entries are globs, checked with negation and precedence by
    `Excludes`, whose own docstring is the fuller account of what they mean;
    this function is only where that matcher gets applied, once per top-level
    entry and once more, recursively, for everything below it by way of
    `skipping`'s `ignore` callback. An entry that matched nothing over this
    walk is printed by `unused_exclude` rather than refused: it is real the
    day this plugin's content grows to match it, not a fault today.
    """
    excludes = Excludes(manifest["exclude"])
    forbidden = frozenset(path.resolve() for path in skip)
    root = manifest["root"].resolve()
    ignore = skipping(forbidden, excludes, root)
    placed: dict[str, str] = {}
    for entry in sorted(manifest["root"].iterdir()):
        if entry.name in NEVER_SHIP:
            continue
        if entry.resolve() in forbidden:
            continue
        target = out / entry.name
        if entry.is_dir():
            # Checked for its own sake, purely so a directory-only entry with
            # nothing excluded inside it is not misreported as unused: a
            # directory match is never a reason to skip the copytree call
            # below, since a later entry might still reinclude a path inside.
            excludes.matches(entry.name)
            shutil.copytree(entry, target, ignore=ignore)
            _prune_empty_directories(target)
        else:
            if excludes.matches(entry.name):
                continue
            shutil.copy2(entry, target)
        if entry.name in CONTENT_DIRS and target.is_dir():
            for item in sorted(target.iterdir()):
                placed[f"{entry.name}/{item.name}"] = manifest["id"]
    for pattern in excludes.unused():
        print(unused_exclude(manifest["manifest_path"], pattern))
    return placed


def drop_placeholders(out: Path, placed: dict[str, str]) -> None:
    """A placeholder is not content, so it neither ships nor holds a directory open.

    A file such as `.gitkeep` exists to make git keep an empty directory, and
    the folder that ships is not a git repository. Left in, it is a file no
    harness reads sitting inside that folder's `contents` fingerprint, which is
    the invariant that no harness folder holds a file that harness does not
    read. It is also credited as an item this plugin placed, so a dependency
    carrying the same placeholder is reported as a second source for a file
    neither of them ships on purpose.

    This is the rule `emitters.declared_kinds` already states, that a dot file
    does not declare a kind, applied to the copy rather than to the census. The
    Foundry template ships four content directories held open by placeholders
    precisely so a fresh plugin repository has somewhere to put its first skill,
    and none of the four should reach anyone who installs it.

    Only the top level of each content directory is swept. Inside a skill
    directory a dot file is that skill's own business, and a directory that
    still holds something is left alone.

    `placed` is the map of what is in the tree and who put it there, so a file
    removed here gives its credit back. Left in, the map would name a path that
    no longer exists, and a dependency handing over that same name would be
    refused as a second source for a file nobody ships.
    """
    for kind in CONTENT_DIRS:
        directory = out / kind
        if not directory.is_dir():
            continue
        for entry in sorted(directory.iterdir()):
            if entry.name.startswith(".") and entry.is_file():
                entry.unlink()
                placed.pop(f"{kind}/{entry.name}", None)
        if not any(directory.iterdir()):
            directory.rmdir()


def check_take_entry(manifest: dict, dependency: dict, kind: str, item: object) -> None:
    """One plain name, sitting directly in that dependency's content directory.

    The entry is used unchanged on both sides of the copy: read from
    `<dependency>/<kind>/<item>`, written to `<kind>/<item>` in the neutral
    tree. So anything in it that walks walks on both sides, and fencing `kind`
    against `CONTENT_DIRS` alone leaves the fence open. `take: {skills:
    ["../mcp.json"]}` reads a file that is not content at all and writes it to
    the root of the shipped folder, over the plugin's own `mcp.json` if it has
    one. Nothing catches it on the way past: the collision map is keyed on the
    literal string, and nothing else ever writes `skills/../mcp.json`.

    That is the case this check exists for. MCP servers are always the plugin's
    own and are the one thing a dependency may not hand over, and without a
    fence on the entry a dependency hands one over on the priority channel,
    silently, under its own server name.
    """
    if isinstance(item, str) and item not in ("", ".", "..") and "/" not in item and "\\" not in item:
        return
    raise BuildError(
        f"{manifest['manifest_path']}: cannot take '{item}' from {dependency['id']}.\n"
        f"  Declared under take.{kind}.\n"
        f"  A take entry is one plain name sitting directly in that dependency's\n"
        f"  {kind}/ directory, with no '/' and no '..'. An entry that walks reads\n"
        f"  something that is not content and writes it outside {kind}/, and a\n"
        f"  dependency hands over {', '.join(CONTENT_DIRS)} and nothing else.\n"
        f"  Name the item itself, or ask {dependency['id']} to put it in {kind}/."
    )


def copy_dependency_content(manifest: dict, out: Path, placed: dict[str, str]) -> list[dict]:
    """The exact items this plugin asked for from each dependency.

    `placed` maps every path already written to whoever wrote it, so the
    second writer to the same path is caught rather than silently winning.
    That map is keyed on `<kind>/<item>`, which is only a path inside the
    neutral tree because `check_take_entry` has already refused everything that
    is not one.
    """
    taken = []
    for dependency in manifest["dependencies"]:
        source_root = dependency["path"]
        for kind, items in sorted(dependency["take"].items()):
            if kind not in CONTENT_DIRS:
                raise BuildError(
                    f"{manifest['manifest_path']}: cannot take '{kind}' from {dependency['id']}.\n"
                    f"  A dependency hands over {', '.join(CONTENT_DIRS)} and nothing else."
                )
            for item in items:
                check_take_entry(manifest, dependency, kind, item)
                source = source_root / kind / item
                if not source.exists():
                    raise BuildError(
                        f"{manifest['manifest_path']}: {dependency['id']} has no {kind}/{item}.\n"
                        f"  looked in: {source}\n"
                        f"  Either the name is wrong, or the dependency stopped providing it."
                    )
                link = source if source.is_symlink() else (find_symlink(source) if source.is_dir() else None)
                if link is not None:
                    raise BuildError(
                        f"{manifest['manifest_path']}: cannot take '{item}' from {dependency['id']}.\n"
                        f"  Declared under take.{kind}.\n\n"
                        f"  {link} is a symlink. This is the same refusal fingerprint()\n"
                        f"  already raises on {dependency['id']}'s own checkout, checked again\n"
                        f"  here because this is the point the copy actually happens: copying\n"
                        f"  dereferences a symlink instead of copying it, so what ships could\n"
                        f"  otherwise hold something that dependency's own pin never measured.\n\n"
                        f"  Remove the symlink from {dependency['id']}, or replace it with a\n"
                        f"  real copy of what it points to."
                    )
                relative = f"{kind}/{item}"
                if relative in placed:
                    raise BuildError(
                        f"TWO SOURCES FOR THE SAME THING.\n\n"
                        f"  {relative} comes from both {placed[relative]} and {dependency['id']}.\n\n"
                        f"  Only one can ship, and picking one silently would mean nobody\n"
                        f"  finds out which. Rename one, or stop taking one of them."
                    )
                placed[relative] = dependency["id"]

                target = out / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                if source.is_dir():
                    shutil.copytree(source, target, ignore=ignored)
                else:
                    shutil.copy2(source, target)
                taken.append({"from": dependency["id"], "item": relative})
    return taken


def check_provides(manifest: dict, out: Path) -> None:
    """Everything the plugin claims to provide has to actually be there."""
    missing = []
    for kind, items in sorted((manifest["provides"] or {}).items()):
        if kind not in CONTENT_DIRS:
            raise BuildError(
                f"{manifest['manifest_path']}: 'provides' lists '{kind}'.\n"
                f"  A plugin provides {', '.join(CONTENT_DIRS)} and nothing else."
            )
        for item in items or []:
            if not (out / kind / item).exists():
                missing.append(f"{kind}/{item}")
    if missing:
        raise BuildError(
            "CLAIMS SOMETHING IT DOES NOT HAVE.\n\n  "
            + "\n  ".join(missing)
            + f"\n\n  Listed under 'provides' in {manifest['manifest_path']}, but absent\n"
            "  from the built folder. Either add them, or stop claiming them."
        )


def survived_take(taken: list[dict], tree: Path) -> list[dict]:
    """What `taken` looks like once this one harness's own folder is finished.

    `taken` is built once, against the single neutral tree every harness
    starts from, before any of them has pruned a thing. Handing that same list
    to every target's lock file describes the neutral tree, not the folder the
    lock file sits inside: a pi folder built with `degrade.pi.drop: [agents]`
    holds no agents/ directory at all, and the unfiltered list still recorded
    it as having taken agents/auditor.md from wherever that came from. A lock
    file is a record of the folder it ships in, so what it calls `took` has to
    be checked against what `emitters.run` actually left standing in `tree`,
    not against what the build handed every folder to start from.
    """
    return [entry for entry in taken if (tree / entry["item"]).exists()]


def take_left_behind(tree: Path) -> list[str]:
    """A file-level loss an emitter left in the tree for write_lock to find.

    Kind-level loss already has a home: the framework decides it before any
    folder is written, and `write_lock` reads it off the `Loss` it was handed.
    A file-level loss does not, because deciding one means reading the tree
    that folder ends up holding, which only the emitter that wrote it has done.
    `instructions.py` is the one emitter that has this today: it keeps only
    what its own generated index names and prunes everything else, one path at
    a time, and a file nobody named is not a kind the framework's `Loss` object
    has any way to describe.

    So the emitter leaves the list under `LEFT_BEHIND_NAME`, in the same tree
    it just finished writing, and this is the only other place that name is
    read. Removed the moment it is read, whether or not anything was in it, so
    it never ships and is never inside the `contents` fingerprint measured
    right after this returns.
    """
    path = tree / LEFT_BEHIND_NAME
    if not path.is_file():
        return []
    names = json.loads(path.read_text())
    path.unlink()
    return names


def write_lock(answer: dict, taken: list[dict], tree: Path, target: str, loss, name_the_target: bool) -> dict:
    """A record of what actually went in, written last so it can be complete.

    This is history, not instructions. Nothing reads it to reproduce a build.
    It exists so that when a shipped plugin misbehaves, the exact set of things
    it was built from is a fact rather than a reconstruction. Every recorded
    drop lands here too, so a folder that is missing something says so from
    inside itself rather than only in the release record beside it. That
    includes a loss no kind can name: `take_left_behind` reads back whatever
    the emitter that just ran left in the tree for this purpose, the moment
    before it stops being readable.

    The harness name and the drops are written only when the manifest named
    `targets` at all. A manifest that never mentions targets has to keep
    producing the bytes it produced before the key existed, and a lock file is
    part of the folder that ships.

    `contents` is measured before this file is written, so a lock file is never
    inside its own fingerprint.
    """
    lock = dict(answer)
    lock["took"] = taken
    if name_the_target:
        lock["target"] = target
        lock["dropped"] = [{"kind": drop.kind, "why": drop.why} for drop in loss.dropped]
        # Written only when there is one. A folder built from a plugin with no
        # `only` on any rule keeps the bytes it produced before the key existed,
        # and those bytes are inside every pin anyone has already written.
        if loss.rules:
            lock["rules"] = [{"at": rule.at, "run": rule.run, "why": rule.why} for rule in loss.rules]
    # Read for every target, not only the ones that name harnesses: nothing
    # else ever writes this file, so on every target but the one that does,
    # this call finds nothing and costs one is_file() check.
    left_behind = take_left_behind(tree)
    if left_behind:
        lock["left_behind"] = left_behind
    lock["contents"] = fingerprint(tree)
    (tree / LOCK_NAME).write_text(json.dumps(lock, indent=2) + "\n")
    record = {"target": target, "contents": lock["contents"], "dropped": lock.get("dropped", [])}
    if lock.get("rules"):
        record["rules"] = lock["rules"]
    if lock.get("left_behind"):
        record["left_behind"] = lock["left_behind"]
    return record


def write_release(answer: dict, records: list[dict], out: Path) -> None:
    """One tag, one version, one resolution answer, and N folders under it.

    The version names the source and the resolution answer, not the capability
    set. The same version across five folders means the same source tree, the
    same dependency pins and the same Foundry. It does not mean the same
    contents, and the per-harness fingerprint below differs by construction.
    The shipped folder is the unit people install, so the folder is the thing
    that gets fingerprinted.
    """
    release = {
        "plugin": answer["plugin"],
        "version": answer["version"],
        "foundry": answer["foundry"],
        "built_with_foundry": answer["built_with_foundry"],
        "targets": records,
    }
    (out / RELEASE_NAME).write_text(json.dumps(release, indent=2) + "\n")


def built_by_this_tool(out: Path) -> bool:
    """One folder carries a lock file; a release of several carries a record."""
    return (out / LOCK_NAME).exists() or (out / RELEASE_NAME).exists()


def build(plugin_dir: Path, out: Path) -> dict:
    """Assemble beside the destination, move into place only once it is whole.

    A refusal happens partway through: a collision is only found once the file
    that collides is about to be written. If the half-written folder stayed on
    disk, the refusal above would then fire on every later build into the same
    place and say the folder was not built by this tool, which is false and
    names no correct next step. So nothing appears at `out` unless the build
    finished, and a build that was refused can simply be run again.

    With one harness named, or none, the folder at `out` is the plugin, which
    is what every existing marketplace listing points at. With two or more,
    `out` holds one complete folder per harness and the release record beside
    them. The count decides the layout, so nothing changes for a plugin that
    ships to one place.
    """
    answer = resolve(plugin_dir)
    manifest = read_manifest(plugin_dir)
    targets = manifest["targets"]

    if out.exists() and not built_by_this_tool(out) and any(out.iterdir()):
        raise BuildError(
            f"{out} already has things in it and was not built by this tool.\n"
            f"  Refusing to overwrite. Point --out somewhere empty."
        )

    out.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{out.name}-building-", dir=out.parent))
    work = staging / out.name
    work.mkdir()
    try:
        # One neutral tree, assembled once. Every harness gets a private copy
        # of it, so no emitter can be reached by what another emitter did.
        neutral = staging / "neutral"
        neutral.mkdir()
        placed = copy_own_content(manifest, neutral, skip=(out, staging))
        drop_placeholders(neutral, placed)
        taken = copy_dependency_content(manifest, neutral, placed)
        check_provides(manifest, neutral)
        emitters.check_skills_are_one_level_deep(neutral, manifest["manifest_path"])
        emitters.check_rules(neutral, manifest["manifest_path"], tuple(targets))

        declared = emitters.declared_kinds(neutral)
        rules = emitters.hook_rules(neutral)
        losses = emitters.plan(targets, declared, manifest["degrade"], manifest["manifest_path"], rules)

        records = []
        for target in targets:
            tree = work / target if len(targets) > 1 else work
            shutil.copytree(neutral, tree, dirs_exist_ok=True)
            emitters.run(target, manifest, tree)
            records.append(
                write_lock(
                    answer,
                    survived_take(taken, tree),
                    tree,
                    target,
                    losses[target],
                    manifest["targets_declared"],
                )
            )
        if len(targets) > 1:
            write_release(answer, records, work)

        if out.exists():
            shutil.rmtree(out)
        work.rename(out)
    finally:
        shutil.rmtree(staging, ignore_errors=True)

    answer["took"] = taken
    answer["targets"] = records
    answer["contents"] = records[0]["contents"]
    return answer


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a plugin repo into a shippable folder.")
    parser.add_argument(
        "plugin", nargs="?", type=Path, default=Path.cwd(), help="the plugin repo (default: here)"
    )
    parser.add_argument("--out", type=Path, help="where the folder goes")
    parser.add_argument("--check", action="store_true", help="build to a temporary folder and throw it away")
    args = parser.parse_args()

    if not args.out and not args.check:
        parser.error("give --out, or --check to build without keeping anything")

    plugin_dir = args.plugin.resolve()
    temporary = None
    try:
        if args.check:
            temporary = tempfile.mkdtemp(prefix="foundry-check-")
            destination = Path(temporary) / "built"
        else:
            destination = args.out.resolve()

        answer = build(plugin_dir, destination)
    except (BuildError, ResolveError, EmitError) as problem:
        print(f"\n{problem}\n", file=sys.stderr)
        return 1
    finally:
        if temporary:
            shutil.rmtree(temporary, ignore_errors=True)

    print(f"{answer['plugin']} {answer['version']}")
    print(f"  built with Foundry {answer['built_with_foundry']}, resolved to {answer['foundry']}")
    print(f"  dependencies: {len(answer['dependencies'])}, items taken: {len(answer['took'])}")
    records = answer["targets"]
    if len(records) == 1:
        print(f"  contents: {records[0]['contents']}")
    else:
        width = max(len(record["target"]) for record in records)
        for record in records:
            print(f"  {record['target']:<{width}}  contents: {record['contents']}")
    # Every drop was written down by the author before the build would run, and
    # it is printed anyway. A loss agreed to months ago is still a loss shipping
    # today, and the person watching the build is the last one who can notice.
    for record in records:
        for drop in record["dropped"]:
            print(f"  dropped {drop['kind']} from {record['target']}: {drop['why']}")
        for rule in record.get("rules", []):
            print(f"  dropped the hook at {rule['at']} from {record['target']}: {rule['why']}")
    if not args.check:
        print(f"  written to: {destination}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
