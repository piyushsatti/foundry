# Mock G — a product planned entirely in conversation (real session, mined at schema v2)

**Surface:** claude-code · **Date:** 2026-07-05 (13:02–22:47, ~10h with a ~5h gap) · **Nodes:** 14 · **Lines:** 3 · **Beats:** 3 · **Artifacts:** 9 · **Intent:** v2 · **Frontier:** n14 (deliberately closed) · **Source:** `61722204-3b99-4bea-8955-cf965fb28351.jsonl` (the "hailey" session), captured at line 621 — the session had ended.

This is the Hailey product-planning session: concept diagram → stack + provisioning decisions → committed spec → a phase-1 implementation plan written and immediately parked → architecture doc → three personas walked through full weeks → one consolidated requirements doc → a clean, declared stop. Chosen as the **zero-orchestration** counterpoint to mock-d2 and mock-e: **not a single subagent dispatch in the whole transcript** — every fork on this map is conversational, and the session's biggest structural event is an *abandonment* (the parked plan), not a merge.

## Structure summary

```
SHAPE — "What is Hailey, and what would we build?"
  n01──n02──n03──n04──n05──n06 ── answered, line ends
                            ▲plan │
                     (parked by   │ succession (the pivot, L341)
                      the pivot)  ▼
                          DOSSIER — "Put the understanding on paper before any code"
                          n07──n08━━━━━━━━━━━━━━▶ n12──n13──n14 ── closed clean
                                 │ fork             ▲              (zero open)
                                 ▼                  │ merge (P1–P28 feed n12)
                          LIVED — "Where does Hailey earn its keep in a real week?"
                          n09──n10──n11 ────────────┘
```

- **All structure is conversational.** The LIVED fork is Pi proposing the persona method at L392; the merge is Pi asking for the consolidation at L494. Nothing ran in parallel — the fork/merge topology describes *threads of inquiry over time*, not concurrency. Same schema, opposite physics from mock-e.
- **The flagship moment is a parking, not a merge**: n06 writes a complete, committed 12-task implementation plan; n07 parks it in the next breath. The plan is `artifacts[a03] status: "parked"` — the map must show a finished artifact that nothing executes.
- **A session with zero open questions.** Pi closed it deliberately ("call it a day"); n14 is a decision, `openCount` renders 0. Contrast with d2 (captured mid-edit) and e/f (each leaves an open node) — this mock tests whether a *closed* map still reads as alive.
- **Voice-transcription register throughout**: 8 quotes, byte-exact, dense with "uh"/"um"/false starts ("I don't want to play... pay, like, ninety nine dollars a year", "HAiley").

## What was folded

- **The discovery-round Q&A → n03/n04 summaries.** The stack conversation ran ~90 minutes over many exchanges (TypeScript challenge, responsibilities-on-cloud, voice configurability); the map keeps the two rulings and folds the volley. One interruption (Pi cutting off an answer to sharpen his question) is n03's residual.
- **Skill loads and rendering mechanics** (brainstorming/writing-plans/API-doc skills, mermaid render-to-SVG detours) folded into node summaries — process, not story.
- **Per-persona beat detail** (18 + 13 beats, tier labels, counterfactual lines) lives in the artifacts; nodes carry counts and the method.

## Sanitization + fabrication notes

**Sanitization holds** (grep-verified at build time): no hostnames, IPs, SSH usernames, employer identifiers, or work email in mock-g.json/md. The source session is entirely personal-project material (a solo product idea); persona names (Avery, Priya, Marcus, an EA named Elena, partner David) are fictional characters authored *in* the session — kept, since they're the artifact's content, not real people. The one platform-fee dollar amount is Pi's own spoken words in a byte-exact quote.

**Verbatim inventory:** 8 quotes, all byte-exact substrings of the cited lines (programmatically verified), all Pi's prose — this is the only mock of the three with **no fallback quotes at all**: no assistant articulations, no option labels. Conversational sessions are quote-rich; the verbatim rule pays off best exactly where orchestration is absent.

**Inferred/editorialized (flagged):** intent wording (2 versions; the single shift anchored at decision n07); line labels/outcomes; beat titles; moment classes (contentious: n11 "pivot" — the Marcus stress test changed the *value proposition's shape*, which reads as a turn even though the work plan didn't change; n04 "breakthrough" — a $0 unblock of "try it ASAP"). `artifacts[a03].status: "parked"` is an invented enum value (see friction #1). The claim that capabilities.md consolidates "28 numbered interaction points" comes from the session's own P1–P28 numbering referenced at L504.

## Where schema v2 fought this session (friction)

1. **"Parked" is a missing artifact status.** The walking-skeleton plan is finished, committed, and deliberately not being executed. `created` misstates its fate; `superseded` is false (nothing replaced it); `in-progress` is the opposite. Invented `parked` — the enum needs a value for *done-but-dormant*, which is common for planning sessions.
2. **Nothing distinguishes conversational forks from concurrent ones.** LIVED's fork/merge is byte-identical in schema to mock-e's agent fan-outs, but rendering them the same would lie about the session: nothing here ever ran in parallel. Lines may need a `carrier`/`concurrency` hint at line level (segments have `carrier`; lines don't).
3. **A deliberate close has no schema home.** mock-e forced `frontier` onto an open question; here frontier points at the closing decision and `openCount` is 0. "Session ended on purpose, next step lives in artifact a03" is currently smeared across `frontier.detail`, n14's summary, and an artifact status. A `session.closure: {kind: declared|abandoned|compacted-away|mid-work, next: ...}` would say it directly.
4. **Artifact-heavy sessions invert the map's weight.** Nine artifacts for fourteen nodes, and the session's *substance* (the beats, the counterfactuals, the MVP cut) is inside documents the map only names. For a planning session the artifact shelf is the story and the rails are scaffolding — supporting evidence for Round 5's open map-primary vs prose-primary question, from the map-skeptical side.
5. **Merge-that-feeds-creation needed plain `merge`.** LIVED lands into n12 at its creation (P1–P28 are inputs), not as an update — so `relation: "merge"` (mock-d's MERGE-1 semantics) reappears at line level, alongside d2's `merge-update`. Confirms mock-f's friction #3: the relation enum is now four values across the mock corpus and needs a Phase-3 ruling.
6. **The persona method is a *method* decision the schema stores as a move.** Pi's L392 proposal ("build a hypothetical week…") changed how requirements would be derived for the rest of the session — arguably a standing decision with `standing: active`. But it reads as work, not law, so n09 is a move with the quote in `because`. The decision/move boundary blurs when the ruling is "we will *work* this way".
