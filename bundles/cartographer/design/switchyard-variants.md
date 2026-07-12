# Gate 1 round 3 — four structural variants on the Switchyard chassis

*Internal doc for the orchestrator and Pi. Round-2 verdict (Pi, 2026-07-05): the Switchyard is THE direction — Threaded Spine and Strip & Ledger cut, their instruments revivable as lenses. This round iterates structure ON the chosen chassis, not against it. Two round-2 findings govern everything here: the hard requirement ("when a conversation has many parallel things it's working on, I want each of those streams to be very clear") and the critique ("a lot of visual clarity is being sacrificed there for text… not enough icons… not enough feel and creative expression"). Pi seeded variant 1 himself.*

## The chassis (fixed unless a variant says otherwise)

From `hybrid-ideation.md` §Concept 2, the parts every variant inherits: fixed-width topic lanes left-to-right in spine order, each headed by its topic card, pinned on scroll; the topic's colored line running straight down its lane through each card's docking dot; cards stacking in spine order; dead ends as spur cards at stub density off a closed-station spur; cross-topic influence as orthogonal 45/90° interchange connectors carrying no invented prose; the left-edge **change register** — change events in transcript order, chronology as a lens and never the sort order; the seam as a register bar plus painted property, never a band across the lanes; the shared node-card anatomy (header band / body / quote inset / footer strip); detail-on-select pane (pattern 16) that never navigates away.

**The standing objection, still standing.** Round 1 killed mind-map and expedition-map for layout instability (ideation-paradigms.md §11, §16 — free 2D placement forces invented geography; re-layout on update reads as chaos). Variant 1 walks straight back into that territory on Pi's instruction, so it — and every other variant — states its stability law explicitly: what fixes every position, and the guarantee that **the engine never moves or re-routes anything**. The only hand allowed to move geometry is Pi's.

**Non-negotiables carried unchanged** (claude-design-iteration-2.md): JSON is ground truth; node text verbatim; quotes never ellipsized; elide whole nodes, never shorten (title-only is a sanctioned altitude, truncation is not); corrections off the spine at rest; open questions loud at rest; Mock B first; desktop-first.

---

## Variant 1 — "The System Map" *(Pi's seed, mandatory)*

*Switchyard units placed on an infinite pannable/zoomable canvas — spatial arrangement as a thinking surface, not as data.*

**What changes vs baseline.** The viewport-bound row of lanes becomes a canvas of **units**. A unit is one topic's lane-cluster — header card, line, docked cards, spurs — internally identical to a baseline lane. The canvas arranges units; it never reaches inside one. Pi can drag units, group them into **named regions** (a lasso'd, labeled, color-washed area — Miro frames, pattern 32: meaning on the canvas is *declared* by a label Pi typed, never inferred from proximity), and tag units — his "different tags in this 2D space so we know how to think about the reasoning." Clicking any node loads the persistent side panel with the full card, history, provenance, quote — detail-on-select (pattern 16), never navigate away. **Untouched:** everything inside a unit — card anatomy, spine-order stacking, spur treatment, docking dots, rings, the seam-as-painted-property, quoted-vs-inferred typography.

