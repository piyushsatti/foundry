# Manifold docs

Product documentation for **manifold** — the project compass (SQLite graph, CLI, MCP, web UI).

**Start here for usage:** [`how-to-use.md`](how-to-use.md) — chat-first guide (compass questions, spec-audit vs drift-report, daily loop).

**New user path:** start with [`how-to-use.md`](how-to-use.md#if-you-are-new-read-this-first), then use [`glossary.md`](glossary.md#human-terms-vs-api-terms) only when a term needs precision.

Future foundry skills will get their own `docs/<skill>/` folders; manifold lives here.

---

## Canon (living)

| Doc | Use for |
|---|---|
| [`how-to-use.md`](how-to-use.md) | **How to consume manifold** — agents, chat, CLI, web |
| [`glossary.md`](glossary.md) | Proper nouns — code and docs must match |
| [`todo.md`](todo.md) | Master checklist, locked decisions, what's next |
| [`human-comprehension-redesign-plan.md`](human-comprehension-redesign-plan.md) | Research-backed plan for human-readable Manifold surfaces |
| [`human-presentation.md`](human-presentation.md) | Diagrams, mindmaps, HTML — presentation layer split |
| [`orchestrator-contract.md`](orchestrator-contract.md) | Pre-dispatch checklist (Topic F stub) |

Ephemeral plans and session notes live in **`.gitignored/`** (local only, not tracked in git).

---

## Code & skill (implementation)

| Path | Role |
|---|---|
| [`../../packages/manifold/`](../../packages/manifold/) | Python library + CLI |
| [`../../plugins/manifold/server/`](../../plugins/manifold/server/) | MCP server (40+ tools) |
| [`../../apps/manifold-web/`](../../apps/manifold-web/) | Browser UI |
| [`../../plugins/manifold/skills/manifold/`](../../plugins/manifold/skills/manifold/) | Agent skill (SKILL.md + references) |

**Skill deep dives:** [`../../plugins/manifold/skills/manifold/references/user-guide.md`](../../plugins/manifold/skills/manifold/references/user-guide.md) (setup, MCP registration), [`why-manifold.md`](../../plugins/manifold/skills/manifold/references/why-manifold.md) (positioning).

---

## Research & archive

| Path | Role |
|---|---|
| [`../../research/manifold/`](../../research/manifold/) | Landscape + Topic K human-output studies |
| [`../archive/topics/`](../archive/topics/) | Shipped topic design specs |
| [`../archive/manifold-v0.1/`](../archive/manifold-v0.1/) | Pre-landscape design |

---

## Quick commands

```bash
packages/manifold/scripts/manifold version
packages/manifold/scripts/manifold next-leaves <project>
packages/manifold/scripts/manifold spec-audit <project>
packages/manifold/scripts/manifold drift-report <project>
packages/manifold/scripts/manifold serve
```

**Tests:** `cd packages/manifold && python3 -m unittest discover` (+ MCP + web suites).

**Env:** `$MANIFOLD_DB`, `$MANIFOLD_CONFIG` — see [`how-to-use.md`](how-to-use.md#setup-once).
