# Verdicts and drift-report

How realization nodes get wired to checks, and how `drift-report` classifies results. For the weekly cadence, see [`rituals.md`](rituals.md). For CLI/MCP setup, see [`user-guide.md`](user-guide.md) § Drift report. For schema and runners, see [`architecture.md`](architecture.md) § Verdict runners.

---

## Four mechanisms

| Mechanism | Field | How it runs |
|---|---|---|
| **`automated_check`** | `verdict_check` | Shell command in `project_root`; exit 0 → satisfied |
| **`python_assertion`** | `verdict_assertion` | AST-walked boolean expression with whitelisted helpers (`file_exists`, `file_contains`, `ast_has_call`, …) |
| **`human_signoff`** | `verdict_status` | Trusts the stored human status; no recomputation |
| **`llm_judge`** | `verdict_judge_prompt` | Shells out to a **persistent** judge command (`$MANIFOLD_JUDGE_CMD` or `spec_config.judge_command`); see § LLM judge below |

`drift-report` runs these via `validate.run_verdicts` without persisting a validation row.

---

## Attach checks via `update_node` / MCP

Verdict fields are ordinary node columns. Set them with `update_node` (CLI `edit` or MCP).

**MCP example:**

```json
{
  "project_id": "manifold",
  "node_id": "R.example",
  "expected_revision_id": 12,
  "actor": "agent",
  "change_reason": "evolution",
  "fields": {
    "verdict_mechanism": "python_assertion",
    "verdict_assertion": "file_exists('packages/manifold/manifold/cli.py')"
  }
}
```

For `automated_check`, set `verdict_mechanism` + `verdict_check` (shell one-liner). For `human_signoff`, set `verdict_mechanism` + `verdict_status` (`satisfied` / `violated`). Peek `expected_revision_id` first (`peek_node`).

After wiring, run `run_validation` (or `drift-report --force`) to populate evidence.

---

## `project_root` vs `--repo`

Checks execute with `cwd = project_root`. Resolution order:

1. CLI `--repo` or MCP `project_root` argument (per-invocation override)
2. `spec_config.project_root` on the project row (persistent default)

If neither is set, drift-report warns and automated checks may not reflect the deployed codebase. **Always pass `--repo` or set `project_root` in `spec_config`** before trusting violated/satisfied counts.

```bash
packages/manifold/scripts/manifold drift-report manifold --repo /path/to/ai-foundry
```

---

## Drift-report buckets

| Bucket | Meaning |
|---|---|
| **violated** | Mechanism ran; spec↔code mismatch, or `judge_required` (includes missing/broken LLM judge — see § LLM judge) |
| **errored** | Mechanism wired but check failed to execute (bad path, timeout, subprocess error) — **not** a spec violation |
| **unverified** | No `verdict_mechanism` on the node (`source=no_mechanism`) |
| **satisfied** | Mechanism ran; check passed |

CLI **exit 1** only when `summary.violated > 0`. Errored and unverified exit 0 — interpret the report, don't rely on exit code alone.

MCP `drift_report` returns the same keys: `violated`, `errored`, `unverified`, `satisfied`, `summary`.

---

## Verdicts vs target_status (independent axes)

`drift-report` scores **verdict checks** on realization nodes — it does not read `target_status`. **`transition_target`** (writeback) moves **`next-leaves`**, not drift buckets. A node can be `achieved` while its verdict is still violated, or vice versa. Run both surfaces after implementation work: writeback for the frontier, drift-report for code↔spec truth.

### next-leaves verdict columns

| Column | Source | When shown |
|---|---|---|
| **STORED** | `nodes.verdict_status` (human_signoff or last `run_validation` persist) | Always (CLI + MCP leaf dict as `verdict_status`) |
| **COMPUTED** | Ephemeral `run_verdicts` (same engine as drift-report; not persisted) | CLI when `--repo` set; MCP when `project_root` set (`computed_verdict_status` on each leaf) |

After `drift-report`, use `next-leaves --repo <checkout>` to see computed buckets on the frontier without persisting. Default output without `--repo` shows stored status only — `(none)` is normal when checks were never persisted.

---

## Writing checks that don't lie

Cross-tech dogfood (2026-06-07) surfaced three recurring failure modes:

### 1. Grep must anchor to code constructs, not keywords

Bad: `grep -q 'logging\|json'` — matches comments (`// logging deferred`) and yields false **satisfied**.

