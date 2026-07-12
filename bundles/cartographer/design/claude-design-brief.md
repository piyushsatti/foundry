# cartographer — design brief for Claude Design

Four design directions for a session map. This document is self-contained; three data files (`mock-a.json`, `mock-b.json`, `mock-c.json`) are uploaded alongside it and are the exact data every render must use.

---

## 1. What cartographer is

Cartographer renders a **session map**: a consolidated, semantic tree of what happened in one AI working session (a Claude Code or claude.ai session). Every existing session tool is *log-faithful* — it renders chronology, so rework, dead ends, and corrections pile up as noise. Cartographer is *state-faithful*:

- **Rework UPDATES nodes instead of appending.** When the session revises an earlier conclusion, the node's version bumps (v1 → v2 → v3) and the old reading moves into that node's history. The map never grows a "second attempt" sibling.
- **The spine always reads clean top-to-bottom** — "what we did and how we approached it." A cold reader scanning only titles and summaries gets the true current story with zero rework noise.
- **Corrections and wrong turns are demoted behind nodes.** Dead ends, false alarms, and superseded versions are always *reachable* (one interaction away) but never on the spine at rest.
- **Provenance goes down to transcript spans.** Every node, residual, and quote carries pointers to the exact line ranges of the raw session transcript that produced it. Trust is earned per-node: the "prove it" gesture is always one hop away.
- **Decisions are verbatim.** Decision nodes anchor to exact transcript quotes — the user's own words — and the render must visibly distinguish quoted text from summary text the mapping engine inferred.

**The owner and reader is Pi** — one person, a developer, and a strongly *visual* person. This is a **human transparency tool**: it exists so Pi can understand and steer his own AI sessions at a glance, mid-session or end-of-day. It is not a dashboard for a team, not an analytics product, not an agent-monitoring console. The at-rest render must be readable by a tired end-of-day human with zero interaction. If the map doesn't help Pi read his own day, nothing else it does matters.

**Node vocabulary** (from the data files): every node has a stable `id`, a `version`, a `type` (`topic` | `move` | `decision` | `open-question`), a `title` (short spine label), a `summary` (current consolidated reading), and a `status` (`done` | `active` | `open` | `false-alarm` | `dead-end`). Nodes may carry `residuals` (folded wrong turns, each with its own provenance), `history` (superseded versions, each with a `superseded_because`), `provenance` (one or more transcript line spans), and — decision nodes only — a `quote` (verbatim text + line span). Topics are top-level; other nodes parent under them.

**Ground-truth rule: the JSON is the content.** Render actual node titles, summaries, quotes, and residual labels verbatim from the uploaded files. Never invent, paraphrase, or truncate node text — the realism of the data is the point of the exercise. Quotes especially are never ellipsized.

---

## 2. The data — three mock sessions

### Mock A — the orchestrator chat (`mock-a.json`)

A claude.ai session where Pi ran **three workstreams in one day**, hopping between them: transcript mining (topic `n01`), file consolidation (topic `n07`), orchestration design (topic `n13`). 17 nodes. In the raw transcript these interleave into a braid; the map must show **three clean spines** — each topic with its children grouped under it, regardless of interleaved provenance (topic nodes carry multiple disjoint line spans as proof).

What a correct render of A must show:

- Three top-level topics, children grouped under each. The core state-vs-log demonstration.
- **`n10` is the false-alarm test.** Mid-consolidation, old notes referenced a "session-lens repo" that couldn't be found; ~40 minutes of hunting (GitHub, two machines, a backup index) ended with the realization no code had ever existed. On the spine this is ONE node whose reading is the *conclusion* ("notes only — no code ever existed, nothing lost"); the entire hunt lives in its residual (lines 421–492), behind a click. If a reader sees the hunt at rest, the render fails.
- **`n03` (v2) and `n04` (v2)** are the updated-in-place tests among fifteen v1 siblings. `n04` is the high-stakes case: a *decision* (the buildout order) revised because of work in a *different topic* (the dependency pass during orchestration design) — its history must show the superseded ordering and the `superseded_because`.
- Four decision quotes: `n04`, `n06`, `n11`, `n15` — casual lowercase chat register, sitting adjacent to inferred summary prose. The quoted/inferred distinction must survive that adjacency.
- Three residual species: a false-alarm detour (`n10`), a tooling bug (`n03` — first tally double-counted), a rejected alternative (`n11` — the "attic" archive repo). One residual's span (`n11`, lines 548–570) nests inside another node's span (`n09`) — provenance affordances must tolerate overlap.
- Mixed statuses at rest: mostly `done`, `n07` is `active` (batch 2 pending), `n17` is `open`, `n10` is `false-alarm`.

