# How to use manifold

Manifold is a **project compass**: a versioned spec graph in SQLite that answers orientation questions for long-horizon work. This guide is for **chat-first use** (agent + skill + MCP). CLI and web are alternates for the same data.

**Proper nouns:** [`glossary.md`](glossary.md) · **Agent skill:** [`../../bundles/manifold/skills/manifold/SKILL.md`](../../bundles/manifold/skills/manifold/SKILL.md)

---

## If you are new, read this first

You can use Manifold without learning the graph internals. Start with the question you need answered:

| If you want to know... | Ask this | You will see |
|---|---|---|
| What this project is | "What is this project?" | Purpose, important spec items, links to deeper views |
| Current state | "Where are we on `<project>`?" | Status brief or target-status summary |
| What is ready to work on | "What is ready next?" | Ready frontier work (`next-leaves`) |
| Whether spec changes were explained | "Run spec audit" | Revision-history findings |
| Whether code still matches spec | "Run drift report" | Violated, errored, unverified, and satisfied evidence buckets |
| What a proposed change will do | "Show the trajectory before accepting" | Preview of graph changes before mutation |

Use these docs by need:

| Need | Read |
|---|---|
| Quick usage and daily loop | This guide |
| Human/API vocabulary | [`glossary.md`](glossary.md#human-terms-vs-api-terms) |
| HTML, diagrams, status brief surfaces | [`human-presentation.md`](human-presentation.md) |
| Why the human-readable redesign exists | [`human-comprehension-redesign-plan.md`](human-comprehension-redesign-plan.md) |
| Full CLI/MCP setup | [`../../bundles/manifold/skills/manifold/references/user-guide.md`](../../bundles/manifold/skills/manifold/references/user-guide.md) |
| Roadmap and locked decisions | [`todo.md`](todo.md) |

---

## What you are not learning

You do not need to memorize 41 MCP tool names. You ask **compass questions** in plain language; the agent (with the manifold skill loaded) maps them to the right surface.

Manifold is **not**:

- A ticket tracker (use Linear / Issues)
- A dispatch engine (orchestrator — future separate skill)
- Live agent status (progress-tracker MCP)
- A one-shot Spec Kit workflow (use Spec Kit for greenfield feature specs)

---

## The compass questions

| You might say | Question | Primary surface |
|---|---|---|
| "What is this project about?" | What is this project? | `peek_project`, `list_nodes`, `show` |
| "Where are we?" | Where are we? | `list_targets`, node status |
| "What is ready next?" | What next? | `next-leaves` |
| "Did we explain our spec changes?" | Are revisions explained? | **`spec-audit`** |
| "Does the code match the spec?" | Does code match spec? | **`drift-report`** |
| "How are company themes tracking?" | Company themes | `portfolio-report` |
| "How do we evolve the spec toward X?" | As-is → to-be | **`trajectory propose`** → **`show`** → **`accept`** |

### Reviews and drift (don't mix these up)

| Idea | Manifold surface | Reads |
|---|---|---|
| **Spec review / revision hygiene** — pivots, missing `change_reason`, rationale without clarification | **`spec-audit`** | Revision history in the DB only |
| **Intent drift / code vs spec** — tests failing, checks not wired | **`drift-report`** | Verdicts on realization nodes (+ repo root for automated checks) |
| **Graph structure** — cycles, coverage, invalid edges | **`validate`** | Graph rules |

`spec-audit` never reads your codebase. `drift-report` never flags "unset change_reason" on old revisions — that's `spec-audit`.

### Status, evidence, and priority are separate

| Human idea | Manifold term | What it means | What it does not mean |
|---|---|---|---|
| Work state | `target_status` | Planned, in progress, achieved, abandoned, or superseded in the spec graph | Code is correct |
| Evidence status | `verdict_status` / drift bucket | A configured check is satisfied, violated, errored, or missing | The roadmap priority is known |
| Ready frontier | `next-leaves` | The smallest open graph leaves that are not blocked | The most valuable business priority |

`next-leaves` is readiness, not prioritization. You still decide what matters most.

`drift-report` is not "all clear" just because there are no violations. Treat **errored** checks as broken evidence and **unverified** items as unknowns.

---

## Setup once

1. **Runtime** — clone foundry; CLI via `packages/manifold/scripts/manifold`.
2. **Database** — one SQLite file **per product idea** (recommended):

   ```bash
   packages/manifold/scripts/manifold init-ideas
   ```

   Creates `~/.claude/foundry.db`, `~/.claude/chronicler.db`, `~/.claude/hailey.db` and writes `~/.claude/manifold.json` with the registry. Default for this repo: **`foundry`** → `ai-foundry` project.

   Point at one idea per session:

   ```bash
   manifold --idea foundry serve
   manifold --idea chronicler next-leaves chronicler
   ```

   Or set `$MANIFOLD_DB` / `db_path` in config for a single default file.

3. **MCP** — register [`bundles/manifold/server/mcp_server.py`](../../bundles/manifold/server/mcp_server.py) with `MANIFOLD_DB` set to the idea you're working on. Template: [`bundles/manifold/.mcp.json`](../../bundles/manifold/.mcp.json). Use separate MCP entries per idea if you switch often.
4. **Skill** — sync [`bundles/manifold/skills/manifold/`](../../bundles/manifold/skills/manifold/) to your host skills directory so the agent knows when and how to call manifold.
5. **Projects** — import or register at least one project (`manifold import …` or MCP `register_project`).

**Foundry dogfood:** `manifold init-foundry` resets the **current** DB to the ai-foundry graph. Prefer `init-ideas` for a clean per-idea layout.

**Visualization testing:** seed the rich Chronicler showcase (3 projects, 50+ nodes, cross-blockers):

```bash
manifold --idea chronicler seed-chronicler --force
manifold --idea chronicler serve
```

Then open `/projects/chronicler/brief`, `/mindmap?focus=I.1`, `/views/blockers?focus=R.5.1`.

Optional fictional Acme demo: `manifold seed-demo`. See [`human-presentation.md`](human-presentation.md).

Host-specific install paths (Claude, Cursor, …) will live in `install/hosts/` when added; until then see [`bundles/manifold/skills/manifold/references/user-guide.md`](../../bundles/manifold/skills/manifold/references/user-guide.md).

---

## Daily loop (chat-first)

```text
Orient  →  "what's next on <project>?"
Review  →  "spec audit on <project>" / "drift report on <project>"
Work    →  (you + agent implement in the repo)
Writeback → "mark <node> achieved" / "update rationale, reason evolution"
```

### Read (agent queries)

Examples you can paste into chat:

- *What is ready next for **web**?*
- *Why does node **web/R.3** exist? Show rationale and parents.*
- *Run a **spec audit** on **web** — anything flagged?*
- *Drift report for **web** — what's violated or unverified?*
- *What's blocking **product-app/R.12**?* (agent may use `list_cross_blocking_chain`)
- *How is theme **T.1** tracking?* (`portfolio-report`)

The agent calls MCP tools (or CLI) and summarizes. You decide priorities; manifold returns the **ready frontier from the graph**, not a ranked roadmap.

### Write (agent mutates the graph)

After implementation, tell the agent to update the spec:

- *Mark **web/R.12** as **achieved**.*
- *Update **web/I.2** rationale — we chose X because Y; **change_reason** = **evolution**.*
- *Link **portfolio/T.1** to **product-app/I.1**.*

Every content edit requires an explicit **`change_reason`**: `correction`, `evolution`, `clarification`, `refactor`, `pivot`, or `other`. Mechanical transitions may auto-set reasons.

Writes use **`actor`** (e.g. `agent:dispatch-1`) so revisions stay attributable.

### Rituals (weekly or before trusting the graph)

1. **Spec audit** — are we documenting *why* spec changes happened?
2. **Drift report** — for projects with verdicts wired, does code still match?
3. **Next-leaves** — is the frontier what you expect? Use `next-leaves --verbose` (CLI) to see cross-blocked exclusions.

---

## CLI and web (same compass)

| Mode | When |
|---|---|
| **Chat + MCP** | Default — compass Q&A and edits in flow |
| **CLI** | Scripts, CI (`drift-report` exits 1 on violations), quick terminal checks |
| **Web** | `manifold serve` — browse graph, spec-audit and drift-report pages |

```bash
packages/manifold/scripts/manifold next-leaves web
packages/manifold/scripts/manifold next-leaves web --verbose   # show cross-blocked
packages/manifold/scripts/manifold spec-audit web
packages/manifold/scripts/manifold drift-report web --force
packages/manifold/scripts/manifold serve
```

---

## Multi-project and portfolio

- **One idea, one DB (recommended)** — Chronicler, Hailey, and Foundry each get their own file under `~/.claude/` (`init-ideas`). No shared tables unless you opt into a rollup DB later.
- **Legacy: one DB, many projects** — still supported via `$MANIFOLD_DB` + multiple `project_id`s in the same file.
- **Portfolio** — optional rollup project `portfolio` with theme layer; seed separately when you need cross-idea bets (not included in `init-ideas`).
- **Cross-project blocking** — `create_cross_edge` (MCP); `next-leaves` excludes blocked leaves until blockers are `achieved`.

See [`../../bundles/manifold/skills/manifold/references/business-model.md`](../../bundles/manifold/skills/manifold/references/business-model.md).

---

## What the agent needs from you

| Agent can infer | You must supply |
|---|---|
| Which compass question | **Project id** (or unambiguous name) |
| spec-audit vs drift-report | **Judgment** on intentional pivots |
| Tool calls, revision ids | **Spec content** (rationale, body) |
| Blocker chains | **Whether to dispatch work** (orchestrator — not manifold) |

---

## Skills vs custom agents

**The manifold skill is the durable contract** — compass routing, nouns, anti-patterns. Any host agent with skill + MCP is a manifold-capable agent.

Custom subagents (read-only compass, spec editor only) are optional optimizations; they are not required for chat-first use.

---

## Further reading

| Doc | Topic |
|---|---|
| [`glossary.md`](glossary.md) | All proper nouns |
| [`human-comprehension-redesign-plan.md`](human-comprehension-redesign-plan.md) | Human-readable surface plan and evidence caveats |
| [`../../bundles/manifold/skills/manifold/references/user-guide.md`](../../bundles/manifold/skills/manifold/references/user-guide.md) | Full CLI/MCP setup |
| [`../../bundles/manifold/skills/manifold/references/why-manifold.md`](../../bundles/manifold/skills/manifold/references/why-manifold.md) | Why vs Spec Kit, tickets, memory |
| [`orchestrator-contract.md`](orchestrator-contract.md) | Pre-dispatch checklist for orchestrators |
| [`todo.md`](todo.md) | Roadmap and locked decisions |
