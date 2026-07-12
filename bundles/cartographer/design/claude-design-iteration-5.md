# cartographer — round 5: the Concourse — does the map lead, or the prose?

**Recap.** Round 4 drew everything the data carried, faithfully — and the data carried no story. Pi's verdict: "I am starting to see a shape that I like" — and then — "I really cannot tell what this particular session was, or what the session had meaning or was getting towards." The diagnosis: mock-d carried a WHERE (tree, lines, forks, merges, provenance) and no WHY (no intent at any level) and no WHAT-FOR (no artifacts, no outcomes, no settlements) — "we produced a plan file" existed only as substrings inside summary prose. Three research streams converged on one wall: **geometry cannot narrate** (two fresh-eyes passes, blind to each other, independently landed on Shahaf's *Metro Maps of Information*: maximally coherent mechanical lines were "discouraging — coherent, they were not important"); **lines are editorial** — a line narrates only when it is a coherence-selected thread aimed at one question, never a bucket of which-agent-ran; **the story needs words at three altitudes** — thesis, synopsis, station; and **outputs are first-class or invisible**. The data is upgraded to schema v2: **`mock-d2.json` is uploaded alongside this prompt — render from it and nothing else.** This round renders the **Concourse** — the station hall where the departure board, the system map, and the trains' destinations face you at once — and settles ONE gate: **map-primary vs prose-primary**. The same data, twice; the only variable is which surface leads.

**Context (skip if you rendered rounds 1–4).** Cartographer renders a session map: a consolidated semantic tree of one AI working session. State-faithful, not log-faithful: rework UPDATES nodes in place (version bump + history entry with `superseded_because`); dead ends fold into per-node `residuals`; decisions anchor to verbatim transcript `quote`s; every node carries `provenance` line-spans into the raw transcript. Reader: Pi — one strongly visual developer, tired at end of day; the at-rest render must work with zero interaction.

---

## 1 · Mock D2 — the same real day, now with a story

The same 2026-07-05 meditate session as round 4 — 19 nodes, ids unchanged, every quote, span, residual, and history entry byte-identical to mock-d (two prose edits only, both because the old line names died: n03's title "review lines" → "review lenses"; n14's residual "line M" → "the RUNNABLE line"). What changed: the five **mechanical** lines (mainline + one per agent + recovery) are re-cut into the **three questions the session actually pursued**:

| Line | Label | `because` (byte-exact, speaker, transcript line) | Nodes |
|---|---|---|---|
| ① REVIEW | What state is meditate in? | "Uh, don't update the version number Right now, I want you to do information gathering, and you can store all the information in gitignore folder, uh, for now." — Pi, line 8. *Carries the line's MODE; the three-lens scope wording is editorial — flagged in the JSON's note* | n01–n07 |
| ② RESCUE | Rescue the lost spec | "So the first thing that makes sense to me is creating the README, and I'm ready to take whatever, um, suggestions you have here. However, we do have the file system of the laptop that originally created, Meditate, so that is accessible. It's in the m n t folder." — Pi, line 196 | n08–n11 |
| ③ RUNNABLE | Make meditate run here | "make a plan for the natural next moves" — Pi, line 340 | n12–n19 |

```
REVIEW ① — "What state is meditate in?"
  n01──n02──n03━━━━━━━━━━━━━━━━▶ n07 (v1 ▸ v2) ── answered; line ends
             │ fan-out ×3        ▲▲▲   ▲                   │ succession
             ├⟨design⟩     n04 ──┘││   │ merge-update      ▼
             ├⟨impl⟩       n05 ───┘│   │ (bumps n07 → v2)  RUNNABLE ③ — "Make meditate run here"
             └⟨literature⟩ n06 ────┘   │                   n12─n13─n14─n15─n16─n17─n18─n19
  RESCUE ② — "Rescue the lost spec"    │                             frontier▲       ◇open
  n07@1 ──fork──▶ n08(n09─n10─n11) ────┘
```

**Key deltas vs round 4's mock — each changes the drawing:**