### Mock B — the debugging session (`mock-b.json`)

A ~4-hour Claude Code session: a nightly Airflow DAG (`revenue_rollup_daily`) pages because its quality gate tripped — the rollup produced 94% fewer rows than normal, with no crash. 12 nodes, one topic (`n01`). The spine reads: triage (`n02`) → facts from logs (`n03`) → hypothesis (`n04`) → root cause (`n07`) → decision (`n08`) → fix (`n09`) → verify (`n10`) → closeout (`n11`) → open question (`n12`).

What a correct render of B must show:

- **`n04` is the flagship history test.** The hypothesis was *rewritten in place twice*: v1 "partial upstream landing" → v2 "scheduler-upgrade interval shift" → v3 (current) "upstream status-enum rename silently filters 94% of rows." Each superseded version has a `superseded_because` (the evidence that killed it) and its own provenance span — `n04` carries three disjoint spans, one per version. The history chain must be reachable, readable, and absent from the spine at rest.
- **`n05` and `n06` are the dead-end tests.** They are the investigations that killed hypothesis v1 and v2, status `dead-end`, parented *under* `n04`. At rest they render demoted — folded behind the hypothesis, never as inline chronological steps. A render that lays them on the spine as timeline entries fails this mock.
- **`n09` (v2)** — the fix was widened from daily-only to daily+weekly after a grep found a second copy of the filter. A second, smaller in-place update sitting near the flagship one.
- **`n08`** is the only quoted decision ("patch our side, don't wait on upstream," lines 878–881) — the verbatim/inferred contrast test in a single-quote session.
- Residuals behind clicks: `n02` folds a misread-alert wrong turn; `n07` folds a brief false suspicion of the quality check itself.
- **`n12` (open question — an enum-drift sentinel drafted but never built) stays loud at rest.** Open work is not mess; it must not fold away.

### Mock C — the mega-session slice (`mock-c.json`)

A long Claude Code session on a Python library ("tessel") that started as one refactor and chained into four work items: storage refactor (topic `n01`) → a test flake the refactor surfaced (`n07`) → a CI matrix drift the flake fix exposed (`n12`) → release prep (`n16`). 18 nodes. **One auto-compaction event fired mid-session** — the agent's context was rewritten at ~148k tokens, chronologically after node `n13` (transcript line ~610). The chronological pivot order was refactor → flake → CI → **[compaction]** → CI finish → refactor finish → release. The map does NOT show that zigzag.

What a correct render of C must show:

- **Four topics, each appearing exactly once.** The session returned to the refactor after the seam, but there is no "refactor, continued" node — the return manifests as `n01` bumping to v3 and new children (`n05`, `n06`) appearing under the original topic. This is the hardest state-vs-log case in the three mocks.
- **The compaction seam, visibly.** `session.compaction_events[0]` places it after `n13`. However drawn — a rule, a band, a marker, a shading change — it must convey "the agent's memory was rewritten here" without shattering `n01`, which straddles the seam (created before it, revised and completed after it). Note the structural trap: `n05`/`n06` sit spine-*earlier* than `n13` but are chronologically *post*-seam. A seam drawn as a naive horizontal cut through spine order lies. Each direction must find its own honest answer — a point-marker, a property painted on nodes/versions ("produced post-seam"), or both.
- **Two provenance flavors, visually distinguished.** Most provenance points at raw transcript spans (`c-mega-0630.jsonl`). Three entries point at `c-mega-0630.compact-1.summary` — the compaction summary — on `n01` (v3) and `n12` (v2), the two nodes updated *after* the seam about *pre*-seam events. Summary-derived provenance is a lower trust class (the engine could no longer see the raw content); identical chips would hide that. Style the difference: solid vs hollow, full vs dashed — a visible second-class citizenship.
- Version history behind clicks: `n01` (v3, two entries), `n04` (v2 — a "premature green" test run), `n07` (v2 — "we caused it" corrected to "it predates us"), `n12` (v2 — "flake fix incomplete" corrected to "independent matrix drift"). Every v1 here is a *wrong reading that got corrected* — exactly what belongs behind the node, never on the spine.
- Dead ends folded: `n09` carries two disproved hypotheses (SQLite WAL race; new-backend-introduced-it) as residuals; `n04` carries the premature-green residual.
- Quotes on `n03`, `n06`, `n14`, `n17`. Open question `n11` (a test-order sweep never run) findable and visibly open at the end.

