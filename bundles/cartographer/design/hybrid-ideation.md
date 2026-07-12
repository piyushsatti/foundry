# Gate 1 round 2 — three Spine & Rail × Transit Map hybrids

*Internal doc for the orchestrator and Pi. The upload artifact for Claude Design is `claude-design-iteration-2.md` (self-contained). Round-1 verdict (Pi, 2026-07-05): Dossier and Annotated Original killed; Dossier's text density salvaged; Spine & Rail loved for the flow-of-changes side scan; Transit Map loved for structural clarity; the ask is a UML-blobs-and-connectors hybrid of the two survivors.*

## The four signals every concept must carry

1. **Text-bearing node blobs with visible connectors** — nodes are text-FIRST cards whose title + summary read at rest, with an internal heading→body hierarchy. Not dots, not flags, not labels.
2. **Dossier-grade glanceable hierarchy** — heading level → subheading level → paragraph, scannable top-down (the explicit salvage from the killed Dossier).
3. **An always-visible flow-of-changes rail** — the fast vertical scan-and-scroll Pi loved in Spine & Rail.
4. **Transit-Map-grade structural clarity** — workstreams as legible lines/paths.

**The standing objection each concept must answer:** the round-1 catalog killed mind-map and expedition-map paradigms for **layout instability** (ideation-paradigms.md §11, §16 — free 2D placement forces invented geography; re-layout on update reads as chaos). Blobs-with-connectors flirts with exactly that kill. Every concept below therefore states a stable layout discipline up front: connectors are never free-angle, nothing ever re-routes, and each concept names the single law that fixes every element's position.

**A tension the signals hide, resolved three ways.** Signals 1–2 want text at a comfortable reading measure; signal 4 wants N parallel paths. Full-measure cards × N parallel lines exhausts any viewport. Each concept resolves it by choosing ONE place where text lives at full measure and compressing the map vocabulary everywhere else — which is also what makes the three structurally distinct rather than palette variants. A second ambiguity: round-1 Spine & Rail's rail was a *transcript-provenance ruler*, but Pi described it as "the flow of changes." The concepts deliberately split the interpretations — 1 keeps the transcript ruler and adds change ticks; 2 rebuilds the rail as an explicit change-event register; 3 makes the map itself the change scanner and demotes always-visible provenance to one hop.

## The shared node blob (all three concepts)

