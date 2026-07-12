# Mock D — transit lines that merge and diverge (real session)

**Surface:** claude-code · **Date:** 2026-07-05 · **Nodes:** 19 (3 topics, 11 moves, 4 decisions, 1 open question) · **Lines:** 5 · **Source:** a real transcript, `ae18157a-…jsonl` in the foundry project's session directory, captured at line 718 (the session was still running; the JSONL is append-only, so all spans below stay valid).

Pi's ask, near-verbatim: *"I would like to see a mock conversation where there is a bunch of transit lines merging and diverging, that perhaps is taken from a real world example or chat I've had in the past."* This is that mock. Unlike Mocks A–C, **nothing structural here is invented** — the forks, merges, quotes, and line spans are extracted from an actual session earlier the same day.

## The situation

The 2026-07-05 "meditate" session: a full review of the meditate plugin, run in three phases across ~6 hours (with a ~5-hour gap in the middle).

1. **The review fans out.** Pi asks for a full review at three levels — design/architecture, implementation quality, and a literature check against the memory-curation field. Three background agents are dispatched in parallel; the mainline keeps working while they run (scope notes, firsthand findings, an insurance wakeup). All three reports land and are **merged into one SYNTHESIS.md** with a combined verdict: conceptually ahead of the field, currently unable to run on this machine.
2. **A finding forks a new line.** The synthesis's scariest critical — the plugin's spec docs exist *only* on the old laptop that originally ran meditate — becomes its own workstream: reach the old filesystem (stale mount, SSH detour), vendor the authority docs into `plugins/meditate/docs/`, write the README around them. That line's output **merges back into the synthesis, updating it in place** (v1 → v2): the lost-spec critical is resolved.
3. **The merged state feeds a plan, and the plan executes.** Pi returns hours later and asks for "a plan for the natural next moves." The recovered docs — absent when the review agents ran — are re-read for the contract (itself a small fork/merge in the source, folded here; see n14's residual), three calls get locked, the plan is approved, and execution proceeds through workstreams C, A+B, and D5. At capture, A+B is active and workstream E plus verification are open.

## The line topology

Five lines. `M` is the mainline; `D`/`I`/`L` are the three review agents; `R` is the doc-recovery workstream.

```
M  n01─n02─n03━━━━━━━━━━━━━━━━━━━▶n07━━━━━━━━━━━━━▶n12─n13─n14─n15─n16─n17─n18─n19
            │  FORK-1 (×3)        ▲▲▲   ▲
            ├──▶ D: n04 ──────────┘││   │
            ├──▶ I: n05 ───────────┘│   │ MERGE-2 (updates n07 → v2)
            └──▶ L: n06 ────────────┘   │
               MERGE-1 (SYNTHESIS.md)   │
                                        │
            n07@v1 ──FORK-2──▶ R: n09─n10─n11 ──┘
            (lost-spec critical spawns the recovery line,
             which loops back into the node it forked from)
```

- **FORK-1** (at `n03`, source lines 81–85): one dispatch node spawns three independent lines. The mainline continues in parallel — a fork is not a handoff.
- **MERGE-1** (at `n07`, lines 135–193): all three lines' reports are consumed by a single synthesis node. The agent lines terminate; only `M` continues.
- **FORK-2** (at `n07`, line 196): a *finding* inside the merged node spawns line `R`. This fork is user-initiated and motivated by the merge's own output.
- **MERGE-2** (back into `n07`, lines 298–309): line `R`'s output does not create a new node — it **updates the node it forked from**, bumping `n07` to v2 with a history entry. Fork-source and merge-target are the same node.

A third fork/merge pair exists in the source (two parallel Explore agents mining the recovered contract docs, lines 344/346 → 390) and is deliberately **folded into line M** as `n14` to keep the mock at five lines; the fold is flagged in `n14`'s residual.

## What a correct render must show

The merge/diverge moments are the load-bearing elements of this mock:

- **FORK-1 at `n03`** must read as one point splitting into three lines (`n04`, `n05`, `n06`) *while `M` itself continues* — a render that shows the mainline pausing at the fork misrepresents the session (the scope notes and the insurance wakeup happened during the fan-out).
- **MERGE-1 at `n07`** must show three lines terminating into a single node. The spine consequence: `n04`–`n06` are *inputs* to `n07`, not steps before it on the same line. A render that lays the three reviews inline on `M` in landing order fails this mock.
- **FORK-2 → MERGE-2 as a loop**: line `R` departs from `n07` and returns to `n07`. The render must show both that the recovery line exists *because of* a finding in the synthesis, and that its landing is an **in-place update** (`n07` v1 → v2, with history reachable) rather than a new downstream node. This is the single hardest moment in the mock and the reason the schema extension exists.
- **The spine still reads clean top-to-bottom per line.** Line `M` alone must tell the story: review → dispatch → synthesis → plan → locked calls → execution → open work. Lines `D`/`I`/`L` are one-node lines; `R` is a three-node line under its own topic (`n08`).
- **Verbatim vs inferred**: four quotes (`n02`, `n09`, `n13`, `n15`), three of them Pi's actual words in his actual voice-transcribed register (including the "uh"s), one flagged as an assistant articulation (see fabrication notes). Quoted text must render distinct from reducer prose.
- **Updated-in-place nodes**: `n07@v2` and `n14@v2`, each with a real `superseded_because`. `n07`'s v2 was caused by a *different line's* work — same cross-topic-revision property Mock A stressed, now with the causing line visible on the map.
- **Residuals folded**: the stale insurance wakeup (`n07`), the stale-mount false start (`n10`), the uv stdout-purity check (`n16`), and the folded fork (`n14`). The wakeup residual is this mock's false-alarm: a scheduled check-in that fired hours behind reality and was correctly discarded.
- **Mixed statuses at rest**: `done` (most), `active` (`n12`, `n17` — session live at capture), `open` (`n19`, which must stay loud).
- **Lines are orthogonal to the parent tree**: line `M` traverses two topics (`n01` and `n12`); topic `n08` belongs entirely to line `R`. A render must not conflate line membership with tree grouping — they answer different questions ("which workstream carried this" vs "what is this part of").

## Schema extension (provisional — Phase 3 input)

Two additions on top of the README schema, kept minimal:

1. A top-level **`lines` array**: `{ id, label, forks_from: { line, node } | null, merges_into: { line, node } | null }`. A line with `forks_from: null` is a root line.
2. A **`line` field on every node** naming the line that carries it.

The node `parent` tree is unchanged; lines are a transit topology laid *over* the tree. Nothing else in the README schema moved.

**The real schema finding:** merges make the map a **DAG**, which the current parent-tree schema cannot express — `n07` has one `parent` but four incoming lines (M, D, I, L) and one returning line (R). This mock encodes the DAG edges in `lines[]` and leaves `parent` as pure grouping, but that is a workaround, not a design: MERGE-2 in particular (a line whose output lands as a *version bump on its own fork point*) shows that merge edges may target `node@version`, not just nodes. Phase 3 must decide whether merge/fork edges live on lines (as here), on nodes, or as first-class edge objects.

Limitations found while building (honest, for Phase 3):

- **`forks_from`/`merges_into` as single fields force one fork and one merge per line.** Fine here; a line that merges, re-emerges, and merges again cannot be expressed. Probable fix: per-line edge lists.
- **Merge-as-update vs merge-as-new-node is invisible in the extension.** MERGE-2 targets `n07` and bumps it to v2; MERGE-1 targets `n07` at creation. The JSON cannot distinguish these; the history entry carries the truth by prose only.
- **Fork cause is prose, not structure.** FORK-2 exists because of a specific finding *inside* `n07`'s summary; there is no way to point at it short of an annotation. This connects directly to Phase 2's selectable-assumption mechanic.
- **One fork point spawning three lines** is representable but ambiguous in counting: is FORK-1 one fork event or three fork edges? The render probably cares (one visual split), the schema as written says three.

## Sanitization + fabrication notes

**Sanitized (real material excluded from the mock):**

- Source lines 226 and 310 name two personal machines, a corporate-prefixed hostname, a tailnet IP, and SSH usernames. All are excluded; the mock says "the old laptop" and the `n10` residual notes the exclusion. Provenance spans still point at those lines — a renderer following provenance into the raw transcript would see them, which is itself a real Phase-3 question (provenance reveals what summaries scrub).
- No work credentials, employer identifiers, or ticket systems appear anywhere in the source session; it is entirely personal-project (meditate/foundry) material.

**Fabricated / editorialized (everything else is extracted):**

- **Nothing structural.** All forks, merges, dispatch lines, landing lines, the stale wakeup, the stale mount, the 5-hour gap, the version bumps, and the open workstreams are real and at the cited line numbers.
- The three user quotes (`n02`, `n09`, `n13`) are byte-exact substrings of the source JSONL, verbatim rule honored with zero fabrication — including voice-transcription artifacts. Spans are real JSONL line numbers.
- **`n15`'s quote is the assistant's words, not Pi's** — the plan approval happened through the plan-mode UI gate, which leaves no user prose to quote. Flagged here and in the node summary. This is a genuine design problem, not a shortcut: *decisions ratified by UI click have no quotable user text.* The verbatim rule needs a defined fallback for gate-approved decisions.
- Node titles and summaries are reducer prose (as in all mocks), written against the actual transcript content; the folded third fork/merge (`n14`) is a deliberate simplification, flagged in its residual.
- `captured_at_line: 718` (19:37 UTC): the source session was still running when this mock was built. Statuses (`active`, `open`) are true as of that line and will drift from the real session — which is exactly what a live map would have to handle.