---

## 3. Acceptance criteria — every direction must demonstrate all six

1. **Top-down readability at rest.** Zero interaction, the spine alone tells the story. Test: Mock B read cold in under 30 seconds yields *fail → investigate → root cause → fix → verify*. Mock A at rest shows none of: the double-count bug, the 40-minute repo hunt, the rejected attic repo, the original build order. Mock C at rest shows four topics whose summaries make the causal chain legible.
2. **Click-to-expand residual detail.** Every residual reachable in one interaction, with its own provenance. Test targets: A `n10`/`n03`/`n11`; B `n02`/`n07` plus dead-end nodes `n05`/`n06` folded under `n04`; C `n09` (two residuals)/`n04`.
3. **Node-history access.** Superseded versions with their `superseded_because`, behind interaction — not shown by default, not lost. Test targets: B `n04` (v1→v2→v3, the flagship) and `n09`; A `n03`/`n04`; C `n01`/`n04`/`n07`/`n12`. Bonus: the history view should support comparing non-adjacent versions (v1 vs v3), not just neighbors.
4. **Provenance affordance.** From any node AND any residual, a visible path to its raw transcript span(s). Must handle: multi-span nodes (A's topics have up to four disjoint spans; B's `n04` has three), residual-level spans, overlapping spans (A: `n11` inside `n09`), and — in C — the two provenance flavors (raw vs compaction-summary).
5. **Updated-in-place vs genuinely-new.** A versioned node (v2+) is visually distinct from its v1 siblings *without opening anything*, and the signal scales: `n04@v3` should read as more-revised than `n09@v2`. Updated nodes keep their spine position — position stability is itself part of the update signal.
6. **The compaction seam (Mock C).** Visible, honest, non-destructive: conveys "memory rewritten here," does not fragment straddling topic `n01`, and works with the summary-derived provenance marking.

**Standing rules across all directions:**

- **Quoted vs inferred, always.** Verbatim decision quotes (A: `n04`,`n06`,`n11`,`n15`; B: `n08`; C: `n03`,`n06`,`n14`,`n17`) render typographically distinct from engine-inferred summaries. Quotes are never truncated or paraphrased.
- **Open questions stay loud.** A `n17`, B `n12`, C `n11` must be visible at rest and clearly unresolved. Statuses (`done`/`active`/`open`/`false-alarm`/`dead-end`) need a legible at-rest vocabulary.
- **Long payloads never wreck rhythm.** Any expanded residual or raw span renders in a capped, scrollable well — vertical rhythm of the spine survives arbitrary payload size.

---

## 4. The four directions

Generate all four. They differ in **paradigm** — layout logic, metaphor, where things live — not in palette or styling accents. Do not let them converge.

---

### Direction 1 — "The Dossier" (literate document with a revision apparatus)

**Core metaphor:** the session as a continuously edited field report — a document whose sections are topics and whose entries are nodes, carrying an encyclopedia's revision apparatus (versions, citations) behind every block. The likely workhorse: it bets that *reading* is the fastest interface.

**Layout skeleton:** a single reading column (comfortable measure, ~680–760px) with a slim left rail (topic table of contents doubling as scroll map). Topic nodes are section headings with one-line topic summaries. Each child node is a compact entry: title line, 1–2 line summary, and a right-aligned metadata gutter (status mark, version chip, provenance footnote marks). Decision entries set the verbatim quote as an inset quotation block with its line span. Nothing else is visible at rest.