The UML-style card, anatomy fixed across concepts (this is the Dossier salvage — steal: paradigm 1's *position-stability + version chips*; pattern 19 *quote-survives-anchor* for the inset):

- **Header band** — type glyph, **title** (the heading), status mark, version chip (chip only when v ≥ 2 — Figma *named-versions vs autosave* discipline, pattern 10).
- **Body** — the summary, 1–3 lines, verbatim from JSON (the paragraph level).
- **Quote inset** — decision cards only: the verbatim quote, quotation-styled, its line span attached; never truncated.
- **Footer strip** — provenance chips (one per span; hollow/dashed for summary-derived), residual stubs (GitHub *resolved-thread collapse-to-stub*, pattern 4), expanding into capped scrollable wells (Jupyter *scrolled outputs*, pattern 8).

Topic nodes render as larger section-header cards (title + one-line topic summary) — the subheading tier between session title and child cards.

---

## Concept 1 — "The Threaded Spine"

*One full-measure column of cards; the metro squeezed into a thread gutter; the transcript ruler kept.*

**Governing paradigm: Spine & Rail** (paradigm 3 — spine + marginalia + persistent rail). Transit Map contributes instruments only: topic lines, station docking, rings, closed-station spurs, the interchange. A third ancestor is knowingly revived as pure geometry: the **git-graph gutter braid** (paradigm 5, the round-1 top runner-up — directions-rationale.md said revive if Pi wants something more technical; here its braid geometry returns without its git-literacy tax).

**Layout skeleton — three fixed zones.** (a) Left: a **thread gutter** (~80px). Every topic owns a fixed vertical slot for the full session height; its colored line runs straight down that slot — bold with station dots through its own section, thin and dim elsewhere. Each card docks to its topic's line via a short horizontal stub to a station dot at card top-left. (b) Center: the card column (~680px measure), cards in spine order, topics as section headers. (c) Right: the **rail** — Spine & Rail's full-height transcript ruler with span brackets (paradigm 3's signature steal), now also carrying **change ticks**: every version bump paints a tick at the span that produced it (n04's three spans = three ticks on one node's thread color). Scrolling the rail is the flow-of-changes scan.

**Stability discipline (the objection answered):** document flow is the law. Cards occupy a single pinned column and never move except by semantic spine order; gutter lines are straight vertical runs in fixed slots; connectors are confined to the gutter — vertical runs plus short horizontal docking stubs, nothing free-angle, nothing crossing text. An update adds a ring and a tick; an insertion adds a row. Nothing re-routes, ever.

**Steals, named:** transcript rail with span brackets (paradigm 3); git-graph braid geometry (paradigm 5); rings/closed-station/interchange (paradigm 4); *span-to-log deep link* (pattern 17); *detail-on-select pane* (pattern 16); *page-plus-history-tab* (pattern 9); Gerrit *any-pair version diff* (pattern 13); Perfetto *visible seam as provenance annotation* (pattern 33).

**The flagship image:** Mock A's `n04` — the orchestration line physically runs up its gutter slot and plugs into the `n04` card's station dot in the mining section. Cross-topic causality as a literal drawn connector, with zero 2D canvas.

**Six criteria:** (1) *At rest* — the card column reads like the Dossier did: topic headers, title + summary cards, quote insets; the gutter braid gives pre-attentive structure. (2) *Residuals* — a spur stub off the station dot ending in a closed-station glyph, one-line label under the card ("▸ the hunt for a repo that never existed — lines 421–492"); B's `n05`/`n06` are dimmed half-height spur cards folded under `n04`, collapsed to stubs at rest. (3) *History* — rings on the station dot (n04@v3 wears two) + version chip; click opens the revision panel, newest-first with `superseded_because`, any two versions diffable. (4) *Provenance* — rail brackets per card; multi-span topics visibly claim disjoint stretches of the day; overlaps (A: `n11` inside `n09`) nest as brackets do; bracket click = deep-linked span in the detail pane. (5) *Updated vs new* — ring count + chip + position stability + rail ticks; n04@v3 outweighs n09@v2 at a glance. (6) *Seam* — a full-width rule crossing gutter, column, and rail; rail texture changes after it; summary-derived brackets and chips render dashed/hollow; **the gutter threads cross unbroken** — C's `n01` thread runs straight through the seam, the strongest possible "no shattered straddler."

**Stress mock: A.** Three lines braiding, a full-document-height interchange connector, and a busy rail all at once. **Honest expected failure:** the gutter degenerates into exactly the git-graph spaghetti the runner-up was cut for, and the `n04` interchange connector — spanning most of the page — either reads as clutter or gets scrolled past unseen.

**Structurally distinct because:** the map is *subordinated* — compressed into a gutter annotation on a governing text column; the other two concepts give the diagram progressively more real estate.

---

## Concept 2 — "The Switchyard"

*The canvas governs; the stations are the cards; a rail-yard of parallel tracks with text-bearing rolling stock.*

**Governing paradigm: Transit Map** (paradigm 4). Spine & Rail contributes the rail (rebuilt as a change register) and the detail-on-select chassis. The Dossier salvage contributes the card interior.

**Layout skeleton.** Fixed-width **topic lanes** (~360–420px), one per topic, left-to-right in spine order; each lane headed by its topic card, pinned on scroll (Perfetto *pinned tracks*, pattern 39; Miro *frames-as-TOC*, pattern 32 — the header row is the three-second overview). The topic's colored line runs straight down its lane through each card's docking dot; cards stack in spine order. Dead ends are **spur cards** — shifted a half-step off the line onto a short spur ending in the closed-station glyph, rendered at stub density. Cross-topic influence is an **interchange connector**: an orthogonal 45/90° run from the source lane to the target card's docking dot (A: orchestration lane → `n04` in the mining lane). Connectors carry no invented prose — causality lives in the topic summaries.

**The rail:** left edge, full height — the **change register**. A compact ledger of change events in *transcript* order: node created, version bumped, seam — each entry a tick + mini-label in its lane's color, positioned by the start line of the span that produced it. Scrolling it is the flow-of-changes scan Pi loved, and it is where the chronological braid lives (A's interleaving is *shown* in the register while the lanes stay clean) — chronology as a lens, never the canvas's sort order (pattern 20's discipline; anti-patterns list, ideation-patterns.md).

