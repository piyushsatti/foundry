#!/usr/bin/env python3
"""Materialize plugin bundles: bundles/<name>/ (source) -> plugins/<name>/ (self-contained output).

Structure: each bundles/<name>/bundle.yaml declares build (bool), compose
(skills/agents from library/, packages from packages/ with optional sidecars),
and exclude globs. Everything else in the bundle dir ships verbatim. Skills
compose as directories (library/skills/<x>/), agents as single files
(library/agents/<x>.md).

Why: main holds only DRY source; plugins/ is gitignored build output. CI runs
this on release and publishes plugins/ to the release ref the marketplace serves.
bundle.yaml `build:` flags are the SINGLE owner of "what ships": this script
derives the release catalog, the root marketplace.json (git-subdir sources),
and the <!-- foundry:bundles --> doc blocks from them — never hand-edit those.

Operate:
    python3 scripts/build.py [--only NAME ...] [--check] [--out DIR]
    python3 scripts/build.py --sync         # regenerate root marketplace.json + doc blocks only
--check builds to a temp dir and byte-diffs against the existing output dir
(release-ref drift gate). CI asserts --sync leaves no diff (catalog/doc freshness).
Determinism is separately asserted by tests/test_build_determinism.py.
"""
from __future__ import annotations

import argparse
import filecmp
import fnmatch
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
BUNDLES = REPO / "bundles"
PACKAGES = REPO / "packages"
LIBRARY = REPO / "library"
DEFAULT_OUT = REPO / "plugins"
ROOT_MARKETPLACE = REPO / ".claude-plugin" / "marketplace.json"

# Repo-level catalog fields (the only non-derived marketplace content).
CATALOG_META = {
    "name": "foundry",
    "owner": {"name": "Piyush Satti"},
    "description": "Piyush's agentic infrastructure — memory curation, project-compass, review, orchestration, and dev-environment plugins.",
}
GIT_SUBDIR_URL = "https://github.com/piyushsatti/foundry.git"
RELEASE_REF = "release"

DOC_BLOCK_FILES = ["README.md", "CLAUDE.md", "AGENTS.md"]
DOC_BLOCK_RE = re.compile(
    r"<!-- foundry:bundles:start -->.*?<!-- foundry:bundles:end -->", re.DOTALL
)


def load_bundle_yaml(path: Path) -> dict:
    cfg = yaml.safe_load(path.read_text()) or {}
    compose = cfg.get("compose") or {}
    return {
        "build": bool(cfg.get("build", False)),
        "compose": {
            "skills": compose.get("skills") or [],
            "agents": compose.get("agents") or [],
            "packages": compose.get("packages") or [],
        },
        "exclude": cfg.get("exclude") or [],
    }


def make_ignore(bundle_root: Path, patterns: list[str]):
    """shutil.copytree ignore callback honoring the exclude globs (matched
    against paths relative to the bundle root)."""
    def _ignore(directory: str, names: list[str]) -> set[str]:
        rel_dir = Path(directory).relative_to(bundle_root)
        ignored = set()
        for name in names:
            rel = str(rel_dir / name) if str(rel_dir) != "." else name
            for pat in patterns:
                if (
                    fnmatch.fnmatch(rel, pat)
                    or fnmatch.fnmatch(name, pat)
                    or fnmatch.fnmatch(rel + "/", pat.rstrip("*") + "*")
                    or fnmatch.fnmatch(rel, pat.replace("/**", ""))
                    # "**/x/**" must also kill an x sitting at the copy root
                    or fnmatch.fnmatch(name, pat.replace("/**", "").replace("**/", ""))
                ):
                    ignored.add(name)
                    break
        return ignored

    return _ignore


def build_bundle(bdir: Path, out_root: Path) -> None:
    name = bdir.name
    cfg = load_bundle_yaml(bdir / "bundle.yaml")
    dst = out_root / name

    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(bdir, dst, ignore=make_ignore(bdir, cfg["exclude"]), symlinks=False)

    # compose: promoted library skills (directories) — same excludes as the
    # verbatim copy, so dev-only files (evals/, __pycache__) never ship
    for skill in cfg["compose"]["skills"]:
        src = LIBRARY / "skills" / skill
        if not src.is_dir():
            sys.exit(f"build: {name}: compose.skills '{skill}' not found in library/skills/")
        target = dst / "skills" / skill
        if target.exists():
            shutil.rmtree(target)  # compose owns its target
        shutil.copytree(src, target, ignore=make_ignore(src, cfg["exclude"]))

    # compose: promoted library agents (single .md files)
    for agent in cfg["compose"]["agents"]:
        src = LIBRARY / "agents" / f"{agent}.md"
        if not src.is_file():
            sys.exit(f"build: {name}: compose.agents '{agent}' not found in library/agents/")
        (dst / "agents").mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst / "agents" / f"{agent}.md")

    # compose: vendored packages (+ sidecar files beside the package dir)
    for spec in cfg["compose"]["packages"]:
        pkg = spec["package"]
        dest = dst / spec["dest"]
        src_pkg = PACKAGES / pkg / pkg
        if not src_pkg.is_dir():
            sys.exit(f"build: {name}: package '{pkg}' not found at {src_pkg}")
        if dest.exists():
            shutil.rmtree(dest)  # compose owns its target
        dest.mkdir(parents=True)
        shutil.copytree(
            src_pkg,
            dest / pkg,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
        )
        sidecars = spec.get("sidecars", [])
        if isinstance(sidecars, str):
            sidecars = [sidecars]
        for sc in sidecars:
            sc_src = PACKAGES / pkg / sc
            if not sc_src.is_file():
                sys.exit(f"build: {name}: sidecar '{sc}' not found at {sc_src}")
            shutil.copy2(sc_src, dest / sc)