**How the demonstrables manifest:**
1. *Readability:* literally reading a document; entries hard-capped at title + short summary.
2. *Residuals:* a collapsed one-line callout under the owning entry — e.g. under A's `n10`: "▸ the hunt for a repo that never existed (lines 421–492)" — expanding in place into a capped well.
3. *History:* the version chip (`v3`) opens a per-node revision panel: superseded summaries newest-first, each with its `superseded_because` and span; any two versions comparable.
4. *Provenance:* footnote-style span chips per entry; clicking opens a side sheet with the span reference (and, in a real build, the raw lines). Multi-span nodes list multiple chips.
5. *Updated vs new:* position stability + version chip + a quiet changed-tint in the gutter. New nodes carry no chip. Chip prominence scales with version count.
6. *Seam (Mock C):* a full-width chapter rule — "— context compacted here —" — styled as structure, not error; AND summary-derived citations render as hollow "second-class" footnote chips wherever they occur, since in a consolidated document the rule alone cannot be honest about post-seam updates to pre-seam sections.

**Patterns to borrow (named):** Wikipedia's *page-plus-history-tab* (article shows only current state; complete revision list one tab away); the *"citation needed"-style badge* for summary-derived or unvalidated provenance; Figma's *named-versions vs autosave* discipline (only meaning-changing updates mint a visible version chip — no chip noise for cosmetic rewrites); GitHub's *resolved-thread collapse-to-stub* for residuals (one summary line, "show resolved," fully reversible); org-mode's *three-state density cycling* as a global control (overview: topics only → contents: topics + titles → all: full summaries) — this direction should explicitly explore density-at-rest via that cycle, rendering Mock B at both "contents" and "all."

**Hardest mock:** A. A document is a sequence machine; three interleaved workstreams must serialize into sections without lying, and `n04`'s cross-topic revision (a mining decision revised by orchestration work) must read naturally inside the mining section.

**Anti-patterns to avoid:** (1) prose sprawl — long engine-written paragraphs are where summarization drift breeds; entries stay telegraphic. (2) version-noise fatigue — a chip on every cosmetic rewrite teaches the reader to ignore chips. (3) chronology creep — never re-order entries by time; spine order is semantic.

---

### Direction 2 — "Spine & Rail" (central story column, margin residuals, persistent transcript ruler)

**Core metaphor:** an illuminated manuscript, or an arterial road with lay-bys: one central column is the story; everything demoted parks in the margin at the point where it forked; and the raw transcript is a **persistent skinny rail on the right edge** — a full-height ruler of the entire session onto which every node projects a bracket marking its span(s). Provenance as an always-visible instrument, not a buried link.

**Layout skeleton:** three vertical zones. Left margin: dim residual stubs and dead-end stubs, tethered to their spine node at fork height. Center: the spine — node cards top-down, topics as section headers. Right: the transcript rail — a compressed vertical map of the raw session (message-density texture), with span brackets projected from each node; selecting a node highlights its brackets, selecting a bracket opens the raw span in a detail panel that never navigates away from the map.

**How the demonstrables manifest:**
1. *Readability:* the center column alone is the clean read; margins at rest are dim stubs.
2. *Residuals:* margin stubs with one-line labels; expand in place in the margin. Mock B's `n05`/`n06` park as two stubs tethered to `n04`.
3. *History:* card edges peek from behind versioned spine nodes — stack depth = version count (`n04@v3` shows two edges behind it). Click fans the stack; each superseded card carries its summary + `superseded_because`.
4. *Provenance:* the rail IS the affordance. Multi-span nodes project multiple brackets (Mock A's topics visibly claim disjoint stretches of the day — the interleaving is *shown*, in the rail, while the spine stays clean; this is the direction's signature image). Overlapping spans (A: `n11` inside `n09`) nest as brackets naturally do.
5. *Updated vs new:* stack thickness (has history) vs flat single card; churn is legible pre-attentively without reading.
6. *Seam (Mock C):* the seam crosses the entire canvas — margin, spine, and rail — and the rail changes texture after it (different source: the post-seam context). Brackets projected from post-seam node versions onto pre-seam rail regions render dashed/hollow: summary-derived provenance, visibly weaker.

**Patterns to borrow (named):** Jaeger/OpenTelemetry *span-to-log deep link* (bracket click opens the transcript pre-scrolled and highlighted, one hop); Chrome DevTools/Perfetto *detail-on-select pane* (selection fills a persistent panel; the map never scrolls out from under you); *multi-span tethers* (several brackets converging on one node makes "this consolidates dispersed work" visible); Perfetto's *explicit discontinuity markers* for the seam — styled as a provenance annotation, not a tear.

**Hardest mock:** A. Three workstreams share one spine; margins and rail brackets get busy simultaneously, and the design must keep "clean center" from degrading into a braid.

