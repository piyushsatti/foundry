# /// script
# requires-python = ">=3.11"
# dependencies = ["ruamel.yaml"]
# ///

"""
Migrate memory-file frontmatter to schema_version 2 (the new `scope` mapping).

Known limitations (both covered by the T5 apply process, see below):

(a) Frontmatter/body split uses ``text.split("---\\n", 2)``. This mis-fires ONLY if a
    frontmatter VALUE itself contains a line that is exactly ``---`` (which would be read
    as the closing fence early, truncating the frontmatter). Real memory files are simple
    ``key: value`` frontmatter with no such embedded fence, so this does not occur in
    practice. The T5 live migration runs dry-run first -> human diff review -> archive of
    every original -> post-apply validation, any of which catches a mis-split before it
    can do harm. Additionally, ``main``'s per-file try/except (see below) converts a YAML
    parse failure from such a mis-split into a clean recorded skip/FAIL rather than a crash.

(b) CRLF (``\\r\\n``) files are skipped as "no metadata block": the split key is the LF form
    ``---\\n``, so a CRLF file's leading ``---\\r\\n`` does not match and the file is left
    untouched. The target corpus is Linux (LF), so this is acceptable; such a file is
    reported as skipped, never silently corrupted.
"""

import argparse
import io
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

from ruamel.yaml import YAML

KNOWN_ROLES: dict[
    str, str
] = {}  # slug -> explicit role override (empty for now; config-refinable)

# Excluded filenames that main() never touches, even in a directory target.
_EXCLUDED_NAMES = {"MEMORY.md", "workflow_pending_cleanup.md"}

# Frontmatter fence: a line that is exactly `---` (optional trailing whitespace) plus its newline.
# LINE-ANCHORED (not a substring) so a `---` inside a block scalar, or a `---` horizontal rule in
# the body, is never mistaken for the closing fence — the old substring split (`text.split("---\n")`)
# silently truncated such files and relocated their content.
_FENCE_SPLIT = re.compile(r"(?m)^---[ \t]*\r?\n")


def _encode(path: str) -> str:
    """Encode an absolute path to a key slug: replace every '/' and '.' with '-'.

    This is the canonical Claude Code slug rule (verified live at v2.1.195) — underscores are
    PRESERVED. Kept in sync with bin/meditate-slug (the shell single-source-of-truth the skills
    call); this Python copy exists so the migrate script has no runtime dependency on it.
    """
    return re.sub(r"[/.]", "-", path)


def derive_scope(memfile_path: Path) -> dict:
    """
    Return {"depth": int, "role": str} for a memory file's storage location.

    The memory file is expected at:
        <root>/projects/<slug>/memory/<file>.md

    so the slug is recovered as:
        slug = memfile_path.parent.parent.name

    home_slug is derived by encoding Path.home():
        home_slug = _encode(str(Path.home()))   # e.g. "/home/piyush" -> "-home-piyush"

    Role (first match wins):
        "home"              if slug == home_slug
        KNOWN_ROLES[slug]   if slug in KNOWN_ROLES     # explicit config override
        "worktree"          if "--worktrees-" in slug  # encoded "/.worktrees/"
        "dir"               otherwise                  # best-effort; repo/sub refined at runtime/config

    Depth:
        0 if role == "home" (slug == home_slug)
        else len([s for s in slug.removeprefix(home_slug).split('-') if s])
             # APPROXIMATE for slugs with dotted/dashed components (e.g. FEAT-12 counts as 2 segs,
             # --worktrees- adds an empty seg that is filtered out); exact for the home key.
    """
    slug: str = memfile_path.parent.parent.name
    home_slug: str = _encode(str(Path.home()))

    # Determine role (first match wins)
    if slug == home_slug:
        role = "home"
    elif slug in KNOWN_ROLES:
        role = KNOWN_ROLES[slug]
    elif "--worktrees-" in slug:
        role = "worktree"
    else:
        role = "dir"

    # Determine depth
    if role == "home":
        depth = 0
    else:
        depth = len([s for s in slug.removeprefix(home_slug).split("-") if s])

    return {"depth": depth, "role": role}


def _make_yaml() -> YAML:
    """Return a ruamel.yaml round-trip instance configured for 2-space indentation."""
    yaml = YAML()
    yaml.default_flow_style = False
    yaml.preserve_quotes = True
    yaml.indent(mapping=2, sequence=2, offset=2)
    yaml.width = 4096  # prevent line-wrapping
    return yaml


