#!/usr/bin/env python3
"""Load and validate skills/manifest.yaml — allowlist + dependency graph."""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST = REPO_ROOT / "skills" / "manifest.yaml"

MARKER_START = "<!-- foundry:dependencies:start -->"
MARKER_END = "<!-- foundry:dependencies:end -->"

LIST_KEYS = frozenset({"requires", "suggests", "dispatches", "external"})
SCALAR_KEYS = frozenset({"path", "origin", "bundle", "status", "mcp_bundle"})


def _parse_inline_list(value: str) -> list[str]:
    value = value.strip()
    if value == "[]":
        return []
    if not (value.startswith("[") and value.endswith("]")):
        raise ValueError(f"expected inline list, got: {value!r}")
    inner = value[1:-1].strip()
    if not inner:
        return []
    return [part.strip() for part in inner.split(",") if part.strip()]


def load_manifest(path: Path = MANIFEST) -> dict:
    """Minimal YAML parser for our manifest shape (no PyYAML dependency)."""
    if not path.is_file():
        raise FileNotFoundError(path)

    data: dict = {"version": None, "skills": {}, "external_registry": {}}
    section: str | None = None
    current_skill: str | None = None
    current_external: str | None = None

    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue

        if line.startswith("version:"):
            data["version"] = int(line.split(":", 1)[1].strip())
            continue

        if line.strip() == "skills:":
            section = "skills"
            current_skill = None
            current_external = None
            continue

        if line.strip() == "external_registry:":
            section = "external_registry"
            current_skill = None
            current_external = None
            continue

        if section == "skills":
            m = re.match(r"^  ([\w-]+):\s*$", line)
            if m:
                current_skill = m.group(1)
                data["skills"][current_skill] = {
                    "requires": [],
                    "suggests": [],
                    "dispatches": [],
                    "external": [],
                }
                continue

            if current_skill:
                m = re.match(r"^    (\w+):\s*(.+)$", line)
                if m:
                    key, value = m.group(1), m.group(2).strip()
                    if key in LIST_KEYS:
                        data["skills"][current_skill][key] = _parse_inline_list(value)
                    elif key in SCALAR_KEYS:
                        data["skills"][current_skill][key] = value
                    continue

        if section == "external_registry":
            m = re.match(r"^  ([\w-]+):\s*$", line)
            if m:
                current_external = m.group(1)
                data["external_registry"][current_external] = {}
                continue
            if current_external:
                m = re.match(r"^    (\w+):\s*(.+)$", line)
                if m:
                    data["external_registry"][current_external][m.group(1)] = m.group(2).strip()

    if data["version"] is None:
        raise ValueError("manifest missing version")
    if not data["skills"]:
        raise ValueError("manifest has no skills")

    return data


def validate_manifest(data: dict | None = None) -> list[str]:
    data = data or load_manifest()
    errors: list[str] = []
    names = set(data["skills"])

    for name, meta in data["skills"].items():
        rel = meta.get("path")
        if not rel:
            errors.append(f"{name}: missing path")
            continue
        abs_path = REPO_ROOT / rel
        if not abs_path.is_dir():
            errors.append(f"{name}: path not found: {rel}")

        mcp_bundle = meta.get("mcp_bundle")
        if mcp_bundle:
            bundle_path = REPO_ROOT / mcp_bundle
            if not bundle_path.is_dir():
                errors.append(f"{name}: mcp_bundle not found: {mcp_bundle}")

        for dep_key in ("requires", "dispatches"):
            for dep in meta.get(dep_key, []):
                if dep not in names:
                    errors.append(
                        f"{name}: {dep_key} references unknown skill {dep!r} (not in manifest)"
                    )

        for dep_key in ("suggests",):
            for dep in meta.get(dep_key, []):
                if dep not in names and dep not in data.get("external_registry", {}):
                    errors.append(
                        f"{name}: suggests references {dep!r} — not in manifest or external_registry"
                    )

        for ext in meta.get("external", []):
            if ext in names:
                errors.append(
                    f"{name}: {ext!r} listed in external but is in manifest (move to requires/dispatches/suggests)"
                )
            elif ext not in data.get("external_registry", {}):
                errors.append(
                    f"{name}: external references {ext!r} — add to external_registry"
                )

    return errors


def cmd_list(data: dict) -> None:
    for name in sorted(data["skills"]):
        print(name)


def cmd_deps(data: dict, skill: str) -> None:
    if skill not in data["skills"]:
        sys.exit(f"unknown skill: {skill}")
    meta = data["skills"][skill]
    for key in ("requires", "suggests", "dispatches", "external"):
        vals = meta.get(key, [])
        if vals:
            print(f"{key}: {', '.join(vals)}")


def cmd_reverse(data: dict, skill: str) -> None:
    """Who requires/suggests/dispatches this skill?"""
    if skill not in data["skills"] and skill not in data.get("external_registry", {}):
        sys.exit(f"unknown skill: {skill}")

    found = False
    for name, meta in sorted(data["skills"].items()):
        for key in ("requires", "suggests", "dispatches"):
            if skill in meta.get(key, []):
                print(f"{name} ({key})")
                found = True
    if not found:
        print("(none in manifest)")


