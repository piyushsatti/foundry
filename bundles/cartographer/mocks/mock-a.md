# Mock A — the orchestrator chat

**Surface:** claude.ai · **Date:** 2026-07-04 · **Nodes:** 17 (3 topics, 8 moves, 4 decisions, 1 open question, 1 false-alarm)

## The situation

One claude.ai session in which Pi ran three workstreams across a single day, hopping between them as results came back:

1. **Transcript mining** — 21 days of session transcripts mined for recurring friction. Two extraction passes (Claude Code JSONL first, claude.ai exports later in the day), 19 raw patterns deduped to 12 themes, converted into an approved 7-item buildout with per-item spec files and a dependency-ordered build sequence.
2. **File consolidation** — six scattered note/scratch locations inventoried, everything ruled into the foundry monorepo (no new repo), batch 1 (143 files) moved via a paste-back script; batch 2 parked pending dedup review. Mid-inventory, a **false alarm**: old notes referenced a "session-lens repo" that couldn't be found anywhere. ~40 minutes of searching (GitHub, two machines, a backup-drive index) before the notes' own dates showed no code had ever existed — the "repo" was aspirational.
3. **Orchestration design** — named the failure mode (execution debris drowning orchestrator sessions), ruled the two-tier rule (orchestrator decides, workers execute), drafted the paste-ready mandate template, and parked the state-survival question as explicitly open.

The workstreams interleave in the chronology: mining opens the day, consolidation interrupts, the mining second pass returns mid-afternoon, orchestration design closes the evening — and the orchestration work retroactively **revises a mining decision** (the buildout sequence). A log-faithful renderer shows a braid; the map must show three clean spines.

## What a correct render must show

- **Three top-level topic nodes** (`n01`, `n07`, `n13`), each with its children grouped under it — regardless of the fact that their provenance spans interleave in transcript order. This is the core state-vs-log distinction this mock exists to demonstrate.
- **The spine reads clean top-to-bottom.** Titles + summaries alone must tell "what we did and how we approached it" with zero rework noise. If a reader encounters the double-counting bug, the 40-minute repo hunt, the rejected archive repo, or the original numeric build order **at rest**, the render fails.
- **The false alarm is ONE node** (`n10`, status `false-alarm`), whose spine reading is the *conclusion* ("notes only — no code ever existed, nothing lost"). The wrong turn — the GitHub/local/backup hunt — lives in its residual, reachable behind a click, never as sibling nodes or timeline entries.
- **Updated-in-place nodes are visually distinct from version-1 nodes.** `n03` (v2: second corpus pass changed the numbers) and `n04` (v2: build sequence re-derived) must signal "this node has history," and the history reveal must show the old summary *and* `superseded_because`. Note `n04`'s revision was caused by a *different topic's* work (the dependency pass in orchestration design) — the map should make that survivable, the log never could.
- **Decision nodes carry verbatim quotes** (`n04`, `n06`, `n11`, `n15`) and the render must visibly distinguish quoted text from inferred summary text — quotes are Pi's words, summaries are the reducer's.
- **Provenance affordance on every node**: some path from any node (and any residual) to its transcript line span. Topic nodes have *multiple disjoint spans* — the affordance must handle that, not assume one span per node.
- **Mixed statuses render legibly**: `done` (most), `active` (`n07` — batch 2 pending), `open` (`n17`), `false-alarm` (`n10`).

## Design demonstrables this mock stresses

| Demonstrable (from brief §Phase 1.3) | Where it bites here |
|---|---|
| Top-down readability | 17-node spine must scan in under a minute; three topics with 4–5 children each |
| Updated-in-place vs new node treatment | `n03`, `n04` (v2) sitting among fifteen v1 siblings |
| Node-history access | `n04`'s history entry shows a superseded *decision* — the highest-stakes history case |
| Click-to-expand residual detail | Three residuals of different species: a false-alarm detour (`n10`), a tooling bug (`n03`), a rejected alternative (`n11`) |
| Provenance affordance | Multi-span provenance on topics; residuals carry their own spans; overlapping spans (`n11` inside `n09`) |
| Quoted vs inferred distinction | Four quotes, chat-register lowercase, adjacent to reducer prose |
| (implicit) topic grouping vs chronology | Child provenance interleaves across topics: n03's second span [643–748] falls *between* consolidation and orchestration work |

Not stressed here (by design): compaction seams (Mock C), hypothesis/dead-end chains (Mock B). `compaction_events` is deliberately empty.

## Fabrication notes

Built from the real 2026-07-04 situation but all specifics are fabricated: line numbers, pattern/file counts, item names, quote wording, and the "session-lens" name are invented for the mock. Sanitized per the brief — no hostnames, IPs, credentials, or work identifiers; work-machine material is excluded in-fiction too (`n02`).
