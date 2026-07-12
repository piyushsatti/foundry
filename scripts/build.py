#!/usr/bin/env python3
"""Materialize plugin bundles: bundles/<name>/ (source) -> plugins/<name>/ (self-contained output).

Structure: each bundles/<name>/bundle.yaml declares build (bool), compose
(skills/agents from library/, packages from packages/ with optional sidecars),
and exclude globs. Everything else in the bundle dir ships verbatim.

Why: main holds only DRY source; plugins/ is gitignored build output. CI runs
this on release and publishes plugins/ to the release ref the marketplace serves.
Generalizes the old plugins/manifold/scripts/vendor_sync.py (retired).

Operate:
    python3 scripts/build.py [--only NAME ...] [--check] [--out DIR]
--check builds to a temp dir and byte-diffs against the existing output dir
(release-ref drift gate; on main there is usually no output to compare).
Determinism is separately asserted by tests/test_build_determinism.py.
"""
from __future__ import annotations

import argparse
import filecmp
import fnmatch
import json
import shutil
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BUNDLES = REPO / "bundles"
PACKAGES = REPO / "packages"
LIBRARY = REPO / "library"
DEFAULT_OUT = REPO / "plugins"
MARKETPLACE_SRC = REPO / ".claude-plugin" / "marketplace.json"


# ---------------------------------------------------------------- bundle.yaml
def load_bundle_yaml(path: Path) -> dict:
    """Minimal parser for the fixed bundle.yaml shape (no PyYAML dependency).

    Recognizes: build (bool), compose.skills / compose.agents (inline or dash
    lists of strings), compose.packages (dash list of mappings with package/
    dest/sidecars), exclude (dash list of strings).
    """
    cfg: dict = {"build": False, "compose": {"skills": [], "agents": [], "packages": []}, "exclude": []}
    lines = path.read_text().splitlines()
    section = None  # None | 'compose' | 'exclude'
    subkey = None   # inside compose: 'skills' | 'agents' | 'packages'
    current_pkg: dict | None = None

    def parse_inline_list(val: str) -> list[str]:
        val = val.strip()
        if not (val.startswith("[") and val.endswith("]")):
            return []
        inner = val[1:-1].strip()
        return [x.strip().strip("'\"") for x in inner.split(",") if x.strip()]

    for raw in lines:
        line = raw.rstrip()
        if not line or line.lstrip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip())
        stripped = line.strip()

        if indent == 0:
            current_pkg = None
            if stripped.startswith("build:"):
                cfg["build"] = stripped.split(":", 1)[1].strip().lower() == "true"
                section = None
            elif stripped.startswith("compose:"):
                section = "compose"
                subkey = None
            elif stripped.startswith("exclude:"):
                section = "exclude"
                rest = stripped.split(":", 1)[1]
                if rest.strip():
                    cfg["exclude"] = parse_inline_list(rest)
            else:
                section = None
            continue

        if section == "compose" and indent == 2:
            current_pkg = None
            key, _, rest = stripped.partition(":")
            if key in ("skills", "agents", "packages"):
                subkey = key
                if rest.strip() and key != "packages":
                    cfg["compose"][key] = parse_inline_list(rest)
            continue

        if section == "compose" and subkey == "packages" and stripped.startswith("- "):
            current_pkg = {}
            cfg["compose"]["packages"].append(current_pkg)
            body = stripped[2:]
            if body.startswith("{"):  # inline mapping
                inner = body.strip("{}")
                for part in inner.split(","):
                    k, _, v = part.partition(":")
                    current_pkg[k.strip()] = v.strip().strip("'\"")
                current_pkg = None
            elif ":" in body:
                k, _, v = body.partition(":")
                current_pkg[k.strip()] = v.strip().strip("'\"")
            continue

        if section == "compose" and current_pkg is not None and ":" in stripped:
            k, _, v = stripped.partition(":")
            v = v.strip()
            current_pkg[k.strip()] = parse_inline_list(v) if v.startswith("[") else v.strip("'\"")
            continue

        if section == "compose" and subkey in ("skills", "agents") and stripped.startswith("- "):
            cfg["compose"][subkey].append(stripped[2:].strip().strip("'\""))
            continue

        if section == "exclude" and stripped.startswith("- "):
            cfg["exclude"].append(stripped[2:].strip().strip("'\""))
            continue

    return cfg


# ------------------------------------------------------------------- copying
def make_ignore(bundle_root: Path, patterns: list[str]):
    """shutil.copytree ignore callback honoring the exclude globs.

    Each glob is matched against the path relative to the bundle root, so
    "**/evals/**" style patterns behave as expected.
    """
    def _ignore(directory: str, names: list[str]) -> set[str]:
        rel_dir = Path(directory).relative_to(bundle_root)
        ignored = set()
        for name in names:
            rel = str(rel_dir / name) if str(rel_dir) != "." else name
            for pat in patterns:
                if (
                    fnmatch.fnmatch(rel, pat)
                    or fnmatch.fnmatch(name, pat)
                    # "**/x/**" should also kill the x dir itself
                    or fnmatch.fnmatch(rel + "/", pat.rstrip("*") + "*")
                    or fnmatch.fnmatch(rel, pat.replace("/**", ""))
                ):
                    ignored.add(name)
                    break
        return ignored

    return _ignore