**Anti-patterns to avoid:** (1) margin inversion — if a messy session puts more visual mass in the margin than the spine, the hierarchy has failed; margins are stubs, not content. (2) rail-as-timeline temptation — the rail is a provenance instrument; spine order stays semantic, never sorted to match the rail. (3) expert-density wall — the rail must read at a glance, not like a trace-viewer that assumes a trained operator.

---

### Direction 3 — "Transit Map" (metro diagram; the genuinely spatial direction)

**Core metaphor:** a tube map laid out vertically — each topic is a colored line, nodes are stations, progress flows downward along each line, dead ends are short spurs ending in a closed-station glyph, and cross-topic influence is an interchange. The bet: parallelism and where-things-connect are worth paying spatial complexity for.

**Layout skeleton:** a vertical canvas. One line per topic, running parallel, each with its color and name; stations sit on their line with flag labels (title + status mark); a left line-index legend doubles as the topic TOC and jump navigation. Deliberate, schematic geometry — 45/90-degree bends, even station spacing — never organic graph layout. Station detail (summary, provenance, history) lives in a select-to-inspect panel.

**How the demonstrables manifest:**
1. *Readability:* the line index gives the three-second overview (this is the overview-first direction); reading down any single line gives that workstream's story. For Mock A: three lines, glanceable in one screen.
2. *Residuals:* dead-end spurs — short thin stubs off a station ending in a dashed open circle ("closed station"). B's `n05`/`n06` are two spurs off the `n04` station; A's `n10` hunt is a spur off a station whose flag already states the conclusion.
3. *History:* revised stations accrete interchange-style rings — `n04@v3` wears two rings and is instantly the most-reworked point on the map. Click for the version panel.
4. *Provenance:* station panel lists span chips ("view this line section"); multi-span stations list several.
5. *Updated vs new:* ringed station vs plain dot — a pre-attentive, legend-friendly signal.
6. *Seam (Mock C):* a **fare-zone band** — a shaded horizontal band crossing all lines at once, which is what compaction actually does to a session (it hits every workstream simultaneously). Stations above and below keep their lines continuous — `n01`'s line crosses the band unbroken. Post-seam ring-revisions asserting pre-seam facts get hollow/dashed rings (summary-derived).

**The flagship move:** Mock A's `n04` — a mining decision revised because of orchestration-design work — renders as an **interchange**: a connector from the orchestration line into the `n04` station. Cross-topic causality made spatial; a log renderer could never show this.