def _skill_doc_path(meta: dict) -> Path | None:
    base = REPO_ROOT / meta["path"]
    for name in ("SKILL.md", "skill.md"):
        path = base / name
        if path.is_file():
            return path
    return None


def _format_dep_list(vals: list[str]) -> str:
    if not vals:
        return "—"
    return ", ".join(f"`{v}`" for v in vals)


def render_dependencies_section(name: str, meta: dict, data: dict, skill_dir: Path) -> str:
    manifest_rel = Path(os.path.relpath(MANIFEST, skill_dir)).as_posix()

    labels = {
        "requires": "Must exist in bundle before running",
        "suggests": "Soft handoff after this skill — suggest, do not auto-chain",
        "dispatches": "May invoke via Skill tool or subagent prompt",
        "external": "Outside foundry bundle (host plugins)",
    }

    lines = [
        MARKER_START,
        "## Dependencies",
        "",
        f"Registry: [`manifest.yaml`]({manifest_rel}) · refresh: `python3 scripts/skills_manifest.py sync-docs`",
        "",
        "| Kind | Skills | Role |",
        "|------|--------|------|",
    ]

    any_row = False
    for key in ("requires", "suggests", "dispatches", "external"):
        vals = meta.get(key, [])
        if not vals:
            continue
        any_row = True
        lines.append(f"| **{key}** | {_format_dep_list(vals)} | {labels[key]} |")

    if not any_row:
        lines.append("| — | — | No manifest dependencies |")

    used_by: list[str] = []
    for other, ometa in sorted(data["skills"].items()):
        if other == name:
            continue
        for key in ("requires", "suggests", "dispatches"):
            if name in ometa.get(key, []):
                used_by.append(f"`{other}` ({key})")

    if used_by:
        lines.extend(["", f"**Used by:** {', '.join(used_by)}"])

    lines.extend(["", MARKER_END])
    return "\n".join(lines)


def inject_dependencies(path: Path, section: str) -> bool:
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(
        re.escape(MARKER_START) + r".*?" + re.escape(MARKER_END),
        re.DOTALL,
    )

    if pattern.search(text):
        new_text = pattern.sub(section, text)
    elif text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            body = parts[2].lstrip("\n")
            new_text = f"---{parts[1]}---\n\n{section}\n\n{body}"
        else:
            new_text = text.rstrip() + "\n\n" + section + "\n"
    else:
        new_text = text.rstrip() + "\n\n" + section + "\n"

    if new_text == text:
        return False
    path.write_text(new_text, encoding="utf-8")
    return True


def cmd_sync_docs(data: dict, skill: str | None = None) -> int:
    updated = 0
    skipped = 0
    targets = [skill] if skill else sorted(data["skills"])

    for name in targets:
        if name not in data["skills"]:
            print(f"ERROR: unknown skill: {name}", file=sys.stderr)
            return 1
        meta = data["skills"][name]
        doc = _skill_doc_path(meta)
        if doc is None:
            print(f"skip {name}: no SKILL.md or skill.md", file=sys.stderr)
            skipped += 1
            continue
        section = render_dependencies_section(name, meta, data, doc.parent)
        if inject_dependencies(doc, section):
            print(f"updated: {doc.relative_to(REPO_ROOT)}")
            updated += 1
        else:
            print(f"unchanged: {doc.relative_to(REPO_ROOT)}")

    print(f"Done. {updated} updated, {skipped} skipped.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Foundry skills manifest")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="skill names for sync allowlist")
    sub.add_parser("validate", help="check paths and dependency graph")

    p_deps = sub.add_parser("deps", help="show deps for one skill")
    p_deps.add_argument("skill")

    p_rev = sub.add_parser("used-by", help="who references this skill")
    p_rev.add_argument("skill")

    p_path = sub.add_parser("path", help="repo-relative path for one skill")
    p_path.add_argument("skill")

    p_bundle = sub.add_parser("mcp-bundle", help="repo-relative MCP bundle path (if any)")
    p_bundle.add_argument("skill")

    p_sync = sub.add_parser("sync-docs", help="inject ## Dependencies into SKILL.md from manifest")
    p_sync.add_argument("skill", nargs="?", help="one skill only (default: all)")

    args = parser.parse_args()
    data = load_manifest()

    if args.cmd == "list":
        cmd_list(data)
        return 0

    if args.cmd == "validate":
        errors = validate_manifest(data)
        if errors:
            for e in errors:
                print(f"ERROR: {e}", file=sys.stderr)
            return 1
        print(f"OK: {len(data['skills'])} skills, dependency graph valid")
        return 0

    if args.cmd == "deps":
        cmd_deps(data, args.skill)
        return 0

    if args.cmd == "used-by":
        cmd_reverse(data, args.skill)
        return 0

    if args.cmd == "path":
        if args.skill not in data["skills"]:
            sys.exit(f"unknown skill: {args.skill}")
        print(data["skills"][args.skill]["path"])
        return 0

    if args.cmd == "mcp-bundle":
        if args.skill not in data["skills"]:
            sys.exit(f"unknown skill: {args.skill}")
        bundle = data["skills"][args.skill].get("mcp_bundle", "")
        if bundle:
            print(bundle)
        return 0

    if args.cmd == "sync-docs":
        return cmd_sync_docs(data, args.skill)

    return 1


if __name__ == "__main__":
    sys.exit(main())
