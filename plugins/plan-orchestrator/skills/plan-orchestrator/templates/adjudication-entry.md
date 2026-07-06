# Architect Adjudication Entry Format

Every entry in `<work-dir>/assumptions.md` and in phase-plan `assumptions:` frontmatter uses this shape:

```yaml
- id: A<N>
  claim: "<one-line statement of the decision>"
  rationale: "<one-line — why this choice over alternatives>"
  confidence: high | medium | low
  risk_if_wrong: "<one-line — what breaks if wrong>"

  source:                                # exactly ONE form (see below)
    cite:                                # factual claim against external source
      - file: <relative-path>
        anchor: <slug-of-heading>
    # OR
    derived_from: [A<X>, A<Y>]            # this builds on other adjudications
    # OR
    originates_at: framing-stage         # architect-original; valid values:
                                          # spec, framing-stage, planning-stage, close-out-stage

  affects_artifacts:                      # required if decision should propagate
    - <relative-path>

  status: pending | validated | invalidated | revised | wont-fix
  validated_by: -
  validated_at: -

  # Optional:
  resolves: [E<N>, ...]
  note: "<clarification>"
```

## The `source:` field — three forms

| Form | When to use | Example |
|---|---|---|
| `cite:` | Factual claim against external content | Citing a spec line, contract section, glossary term |
| `derived_from:` | Builds on other adjudication(s) | "This pattern from A11 extended to the CLI" |
| `originates_at:` | Architect-original; nothing to cite | First-time choice; no source to reference |

Exactly one form is required. `cite:` and `derived_from:` MAY both be present (a derived adjudication that also cites supporting facts). `originates_at:` is mutually exclusive with the other two — if you can cite something, you should.

## Why each form exists

- **`cite:`** — forces read-back. The architect cannot write a claim about file X without specifying which section of X. `verify-refs.py` checks each file:anchor resolves; Haiku claim-check verifies the claim text agrees with the cited section.
- **`derived_from:`** — for adjudications that build on others. Round-2 finding: planners genuinely want to say "this is per A19's pattern." Without this, derived choices end up disguised as fresh originations. The derived adjudication MUST NOT contradict the ones it builds on; the assumption sweep verifies.
- **`originates_at:`** — for genuinely fresh architect choices with no source. Names the stage where the choice was first made. Cleaner than the prior `cites: []` workaround.

## Verification

- `cite:` paths/anchors must resolve per the canonical slug rule (verified by `verify-refs.py`)
- `derived_from:` IDs must resolve to defined adjudications somewhere in the run (verified by `verify-refs.py`)
- `affects_artifacts:` paths must exist; for `validated` adjudications, mtime must be ≥ `validated_at` (verified by `verify-coverage.py` — warns on pending, blocks on validated)
- Each adjudication is subject to Haiku claim-check (against `cite:` content) and Haiku coverage-check (against `affects_artifacts:`) before any stage gate closes

## What "validated" actually means

An adjudication is `validated` only when ALL of:
1. Structural checks pass (`source` resolves, `affects_artifacts` paths exist)
2. Alignment checks pass (Haiku returns YES on every cite; YES on every affected artifact)
3. Either (a) user explicitly validates at the user gate, OR (b) the adjudication was made by a planner and the architect accepts at the next ORIENT cycle

If any of (1) or (2) fails, the adjudication is not validated regardless of the `status:` field — the gate blocks until they pass.

## Examples

### Cited (factual claim from a known source)

```yaml
- id: A42
  claim: "ValidationFailureReason enum has 9 values"
  rationale: "v0.2: drop unit-dead, drop duplicate, add target-blocked"
  confidence: high
  risk_if_wrong: low
  source:
    cite:
      - file: contracts/C2-move-validation-interface.md
        anchor: error-validation-failure-reason
  affects_artifacts:
    - phases/P1/plan.md
    - phases/P4/plan.md
  status: validated
  validated_by: architect (precision check)
  validated_at: 2026-05-18T19:00Z
```

### Derived-from (builds on other adjudications)

```yaml
- id: A23
  claim: "P3 CLI uses session_factory + with_retry from P1 (no duplicate retry loop)"
  rationale: "Single source of retry discipline per A11; P3 imports rather than reimplements"
  confidence: high
  risk_if_wrong: medium
  source:
    derived_from: [A11, A43]
  affects_artifacts:
    - phases/P3/plan.md
  status: pending
  validated_by: -
  validated_at: -
```

### Architect-original (fresh choice; no source)

```yaml
- id: A4
  claim: "Timezone strategy: timestamps stored UTC, rendered/computed in local TZ"
  rationale: "Spec is silent. Local-time streak math matches user mental model."
  confidence: medium
  risk_if_wrong: medium
  source:
    originates_at: framing-stage
  affects_artifacts:
    - glossary.md
    - phases/P1/plan.md
    - phases/P2/plan.md
    - phases/P4/plan.md
  status: pending
  validated_by: -
  validated_at: -
```
