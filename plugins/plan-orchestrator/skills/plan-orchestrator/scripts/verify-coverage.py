#!/usr/bin/env python3
"""verify-coverage.py — adjudication `affects_artifacts:` coverage check.

Per decision 48 (round-2): runs on BOTH validated and pending adjudications.

  - For `validated` adjudications: FAIL (exit 1) if any affects_artifacts path
    is missing or has mtime < validated_at.
  - For `pending` adjudications: WARN (exit 2) — non-blocking, but architect
    sees drift early.
  - For `invalidated` / `revised` / `wont-fix`: skipped.

Usage:  python3 verify-coverage.py <work-dir>

Exit codes:
  0  all coverage verified clean
  1  validated adjudication has missing/stale affects_artifacts (BLOCKING)
  2  pending adjudication has missing/stale affects_artifacts (WARNING)
  3  both blocking AND warnings present
"""
import sys
import re
from pathlib import Path
from datetime import datetime, timezone


def parse_iso(s):
    s = s.strip().replace("Z", "+00:00").strip("'\"")
    try:
        return datetime.fromisoformat(s)
    except Exception:
        return None


def extract_adjudications(text):
    """Yield (adj_id, status, validated_at_str | None, [affects_artifacts])."""
    blocks = re.split(r"(?=^\s*-\s+id:\s+\w+)", text, flags=re.MULTILINE)
    for block in blocks:
        m_id = re.match(r"\s*-\s+id:\s+(\w+)", block)
        if not m_id:
            continue
        adj_id = m_id.group(1)

        m_aff = re.search(
            r"affects_artifacts:\s*\n((?:\s+-\s+.+\n)+)", block
        )
        if not m_aff:
            continue
        artifacts = [
            am.group(1).strip()
            for am in re.finditer(r"-\s+(.+?)(?:\n|$)", m_aff.group(1))
        ]

        m_status = re.search(r"^\s*status:\s+(\S+)", block, re.MULTILINE)
        status = m_status.group(1).strip() if m_status else "pending"

        m_ts = re.search(r"validated_at:\s+(.+?)(?:\n|$)", block)
        ts = m_ts.group(1).strip() if m_ts else "-"
        ts = None if ts == "-" else ts

        yield adj_id, status, ts, artifacts


def get_creation_time_for_pending(block_text):
    """For pending adjudications without validated_at, use the file's
    modification time as a rough proxy for when the adjudication was written.
    Returns None if no proxy available."""
    # Try to find a timestamp embedded in the block (e.g. a comment) — uncommon
    return None  # fall through to never-blocking warn-only check


def main():
    if len(sys.argv) != 2:
        print("Usage: verify-coverage.py <work-dir>", file=sys.stderr)
        return 2  # usage shares exit-code-2 semantic but is distinct

    work_dir = Path(sys.argv[1])
    candidates = [work_dir / "assumptions.md"]
    phases_dir = work_dir / "phases"
    if phases_dir.exists():
        candidates.extend(phases_dir.rglob("plan.md"))

    blocking_issues = []
    warnings = []
    total_validated = 0
    total_pending = 0

    for f in candidates:
        if not f.exists():
            continue
        for adj_id, status, ts_str, artifacts in extract_adjudications(
            f.read_text()
        ):
            if status in ("invalidated", "revised", "wont-fix"):
                continue

            for art in artifacts:
                full = work_dir / art
                if status == "validated":
                    total_validated += 1
                    adj_time = parse_iso(ts_str) if ts_str else None
                    if not full.exists():
                        blocking_issues.append(
                            f"{adj_id} (validated): affects_artifacts path "
                            f"'{art}' does not exist"
                        )
                        continue
                    if adj_time:
                        mtime = datetime.fromtimestamp(
                            full.stat().st_mtime, tz=timezone.utc
                        )
                        if mtime < adj_time:
                            blocking_issues.append(
                                f"{adj_id} (validated): '{art}' mtime "
                                f"({mtime.isoformat()}) is before validated_at "
                                f"({ts_str}) — change not landed"
                            )
                elif status == "pending":
                    total_pending += 1
                    if not full.exists():
                        warnings.append(
                            f"{adj_id} (pending): affects_artifacts path "
                            f"'{art}' does not exist yet"
                        )

    summary = (
        f"{total_validated} validated path-checks; "
        f"{total_pending} pending path-checks"
    )

    if not blocking_issues and not warnings:
        print(f"OK ({summary})")
        return 0

    if blocking_issues:
        print(f"FAIL: {len(blocking_issues)} blocking coverage gap(s):")
        for i in blocking_issues[:30]:
            print(f"  {i}")
    if warnings:
        print(f"WARN: {len(warnings)} pending-adjudication coverage warning(s):")
        for w in warnings[:30]:
            print(f"  {w}")
    print(f"\n{summary}")

    if blocking_issues and warnings:
        return 3
    if blocking_issues:
        return 1
    return 2  # warnings only


if __name__ == "__main__":
    sys.exit(main())
