#!/usr/bin/env python3
"""Real plugin repositories, built and proved to still emit what they emitted before.

`template/` proves very little on its own. It carries one skill, `feedback`,
and holds `agents/` and `commands/` open with a `.gitkeep` the build deletes
before anything ships. Its `exclude` is five flat top-level names. Nothing in
it is nested, nothing in it is a glob, nothing in it depends on another plugin,
and nothing in it is negated. So all five of the template's fingerprints can
sit exactly where they are while a change to `exclude`, to a dependency `take`,
or to a skill nested two directories too deep breaks every plugin repository
actually built with Foundry, and the template job still prints green.

This check closes that hole the direct way: it builds the plugin repositories
that actually exist, rather than a shape standing in for them, and compares
what came out against what the same source built the last time somebody ran
`--record`. Two sources feed it.

| Source | What it proves |
|---|---|
| `tests/fixtures/` | committed, so a clone runs a real check. Cases built to carry what the template does not: nested paths sharing a name with a top-level exclude, a directory `exclude` cannot see, entries a future negation would reach into |
| Whatever `repos.local` names | real manifests, real dependency pins, real content nobody wrote for a test. Not committed, and neither are its baselines |

Comparing by a single hash per plugin would say something moved and never say
what. So a baseline under `.github/checks/baselines/<id>.json` records, per
harness folder that plugin's manifest asked for, every relative file path in it
against a digest of that file's bytes, plus that folder's own `contents`
fingerprint read out of its `foundry.lock.json`. A file that appeared, a file
that vanished and a file whose bytes changed are three different failures, and
each one is named by path.

A file list alone was not enough, and the case that proves it is the one this
check will meet first. Changing what a lock file records rewrites bytes inside
`foundry.lock.json` in every folder of every plugin while adding and removing
nothing, so a list-only baseline goes red everywhere at once and names no file.
The per-file digest is what turns that into a line per lock file. The folder's
`contents` fingerprint is kept beside it as a cross-check: it is what a pin
downstream is actually written against, so a report that named files without
naming it would leave out the number that breaks somebody else's build.

A plugin naming exactly one target, or none, emits its content at the root of
the output directory: no per-target subdirectory, no `foundry.release.json`.
Both shapes are real and both are built here. `describe()` below builds either
by asking the build's own answer how many targets it wrote, rather than
assuming the multi-target layout and special-casing the other one.

Dependency pins are not re-checked here. `resolve.py`'s own `check_pins`
already refuses the build the moment a pin stops matching a dependency's
fingerprint, so building a plugin that pins another exercises it. Writing a
second copy of that check here would just be a second copy to keep in sync
with the first.

Never write into the repository being built, and never write an absolute path
into anything this check produces. Every repository is built into a temporary
directory that is removed once it has been read, and a baseline records file
paths relative to the folder they came from and a plugin id, nothing about
where that plugin's source sat on the machine that recorded it.

Operate:
    python3 .github/checks/repos.py                  build everything found, compare
    python3 .github/checks/repos.py --record          build everything found, record baselines
    python3 .github/checks/repos.py PATH [PATH ...]   only these repos, discovery skipped entirely

To add your own repositories, write one path per line in `repos.local` beside
this file. Blank lines and `#` comments are ignored, and a relative path is
read from the repository root. That file and the baselines recorded from it
are both ignored by git.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from harnesses import LOCK_NAME  # noqa: E402
from report import Report  # noqa: E402

import build  # noqa: E402
from build import BuildError  # noqa: E402
from emitters import EmitError  # noqa: E402
from resolve import ResolveError  # noqa: E402

FOUNDRY_ROOT = Path(__file__).resolve().parents[2]
BASELINES_DIR = Path(__file__).resolve().parent / "baselines"
FIXTURES_DIR = FOUNDRY_ROOT / "tests" / "fixtures"
MANIFEST_NAME = "foundry.plugin.yaml"

# Where somebody's own plugin repositories are listed, one path per line. Both
# this file and the baselines recorded from it are ignored by git, and that is
# the point rather than an accident of convenience.
#
# Foundry keeps no list of the plugins built with it. It learns nothing about
# who uses it until somebody chooses to tell it, and a tuple of seven names
# committed here would be exactly that list, published, naming repositories and
# recording what each one ships. So the names live on the machine that has the
# repositories, the fixtures below are the only plugins this repository knows
# about, and a clone with no local file still runs a real check.
LOCAL_LIST = Path(__file__).resolve().parent / "repos.local"
LOCAL_BASELINES = BASELINES_DIR / "local"


def discover_local() -> list[Path]:
    """The repositories named in `repos.local`, if there is one.

    A path that is not there is reported and skipped rather than failing the
    run, because a list written on one machine is expected to be wrong on
    another, and that is not the failure this check exists to report.
    """
    if not LOCAL_LIST.is_file():
        return []
    found = []
    for line in LOCAL_LIST.read_text().splitlines():
        entry = line.split("#", 1)[0].strip()
        if not entry:
            continue
        candidate = Path(entry).expanduser()
        if not candidate.is_absolute():
            candidate = (FOUNDRY_ROOT / candidate).resolve()
        if candidate.is_dir() and (candidate / MANIFEST_NAME).is_file():
            found.append(candidate)
        else:
            print(f"skipping {entry}: no {MANIFEST_NAME} at {candidate}")
    return found


def discover_fixtures() -> list[Path]:
    """Every fixture under tests/fixtures/, found rather than named by hand here.

    A fixture the next agent adds gets built and baselined the moment it lands
    in that directory, with nothing in this file to update. `tests/fixtures/`
    holds its own README rather than a manifest, so a directory with no
    foundry.plugin.yaml in it, that one included, is silently not a fixture.
    """
    if not FIXTURES_DIR.is_dir():
        return []
    return sorted(
        path for path in FIXTURES_DIR.iterdir() if path.is_dir() and (path / MANIFEST_NAME).is_file()
    )


def digest(path: Path) -> str:
    """A short digest of one shipped file's bytes.

    Twelve hex characters, the same width `contents` prints at, so a baseline
    reads at a glance rather than as a wall of sixty-four-character hashes.
    Nothing here defends against a chosen collision: this compares a build
    against the same build's own output on a machine that already trusts both,
    and the shorter value is worth more than a threat that is not in the room.
    """
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]


def describe(plugin_dir: Path) -> dict:
    """Build `plugin_dir` into a throwaway directory, and describe what shipped.

    Raises `BuildError`, `ResolveError` or `EmitError` straight out of the
    build, uncaught. A real defect in a real plugin has to stop this check the
    same way it would stop a release; catching it here and reporting "no
    baseline to compare" would turn a build failure into a quieter and
    different kind of red.
    """
    with tempfile.TemporaryDirectory(prefix="foundry-repos-") as scratch:
        out = Path(scratch) / "out"
        answer = build.build(plugin_dir, out)
        targets = [record["target"] for record in answer["targets"]]
        # One target, or none named at all, ships at the root of `out` with no
        # subdirectory of its own. Two or more each get a folder named for the
        # target. Asking the build's own answer which shape it wrote, instead
        # of assuming the multi-target layout, is what lets this function build
        # a single-target plugin the same way it builds everything else.
        folders = {targets[0]: out} if len(targets) == 1 else {name: out / name for name in targets}

        described: dict[str, dict] = {}
        for name, folder in folders.items():
            files = {
                str(path.relative_to(folder)): digest(path)
                for path in sorted(folder.rglob("*"))
                if path.is_file()
            }
            lock = json.loads((folder / LOCK_NAME).read_text())
            described[name] = {"files": files, "contents": lock["contents"]}
        return {"id": answer["plugin"], "targets": targets, "folders": described}


def baseline_path(plugin_id: str, plugin_dir: Path) -> Path:
    """Where this plugin's baseline is kept.

    A fixture's goes beside the other fixtures and is committed, because the
    fixtures are this repository's own. Anything else goes under `local/`,
    which is ignored by git for the reason `LOCAL_LIST` explains: a baseline
    names a plugin and lists every file it ships, so committing one would
    publish a plugin Foundry is not supposed to know exists.
    """
    if plugin_dir.is_relative_to(FIXTURES_DIR):
        return BASELINES_DIR / f"{plugin_id}.json"
    return LOCAL_BASELINES / f"{plugin_id}.json"


def record(plugin_dir: Path) -> str:
    """Write this plugin's baseline, overwriting whatever was recorded before."""
    baseline = describe(plugin_dir)
    path = baseline_path(baseline["id"], plugin_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(baseline, indent=2, sort_keys=True) + "\n")
    return baseline["id"]


