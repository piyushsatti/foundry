# cartographer — round 4: draw the merge, pick the layers

**Recap.** Round 3's verdict split: the train-station tree is the look — "very visually clear" — but the surface was too noisy and too instrument-grade, and Pi ruled for rounds 1–2's temperament: "a lot more friendly and intuitive." Layers were endorsed in principle, near-verbatim, but "I'm not really sure how I want the layers structured" — so this round renders three candidate structurings (L-A/L-B/L-C, §3) for Pi to pick by eye. A noise audit has since assigned every round-3 element a home density; §2 is that audit compressed, and it is law — what renders where is not a style choice, and seven elements are cut outright. AD-1 Network Modernism stays the working default, softened per the friendliness ruling; the spatial canvas stays parked — not spec'd, not killed. And the data is new: **Mock D is a real session** — Pi's own 2026-07-05 meditate review — with transit lines that genuinely fork and merge. `mock-d.json` is uploaded alongside this prompt; render from it and nothing else.

**Context (skip if you rendered rounds 1–3).** Cartographer renders a session map: a consolidated semantic tree of one AI working session. State-faithful, not log-faithful: rework UPDATES nodes in place (version bump + history entry with `superseded_because`); dead ends fold into per-node `residuals`; decisions anchor to verbatim transcript `quote`s; every node carries `provenance` line-spans into the raw transcript. Node fields: `id`, `version`, `type` (topic/move/decision/open-question), `title`, `summary`, `status` (done/active/open/false-alarm/dead-end), `parent`, `line`, `residuals`, `history`, `provenance`, `quote`. Reader: Pi — one strongly visual developer, tired at end of day; the at-rest render must work with zero interaction.

---

## 1 · Mock D — a real session that forks and merges

The 2026-07-05 meditate session, ~6 hours in three phases: a full plugin review fans out as three parallel background agents and merges into one synthesis; the synthesis's scariest finding (the plugin's spec docs exist only on an old laptop) forks a doc-recovery line whose output merges BACK into the synthesis, updating it in place; hours later the merged state feeds a plan, and the plan executes. 19 nodes, 5 lines, 3 topics. Nothing structural is invented — every fork, merge, quote, and span is extracted from the real transcript.

Two schema additions over prior rounds: a top-level `lines` array (`{id, label, forks_from: {line, node}|null, merges_into: {line, node}|null}`) and a `line` field on every node. Lines are a transit topology laid OVER the parent tree; `parent` stays pure grouping.

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

**Acceptance criteria — a render fails this mock if any of these miss:**

