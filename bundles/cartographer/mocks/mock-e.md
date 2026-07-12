# Mock E — the orchestration monster (real session, mined at schema v2)

**Surface:** claude-code · **Date:** 2026-07-05 → 06 (13:08–03:41, ~14.5h) · **Nodes:** 24 · **Lines:** 4 · **Beats:** 4 · **Artifacts:** 14 · **Intent:** v4 · **Frontier:** n24 (session at rest) · **Source:** `ea9003bf-f93a-4425-93cc-1ec3437b07f3.jsonl` (the "skills" session), captured at line 1984 — the session had ended.

This is the crucible-buildout session: a skills triage that became the design, build, benchmark, dogfood-by-recursion, and marketplace install of a whole review system. Chosen as the **many-parallel-streams** counterpoint to mock-d2: where d2 had one fan-out and one loop-back, this session has two two-track forks, one eleven-dispatch burst, ~72-agent and ~108-agent background workflows, a compaction seam, and a rule (no commits) that lives for twelve hours and dies on-map.

## Structure summary

```
TRIAGE — "Which of these skills deserve to live?"
  n01──n02──n03──n04━━━━━━━▶ n07 ── answered, line ends
                 │ fan ×2    ▲▲                │ succession
                 ├─⟨worktree⟩ n05 ─┘│          ▼
                 └─⟨research⟩ n06 ──┘   FORGE — "What should hats + red-vs-blue become?"
                                        n08──n09──n10━━━━━▶ n13 ── answered
                                                  │ fan ×2  ▲▲       │ succession
                                                  ├─⟨research⟩ n11 ─┘│
                                                  └─⟨build⟩    n12 ──┘
  PROVE — "Does crucible actually work?"                             ▼
  n14──n15──n16──n17(v1 ▸ v2)──n18──n19 ── answered ──────────────────
              ▲                      │
              └── n19's panel catches n17@1's rigged eval; honest re-run bumps n17 → v2
                                     │ succession (across the /compact seam)
  SHIP — "Get the real thing installed"
  n20──n21──n22──n23──n24 ◇open
```

- **Two clean two-segment fan-outs** (TRIAGE: worktree fixer ∥ deep-research; FORGE: contract research ∥ phase-1+2 build), both landing in a single integration node.
- **An in-line loop-back without a line**: n19 (the dogfood panel + fixes) supersedes n17@1's distinctness verdict, bumping n17 to v2. Unlike mock-d2's RESCUE, the correcting work is *downstream on the same line* — the schema carries it as history + `superseded_because`, not as an `into:` edge.
- **The no-commits arc**: n03 (`standing: expired`, `superseded_by: n22@1`) is set in TRIAGE at 13:54 and retired in SHIP at ~03:19 — the longest-lived rule in any mock, dying three lines away from where it was born.
- **A compaction seam between PROVE and SHIP** (`compaction_events[0]`, /compact at line 1528) — the first mock to have a non-empty `compaction_events`, and the seam coincides with a line boundary.
- **Session at rest**: unlike mock-d2 (captured mid-edit), this session ended. `frontier` points at the open question the session *chose* to leave (n24: does the hook matcher fire live?).

## What was folded