- **The agent fan-out now lives INSIDE REVIEW.** Old lines D/I/L are `lines[REVIEW].segments[]` — `REVIEW/design`, `REVIEW/impl`, `REVIEW/literature` — each fanning out at n03 and landing at n07; n04/n05/n06 carry a `segment` field. Render the fan-out as **branch geometry within REVIEW's band**: three thin parallel strands in REVIEW's hue, never three line identities, never three bullets. One question, three probes. The trunk visibly continues during the fan-out (n03's summary: scope notes, insurance wakeup).
- **The old mainline M is gone as an identity.** One chat window carried two missions; v2 splits it into REVIEW and RUNNABLE joined by a **`succession` edge** (RUNNABLE's `from`: n07@2, relation `succession`): REVIEW ends *answered* and RUNNABLE takes over from its final state — a hand-off, not a fork; no continuing trunk.
- **The loop-back merge is now version-addressed.** RESCUE's `from`: {REVIEW, n07, **version 1**, `fork`}; `into`: {REVIEW, n07, **version 2**, `merge-update`}. Round 4's known limitation — "merge-as-update vs merge-as-new-node is invisible" — is fixed in structure, not prose. Still the single hardest moment; the fork's cause is now carried by `lines[RESCUE].because`, not buried in a summary.
- **New top-level story data:** versioned `session.intent`, `artifacts[]`, `session.frontier`, `beats[]`, a `moment` on every node, `settled` one-liners, decision `standing`.

**Intent, versioned** (each shift anchored to a *decision* node — the ruling, not the finding):

| v | Intent (verbatim from JSON) | Shifted at |
|---|---|---|
| 1 | Assess meditate end to end — design, implementation quality, and standing against the memory-curation field — as read-only reconnaissance: no plugin edits, no version bump, findings to .gitignored/. | → n09@1 (the lost-spec critical ruled a workstream — recovery entered the goal) |
| 2 | Assess meditate and recover its lost spec: vendor the authority docs into the repo and build the README around them, so the verdict rests on a spec that exists here. | → n15@1 (plan approved — assessment became repair) |
| 3 · current | Make meditate run on this machine: execute the approved repair plan (workstreams A–E plus a no-live-mutation verification pass) on top of the recovered spec. | — |

**Artifacts — 13, first-class**, each with `produced_by: node@version`: a01 scope file (n03) · a02–a04 the three lens reports (n04–n06) · a05 SYNTHESIS.md, produced by n07@1 and **rewritten by the loop-back** (`updated_by: n07@2`) · a06 vendored authority docs ×6 (n10) · a07 README (n11) · a08 repair plan A–E (n15) · a09 bin/ helpers ×3 (n16) · a10 skills rewired + a11 config split + **a12 apply/SKILL.md, status `in-progress`** (n17) · a13 migrate hardened (n18). Shelf grouping: `synthesis · reports ×3 · docs ×6 · README · plan A–E · bin/ ×3 · skills · config · migrate` — a12 is the shelf's live edge; it IS the frontier's object.

**Beats — 3 acts, data now:** "Three lenses, one verdict" (n01→n07) · "The spec was on the old laptop" (n08→n11) · "From verdict to repair" (n12→n19, note: *opens after a ~5-hour gap* — previously only rail whitespace).

**Moments:** 4 breakthrough · 2 setback · 4 pivot · 9 grind. **Default density: 10 of 19 stations full-size; the 9 grind nodes (n01 n02 n03 n08 n11 n12 n16 n17 n19) demote to unlabeled ticks** — with three musts that survive demotion: **n19 stays loud amber** (open trumps grind), **n17 carries the frontier caret** (you-are-here trumps tick size), and **n02 shows its expired standing even at tick scale** (struck corner, or at first zoom). The map should skim as: two setbacks and a breakthrough land in a pivot (n07) → a pivot–breakthrough rescue (n09, n10) → pivot, breakthrough, pivot (n13–n15) → breakthrough (n18) → open (n19).

**Settled + standing:** n07.settled — "The lost-spec critical is resolved: the authority docs live in plugins/meditate/docs/ and the synthesis reads against a spec that exists in this repo." n14.settled — "The manifest container is candidates:, the slug rule follows the canonical decisions log, and the verb lexicon is the 14-verb superset — the review's 'neither shape works' ambiguity is closed." Churn renders as what it *bought*, never as a correction count. **n02 is `standing: "expired"`, `superseded_by: "n15@1"`** — the read-only ground rule died when the plan was approved; render it visibly struck/greyed with "superseded by n15" wherever it appears. A render that shows n02 as live law fails this mock. n09/n13/n15 are `active` — fulfilled ≠ expired.

## 2 · The Concourse — six elements, plus the carried grammar

1. **Thesis header** — pinned above everything, departure-board register: **"set out to ___ · produced ___ · open ___"**. Every slot fills ONLY from JSON fields — `session.intent` + history, `artifacts[]` (count + grouped names), open nodes, `session.frontier`. No slot carries a word without a field behind it. The correct fill for mock-d2:
   > Set out to **assess meditate end to end, read-only** *(intent v1)* — the goal grew into **rescuing its lost spec** *(v2, at n09)* and then **making it run on this machine** *(v3, at n15)* · produced **13 artifacts** — 3 lens reports + a twice-written synthesis, 6 vendored spec docs, a README, an approved A–E plan, 3 bin/ helpers, a hardened migrate, rewired skills · open: **workstream E, the verification pass, the unapplied literature citations** *(n19)*, frontier **mid-edit in apply/SKILL.md** *(n17@1)*.

   Intent is versioned: the header shows v3 with the drift one click behind — a goal-rewrite is a beat on the map, never a silent edit. `session.title` stays in the masthead as the structural synopsis; title and intent answer different questions and both render.
2. **Docked synopsis** — 4–6 sentences, terse and factual. **CRITICAL RULE: sentences are ASSEMBLED from JSON fields — intent texts, line labels + `because` + `outcome`, beat titles, `settled` one-liners, artifact names, `frontier` — never free-written. Every sentence must be traceable to named fields; connective tissue is grammatical mortar only and carries no claims.** Assembly recipe for mock-d2 — S1: intent v1→v3 with its shift anchors. S2: beat-1 title + REVIEW's label and `outcome`. S3: RESCUE's `because` + `outcome` + n07.settled. S4: beat-3 title + its gap note + a08–a13 names + n14.settled. S5: `frontier.detail` + n19's title. Hover any sentence → its line, stations, terminal, and shelf chips light; everything else dims, never vanishes.
3. **Key-moments map** — the home altitude. Breakthrough/pivot/setback stations full-size wearing their **verbatim node titles** (already episode-grade: "Old filesystem reached; docs located and vendored" — never tool names); grind as unlabeled ticks on the stroke, per §1's 10/9 split and its three overrides. The full log is a zoom level, not the home. Less map, not more. Round 4's five geometry rulings hold (fork/merge as line strokes, interchange ring on n07, no arrowheads at rest, wire-hop arcs where a run crosses a lane it doesn't stop at); numbered bullets and lane hues now attach to the THREE editorial lines, spine order ① REVIEW ② RESCUE ③ RUNNABLE.
4. **Terminals + the shelf** — every line ends AT a drawn destination reflecting its question answered: REVIEW's terminus board wears its `outcome` (answered at n07@2), RESCUE's its resolution, RUNNABLE's stands **ghosted-open** at the live edge. A quiet "← because:" note under each terminus board cites the line's charter. Artifacts render as **solid terminal glyphs** feeding a compact shelf strip (grouping in §1); each chip lights its producing node; a05 shows its loop-back update; a12 renders live/in-progress at the shelf's frontier edge. "We produced a plan file" becomes ink at rest. Struck terminals (abandoned goals) exist in the grammar — **dormant here; do not invent an occasion**.
5. **Story spine** — a thin strip IDENTICAL in every frame: the current intent sentence (v3) · the three beat bands · the frontier caret at n17. Nothing else — the mock carries no eval data, so no sparkline.
6. **In-place semantic zoom** — click a station: **dot → card → transcript excerpt, one camera**. The station's line stays lit; context compresses and dims but never vanishes; the spine never moves; Escape unwinds one step (excerpt → card → home). SECTOR is retired as a place — the round-4 L-A/L-B/L-C question died with it.

**Carried from round 4, adapted.** **The rail:** viewport-pinned left, full transcript height, IDENTICAL in every frame — now **three soft threads**, one per editorial line, lane hue, headed by their numbered bullets; REVIEW's thread splits into three thin strands during the fan-out and rejoins at n07's landing (mirroring the map's branch-in-band); marks at true transcript position — the ~5-hour gap before n12 reads as one long whitespace; three mark forms at rest only — plain lane-colored dot (created/updated), ◆ (decision landed), amber ? (question opened); hover a mark → label; click → navigate. Rounds-1/2 friendliness — no ruler numbers, no column grid, no ledger. **The laws:** (1) icons augment text, never replace it at default altitude; (2) every meaning has two channels — nothing in hue alone; (3) hue budget — **lane hues = the 3 editorial lines only**, one amber = open work only, all other ink achromatic on paper. Status is shape+fill (hollow open · half active · solid done); trust is stroke style (solid = raw-span-backed, dashed = summary-derived, dotted = residual/ghost). AD-1 Network Modernism, softened — warm paper, generous spacing, air around everything.

## 3 · Render plan — exactly these frames, in order

1. **F1 — the Concourse, map-primary home.** Full mock-d2 at rest: thesis header, docked synopsis, key-moments map with terminals and shelf, spine, rail. *Answers: does the glance test pass — goal, steps, back-and-forth, payoff, remainder in ten seconds?*
2. **F2 — the Concourse, prose-primary home.** SAME data, same elements, same assembled sentences, same map: the thesis header + synopsis at reading measure IS the page; the map is its illustration, in the margin or below, cross-highlighting intact. *Answers: which orientation does Pi's eye trust? **F1 vs F2 is the round's gate.** Information design identical between the two except orientation — if they drift anywhere else, re-converge them.*
3. **F3 — the cross-highlight still.** The RESCUE sentence hovered: RESCUE's stroke, n08–n11, its terminus, and chips a06/a07 lit; all else dimmed. *Answers: does sentence↔map binding read as one instrument, in both orientations?*
4. **F4 — semantic-zoom triptych.** n09 at dot → card → transcript excerpt, one camera, the spine identical in all three panels, context dimmed but present; the excerpt carries the byte-exact voice quote ("…It's in the m n t folder.") in pull-quote treatment with its provenance chip. *Answers: is drilling now a deepening — the round-4 F3 fix, on evidence?*
5. **F5 — the churn beat.** n14 at rest — full-size station, its "↺ settled:" second line, version tally badge — beside its expanded history: v1's summary beneath v2, `superseded_because`, the folded-fork residual as a collapsed stub. *Answers: does "a lot of back and forth, but we produced X" finally render?*
6. **F6 — density pair.** The key-moments home beside the full-log zoom of the same region — crop the RUNNABLE run (n12–n19: five of its eight stations are ticks at home). *Answers: is aggressive default suppression right — does home feel emptier and friendlier than round 4 while saying more?*
7. **F7 — terminals close-up.** REVIEW's terminus wearing its answered `outcome`, RESCUE's resolution, RUNNABLE's terminal ghosted-open; the artifact shelf with a12 live; the frontier caret at n17. *Answers: do the lines visibly point AT something — does movement read as progress, never mere activity?* (The proposal asks for one struck/abandoned terminal; mock-d2 has none — the struck grammar stays dormant.)

## 4 · Standing non-negotiables (every frame obeys them)

- **The JSON is ground truth.** Titles, summaries, quotes, labels, intent texts, beat titles, settled lines, outcomes, artifact names, statuses, versions, spans render verbatim from `mock-d2.json`. Never invent, paraphrase, or truncate node text. Quotes are NEVER ellipsized.
- **Quotes are byte-exact, including voice-transcription artifacts** — every "uh," every "m n t." Cleaning them up is paraphrase: a breach, not a favor.
- **n15's quote is assistant-articulated — mark it.** A small fixed tag, exactly "assistant's words — approved via gate," set apart from the pull-quote treatment Pi's own words get (n02, n09, n13).
- **Editorial fields are DATA.** Intent wording, line labels, `because` texts, beat titles, `settled` one-liners, `outcome`s — render verbatim from JSON, never rephrase, never improve. The JSON flags which are inferred (intent wording, beat titles, line labels, moment classes); quoted vs inferred stays typographically distinct.
- **The synopsis assembly rule (§2.2) is absolute** — no free-written prose anywhere on the surface: every sentence, slot, and caption traces to named JSON fields.
- **Elide whole nodes, never shorten one.** Title-only and tick are sanctioned densities; truncation is not.
- **Corrections stay off the spine at rest** — residuals and superseded versions one interaction away. **Grind ticks are NOT corrections**: they are real steps rendered at low density — ticks, never ghosts.
- **Open questions loud at rest at every density** — n19's amber survives its grind class in every frame.
- **Friendly temperament** — every frame at least as quiet as round 4. If a frame looks busier than round 4's F1, it is wrong — take ink away until it isn't.
- **Sanitization holds.** "The old laptop," "the m n t folder" — render only what the JSON carries; never reconstruct or invent identifiers.
- **Desktop-first**, generous landscape viewport; no mobile variants. Renders differ where the spec says and nowhere else.

## 5 · What Pi decides from these renders

1. **Map-primary vs prose-primary (F1 vs F2). THE gate — nothing else locks until it does.** Whichever loses survives as the winner's supporting element.
2. **Does the editorial line cut read TRUE** — REVIEW/RESCUE/RUNNABLE vs mock-d's mechanical five? The faithfulness gate, inherited from round 4: does the re-cut match his memory of the day, including the fan-out demoted to segments?
3. **Does the thesis header + synopsis pass his glance test** — "what was this for, how did it go, what did it produce" — and does every assembled sentence read terse and factual? One sentence that reads as spin is a trust-extinction event.
4. **Key-moments default density (F6)** — right amount hidden? Ratify the 10-full/9-tick split or move the dial.
5. **Moment badges** — should breakthrough/pivot/setback wear visible glyphs, or is size-only classification enough?
6. **The story spine** — earns its strip in every frame, or folds into the masthead?
7. **Anything the Concourse killed that he misses from round 4** — SECTOR as a place, OUTLINE-as-home, per-agent line identity, anything.
