# skills/ — the registry home

**Structure.** This directory holds the skill **registry**, not skills. Every
authored skill lives in its owning bundle (`bundles/<name>/skills/`) or, when
two bundles share it, in `library/skills/`. The one exception: `os-doctor/`
(personal, fate undecided — repo issue #8).

- **[manifest.yaml](manifest.yaml)** — allowlist + dependency graph across all
  authored (bundle + library) and vendored skills.
- **[todo.md](todo.md)** — open skill work.

**Why.** The old staging pipeline (draft here → promote to a plugin) is
retired: a skill is born in its bundle, and `library/` is the only promotion
target (second consumer, Rule of Three). One registry file keeps the
cross-bundle dependency graph checkable.

**Operate.**

```bash
python3 ../scripts/skills_manifest.py validate    # graph + exact-case SKILL.md check
python3 ../scripts/skills_manifest.py sync-docs   # inject ## Dependencies into SKILL.md
python3 ../scripts/skills_manifest.py deps <skill>
python3 ../scripts/skills_manifest.py used-by <skill>
```

| Manifest field | Meaning |
|-------|---------|
| `requires` | Hard — must be in manifest; validate fails if missing |
| `suggests` | Soft handoff after this skill |
| `dispatches` | May invoke via Skill tool / subagent — must ship in the same bundle (bundle-completeness) |
| `external` | Outside foundry (host plugins); listed in `external_registry`, documented not validated |

## Where things live

| Artifact | Location |
|----------|----------|
| Bundle-local skills | `../bundles/<name>/skills/` |
| Shared (2+ bundles) | `../library/skills/` — wardrobe, audit, hats, red-vs-blue |
| Shared agents | `../library/agents/` — panelist, red-attacker, blue-verifier, adjudicator |
| Vendored upstream | [../vendor/skills/](../vendor/skills/) |
| MCP servers | inside their bundle (`server/`) |