**The stability law (the hard part, answered in four clauses).**
1. *Deterministic seed layout.* Units spawn on a fixed-pitch grid, one column per topic, in spine order, single row — which means **the canvas at rest, zoomed to fit, IS the baseline Switchyard**. No force layout, no packing algorithm, no aesthetic optimizer. Same JSON, same seed positions, every time.
2. *Drags are durable curation.* This is the incident.io curate-pins pattern (ideation-patterns.md §2), promoted from Phase 2 interaction to layout law: Pi's placements are pins the engine can never silently overwrite. A reducer update changes a unit's *contents* (cards append downward, badges accrete, rings grow) — never its canvas coordinate. New topics enter at the next free seed slot, displacing nothing.
3. *Internal geometry stays lawful.* The baseline lane law governs inside every unit: cards append downward in spine order, the line never bends, spurs stay half-step offsets. The canvas has no jurisdiction over a unit's innards.
4. *Inter-unit connectors degrade honestly instead of re-routing wildly.* In seed layout, interchange connectors render exactly as baseline (orthogonal, at the target card's y). Once Pi's curation moves units apart, a connector that can no longer route cleanly (crossing units, exceeding a length threshold) collapses to a **paired interchange-port glyph** on both endpoints — select either port and the full orthogonal link draws temporarily with the partner highlighted. Re-routing happens only at drop time of a Pi-initiated drag, never on engine update.

**Where the register lives.** Viewport-pinned to the left edge — it is an instrument, not geography, so it does not live on the canvas. One global register (per-unit registers would shatter the chronological braid, which is the register's entire job). Clicking a register entry pans/zooms the canvas to the unit and flashes the card — the register doubles as the canvas's navigation spine.

**The at-rest three-second read.** "Home" is always zoom-to-fit of the seed-or-curated layout. At fit altitude, units render icon-forward: topic header card at full text, child cards compressed to title-row-or-glyph density (a sanctioned altitude — whole fields elided, nothing shortened). The read is the baseline's pinned header row, now with Pi's own regions and tags as the second sentence. This variant is half a product without variant 2; see compatibility.

**Six criteria — only the diffs.** (1) *At rest:* fit-zoom overview as above; the danger is that "home" requires a gesture — the app must open at fit, always. (4) *Provenance:* unchanged mechanics; selecting a card still lights its register entries, and the register now also *locates* the card spatially. (6) *Seam:* identical — register bar at true chronological position, seam tint painted on post-seam cards/versions across all units regardless of where Pi dragged them; hollow chips for summary-derived provenance.

**Stress mock: B.** One topic = one lonely unit on an empty prairie; pan and zoom buy nothing. It must degrade to a fit-zoomed single switchyard indistinguishable from baseline — if Mock B renders with visible "canvas-ness" (grid dots, empty vastness, a minimap for one unit), the variant fails its floor. **Second honest failure: invented geography creeping back in** — not from the engine (the law forbids it) but from Pi's own hands: a reader (including future-Pi) reads meaning into proximity that nobody declared. Mitigations: regions are the only sanctioned meaning-carrier (labeled, explicit); curation is per-viewer state stored outside the map artifact (per pattern 39's note), so the map itself stays viewer-independent and exportable in seed order.

**Visual feel raised by:** territory. Zoom, region washes, colored lines converging at ports, the fly-to gesture — the map starts *feeling* like a rail network diagram of the day's thinking, with zero invented prose and zero shortened text: expressiveness comes entirely from altitude, color, and glyph, never from touching the words.

**Composes with:** variant 2 (near-mandatory pair — canvas zoom and semantic zoom are the same gesture), variant 4 (board pins above the canvas, one row per unit). Tension with variant 3 (see its entry).

---

## Variant 2 — "The Flyover"

*Four designed altitudes on one zoom gesture — icon-first metro glyphs at the top, raw transcript at the bottom; zoom-as-provenance revived as the Switchyard's lens.*

**What changes vs baseline.** The single at-rest density becomes a ladder of exactly four **snap altitudes** — discrete designed views, not continuous scaling (pattern 41's break taken seriously: each level is its own layout, so ship four and refuse the in-betweens):
- **A3 — glyph altitude.** The round-1 Transit Map face Pi loved, reborn as a view: lanes compress to schematic lines; stations are pure icon — type glyph, status color, version rings, spur stubs, a beacon on open questions. Topic titles only. This is the "more icons, more feel" answer in its most concentrated form.
- **A2 — title altitude.** Cards as title-only rows on their docking dots, verbatim and unabridged (the sanctioned elision: whole summaries omitted, no text shortened).
- **A1 — card altitude.** The baseline at-rest Switchyard, unchanged.
- **A0 — bedrock.** Zooming *into* a single card past full detail opens its deep-linked transcript span in place (span-to-log, pattern 17), map still visible around it. This is directions-rationale.md's explicit revival clause executed: zoomable-icicle's zoom-as-provenance grafted onto the chosen direction as a lens — keep zooming and you hit ground truth.

**Untouched:** all geometry, the register, the seam treatment, card anatomy at A1, interaction chassis.

**Stability law.** Zoom changes representation, never position. Every card's docking dot — lane-x from the fixed slot, y from spine order — is the altitude-invariant anchor; representations grow and shrink *around their dot*. Lane pitch per altitude is a fixed constant (A3 compresses lane width by a fixed ratio, deterministically), so the A3↔A1 transition is a pure scale-about-anchors animation with zero reflow. Nothing re-routes; connectors exist at every altitude, drawn to the same dots.

**Six criteria — only the diffs.** (1) *At rest:* default altitude is A1 (Mock B must open readable, not as glyphs); A3 is one gesture up. Open questions stay loud at *every* altitude — the beacon is an A3 glyph, not an A1 luxury. (3) *History:* rings are the A3 churn signal (n04@v3's double ring vs n09@v2's single is the whole point of glyph altitude). (4) *Provenance:* gains its strongest form — A0 makes "prove it" a zoom, not a click. (6) *Seam:* the painted seam tint must survive down to A3 (tinted station fill), or the seam vanishes exactly at the overview altitude where a tired reader lives.

**Stress mock: C.** Four lanes at A3 must still tell refactor → flake → CI → release from topic titles alone. **Honest failure:** the mid-altitude dead zone — A2 is neither glanceable like A3 nor readable like A1, and the causal chain (which lives in topic *summaries*) is invisible above A1; if the answer is "keep topic summaries rendered at A2/A3 while children go glyph," the topic cards grow into billboards and the schematic look is compromised. Render the compromise honestly.

**Visual feel raised by:** the glyph vocabulary finally gets a stage. A3 is the most iconographic surface in the whole design program — status color, rings, spurs, beacons doing pre-attentive work with zero sentences on screen, and none of it violates the text rules because A3 elides whole fields, never shortens one.

**Composes with:** variant 1 (the same zoom gesture drives canvas altitude and card altitude — together they are one continuous system-map-to-bedrock descent), variant 3 (focus is per-lane altitude assignment — see below), variant 4.

---

## Variant 3 — "The Working Line"

*Hoist one lane to full reading measure; the others compress to schematic strips — one stream deep, all streams visible.*

**What changes vs baseline.** A per-lane **focus mode**. Click a lane's header (or its departures-board row, variant 4) and that lane widens in place to a full Dossier reading measure (~680px) — summaries breathe, quote insets render wide, residual stubs get room. Every other lane compresses in place to **strip density**: the Strip & Ledger instrument revived exactly as decisions.md licensed — a skinny schematic line carrying station glyphs, rings, spur stubs, open-question beacons, seam paint, and nothing else. A breadcrumb/tab row (pattern 35's zoom-with-breadcrumb) switches focus; Escape returns to equal lanes. Interchange connectors into the focused lane stay drawn — source becomes a strip station, target a full card dot — and become *more* legible under focus, because the focused lane finally has the width to receive them. **Untouched:** at-rest default is equal lanes (baseline); the register; the seam; card anatomy.

**Stability law.** Lanes never reorder and never move vertically: focus changes a lane's **width allotment only**, from a two-value system (full measure / strip width) — no continuous resize, no drag-to-resize. X-order is invariant (the focused lane widens in place; flanking strips compress in place), y is spine order as ever, and within-lane geometry is untouched at both widths. Deterministic: the same focus state always produces the same layout.

**Six criteria — only the diffs.** (1) *At rest:* unchanged — focus is an interaction, so the tired-end-of-day zero-interaction read is the baseline's. This is deliberate: the hard requirement says each parallel stream must be clear, so equal lanes stay the resting state and focus is the *reading* state. (2) *Residuals:* on strips, spurs are glyph-only — one click to the capped well as ever. (5) *Updated vs new:* the strips deliver Strip & Ledger's best trick safely — ring counts scanning pre-attentively down a skinny line — without its fatal bet, because the strip is never the only surface; the full cards are one focus-click away.

**Stress mock: A.** Three genuinely parallel streams that Pi hops between all day. **Honest failure: focus-thrash.** If following the day requires cycling focus lane-to-lane-to-lane, reading becomes interaction-gated — precisely what the at-rest mandate forbids — and each switch reflows two lanes' widths, taxing spatial memory (the DOI warning, pattern 38's break: without stable landmarks, a visual person loses his sense of place). The strips are the mitigation (the unfocused streams never vanish, unlike hoisting), but render the thrash honestly: Mock A with focus on the consolidation lane while the mining lane's ringed stations silently demand attention.