def discover() -> list[Path]:
    return sorted(
        d for d in BUNDLES.iterdir()
        if d.is_dir() and (d / "bundle.yaml").exists() and load_bundle_yaml(d / "bundle.yaml")["build"]
    )


def plugin_meta(bdir: Path) -> dict:
    pj = json.loads((bdir / ".claude-plugin" / "plugin.json").read_text())
    return {"name": pj["name"], "description": pj["description"], "version": pj["version"]}


def build(out_root: Path, only: list[str] | None = None) -> None:
    out_root.mkdir(parents=True, exist_ok=True)
    for bdir in discover():
        if only and bdir.name not in only:
            continue
        build_bundle(bdir, out_root)
        print(f"build: {bdir.name} -> {out_root / bdir.name}")


# ------------------------------------------------------- generated artifacts
def release_catalog() -> dict:
    """Catalog for the release ref: relative ./plugins/<name> sources, no version key."""
    plugins = [
        {"name": m["name"], "source": f"./plugins/{m['name']}", "description": m["description"]}
        for m in (plugin_meta(b) for b in discover())
    ]
    return {**CATALOG_META, "plugins": sorted(plugins, key=lambda p: p["name"])}


def root_catalog() -> dict:
    """Catalog served on main: git-subdir sources pinned to the release ref, no version key."""
    plugins = [
        {
            "name": m["name"],
            "source": {
                "source": "git-subdir",
                "url": GIT_SUBDIR_URL,
                "path": f"plugins/{m['name']}",
                "ref": RELEASE_REF,
            },
            "description": m["description"],
        }
        for m in (plugin_meta(b) for b in discover())
    ]
    return {**CATALOG_META, "plugins": sorted(plugins, key=lambda p: p["name"])}


def doc_block() -> str:
    rows = [
        f"| `{m['name']}` | {m['version']} | {m['description']} |"
        for m in sorted((plugin_meta(b) for b in discover()), key=lambda m: m["name"])
    ]
    parked = sorted(
        d.name for d in BUNDLES.iterdir()
        if d.is_dir() and (d / "bundle.yaml").exists() and not load_bundle_yaml(d / "bundle.yaml")["build"]
    )
    lines = [
        "<!-- foundry:bundles:start -->",
        "<!-- generated by scripts/build.py --sync from bundles/*/bundle.yaml — do not edit -->",
        "| Bundle | Version | What it is |",
        "|--------|---------|------------|",
        *rows,
    ]
    if parked:
        lines.append(f"\nParked (source only, `build: false`): {', '.join(f'`{p}`' for p in parked)}")
    lines.append("<!-- foundry:bundles:end -->")
    return "\n".join(lines)


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")


def sync() -> None:
    """Regenerate everything derived from bundle.yaml flags on main:
    the root marketplace.json and the doc bundle-blocks."""
    write_json(ROOT_MARKETPLACE, root_catalog())
    print(f"sync: {ROOT_MARKETPLACE}")
    block = doc_block()
    for fname in DOC_BLOCK_FILES:
        f = REPO / fname
        if not f.is_file():
            continue
        text = f.read_text()
        if DOC_BLOCK_RE.search(text):
            f.write_text(DOC_BLOCK_RE.sub(lambda _: block, text))
            print(f"sync: bundle block -> {fname}")
        else:
            print(f"sync: WARNING no foundry:bundles markers in {fname} — block not placed")


def check_sync() -> int:
    """0 if root catalog + doc blocks match what --sync would write."""
    bad = []
    if json.loads(ROOT_MARKETPLACE.read_text()) != root_catalog():
        bad.append(str(ROOT_MARKETPLACE))
    block = doc_block()
    for fname in DOC_BLOCK_FILES:
        f = REPO / fname
        if not f.is_file():
            continue
        m = DOC_BLOCK_RE.search(f.read_text())
        if m is None or m.group(0) != block:
            bad.append(fname)
    if bad:
        print("check-sync: STALE (run scripts/build.py --sync):\n  " + "\n  ".join(bad))
        return 1
    print("check-sync: clean")
    return 0


# ---------------------------------------------------------------------- check
def _rel_files(root: Path) -> set[str]:
    return {str(p.relative_to(root)) for p in root.rglob("*") if p.is_file()}


def check(out_root: Path) -> int:
    """Rebuild into a temp dir; byte-diff against out_root (release drift gate)."""
    if not out_root.is_dir():
        print(f"check: nothing at {out_root} to compare against (main has no committed output)")
        return 1
    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = Path(tmp) / "plugins"
        build(tmp_root)
        write_json(tmp_root / ".claude-plugin" / "marketplace.json", release_catalog())
        fresh, committed = _rel_files(tmp_root), _rel_files(out_root)
        bad = [f"only in fresh build: {p}" for p in sorted(fresh - committed)]
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
    ap.add_argument("--sync", action="store_true", help="regenerate root catalog + doc blocks only")
    ap.add_argument("--check-sync", action="store_true", help="verify root catalog + doc blocks are fresh")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT, help="output root (default: plugins/)")
    args = ap.parse_args()

    if args.check:
        return check(args.out)
    if args.sync:
        sync()
        return 0
    if args.check_sync:
        return check_sync()
    build(args.out, args.only)
    if not args.only:  # partial builds don't rewrite the catalog
        write_json(args.out / ".claude-plugin" / "marketplace.json", release_catalog())
        print(f"build: marketplace catalog -> {args.out / '.claude-plugin' / 'marketplace.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
