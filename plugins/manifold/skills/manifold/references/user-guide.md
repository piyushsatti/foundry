# manifold — User Guide

You've cloned `agent-skills` and want to use manifold to manage layered project specs. This doc gets you from zero to "importing a project + editing a node + handing it to an agent" in under five minutes.

If you want internals, read [`ARCHITECTURE.md`](ARCHITECTURE.md) instead.

---

## What manifold does for you

You have a project. The project has goals, capabilities, contracts, and code. As the project grows you lose track of which capabilities are speculative versus shipped, which contracts are stable, and what the project's intent layer even *says* anymore.

Manifold gives you a structured spec for your project:

- **Layers** — intent / capabilities / contracts / realizations (or whatever you define). Each layer is a complete view of the project at one resolution.
- **Nodes** — one per spec item. Carry a body, structural fields (layer, parents, verdict, target), rationale, and alternatives considered.
- **Compass** — `next-leaves` answers "what do we work on next?" `target_status` tracks where each node is in its lifecycle; defaults to `planned` on creation.
- **Spec audit (M3)** — every content edit requires `change_reason`. `spec-audit` surfaces unexplained revisions and rationale changes.
- **Drift report (M4)** — `drift-report` rolls up violated verdicts and unverified realizations on the bottom layer (spec↔code).
- **Portfolio (H)** — `portfolio-report` rolls up company **themes** across team projects; `render portfolio --template quarter-roadmap` for exec slides.
- **Cross-project (I)** — `create_cross_edge` + `list_cross_blocking_chain`; `next-leaves` respects blockers in other projects.
- **Verdicts** — automated checks, AST assertions, LLM judgments, or human sign-off per node. The spec is checked, not just written.
- **History** — every change is a revision. Time-travel queries: how did this node evolve?

All of this lives in a single SQLite database (`~/.claude/manifold.db`). No spec files on disk.

---

## Install

The skill is stdlib-only Python. Runtime code is split across the repo:

| Path | Role |
|---|---|
| `packages/manifold/` | Core library + CLI |
| `mcps/manifold/` | MCP server |
| `apps/manifold-web/` | Web UI (`manifold serve`) |

```bash
git clone https://github.com/YOU/agent-skills ~/code/agent-skills
cd ~/code/agent-skills
packages/manifold/scripts/manifold version
packages/manifold/scripts/manifold --help
```

Optional: `ln -sf ~/code/agent-skills/packages/manifold/scripts/manifold ~/bin/manifold`

For Claude Code, copy or link `skills/manifold/` → `~/.claude/skills/manifold/` (instructions only; CLI/MCP use paths above).

---

## The DB

manifold stores everything in one SQLite file:

```
~/.claude/manifold.db
```

You can override the path with `$MANIFOLD_DB`:

```bash
export MANIFOLD_DB=~/my-projects/spec.db
```

The file is created on first use. **Take backups occasionally:** see the "Backups" section below.

---

## Configuration

manifold can be tuned via a machine-local JSON file at `~/.claude/manifold.json`. This
consolidates the three runtime knobs so you don't repeat them across your shell profile,
`.mcp.json`, and cron wiring.

### Precedence

For each setting, the most specific source wins:

```
env var  >  config file  >  built-in default
```

Environment variables always win; existing env-var users and CI are unaffected.

For `judge_command` specifically, there is an additional tier: a per-project setting in the
DB (stored in `spec_config.judge_command`) sits between the env var and the config file,
because a project-level setting is more specific than a machine-level one.

### The config file

```json
{
  "db_path": "~/.claude/manifold.db",
  "judge_command": "claude --print",
  "snapshot_interval": 3600
}
```

All three keys are optional. `~` in `db_path` is expanded; `judge_command` is **not**
expanded by manifold (the shell handles its own expansion at execution time).

The config file path can be overridden via `$MANIFOLD_CONFIG` (useful for testing).

### `manifold config` commands

**`manifold config path`** — Print the resolved config file path and whether it exists.

```
$ manifold config path
/Users/me/.claude/manifold.json  (exists)
```

**`manifold config show`** — Show each effective setting, its resolved value, and where it
came from (`env` / `file` / `default`). Useful for "why is my DB pointing there?"

```
$ manifold config show
db_path            /Users/me/.claude/manifold.db       (default)
judge_command      claude --print                       (file)
snapshot_interval  3600                                 (default)
config path        /Users/me/.claude/manifold.json      (exists)
```