- **FORK-1 (at n03):** one point splits into three lines (D, I, L) *while M itself continues* — the mainline kept working during the fan-out. A render that pauses the mainline at the fork misrepresents the session.
- **MERGE-1 (at n07):** three lines terminate INTO a single node. n04–n06 are *inputs* to n07, not steps before it on line M — laying the three reviews inline on M in landing order fails.
- **FORK-2 → MERGE-2 as a loop:** line R departs from n07 and returns to n07. Its landing is an **in-place update** — n07 v1→v2, history reachable — not a new downstream node. Fork-source and merge-target are the same node. This is the single hardest and most important moment in the mock.
- **Line M alone tells the story** top-to-bottom: review → dispatch → synthesis → plan → locked calls → execution → open work.
- **Lines are orthogonal to topics:** M traverses two topics (n01, n12); topic n08 belongs entirely to line R. "Which workstream carried this" and "what is this part of" are different questions — never conflate them.
- **n19 stays loud** at every density — the one open question.
- **n15's quote is the assistant's words, not Pi's** (the plan was approved through a UI gate; no user prose exists). It must carry a small honest marker distinguishing it from Pi's own quoted words — see §5.
- **Both updated-in-place nodes** (n07@v2, n14@v2) carry real history with `superseded_because`; the four residuals (the stale insurance wakeup on n07 — this mock's false alarm; the stale-mount false start on n10; the uv stdout-purity check on n16; the folded fork on n14) are one interaction away, never at-rest content. Statuses are mixed at rest: mostly `done`, `active` on n12/n17, `open` on n19.

**Geometry rulings forced by Mock D** (the standing spec predates lines that merge — these five resolve it; obey them):

1. **Bullets and lane hues attach to LINES, not topics:** ① M · ② D · ③ I · ④ L · ⑤ R, spine order. A line head is its numbered bullet + verbatim line `label` (unboxed at MAP; terminus board with computed status roll at OUTLINE). Topic nodes (n01, n08, n12) render as section-header stations at their position ON their line — topics group, lines carry.
2. **Fork/merge runs are line strokes — MAP ink, not connectors.** A merge run terminates at the target's docking dot; termination IS the direction cue — no arrowheads at rest, chevrons stay interaction-only. Merge-target dots wear the interchange ring (n07 wears it).
3. **Wire-hop arcs render wherever a run crosses a lane it does not stop at, at every density the run renders** — a one-element promotion from OUTLINE, forced by lines that cross lanes at MAP, where no headings exist to kill a false touches-this-lane read.
4. **MERGE-2's landing carries no dot ornament at MAP** (version rings are cut): the in-place update is carried by the returning stroke itself, by n07's version tally chip at OUTLINE, and by the second dot on M's rail thread. SECTOR and the panel carry the full history.
5. **Rail threads follow lines — five threads — and never merge.** Merging is map geometry; on the rail a landing is just marks, and a thread simply ends when its line lands.

## 2 · The surface — three densities, one rail

Standing law first: **(1)** icons augment text, never replace it at default altitude; **(2)** every meaning has two channels — nothing in hue alone; **(3)** hue budget: lane hues = line identity only, one amber = open work only, all other ink achromatic on paper. Status is shape+fill; trust is stroke style (solid = raw-span-backed, dashed = summary-derived, dotted = residual/ghost — surface-wide).

- **MAP — the abstract tree. 12 elements, nothing else:** typed docking dots (move tick · decision roundel · topic head); status fill-states (hollow = open, half = active, solid = done; achromatic check/slash terminal pair); ghost-station glyph *(dormant — no false-alarm node here)*; amber ? badge (n19); numbered line bullets; interchange ring on merge-target dots; the rail's three mark forms; the rail seam band *(dormant — `compaction_events` is empty)*; stroke-trust grammar; slimmed masthead; empty-state art license *(dormant — no empty state)*; elevation ladder, four rungs (lines < connectors < cards/rows < lifted selection + panel).
- **OUTLINE — MAP plus exactly one verbatim heading per dot, plus 7:** full interchange connectors *(dormant — Mock D has no cross-line reference links; forks/merges are line geometry per ruling 2)*; wire-hops (per ruling 3); underpass elevation (connectors dimmed at rest); tally chips (version · residuals · open — small, countable, JSON-derived); terminus boards (bullet + verbatim label + computed roll, e.g. line M's "12 stations · 1 open · updated ×2"); spur cards + buffer stops *(dormant — no dead-end nodes)*; post-seam corner tab *(dormant)*.
- **SECTOR — one line's dedicated reading view at ~680px measure, plus 5:** full cards with history (onion-skin diffs, `superseded_because`) and residuals expanding on demand; provenance chips (capsule + span); ≈ prefix on summary-derived spans *(dormant — every span here is raw)*; pull-quote typography; force-push "decision re-derived" row *(dormant — no superseded decision)*; post-seam paper shift *(dormant)*.
- **Interaction-only (4):** directional chevrons (only on a lifted run); route-focus ribbon (hover a line: thicken one step, dim other lines' furniture, never card text); ruler numbers (rail hover only); legend strip (summoned via "?").
- **Cut (7 — these do not exist in any frame):** version rings; glint dots; 3-letter line codes; the FIDS/tabular register grid; the full masthead strapline + operator roundels; the departures board; the yard strip + brush.

*Dormant* means the grammar exists but this mock never triggers it — do NOT invent an occasion for it.

**The rail — the friendly chronology sidebar.** Full transcript height, viewport-pinned left, IDENTICAL in every frame of every candidate — the stable landmark that keeps drill-down from disorienting. Five soft threads, one per line, lane hue, generous spacing, each headed by its numbered bullet. Marks at true transcript position, positions proportional — the ~5-hour gap before line 326 must read as one long whitespace. **Three mark forms at rest, only:** plain lane-colored dot (created/updated), ◆ (decision landed), amber ? (question opened). Dots only at rest; hover a mark → label (event · node title · line position); click → navigate to that node in the current layer. No printed ruler numbers at rest. No column grid, no six-glyph event codes, no tabular ledger — that was round 3's rejected temperament. Same job, rounds-1/2 form.

**Navigation contract (holds in every candidate):** click a line (head, title, or stroke) → its SECTOR. Click a dot or heading → node detail side panel — the full card as SECTOR renders it, history, residuals, provenance chips opening the deep-linked span in a capped well; the layer beneath does not change; the node's rail marks light. Escape unwinds one level: span well → history → panel → sector → home → no-op. Breadcrumb lives in the masthead: root = verbatim session title; inside a sector it grows "▸ ① Mainline — review orchestration, plan, execution"; clicking root = home. **OUTLINE is home** in every candidate. Masthead, slimmed: verbatim session title + date + amber open count ("1 open") — nothing else.

**Temperament (governs every frame):** AD-1 Network Modernism — humanist grotesque, transit-grade lane inks on warm paper (near-black slate in dark mode), geometric roundel-first glyphs — **softened**: soft strokes, generous spacing, air around everything; rounds-1/2 friendliness, not round 3's cockpit. Every frame must feel EMPTIER and friendlier than round 3. If a frame looks as busy as round 3, it is wrong — take ink away until it isn't.

## 3 · The three candidate structurings

Shared geometry in all three: lines as vertical columns, stations descending in spine order, top-to-bottom — the train-station tree. Layers are an IA, not a zoom dial: each is a designed view, no in-betweens. Transcript access is a provenance-chip click from any layer.

- **L-A · Three-tier ladder.** T1 = MAP, T2 = OUTLINE, T3 = SECTOR — three places, keyboard-stepped; the panel is available at T1/T2 without leaving the tier. Cleanest density separation, quietest top view; the most navigation. Lands at T2, T1 one keystroke up.
- **L-B · Two layers.** One map at OUTLINE (headings always on); MAP exists only as a density toggle, not a place; click a line → SECTOR. Fewest moves, one obvious home; the quiet abstract view stops being a resting state.
- **L-C · Hub and detail.** The OUTLINE map is the only map and it never changes; SECTOR opens as an overlay lightbox above the dimmed hub; Escape always means home. Maximal spatial stability; deep reading is never a place, only a layer floating above one.

## 4 · Render plan — exactly these frames, in order

F1–F4 are shared: they render identically under L-A and L-B (L-C differs only where F5 shows). Information design identical everywhere the spec doesn't name a difference; if two frames drift apart anywhere else, re-converge them.

1. **F1 — hero: OUTLINE home, full Mock D.** All five lines; FORK-1 splitting off a continuing M; MERGE-1's three terminations into n07; the FORK-2→MERGE-2 loop; n19's amber badge; every heading verbatim; the rail with its 5-hour whitespace. *Answers: does real merge/diverge topology read at rest, at home density, in a frame that feels friendly? (Also the faithfulness gate, §6.8.)*
2. **F2 — MAP, same viewport as F1.** Dots, bullets, line geometry, rail — no headings. *Answers: is the quiet abstract view a PLACE worth landing on (L-A's T1) or merely a toggle (L-B)? F1 beside F2 is the landing-density decision.*
3. **F3 — SECTOR of line M as a full place (L-A/L-B form), centered on n07@v2, history open:** v1's summary visible beneath v2, `superseded_because` naming line R's landing — "this is the changes we have made here" — with the stale-wakeup residual as a collapsed stub. *Answers: does the in-place update read — v1→v2 with the causing line named?*
4. **F4 — OUTLINE with the side panel open on n09.** Full card; the voice-transcribed quote byte-exact ("…It's in the m n t folder.") in pull-quote treatment; provenance chips; map + rail still visible, n09's rail marks lit. *Answers: panel vs modal — is this reading width enough while the map stays on screen?*
5. **F5 — L-C only: the same sector as F3, as an overlay lightbox** above the dimmed, unmoved OUTLINE hub, the other lines still legible beneath. *Answers: sector-as-place (F3) vs sector-as-overlay (F5) — the whole L-C question in one comparison.*
6. **F6 — chrome comparison strip:** three narrow crops of the same state (home, n07's sector one click away) under L-A / L-B / L-C — masthead, breadcrumb, and tier control only, map identical. *Answers: what switching cost each candidate charges in daily use — ladder tiers vs density toggle vs the hub's single crumb.*

## 5 · Standing non-negotiables (every frame obeys them)

- **The JSON is ground truth.** Titles, summaries, quotes, statuses, versions, spans render verbatim from `mock-d.json`. Never invent, paraphrase, or truncate node text. Quotes are NEVER ellipsized.
- **Quotes are byte-exact, including voice-transcription artifacts** — every "uh," every "m n t." Cleaning them up is paraphrase: a breach, not a favor.
- **n15's quote is assistant-articulated — mark it.** A small fixed tag, exactly "assistant's words — approved via gate," set apart from the pull-quote treatment Pi's own words get (n02, n09, n13).
- **Elide whole nodes, never shorten one.** Title-only and glyph-only are sanctioned densities; truncation is not.
- **Quoted vs inferred** always typographically distinct.
- **Corrections stay off the spine at rest** — residuals and superseded versions one interaction away. **Open questions loud at rest at every density** (n19).
- **Sanitization holds.** The source session names real machines; the mock says "the old laptop." Render only what the JSON carries; never reconstruct or invent identifiers.
- **Desktop-first**, generous landscape viewport; no mobile variants.
- **Renders differ where the spec says and nowhere else.**

## 6 · What Pi decides from these renders

1. **The layer structuring** — L-A / L-B / L-C. The round's gate; nothing above locks it.
2. **Landing density** — OUTLINE recommended (law-1-clean); choosing the quiet MAP as home requires a formal law-1 amendment.
3. **Panel vs modal** for node detail — panel is spec'd; modal is the standing veto alternative. F4 is the evidence.
4. **Rail at rest** — dots-only (spec'd) vs round-2-style mini-labels always on. Both are friendly; pick by eye.
5. **Ratify the 7 cuts** — board, yard strip, FIDS grid, version rings, 3-letter codes, glint, strapline+roundels. Anything missed in these frames? Each revivable on request; none returns by default.
6. **MAP hover-peek** — the transient one-node verbatim title on dot hover: useful, or hover-noise that undermines the density boundary?
7. **Transit-copy depth** — named moments ("single-line service") as captions under the kept empty-state license, or glyphs only?
8. **Mock faithfulness — new, and itself a gate:** does the drawn merge/diverge read TRUE to Pi's memory of the meditate session? If the map reads false to the person who lived the day, the mock or the drawing is wrong — say which before round 5.
