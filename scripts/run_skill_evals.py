#!/usr/bin/env python3
"""Validate skill eval definitions under skills/<skill>/evals/evals.json.

This script checks that each eval has the required structure and prints a
human-readable checklist (prompt, expected output, pass-criteria hints).
Full agent evals — running prompts against a live agent and judging responses —
are executed in the Cursor skill UI, not here.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
REQUIRED_KEYS = frozenset({"id", "prompt", "expected_output"})

# Reuse manifest path-resolution so skills that moved into plugins/ resolve correctly.
sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from skills_manifest import load_manifest
except Exception:  # fallback if manifest tooling is unavailable
    load_manifest = None

# MCP tool names (underscore form) and CLI aliases (hyphen form) we hint on.
TOOL_KEYWORDS: dict[str, tuple[str, ...]] = {
    "spec_audit": ("spec_audit", "spec-audit"),
    "drift_report": ("drift_report", "drift-report"),
    "next_leaves": ("next_leaves", "next-leaves"),
    "list_cross_blocking_chain": ("list_cross_blocking_chain",),
    "peek_project": ("peek_project",),
    "list_targets": ("list_targets",),
}


def _skill_dir(skill: str) -> Path:
    """Resolve a skill's repo-relative dir via the manifest (handles plugins/)."""
    if load_manifest is not None:
        try:
            meta = load_manifest()["skills"].get(skill)
        except Exception:
            meta = None
        if meta and meta.get("path"):
            return REPO_ROOT / meta["path"]
    # Fallback: legacy flat layout for skills not in the manifest.
    return REPO_ROOT / "skills" / skill


def _evals_path(skill: str) -> Path:
    return _skill_dir(skill) / "evals" / "evals.json"


def load_evals(skill: str) -> dict:
    path = _evals_path(skill)
    if not path.is_file():
        raise FileNotFoundError(f"evals file not found: {path}")
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def validate_structure(data: dict) -> list[str]:
    """Return a list of structural error messages (empty if valid)."""
    errors: list[str] = []
    if "evals" not in data or not isinstance(data["evals"], list):
        errors.append("top-level 'evals' must be a list")
        return errors

    seen_ids: set[int] = set()
    for idx, ev in enumerate(data["evals"]):
        label = f"evals[{idx}]"
        if not isinstance(ev, dict):
            errors.append(f"{label}: must be an object")
            continue

        missing = REQUIRED_KEYS - ev.keys()
        if missing:
            errors.append(f"{label}: missing keys: {', '.join(sorted(missing))}")
            continue

        eid = ev["id"]
        if not isinstance(eid, int):
            errors.append(f"{label}: id must be an integer, got {type(eid).__name__}")
        elif eid in seen_ids:
            errors.append(f"{label}: duplicate id {eid}")
        else:
            seen_ids.add(eid)

        for key in ("prompt", "expected_output"):
            if not isinstance(ev[key], str) or not ev[key].strip():
                errors.append(f"{label}: '{key}' must be a non-empty string")

    return errors


def _detect_tools(text: str) -> list[str]:
    """Return tool names whose keywords appear in *text* (case-insensitive)."""
    lower = text.lower()
    found: list[str] = []
    for tool, keywords in TOOL_KEYWORDS.items():
        if any(kw.lower() in lower for kw in keywords):
            found.append(tool)
    return found


def _pass_criteria_hints(expected_output: str) -> list[str]:
    """Derive keyword-matching hints from expected_output."""
    hints: list[str] = []
    tools = _detect_tools(expected_output)
    if tools:
        hints.append(f"MCP/CLI tools referenced: {', '.join(tools)}")
    if re.search(r"change_reason|revision discipline", expected_output, re.I):
        hints.append("Pass if response discusses change_reason / revision discipline")
    if re.search(r"\bproject_root\b|\brepo\b", expected_output, re.I):
        hints.append("Pass if response mentions project_root or repo path when needed")
    if re.search(r"cross.block|excluded", expected_output, re.I):
        hints.append("Pass if response covers cross-blocked exclusions")
    if re.search(r"target_status|achieved|planned", expected_output, re.I):
        hints.append("Pass if response summarizes achieved vs planned nodes")
    if not hints:
        hints.append("Pass if agent behavior matches expected_output description")
    return hints


def validate_strict(expected_output: str, eval_id: int) -> list[str]:
    """In --strict mode, expected_output must mention at least one known tool."""
    tools = _detect_tools(expected_output)
    if not tools:
        return [
            f"eval {eval_id}: --strict requires expected_output to mention "
            f"one of {', '.join(TOOL_KEYWORDS)}"
        ]
    return []


def print_checklist(data: dict) -> None:
    evals = data.get("evals", [])
    skill = data.get("skill_name", "(unknown)")
    print(f"Skill: {skill}")
    print(f"Evals: {len(evals)}")
    print()

    for ev in evals:
        eid = ev.get("id", "?")
        print(f"## Eval {eid}")
        print(f"  [ ] Prompt: {ev.get('prompt', '')}")
        print(f"  [ ] Expected: {ev.get('expected_output', '')}")
        for hint in _pass_criteria_hints(ev.get("expected_output", "")):
            print(f"      hint: {hint}")
        print()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate skill eval definitions and print a checklist."
    )
    parser.add_argument(
        "--skill",
        default="manifold",
        help="Skill name (default: manifold)",
    )
    parser.add_argument(
        "--eval-id",
        type=int,
        default=None,
        help="Only print the eval with this id",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Require expected_output to mention known MCP tool names",
    )
    args = parser.parse_args(argv)

    try:
        data = load_evals(args.skill)
    except FileNotFoundError as exc:
        print(exc, file=sys.stderr)
        return 1
    except json.JSONDecodeError as exc:
        print(f"invalid JSON: {exc}", file=sys.stderr)
        return 1

    errors = validate_structure(data)
    if args.eval_id is not None:
        ids = {ev["id"] for ev in data.get("evals", []) if isinstance(ev, dict) and "id" in ev}
        if args.eval_id not in ids:
            errors.append(f"--eval-id {args.eval_id} not found")

    if args.strict:
        for ev in data.get("evals", []):
            if not isinstance(ev, dict) or "id" not in ev:
                continue
            if args.eval_id is not None and ev["id"] != args.eval_id:
                continue
            errors.extend(
                validate_strict(ev.get("expected_output", ""), ev["id"])
            )

    if errors:
        print("VALIDATION FAILED:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    if args.eval_id is not None:
        filtered = [ev for ev in data["evals"] if ev["id"] == args.eval_id]
        data = {**data, "evals": filtered}

    print_checklist(data)
    print("All eval definitions structurally valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