**`manifold config init [--force]`** — Write a config file seeded from your current
effective values (so whatever env vars you have right now become the file's starting
point). Refuses to overwrite an existing file unless `--force` is given.

```
$ manifold config init
OK: config written to /Users/me/.claude/manifold.json

$ manifold config init
config already exists at /Users/me/.claude/manifold.json (use --force to overwrite)

$ manifold config init --force
OK: config written to /Users/me/.claude/manifold.json
```

To edit settings after initialization, open the JSON file in any text editor. There is no
`config set` command (hand-editing is simpler and more transparent).

---

## Common workflows

### 1. Import an existing v0.2 spec

If you have a project with a v0.2 manifold spec (`<project>/specs/spec.yaml` + `<project>/specs/<layer>/*.md`), import it:

```bash
manifold import ~/code/my-project
```

Output:

```
OK: imported project 'my-project'
     nodes: 27
     revisions: 84
```

The importer walks the project's git history of `specs/` and writes every commit as a revision. So you import with full history, not just the current state.

Re-running `manifold import` is **idempotent**: it picks up from the last imported git_sha and only replays new commits.

### 2. Show a node

```bash
manifold show my-project I.1
```

Renders the node as markdown. Useful for reading specs in a terminal.

### 3. Edit a node's body

```bash
manifold edit my-project I.1 --reason clarification
```

Opens `$EDITOR` (defaults to `vi`) with the node's markdown body. Save and quit; a new revision lands in the DB. **`--reason` is required** when the body changes (`correction` | `evolution` | `clarification` | `refactor` | `pivot` | `other`). If you didn't change anything, manifold says "No changes; nothing to save."

> **Note:** the CLI only edits the body. To edit structural fields (layer, parents, target_status, verdict), use the MCP from an agent, or the web UI (`manifold serve`).

### 4. Take a backup

```bash
manifold snapshot
# OK: snapshot at /Users/you/.claude/manifold.db.snapshot-2026-05-23T22-12-04+00-00
```

Creates a `VACUUM INTO` backup as a sibling file. Snapshots are small (manifold dbs stay under tens of MB) and complete; you can copy them anywhere.

### 5. Export to markdown tree (git-friendly archival)

```bash
manifold export my-project ~/archives/my-project-2026-05
# OK: exported 'my-project'
#      nodes: 27
#      out:   /Users/you/archives/my-project-2026-05/specs/
```

Writes a v0.2-style on-disk spec tree: `<out>/specs/spec.yaml` + `<out>/specs/<layer>/<id>-<slug>.md` per node, with YAML frontmatter (target/verdict/parents nested) + markdown body. Diff-friendly, human-readable, round-trippable through `manifold import`.

**This is not the same as `dump`.** Export writes current state only — no revision history, no validation results, no verdicts table. Use `dump` for full backups; use `export` for git-friendly archives, handoff to external tools, or operators who prefer files.

The output refuses to overwrite an existing `specs/` directory; move or delete the old one first.

### 6. Dump for portability

`snapshot` makes a binary SQLite file. For a portable, text-based backup:

```bash
manifold dump ~/backups/manifold-2026-05-23.ndjson
```

Writes a newline-delimited JSON file with one record per row. Lossless. To restore into a fresh DB:

```bash
MANIFOLD_DB=/tmp/restored.db manifold restore ~/backups/manifold-2026-05-23.ndjson
```

(Manifold refuses to restore into an existing DB — protects you from clobbering live data.)

---

## Hand manifold to an AI agent (MCP)

manifold ships an MCP server so Claude Code (and any other MCP client) can read and write your spec directly. Set it up once:

### Register the MCP server

Copy `mcps/manifold/.mcp.json.example` into your host MCP config:

```json
{
  "mcpServers": {
    "manifold": {
      "command": "python3",
      "args": ["/Users/YOU/code/agent-skills/mcps/manifold/server/mcp_server.py"],
      "env": {
        "MANIFOLD_DB": "/Users/YOU/.claude/manifold.db"
      }
    }
  }
}
```

Replace paths. Restart your MCP host.

### Headless / CI (no MCP host registration)

When the MCP client is not registered (subagents, CI, scripted agents), pipe JSON-RPC lines to the server over stdio. Build request lines with a heredoc — do not hand-escape JSON in `printf`.

```bash
MANIFOLD_DB=~/.claude/manifold.db python3 mcps/manifold/server/mcp_server.py <<'EOF'
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"ci","version":"1"}}}
{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"next_leaves","arguments":{"project_id":"obs-fastapi"}}}
EOF
```

