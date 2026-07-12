#!/usr/bin/env python3
"""
verify-dag.py — checks YAML/prose consistency in <work-dir>/dag.md.

Usage:  python3 verify-dag.py <work-dir>

Exit codes:
  0  pass
  1  mismatch detected (escalation appended to escalations.md)
  2  usage error

Stdlib only; uses pyyaml if available, else minimal regex parsing.
"""
import sys
import re
from pathlib import Path
from datetime import datetime, timezone


def parse_yaml_block(text):
    m = re.match(r"\A---\n(.*?)\n---\n(.*)$", text, re.DOTALL)
    if not m:
        return None, text
    return m.group(1), m.group(2)


def parse_yaml(yaml_text):
    try:
        import yaml
        return yaml.safe_load(yaml_text) or {}
    except ImportError:
        phases = re.findall(r"^\s*(P\d+):", yaml_text, re.MULTILINE)
        contracts = re.findall(r"^\s*(C\d+):", yaml_text, re.MULTILINE)
        return {
            "phases": {p: {} for p in phases},
            "contracts": {c: {} for c in contracts},
        }


def extract_prose_ids(prose, prefix):
    # Word boundary handles markdown bold (**C3**), em-dash (──C3──), and
    # normal whitespace prose. Trailing \b is symmetric.
    return set(re.findall(rf"\b({prefix}\d+)\b", prose))


def next_escalation_id(existing_text):
    ns = re.findall(r"^## E(\d+)", existing_text, re.MULTILINE)
    return max((int(x) for x in ns), default=0) + 1


def main():
    if len(sys.argv) != 2:
        print("Usage: verify-dag.py <work-dir>", file=sys.stderr)
        return 2

    work_dir = Path(sys.argv[1])
    dag_md = work_dir / "dag.md"
    if not dag_md.exists():
        print(f"FAIL: {dag_md} does not exist", file=sys.stderr)
        return 1

    text = dag_md.read_text()
    yaml_text, prose = parse_yaml_block(text)
    if yaml_text is None:
        print("FAIL: dag.md missing YAML frontmatter block", file=sys.stderr)
        return 1

    parsed = parse_yaml(yaml_text)
    yaml_phases = set((parsed.get("phases") or {}).keys()) if isinstance(parsed, dict) else set()
    yaml_contracts = set((parsed.get("contracts") or {}).keys()) if isinstance(parsed, dict) else set()

    prose_phases = extract_prose_ids(prose, "P")
    prose_contracts = extract_prose_ids(prose, "C")

    issues = []
    if yaml_phases - prose_phases:
        issues.append(f"phases in YAML not in prose: {sorted(yaml_phases - prose_phases)}")
    if prose_phases - yaml_phases:
        issues.append(f"phases in prose not in YAML: {sorted(prose_phases - yaml_phases)}")
    if yaml_contracts - prose_contracts:
        issues.append(f"contracts in YAML not in prose: {sorted(yaml_contracts - prose_contracts)}")
    if prose_contracts - yaml_contracts:
        issues.append(f"contracts in prose not in YAML: {sorted(prose_contracts - yaml_contracts)}")

    if not issues:
        print("OK")
        return 0

    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    # Per-dispatch escalation file (decision 52). The architect concatenates
    # escalations/*.md on each ORIENT, so a slugged filename keeps script-owned
    # findings distinct from agent-owned ones.
    esc_dir = work_dir / "escalations"
    esc_dir.mkdir(exist_ok=True)
    safe_ts = re.sub(r"[^0-9A-Za-z]+", "-", timestamp).strip("-")
    esc_md = esc_dir / f"architect-verify-dag-{safe_ts}.md"

    claim = "; ".join(issues).replace('"', "'")
    entry = f"""## E1 — {timestamp} — yaml-prose-mismatch
severity: blocking
detected_by: architect-verify-dag
source: dag.md
type: yaml-prose-mismatch
claim: "{claim}"
lands_at: framing
blocks: all downstream consumers of dag.md state
suggested_resolution: "architect reconciles; re-emit dag.md so YAML and prose agree"
status: open
resolved_by: -
resolved_at: -
"""
    esc_md.write_text(entry)

    print(f"FAIL: {claim}", file=sys.stderr)
    print(f"Escalation written to {esc_md}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
