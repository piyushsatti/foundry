# cartographer — round 5 proposal: the Concourse

*Round 4 drew everything the data carried, faithfully — and the data carried no story; round 5 gives the session a goal, words, and destinations, then renders the same day twice so Pi can choose whether the map tells the story or illustrates it.*

## 1 · The finding: an honest map of data that had no story

Pi's round-4 verdict, in his words: "I am starting to see a shape that I like" — and then the failure — "I really cannot tell what this particular session was, or what the session had meaning or was getting towards." What he asked for is the whole requirement in one sentence: *"at a glance: this is what we're trying to do, these are the steps, this is how the session went — it was a lot of back and forth, but we produced a plan file."*

The diagnosis ran that sentence as a test suite — seven glance questions against the round-4 render of mock-d — and six fail or half-fail. **None fails for rendering reasons.** F1 faithfully draws everything the JSON carries. The JSON carries a **WHERE** — parent tree, lines, forks, merges, provenance spans — and no **WHY** (no intent at any level: session, line, or node) and no **WHAT-FOR** (no artifacts, no outcomes, no settlements). "We produced a plan file" is invisible because every artifact — SYNTHESIS.md, the vendored docs, the plan, the bin/ helpers — exists only as substrings inside summary prose. The back-and-forth's *settlement* lives in `history[].superseded_because`, which standing law rightly demotes off the spine — so the law that hides corrections also deleted Pi's story. Topology without motive or payoff cannot be rendered into a story by any amount of ink.

Then the field confirmed it. Two research streams ran fresh-eyes and blind to each other — one through games, one through software — and **both independently landed on the same paper**: Shahaf et al.'s *Metro Maps of Information*, the transit metaphor's own source literature. Its authors built maximally coherent metro lines and found the result "discouraging — coherent, they were not important." Geometry alone provably cannot narrate; lines need labels, importance-weighting, and editorial selection. When two agents approaching from opposite directions converge on one citation, that is the field telling us where the wall is.

And the root cause is specific: **mock-d's lines were cut mechanically** — one line per dispatched agent plus the mainline. D, I, and L are one-station lines that exist because three Task calls happened, not because the session pursued three separable questions. A line only narrates if it is a coherent thread aimed at one question. No studied game lets raw topology carry the story — every one pairs the graph with a verbal anchor — and the agent-trace vendors who tried are the cautionary tale: their users regressed to reading flat text.

The F3 failure is the same disease in navigation. "It just switches me from the timeline to something else" is literally accurate: SECTOR swaps coordinate systems — map space for reading-column space — keeping only the rail, which encodes transcript time, the one ordering the map deliberately doesn't use. And even a perfect zoom would land on a card unable to say *why this node matters to the session*, because intent, beat, and artifact context aren't data. Fix the data and the frame; the camera follows.

## 2 · The proposed surface: the Concourse

The station hall — where the departure board, the system map, the announcements, and the trains' destinations all face you at once. Not a new spec; a place to stand. Six elements, composed:

1. **The thesis header** *(Golden Idol)* — pinned above everything: **"set out to ___ · produced ___ · open ___"**. Slots fill live from `session.intent`, `artifacts[]`, and open nodes; blanks are the honest remainder. Intent is versioned — a goal-rewrite renders as a beat on the map, never a silent edit.
2. **The docked synopsis** *(GitHub Actions summaries · incident.io postmortems)* — 4–6 generated sentences, terse and factual. Hover any sentence and its line, stations, and terminal light while the rest dims *(Strava's cross-highlight)*. The story in words; the map as corroboration — or the reverse (§4).
3. **The map at key-moments density** *(chess.com Game Review)* — the home altitude shows moment-classified stations: breakthroughs and pivots full-size, grind as ticks on the stroke. Stations wear **beat titles — episode titles, never tool names** ("recovered the lost spec," not "Bash ×4"). The full log is a zoom level, not the home. Less map, not more.
4. **Terminals and the shelf** *(Slay the Spire · Dagster)* — every line ends AT something. Goal terminals sit ghosted until reached, struck through if abandoned; artifacts render as solid terminal stations feeding a small shelf strip ("SYNTHESIS.md · docs ×6 · README · plan A–E · bin/ ×3"), each chip lighting its producing node. "We produced a plan file" becomes ink at rest.
5. **The story spine** — a thin strip identical in every layer: intent sentence · beat bands · frontier caret · an eval-ish progress sparkline *only if it earns its ink* (it is a heuristic — texture, never verdict). The narrative frame travels where the geometry can't.
6. **Semantic zoom in place** *(DOI trees · Supreme Commander)* — click a station: dot → card → transcript excerpt, one camera. The line stays lit; everything else dims but never vanishes; the spine never moves. SECTOR stops being a place. This is the F3 fix.

**Kept from rounds 1–4:** the friendly transit skeleton (train-station tree, lines as strokes, the five fork/merge geometry rulings), the rail with its transcript-true positions and 5-hour whitespace, the three laws, the stroke-trust grammar (solid/dashed/dotted), verbatim rules, n19-loud, sanitization.

**Retired:** SECTOR as a separate place — and with it the L-A/L-B/L-C question as posed; semantic zoom plus the spine supersede tier navigation. OUTLINE's every-node-headed density as home — key moments is home; the full log is one zoom in. Tally chips as narrative — counts stay as chips, but `settled:` one-liners now do the storytelling; counts are not narrative.

**Noted, not spec'd:** a **rumor mode** — an Outer Wilds-style second projection clustering the same stations by the question they served. That, not a looser transit layout, is the answer to Pi's mind-map itch. A later round.

## 3 · Schema v2, argued

Every addition serves the glance test — the identity ruling holds: human transparency first, nothing here is machine plumbing.

| Field | Glance question | Extraction cost | Render sketch |
|---|---|---|---|
| `session.intent` (versioned) | What was this FOR? What was it getting towards? | Expensive but bounded — opening turns seed it; drift needs judgment. Versioned because intent drifts (read-only review → repair pass) | First slot of the thesis header; intent history one click behind it |
| `artifacts[]` — kind, name, `produced_by: node@version`, status | What did we produce? | Cheap — file writes, plan approvals, report landings are literal tool events in the JSONL | Solid terminals feeding the shelf; chips light their producing node |
| `session.frontier` | Where was the cursor? What's next? | Near-free — pure extraction | You-are-here caret on map, spine, and rail |
| per-line `label` (3–6 words) + `because` | Why does this thread exist? | Cheap where dispatched — the Task prompt IS the reason, quotable verbatim; mild inference for user-initiated forks | Line-head legend; a quiet "← because: lost-spec critical in n07" under the terminus board |
| `beats[]` — label, kind, span | What were the acts, in story order? | Moderate — boundaries are mostly machine-visible (fan-out, merge landings, plan approval, the 5-hour gap); labels need inference | Act bands behind the map; chapter heads on the rail; the spine's bands |
| `settled:` one-liner on churned nodes | What did the back-and-forth settle? | Cheap — derived from `history[].superseded_because`; a rewrite duty on the reducer, not new data | "↺ settled: manifest container = `candidates:`" as the station's second line |
| decision `standing: active \| expired(superseded_by)` | Which rules still bind? | Approval is machine-visible; linking it to the rule it retires is inference | Struck-corner tag on expired roundels — n02's "no plugin edits" visibly dies at n15's approval |
| node `moment: breakthrough \| setback \| pivot \| grind` | Which stations matter? | Inference — but the classifier gates only SIZE at the home density, never existence | Full-size station vs tick on the stroke |

**Rejected, and staying rejected:** blanket per-node `reason` (nineteen rationale lines is round-3 noise reborn; sequence implies reason mid-line, forks get theirs via `because`); a turn stratum (log-faithfulness reborn — the tool's anti-thesis); per-node event digests (counts are not narrative).

**The reducer principle — cutting lines is a narrative act.** A line is a coherence-selected thread aimed at one question, labeled in words. It is never a bucket of "which agent ran" or "which files got touched." Mock-d is the cautionary example: five lines cut by carrier, three of them one-station lines — structurally true, narratively mute. The recut (mock-d2) asks of every candidate line: *what question was this thread answering, and does every hop read as one evolving pursuit?* Score a line by its weakest transition; a line that can't answer gets merged or demoted. This is a reducer responsibility, spec'd now, before any reducer exists — because it is the difference between a map of the session and a map of the tooling.

## 4 · The open question, framed for the eye: does the map lead, or the prose?

Both research streams surfaced evidence, and it does not all point one way. Presented straight:

**For map-primary** — the Concourse as drawn in §2: synopsis docked above the map, the map is the page. Every studied game keeps the board central and lets one sentence anchor it; none inverts. Pi is a strongly visual reader who killed the document-shaped Dossier on sight in round 1, and the round-1 null-hypothesis control — the strongest log-primary *text* rendering — lost to state-primary graphics before any reducer existed.

**For prose-primary** — the synopsis IS the page: the thesis header plus 4–6 sentences at reading measure, with the map as its illustration in the margin or below, every sentence still cross-highlighting. When the agent-trace vendors hit exactly this wall, their users regressed to flat text — Langfuse shipped a Cmd+F-able Log View as the *fix*. incident.io's artifact of record is the prose postmortem, with the timeline as evidence. GitHub renders the same PR as Conversation and Files, and people read Conversation first. The strongest "how it went" artifacts in shipped software are prose, with structure as exhibit.

This is not decidable in text, and we won't pretend otherwise — Pi rules by eye. **Round 5 renders BOTH orientations from the SAME mock-d2 JSON** — same elements, same generated voice, same map. The only variable is which surface leads, so the comparison is pure orientation. Whichever loses survives as the winner's supporting element; nothing in §2 is exclusive to either.

## 5 · Round-5 render plan (sketch — the iteration-5 prompt gets authored from this)

1. **F1 — the Concourse, map-primary home.** Full mock-d2 at rest: thesis header, docked synopsis, key-moments map with terminals and shelf, spine, rail. *Answers: does the glance test pass — goal, steps, back-and-forth, payoff, remainder in ten seconds?*
2. **F2 — the Concourse, prose-primary home.** Same data: the synopsis at reading measure is the page; the map is its illustration. *Answers: which orientation does Pi's eye trust? F1 vs F2 is the gate.*
3. **F3 — the cross-highlight still.** One synopsis sentence hovered; its line, stations, and terminal lit; all else dimmed. *Answers: does sentence↔map binding read as one instrument, in both orientations?*
4. **F4 — semantic zoom triptych.** The same station at dot → card → excerpt, one camera, spine identical in all three panels, context dimmed but present. *Answers: is drilling now a deepening — the round-4 F3 fix, on evidence?*
5. **F5 — the churn beat.** The back-and-forth compressed to one settled, beat-titled station with its ×N badge and "↺ settled:" line; the expanded state alongside. *Answers: does "a lot of back and forth, but we produced X" finally render?*
6. **F6 — density pair.** The key-moments home beside the full-log zoom of the same region. *Answers: is aggressive default suppression right — does home feel emptier and friendlier than round 4 while saying more?*
7. **F7 — terminals close-up.** A goal terminal ghosted, one struck, artifact terminals feeding the shelf, frontier caret at the live edge. *Answers: do the lines visibly point AT something — does movement read as progress, never mere activity?*

## 6 · What Pi decides

1. **The orientation — map-primary vs prose-primary (F1 vs F2). This is the round's gate; nothing else locks until it does.**
2. Ratify **key-moments as home density**, full log one zoom in (F6).
3. Does the **generated voice earn trust** — thesis, synopsis, episode titles: terse and factual, or does any sentence read as spin? One wrong sentence is a trust-extinction event.
4. **Moment classification by eye** — do the full-size vs tick calls match his memory of the day? (The faithfulness gate, inherited from round 4.)
5. Confirm the **retirements**: SECTOR-as-place and the L-A/L-B/L-C question, superseded by zoom + spine.
6. **Rumor mode** — park for post-v0, or schedule as a later round's second projection.