**Stability discipline:** lanes own fixed horizontal slots — Transit Map's own round-1 anti-pattern rule, now the governing law. Cards only append downward within their lane or gain badges; late-arriving children (C: `n05`/`n06` post-seam) insert at their spine position and shift one lane only; interchange connectors run orthogonally at the target card's y. No force layout, no re-route, no free angles.

**Steals, named:** fare-zone thinking relocated honestly (see seam), closed-station glyph, rings (paradigm 4); *detail-on-select* (pattern 16); *span-to-log deep link* (pattern 17); org-mode *three-state density cycling* per lane (pattern 3); *chapter ticks on the register* (pattern 43); Gerrit *any-pair diff* (pattern 13).

**Six criteria:** (1) *At rest* — read down one lane for one workstream's story in full sentences; read the pinned header row for the session in three seconds; Mock B degrades to a single clean lane of cards — a good product, not an embarrassment. (2) *Residuals* — spur cards at stub density, one interaction to a capped well; B's `n05`/`n06` are two spurs off `n04`'s dot. (3) *History* — rings on the docking dot + chip; version panel in the persistent right detail pane, any-pair diff. (4) *Provenance* — footer chips per span; selecting a card highlights the register entries its spans produced (multi-span `n04` lights three disjoint register stretches — the interleaving made visible without touching the lanes); overlapping spans coexist as register highlights. (5) *Updated vs new* — ring count on dots; per-lane register tick density gives pre-attentive churn ("the mining lane changed a lot late in the day"). (6) *Seam* — **the fare-zone band is deliberately NOT drawn across the lanes**, because lane-y is spine order and a horizontal cut would lie about `n05`/`n06` (mock-c.md design question 1, the structural trap). Instead: a full-width seam bar in the change register at its true chronological position, plus a painted property on the canvas — post-seam cards and versions carry a seam tint/badge, and summary-derived chips render hollow. Point-marker where time is real; property where it isn't.

**Stress mock: C.** Four lanes squeeze the measure to ~340px; cards wrap tall; lanes end at uneven heights. **Honest expected failure:** horizontal budget exhaustion, plus the false-correspondence read — a cold reader infers same-height = same-time across lanes, which is untrue; and the causal chain refactor→flake→CI→release must be caught from the header row's summaries or it is lost.

**Structurally distinct because:** it is the only concept where the *canvas* governs and the text lives inside the map — the cards are stations, not a column beside one.

---

## Concept 3 — "Strip & Ledger"

*A true schematic strip map and a full-text ledger as peer registers, locked row by row.*

**Governing paradigm: a third discipline genuinely governs — the row register.** Neither parent's layout survives intact: one shared vertical sequence of rows is the single law, and both panes obey it. The real-world anchor is the in-car transit strip map beside its stop list. Transit Map contributes the entire left register's vocabulary; Spine & Rail contributes the structural DNA (a persistent parallel rail scanned vertically) — *inverted*: the rail is now the map, and the transcript retreats to the detail pane.

**Layout skeleton — two row-locked registers.** Left (~220–260px): the **strip** — a genuine schematic transit diagram: topic lines in fixed slots, 45/90° bends only, stations as dots with rings, spurs with closed-station glyphs, interchange links, the seam treatment. No text beyond line names. Right (~700px): the **ledger** — the full card register, one card per station, top-aligned to its station's row; topics as header rows. The connector between blob and diagram is the row itself — station k and card k share a y-band, so zero free-form connectors ever cross the gap. One scroll drives both.

