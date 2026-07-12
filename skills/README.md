# Authored skills (staging)

Skills **we write and own**, staged here before they earn a version and get
promoted into a plugin. Edit freely — foundry is source of truth.

## Registry (in-repo)

**[manifest.yaml](manifest.yaml)** — allowlist + dependency graph across *all*
authored skills (staging + promoted) and vendored skills (`requires`,
`suggests`, `dispatches`, `external`). Open work: **[todo.md](todo.md)**.

```bash
# After editing manifest.yaml:
python3 ../scripts/skills_manifest.py sync-docs   # inject ## Dependencies into SKILL.md
python3 ../scripts/skills_manifest.py validate
python3 ../scripts/skills_manifest.py deps brief
python3 ../scripts/skills_manifest.py used-by audit
```

Vendored copies: [`../vendor/skills/`](../vendor/skills/).

## Dependency kinds (manifest.yaml)

| Field | Meaning |
|-------|---------|
| `requires` | Hard — must be in manifest; validate fails if missing |
| `suggests` | Soft handoff after this skill (e.g. brief → subset) |
| `dispatches` | May invoke via Skill tool / subagent (e.g. plan-orchestrator → audit) |
| `external` | Plugin skills not in repo; listed in `external_registry` |

---

## Staged here

| Skill | Status | What it does | Triggers |
|-------|--------|--------------|----------|
| [os-doctor](os-doctor/) | shipped | Read-only PARA health check for `~/LifeOS` | /os-doctor, check the vault, weekly review |
| [present](present/) | draft | Human diagrams, briefs, mindmaps from manifold | diagram, mindmap, status brief |
| [worktree](worktree/) | shipped | Create/check/archive/revive/reap a wired git worktree | /worktree, new worktree, reap |

### Parked

`brief`, `audit`, `subset` — deferred 2026-07-05 (can live without for now;
revisit on demand). Present under their dirs, not in the active review queue.

---

## Promoted to plugins

These graduated out of staging and now live under [`../bundles/`](../bundles/)
(still registered in `manifest.yaml` by their bundle path):

| Skill | Home |
|-------|------|
| manifold | [`../bundles/manifold/skills/manifold/`](../bundles/manifold/skills/manifold/) |
| plan-orchestrator, progress-tracker | [`../bundles/plan-orchestrator/skills/`](../bundles/plan-orchestrator/skills/) |
| wardrobe, consult, hats, red-vs-blue | [`../bundles/crucible/skills/`](../bundles/crucible/skills/) |

The crucible lens × stance review system (evidence base:
[`../docs/adversarial-review-methodology.md`](../docs/adversarial-review-methodology.md))
shipped and was packaged into `plugins/crucible/` on 2026-07-05.

---

## Not here

| Artifact | Location |
|----------|----------|
| Vendored skills | [../vendor/skills/](../vendor/skills/) |
| progress-tracker MCP | bundled in [../bundles/plan-orchestrator/](../bundles/plan-orchestrator/) |
| Cursor built-in skills | `~/.cursor/skills-cursor/` (do not copy) |
| Superpowers plugin skills | Claude plugin cache |