One JSON object per line. Send `initialize` first, then `tools/call`. Set `MANIFOLD_DB` in the environment. Full tool list and input schemas: `TOOLS` in `mcps/manifold/server/mcp_server.py` (~line 510).

### Verify the agent can see it

In Claude Code, type:

> What manifold tools do you have available?

The agent should list **38** tools: `peek_node`, `list_projects`, `create_node`, `update_node`, `spec_audit`, `drift_report`, `portfolio_report`, `create_cross_edge`, … If it doesn't see them, the MCP isn't registered — re-check the path in `.mcp.json`.

### Example agent prompts

> Show me the verdict status across all nodes in `my-project`.

The agent uses `peek_project` + `list_nodes`.

> What targets are planned across all my projects?

The agent uses `list_targets` with no `project_id` filter.

> Walk back through the history of node K.6 in `my-project` — when did its verdict mechanism change?

The agent uses `list_revisions` + `diff_revisions`.

> Mark target on node C.3 as achieved.

The agent uses `peek_node` to get `current_revision_id`, then `transition_target` with that as `expected_revision_id` and `to_status='achieved'`.

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'manifold'"

You're running `python3 -m manifold` from the wrong directory. Either:
- `cd` into `skills/manifold/` in your repo clone, OR
- Use a PATH shim that `cd`s there before invoking (see Install above).

### "FAIL: node X:Y not found"

The node ID is case-sensitive. Try `manifold show <project>` to see the project's node IDs, or use `resolve_node` via MCP for fuzzy lookup.

### "STALE_REVISION" error from an agent

The agent's view of the node is older than what's actually in the DB (someone else — you, another agent, the CLI — modified it). The agent should call `peek_node` again to get the fresh `current_revision_id` and retry the update with that. Modern agents handle this automatically; if yours doesn't, that's a bug in the agent.

### "MISSING_ACTOR" error from an agent

The MCP requires a non-empty `actor` field on every write so revisions are attributable. The agent should pass `actor="agent:<dispatch-id>"` or similar. If the agent omits it, manifold rejects the write. CLI writes auto-use `human:<your-shell-user>`.

### My DB is corrupt / I lost data

If you've been taking snapshots (`manifold snapshot`), restore the most recent one:

```bash
mv ~/.claude/manifold.db ~/.claude/manifold.db.broken
cp ~/.claude/manifold.db.snapshot-<timestamp> ~/.claude/manifold.db
```

If you haven't been taking snapshots, but you have an NDJSON dump:

```bash
mv ~/.claude/manifold.db ~/.claude/manifold.db.broken
MANIFOLD_DB=~/.claude/manifold.db manifold restore ~/backups/manifold-<date>.ndjson
```

If you have neither: the project is lost. Take snapshots.

### How often should I snapshot?