Good: anchor to real constructs the spec claims exist:

```bash
grep -qE 'def health|app\.get\("/health"' src/app.py
grep -q 'appendFileSync.*stdout' server.js
```

If the check can match a comment or string literal alone, it is worse than unverified.

### 2. curl checks measure process liveness, not code existence

`curl -sf http://127.0.0.1:8000/health` passes only when a server is running. Connection refused → **violated** or **errored**, not "code missing."

Documented ceremony when liveness is intentional:

```bash
# start server in background, run drift, then stop
uvicorn app.main:app --port 8000 &
PID=$!
sleep 1
manifold drift-report myproj --repo . --force
kill $PID
```

Prefer grep/`python_assertion` for "code exists" claims; reserve curl for behavioral/integration claims.

### 3. Drift-report is branch-unaware

Checks run against the **current working tree**. On repos with competing plan branches, record which branch the run reflects (note in commit message or report). Drift-report will not evaluate "branch X" — only what is checked out.

---

## Layer scope: default vs `--all-layers`

**Default:** drift-report scans only the **bottom layer** in `spec_config` (usually `realizations`).

**Upper layers are invisible** unless you pass `--all-layers` (CLI) or `all_layers: true` (MCP).

| Wired on | Visible in default drift-report? |
|---|---|
| `R.*` realization + `automated_check` | Yes |
| `C.*` capability + `human_signoff` | **No** — use `--all-layers` |
| `I.*` intent + `llm_judge` | **No** — use `--all-layers` |

```bash
packages/manifold/scripts/manifold drift-report obs-fastapi \
  --repo /path/to/checkout --all-layers
```

Cross-tech dogfood round 2 (2026-06-07): `human_signoff` on C.1 only appeared after `--all-layers`.

---

## LLM judge (`llm_judge`)

**What it is:** drift-report pipes a structured prompt (parent + child node text) to a **shell command you configure**. The command prints `satisfied` or `violated` on the first line; the rest is evidence.

**Not magic** — manifold does not call an LLM itself. You supply the binary/script via:

1. **`MANIFOLD_JUDGE_CMD`** environment variable (session/CI), or
2. **`spec_config.judge_command`** on the project row (persistent)

The command must exist on every drift run. A one-shot temp script that is deleted afterward will fail on the next report.

**Minimal stub (for testing only):**

```bash
export MANIFOLD_JUDGE_CMD='/path/to/judge.sh'
# judge.sh: read prompt from stdin; first line of stdout must be satisfied or violated
```

**Wire a node:**

```json
{
  "verdict_mechanism": "llm_judge",
  "verdict_judge_prompt": "Optional extra criteria appended to the prompt."
}
```

**Failure buckets:** missing command, non-zero exit, or unparseable output → internal status `judge_required` → drift-report bucket **`violated`** (not **`errored`**). Fix the judge setup before treating the node as a spec violation.

**When to use:** intent or capability nodes where automated grep/curl is awkward and a human has not signed off. Realizations usually prefer `automated_check` or `python_assertion`.

---

## When unverified is OK vs not

**OK:**

- Intent or capability nodes — not in drift-report's default bottom layer
- Realization nodes you have not wired yet (bootstrap in progress)
- Nodes you deliberately leave human-only until a check exists

**Not OK (for a trustworthy compass):**

- Bottom-layer realization nodes you treat as "done" or dispatch against — wire a mechanism or accept explicit human_signoff
- Weekly ritual showing many unverified realizations on a project you claim is drift-gated
- Using exit code 0 as "all clear" when errored or unverified counts are high

Fix errored first (broken `project_root`, bad command), then wire unverified realizations, then address violated.

---

## Dogfood: `ai-foundry` project

Foundry dogfoods on `project_id = ai-foundry` in **`~/.claude/foundry.db`** (set via `manifold init-ideas` or `MANIFOLD_DB`).

Reset and seed:

```bash
packages/manifold/scripts/manifold init-ideas          # all ideas; foundry.db + config
packages/manifold/scripts/manifold --idea foundry init-foundry   # reset foundry DB only
python3 packages/manifold/scripts/bootstrap_dogfood_verdicts.py --db ~/.claude/foundry.db
```

Re-run bootstrap after adding realization nodes. Then:

```bash
packages/manifold/scripts/manifold drift-report ai-foundry \
  --repo /path/to/ai-foundry
```
