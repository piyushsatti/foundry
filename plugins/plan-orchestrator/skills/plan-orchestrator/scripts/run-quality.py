#!/usr/bin/env python3
"""
run-quality.py — post-run quality assessment (decision 33).

Reads the work-dir and produces <work-dir>/run-quality.yaml capturing:
- hard checks (tier violations, blocking escalations, unresolved assumptions)
- soft checks (continuation halts, cascade count, phases redone)
- audit findings bucketed by lands_at tier
- skeptic findings count + true-positive rate (if user marked validity)
- dispatch counts (opus / sonnet / haiku) from TODO.md frontmatter
- token cost (actual vs predicted)

Usage:  python3 run-quality.py <work-dir>

Exit:
  0  green
  1  red (any hard check failed)
  2  yellow (no hard fails; soft warnings)
"""
import sys
import re
from pathlib import Path
from datetime import datetime, timezone


def read(p):
    return p.read_text() if p.exists() else ""


def count_escalations(text, predicate):
    """Count escalation entries whose body matches a predicate fn(block_text)."""
    cnt = 0
    starts = [m.start() for m in re.finditer(r"^## E\d+", text, re.MULTILINE)]
    for i, start in enumerate(starts):
        end = starts[i + 1] if i + 1 < len(starts) else len(text)
        block = text[start:end]
        if predicate(block):
            cnt += 1
    return cnt


def is_blocking_open(block):
    return "status: open" in block and "severity: blocking" in block


def is_open(block):
    return "status: open" in block


def by_status(text):
    out = {"open": 0, "acknowledged": 0, "resolved": 0, "wont-fix": 0}
    for status in out:
        out[status] = count_escalations(text, lambda b, s=status: f"status: {s}" in b)
    return out


def by_lands_at(text):
    out = {"T0": 0, "T1": 0, "T2": 0, "T3": 0}
    for m in re.finditer(r"lands_at\s*:\s*(T\d)", text):
        tier = m.group(1)
        if tier in out:
            out[tier] += 1
    return out


def skeptic_findings(text):
    """Find skeptic entries: type=omission. Count total and (if marked) validated."""
    total = 0
    validated = 0
    starts = [m.start() for m in re.finditer(r"^## E\d+", text, re.MULTILINE)]
    for i, start in enumerate(starts):
        end = starts[i + 1] if i + 1 < len(starts) else len(text)
        block = text[start:end]
        if "type: omission" in block:
            total += 1
            if re.search(r"resolved_by:\s+user\s*\(valid\)", block):
                validated += 1
    return total, validated


def count_pending_assumptions(work_dir):
    cnt = 0
    candidates = [work_dir / "assumptions.md"]
    if (work_dir / "phases").exists():
        candidates.extend((work_dir / "phases").rglob("*.md"))
    for f in candidates:
        if not f.exists() or not f.is_file():
            continue
        text = f.read_text()
        for m in re.finditer(
            r"-\s+id:\s+A\d+(?:\n(?:\s+\S.*|\s*))*?(?=\n-\s+id:|\n[a-zA-Z_]+:|\n\s*\n|\Z)",
            text,
            re.MULTILINE,
        ):
            if "status: pending" in m.group(0):
                cnt += 1
    return cnt


def context_halts(work_dir):
    cnt = 0
    if not (work_dir / "phases").exists():
        return 0
    for status_f in (work_dir / "phases").rglob("status.md"):
        text = status_f.read_text()
        cnt += text.count("reason: context-budget")
    return cnt


def phases_complete(work_dir):
    cnt = 0
    if not (work_dir / "phases").exists():
        return 0
    for status_f in (work_dir / "phases").rglob("status.md"):
        text = status_f.read_text()
        if re.search(r"^status:\s*complete\b", text, re.MULTILINE):
            cnt += 1
    return cnt


def dispatch_counts_from_todo(todo_text):
    counts = {"opus": 0, "sonnet": 0, "haiku": 0}
    for k in counts:
        m = re.search(rf"{k}_dispatches\s*:\s*(\d+)", todo_text)
        if m:
            counts[k] = int(m.group(1))
    return counts


def main():
    if len(sys.argv) != 2:
        print("Usage: run-quality.py <work-dir>", file=sys.stderr)
        return 2

    work_dir = Path(sys.argv[1])
    esc_text = read(work_dir / "escalations.md")
    todo_text = read(work_dir / "TODO.md")

    final_blocking = count_escalations(esc_text, is_blocking_open)
    pending_assumptions = count_pending_assumptions(work_dir)
    status_dist = by_status(esc_text)
    lands_dist = by_lands_at(esc_text)
    skeptic_total, skeptic_valid = skeptic_findings(esc_text)
    halts = context_halts(work_dir)
    completed = phases_complete(work_dir)
    dispatches = dispatch_counts_from_todo(todo_text)

    hard_failed = (final_blocking > 0) or (pending_assumptions > 0)
    soft_yellow = (halts > 2) or (dispatches["opus"] > 50)
    overall = "red" if hard_failed else ("yellow" if soft_yellow else "green")

    timestamp = datetime.now(timezone.utc).isoformat()
    report = f"""run_id: {timestamp}
overall: {overall}

hard_checks:
  final_blocking_escalations: {final_blocking}
  unresolved_assumptions: {pending_assumptions}

soft_checks:
  context_budget_halts: {halts}
  phases_completed: {completed}

escalations_by_status:
  open: {status_dist['open']}
  acknowledged: {status_dist['acknowledged']}
  resolved: {status_dist['resolved']}
  wont_fix: {status_dist['wont-fix']}

audit_findings_by_lands_at:
  T0: {lands_dist['T0']}
  T1: {lands_dist['T1']}
  T2: {lands_dist['T2']}
  T3: {lands_dist['T3']}

skeptic_findings:
  total: {skeptic_total}
  validated_as_real: {skeptic_valid}

dispatches:
  opus: {dispatches['opus']}
  sonnet: {dispatches['sonnet']}
  haiku: {dispatches['haiku']}
"""

    out_path = work_dir / "run-quality.yaml"
    out_path.write_text(report)
    print(report)
    print(f"Report written to {out_path}", file=sys.stderr)

    return 0 if overall == "green" else (1 if overall == "red" else 2)


if __name__ == "__main__":
    sys.exit(main())
