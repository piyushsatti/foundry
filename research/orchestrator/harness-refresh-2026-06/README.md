# Orchestrator harness refresh — June 2026

**Status:** Complete  
**Purpose:** Reconcile the May 2026 orchestrator v0.1 contract with May–June Claude Code harness research before writing `docs/orchestrator-design.md` or `skills/orchestrator/`.

## Inputs

| Source | Role |
|---|---|
| [`docs/archive/orchestrator-2026-05/orchestrator-synthesis-2026-05-24.html`](../../../docs/archive/orchestrator-2026-05/orchestrator-synthesis-2026-05-24.html) | v0.1 contract (§7) |
| [`docs/archive/orchestrator-2026-05/orchestrator-synthesis-addendum-2026-05-24.md`](../../../docs/archive/orchestrator-2026-05/orchestrator-synthesis-addendum-2026-05-24.md) | Handoff schema extension |
| `.gitignored/handoffs/SESSION-HANDOFF-2026-05-24-orchestrator.md` | Locked user decisions (local) |
| [`research/claude-code/ecosystem-2026-05/`](../claude-code/ecosystem-2026-05/) | Harness + model/effort field research |
| [`research/manifold/landscape-2026-06/synthesis.md`](../../manifold/landscape-2026-06/synthesis.md) | Positioning: intent-broker vs orchestrator |

## Deliverable

[`synthesis.md`](synthesis.md) — contract audit, build-vs-native scope, skill/runner deltas, ordered action list, **§10 gaps before skill design**.

## Next step (outside research/)

Write [`docs/orchestrator-design.md`](../../../docs/orchestrator-design.md) using this synthesis + May HTML §7 + addendum.
