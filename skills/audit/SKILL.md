---
name: audit
description: Independent review of an artifact in scope — structured findings with severity tiers, no fixes. Use when user says audit, independent audit, second opinion, strict auditor, surface parity audit, spec audit of files/plans/PRs (not manifold DB — use manifold skill for MCP spec_audit), regression check, or audit the intent.
argument-hint: "What to audit and where (paths, plan file, PR, etc.)"
---

<!-- foundry:dependencies:start -->
## Dependencies

Registry: [`manifest.yaml`](../manifest.yaml) · refresh: `python3 scripts/skills_manifest.py sync-docs`

| Kind | Skills | Role |
|------|--------|------|
| **suggests** | `hats`, `red-vs-blue` | Soft handoff after this skill — suggest, do not auto-chain |

**Used by:** `brief` (suggests), `grill-with-docs` (suggests), `hats` (suggests), `plan-orchestrator` (dispatches), `red-vs-blue` (suggests), `subset` (suggests)

<!-- foundry:dependencies:end -->

# Audit

Independent review. The auditor **reads, evaluates, reports** — never implements fixes.

<HARD-GATE>
Do not edit files, run fixes, or start implementation. Findings only. Route fixes back to the original agent or the user.
</HARD-GATE>

## Before dispatch

1. Confirm **scope** — files, docs, plan, PR, or intent statement. If unclear, ask.
2. Ask the user **which model** to use for the auditor subagent (or review in-session if they prefer). Do not assume a tier.
3. Optional: ask for a **persona** (strict auditor, SRE, security, domain expert). Default: neutral independent reviewer.

## Auditor instructions

Give the subagent (or yourself, if in-session):

- Read everything in scope completely before writing findings.
- Think independently — second- and third-order effects, not rubber-stamping.
- **Raise, don't fix.** No patches, no "while I'm here" edits.
- Separate facts from assumptions. Flag unverified claims.
- Be direct. No praise sandwich. Findings stand on their own.

## Output format

```markdown
# Audit: [subject]

**Scope:** [what was read]
**Reviewer:** [persona if any]

## Executive summary
[2–4 sentences: overall verdict + top risks]

## Findings

| ID | Severity | Location | Finding | Evidence |
|----|----------|----------|---------|----------|
| F1 | blocker  | …        | …       | …        |
| F2 | major    | …        | …       | …        |
| F3 | minor    | …        | …       | …        |

Severity: **blocker** (must fix before proceed) · **major** (should fix) · **minor** (fix when convenient) · **nit** (style/preference)

## Assumptions challenged
- [claim] → [why it may not hold]

## Gaps / out of scope
- [what was not reviewed and why]

## Recommended next steps
1. [action for implementer — not performed by auditor]
```

## After the audit

Present findings to the user. Wait for direction before acting on any finding.

## Not this skill

- **grill-with-docs** — interactive Q&A to stress-test a plan against domain docs
- **hats** — multiple parallel lenses + synthesis
- **red-vs-blue** — adversarial attack vs defend pair
- **manifold drift-report** — spec↔code divergence via manifold CLI/MCP
- **manifold spec_audit** — revision discipline on DB graph (invoke manifold skill)
