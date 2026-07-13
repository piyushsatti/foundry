---
# DAG manifest — YAML is authoritative for the invalidation script.
# Prose below is for humans. If they disagree, verify-dag.py raises an escalation.
generated: <ISO timestamp>
schema_version: 1

phases:
  P1:
    name: <short-slug>
    produces: [C1]
    consumes: {}
    skill_requirements: []
    status: draft       # draft | locked | in-progress | stale | complete | blocked
    depends_on: []
    escalations: []

  # ... more phases. Audit phases (P5, P6, ...) are added automatically
  # per skill-catalog.md audit_triggers.

contracts:
  C1:
    producer: P1
    version: 0.1
    locked: false

  # ... more contracts

audit_triggers:
  # mirrored from skill-catalog.md for convenience
  security-review:
    spec_keywords: []
    file_patterns: []
    always_for: []
---

# DAG — Human-readable narrative

The YAML above is authoritative for the invalidation script. Below is for humans. If they disagree, `verify-dag.py` raises a `yaml-prose-mismatch` escalation.

## Phase overview

- **P1 — <name>:** <one-line description>
- **P2 — <name>:** <one-line description>

## Critical contracts

- **C1:** <one-line on what this contract represents>

## Dependency edges (ASCII)

```
P1 ──C1──▶ P2
         └─▶ P3
```

## Audit phases

- **P5 (audit, security-review):** triggered by keywords <list>
- **P6 (audit, pr-review-toolkit:review-pr):** always for T3 phases
