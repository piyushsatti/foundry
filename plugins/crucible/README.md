# crucible

Lens × stance adversarial + panel review system. Every reviewer in crucible is a
tuple **(lens, stance, model, effort)**: the **lens** is what a reviewer cares
about (architect, security, frontend, …), the **stance** is how it engages
(`attack` · `verify` · `neutral` · `partner`), and model/effort is capability
allocation pinned per stance agent. Three entry points compose preset tuples so
a lens is defined once and consumed everywhere — no persona is ever
re-described across skills.

## Skills

| Skill | Stance | Job |
|-------|--------|-----|
| `wardrobe` | — (reference library, not invocable) | The shared hat library — one file per professional lens, consumed by all three skills below |
| `consult` | partner | "Think this through with me" — one lens, in-thread, conversational brainstorm/validate |
| `hats` | neutral | "What am I missing?" — 3–4 distinct lenses, blind parallel panel, structured synthesis |
| `red-vs-blue` | attack + verify | "Will this break?" — adversarial attack/verify pair + adjudicated verdict, gated by a worthiness check |

`consult`, `hats`, and `red-vs-blue` all `requires: [wardrobe]` in the skills
manifest. The wardrobe's 14-hat v1 roster — 10 general-software
(`architect`, `senior-engineer`, `security`, `sre`, `frontend`, `product`,
`coverage`, `simplifier`, `finance`, `coach`) plus 4 agentic-infra
(`prompt-engineer`, `harness-engineer`, `skill-designer`, `eval-engineer`) — and
its authoring contract live in
[`skills/wardrobe/hats/HATS.md`](skills/wardrobe/hats/HATS.md).

## Agents

Four stance agents carry pinned model/effort so skills dispatch a real
subagent instead of a generic one. Both `model:` and `effort:` in agent
frontmatter are **honored** by Claude Code (documented supported fields —
verified 2026-07-05 via [sub-agents docs](https://code.claude.com/docs/en/sub-agents.md);
`effort:` takes `low`/`medium`/`high`/`xhigh`/`max`), so the pins do take
effect when the agent type is dispatched. What stays **provisional** is the
chosen *values* — placeholders pending the phase-3 seeded-flaw benchmark in
the design doc, not tuned data. (Whether the pins take effect ≠ whether the
values are optimal; the first is settled, the second is not.)

| Agent | Stance | Dispatched by |
|-------|--------|---------------|
| `red-attacker` | attack | `red-vs-blue` |
| `blue-verifier` | verify | `red-vs-blue` |
| `adjudicator` | reconciles red + blue, never either | `red-vs-blue` |
| `panelist` | neutral, one hat each | `hats` |

`consult` runs in-thread at the session model — no agent, no pin. That's
intentional (consult is conversational), not an omission.

## Evidence base

The design decisions each skill/hat/agent cites by D-number live in
[`docs/adversarial-review-methodology.md`](docs/adversarial-review-methodology.md)
(D1–D11 protocol layer: why external review beats self-critique, why 3–4
blind parallel reviewers, why one round, why blue verifies rather than
counter-attacks, why adjudication is separate; D12–D17 persona/contract
layer: why a hat is a checklist-contract and not a character, why frontmatter
is withheld from the model, why personas drift and need re-injection).
Every skill, hat file, and agent cites this doc as
`${CLAUDE_PLUGIN_ROOT}/docs/adversarial-review-methodology.md`, with a
relative-path fallback noted alongside each citation for the case where
`${CLAUDE_PLUGIN_ROOT}` is unset. The canonical copy lives here in the plugin;
a one-line pointer stub is left at the old repo-root path
(`docs/adversarial-review-methodology.md`) for anyone who finds it there
first.

## The plan-mode hook (EXPERIMENTAL)

`hooks/plan-review-nudge.sh` is a `PreToolUse` hook keyed on `ExitPlanMode`.
It's a heuristic, **never-blocking** nudge: if a finalized plan looks
high-stakes (long, or matches `migration|auth|security|launch|delete|
production|payment|schema`), it emits a short advisory reminding you to
consider running `red-vs-blue` before proceeding — at most once, and it
always allows the tool call regardless. `hooks/hooks.json` wires it via
`${CLAUDE_PLUGIN_ROOT}` for plugin-native autoloading.

**This is the first hook shipped by any plugin in this repo.** Status after the
2026-07-05 install (checked against the
[hooks](https://code.claude.com/docs/en/hooks.md) and
[plugins](https://code.claude.com/docs/en/plugins.md) docs):

1. **Plugin-hook autoload — CONFIRMED** (2026-07-05, `claude plugin details`
   inventories `Hooks (1) PreToolUse`; no `settings.json` edit needed).
2. **`ExitPlanMode` matcher — VERIFIED firing live** (2026-07-12: the nudge
   fired on plan finalization in a real session, twice).

The hook is still **experimental** in a different sense: it has not been
through a proper hook design/test pass — that is the dedicated hooks-overhaul
phase (repo issue #3).

Treat the hook as experimental until confirmed working post-install. If
autoload doesn't fire, `hooks/settings-fragment.example.json` is a manual
fallback — paste it into `.claude/settings.json` under `hooks.PreToolUse`
(with the install path filled in) to wire the same script by hand. The hook
never blocks in any case, so a non-firing or mis-wired hook is inert, not
harmful.

## Running skill evals

Each skill ships a structural eval set under `skills/<name>/evals/evals.json`
(prompt + expected-output checklist; full agent evals — running a prompt
against a live agent and judging the response — happen in the Cursor skill
UI, not here). Validate structure from the repo root:

```bash
python3 scripts/run_skill_evals.py --skill wardrobe
python3 scripts/run_skill_evals.py --skill consult
python3 scripts/run_skill_evals.py --skill hats
python3 scripts/run_skill_evals.py --skill red-vs-blue
```

The script resolves each skill's directory via `skills/manifest.yaml`, so it
works whether a skill lives under `skills/` or, as here, under `bundles/`.

## Status

Phases 1–2 (hat library + stance agents) shipped and were test-approved
2026-07-05 as sibling `skills/` + `home/agents/` installs. This phase (4)
folded them into this plugin; the interim locations are decommissioned
(moved, not duplicated — nothing remains at `skills/wardrobe`,
`skills/consult`, `skills/hats`, `skills/red-vs-blue`, or
`home/agents/{red-attacker,blue-verifier,adjudicator,panelist}.md`). Phase 3
(the seeded-flaw model×effort benchmark) has not yet run; agent
model/effort pins remain provisional until it does. Full design history:
`.gitignored/plans/crucible-plugin-design.md` (local, not committed).
