---
name: manifold
description: "Project compass for long-lived software specs. Use when the user asks what a project is for, what to build next, whether the spec audit is clean, or when reading/updating a manifold spec via CLI or MCP. Covers next-leaves, spec-audit, MCP spec_audit on tracked projects, node edits, validation, import/export. NOT for one-shot feature specs (use Spec Kit), task tickets (Linear/issues), live agent status (progress-tracker), or dispatching work (orchestrator). Proper nouns: docs/manifold/glossary.md. Usage: docs/manifold/how-to-use.md."
---

<!-- foundry:dependencies:start -->
## Dependencies

Registry: [`manifest.yaml`](../../../../skills/manifest.yaml) · refresh: `python3 scripts/skills_manifest.py sync-docs`

| Kind | Skills | Role |
|------|--------|------|
| **suggests** | `red-vs-blue`, `present` | Soft handoff after this skill — suggest, do not auto-chain |

**Used by:** `present` (suggests), `progress-tracker` (suggests)

<!-- foundry:dependencies:end -->

# manifold

**Project compass** — keeps a project's *why* structured, versioned, and queryable so you don't lose intent over months of agent-assisted work.

> Software projects lose their "why" faster than they lose their code. Manifold holds intent in a queryable graph with spec-audit (revision discipline), drift-report (spec↔code on wired verdicts), and a "what's next" API. Read `references/why-manifold.md` for how this compares to Spec Kit, KAOS tools, and agent memory.

**Store:** SQLite at `$MANIFOLD_DB` (default `~/.claude/manifold.db`). **Runtime:** `packages/manifold/` (library), `bundles/manifold/server/` (MCP), `apps/manifold-web/` (UI).

---

## The compass questions

| Question | How |
|---|---|
| What is this project? | Layered spec graph (intent → capabilities → contracts → realizations, or custom layers) |
| Where are we? | `target_status`, verdicts per node |
| What next? | `next-leaves <project>` — unfinished leaf nodes ready to work |
| Are spec revisions explained? | `spec-audit <project>` — M3 revision discipline |
| Does code match spec? | `drift-report <project>` — violated verdicts + unverified realizations (M4; not revision audit) |
| How do we get from as-is to to-be? | `trajectory propose` → `show` → `accept` — plan/apply, not ad-hoc edits |
| How are themes tracking? | `portfolio-report` — company theme roll-up (Topics H+I) |

---

## When to invoke this skill

**Do invoke** when:

- User asks "what should I build next?" for a manifold-tracked project
- User gives a **target brief** or asks how to evolve the spec toward a to-be state
- User asks if the project is on track, what changed from original intent, or why a spec node exists
- You need to read/update spec nodes, run validation, import/export, or call manifold MCP tools
- Orchestrator handoff: fetch `next-leaves`, write back verdicts/target status

**Do not invoke** when:

- **One-shot feature from scratch** → GitHub Spec Kit (`/speckit.specify` workflow) is a better fit
- **Task/ticket tracking** → Linear, Jira, GitHub Issues
- **"What are my agents doing right now?"** → progress-tracker MCP (`peek_project`, `todo_*`)
- **Dispatching and running agents** → **`dispatch-orchestrator`** (future skill); manifold only holds the spec

---

## Language → surface

| You say | Surface |
|---|---|
| What is this project? | `peek_project`, `list_nodes`, `show` |
| Where are we? | `list_targets`, node status |
| What next? | `next-leaves` |
| Spec changes explained? | `spec-audit` / MCP `spec_audit` |
| Code match spec? | `drift-report` / MCP `drift_report` |
| As-is → to-be? | `trajectory propose` → `show` → `accept` |
| Company themes? | `portfolio-report` |

Canonical routing: [`docs/manifold/how-to-use.md`](../../docs/manifold/how-to-use.md).

## Not this skill