def migrate_file(p: Path, *, apply: bool, backup_stamp: str | None = None) -> dict:
    """
    Migrate ONE memory file's frontmatter to schema_version 2. Return a diff dict:
      {"path": str, "changed": bool, "before_scope", "after_scope",
       "added_schema_version": bool, "added_genericity": bool, "post_write_ok": bool,
       "notes": list[str]}

    When apply=True and backup_stamp is given, the ORIGINAL is copied to
    ``<file.parent>/.migrate-backup-<stamp>/<file.name>`` immediately before the overwrite — so
    only files that actually change get backed up, and a missing/unreadable target fails cleanly
    (via the read at the top) instead of crashing a separate pre-pass.

    1. Split into (frontmatter_text, body) as above. If no parseable frontmatter / no `metadata:` map ->
       changed=False, notes=["no metadata block"], no write.
    2. Parse frontmatter with ruamel.yaml round-trip. md = parsed["metadata"].
    3. If md.get("schema_version") == 2 -> changed=False, no write (idempotent).
    4. before_scope = md.get("scope"); md["scope"] = derive_scope(p)   # replace old enum with the mapping
    5. md["schema_version"] = 2                                        # presence is the invariant; order not significant
    6. if "genericity" not in md: md["genericity"] = "specific"; added_genericity=True
    7. if apply: write reassembled text back to p. else: do not write.
    Return the diff dict (changed=True when steps 4-6 produced any change).
    """
    result: dict = {
        "path": str(p),
        "changed": False,
        "before_scope": None,
        "after_scope": None,
        "added_schema_version": False,
        "added_genericity": False,
        "post_write_ok": True,
        "notes": [],
    }

    text = p.read_text(encoding="utf-8")
    parts = _FENCE_SPLIT.split(text, maxsplit=2)  # -> ['', '<frontmatter>', '<body>']

    if len(parts) < 3 or parts[0].strip() != "":
        result["notes"].append("no metadata block")
        return result

    frontmatter_text, body = parts[1], parts[2]

    yaml = _make_yaml()
    parsed = yaml.load(io.StringIO(frontmatter_text))

    if not isinstance(parsed, dict) or "metadata" not in parsed:
        result["notes"].append("no metadata block")
        return result

    md = parsed["metadata"]

    if md.get("schema_version") == 2:
        result["notes"].append("already schema_version 2 — skipped")
        return result

    # Step 4: remap scope
    result["before_scope"] = md.get("scope")
    new_scope = derive_scope(p)
    md["scope"] = new_scope
    result["after_scope"] = new_scope

    # Step 5: add/set schema_version
    if "schema_version" not in md:
        result["added_schema_version"] = True
    md["schema_version"] = 2

    # Step 6: default genericity
    if "genericity" not in md:
        md["genericity"] = "specific"
        result["added_genericity"] = True

    result["changed"] = True

    if apply:
        # Back up the ORIGINAL before overwriting — only files that actually change reach here.
        if backup_stamp is not None:
            backup_dir = p.parent / f".migrate-backup-{backup_stamp}"
            backup_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, backup_dir / p.name)

        buf = io.StringIO()
        yaml.dump(parsed, buf)
        dumped = buf.getvalue()
        # Ensure dumped ends with exactly one newline (ruamel always does, but be defensive)
        if not dumped.endswith("\n"):
            dumped += "\n"
        new_text = "---\n" + dumped + "---\n" + body
        p.write_text(new_text, encoding="utf-8")

        # Post-write self-check: migration only touches frontmatter, so the body must survive
        # byte-identical. A mismatch means the fence split grabbed the wrong region — surface it
        # loudly rather than reporting a corrupted file as VALIDATED OK.
        recheck = _FENCE_SPLIT.split(p.read_text(encoding="utf-8"), maxsplit=2)
        if len(recheck) < 3 or recheck[2] != body:
            result["post_write_ok"] = False
            result["notes"].append("POST-WRITE BODY MISMATCH — frontmatter split suspect")

    return result


