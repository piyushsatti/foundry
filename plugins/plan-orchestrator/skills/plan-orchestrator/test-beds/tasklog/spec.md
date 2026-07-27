# Spec — `tasklog`

A minimal event-sourced task audit tool. Synthetic test-bed for plan-orchestrator round-3.

## What

A CLI tool that:

1. Accepts append-only **task-state-change events** written to a JSONL log file.
2. Routes each event to two **independent consumer processes**, each maintaining its own materialized view:
   - `stats` — per-user counts of `tasks_created`, `tasks_completed`, `tasks_assigned`
   - `timeline` — per-task ordered list of state changes
3. Supports **replay**: given the full event log, reproduces both materialized views from scratch (byte-identical to live-streamed result).
4. Supports **idempotency**: replaying the same log twice produces the same views as replaying once.
5. Supports **schema evolution**: at least one new event type can be added after Planning has started, without breaking earlier consumers' replay against logs that contain only the original types.

The system has one producer (the CLI that accepts events on stdin and appends to the log) and two consumers (the two view-maintainers). Producer and consumers run as separate processes. The event log on disk is the contract between them.

## Why

This is a synthetic test-bed for the `plan-orchestrator` skill, not a product. The goal is to exercise machinery added in iteration-3 (decisions 60–64) and identify failure modes for iteration-4.

Specifically, this spec is designed to stress:

- **Cascade convergence (decision 61)** — two consumers share one event-schema contract; if a planner refines an event type, the other consumer is restaled. Tests whether the N=3 bound holds.
- **Spec-version pinning (decision 62)** — the spec WILL be revised mid-run to add a new event type (deliberate test point). Tests whether the stale-spec sweep correctly invalidates and re-validates adjudications.
- **ORIENT context discipline (decision 60)** — multi-cycle run with parallel reviewers and many adjudications. Tests whether `orient-latest.md` redirect actually preserves architect context.
- **Atomic-write discipline (decision 63)** — implementer writes its own status.md repeatedly. Tests whether the `.tmp` + rename pattern lands.
- **Audit-N=3 user options (decision 64)** — if audits don't converge, the deliberate self-proxy at the gate tests whether the three-option spec is operable.

## Success metrics (desk-evaluable / scriptable)

1. **Replay determinism:** `python tasklog replay <log> --out views/` invoked twice produces byte-identical `views/stats.json` and `views/timeline.json`.
2. **Idempotency:** consuming a log of N events, then re-consuming the same log, yields the same views as consuming once.
3. **Schema evolution:** an event type added mid-development can be replayed against a log that mixes old and new event types; consumers don't crash on unknown types they don't subscribe to.
4. **Test coverage:** ≥1 pytest each for replay-determinism, idempotency, and schema-evolution.
5. **All Structural checks pass; ≥80% Alignment checks return YES; audits clean or accepted-advisory.**

## Scope — in

- 3 initial event types: `task_created`, `task_completed`, `task_assigned`
- Exactly 2 consumers: `stats` and `timeline`
- File-based JSONL event log (one log file at `events.jsonl`)
- File-based materialized views (`views/stats.json`, `views/timeline.json`)
- Python 3.11+, stdlib only (+pytest for tests)
- Single-writer producer (no concurrent writes to the log)
- Process-level isolation (each consumer is a separate `python -m` invocation)
- A `replay` command that derives views from scratch
- A `consume` command that processes new events incrementally
- Idempotency via per-consumer cursor (last-event-id processed, persisted)

## Non-goals (explicit)

- **No more than 2 consumers.** Don't propose adding a third.
- **No more than 4 total event types** (3 + 1 added mid-run). Don't propose more.
- **No real-time / streaming infrastructure.** No Kafka, Redis, sockets, websockets.
- **No authentication, multi-tenancy, RBAC.**
- **No web UI, no REST API, no GraphQL.**
- **No deployment / packaging / pip-installable.** Local files only.
- **No database** beyond JSONL + JSON view files.
- **No external dependencies** beyond stdlib + pytest.
- **No optimization, no profiling, no concurrency primitives.** Single-writer producer is enough.
- **No event-validation framework** (Pydantic, marshmallow, etc.) — plain dicts + a hand-written validator are enough.
- **No history-rewriting**, no compaction, no snapshots, no retention policy.
- **No CLI subcommand framework** (Click, Typer) — argparse from stdlib.
- **No logging framework** — print to stderr.

## Constraints

- Python 3.11 or later
- Standard library + `pytest` only
- Linux/macOS file semantics assumed (atomic rename via `os.replace`)
- Total expected source LOC: 200–400 across producer + 2 consumers + replay + tests

## Existing context

None. Greenfield. No prior code, no prior decisions to honor beyond this spec.

## Deliberate test points for the skill

These are not features of `tasklog`; they are observations the skill should make about itself while running:

- **TP-1 (cascade):** when one planner refines an event-type schema during Planning, does the other consumer-planner correctly restale and re-plan against the refined version? Does the cascade converge within N=3 iterations?
- **TP-2 (spec mutation):** mid-Planning, I (the architect) will revise this spec by adding a fourth event type (`task_unassigned`). Does ORIENT detect the spec mtime change? Are all spec-citing adjudications marked `stale-spec`? Are they re-validated before the next gate opens?
- **TP-3 (ORIENT context budget):** after ~10 cycles, has the architect's context filled with script output, or did `orient-latest.md` keep it lean?
- **TP-4 (atomic writes):** does the implementer's `status.md` ever appear partial to ORIENT? If not, is that because of the `.tmp`+rename discipline, or because writes are small enough that the harness's Write is effectively atomic regardless?
- **TP-5 (rubber-stamping at gates):** I'm self-proxying at gates. Am I rubber-stamping my own adjudications? Does the tier-1/2/3 presentation (decision 56 branch 4) help, or is it theater when there's no actual second person?
