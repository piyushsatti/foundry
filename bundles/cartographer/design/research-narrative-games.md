# How games make branching structure tell a story at a glance

Research domain: games + game-adjacent narrative systems. Question: the session map shows structure but not story —
what devices make a network narrate goal, steps, position, output, and remainder? (Fresh-eyes doc; written without
reading the other design files.)

## Executive answer

1. **Anchor the goal as a terminal station** (Slay the Spire's boss-at-top): every line must visibly point AT something; then all movement reads as progress or detour, never as mere activity.
2. **Classify turns and surface only key moments** (chess.com Game Review): back-and-forth compresses when most stations are demoted to ticks and only breakthrough/blunder/pivot moments render as full stations — plus one eval-bar strip answering "was it going well?"
3. **Pair the graph with a persistent verbal anchor** (Golden Idol's thesis-sentence, quest-log objective lines): no game lets raw topology carry the story; a one-sentence "set out to X → produced Y → still open Z" header does the narrating, the map does the corroborating.
4. **Make drill-in a zoom, not a screen** (Supreme Commander strategic zoom; Outer Wilds detail-beside-graph): detail replaces representation in place while the frame persists — deepening, not teleporting.
5. **Two projections of one dataset** (Outer Wilds rumor mode vs map mode): a rigid timeline AND a curated idea-cluster view, toggleable — the mind-map feel is a second lens, not a looser layout.

## Per-system findings

### Outer Wilds — ship log (rumor mode / map mode)
- **Problem solved:** hours of nonlinear investigation stay legible as one coherent inquiry.
- **Devices:** two toggleable projections of identical data — map mode (where things are) vs rumor mode (how ideas connect); nodes cluster and are color/position-curated by *curiosity* (the mystery they serve), so the board reads as N questions, not one blob; every node carries state badges — "There's more to explore here" marks unfinished threads; unvisited rumors render as ghost nodes (you can see the shape of what you don't know); links only appear once *you* learned the connection, so the graph is a portrait of your understanding, not the world.
- **Steal:** color stations by the question they serve, not just the workstream; "more here" badges on threads the session opened but never closed = the "what remains" answer; a mind-map projection as a toggle over the same nodes.
- **Kill:** hand-authored cluster positions (a designer placed every rumor node); sessions need it computed — cluster by workstream centroid, keep transit view as the layout of record.
- Sources: outerwilds.fandom.com/wiki/Computer; nh.outerwildsmods.com/guides/ship-log/

### Detroit: Become Human — chapter-end flowchart
- **Problem solved:** "how did this chapter go, and relative to what could have happened?"
- **Devices:** the flowchart is shown *after* the chapter as a debrief, not during; your taken path is lit, untaken branches shown as locked/greyed stubs — the road-not-taken is what makes the taken path feel like a story; chapter segmentation (one flowchart per chapter, never the whole game at once).
- **Steal:** render abandoned approaches as short grey stub-branches off the line ("tried X, backed out") — Pi's "lots of back and forth" becomes visible, honest exploration instead of noise; chapter the session (goal-shifts = chapter breaks) and let the top-level map be chapters, not turns.
- **Kill:** exhaustive branch display — Detroit's stubs are authored possibilities; a session's untaken paths are unbounded, so only show branches *actually attempted then abandoned*.
- Sources: playstationlifestyle.net/2019/07/15/detroit-become-human-flowchart/; interactivepasts.com "How Games Tell Tales, Part 3"

### Slay the Spire / FTL — sector maps
- **Problem solved:** a branching graph that reads as "a run with a destination," not a graph.
- **Devices:** StS — the boss is rendered at the top of every act map from turn one; every edge visually ascends toward it, so any path = progress. Node icons are *typed* (fight/elite/shop/rest/treasure), so a route is skimmable as a sentence of icon-words. All paths converge at the boss (guaranteed narrative climax). FTL — the exit beacon plus the advancing rebel-fleet red zone swallowing the map behind you: elapsed time/pressure made territorial; you read urgency spatially.
- **Steal:** goal as terminal station at a fixed edge of the canvas, all lines oriented toward it; a small typed-icon vocabulary for stations (decision, artifact, error, research, churn-loop) so a line skims like a sentence; a subtle "spent" wash over the map behind the current position (FTL's fleet) to show where the session's effort went.
- **Kill:** forced convergence — sessions legitimately end with parallel unfinished lines; StS's single-boss convergence only fits single-goal sessions.
- Sources: slaythespire.wiki.gg/wiki/Map_Generation; ftl.fandom.com/wiki/Rebel_Fleet

### Chess.com / Lichess — Game Review
- **Problem solved:** the closest analog to cartographer's core problem — a long linear log of moves turned into a story with almost no visual vocabulary.
- **Devices:** every move classified (brilliant/great/good/inaccuracy/mistake/blunder/miss) via an expected-points model — annotation is judgment, not description; **key moments** — the review tour visits only the handful of turns where the story turned; the eval bar — one continuous strip showing who was winning the whole game, so the arc is visible before any move is read; coach commentary — one generated sentence per key moment saying *why* it mattered; game phases (opening/middlegame/endgame) chapter the log.
- **Steal:** classify session turns (breakthrough, blunder/rework, pivot, grind) and badge stations accordingly; a session eval-strip along the spine — distance-to-goal or confidence over time — instantly shows "a lot of back and forth" as oscillation followed by the final climb; default view = key moments only, full log behind a toggle.
- **Kill:** the engine's objective ground truth — session "eval" is a heuristic (tests passing, plan sections filled, goal-distance estimate); present it as texture, not verdict.
- Sources: chess.com/terms/game-review; support.chess.com "How are moves classified?"

### Obra Dinn / Golden Idol / Her Story — evidence boards
- **Problem solved:** making the act of connecting facts *be* the narrative.
- **Devices:** Obra Dinn — the book's fixed skeleton (crew manifest, chapters, ship map) exists from minute one with blanks; progress = filling a known-shaped container, so "what remains" is always visible as empty slots; the rule-of-three: fates lock in validated batches of three, and the handwriting turns to print — an irreversible "this is now settled" beat that converts churn into canon. Golden Idol — each scene's story is a fill-in-the-blank thesis sentence; the narrative is literally a sentence with holes that evidence fills; segments confirm in chunks to bound frustration. Her Story — the archive is the terrain and search queries are the movement (thin transplant; noted for completeness).
- **Steal:** the strongest "what was this FOR" device found: a fill-in-the-blank session thesis pinned above the map — "Goal: ___. Approach: ___. Produced: ___. Open: ___" — slots filling as the session proceeds, blanks = remainder; a "settled" typographic state for stations (draft → locked) when a churn loop resolves, retro-collapsing the loop into one confirmed station.
- **Kill:** Obra Dinn's fixed container size — a session's skeleton isn't known up front; the thesis sentence must be inferred and allowed to be *revised* (a revision is itself a story beat: "the goal changed here").
- Sources: gamedeveloper.com/design/case-of-the-golden-idol; obradinn.fandom.com (Rule of Three)

### Quest logs & journals — Witcher 3, Zelda BotW/TotK
- **Problem solved:** every open thread carries its own reason-for-existing.
- **Devices:** Witcher 3 — journal entries are retrospective past-tense prose by an in-world narrator (Dandelion) that *rewrites as you progress*: done steps become story, the active step stays imperative; the objective line ("Find the baron's daughter") is always one sentence, always visible. Zelda — the adventure log timestamps each step and pins one active objective; completed quests move to a separate ledger.
- **Steal:** per-line auto-generated retrospective blurbs (2-3 past-tense sentences per workstream) shown on hover/zoom — done stations narrated as story, current station as imperative; one bolded objective sentence per line at the line's head.
- **Kill:** hand-authored prose quality — generated blurbs must be terse and factual or they become noise; no voice-y narrator.
- Source: witcher.fandom.com; gamefaqs threads on Dandelion narration

### Zelda BotW — Hero's Path mode
- **Problem solved:** "what did I actually do these past N hours?" — 200 hours of movement as one green trail plus a time slider to replay it; deaths marked on the trail.
- **Steal:** a time scrubber under the session map that replays the map's growth; failure markers (errors, reverts) as small X's on the trail. **Kill:** raw spatial fidelity — the value is the scrubber and the death markers, not the wiggle.
- Source: zelda.fandom.com/wiki/Hero's_Path_Mode; pastemagazine.com 200-hours piece

### Skill/tech trees — Path of Exile, Civilization
- **Problem solved:** progress-as-territory; a build/strategy legible as a shape.
- **Devices:** PoE — allocated nodes form one lit contiguous path through a dim constellation; intent is readable as *direction of travel* through territory-you-ignored; Civ — techs in era columns (time = x-axis), and clicking a distant tech highlights the full prerequisite chain ("beeline") — a preview of the path implied by a goal.
- **Steal:** dim-but-present context (considered-but-unexplored options faint behind the lit line — the mind-map feel without layout chaos); "beeline" projection: given the stated goal, ghost the remaining implied stations ahead of the current position — the map shows the future, not just the past.
- **Kill:** the full authored possibility space; only render unexplored nodes the session itself mentioned.

### After-action screens — XCOM debrief, Hades run recap, racing/sports telemetry
- **Problem solved:** the "how it went" genre — one screen, consumed in ~10 seconds, after the action.
- **Devices:** fixed-slot scorecard (objective met? losses, loot, time — same slots every mission, so reading is instant); Hades separates the run recap (what happened) from persistent meta-progress (what it counted toward); telemetry overlays lap traces against a reference to show *where* time was lost.
- **Steal:** a session debrief card as the map's front door — outcome, duration, artifacts produced, loops hit, threads left open — with the map behind it as the "expand" view; fixed slots so every session reads identically fast.
- **Kill:** win/lose framing; sessions end in states, not verdicts.

### Metro Maps of Information (Shahaf & Guestrin, CMU) — game-adjacent, directly on the ask
- The transit metaphor *is* proven for narration — but only when each line is a *coherent narrative thread* selected by a coherence metric, with stations as salient events. Lines are editorial constructs, not raw structural buckets. If cartographer's 5 lines were derived mechanically (files touched, agents, phases), that is likely the root cause of "structure but not story": the lines themselves must be stories.
- Source: cs.cmu.edu/~dshahaf/fp0590-shahaf.pdf ("Trains of Thought: Generating Information Maps")

## The transplant set (ranked for round 5)

1. **Thesis header with blanks** (Golden Idol) — pinned sentence above the map: "Set out to ___ · produced ___ · open: ___"; slots fill live; a goal-rewrite is rendered as a beat on the map.
2. **Turn classification + key-moments default** (chess.com) — badge stations breakthrough/blunder/pivot/grind; default render shows only key moments as full stations, the rest as ticks; full log is a zoom level.
3. **Goal as terminal station** (Slay the Spire) — each line ends at a rendered destination station (checkered/ghosted until reached); artifacts produced = solid terminal, abandoned goal = struck-through terminal.
4. **Semantic zoom, one camera** (Supreme Commander / Outer Wilds) — drilling in swaps station-dot → station-card → full transcript excerpt in place, breadcrumb spine always visible; never a separate detail screen. (nerdsworthacademy.com Mechanic Monday: Strategic Zoom)
5. **Eval strip on the spine** (chess.com) — thin progress-toward-goal sparkline under the whole map; oscillation = the back-and-forth, compressed into one glance.
6. **Churn collapse via locked beats** (Obra Dinn rule-of-three) — when a rework loop resolves, fold its turns into one "settled" station (typographic state change) with a ×N badge; expandable at deeper zoom.
7. **Ghost stubs for abandoned attempts** (Detroit) — short grey dead-end branches where an approach was tried and dropped; the not-taken makes the taken path read as chosen.
8. **Rumor-mode toggle** (Outer Wilds) — second projection: same stations clustered by question/idea instead of time; answers the mind-map expectation without loosening the transit layout.
9. **Line-head objective sentences + past-tense blurbs** (quest logs) — one imperative sentence per line head; hover gives a 2-sentence retrospective of the line so far.
10. **Debrief card front door + replay scrubber** (XCOM/Hades + Hero's Path) — fixed-slot summary card as the entry view; time slider replays map growth.

## Contradictions with (assumed) current direction

- **Lines must be editorial, not structural.** Shahaf's metro-maps result + Outer Wilds curiosities both say the same thing: a line only narrates if it's a coherent thread toward one question. Mechanically derived workstreams will always read as "structure but not story."
- **Don't perfect one view — ship two projections.** Outer Wilds' rumor/map toggle and Detroit's per-chapter flowcharts suggest the mind-map ask is best met with a second lens over the same nodes, not a softer transit layout.
- **No studied game lets the graph narrate alone.** Every one pairs it with a verbal anchor (objective line, thesis sentence, coach caption). Cartographer needs a text layer as a first-class element, not a garnish.
- **Less map, not more.** Chess.com hides most moves by default; Detroit shows one chapter at a time. The at-a-glance fix is aggressive default suppression with zoom-to-reveal — the opposite instinct from rendering the whole session richer.