**Visual feel raised by:** contrast. One lane of full typographic richness flanked by pure schematic glyph-work is the strongest single image in this family — the text-density salvage and the metro iconography on screen simultaneously, each at its best density, neither compromising the other.

**Composes with:** variant 2 cleanly — focus mode *is* per-lane altitude assignment (focused lane at A1, others at A3), so V2+V3 are one mechanism with two triggers (global zoom, per-lane hoist). With variant 1, in-place widening fights Pi's curated unit positions (a widening unit could collide with a hand-placed neighbor, and the engine may not move that neighbor — the law forbids it); if composed, focus on canvas must open as an **overlay lightbox** over the unit, not in-place growth. With variant 4, the board is the natural focus switcher.

---

## Variant 4 — "The Departures Board"

*A pinned header instrument styled as the station departures board — one row per lane: status, churn sparkline, open-question beacons — the three-second read made iconic; the minimap promotion folded in.*

**What changes vs baseline.** The pinned topic-header row (already the baseline's three-second overview) is rebuilt as a full **instrument band** across the viewport top, in departures-board visual language — one row per lane, in lane order, lane color as the row's livery:
- **topic title** (verbatim) and status mark;
- a **churn sparkline** — that lane's change-register ticks projected onto a tiny transcript-time axis ("the mining lane changed a lot late in the day" becomes a literal graph; per-lane sparklines and the register are the same data, one global and chronological, one per-lane and pre-attentive);
- **open-question beacons** — count and glow for any `open` node in the lane (n17, n12, n11 stay loud from the board even when scrolled out of view — the "open questions loud" rule gets a permanent home that scrolling cannot defeat);
- version-churn count and a seam tick where the lane has post-seam content.

Below the board, a thin **yard strip with brush**: the whole session in spine order with chapter ticks at topic boundaries and the seam (patterns 37 + 43) — drag the brush to scroll the yard. This is directions-rationale.md's promotion clause executed: round-2's Mock C stress (lanes overflowing one screen at uneven heights) is exactly the "renders overflow" trigger that promotes minimap-with-brush into Phase 1. **Untouched:** everything below the board — lanes, cards, register, seam, connectors.

**Stability law.** The board is a viewport-pinned instrument with **zero canvas geometry** — rows mirror lane order (fixed slots), never reorder, never affect lane layout; it renders from the same JSON, adds nothing. One honesty seam inside the instrument itself: sparkline x-axes are *transcript* order (they are register projections — chronology as a lens, which is the register's licensed job), while the brush strip is *spine* order (pattern 37's break, respected: a time-axis scroll map would quietly re-impose the log). The two axes are visually distinct on purpose — sparklines are per-row decoration you click (click a tick = click that register entry, fly to the node); the brush is the one draggable scroll surface, and it speaks spine.

**Six criteria — only the diffs.** (1) *At rest:* the three-second read moves up into the board and gets stronger — session title, N lanes, statuses, churn shapes, open counts, seam presence, all before reading a sentence. (5) *Updated vs new:* churn gains a pre-attentive per-lane signal that the register (global, interleaved) could only give by scanning. (6) *Seam:* a tick on every affected lane's row plus the chapter tick on the brush strip — the board answers "did compaction touch this stream?" per-lane, which nothing in the baseline does at rest.

**Stress mock: B.** A departures board with one row. **Honest failure:** instrument chrome — a grand header for a single lane reads as cockpit cosplay, spending vertical budget Mock B needs for cards. It must degrade to a slim single-row status bar (title, status, sparkline, open beacon) or it fails the "clean product, not a degenerate case" floor the baseline set for B.

**Visual feel raised by:** the board is pure iconography and micro-dataviz in a recognizable, charismatic idiom — the single cheapest answer to "not enough feel and creative expression," because it adds an expressive surface without touching one node card or one word of node text.

**Composes with:** everything. On variant 1, the board pins above the canvas with one row per unit and rows double as fly-to targets; with variant 3, rows are the focus switcher; with variant 2, board and brush are altitude-invariant (they are instruments, not geometry).

---

## Composition matrix

| | V1 System Map | V2 Flyover | V3 Working Line | V4 Departures Board |
|---|---|---|---|---|
| **V1** | — | **natural pair** — one zoom gesture, canvas-to-bedrock | tension: in-place widening vs curated positions → focus must become an overlay on canvas | composes — board rows fly to units |
| **V2** | | — | **unifies** — focus = per-lane altitude assignment | composes — instruments are altitude-invariant |
| **V3** | | | — | composes — board rows switch focus |
| **V4** | | | | — |

No hard conflicts; the one real tension is V1+V3 (resolved by overlay-focus). The maximal coherent stack is all four: canvas of units (V1) with snap altitudes (V2), per-lane hoist as overlay (V3), board + brush pinned above (V4). The minimal render that honors both of Pi's round-2 asks is **V1+V2** — the canvas is not honestly evaluable without semantic zoom, because fit-altitude *requires* a designed compressed representation, and "zoom in to read" is the canvas's entire reading contract.

## What renders should decide

1. **What a unit is** (V1): this round assumes unit = topic lane-cluster within one session. If Pi's mental model is whole-*session* switchyards on a shared canvas (a multi-session atlas), that is a different, bigger product — post-v0 per the Wave fence — and he should say so before renders bake the assumption in.
2. **Default altitude at fit-zoom** (V1+V2): A2 titles vs A3 glyphs. Recommend rendering both against Mock A and letting taste decide.
3. **Curation storage** (V1): per-viewer state outside the map artifact (recommended, keeps the map viewer-independent) vs baked into the map file.
4. **Focus ergonomics** (V3): in-place widening (viewport mode) vs overlay lightbox (canvas mode) — affects whether V3 survives composition with V1.
5. **Board default** (V4): always-on vs summoned. Always-on is the recommendation — an instrument that must be summoned cannot serve the three-second read — but Mock B's slim degradation must be proven first.