def compare(plugin_dir: Path, report: Report) -> None:
    """This plugin, built now, against the baseline recorded for it.

    Every difference is reported, not just the first: a change that moved one
    file and one fingerprint should say both, because whoever reads this is
    about to decide whether the whole thing was intended.
    """
    built = describe(plugin_dir)
    plugin_id = built["id"]
    path = baseline_path(plugin_id, plugin_dir)
    if not path.is_file():
        report.wrong(
            f"{plugin_id}: no recorded baseline at {path.relative_to(FOUNDRY_ROOT)}. "
            f"Run with --record once to create it."
        )
        return
    recorded = json.loads(path.read_text())

    if recorded["targets"] != built["targets"]:
        report.wrong(
            f"{plugin_id}: 'targets' changed. recorded {recorded['targets']}, built {built['targets']}."
        )

    for target in sorted(set(recorded["folders"]) | set(built["folders"])):
        before = recorded["folders"].get(target)
        after = built["folders"].get(target)
        if before is None:
            report.wrong(f"{plugin_id} {target}: this folder is new; the baseline never recorded it.")
            continue
        if after is None:
            report.wrong(f"{plugin_id} {target}: this folder is missing; the baseline recorded one.")
            continue
        for entry in sorted(set(after["files"]) - set(before["files"])):
            report.wrong(f"{plugin_id} {target}: {entry} appeared.")
        for entry in sorted(set(before["files"]) - set(after["files"])):
            report.wrong(f"{plugin_id} {target}: {entry} vanished.")
        for entry in sorted(set(before["files"]) & set(after["files"])):
            if before["files"][entry] != after["files"][entry]:
                report.wrong(f"{plugin_id} {target}: {entry} changed.")
        if before["contents"] != after["contents"]:
            # Reported alongside the files rather than instead of them. This is
            # the number a downstream pin is written against, so it is what
            # somebody else's build refuses on, and every line above is only the
            # explanation of why it moved.
            report.wrong(
                f"{plugin_id} {target}: the contents fingerprint moved from "
                f"{before['contents']} to {after['contents']}."
            )


