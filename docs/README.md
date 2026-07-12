# foundry docs

Durable design and product documentation. Ephemeral session state (handoffs, plans, audits) is **not** here — it lives in `.gitignored/` and is never committed.

## Manifold

The KAOS project-compass — a spec substrate (`packages/manifold`, a.k.a. `manifold-lib`), an MCP server (`bundles/manifold`), and a web UI (`apps/manifold-web`).

| Doc | Purpose |
|---|---|
| [`manifold/how-to-use.md`](manifold/how-to-use.md) | Start here — chat-first compass guide |
| [`manifold/README.md`](manifold/README.md) | Index |
| [`manifold/glossary.md`](manifold/glossary.md) | Canonical nouns + MCP tool surface |
| [`manifold/orchestrator-contract.md`](manifold/orchestrator-contract.md) | Integration contract |
| [`manifold/kaos-lineage.md`](manifold/kaos-lineage.md) | Formal grounding (Tree vs DAG across four traditions) |
| [`manifold/todo.md`](manifold/todo.md) | Working backlog |

## Claude Code setup (design notes)

Rationale and reference behind this machine's Claude Code configuration — all employer-agnostic.

| Doc | Purpose |
|---|---|
| [`design-philosophy.md`](design-philosophy.md) | Posture, threat model, per-guard rationale |
| [`2026-06-11-config-baseline.md`](2026-06-11-config-baseline.md) | Pre-redesign settings snapshot |
| [`access-tier-roadmap.md`](access-tier-roadmap.md) | Wishlist for the guard system |
| [`clipboard-model.md`](clipboard-model.md) · [`permission-pipe-limitation.md`](permission-pipe-limitation.md) · [`worktree-context-loading.md`](worktree-context-loading.md) | Investigated Claude Code behaviors |
| [`capture-tooling/`](capture-tooling/) | **Legacy** — the pre-plugin config-capture scripts (superseded by `bundles/` + `home/`) |
| [`PROVENANCE.md`](PROVENANCE.md) | Where each consolidated component came from |

## Archive

Shipped or superseded design history in [`archive/`](archive/): manifold v0.1 design, shipped topic specs (drift-report, portfolio/cross-project, trajectory), and the May 2026 orchestrator brainstorm.

## Conventions

- **Durable docs** → tracked here in `docs/`.
- **Ephemeral scratch** (plans, audits, handoffs) → `.gitignored/` (local only, never committed).
