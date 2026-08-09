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


class BuildError(Exception):
    """The folder could not be written. The message is the whole report."""


def ignored(_directory: str, names: list[str]) -> set[str]:
    return {name for name in names if name in NEVER_SHIP or name.endswith((".pyc", ".pyo"))}


def skipping(forbidden: frozenset[Path]):
    """`ignored`, plus the two directories this build owns, at every level.

    `shutil.copytree` asks this before it descends into anything, and it asks
    at each level rather than once at the top. That is the only place the
    destination and the staging directory can be caught when either sits deeper
    than a direct child of the plugin root: a top-level filter never sees them,
    because the directory holding them was already handed to `copytree` whole.

    `--out build/dist` is the case. `build` is an ordinary top-level directory,
    so it is copied entire, and the staging directory sitting inside it is
    copied into itself until the path is too long for the filesystem. That is a
    `shutil.Error` with no next step in it, on the first build rather than the
    second.
    """

    def ignore(directory: str, names: list[str]) -> set[str]:
        here = Path(directory)
        skipped = ignored(directory, names)
        return skipped | {
            name for name in names if name not in skipped and (here / name).resolve() in forbidden
        }

    return ignore


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
    """
    excluded = set(manifest["exclude"])
    forbidden = frozenset(path.resolve() for path in skip)
    ignore = skipping(forbidden)
    placed: dict[str, str] = {}
    for entry in sorted(manifest["root"].iterdir()):
        if entry.name in NEVER_SHIP or entry.name in excluded:
            continue
        if entry.resolve() in forbidden:
            continue
        target = out / entry.name
        if entry.is_dir():
            shutil.copytree(entry, target, ignore=ignore)
        else:
            shutil.copy2(entry, target)
        if entry.name in CONTENT_DIRS and target.is_dir():
            for item in sorted(target.iterdir()):
                placed[f"{entry.name}/{item.name}"] = manifest["id"]
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


def write_lock(answer: dict, taken: list[dict], tree: Path, target: str, loss, name_the_target: bool) -> dict:
    """A record of what actually went in, written last so it can be complete.

    This is history, not instructions. Nothing reads it to reproduce a build.
    It exists so that when a shipped plugin misbehaves, the exact set of things
    it was built from is a fact rather than a reconstruction. Every recorded
    drop lands here too, so a folder that is missing something says so from
    inside itself rather than only in the release record beside it.

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
    lock["contents"] = fingerprint(tree)
    (tree / LOCK_NAME).write_text(json.dumps(lock, indent=2) + "\n")
    record = {"target": target, "contents": lock["contents"], "dropped": lock.get("dropped", [])}
    if lock.get("rules"):
        record["rules"] = lock["rules"]
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
                write_lock(answer, taken, tree, target, losses[target], manifest["targets_declared"])
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