def build_bundle(bdir: Path, out_root: Path) -> dict:
    """Materialize one bundle. Returns its marketplace entry."""
    name = bdir.name
    cfg = load_bundle_yaml(bdir / "bundle.yaml")
    dst = out_root / name

    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(bdir, dst, ignore=make_ignore(bdir, cfg["exclude"]), symlinks=False)

    # compose: promoted library capabilities
    for skill in cfg["compose"]["skills"]:
        src = LIBRARY / "skills" / skill
        if not src.is_dir():
            sys.exit(f"build: {name}: compose.skills '{skill}' not found in library/skills/")
        shutil.copytree(src, dst / "skills" / skill, dirs_exist_ok=False)
    for agent in cfg["compose"]["agents"]:
        src = LIBRARY / "agents" / agent
        if not src.is_dir():
            sys.exit(f"build: {name}: compose.agents '{agent}' not found in library/agents/")
        shutil.copytree(src, dst / "agents" / agent, dirs_exist_ok=False)

    # compose: vendored packages (+ sidecar files beside the package dir)
    for spec in cfg["compose"]["packages"]:
        pkg = spec["package"]
        dest = dst / spec["dest"]
        src_pkg = PACKAGES / pkg / pkg
        if not src_pkg.is_dir():
            sys.exit(f"build: {name}: package '{pkg}' not found at {src_pkg}")
        # compose.packages OWNS dest: replace any stale copy the verbatim
        # bundle copy carried along (e.g. a committed _vendor/ pre-flip).
        if dest.exists():
            shutil.rmtree(dest)
        dest.mkdir(parents=True)
        shutil.copytree(
            src_pkg,
            dest / pkg,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
            dirs_exist_ok=False,
        )
        sidecars = spec.get("sidecars", [])
        if isinstance(sidecars, str):
            sidecars = [sidecars]
        for sc in sidecars:
            sc_src = PACKAGES / pkg / sc
            if not sc_src.is_file():
                sys.exit(f"build: {name}: sidecar '{sc}' not found at {sc_src}")
            shutil.copy2(sc_src, dest / sc)

    pj = json.loads((dst / ".claude-plugin" / "plugin.json").read_text())
    return {"name": pj["name"], "source": f"./plugins/{name}", "description": pj["description"]}


def discover() -> list[Path]:
    return sorted(
        d for d in BUNDLES.iterdir()
        if d.is_dir() and (d / "bundle.yaml").exists() and load_bundle_yaml(d / "bundle.yaml")["build"]
    )


def build(out_root: Path, only: list[str] | None = None) -> list[dict]:
    out_root.mkdir(parents=True, exist_ok=True)
    entries = []
    for bdir in discover():
        if only and bdir.name not in only:
            continue
        entries.append(build_bundle(bdir, out_root))
        print(f"build: {bdir.name} -> {out_root / bdir.name}")
    return entries


# ---------------------------------------------------------------- marketplace
def write_marketplace(entries: list[dict], out_root: Path) -> None:
    """Regenerate the release-ref marketplace catalog next to the built plugins.

    Entries carry name/source/description only — never a version key
    (plugin.json is the sole version source; the docs warn a duplicated
    version silently masks bumps). Root .claude-plugin/marketplace.json on
    main is hand-maintained (git-subdir sources); this file serves the
    release ref where ./plugins/<name> paths exist.
    """
    src = json.loads(MARKETPLACE_SRC.read_text())
    catalog = {
        "name": src["name"],
        "owner": src["owner"],
        "description": src["description"],
        "plugins": sorted(entries, key=lambda e: e["name"]),
    }
    mp_dir = out_root / ".claude-plugin"
    mp_dir.mkdir(parents=True, exist_ok=True)
    (mp_dir / "marketplace.json").write_text(json.dumps(catalog, indent=2) + "\n")
    print(f"build: marketplace catalog -> {mp_dir / 'marketplace.json'}")


# ---------------------------------------------------------------------- check
def _rel_files(root: Path) -> set[str]:
    return {str(p.relative_to(root)) for p in root.rglob("*") if p.is_file()}


def check(out_root: Path) -> int:
    """Rebuild into a temp dir; byte-diff against out_root. 0 = clean."""
    if not out_root.is_dir():
        print(f"check: nothing at {out_root} to compare against (main has no committed output)")
        return 1
    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = Path(tmp) / "plugins"
        entries = build(tmp_root)
        write_marketplace(entries, tmp_root)
        fresh, committed = _rel_files(tmp_root), _rel_files(out_root)
        bad = []
        bad += [f"only in fresh build: {p}" for p in sorted(fresh - committed)]
        bad += [f"only in committed output: {p}" for p in sorted(committed - fresh)]
        for p in sorted(fresh & committed):
            if not filecmp.cmp(tmp_root / p, out_root / p, shallow=False):
                bad.append(f"content drift: {p}")
        if bad:
            print("check: DRIFT\n  " + "\n  ".join(bad))
            return 1
    print("check: clean")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    ap.add_argument("--only", nargs="*", help="build only these bundles")
    ap.add_argument("--check", action="store_true", help="drift-gate against existing output")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT, help="output root (default: plugins/)")
    args = ap.parse_args()

    if args.check:
        return check(args.out)
    entries = build(args.out, args.only)
    if not args.only:  # partial builds don't rewrite the catalog
        write_marketplace(entries, args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