def main(targets: list[Path], *, apply: bool = False) -> int:
    """
    Iterate targets. A target that is a directory -> its '*.md' files EXCLUDING 'MEMORY.md' and
    'workflow_pending_cleanup.md'. A target that is a file -> that file.
    For each: call migrate_file; print a concise per-file diff line.
    apply defaults False (dry-run). With apply=True, migrate_file backs up each CHANGED original to
        <file.parent>/.migrate-backup-<UTC-stamp>/<file.name>   (shutil.copy2; one stamp per run)
    right before overwriting it, and self-checks that the body survived byte-identical.
    AFTER all writes (apply=True): re-read each CHANGED file and validate metadata has
        scope (a mapping), genericity, schema_version == 2.
    Return 0 on success; non-zero if any file failed, body mismatched, or validation failed.
    """
    # Collect all target files. Excluded names (MEMORY.md, workflow_pending_cleanup.md)
    # are skipped for BOTH directory members and explicit file targets.
    files: list[Path] = []
    for target in targets:
        if target.is_dir():
            for md_file in sorted(target.glob("*.md")):
                if md_file.name not in _EXCLUDED_NAMES:
                    files.append(md_file)
        elif target.name in _EXCLUDED_NAMES:
            print(f"skipped: {target.name}  [excluded name]")
        else:
            files.append(target)

    # One UTC stamp per run; migrate_file uses it to back up each CHANGED original before overwrite.
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    # Migrate each file. A single bad file must not abort the run: wrap each call in
    # try/except, record the failure, and continue to the next file.
    changed_files: list[Path] = []
    n_migrated = 0
    n_skipped_v2 = 0
    n_skipped_no_meta = 0
    body_mismatches = 0
    failed: list[tuple[Path, str]] = []
    for f in files:
        try:
            diff = migrate_file(f, apply=apply, backup_stamp=stamp if apply else None)
        except Exception as exc:  # noqa: BLE001 — intentionally broad: isolate one bad file
            failed.append((f, f"{type(exc).__name__}: {exc}"))
            print(f"FAILED: {f.name}  [{type(exc).__name__}: {exc}]")
            continue
        if diff.get("post_write_ok") is False:
            body_mismatches += 1
        notes = ", ".join(diff["notes"]) if diff["notes"] else ""
        note_str = f"  [{notes}]" if notes else ""
        if diff["changed"]:
            n_migrated += 1
            changed_files.append(f)
            status = "CHANGED"
        else:
            status = "skipped"
            if "already schema_version 2 — skipped" in diff["notes"]:
                n_skipped_v2 += 1
            elif "no metadata block" in diff["notes"]:
                n_skipped_no_meta += 1
        print(
            f"{status}: {f.name}  scope: {diff['before_scope']} -> {diff['after_scope']}{note_str}"
        )

    # Post-write validation (apply=True only): re-read each CHANGED file and confirm the
    # metadata invariant. Validation failures are counted alongside FAILED files.
    validation_failures = 0
    if apply:
        yaml = _make_yaml()
        for f in changed_files:
            text = f.read_text(encoding="utf-8")
            parts = _FENCE_SPLIT.split(text, maxsplit=2)
            if len(parts) < 3:
                print(f"VALIDATION FAIL: {f.name} — no frontmatter after rewrite")
                validation_failures += 1
                continue
            parsed = yaml.load(io.StringIO(parts[1]))
            md = parsed.get("metadata", {}) if parsed else {}
            ok = (
                isinstance(md.get("scope"), dict)
                and "genericity" in md
                and md.get("schema_version") == 2
            )
            if not ok:
                print(
                    f"VALIDATION FAIL: {f.name} — metadata invariant not satisfied: {md}"
                )
                validation_failures += 1
            else:
                print(f"VALIDATED OK: {f.name}")

    # Structured tally of the run.
    print(
        f"TALLY: {n_migrated} migrated, {n_skipped_v2} skipped (already v2), "
        f"{n_skipped_no_meta} skipped (no metadata), {body_mismatches} BODY-MISMATCH, "
        f"{len(failed)} FAILED"
    )

    # Non-zero if any file failed, any body mismatched on write, or any validation failed.
    # 1-per-category cap keeps the exit code from wrapping mod 256 on huge runs.
    return 1 if (failed or body_mismatches or validation_failures) else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Migrate memory-file frontmatter to schema_version 2."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        default=False,
        help="Actually write files. Default is dry-run (no writes).",
    )
    parser.add_argument(
        "targets",
        nargs="*",
        default=[
            str(Path.home() / ".claude" / "projects" / _encode(str(Path.home())) / "memory")
        ],
        help="Files or directories to migrate (default: this machine's home-key memory dir).",
    )
    args = parser.parse_args()
    raise SystemExit(main([Path(t) for t in args.targets], apply=args.apply))