**Patterns to borrow (named):** the *closed-station glyph* for dead ends; the *fare-zone band* for the seam; Miro-style *frames-as-TOC* (the line index is the session's table of contents); *chapter ticks on the scroll rail* if the canvas exceeds one screen (topic boundaries and the seam as labeled ticks).

**Hardest mock:** B — a single-topic session is one lonely line with spurs, and the entire multi-line vocabulary buys nothing. The direction passes only if that degenerate case still looks like a good product (a clean single spine with spurs) rather than an embarrassment. Secondary stress: layout stability — Mock C's `n05`/`n06` arriving late on topic 1's line must not re-route the geometry.

**Anti-patterns to avoid:** (1) re-layout on update — a map that re-routes when a node arrives or bumps reads as chaos; lines own fixed horizontal slots, stations only append or gain rings. (2) time as the y-axis contract — vertical position is spine order within a line, not the clock; otherwise C's post-seam children under topic 1 break the geometry. (3) decorative geography — no rivers, no whimsy; the schematic austerity is what keeps it a work tool.

---

### Direction 4 — "The Annotated Original" (transcript-with-marginalia; the null-hypothesis control)

**Core metaphor:** a Talmud page or an annotated screenplay: the raw transcript remains the primary substrate, and the map lives in a structured margin — bracket lines grouping transcript spans into semantic nodes, margin notes carrying the node faces. The inversion of the other three: map as overlay, not replacement.

**Why it's here — say this plainly:** cartographer's core bet is that the *map*, not the *log*, should be the primary surface. This direction is the strongest possible version of the opposite bet, rendered honestly, so the comparison is made visually rather than assumed. If this direction reads better than the other three, that is a finding, not a failure.

**Layout skeleton:** a wide transcript column, heavily folded by default — each bracketed region collapsed to a one-line summary bar ("42 messages — hypothesis testing") — plus a structured margin column of node notes. The margin column read top-down must function as the spine: titles, summaries, status marks, version ticks. Bracket lines physically connect each note to its span(s).

**How the demonstrables manifest:**
1. *Readability:* the margin column is the clean read; the substrate is ~90–95% folded at rest (for Mock C, show the fold stats honestly — e.g. "612 lines folded").
2. *Residuals:* bracketed regions whose margin note is a gray dead-end/false-alarm chip; the region auto-collapses; the chip reopens the raw exchange. Uniquely, the residual here IS its own raw evidence — no summary intermediary.
3. *History:* margin notes are versioned stickies — superseded notes stack behind the current one with edit ticks; fan to read v1/v2 with `superseded_because`.
4. *Provenance:* physically attached — the note sits on its span; provenance *cannot drift*. Multi-span nodes render as **multi-span tethers**: several bracket lines converging on one note (Mock A's topics; B's `n04` with three spans). Make the convergence beautiful — it is this direction's signature image, and it visualizes "this note consolidates dispersed work" better than any other direction.
5. *Updated vs new:* sticky stack + edit tick vs a single flat note.
6. *Seam (Mock C):* the substrate itself changes — the pre-seam transcript region is replaced by the compaction-summary block behind a seam banner ("context compacted here — raw transcript archived"); notes above the seam tether into the archived region, and post-seam notes about pre-seam events visibly tether into the *summary block* rather than raw lines — the two provenance flavors fall out of the geometry for free.

**Patterns to borrow (named):** Hypothesis/Google-Docs *quote-survives-anchor* (the note stores what it referred to, so it remains meaningful even if its span is archived); GitHub's *resolved-collapse* for folded regions; W3C-style *redundant anchoring* rendered as bracket + quoted text together.

**Hardest mock:** C — the transcript's mass dominates and the fold machinery is under maximum load; also the substrate is chronological while the map is consolidated, so Mock A's margin notes cannot group by topic without fighting their own anchors (`n03`'s two spans sit ~350 lines apart with another topic's work between them). **Render that fight honestly** — the degree to which the margin fails to group topics is exactly the evidence this control exists to produce.

**Anti-patterns to avoid:** (1) unfolded-by-default transcript walls — at rest, the substrate is almost entirely collapsed or the direction is unusable. (2) demoting the margin to labels — margin notes are full nodes (versions, statuses, quotes, history), not captions. (3) hiding the paradigm's cost — do not secretly reorder or de-interleave the transcript to make topics group; the substrate's chronology is the whole point of the control.

---

## 5. Instructions to Claude Design

1. **Generate each direction against Mock B first.** It is the smallest and densest test (12 nodes, a 3-version history chain, two dead ends, two residuals, one quote, one open question). Then check the direction survives Mock A (parallel topics, false alarm, cross-topic revision) and Mock C (scale, pivots, the seam). A direction that only works on its favorite mock fails.
2. **Differ in paradigm, not palette.** If two directions could be transformed into each other by restyling, they have converged — re-diverge. Layout logic, where residuals live, how provenance is reached, and what the first three seconds show must all differ.
3. **Desktop-first.** This is a desktop working tool; design for a generous landscape viewport. No mobile variants needed in this round.
4. **Density at rest is a design variable — explore it per direction.** What the map shows with zero interaction (everything folded vs full summaries vs overview) is the thing Pi will feel first. Where a direction has a natural density dial (Direction 1's overview/contents/all cycle; Direction 3's line-index vs full canvas), show two settings of it.
5. **The JSON is ground truth.** Render real titles, summaries, quotes, statuses, version numbers, and line spans from the uploaded files. Never invent node content; never truncate a quote. If space forces elision, elide whole nodes from a zoomed-out view rather than shortening any node's text.
6. **Show interaction states statically where needed.** For each direction, at minimum: the at-rest view of Mock B, plus one view with a residual expanded, a history panel open (use `n04`), and a provenance affordance active — annotated callouts are fine.
7. **What happens after this round:** one direction (or a hybrid) gets picked by Pi visually and iterated; a later phase adds an annotation/review layer (select nodes and assumptions, comment, submit as one packet — GitHub-PR-review-style, including an outdated-when-node-changes mechanic and Gerrit-style resolved-stays-behind history). You do not need to design that now, but do not paint any direction into a corner where node-level selection would be impossible.
