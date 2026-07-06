# Topic E — `drift-report` design (M4 spec↔code)

**Status:** v1 locked (2026-06-06). Ready to implement.

**Related:** [`glossary.md`](../../manifold/glossary.md) (M4 nouns), [`todo.md`](../../manifold/todo.md) Topic E.

---

## Problem

**Question:** Does the code still match what the spec says we are building?

This is different from **`spec-audit`** (M3), which asks: did we change the spec without explaining why? Spec-audit never reads source code.

Today, manifold can check code **per node** when `verdict_mechanism` is configured (`validate --with-verdicts`). There is no single project-wide report that answers "where has spec↔code diverged?"

---

## Command (locked — L3, D3)

Standalone, symmetric with `spec-audit`:

| Surface | Name |
|---|---|
| CLI | `manifold drift-report <project> [options]` |
| MCP | `drift_report` |
| HTTP | `/projects/<p>/drift-report` |

No subcommand nesting (`manifold drift code`).

---

## v1 scope (locked — L16)

**Ship Option B:**

1. **Violated** — realization node has a verdict mechanism; check ran; status is `violated` (or `judge_required` where applicable).
2. **Unverified** — realization node has **no** verdict mechanism configured (`no_mechanism` / empty). Actionable coverage gap: "we cannot tell if code matches."
3. **Satisfied** — listed in summary counts; optional detail section (not the headline).

Focus layer: **realizations** (bottom spec layer by convention). Flag `--all-layers` optional for nodes with mechanisms outside realizations.

### Inputs

- Project ID (required)
- Repo root: `spec_config.project_root`, overridable via `--repo PATH`
- `--force` — bypass verdict cache (same semantics as `validate --with-verdicts --force`)
- `--since` — not in v1 (verdicts are point-in-time, not revision-scoped)

### Execution

1. Load project graph
2. Select realization-layer nodes (default)
3. Run `run_verdicts` (reuse `validate.py` — no duplicate check logic)
4. Classify each node: satisfied / violated / unverified / deferred_external / unknown
5. Emit report

### Output

**Terminal (default):** sections `VIOLATED`, `UNVERIFIED`, summary counts.

**Markdown (`--format md`):** PR-pasteable artifact. Each finding includes:
- `node_id`, title/body snippet, `rationale` excerpt
- verdict status + truncated evidence
- link hint: `manifold peek <project> <node_id>` (or node URL on web)

Exit code: non-zero if any **violated** (unverified alone does not fail — it's a gap, not a confirmed drift).

---

## v2 — next when opportunity allows (L17)

**Option C — LLM rationale match:**

- Optional `--with-llm` (or dedicated mechanism on nodes)
- Judge reads node `rationale` + repo context; answers "does implementation still match why?"
- Requires stable judge command config (same path as existing `llm_judge` mechanism)

Not v1. Document in roadmap; do not stub half-built flags in v1 CLI.

---

## Explicitly out of v1

| Item | Why deferred |
|---|---|
| Spec Kit / OpenSpec on-disk scan | External interop (Topic D pattern) |
| Finding → `change_reason=pivot` workflow | Needs finding records + accept/reject UX |
| `--since` date filter | Verdicts are not revision-scoped |
| New static analysis (symbol grep, AST) | Use verdict hooks; don't invent parallel check engine |
| Web UI dedicated view | CLI + MCP + HTTP JSON first; web can follow |

---

## Success criteria

After v1 ships:

- Positioning sentence *"produce a drift report when code diverges"* is **true** for projects that wire verdicts on realizations
- Users who run `drift-report` expecting code-level checks get code-level checks — not revision audit rows
- `spec-audit` vs `drift-report` split remains honest (glossary M3 vs M4)

---

## Implementation sketch

| Component | Work |
|---|---|
| `queries.py` | `drift_report_findings(conn, project_id, ...)` — select nodes, call verdict runner, return structured rows |
| `cli.py` | `drift-report` subcommand + `--format md` + `--repo` |
| `mcp_server.py` | `drift_report` tool |
| `web.py` | JSON API + optional HTML table (mirror spec-audit) |
| Tests | CLI smoke, query classification, markdown output |
| Docs | glossary surface row → shipped; why-manifold aspirational → factual |

---

## Changelog

| Date | Change |
|---|---|
| 2026-06-06 | v1 = Option B locked; v2 LLM rationale match deferred (L17) |