def main() -> int:
    parser = argparse.ArgumentParser(description="Build real plugin repositories and prove they match.")
    parser.add_argument(
        "paths", nargs="*", type=Path, help="build only these repositories, instead of discovering"
    )
    parser.add_argument("--record", action="store_true", help="write baselines instead of comparing")
    args = parser.parse_args()

    repos = [path.resolve() for path in args.paths] if args.paths else discover_fixtures() + discover_local()
    if not repos:
        sys.exit("no plugin repository found to build. Pass one or more paths explicitly.")

    if args.record:
        # Said loudly and first, because a careless --record overwrites the one
        # thing this check compares against and there is no undo for that.
        print(f"RECORDING {len(repos)} baseline(s). This overwrites whatever was recorded before.")
        for repo in repos:
            try:
                plugin_id = record(repo)
            except (BuildError, ResolveError, EmitError) as broken:
                sys.exit(f"{repo} would not build, so nothing was recorded for it:\n\n{broken}")
            print(f"  recorded {plugin_id}")
        return 0

    report = Report()
    for repo in repos:
        try:
            compare(repo, report)
        except (BuildError, ResolveError, EmitError) as broken:
            sys.exit(f"{repo} would not build:\n\n{broken}")

    if report.problems:
        report.wrong(
            "Either this change was intended, and the baseline should be re-recorded with "
            "--record, or it was not, and this is the bug."
        )
    report.finish(f"every one of {len(repos)} plugin repositories built exactly what its baseline recorded")
    return 0


if __name__ == "__main__":
    sys.exit(main())