For active development: hourly is reasonable (you can set `MANIFOLD_SNAPSHOT_INTERVAL=3600`, though there's no built-in scheduler — wire it to cron yourself). For light use: weekly.

---

## Browse + edit in your browser

manifold ships with a web UI. Start the server:

```bash
manifold serve
# → manifold web server at http://127.0.0.1:7779/
```

Then open `http://127.0.0.1:7779/` in any browser. You'll see:

- **`/`** — list of projects
- **`/projects/<id>`** — **project dashboard** (nodes-per-layer, target/verdict distributions, last validation, recent revisions) + **Run validation button** + tree of layers + nodes with target/verdict badges
- **`/projects/<id>/nodes/<n>`** — node detail with markdown-rendered body + revision timeline (each revision links to its diff page)
- **`/projects/<id>/nodes/<n>/edit`** — CodeMirror body editor + **collapsible "Structural fields" panel** (title, layer, target_status, verdict_mechanism + check/assertion, parents, peers_depends_on); `Cmd+S` saves
- **`/projects/<id>/nodes/<n>/revisions/<rev>`** — revision detail: field-by-field old/new diff + unified body diff
- **`/projects/<id>/validations/<id>`** — validation result page (issues + verdicts tables)
- **`/reports/targets`** — cross-project planned/in-progress targets
- **`/reports/flips`** — cross-project unstable verdicts
- **`/reports/portfolio`** — company theme roll-up (Topics H+I)

The edit form enforces **optimistic concurrency**: a hidden `expected_revision_id` is submitted with each save. If someone else (you, an agent) modified the node between the time you opened the form and the time you clicked Save, you get a conflict page and re-read.

There's also a JSON API at `/api/v1/*` for programmatic access (alternative to the MCP):

```bash
curl http://127.0.0.1:7779/api/v1/projects
curl http://127.0.0.1:7779/api/v1/projects/my-project/nodes/I.1

# PATCH a node body (requires If-Match for optimistic concurrency)
curl -X PATCH http://127.0.0.1:7779/api/v1/projects/my-project/nodes/I.1 \
  -H "If-Match: 42" \
  -H "Content-Type: application/json" \
  -d '{"fields": {"body": "new body"}, "actor": "human:me"}'
```

The server binds to `127.0.0.1` only by default — manifold has no auth layer. For multi-machine access by a single operator, use a private network overlay (Tailscale, SSH tunnel, VPN) rather than exposing the port. Auth comes later only if multiple humans need different permissions on the same instance.

CodeMirror is vendored locally under `web/static/codemirror/` — works offline. No CDN dependency at runtime.

## Validate your spec

`manifold validate <project>` runs the structural checks (layer membership, tree property, intra-layer DAG, external realization, coverage rule) on the project's nodes. Add `--with-verdicts` to also run each node's verdict mechanism (`automated_check` shells out, `python_assertion` runs a sandboxed AST walker, `human_signoff` reads the column). `--with-targets` runs target-state checks (block-DAG cycles + stale planned targets older than 180 days).

```bash
manifold validate my-project
# OK: validation 17 finished
#      nodes:    27
#      issues:   0
#      verdicts: 0

manifold validate my-project --with-verdicts --with-targets
# OK: validation 18 finished
#      nodes:    27
#      issues:   2
#      verdicts: 27
#
# Issues:
#   - [coverage] Node C.3 at layer 'capabilities' has no children …
#   - [target_stale_planned] Node R.7: target.status is 'planned' …
```

Exit code is 0 if no issues, 1 otherwise. The validation row is persisted to the DB (queryable via `/reports` or MCP `get_validation`); each node's `verdict_status` column is updated to the resolved status (after propagation), so `/reports/flips` reflects the latest state.

You can also trigger validation via the JSON API:

```bash
curl -X POST http://127.0.0.1:7779/api/v1/projects/my-project/validations \
  -H "Content-Type: application/json" \
  -d '{"actor":"human:me","with_verdicts":true}'
```

## LLM judge

`verdict_mechanism = "llm_judge"` on a node tells manifold to ask an LLM whether the node satisfies its parent. Manifold doesn't talk to an LLM directly — it shells out to a command you configure, passing the structured prompt on stdin and parsing `satisfied` or `violated` from the first line of stdout.

Configure via env var:

```bash
export MANIFOLD_JUDGE_CMD='claude --print'   # or any other LLM CLI
manifold validate my-project --with-verdicts
```

Or per-project via `spec_config.judge_command` (set when registering the project). The env var takes precedence.

The judge command receives a prompt like:

```
You are judging whether a specification node satisfies its parent contract.

PARENT (the contract being satisfied):
  title: …
  body:
    …

CHILD (the claim under review):
  title: …
  layer: …
  body:
    …

Reply with EXACTLY one of `satisfied` or `violated` on the FIRST LINE,
then a short paragraph of rationale on subsequent lines.
```

If the command isn't set, exits non-zero, times out, or returns unparseable output, the verdict becomes `judge_required` with the failure reason as evidence. Verdicts are still cached: the hash includes the judge command's hash, so switching judges re-evaluates.

## Working with `next-leaves`

`next-leaves` returns the frontier of unfinished work: leaf nodes (no children) whose `target_status` is `planned`, `in_progress`, or unset. This is manifold's answer to "what should we work on next?"

```bash
# All leaf nodes across the project
manifold next-leaves my-project

# Leaf nodes in a specific layer only
manifold next-leaves my-project --layer realizations
```

Example output:

```
NODE           LAYER            TARGET         VERDICT        MECH                 TITLE
------------------------------------------------------------------------
R.3            realizations     planned        unknown        automated_check      CLI operator commands
R.7            realizations     planned        (unset)        human_signoff        Export round-trip
R.12           realizations     in_progress    satisfied      python_assertion     Schema v2 migration
```

The output is sorted by layer order (as declared in `spec.yaml`) and then by node ID within each layer. Use `--layer` to narrow when a project has many layers and you're only interested in one.

The same data is available via the JSON API and MCP:

```bash
# JSON API
curl http://127.0.0.1:7779/api/v1/projects/my-project/next-leaves
curl http://127.0.0.1:7779/api/v1/projects/my-project/next-leaves?layer=realizations
```

Via MCP, an agent can call `next_leaves` with `project_id` (required) and `layer` (optional) to get the same list as a JSON array.

**Cross-project blockers (Topic I):** if `product-app/R.12` has a `blocks` cross-edge to `ai-platform/C.4` and `C.4` is not `achieved`, `R.12` is excluded from `next_leaves(product-app)`. Check blockers with MCP `list_cross_blocking_chain`. See [Portfolio and cross-project links](#portfolio-and-cross-project-links) below.

The orchestrator decides what to do with this list. Manifold's job is to surface it; the orchestrator's job is to pick from it, assign it, or defer it. Pre-dispatch checklist: [`docs/manifold/orchestrator-contract.md`](../../../docs/manifold/orchestrator-contract.md).

---

## Tracking rationale

Every node can carry two prose fields:

- **`rationale`** — why does this node exist? What problem does it solve? Why was it included?
- **`alternatives_considered`** — what was looked at and rejected, and why?

These are optional but encouraged. The validator emits an advisory (non-failing) warning for non-constraint nodes that lack rationale.

To author these fields, use the MCP from an agent. The agent reads the current node, then calls `update_node` with **`change_reason` required**:

```
# Example agent prompt
Update node C.3 in project my-project. change_reason=clarification.
Set rationale to "This capability exists because...".
Set alternatives_considered to "We considered X but rejected it because...".
```

Or use the web UI: the node edit page (`/projects/<p>/nodes/<n>/edit`) exposes these fields in the structural panel alongside title, layer, and verdict.

To author via the JSON API:

```bash
curl -X PATCH http://127.0.0.1:7779/api/v1/projects/my-project/nodes/C.3 \
  -H "If-Match: 42" \
  -H "Content-Type: application/json" \
  -d '{"fields": {"rationale": "...", "alternatives_considered": "..."}, "change_reason": "clarification", "actor": "human:me"}'
```

On the node detail page, rationale and alternatives appear in a collapsible "Rationale" section above the node body.

---

## Spec audit (M3 revision discipline)

`spec-audit` answers: **are spec revisions properly explained?** It does **not** compare code to the spec — that is **`drift-report`** (M4).

```bash
manifold spec-audit my-project --since 2026-01-01
manifold spec-audit my-project --since 2026-01-01 --include-other
```

Example output:

```
Spec Audit — my-project
  since: 2026-01-01
  flagged revisions: 2
  unclarified rationale changes: 1

  [2026-03-14T09:22:11Z] R.7: reason=pivot
    scope pivot on realization node
  [2026-04-02T14:05:30Z] C.3: reason=(unset)
    body changed on legacy revision
```

What each `change_reason` means:

| `change_reason` | What it signals | Action |
|---|---|---|
| `pivot` | Author flagged a deliberate intent shift on the spec | Review whether the change was correct; update related nodes |
| `other` | Escape hatch; justification should be in `note` or body | Check the justification; reclassify if possible |
| `(unset)` | Old revision, or a write that didn't set the field | Review manually; **all new `update_node` calls must set `change_reason`** |
| `clarification` / `correction` | Wording fix or prior error | Usually fine; rationale-only edits should use these |
| `evolution` / `refactor` | World caught up or structural reshuffle | Usually fine if summary matches |

Section 2 flags nodes whose **`rationale`** changed without `clarification` or `correction` — meaning may have shifted without saying so.

Surfaces: HTTP `/projects/<p>/spec-audit`, JSON `/api/v1/projects/<p>/spec-audit`, MCP `spec_audit` (keys: `flagged_revisions`, `unclarified_rationale_changes`).

What to look for:

1. **High `pivot` count:** The spec is revising intent frequently — update root layer or accept a deliberate direction change.
2. **Many `(unset)` revisions:** Legacy data or bypassed writes. Going forward, agents **must** pass `change_reason` on every `update_node`.
3. **Unclarified rationale changes:** Quiet meaning shifts — read before/after and reclassify if needed.

Proper nouns: [`docs/manifold/glossary.md`](../../docs/manifold/glossary.md).

---

## Drift report (M4 spec↔code)

`drift-report` answers: **does code still match the spec on realization nodes?** It runs verdict checks (without persisting a validation row) and surfaces **violated** and **unverified** findings. Default scope is the bottom layer in `spec_config.layers`.

```bash
manifold drift-report my-project
manifold drift-report my-project --format md
manifold drift-report my-project --force
manifold drift-report my-project --repo /path/to/checkout
```

- **`--format md`** — markdown report (for pasting into notes or PRs).
- **`--force`** — re-run verdict checks even when `evidence_hash` is unchanged.
- **`--repo`** — override `project_root` from `spec_config` (where checks execute).

Example terminal output:

```
Drift Report — my-project
  layer: realization
  project_root: /Users/me/code/my-project
  violated: 1  unverified: 2  satisfied: 5

  [violated] R.12  automated_check
    auth middleware missing rate limit
  [unverified] R.15  (no verdict_mechanism)
    logging spec not wired to a check
```

CLI exits **1** when any node is violated; exits **0** when only unverified/satisfied.

Surfaces: HTTP `/projects/<p>/drift-report`, JSON `/api/v1/projects/<p>/drift-report`, MCP `drift_report` (keys: `violated`, `unverified`, `summary`).

v2 (`--with-llm` rationale match) is deferred (L17).

---

## Portfolio and cross-project links (Topics H + I)

Mid-size orgs run **multiple team projects** in one `$MANIFOLD_DB` plus a reserved **`portfolio`** project for company **themes**. See also [`business-model.md`](business-model.md).

### Example A — Portfolio visibility

Register the portfolio project and a theme node:

```bash
# Via MCP register_project: project_id=portfolio, layers=[{name: theme}]
# Then create_node T.1 in portfolio / layer theme — "Q3 Reliability"
```

Link team nodes the theme **tracks** (association, not a graph edge):

```json
// MCP link_portfolio
{"theme_node_id": "T.1", "project_id": "product-app", "node_id": "I.2", "actor": "human:me"}
```

Roll up status:

```bash
manifold portfolio-report
manifold portfolio-report --theme T.1 --format md
manifold render portfolio --template quarter-roadmap
```

```bash
curl http://127.0.0.1:7779/api/v1/reports/portfolio
curl 'http://127.0.0.1:7779/api/v1/reports/portfolio?theme=T.1'
```

MCP: `portfolio_report`, `list_portfolio_links`, `link_portfolio`, `unlink_portfolio`.

**Not this:** `list_targets` — flat status filter, not grouped by theme.

### Example B — Cross-project blocking

Product leaf blocked on AI platform work:

```json
// MCP create_cross_edge — src blocked until dst achieved
{
  "src_project_id": "product-app",
  "src_node_id": "R.12",
  "dst_project_id": "ai-platform",
  "dst_node_id": "C.4",
  "edge_kind": "blocks",
  "actor": "agent:dispatch-1"
}
```

Effects:

- `next_leaves(product-app)` excludes `R.12` until `C.4` is `target_status=achieved`
- `list_cross_blocking_chain(product-app, R.12)` → `[{"node_ref": "ai-platform/C.4", ...}]`
- `portfolio-report` includes **`blocked_by`**: `["ai-platform/C.4"]` on linked rows

MCP read: `list_cross_edges`, `list_cross_blocking_chain`. MCP write: `create_cross_edge`, `delete_cross_edge`. No CLI `cross-edges` in v1 — use MCP.

**node_ref** format: always `project_id/node_id` (e.g. `ai-platform/C.4`) — bare node ids are rejected.

Proper nouns: [`docs/manifold/glossary.md`](../../../docs/manifold/glossary.md) (Portfolio + Cross-project sections).

---

## What manifold does NOT do (yet)

- **Multi-human sharing with distinct permissions** — manifold has no auth. For single-operator multi-machine use, a private network overlay (Tailscale / SSH tunnel) handles network access without auth. An auth layer would only be added if multiple humans needed different permissions on the same instance.
- **OR-refinement and obstacle analysis** — deferred to v0.2. The current structure is AND-refinement only (all children must satisfy for the parent to satisfy). OR-refinement (any one child suffices) is on the roadmap.
- **JSON-typed structural fields in UI** — `contract:` and `applies_to:` are JSON columns. The web UI edits the simpler scalar/list fields. JSON fields still go through MCP / JSON-API PATCH for safety.
- **Tablet UX** — CodeMirror 5 works in modern browsers but isn't optimized for touch. Phone is out of scope.

---

## Next steps

- Read [`ARCHITECTURE.md`](ARCHITECTURE.md) if you want to know how the DB schema looks, where the code lives, or how to extend the tool surface.
- File issues / requests at the agent-skills repo.