**The rail:** the strip *is* the flow-of-changes rail. Rings (version counts), spurs (dead ends), the loud open-question marker, and the seam band are all legible in one skinny column — Pi's fast vertical scan happens on the strip, his reading on the ledger, in a single scroll. **The concept's bet, stated plainly:** what Pi loved in Spine & Rail was the *scannable change flow*, not the transcript ruler per se — so always-visible provenance (the very thing round-1 picked Spine & Rail for) is demoted to one hop: footer chips → detail pane → deep-linked span. If that bet is wrong, this concept loses to Concept 1.

**Stability discipline:** the row registry fixes everything. Lines are straight vertical runs in fixed slots; when a row grows (a residual well expands), the run *stretches* — it never re-routes, because there is nothing to route around. Insertions add a row inside their topic block. Station geometry is a pure function of row order + topic slot.

**Steals, named:** the full paradigm-4 glyph set (rings, spurs, interchange, band); *minimap-with-brush* (pattern 37) — a condensed pinned mini-strip for jumping when the ledger exceeds ~2 screens, with *chapter ticks* (pattern 43) for topic boundaries and the seam; *detail-on-select* (pattern 16); *span-to-log deep link* (pattern 17); Gerrit *any-pair diff* (pattern 13); Perfetto *seam as provenance annotation* (pattern 33).

**Six criteria:** (1) *At rest* — the strip is the three-second overview (Transit's line-index promise, but always visible and geometric, not a legend); the ledger reads top-down as the Dossier did. (2) *Residuals* — spur + closed-station glyph on the strip, stub line under the owning card on the ledger; either side expands the row into a capped well. (3) *History* — rings on the station, chip on the card; either opens the version panel; any-pair diff. (4) *Provenance* — footer chips per span, one hop to the deep-linked pane; multi-span nodes list chips; overlaps live in the pane; the strip carries none (the honest cost, per the bet above). (5) *Updated vs new* — ring count scans pre-attentively down the strip (n04@v3's double ring vs n09@v2's single is the whole point of the left register); chips + position stability on the ledger. (6) *Seam* — a full-width **seam row** across both registers after `n13`'s row, labeled honestly ("memory rewritten here — some rows above were produced after this point"), *plus* post-seam paint: stations and versions produced post-seam get a distinct fill, summary-derived chips render hollow. Marker and property together (mock-c.md design question 1's both-answer); `n01`'s line crosses the seam row unbroken.

**Stress mock: B.** One topic = one straight line: the strip carries two spurs, two ringed stations, one loud open marker — and ~200px of width to justify. **Honest expected failure:** on a single-topic session the strip reads as a decorated scrollbar rather than a map; card pitch (~120px) versus station pitch stretches the geometry until it stops looking like transit at all — at which point the concept collapses into Concept 1 with extra width and weaker provenance.

**Structurally distinct because:** it is the only concept where map and text are *peers* — a complete diagram readable alone, row-locked to a complete document readable alone, with rows as the only connectors.

---

## Distinctness matrix

| | 1 Threaded Spine | 2 Switchyard | 3 Strip & Ledger |
|---|---|---|---|
| **What governs layout** | document flow of one card column | fixed topic lanes on a canvas | the shared row register |
| **Where the text lives** | the column is the surface; map compressed to a gutter | inside the map — cards are the stations | right register, peer to the map |
| **What the rail is** | transcript ruler + change ticks (right) | chronological change register (left) | the strip itself is the change rail |
| **Map vocabulary status** | subordinate annotation | the governing canvas | peer register, readable alone |
| **Provenance at rest** | always visible (brackets) | register highlights + chips | one hop (chips → pane) |
| **Seam treatment** | full-width rule, threads unbroken | register bar + painted property, no canvas band | seam row + painted property |
| **Stress mock / failure** | A / gutter spaghetti | C / lane budget + false correspondence | B / strip as decorated scrollbar |

If two of these converge in render, the failure is the renderer's, not the specs' — the iteration-2 prompt instructs re-divergence exactly as round 1 did.