- **audit** — independent review of files/plans/PRs (not manifold DB)
- **plan-orchestrator** — multi-phase DAG dispatch across components
- **progress-tracker** — live agent status (`peek_project`, `todo_*`)
- **red-vs-blue** — high-stakes adversarial completeness after findings (suggest, don't auto-chain)
- **dispatch-orchestrator** (future) — running agents; manifold holds the spec only

## Writeback after work

After implementing: `update_node` + **`change_reason`** + **`actor`** → `transition_target` → `run_validation`. Ritual: **work → writeback → optional spec-audit**. Weekly cadence: [`references/rituals.md`](references/rituals.md).

## Drift-report ritual

Always pass **`--repo`** (CLI) or **`project_root`** (MCP `drift_report`) — or set `project_root` in `spec_config`. Buckets: **violated** (mismatch), **errored** (check failed to run), **unverified** (no mechanism), **satisfied**. CLI exit **1** = violated only (not errored/unverified). Unverified is fine on unwired layers; not fine on realization nodes you dispatch against. Wiring + dogfood: [`references/verdicts.md`](references/verdicts.md).

**Verdicts vs status:** `drift-report` scores verdict checks, not `target_status`. Writeback (`transition_target`) moves `next-leaves`, not drift buckets — the two axes are independent.

## Trajectory ritual (plan / apply)

When the user gives a **target brief** (desired to-be state): **`propose`** → **`show`** (impact preview) → **`accept`** — never ad-hoc `update_node` chains. **`propose` never mutates** the graph; only **`accept`** writes. Do not call real **`next-leaves`** inside propose/show — preview includes `next_leaves_after`. After accept, run real **`next-leaves`** for execution. Details: [`references/trajectory.md`](references/trajectory.md).

## Portfolio & cross-project

`link_portfolio` · `create_cross_edge` · `list_cross_blocking_chain` — one DB, portfolio themes vs cross-project blocking. See [`references/business-model.md`](references/business-model.md).

---

## Core concepts (plain language)

- **Layers** — zoom levels on the same project (why → what → contracts → code mapping)
- **Nodes** — one spec item; has body, parents, status, rationale, and revision history
- **Verdicts** — is this node actually satisfied? (script, test, human, or LLM check)
- **Revisions** — every edit is versioned; **`change_reason` is required** on `update_node` (correction / evolution / clarification / refactor / pivot / other)

---

## Common commands

```bash
# CLI shim from repo root:
packages/manifold/scripts/manifold next-leaves <project>
packages/manifold/scripts/manifold spec-audit <project>
packages/manifold/scripts/manifold drift-report <project>
packages/manifold/scripts/manifold trajectory propose <project> --target-brief-file brief.md --legs-file legs.json
packages/manifold/scripts/manifold trajectory show <trajectory_id>
packages/manifold/scripts/manifold show <project> <node-id>
packages/manifold/scripts/manifold serve          # web UI
packages/manifold/scripts/manifold import <path> # v0.2 markdown tree
packages/manifold/scripts/manifold export <project> <out-dir>
```

MCP: register `bundles/manifold/server/mcp_server.py` — **42 tools** (23 read + 19 write), including `spec_audit`, `drift_report`, `propose_trajectory`, `peek_trajectory`, `accept_trajectory_leg`, `reject_trajectory`, `portfolio_report`, `link_portfolio`, `create_cross_edge`, `list_cross_blocking_chain`, … Glossary: [`docs/manifold/glossary.md`](../../docs/manifold/glossary.md) · How to use: [`docs/manifold/how-to-use.md`](../../docs/manifold/how-to-use.md).

---

## References

- **`docs/manifold/how-to-use.md`** — chat-first usage (compass questions, daily loop)
- **`references/why-manifold.md`** — why this exists vs Spec Kit, KAOS, tickets, agent memory
- **`references/user-guide.md`** — full CLI/MCP setup and workflows
- **`references/business-model.md`** — one DB, portfolio (A) vs cross-project (B) patterns
- **`references/rituals.md`** — weekly spec-audit → drift-report → next-leaves; when to suggest red-vs-blue
- **`references/verdicts.md`** — verdict mechanisms, buckets, `project_root` / `--repo`, dogfood bootstrap
- **`references/trajectory.md`** — propose → show → accept; plan/apply; leg kinds; anti-patterns
- **`references/architecture.md`** — schema and internals (when extending or debugging)
- **`docs/manifold/orchestrator-contract.md`** — pre-dispatch checklist for orchestrator integrators
