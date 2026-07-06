# `.gitignored/` — local scratch

**Not for git.** This folder is listed in `~/.gitignore_global` so plans, audits, handoffs, and other ephemeral agent output stay on disk but never get committed.

Use subfolders as you like:

| Subfolder | Examples |
|---|---|
| `plans/` | iteration plans, WIP design, research prompts before synthesis ships |
| `audits/` | red-team reports, completeness audits, dogfood session dumps |
| `handoffs/` | session handoffs between chats |
| `demos/` | HTML mocks, spike UIs, review artifacts |

**Durable canon** still belongs in tracked paths:

- Product docs → `docs/<product>/`
- Shipped design history → `docs/archive/`
- Completed research → `research/` (study folder + `synthesis.md`)

When something graduates from scratch to canon, move it out of here and commit it there.

## Current layout (local)

```
plans/
  manifold/              implementation-plan, skill-iteration-plan
  human-output-2026-06/  Topic K synthesis (complete — promoted from .gitignored)
  trigger-vocabulary-2026-06-07.md
  readme-design.md
  palimpsest-quarry.md
handoffs/
  SESSION-HANDOFF-2026-05-24-orchestrator.md
audits/
  cross-tech-dogfood-2026-06-07.md
demos/
  human-layer-demo/      Acme Checkout HTML mocks
```
