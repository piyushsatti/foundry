---
name: feedback_plan_redblue_then_implement
description: "Non-trivial work gets a durable dated plan doc + adversarial red/blue review before any code or config change"
metadata:
  node_type: memory
  last_updated: 2026-06-01
  type: feedback
  originSessionId: 6cceed01-0bbf-411f-a008-fd436f2f8345
---

# Plan → Red/Blue Adversarial Review → Implement

## Why
Implementing before planning makes design problems surface mid-execution — wasting context and creating hard-to-reverse changes. Adversarial review (two independent agents hunting failure modes) catches blind spots that neither the user nor a single assistant surface alone. And durable plan files survive session compaction and context resets; chat scrollback does not. The pattern is demonstrated across 10+ dated plan docs in `~/Documents/notes/infrastructure/` (see [[reference_infrastructure_repo_map]]). The most load-bearing red-team finding to date: stacking new features on a broken security foundation is net-negative even when each feature is individually correct (2026-06-01 three-features red/blue review).

## How to Apply
1. **Write a dated plan file** in `~/Documents/notes/infrastructure/` before implementing. Include: problem statement, why-now, options with tradeoffs, open questions, verifiability gates. Name: `YYYY-MM-DD-plan-<slug>[-v2].md` (write a v2 if a v1 exists — v1 is superseded).
2. **Cross-link**: add a tracker entry in `memory/workflow_pending_cleanup.md` pointing to the plan file.
3. **Red/blue pass**: two independent Sonnet subagents — one finds failure modes / attack surface, one finds control gaps / unverified assumptions. Converge → proceed; diverge → stop and surface to the user.
4. **Respect the Implementation Gate**: research, proposals, and plans are NOT permission to execute — wait for an explicit "do it" / "build it" / "implement".
5. **Verify live state** before trusting any "done" record: stale tracker entries have misled sessions into needless rework. Observed reality beats a written claim ([[feedback_diagnose_before_fixing]]).

## Scope
Applies to: new guards/hooks, settings changes, dotfile migrations, portability scripts, Claude Code org changes, terminal-stack migrations. Not required for routine maintenance, single-file edits, or explicit user-directed quick fixes.

## Related
[[reference_infrastructure_repo_map]] · [[project_portable_dev_machine_north_star]] · [[feedback_diagnose_before_fixing]] · [[feedback_long_output_to_file]]