- **The eleven-dispatch burst → one node (n16).** Between 22:23 and 22:38 the mainline dispatched: 1 Explore, 5 crucible-typed agents (which failed to register), 5 general-purpose re-dispatches, 2 in-thread probes, the corpus builder, and the adjudicator. n16 carries the seven conformance probes; the corpus/packaging/benchmark machinery is n17. A full-fidelity render would need ~9 segments here; the fold is flagged in n16/n17 provenance spans.
- **Workstream bookkeeping** (todo tracking, README/manifest reconciliation, memory updates) folded into n16/n17 summaries.
- **Dead ends → residuals**: the typed-agent registry failure (n16), the 11ms benchmark args crash (n17), the XSS interrupt (n19), the voice-garbled marketplace name (n23). The `Math.random` crash bug caught in the fix-executor's output is in n19's summary (it's part of the fix story, not a detour).
- **The ~5h gap** (research landed 14:05; Pi returned 18:57) is a beat-1 note and prose in n07 — same treatment as mock-d2's gap.

## Sanitization + fabrication notes

**Sanitization holds** (grep-verified at build time): no hostnames, IPs, SSH usernames, employer identifiers, or work email anywhere in mock-e.json/md. Two near-misses handled: Pi's L117 message contains voice-garble that appears to be mangled machine references — that line is not quoted; and the garbled marketplace name in Pi's L1798 install ask is not reproduced anywhere in the mock (n23's residual describes the garble without the token, and n22's quote is the option label instead). The session itself is entirely personal-project material.

**Verbatim inventory:** 10 quotes, all byte-exact substrings of the cited transcript lines (programmatically verified). Nine are Pi's transcribed voice/typing including artifacts ("What do we need ot do", "evaluate four dry", "excecute"). **n22's quote is an option label** ("I commit + push, then verify") from an AskUserQuestion gate — flagged in the node, see friction #2.

**Inferred/editorialized (flagged):** intent wording (all four versions — shifts anchored at n02/n09/n15, all decision nodes per mock-d2's rule); line labels and outcomes; beat titles; moment classes; `settled` sentences on n17/n19; all node titles/summaries are reducer prose written against the transcript. Node ordering inside TRIAGE places n03 (the 13:54 no-commits rule) before n04 (the 13:33 dispatch) — a deliberate ~20-minute reorder so the rule reads as ground-rule rather than interruption; flagged here.

## Where schema v2 fought this session (friction)

1. **In-line supersession has no edge.** n19's work bumps n17 to v2 — same mechanism as mock-d2's loop-back merge, but *within* one line, so there is no `into:` to draw. A render can only discover the n19→n17 causal arrow by reading `history[].superseded_because` prose. If cross-node supersession is common, nodes may need a `supersedes: node@version` field mirroring `superseded_by`.
2. **Option-label quotes are a third verbatim class.** Mock-d2 found UI-gate approvals with *no* user text; this session's biggest ruling (push authorization) has user text that is a *chosen menu option*, plus AskUserQuestion answers elsewhere that are typed free prose. The verbatim rule now has three classes: user prose, assistant articulation (mock-d2's fallback), and selected-option labels. The `quote.note` field carries the flag, but the schema has no structured `quote.kind`.
3. **Fan-out heterogeneity breaks segments.** Segments worked for TRIAGE/FORGE (2 homogeneous strands each) but not for PROVE's burst: 7 probes + corpus + packaging + 2 background workflows differ in carrier, lifespan, and landing node. Folding was the only honest option under a node budget. Segment schema assumes "N similar probes, one landing" — real orchestration bursts aren't shaped like that.
4. **Background workflows ≠ subagents.** The deep-research harness (108 agents) and the benchmark (~72 agents) are single dispatches that internally fan out enormously. The map renders them as one segment/one node — the session's true concurrency (100+ agents) is invisible, and nothing in the schema says "this station is itself a swarm". A `carrier` field exists on segments only, and is free text.
5. **A dead session still needs a frontier.** `session.frontier` is required by the prototype, but this session ended. Pointing frontier at the deliberately-open n24 works, yet semantically "you are here" and "we chose to stop here" are different things — the schema conflates them.
6. **The compaction seam coincides with a line boundary — conveniently.** SHIP starts from the compacted summary, so `after_node: n19` is clean. A /compact mid-line would raise the question mock-d2 never faced: does provenance before the seam still count as *this* line's memory? Untested by this mock (and worth a deliberate test case).
7. **Cross-session interference is invisible from inside.** This session's uncommitted work was discovered and carved around by the *other* live session (mock-f's n05). From this transcript, nothing happened — the schema has no way to represent "another session touched my working tree", even though the sibling mock documents it. Session maps may eventually need cross-map references; the two mocks cross-reference only in prose.
8. **Intent version count is taste.** Four versions already; the L1798 install ask could arguably be v5 ("verify the *installed* thing", distinct from "ship it"). Chose to keep install inside v4 — a reducer needs a rule for when a shift is a new version vs. an elaboration.
